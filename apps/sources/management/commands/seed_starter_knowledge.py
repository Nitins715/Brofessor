"""
Management command to idempotently ingest pre-packaged Computer Science fundamentals
starter notes (CN, DBMS, OS, OOPS) from CodeKairo into Brofessor's knowledge base.
Extracts rich markdown structure with multi-level heading breadcrumbs (# H1 > ## H2 > ### H3),
builds parent/child chunks, generates local 384d FastEmbed vector embeddings,
and extracts Knowledge Graph entities and relationships while maintaining printable PDFs.
"""
import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.sources.models import Source
from apps.processing.pipeline import IngestionPipeline


class Command(BaseCommand):
    help = "Idempotently seeds and ingests curated CS notes (CN, DBMS, OS, OOPS) with hierarchical heading chunks."

    STARTER_SOURCES = [
        {
            "key": "DBMS",
            "name": "Database Management Systems (DBMS) Complete Notes — CodeKairo",
            "pdf_filename": "DBMS_Complete_Notes.pdf",
            "md_filename": "DBMS_Complete_Notes.md",
            "uri": "https://codekairo.com/notes/dbms",
            "description": "Comprehensive notes covering ER models, relational keys, normalization, SQL, transactions, ACID properties, concurrency control, B+ trees, and NoSQL.",
            "modules_count": 12,
        },
        {
            "key": "OS",
            "name": "Operating Systems (OS) Complete Notes — CodeKairo",
            "pdf_filename": "OS_Complete_Notes.pdf",
            "md_filename": "OS_Complete_Notes.md",
            "uri": "https://codekairo.com/notes/operating-systems",
            "description": "Comprehensive notes covering processes, threads, CPU scheduling algorithms, synchronization, deadlocks, IPC, virtual memory, paging, and file systems.",
            "modules_count": 12,
        },
        {
            "key": "CN",
            "name": "Computer Networks (CN) Complete Notes — CodeKairo",
            "pdf_filename": "CN_Complete_Notes.pdf",
            "md_filename": "CN_Complete_Notes.md",
            "uri": "https://codekairo.com/notes/computer-networks",
            "description": "Comprehensive networking notes covering OSI vs TCP/IP models, Data Link framing, IP addressing, subnetting, routing, TCP/UDP, DNS, HTTP/HTTPS, NAT, and security.",
            "modules_count": 12,
        },
        {
            "key": "OOPS",
            "name": "Object-Oriented Programming (OOPS) Complete Notes — CodeKairo",
            "pdf_filename": "OOPS_Complete_Notes.pdf",
            "md_filename": "OOPS_Complete_Notes.md",
            "uri": "https://codekairo.com/notes/oop",
            "description": "Comprehensive Object-Oriented Programming notes covering Classes, Objects, Encapsulation, Abstraction, Inheritance, Polymorphism, SOLID principles, design patterns, and exception handling.",
            "modules_count": 11,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-ingestion and vector embedding generation even if source exists.",
        )

    def handle(self, *args, **options):
        force = options.get("force", False)
        bundle_dir = Path(settings.BASE_DIR) / "apps" / "sources" / "data" / "starter_pack"
        media_starter_dir = Path(settings.MEDIA_ROOT) / "starter_pack"
        media_starter_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(self.style.SUCCESS("  Brofessor Default Starter Knowledge Ingestion (CodeKairo)   "))
        self.stdout.write(self.style.SUCCESS("=" * 65))

        ingested_count = 0
        skipped_count = 0

        for item in self.STARTER_SOURCES:
            src_md = bundle_dir / item["md_filename"]
            src_pdf = bundle_dir / item["pdf_filename"]

            if not src_md.exists() and not src_pdf.exists():
                self.stdout.write(
                    self.style.WARNING(f"  [Skip] Source files not found in {bundle_dir} for {item['key']}")
                )
                continue

            # Ensure both PDF and Markdown are copied to MEDIA_ROOT
            if src_pdf.exists():
                dest_pdf = media_starter_dir / item["pdf_filename"]
                if not dest_pdf.exists() or force:
                    shutil.copy2(src_pdf, dest_pdf)

            if src_md.exists():
                dest_md = media_starter_dir / item["md_filename"]
                if not dest_md.exists() or force:
                    shutil.copy2(src_md, dest_md)

            # Ingest from the Markdown file to preserve exact multi-level heading breadcrumbs
            chosen_file = f"starter_pack/{item['md_filename']}" if src_md.exists() else f"starter_pack/{item['pdf_filename']}"
            chosen_type = Source.SourceType.NOTE if src_md.exists() else Source.SourceType.PDF

            # Check if source already exists
            existing_source = Source.objects.filter(uri=item["uri"]).first()
            if existing_source and existing_source.status == Source.ProcessingStatus.COMPLETED and not force:
                self.stdout.write(
                    f"  [Cached] '{item['name']}' already ingested with {existing_source.documents.count()} document(s). Skipping."
                )
                skipped_count += 1
                continue

            metadata = {
                "subject": item["key"],
                "description": item["description"],
                "modules_count": item["modules_count"],
                "source": "CodeKairo CS Notes",
                "is_starter_pack": True,
                "pdf_filename": item["pdf_filename"],
                "pdf_url": f"/media/starter_pack/{item['pdf_filename']}",
                "has_pdf": src_pdf.exists(),
            }

            source = existing_source or Source.objects.create(
                name=item["name"],
                source_type=chosen_type,
                uri=item["uri"],
                file_path=chosen_file,
                metadata=metadata,
            )

            if existing_source:
                source.source_type = chosen_type
                source.file_path = chosen_file
                source.metadata = {**existing_source.metadata, **metadata}
                source.save(update_fields=["source_type", "file_path", "metadata"])

            self.stdout.write(f"\n-> Ingesting: {source.name}...")
            try:
                doc = IngestionPipeline.process_source(source.id)
                chunks_count = doc.chunks.count() if doc else 0
                headings_count = doc.chunks.filter(heading__gt="").values("heading").distinct().count() if doc else 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ✓ Ingested successfully: {chunks_count} chunks indexed ({headings_count} distinct section headings) with 384d vectors & Graph entities."
                    )
                )
                ingested_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ✗ Ingestion failed for {source.name}: {e}")
                )

        self.stdout.write(self.style.SUCCESS("-" * 65))
        self.stdout.write(
            self.style.SUCCESS(
                f"Summary: {ingested_count} newly ingested, {skipped_count} unchanged."
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 65))
