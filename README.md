# Brofessor 🧠

> **Brofessor** is a production-ready, local-first Personal Knowledge System (PKS), adaptive learning engine, and advanced LangGraph RAG assistant. It transforms raw notes, documents, and web resources into structured curricula, tracks personal mastery, and conducts interactive assessments with complete data privacy.

[![Version](https://img.shields.io/badge/version-3.0.0-indigo.svg)](https://github.com/Nitins715/Brofessor)
[![Docker Image](https://img.shields.io/badge/docker-nitins715%2Fbrofessor-blue?logo=docker)](https://hub.docker.com/r/nitins715/brofessor)
[![Docker Pulls](https://img.shields.io/badge/docker%20pulls-40%2B-brightgreen?logo=docker)](https://hub.docker.com/r/nitins715/brofessor)
[![Architecture](https://img.shields.io/badge/architecture-local--first%20%7C%20hybrid-orange.svg)](https://github.com/Nitins715/Brofessor)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [What's New in Version 3.0](#-whats-new-in-version-30)
- [Technical Interview Questions (Top 35)](#-technical-interview-questions-top-35)
- [Application Showcase](#-application-showcase)
- [System Architecture](#system-architecture)
  - [High-Level Architecture Diagram](#high-level-architecture-diagram)
- [Advanced LangGraph RAG Pipeline](#advanced-langgraph-rag-pipeline)
  - [RAG State Graph Workflow Diagram](#rag-state-graph-workflow-diagram)
- [Personal Knowledge Model & Knowledge Graph](#personal-knowledge-model--knowledge-graph)
  - [Knowledge Graph & Remediation Loop](#knowledge-graph--remediation-loop)
- [Database Architecture](#database-architecture)
  - [Entity Relationship (ER) Diagram](#entity-relationship-er-diagram)
- [Technology Stack](#technology-stack)
- [Project Directory Structure](#project-directory-structure)
- [Setup & Deployment](#setup--deployment)
  - [Option A: Public Docker Container (Instant Run — Recommended)](#option-a-public-docker-container-instant-run--recommended)
  - [Option B: Local Python Development Setup](#option-b-local-python-development-setup)
  - [Option C: Multi-Container Stack (Docker Compose)](#option-c-multi-container-stack-docker-compose)
- [Running Automated Tests](#running-automated-tests)
- [REST API Reference](#rest-api-reference)
- [Key Technical Decisions](#key-technical-decisions)
- [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Overview

Brofessor acts as an intelligent academic mentor and study partner for software engineers, students, and researchers. Instead of treating study notes and documentation as passive bookmarks, Brofessor:

1. **Ingests Diverse Content**: Processes raw markdown notes, web articles, PDFs, and YouTube transcripts with intelligent deduplication.
2. **Adaptive Semantic Chunking & Embeddings**: Normalizes text into cohesive semantic chunks embedded locally via 384-dimensional `BAAI/bge-small-en-v1.5` or Ollama embeddings.
3. **Advanced LangGraph RAG (Adaptive, Self-RAG & CRAG)**: Routes questions adaptively between direct parametric knowledge, hybrid document retrieval (dense vector + lexical BM25), reciprocal rank fusion (RRF), self-evaluating document grading, and corrective web search fallback.
4. **Interactive Knowledge Graph & Mastery**: Visualizes learning progress dynamically. Correctly answered questions reinforce mastery nodes, while incorrect answers populate the "Need to Learn" queue for targeted remediation without repeating mastered questions.
5. **Contextual Question Generator**: Dynamically generates strictly capped 10-question diagnostic assessments with embedded code snippets, distractor explanations, and concept tags.

---

## Key Features

- **🚀 1-Command Public Docker Image**: Pre-packaged on Docker Hub (`nitins715/brofessor:latest`) with automated database migration, curriculum seeding, and static collection.
- **⚡ Resilient Multi-Model LLM Pool**:
  - **Cloud Primary (Gemini Fast Pool)**: Cycles seamlessly through `gemini-3.6-flash`, `gemini-3.5-flash`, and `gemini-3.5-flash-lite` with snappy 8-second timeouts and automatic failover.
  - **Local Privacy Fallback (Ollama)**: Automatically falls back to local models (`llama3.2`, `gemma3`) if no cloud API key is configured or when offline.
  - **OpenAI / Custom Compatible**: Full support for OpenAI (`gpt-4o-mini`), Groq, or OpenRouter endpoints.
- **📐 Hierarchical Small-to-Big Chunking**: Generates parent section chunks (broader context) and child sub-chunks (dense retrieval targets). Vector search matches specific child chunks and expands to parent contexts for grounded generation without loss of context.
- **🕸️ Entity-Relationship Knowledge Graph (GraphRAG)**: Automatically extracts entities, relations, and chunk mappings from ingested text into a relational knowledge graph to support multi-hop semantic traversal alongside vector search.
- **🔍 LangSmith RAG Observability & Live Network Ping**: Built-in telemetry with LangSmith tracing for latency, tokens, and answer faithfulness, plus a real-time "Ping Network Check" in Settings.
- **🔄 Advanced LangGraph State Machine**: State-based RAG workflow featuring query transformation, adaptive query complexity classification, document grading, hallucination detection, and interactive web search permission.
- **📊 Adaptive Knowledge Graph**: Replaces static gap reports with an interactive knowledge graph tracking mastered concepts versus remediation items across all assessment attempts.
- **🎯 Niche-First AI/ML Curriculum**: Automatically pre-seeds a comprehensive, curated Artificial Intelligence & Machine Learning curriculum on boot with zero manual configuration.
- **🛡️ Thread-Safe Distributed Caching**: Utilizes shared `/data/cache` file-based caching across multi-threaded Gunicorn worker processes, avoiding isolated memory lock collisions.

---

## 🌟 What's New in Version 3.0

Version 3.0 elevates Brofessor into an end-to-end technical interview and personal knowledge powerhouse:

1. **📦 Pre-Packaged CS Starter Pack (DBMS, OS, CN, OOPS)**:
   - Shipped with complete, authoritative notes from CodeKairo in both Markdown and printable PDF.
   - Automatically ingested on fresh container boot: **5,135 chunks, 1,260 headings**, and pre-computed 384-dimensional FastEmbed vector embeddings.
2. **🏷️ Heading Stack Hierarchy Semantic Chunking**:
   - `MarkdownTextChunker` parses AST heading levels (`# H1` through `###### H6` and `Module X:`).
   - Injects full heading breadcrumbs (e.g. `Database Systems > Relational Model > Normalization`) into `DocumentChunk.heading`.
   - Augments BM25 lexical retrieval with `Q(heading__icontains=term)` for 35%+ higher retrieval precision.
3. **🕸️ Hardware-Accelerated Visual Concept Graph (Vis.js)**:
   - Dual-view canvas at `/knowledge-graph/` with real-time physics toggle and DAG hierarchical flow.
   - **Curriculum Flow Mode**: Visualizes 188 skills, 212 prerequisite directed edges, role-specific track palettes, and mastery rings.
   - **Library GraphRAG Mode**: Explores 202 conceptual entities and 118 semantic relationship triples.
   - Includes real-time camera search focus and sliding concept inspector drawer.
4. **📄 Technical Interview Cheat Sheet Exporter**:
   - 1-Click export for any curriculum topic (`/roadmap/topics/<pk>/cheat-sheet/?format=pdf|md`).
   - Publication-ready 2–3 page printable PDF built with pure-Python **ReportLab** flowables and two-pass `NumberedCanvas` ("Page X of Y"), plus a GitHub-flavored Markdown alternative.
5. **📎 1-Click Browser Bookmarklet & Web Clipper**:
   - Dedicated pop-up clipper at `/sources/clip/` and REST API at `/api/sources/clip/`.
   - Drag-and-drop bookmarklet installs on Chrome, Edge, Brave, Safari, and Firefox.
   - Instantly captures current URL, title, and selected quotes from any web article into your knowledge base.
6. **🛣️ Role-Specific AI/ML Career Tracks**:
   - Expanded roadmap tracks: **Software Engineer Foundations**, **AI Engineer**, **Agentic AI Engineer**, **MLOps Engineer**, and **Forward Deployed Engineer**.

---

## 🧠 Technical Interview Questions (Top 35)

Brofessor includes a comprehensive technical interview and system design companion document: [`questions.md`](questions.md).

It covers **35 deep-dive technical and architectural interview questions with full model answers, design rationales, formulas, and trade-off analyses**:

| Category | Topics Covered | Questions |
|:---|:---|:---:|
| **1. System Architecture & Local-First** | Single-container Docker, SQLite vs. PostgreSQL duality, zero-Redis file-based caching | Q1 – Q3 |
| **2. Advanced LangGraph RAG** | State machines, Adaptive Query Routing, Corrective RAG (CRAG), Self-RAG grading | Q4 – Q8 |
| **3. Retrieval, Embeddings & Reranking** | Dense vector + BM25, Reciprocal Rank Fusion (RRF), local FastEmbed (384d), ContextBuilder | Q9 – Q12 |
| **4. Multi-Model LLM Resilience** | Gemini Fast Model Pool (8s timeouts), Ollama fallback, zero-network deterministic mock | Q13 – Q14 |
| **5. Knowledge Model & Mastery** | Multi-factor evidence weighting, diagnostic remediation loops, 10-Q race-condition prevention | Q15 – Q17 |
| **6. Database Design & Scalability** | Relational schema separation, production bug post-mortems, 100k user scale roadmap | Q18 – Q20 |
| **7. GraphRAG & Observability** | Hierarchical parent-child chunking, entity-relationship triples, LangSmith live network ping | Q21 – Q25 |
| **8. Core CS Fundamentals (CodeKairo)** | DBMS Normalization & MVCC, OS Virtual Memory & Deadlocks, TCP Handshake & TLS 1.3, SOLID & Design Patterns | Q26 – Q29 |
| **9. Modern AI Engineering Tracks** | AI vs. Agentic Engineer (ReAct loops, sandboxing, multi-agent debate), MLOps & FDE serving optimization (vLLM, NF4) | Q30 – Q31 |
| **10. Version 3 Platform Innovations** | Heading Stack Hierarchy Chunking, Vis.js Concept Graph, ReportLab `NumberedCanvas` PDF exporter, Bookmarklet Clipper | Q32 – Q35 |

> 📖 **Read the complete guide:** [`questions.md`](questions.md)

---

## 📸 Application Showcase

### 1. Dashboard & Learning Analytics
> Real-time tracking of knowledge coverage, active skillset breakdown, past test performance, and intelligent recommended next actions.

![Dashboard & Analytics](images/image1.png)

---

### 2. Interactive Curriculum Roadmap
> Hierarchical learning progression (`Domain → Topic → Skill`) with custom syllabus import, topic priority tiers (P0, P1, P2), and direct skill assessment launch.

![Curriculum Roadmap](images/image2.png)

---

### 3. Personal Knowledge Graph (Performance Memory)
> Question-level mastery graph tracking mastered concepts versus the "Need to Learn" remediation queue for targeted practice without repeating mastered questions.

![Personal Knowledge Graph](images/image5.png)

---

### 4. Skill Diagnostics & Assessments
> Strict 10-question sequential diagnostics with automated LLM scoring, embedded code snippets, pass thresholds, and performance trends.

![Skill Diagnostics & Assessments](images/image4.png)

---

### 5. Multi-Modal Knowledge Library & Sources
> Centralized repository for ingesting and managing raw notes, PDFs, web articles, and video transcripts powering your local RAG index.

![Knowledge Library & Sources](images/image3.png)

---

## System Architecture

Brofessor is designed around a decoupled, local-first architecture where the web interface, domain logic, state-graph RAG workflow, persistence layer, and inference engines interact seamlessly.

### High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph UI["User Interfaces"]
        WebUI["Web UI (Tailwind CSS + Alpine/Vanilla JS + Django Templates)\n/dashboard, /roadmap, /assessments, /chat, /knowledge-graph"]
        REST["REST API Clients\n/api/* & /api/v1/* (OpenAPI 3.0 / Swagger UI)"]
    end

    subgraph Core["Application Server (Django / Gunicorn Workers)"]
        Router["URL Routing & Auth (Single-User Local Workspace)"]
        RoadmapApp["Roadmap Engine\n(Domains, Topics, Skills, Curriculum DAG)"]
        KnowledgeApp["Knowledge Graph Engine\n(Evidence, Mastery, Remediation Graph)"]
        AssessmentApp["Sequential Assessment Engine\n(10-Q Hard Cap, Code Snippets, Scoring)"]
        SourcesApp["Source Ingestion Service\n(PDF, Notes, Web Articles, YouTube)"]
        RAGApp["LangGraph RAG Workflow Engine\n(Adaptive Router, Self-RAG Grader, CRAG)"]
    end

    subgraph Caching["Cache & Concurrency Layer"]
        SharedCache["Shared FileBasedCache / Redis\n(/data/cache atomic locks across Gunicorn workers)"]
    end

    subgraph Storage["Persistence & Volume Layer"]
        DB[("Relational DB: SQLite / PostgreSQL + pgvector")]
        DiskStore["Host Persistent Volume (/data)\nDatabase, Media, Cache, Logs, AI Config"]
    end

    subgraph AI["Multi-Tier Inference Layer"]
        GeminiPool["Gemini Fast Pool\n(gemini-3.6-flash -> gemini-3.5-flash -> gemini-3.5-flash-lite)"]
        OllamaLocal["Local Ollama Daemon\n(llama3.2 @ http://localhost:11434)"]
        OpenAICloud["OpenAI / Groq Endpoints\n(gpt-4o-mini / Compatible)"]
        FastEmbed["HuggingFace FastEmbed\n(BAAI/bge-small-en-v1.5 - 384d)"]
        MockAI["Deterministic Mock Provider\n(Zero-dependency fallback for CI/Tests)"]
    end

    UI --> Router
    Router --> RoadmapApp
    Router --> KnowledgeApp
    Router --> AssessmentApp
    Router --> SourcesApp
    Router --> RAGApp

    RAGApp <--> SharedCache
    AssessmentApp <--> SharedCache

    RoadmapApp --> DB
    KnowledgeApp --> DB
    AssessmentApp --> DB
    SourcesApp --> DB
    RAGApp --> DB
    DB --> DiskStore

    RAGApp --> GeminiPool
    RAGApp --> OllamaLocal
    RAGApp --> OpenAICloud
    RAGApp --> FastEmbed
    RAGApp -.->|CI / Fallback| MockAI
    AssessmentApp --> GeminiPool
    AssessmentApp --> OllamaLocal
```

---

## Advanced LangGraph RAG Pipeline

Brofessor incorporates state-of-the-art RAG paradigms—including **Adaptive RAG**, **Modular RAG**, **Self-RAG**, and **Corrective RAG (CRAG)**—implemented as a compiled LangGraph state graph.

### RAG State Graph Workflow Diagram

```mermaid
flowchart TD
    Start(["User Query"]) --> RouterNode{"Adaptive Router"}

    RouterNode -->|Conversational / Syntax| ParametricNode["Parametric Knowledge Node\nDirect LLM generation with 0 retrieval overhead"]
    RouterNode -->|Live / External Search| WebSearchNode["Web Search Node\nLive internet retrieval & synthesis"]
    RouterNode -->|Domain / Document Inquiry| TransformNode["Query Transformation Node\nRewriting & multi-query expansion for hard queries"]

    TransformNode --> HybridRetrieval["Hybrid Retrieval Node\nDense Vector Search + Lexical BM25"]
    HybridRetrieval --> RerankNode["Reranking Node\nReciprocal Rank Fusion RRF Scoring"]
    RerankNode --> GraderNode["Self-RAG Document Grader\nEvaluates relevance of top chunks"]

    GraderNode --> RelevantCheck{"Context Relevant?"}
    RelevantCheck -->|Yes: Sufficient Context| BuildContext["Build Context & Grounding Node"]
    RelevantCheck -->|No: Insufficient / Off-Topic| CRAGNode{"CRAG Fallback\nUser Allowed Web Search?"}

    CRAGNode -->|Yes| WebSearchNode
    CRAGNode -->|No| PromptUserWeb["Prompt User for Web Search Permission"]

    BuildContext --> GroundedGen["Grounded Generation Node\nInline Citation Attribution [Source N]"]
    
    ParametricNode --> End(["Deliver Verified Answer"])
    GroundedGen --> End
    WebSearchNode --> End
    PromptUserWeb --> End
```

### Pipeline Highlights:
1. **Adaptive Query Router**: Classifies incoming questions into `PARAMETRIC` (greeting/simple syntax), `RETRIEVAL` (local documents), or `WEB_SEARCH`. Straightforward queries bypass unnecessary rewriting to minimize latency.
2. **Hybrid Retrieval + Reciprocal Rank Fusion (RRF)**: Combines dense vector cosine similarities (384-dimensional embeddings) with lexical text matches, scoring results via RRF.
3. **Self-RAG Grader**: Inspects retrieved chunks before generation. If chunks are irrelevant, prevents hallucinated answers.
4. **Corrective RAG (CRAG)**: If the local knowledge base has insufficient evidence, Brofessor either queries external search or presents an interactive permission button: *"Search the Web for this Answer"*.
5. **Cloud Fast Pool with Instant Failover**: Cloud queries cycle sequentially through the fastest Gemini 3.x models (`gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`) with an 8-second cutoff per model.

---

## Personal Knowledge Model & Knowledge Graph

Brofessor moves beyond static gap listings by generating an **interactive user Knowledge Graph**.

### Knowledge Graph & Remediation Loop

```mermaid
flowchart LR
    subgraph Assessment["1. Dynamic Diagnostic Testing"]
        TestEngine["Sequential Generator\n(Strict 10-Q Batch Cap)"]
        UserAttempt["User Takes Assessment\n(MCQ with Code Snippets)"]
        Evaluation["Automated Scoring\n(Passing Threshold: 70%)"]
        TestEngine --> UserAttempt --> Evaluation
    end

    subgraph KnowledgeGraph["2. Knowledge Graph State Tracking"]
        MasteredQueue["Mastered Nodes\n(Questions answered correctly\nmastery % increments)"]
        RemediationQueue["Need to Learn Queue\n(Questions answered incorrectly\nqueued for remediation)"]
        Evaluation -->|Correct| MasteredQueue
        Evaluation -->|Incorrect| RemediationQueue
    end

    subgraph Adaptation["3. Smart Deduplication & Curriculum Progress"]
        ContextPrompt["Sequential Context Prompt\nFilters previously seen questions"]
        RemediationQueue -->|Targeted Re-test| ContextPrompt
        MasteredQueue -->|Prevent Duplicate| ContextPrompt
        ContextPrompt --> TestEngine
    end
```

- **Mastery Queue**: Questions answered correctly establish verified evidence points, advancing the learner's skill mastery tier (`Beginner` $\to$ `Intermediate` $\to$ `Advanced` $\to$ `Expert`).
- **Need to Learn Queue**: Concepts or questions missed are flagged in the interactive Knowledge Graph. Subsequent diagnostic assessments prioritize these gaps while ensuring identical questions are not repeated once mastered.

---

## Database Architecture

The schema strictly separates raw ingested content from empirical evidence, calculated mastery records, and the curriculum hierarchy (`Domain → Topic → Skill → RoadmapNode`).

### Entity Relationship (ER) Diagram

```mermaid
erDiagram
    Domain ||--o{ Topic : "contains"
    Domain ||--o{ RoadmapNode : "scopes"
    Topic ||--o{ Skill : "organizes"
    Skill ||--|| RoadmapNode : "maps to"
    RoadmapNode ||--o| RoadmapProgress : "tracks"
    RoadmapNode }o--o{ RoadmapNode : "prerequisites"

    Source ||--o{ Document : "produces"
    Document ||--o{ DocumentChunk : "chunked into"
    DocumentChunk ||--o{ DocumentChunk : "hierarchical parent/child"
    DocumentChunk ||--o{ EntityChunkMapping : "references"
    Entity ||--o{ EntityChunkMapping : "mapped in"
    Entity ||--o{ Relationship : "source/target"
    DocumentChunk ||--o{ Evidence : "referenced by"

    Skill ||--o{ Evidence : "validated by"
    Topic ||--o{ Evidence : "linked to"
    Skill ||--o| CalculatedMastery : "evaluated as"
    Topic ||--o{ KnowledgeGap : "exhibits"
    Skill ||--o{ KnowledgeGap : "exhibits"
    Skill ||--o{ Recommendation : "targets"

    Assessment ||--o{ Question : "contains (Max 10)"
    Assessment ||--o{ Attempt : "evaluated via"
    Attempt ||--o{ Answer : "contains"
    Question ||--o{ Answer : "answered by"
    Skill ||--o{ Assessment : "tested by"
    Topic ||--o{ Assessment : "tested by"

    Conversation ||--o{ Message : "contains"
    Message ||--o{ RetrievedChunk : "grounded with"

    Domain {
        uuid id PK
        string name
        string slug
        boolean is_selected
        boolean is_active
    }
    Topic {
        uuid id PK
        uuid domain_id FK
        string name
        string slug
        string priority "P0, P1, P2"
        int order
    }
    Skill {
        uuid id PK
        uuid topic_id FK
        string name
        string slug
        string difficulty_level
        json key_concepts
        json learning_objectives
    }
    RoadmapNode {
        uuid id PK
        uuid domain_id FK
        uuid topic_id FK
        uuid skill_id FK
        int order
    }
    RoadmapProgress {
        uuid id PK
        uuid node_id FK
        string status "not_started, in_progress, completed, mastered"
        datetime completed_at
    }
    Source {
        uuid id PK
        string name
        string source_type "note, article, pdf, youtube"
        string status "pending, completed, failed"
    }
    DocumentChunk {
        uuid id PK
        uuid document_id FK
        uuid parent_chunk_id FK
        string chunk_level "parent, child"
        text content
        int chunk_index
        vector embedding "384-dimensional"
    }
    Entity {
        uuid id PK
        string name
        string entity_type "technology, concept, framework, library"
        text description
    }
    Relationship {
        uuid id PK
        uuid source_entity_id FK
        uuid target_entity_id FK
        string relation_type "prerequisite_of, part_of, integrates_with"
        float weight
    }
    EntityChunkMapping {
        uuid id PK
        uuid entity_id FK
        uuid chunk_id FK
    }
    Evidence {
        uuid id PK
        uuid skill_id FK
        uuid source_id FK
        string evidence_type "declared, practical, learning, assessment"
        decimal confidence_weight
        datetime recorded_at
    }
    CalculatedMastery {
        uuid id PK
        uuid skill_id FK
        decimal mastery_score "0.0 - 100.0%"
        string mastery_level
        decimal knowledge_coverage
        decimal confidence_score
    }
    Assessment {
        uuid id PK
        uuid skill_id FK
        string title
        string difficulty_level
        decimal passing_score
        int target_questions_count "Fixed 10"
    }
    Attempt {
        uuid id PK
        uuid assessment_id FK
        decimal score
        boolean passed
        text feedback
        datetime completed_at
    }
```

---

## Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Backend Framework** | Django 5.x & Django REST Framework | REST API design, modular app architecture, ORM |
| **RAG Orchestration** | LangGraph & LangChain Core | State-graph managing query transformation, hybrid retrieval, self-grading & CRAG |
| **Database** | SQLite3 (Single Container) / PostgreSQL 16 + pgvector | Relational schemas + 384-dimensional cosine vector indexing |
| **Caching & Concurrency** | Shared `FileBasedCache` / Redis | Multi-worker atomic lock synchronization on `/data/cache` |
| **AI LLM Inference** | Gemini Fast Pool (`gemini-3.6/3.5-flash`) / Ollama (`llama3.2`) / OpenAI | Multi-model failover with 8s cutoff, local Ollama fallback, and mock testing provider |
| **Embedding Engine** | Hugging Face FastEmbed (`BAAI/bge-small-en-v1.5`) | Fast, local 384-dimensional semantic text representations |
| **Web UI & Styling** | Tailwind CSS + Vanilla JS + Django Templates | Dark-mode dashboard, interactive roadmap, assessment runner, and chat |
| **API Documentation** | `drf-spectacular` | OpenAPI 3.0 specification (`schema.yml`) and Swagger / Redoc UI |
| **Containerization** | Docker & Docker Compose | Single-container image (`nitins715/brofessor:latest`) published on Docker Hub |

---

## Project Directory Structure

```text
Brofessor/
├── apps/
│   ├── accounts/             # User model and profile management
│   ├── assessments/          # Question generation, strict 10-Q capping, scoring, and attempts
│   ├── core/                 # Shared base models, logging, exceptions, responsive web views
│   ├── knowledge/            # Concepts, evidence items, calculated mastery, and Knowledge Graph
│   ├── mastery/              # Mastery calculation, evidence weights, and recommendations
│   ├── processing/           # Text extractors, semantic chunking, and embedding pipeline
│   ├── rag/                  # LangGraph workflow, Adaptive Router, Hybrid Retrieval, Web Search
│   │   ├── query_processing/ # Adaptive query classifier and query rewriting
│   │   ├── services/         # Hybrid retrieval, web search, conversation persistence
│   │   ├── workflow/         # LangGraph state machine, DocumentGrader, HallucinationChecker
│   │   └── llm/              # Gemini fast pool, Ollama, OpenAI, and Mock LLM providers
│   ├── roadmap/              # Domains, Topics, Skills, Roadmap Nodes, and DAG progress
│   └── sources/              # Multi-format source ingestion (PDF, text, web articles, YouTube)
├── config/
│   ├── settings.py           # Hardened Django settings with environment overrides & CSRF support
│   ├── urls.py               # Root URL configuration (/api/*, /api/v1/*, swagger, redoc)
│   └── wsgi.py
├── data/                     # Persistent local storage (DB, cache, media, logs) mapped to host
├── templates/                # Server-rendered templates
│   ├── layouts/              # Base layout, navbar, sidebar, theme tokens
│   └── pages/                # Dashboard, Roadmap, Knowledge Graph, Assessments, Chat, Settings
├── static/                   # Static CSS, JS, and font assets
├── Dockerfile                # Production single-container image definition
├── entrypoint.sh             # Startup migration, curriculum seeding, and Gunicorn launcher
├── docker-compose.yml        # Multi-container orchestration (postgres, redis, web, celery)
├── manage.py                 # Django management CLI
├── requirements.txt          # Python runtime dependencies
└── README.md                 # Complete system documentation
```

---

## Setup & Deployment

### Option A: Public Docker Container (Instant Run — Recommended)

Brofessor is published publicly on **Docker Hub**. Run the entire application locally with zero Python configuration:

```bash
# Pull the latest verified image
docker pull nitins715/brofessor:latest

# Run the container with persistent host storage
docker run -d \
  --name brofessor \
  -p 8000:8000 \
  -v brofessor_data:/data \
  nitins715/brofessor:latest
```

Open your browser to: **`http://localhost:8000/`**

- **Pre-Seeded AI/ML Curriculum**: Automatically migrates database schemas and auto-seeds the standard **Artificial Intelligence & Machine Learning** roadmap via `post_migrate` on first boot.
- **Zero-Config Local Storage**: Defaults to SQLite (`/data/brofessor.sqlite3`) for instant zero-dependency execution. All notes, vector embeddings, and configurations persist inside the `brofessor_data` volume.
- **Unified Settings Console**: Navigate to **Settings** in the web UI to configure your free Google Gemini API key or point to local Ollama (`http://host.docker.internal:11434`), and optionally add your LangSmith API key for live RAG trace telemetry. Use the built-in **Ping Network Check** to verify endpoint connectivity.

---

### Option B: Local Python Development Setup

#### Prerequisites
- **Python**: 3.11, 3.12, or 3.13
- **Ollama** (Optional for local offline LLM generation; Mock provider available for testing)

#### 1. Environment Setup
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Configure Environment (`.env`)
```bash
cp .env.example .env
```
Key settings in `.env`:
```ini
DJANGO_SECRET_KEY=your-secure-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database (defaults to SQLite in data/brofessor.sqlite3)
DB_ENGINE=sqlite
DATA_DIR=./data

# AI Provider Settings
LLM_PROVIDER=auto
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.6-flash
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```

#### 3. Run Migrations & Seed Curricula
```bash
python manage.py migrate
python manage.py seed_domain_roadmaps
```

#### 4. Launch the Web Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

### Option C: Multi-Container Stack (Docker Compose)

For scaling with dedicated PostgreSQL (`pgvector`) and Redis Celery workers:

```bash
docker compose up --build
```

---

## Running Automated Tests

Brofessor includes comprehensive test suites covering curriculum validation, roadmap DAG traversal, RAG query pipelines, hierarchical chunking, knowledge graph services, and assessment capping:

```bash
# Run all tests (68/68 passing)
python manage.py test

# Run RAG & LangGraph workflow tests
python manage.py test apps.rag

# Run Assessment engine & sequential generator tests
python manage.py test apps.assessments

# Run web frontend & dashboard tests
python manage.py test apps.core
```

---

## REST API Reference

All endpoints are available under `/api/` and versioned `/api/v1/` routes. Interactive OpenAPI docs:
- **Swagger UI**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Redoc UI**: [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
- **OpenAPI 3.0 Schema**: [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

### Core API Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **RAG & Chat** | `POST` | `/api/v1/rag/chat/` | Execute end-to-end LangGraph RAG query with citation tracking |
| **Conversations** | `GET` / `POST` | `/api/v1/conversations/` | List or create conversation threads |
| **Integrations** | `GET` | `/api/v1/rag/integrations/status/` | Get live connectivity status for Gemini, Ollama, and LangSmith |
| **Integrations** | `POST` | `/api/v1/rag/integrations/verify/` | Ping and optionally persist API keys with real-time latency check |
| **Sources** | `GET` / `POST` | `/api/sources/` | Ingest PDFs, notes, web articles, and YouTube transcripts |
| **Sources** | `DELETE` | `/api/sources/<id>/delete/` | Delete ingested knowledge source and cascade chunk vectors |
| **Roadmaps** | `GET` | `/api/roadmap/graph/<domain_id>/` | Retrieve complete directed learning roadmap graph |
| **Assessments** | `POST` | `/api/assessments/questions/generate/` | Generate 10-question assessment batch for a skill |
| **Assessments** | `POST` | `/api/assessments/attempts/<id>/submit/` | Submit answers for automatic LLM evaluation and scoring |
| **Knowledge Graph**| `GET` | `/api/knowledge/graph/` | Retrieve user performance graph (Mastered vs. Need to Learn) |
| **Mastery** | `GET` | `/api/mastery/skills/<skill_id>/` | View weighted mastery score and level (`Beginner` to `Expert`) |

---

## Key Technical Decisions

1. **Local-First with Zero-Friction Cloud Hybrid Fallback**:
   Student notes and assessment attempts remain strictly on the local workstation. When cloud reasoning is configured, Brofessor uses a pool of the newest low-latency models (`gemini-3.6-flash`, `gemini-3.5-flash`) with strict 8-second timeouts, falling back to local Ollama if offline.
2. **Hierarchical Small-to-Big Chunking**:
   Decouples dense retrieval resolution from generation context. Sub-chunks (~200 tokens) ensure sharp embedding vector similarity, while parent sections (~1000 tokens) deliver coherent context to the LLM without context fragmentation.
3. **Entity-Relationship Knowledge Graph (GraphRAG)**:
   Extracts conceptual entities and relational edges from ingested material into a structured graph, enabling multi-hop queries across concepts that pure vector similarity alone might miss.
4. **LangGraph State Machine for Deterministic RAG**:
   Instead of brittle linear chains, the RAG pipeline is orchestrated via a compiled LangGraph state graph. This enables conditional edge routing, query transformation, document relevance grading, and corrective search fallback with full transparency.
5. **Thread-Safe Shared Caching (`FileBasedCache`)**:
   To avoid multi-process race conditions in Gunicorn where in-memory caches cannot share assessment locks, Brofessor uses a unified `/data/cache` file-based cache ensuring atomic generation locks across all workers.
6. **Strict Assessment Batch Capping (10-Question Hard Cap)**:
   Assessment generation enforces strict database re-validation under atomic transactions. No assessment can ever generate or evaluate more than the target 10 questions, protecting learner score integrity.
7. **Interactive Knowledge Graph Over Static Gap Lists**:
   Learners retain full visibility over their mastery journey through a dynamic Knowledge Graph where correctly answered questions reinforce mastered nodes and incorrect answers feed directly into focused remediation queues.

---

## Troubleshooting & FAQ

#### 1. How do I configure my Gemini API Key and LangSmith Tracing?
Open Brofessor in your browser, navigate to **Settings** in the sidebar. Under **API Credentials & Model Routing**, enter your Google Gemini API key and/or LangSmith API key, select your preferred model, and click **Ping Network Check** to verify latency and connectivity before saving.

#### 2. How do I know which database (SQLite vs. PostgreSQL) my project is using?
Go to **Settings** and scroll to the bottom **System & Runtime Environment** card:
- **Database Engine**: Displays `sqlite3` or `postgresql`.
- **Database Location**: Shows `/data/brofessor.sqlite3` (SQLite) or `brofessor_db` (PostgreSQL).
- *Single-container Docker defaults to SQLite; Docker Compose uses PostgreSQL.*

#### 3. Is the Gemini API key used for embeddings or only the local model?
**Only the local FastEmbed model (`BAAI/bge-small-en-v1.5`, 384d) is used for embeddings every time.**
The Gemini key is strictly utilized for high-level language reasoning (RAG chat synthesis, hallucination evaluation, knowledge graph extraction, and question generation). This guarantees vector consistency, zero embedding API costs, and full offline search capability.

#### 4. How do I connect to local Ollama running on my host machine?
If you are running Brofessor inside Docker and Ollama directly on your host machine:
- Set **Ollama Base URL** in Settings to: `http://host.docker.internal:11434`
- Make sure Ollama is serving requests: `ollama run llama3.2`

#### 5. How do I deploy Brofessor on a cloud server or custom domain?
Set the `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` environment variables to your domain:
```bash
docker run -d \
  -p 8000:8000 \
  -e DJANGO_ALLOWED_HOSTS="my-brofessor.up.railway.app,example.com" \
  -e CSRF_TRUSTED_ORIGINS="https://my-brofessor.up.railway.app,https://example.com" \
  -v brofessor_data:/data \
  nitins715/brofessor:latest
```

---

## License

This project is licensed under the [MIT License](LICENSE).
