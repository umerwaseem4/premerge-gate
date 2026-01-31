"""Main entry point for the AI PR Review system."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Dict, NoReturn

from src.config import load_config, Config
from src.github_client import GitHubClient
from src.language_detector import detect_languages_in_files
from src.review.graph import create_review_graph
from src.review.state import PRInfo, ReviewState
from src.review.nodes.report_generator import generate_markdown_report


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_review(config: Config) -> Dict:
    """Run the complete review pipeline.

    Args:
        config: Application configuration.

    Returns:
        Final review state.
    """
    logger.info("Starting AI PR Review")

    # Initialize GitHub client
    github = GitHubClient(config)

    # Set status to pending
    workflow_url = github.get_workflow_run_url()
    github.set_status("pending", "AI review in progress...", workflow_url)
    logger.info("Set status to pending")

    try:
        # Fetch PR data
        logger.info(f"Fetching PR #{config.pr_number}")
        pr_metadata = github.get_pr_metadata()
        pr_diff = github.get_full_diff_text()

        # Detect languages
        languages = list(detect_languages_in_files(pr_metadata.files_changed))
        logger.info(f"Detected languages: {languages}")

        # Create PR info object
        pr_info = PRInfo(
            number=pr_metadata.number,
            title=pr_metadata.title,
            description=pr_metadata.description,
            author=pr_metadata.author,
            base_branch=pr_metadata.base_branch,
            head_branch=pr_metadata.head_branch,
            files_changed=pr_metadata.files_changed,
            additions=pr_metadata.additions,
            deletions=pr_metadata.deletions,
            url=pr_metadata.url,
        )

        # Initialize review state
        initial_state: ReviewState = {
            "pr_diff": pr_diff,
            "pr_metadata": pr_info,
            "languages": languages,
            "intent_summary": "",
            "findings": [],
            "decision": "",
            "confidence_score": 0.0,
            "markdown_report": "",
            "docx_report_path": None,
            "current_stage": "init",
            "error_message": None,
        }

        # Create and run the review graph
        logger.info("Creating review pipeline")
        graph = create_review_graph(config)

        logger.info("Running review pipeline")
        final_state = await graph.ainvoke(initial_state)

        logger.info(f"Review complete. Decision: {final_state['decision']}")

        # Build artifact URL
        artifact_url = None
        run_id = os.getenv("GITHUB_RUN_ID")
        if run_id:
            artifact_url = f"https://github.com/{config.github_repository}/actions/runs/{run_id}"

        # Generate final markdown report with artifact link
        markdown_report = generate_markdown_report(final_state, artifact_url)

        # Post or update PR comment
        existing_comment = github.find_existing_review_comment()
        if existing_comment:
            github.update_comment(existing_comment, markdown_report)
            logger.info(f"Updated existing comment {existing_comment}")
        else:
            comment_id = github.post_comment(markdown_report)
            logger.info(f"Posted new comment {comment_id}")

        # Set final status
        decision = final_state["decision"]
        if decision == "PASS":
            github.set_status(
                "success",
                "AI review passed - no blocking issues found",
                workflow_url,
            )
        else:
            blocking_count = sum(
                1 for f in final_state.get("findings", [])
                if f.severity.value == "BLOCKING"
            )
            github.set_status(
                "failure",
                f"AI review failed - {blocking_count} blocking issue(s)",
                workflow_url,
            )

        return final_state

    except Exception as e:
        logger.exception("Error during review")
        github.set_status(
            "error",
            f"AI review error: {str(e)[:100]}",
            workflow_url,
        )
        raise


def main() -> NoReturn:
    """Main entry point."""
    try:
        config = load_config()
        result = asyncio.run(run_review(config))

        # Exit with appropriate code
        if result.get("decision") == "FAIL":
            logger.info("Review completed with FAIL - but this is expected behavior")
            sys.exit(0)  # Don't fail the action, just mark the status
        else:
            logger.info("Review completed with PASS")
            sys.exit(0)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
