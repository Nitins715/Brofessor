import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from apps.rag.services.retrieval import SearchResult
from apps.rag.llm import BaseLLMProvider, get_llm_provider

logger = logging.getLogger("brofessor")


class DocumentGrader:
    """
    Self-RAG Document Relevance Grader:
    Assesses whether retrieved knowledge-base chunks contain relevant information
    to answer the user's question. Filters irrelevant chunks and flags insufficient context.
    """

    GRADER_SYSTEM_PROMPT = """You are an objective document evaluator for a RAG system.
Evaluate whether the following retrieved document context is relevant and useful for answering the user's question.
If the document mentions facts, concepts, or details directly related to the user's inquiry, rate it as "yes".
If the document is unrelated, off-topic, or completely unhelpful, rate it as "no".

Return ONLY a JSON object:
{"relevant": "yes" | "no", "reason": "brief explanation"}"""

    @classmethod
    def grade_chunk(
        cls,
        query: str,
        chunk: SearchResult,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> bool:
        """
        Grades an individual chunk for relevance.
        """
        # Fast similarity heuristic: if similarity or RRF score is strong, pass immediately
        if chunk.similarity_score >= 0.40:
            return True

        # Extremely low similarity: reject immediately without wasting an LLM call
        if chunk.similarity_score < 0.15:
            return False

        active_llm = llm_provider or get_llm_provider()
        prompt = (
            f"User Question: {query}\n\n"
            f"Retrieved Document Content:\n{chunk.content[:600]}\n"
        )
        try:
            resp = active_llm.generate(
                prompt=prompt,
                system_prompt=cls.GRADER_SYSTEM_PROMPT,
                temperature=0.0,
            )
            raw = resp.text.strip()
            first_brace = raw.find("{")
            last_brace = raw.rfind("}")
            if first_brace != -1 and last_brace != -1:
                parsed = json.loads(raw[first_brace : last_brace + 1])
                return parsed.get("relevant", "no").lower() == "yes"
        except Exception as e:
            logger.warning(f"DocumentGrader error ({e}), keeping chunk based on vector score.")
            return chunk.similarity_score >= 0.3

        return False

    @classmethod
    def filter_and_evaluate(
        cls,
        query: str,
        chunks: List[SearchResult],
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> Tuple[List[SearchResult], str]:
        """
        Evaluates all chunks and returns (relevant_chunks, status).
        status: "RELEVANT" | "INSUFFICIENT"
        """
        if not chunks:
            return [], "INSUFFICIENT"

        relevant: List[SearchResult] = []
        for c in chunks:
            if cls.grade_chunk(query, c, llm_provider):
                relevant.append(c)

        if not relevant:
            # None passed strict grading
            return [], "INSUFFICIENT"

        return relevant, "RELEVANT"


class HallucinationChecker:
    """
    Self-RAG Hallucination Checker:
    Verifies that generated answers are grounded in the provided context
    without hallucinating unsupported claims.
    """

    CHECKER_PROMPT = """You are a factual consistency auditor.
Compare the generated answer against the provided context.
Does the answer contain claims or facts that contradict or are completely unsupported by the context?
Answer "yes" if the answer is grounded and supported by the context.
Answer "no" if the answer hallucinates unsupported facts.

Return ONLY a JSON object:
{"grounded": "yes" | "no", "critique": "brief statement"}"""

    @classmethod
    def is_grounded(
        cls,
        answer: str,
        context: str,
        llm_provider: Optional[BaseLLMProvider] = None,
        fast_mode: bool = True,
    ) -> bool:
        if not context or not answer:
            return True

        if fast_mode:
            # Fast verification: if answer cites sources or shares domain vocabulary, it's grounded
            if re.search(r"\[(?:Source|Doc|Web)\s*\d+\]", answer, re.IGNORECASE):
                return True
            answer_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", answer.lower()))
            context_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", context.lower()))
            if len(answer_words.intersection(context_words)) >= 3:
                return True

        active_llm = llm_provider or get_llm_provider()
        prompt = (
            f"Context:\n{context[:1500]}\n\n"
            f"Generated Answer:\n{answer}\n"
        )
        try:
            resp = active_llm.generate(
                prompt=prompt,
                system_prompt=cls.CHECKER_PROMPT,
                temperature=0.0,
            )
            raw = resp.text.strip()
            first_brace = raw.find("{")
            last_brace = raw.rfind("}")
            if first_brace != -1 and last_brace != -1:
                parsed = json.loads(raw[first_brace : last_brace + 1])
                return parsed.get("grounded", "yes").lower() == "yes"
        except Exception as e:
            logger.warning(f"HallucinationChecker error ({e}), assuming grounded.")
            return True

        return True
