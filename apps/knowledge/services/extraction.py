from dataclasses import dataclass, field
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from django.utils.text import slugify

from apps.knowledge.models import Concept
from apps.sources.models import Source, Document
from apps.rag.llm import BaseLLMProvider, get_llm_provider

logger = logging.getLogger("brofessor")

EXTRACTION_SYSTEM_PROMPT = """You are Brofessor's expert knowledge extraction system.
Analyze the provided educational content and extract structured concepts, technologies, skills, and key terms.

Respond ONLY with a valid JSON object in this exact schema:
{
  "concepts": [
    {
      "name": "Concept Name",
      "category": "concept",
      "description": "Clear 1-2 sentence definition or explanation.",
      "importance": "high",
      "evidence_snippet": "Direct sentence or excerpt from the content discussing this concept.",
      "relationships": [
        {"target": "Related Concept Name", "relation": "requires"}
      ]
    }
  ]
}

Categories must be one of: "concept", "technology", "skill", "term".
Importance must be one of: "high", "medium", "low".
Relations must be one of: "requires", "part_of", "implements", "related_to".
Do not include any conversational text or markdown outside the JSON."""


@dataclass
class ExtractedConceptResult:
    """In-memory representation of an extracted concept with its source snippet."""
    concept: Concept
    category: str
    importance: str
    evidence_snippet: str
    relationships: List[Dict[str, str]]
    is_new: bool


class ConceptExtractionService:
    """
    AI-powered concept extraction service.
    Extracts concepts, technologies, skills, and relationships from content,
    and deduplicates them against the Concept database table.
    """

    @classmethod
    def extract_from_text(
        cls,
        text: str,
        source: Optional[Source] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> List[ExtractedConceptResult]:
        """
        Extract concepts from raw text and persist/deduplicate them in the database.
        """
        if not text or not text.strip():
            return []

        active_llm = llm_provider or get_llm_provider()

        # Truncate content to reasonable context window for extraction (e.g. 5000 chars)
        prompt_content = text.strip()[:6000]
        prompt = (
            f"Extract all core concepts, technologies, skills, and key terms from the following text:\n\n"
            f"--- CONTENT BEGIN ---\n"
            f"{prompt_content}\n"
            f"--- CONTENT END ---\n\n"
            f"JSON Output:"
        )

        try:
            response = active_llm.generate(
                prompt=prompt,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                temperature=0.1,
            )
            raw_output = response.text
        except Exception as e:
            logger.error(f"LLM extraction call failed: {e}")
            raise RuntimeError(f"Concept extraction LLM error: {e}") from e

        parsed_data = cls._parse_json_response(raw_output)
        concept_dicts = parsed_data.get("concepts", [])

        results: List[ExtractedConceptResult] = []

        for item in concept_dicts:
            name = (item.get("name") or "").strip()
            if not name:
                continue

            slug = slugify(name)
            if not slug:
                continue

            description = (item.get("description") or "").strip()
            category = (item.get("category") or "concept").lower()
            importance = (item.get("importance") or "medium").lower()
            snippet = (item.get("evidence_snippet") or "").strip()
            relationships = item.get("relationships", [])

            # Concept deduplication: check if concept exists by slug
            existing = Concept.objects.filter(slug=slug).first()
            if existing:
                is_new = False
                concept = existing
                # Enrich description if previously empty
                if not concept.description and description:
                    concept.description = description
                # Update metadata with category and relationships
                meta = concept.metadata or {}
                meta.setdefault("categories", [])
                if category not in meta["categories"]:
                    meta["categories"].append(category)
                existing_rels = meta.get("relationships", [])
                existing_rels.extend(relationships)
                meta["relationships"] = existing_rels
                concept.metadata = meta
                concept.save(update_fields=["description", "metadata"])
            else:
                is_new = True
                concept = Concept.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    metadata={
                        "category": category,
                        "importance": importance,
                        "relationships": relationships,
                        "source_id": str(source.id) if source else None,
                    },
                )

            results.append(
                ExtractedConceptResult(
                    concept=concept,
                    category=category,
                    importance=importance,
                    evidence_snippet=snippet,
                    relationships=relationships,
                    is_new=is_new,
                )
            )

        logger.info(
            f"Extracted {len(results)} concepts ({sum(1 for r in results if r.is_new)} new) from text."
        )
        return results

    @classmethod
    def extract_from_source(
        cls,
        source: Source,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> List[ExtractedConceptResult]:
        """Extract concepts from all documents belonging to a Source."""
        documents = source.documents.all()
        all_results: List[ExtractedConceptResult] = []

        for doc in documents:
            text = doc.content
            if not text and doc.chunks.exists():
                text = "\n\n".join(chunk.content for chunk in doc.chunks.all()[:10])
            if text:
                extracted = cls.extract_from_text(
                    text=text,
                    source=source,
                    llm_provider=llm_provider,
                )
                all_results.extend(extracted)

        return all_results

    @classmethod
    def _parse_json_response(cls, text: str) -> Dict[str, Any]:
        """Robustly extract JSON object from LLM response string."""
        if not text:
            return {}

        clean_text = text.strip()

        # Handle ```json ... ``` markdown codeblocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
        if json_match:
            clean_text = json_match.group(1).strip()

        # Find outermost JSON object {...}
        start = clean_text.find("{")
        end = clean_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean_text = clean_text[start : end + 1]

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as err:
            logger.warning(f"Failed to parse LLM JSON response: {err}. Raw: {clean_text[:200]}")
            return {}
