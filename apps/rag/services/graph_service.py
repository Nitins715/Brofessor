from dataclasses import dataclass, field
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from django.db import transaction
from django.db.models import Q

from apps.sources.models import Document, DocumentChunk, Entity, Relationship, EntityChunkMapping
from apps.rag.llm import BaseLLMProvider, get_llm_provider

logger = logging.getLogger("brofessor")


@dataclass
class GraphTriple:
    """Represents a subject-predicate-object relationship triple."""
    source_name: str
    target_name: str
    relation_type: str
    description: str = ""
    source_type: str = "concept"
    target_type: str = "concept"
    weight: float = 1.0


@dataclass
class SubgraphResult:
    """Traversed knowledge subgraph containing connected entities, relations, and chunks."""
    entities: List[Entity]
    relationships: List[Relationship]
    mapped_chunks: List[DocumentChunk] = field(default_factory=list)
    formatted_paths: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        """Format relationships into clear, readable lines for LLM context injection."""
        if not self.relationships:
            return ""
        lines = []
        for r in self.relationships:
            desc = f" ({r.description})" if r.description else ""
            lines.append(f"• [{r.source_entity.name}] --{r.relation_type.upper()}--> [{r.target_entity.name}]{desc}")
        return "\n".join(lines)


class KnowledgeGraphService:
    """
    Knowledge Graph extraction, traversal, and retrieval service.
    Enables multi-hop relational reasoning across stored knowledge.
    """

    EXTRACTION_SYSTEM_PROMPT = """You are a knowledge graph engineer.
Extract core technical entities (concepts, technologies, tools, algorithms, architectures) and their directed relationships from the provided text.
Identify key relational links such as:
- PREREQUISITE_OF (e.g. Linear Algebra is prerequisite of Attention)
- PART_OF (e.g. cgroups is part of Linux Kernel)
- IMPLEMENTS (e.g. ResNet implements Residual Connections)
- USES (e.g. Docker uses namespaces)
- ENABLES (e.g. Attention enables Context Awareness)
- COMPARED_TO (e.g. Containers compared to Virtual Machines)

Return ONLY a JSON array of triples with this exact schema:
[
  {
    "source": "Entity A",
    "source_type": "concept" | "technology" | "algorithm" | "framework" | "architecture",
    "relation": "PREREQUISITE_OF" | "PART_OF" | "IMPLEMENTS" | "USES" | "ENABLES" | "COMPARED_TO" | "RELATES_TO",
    "target": "Entity B",
    "target_type": "concept" | "technology" | "algorithm" | "framework" | "architecture",
    "description": "Brief 1-sentence explanation of why/how they are linked"
  }
]
If no clear technical relationships exist, return an empty array []."""

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Canonicalize entity name for deduplication."""
        if not name:
            return ""
        clean = name.strip()
        # Remove markdown symbols, punctuation, quotes
        clean = re.sub(r"[`'\"#\(\)\[\]]", "", clean).strip()
        return clean.lower()

    @classmethod
    def extract_triples_from_text(
        cls,
        text: str,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> List[GraphTriple]:
        """
        Extract knowledge triples from raw text snippet using the active LLM.
        """
        if not text or len(text.strip()) < 40:
            return []

        active_llm = llm_provider or get_llm_provider()
        prompt = f"Analyze the following technical text and extract key entity-relationship triples:\n\n{text[:2000]}"

        try:
            res = active_llm.generate(
                prompt=prompt,
                system_prompt=cls.EXTRACTION_SYSTEM_PROMPT,
                temperature=0.0,
            )
            raw = res.text.strip()
            # Parse JSON block
            first_bracket = raw.find("[")
            last_bracket = raw.rfind("]")
            if first_bracket != -1 and last_bracket != -1:
                parsed = json.loads(raw[first_bracket : last_bracket + 1])
                triples: List[GraphTriple] = []
                for item in parsed:
                    s_name = str(item.get("source") or "").strip()
                    t_name = str(item.get("target") or "").strip()
                    rel = str(item.get("relation") or "relates_to").strip().lower()
                    if s_name and t_name and s_name.lower() != t_name.lower():
                        triples.append(
                            GraphTriple(
                                source_name=s_name,
                                target_name=t_name,
                                relation_type=rel,
                                description=str(item.get("description") or "").strip(),
                                source_type=str(item.get("source_type") or "concept").lower(),
                                target_type=str(item.get("target_type") or "concept").lower(),
                            )
                        )
                return triples
        except Exception as e:
            logger.warning(f"KnowledgeGraph extraction LLM error: {e}. Falling back to heuristic extractor.")

        # Heuristic fallback extractor for offline/test environments
        return cls._heuristic_extract(text)

    @classmethod
    def _heuristic_extract(cls, text: str) -> List[GraphTriple]:
        """Fallback rule-based entity relation extraction."""
        triples = []
        patterns = [
            (r"([A-Za-z0-9_\- ]+?)\s+(?:uses|utilizes|relies on)\s+([A-Za-z0-9_\- ]+)", "uses"),
            (r"([A-Za-z0-9_\- ]+?)\s+(?:is part of|belongs to)\s+([A-Za-z0-9_\- ]+)", "part_of"),
            (r"([A-Za-z0-9_\- ]+?)\s+(?:implements|executes)\s+([A-Za-z0-9_\- ]+)", "implements"),
            (r"([A-Za-z0-9_\- ]+?)\s+(?:requires|prerequisite for)\s+([A-Za-z0-9_\- ]+)", "prerequisite_of"),
            (r"([A-Za-z0-9_\- ]+?)\s+(?:compared to|differs from)\s+([A-Za-z0-9_\- ]+)", "compared_to"),
        ]
        for pattern, rel in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                src = match.group(1).strip()
                tgt = match.group(2).strip()
                if 2 <= len(src) <= 40 and 2 <= len(tgt) <= 40:
                    triples.append(
                        GraphTriple(
                            source_name=src,
                            target_name=tgt,
                            relation_type=rel,
                            description=f"{src} {rel} {tgt}",
                        )
                    )
        return triples[:5]

    @classmethod
    def index_chunk(
        cls,
        chunk: DocumentChunk,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> List[Relationship]:
        """
        Extracts triples from a DocumentChunk and persists Entities and Relationships in the DB.
        """
        triples = cls.extract_triples_from_text(chunk.content, llm_provider=llm_provider)
        if not triples:
            return []

        saved_relations: List[Relationship] = []

        with transaction.atomic():
            for t in triples:
                src_canon = cls.normalize_name(t.source_name)
                tgt_canon = cls.normalize_name(t.target_name)

                if not src_canon or not tgt_canon:
                    continue

                # 1. Resolve or create Source Entity
                src_entity, _ = Entity.objects.get_or_create(
                    canonical_name=src_canon,
                    defaults={
                        "name": t.source_name.strip(),
                        "entity_type": t.source_type if t.source_type in Entity.EntityType.values else Entity.EntityType.CONCEPT,
                        "description": t.description or f"Entity {t.source_name}",
                    },
                )

                # 2. Resolve or create Target Entity
                tgt_entity, _ = Entity.objects.get_or_create(
                    canonical_name=tgt_canon,
                    defaults={
                        "name": t.target_name.strip(),
                        "entity_type": t.target_type if t.target_type in Entity.EntityType.values else Entity.EntityType.CONCEPT,
                        "description": t.description or f"Entity {t.target_name}",
                    },
                )

                # 3. Create or update Relationship edge
                rel_type = t.relation_type.lower()
                valid_types = set(Relationship.RelationType.values)
                if rel_type not in valid_types:
                    rel_type = Relationship.RelationType.RELATION

                relationship, _ = Relationship.objects.update_or_create(
                    source_entity=src_entity,
                    target_entity=tgt_entity,
                    relation_type=rel_type,
                    defaults={
                        "description": t.description,
                        "weight": t.weight,
                        "source_chunk": chunk,
                    },
                )
                saved_relations.append(relationship)

                # 4. Map entities to chunk for citation provenance
                for ent in (src_entity, tgt_entity):
                    mapping, created = EntityChunkMapping.objects.get_or_create(
                        entity=ent,
                        chunk=chunk,
                    )
                    if not created:
                        mapping.mention_count += 1
                        mapping.save(update_fields=["mention_count"])

        return saved_relations

    @classmethod
    def find_query_entities(cls, query: str) -> List[Entity]:
        """
        Match words and noun phrases in query string to existing Knowledge Graph entities.
        """
        if not query or not query.strip():
            return []

        clean_query = query.lower()
        matched_entities: List[Entity] = []

        # Find entities whose canonical names appear as substrings or whole words in query
        all_entities = list(Entity.objects.all())
        for ent in all_entities:
            c_name = ent.canonical_name
            if len(c_name) >= 3 and (c_name in clean_query or ent.name.lower() in clean_query):
                matched_entities.append(ent)

        return matched_entities

    @classmethod
    def traverse_subgraph(
        cls,
        start_entities: List[Entity],
        max_depth: int = 2,
        max_edges: int = 12,
    ) -> SubgraphResult:
        """
        Traverses outgoing and incoming relationships from start entities using Breadth-First Search (BFS).
        Returns connected entities, relationships, and mapped document chunks for multi-hop retrieval.
        """
        if not start_entities:
            return SubgraphResult(entities=[], relationships=[], mapped_chunks=[])

        visited_entity_ids: Set[uuid.UUID] = {e.id for e in start_entities}
        collected_entities: Dict[uuid.UUID, Entity] = {e.id: e for e in start_entities}
        collected_relationships: Dict[uuid.UUID, Relationship] = {}
        frontier: List[Entity] = list(start_entities)

        for depth in range(max_depth):
            if not frontier or len(collected_relationships) >= max_edges:
                break

            current_ids = [e.id for e in frontier]
            frontier = []

            # Find all outgoing and incoming relationships for current frontier nodes
            edges_qs = Relationship.objects.filter(
                Q(source_entity_id__in=current_ids) | Q(target_entity_id__in=current_ids)
            ).select_related("source_entity", "target_entity", "source_chunk")

            for edge in edges_qs:
                if edge.id in collected_relationships:
                    continue

                collected_relationships[edge.id] = edge

                # Check newly discovered nodes
                for node in (edge.source_entity, edge.target_entity):
                    if node.id not in visited_entity_ids:
                        visited_entity_ids.add(node.id)
                        collected_entities[node.id] = node
                        frontier.append(node)

                if len(collected_relationships) >= max_edges:
                    break

        # Collect mapped document chunks from all discovered entities for multi-hop context
        entity_ids = list(collected_entities.keys())
        chunk_mappings = (
            EntityChunkMapping.objects.filter(entity_id__in=entity_ids)
            .select_related("chunk", "chunk__document", "chunk__parent_chunk")
            .order_by("-mention_count")[:6]
        )
        mapped_chunks = [m.chunk for m in chunk_mappings]

        return SubgraphResult(
            entities=list(collected_entities.values()),
            relationships=list(collected_relationships.values()),
            mapped_chunks=mapped_chunks,
        )
