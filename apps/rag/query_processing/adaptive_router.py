import json
import logging
import re
from typing import Any, Dict, Optional

from apps.rag.llm import BaseLLMProvider, get_llm_provider

logger = logging.getLogger("brofessor")


class AdaptiveRouter:
    """
    Adaptive RAG Router:
    Classifies incoming user questions into one of three routing strategies:
    1. PARAMETRIC: Simple facts, conversational greetings, basic language syntax
       (answered directly from model knowledge without document search).
    2. RETRIEVAL: Knowledge-base questions requiring stored documents / notes.
    3. WEB_SEARCH: Explicit requests for live external web information.
    """

    ROUTER_SYSTEM_PROMPT = """You are a query routing specialist for an AI knowledge assistant.
Analyze the user's input and classify it into exactly ONE routing category:
- "PARAMETRIC": ONLY pure conversational greetings (e.g. "hello", "how are you"), social pleasantries (e.g. "thanks", "bye"), bot identity/persona questions (e.g. "who are you"), or simple arithmetic calculations (e.g. "what is 5 * 12"). Do NOT classify technical, coding, conceptual, or informational questions as PARAMETRIC.
- "RETRIEVAL": ALL technical questions, programming and coding queries (e.g. questions about Python, syntax, functions, variables, classes, data structures, algorithms), conceptual explanations, documentation queries, user notes, uploaded PDFs, domain skills, and internal knowledge. When in doubt, ALWAYS choose RETRIEVAL so stored sources and documents are searched.
- "WEB_SEARCH": Questions explicitly asking to search the internet or asking about recent live news/events outside normal knowledge.

Return ONLY a JSON object in this format:
{"category": "PARAMETRIC" | "RETRIEVAL" | "WEB_SEARCH", "reason": "brief explanation"}"""

    @classmethod
    def classify(
        cls,
        query: str,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> Dict[str, str]:
        """
        Classifies query intent. Uses fast heuristics first, falling back to LLM.
        """
        clean = (query or "").strip().lower()

        # Fast heuristics for conversational greetings & basic math
        clean_words = set(re.findall(r"\b[a-z]+\b", clean))
        greeting_words = {
            "hi", "hello", "hey", "there", "howdy", "greetings",
            "good", "morning", "afternoon", "evening", "who", "are", "you", "help",
            "thanks", "thank", "bye", "goodbye", "brofessor", "bro", "assistant",
            "for", "the", "a", "an", "to", "my", "your", "i", "am", "doing", "how"
        }
        if clean_words and clean_words.issubset(greeting_words):
            return {"category": "PARAMETRIC", "reason": "Conversational greeting"}

        if re.match(r"^(what is|calculate|solve)?\s*[\d\s\+\-\*\/\(\)\^\.]+\??$", clean):
            return {"category": "PARAMETRIC", "reason": "Basic arithmetic calculation"}

        if any(trigger in clean for trigger in ("search web", "search internet", "google it", "look up on web")):
            return {"category": "WEB_SEARCH", "reason": "Explicit web search instruction"}

        # Fast heuristics for knowledge/technical questions: route directly to RETRIEVAL
        technical_keywords = {
            "python", "code", "coding", "function", "functions", "variable", "variables",
            "class", "classes", "object", "objects", "loop", "loops", "list", "lists",
            "dict", "dictionary", "dictionaries", "tuple", "tuples", "set", "sets",
            "repl", "integer", "string", "float", "boolean", "type", "types", "typecasting",
            "import", "module", "modules", "package", "packages", "library", "libraries",
            "syntax", "operator", "operators", "condition", "recursion", "generator", "yield",
            "decorator", "lambda", "async", "await", "coroutine", "thread", "process",
            "sql", "database", "postgres", "postgresql", "index", "indexing", "vector",
            "embedding", "embeddings", "rag", "model", "neural", "attention", "transformer",
            "document", "documents", "pdf", "file", "note", "notes", "handbook", "chapter"
        }
        if clean_words.intersection(technical_keywords):
            return {"category": "RETRIEVAL", "reason": "Technical domain keyword match"}

        if re.match(r"^(what is|what are|how to|how do|how does|explain|describe|tell me about|difference between|compare|can you explain)\b", clean):
            return {"category": "RETRIEVAL", "reason": "Informational inquiry seeking explanation"}

        # Use active LLM for nuanced classification
        active_llm = llm_provider or get_llm_provider()
        try:
            resp = active_llm.generate(
                prompt=f"User Query: {query}",
                system_prompt=cls.ROUTER_SYSTEM_PROMPT,
                temperature=0.0,
            )
            raw = resp.text.strip()
            # Extract JSON
            first_brace = raw.find("{")
            last_brace = raw.rfind("}")
            if first_brace != -1 and last_brace != -1:
                parsed = json.loads(raw[first_brace : last_brace + 1])
                category = parsed.get("category", "RETRIEVAL").upper()
                if category in ("PARAMETRIC", "RETRIEVAL", "WEB_SEARCH"):
                    return {"category": category, "reason": parsed.get("reason", "")}
        except Exception as e:
            logger.warning(f"AdaptiveRouter LLM classification failed ({e}), defaulting to RETRIEVAL.")

        # Default to RETRIEVAL so stored knowledge is consulted
        return {"category": "RETRIEVAL", "reason": "Default knowledge retrieval"}


class QueryComplexityClassifier:
    """
    Evaluates query difficulty and complexity.
    Only 'hard' queries warrant LLM query transformation, multi-hop sub-queries,
    and deep Self-RAG evaluation. Simple or direct queries proceed directly to
    hybrid retrieval and grounded generation to maintain sub-second latency.
    """

    HARD_INTENT_PATTERNS = [
        r"\b(?:compare|comparison|versus|\bvs\b|difference between|tradeoffs?|pros and cons)\b",
        r"\b(?:how does .+ affect|relationship between|impact of .+ on)\b",
        r"\b(?:step by step|architecture of|detailed implementation|deep dive|under the hood)\b",
        r"\b(?:synthesize|root cause|troubleshoot why|explain why .+ whereas)\b",
    ]

    @classmethod
    def is_hard(cls, query: str) -> bool:
        if not query:
            return False
        clean = query.strip().lower()

        # Check explicit hard reasoning/comparative patterns
        for pattern in cls.HARD_INTENT_PATTERNS:
            if re.search(pattern, clean):
                return True

        # Multi-question or multi-clause queries
        words = clean.split()
        if clean.count("?") > 1:
            return True
        if len(words) >= 15 and any(conj in clean for conj in [" and also ", " whereas ", " however ", " although ", " in addition to "]):
            return True

        return False


class QueryTransformer:
    """
    Transforms and expands user queries into optimized search queries
    for both dense vector retrieval and BM25 lexical matching.
    Only applied to harder/complex queries to avoid unnecessary LLM latency.
    """

    TRANSFORM_PROMPT = """You are a retrieval optimization assistant.
Rewrite the user's conversational question into a clean, keyword-rich search query that maximizes retrieval accuracy from a technical knowledge base.
Remove filler words (e.g., "can you tell me about", "I was wondering"). Focus on key domain terminology, concepts, and identifiers.

Return ONLY the rewritten search query text without quotation marks or explanations."""

    @classmethod
    def transform(
        cls,
        query: str,
        llm_provider: Optional[BaseLLMProvider] = None,
        force: bool = False,
    ) -> str:
        """
        Optimizes and sharpens retrieval query only if query is classified as hard/complex.
        """
        if not query or len(query.strip()) < 10:
            return (query or "").strip()

        # Only transform if query is hard, unless forced
        if not force and not QueryComplexityClassifier.is_hard(query):
            logger.info(f"Query '{query[:35]}...' is straightforward; skipping query rewriting.")
            return query.strip()

        active_llm = llm_provider or get_llm_provider()
        try:
            res = active_llm.generate(
                prompt=f"Original Query: {query}",
                system_prompt=cls.TRANSFORM_PROMPT,
                temperature=0.1,
            )
            transformed = res.text.strip().strip('"\'')
            if transformed and len(transformed) >= 3:
                return transformed
        except Exception as e:
            logger.warning(f"QueryTransformer error ({e}), keeping original query.")

        return query.strip()
