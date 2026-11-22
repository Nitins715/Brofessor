from django.test import TestCase
from apps.processing.chunking.text_chunker import TextChunker, ChunkData
from apps.processing.chunking.config import ChunkingConfig
from apps.processing.extractors.text import TextExtractor
from apps.sources.models import Source, Document, DocumentChunk
from apps.processing.pipeline import IngestionPipeline


class SemanticChunkingHeadingTests(TestCase):
    """Tests for heading-aware semantic chunking and hierarchy preservation."""

    def test_markdown_heading_extraction_and_hierarchy(self):
        sample_markdown = """# Database Systems

This is general intro text for database systems.

## Transactions

Transactions are fundamental for database consistency.

### ACID Properties

ACID stands for Atomicity, Consistency, Isolation, and Durability.
Each property ensures reliable transaction processing.

## Normalization

Normalization reduces data redundancy.

### First Normal Form (1NF)

1NF requires all attribute values to be atomic.
"""
        chunker = TextChunker()
        blocks = chunker._extract_blocks(sample_markdown)

        # Map block text to its assigned heading
        block_headings = {b["text"].split("\n")[0]: b["heading"] for b in blocks}

        # Level 1 intro text
        self.assertEqual(block_headings["# Database Systems"], "Database Systems")
        self.assertEqual(block_headings["This is general intro text for database systems."], "Database Systems")

        # Level 2 block under Transactions
        self.assertEqual(block_headings["## Transactions"], "Database Systems > Transactions")
        self.assertEqual(block_headings["Transactions are fundamental for database consistency."], "Database Systems > Transactions")

        # Level 3 block under ACID Properties
        self.assertEqual(block_headings["### ACID Properties"], "Database Systems > Transactions > ACID Properties")
        self.assertIn("Database Systems > Transactions > ACID Properties", block_headings["ACID stands for Atomicity, Consistency, Isolation, and Durability."])

        # Hierarchy pruned back to Level 2 under Normalization
        self.assertEqual(block_headings["## Normalization"], "Database Systems > Normalization")
        self.assertEqual(block_headings["Normalization reduces data redundancy."], "Database Systems > Normalization")

        # New Level 3 under Normalization
        self.assertEqual(block_headings["### First Normal Form (1NF)"], "Database Systems > Normalization > First Normal Form (1NF)")
        self.assertEqual(block_headings["1NF requires all attribute values to be atomic."], "Database Systems > Normalization > First Normal Form (1NF)")

    def test_chunk_hierarchical_preserves_headings(self):
        text = """# Operating Systems

Overview of operating systems architecture.

## Process Scheduling

Process scheduling handles CPU allocation.

### Round Robin

Round Robin gives each process a fixed time slice quantum.
It ensures fairness among all ready processes in the queue.
"""
        config = ChunkingConfig(
            parent_chunk_size=300,
            parent_chunk_overlap=0,
            child_chunk_size=100,
            child_chunk_overlap=0,
        )
        chunker = TextChunker(config=config)
        parents, children = chunker.chunk_hierarchical(text)

        self.assertGreater(len(parents), 0)
        self.assertGreater(len(children), 0)

        # Check parent heading
        parent_headings = [p.heading for p in parents if p.heading]
        self.assertTrue(any("Operating Systems" in h for h in parent_headings))

        # Check children headings
        child_headings = [c.heading for c in children if c.heading]
        self.assertTrue(any("Process Scheduling" in h or "Operating Systems" in h for h in child_headings))

    def test_pipeline_persists_document_chunk_heading(self):
        source = Source.objects.create(
            name="Test Architecture Note",
            source_type=Source.SourceType.NOTE,
            metadata={
                "title": "System Architecture",
                "text": """# Microservices Architecture

Microservices partition functionality into distinct bounded services.

## Event Driven Communication

Services interact asynchronously via message buses.
""",
            },
        )

        doc = IngestionPipeline.process_source(source.id)
        self.assertIsNotNone(doc)

        chunks = DocumentChunk.objects.filter(document=doc)
        self.assertGreater(chunks.count(), 0)

        # Verify heading field on DocumentChunk model
        chunks_with_heading = chunks.filter(heading__gt="")
        self.assertGreater(chunks_with_heading.count(), 0)

        first_heading_chunk = chunks_with_heading.first()
        self.assertIn("Microservices Architecture", first_heading_chunk.heading)
        self.assertIn("heading", first_heading_chunk.metadata)
