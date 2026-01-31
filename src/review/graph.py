"""LangGraph review pipeline."""

from __future__ import annotations

from functools import partial
from typing import Dict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from src.config import Config
from src.review.state import ReviewState
from src.review.nodes.intent_analysis import intent_analysis
from src.review.nodes.bug_logic_review import bug_logic_review
from src.review.nodes.engineering_quality import engineering_quality_review
from src.review.nodes.production_readiness import production_readiness_review
from src.review.nodes.decision_engine import decision_engine
from src.review.nodes.report_generator import report_generator


def create_review_graph(config: Config) -> StateGraph:
    llm = ChatOpenAI(
        model=config.openai_model,
        api_key=config.openai_api_key,
        temperature=0.1,
    )

    workflow = StateGraph(ReviewState)

    workflow.add_node("intent_analysis", partial(_run_intent_analysis, llm=llm))
    workflow.add_node("bug_logic_review", partial(_run_bug_logic_review, llm=llm))
    workflow.add_node("engineering_quality_review", partial(_run_engineering_quality, llm=llm))
    workflow.add_node("production_readiness_review", partial(_run_production_readiness, llm=llm))
    workflow.add_node("decision_engine", _run_decision_engine)
    workflow.add_node("report_generator", _run_report_generator)

    workflow.set_entry_point("intent_analysis")
    workflow.add_edge("intent_analysis", "bug_logic_review")
    workflow.add_edge("bug_logic_review", "engineering_quality_review")
    workflow.add_edge("engineering_quality_review", "production_readiness_review")
    workflow.add_edge("production_readiness_review", "decision_engine")
    workflow.add_edge("decision_engine", "report_generator")
    workflow.add_edge("report_generator", END)

    return workflow.compile()


async def _run_intent_analysis(state: ReviewState, llm: ChatOpenAI) -> Dict:
    return await intent_analysis(state, llm)


async def _run_bug_logic_review(state: ReviewState, llm: ChatOpenAI) -> Dict:
    return await bug_logic_review(state, llm)


async def _run_engineering_quality(state: ReviewState, llm: ChatOpenAI) -> Dict:
    return await engineering_quality_review(state, llm)


async def _run_production_readiness(state: ReviewState, llm: ChatOpenAI) -> Dict:
    return await production_readiness_review(state, llm)


async def _run_decision_engine(state: ReviewState) -> Dict:
    return await decision_engine(state)


async def _run_report_generator(state: ReviewState) -> Dict:
    return await report_generator(state)
