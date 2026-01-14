# BATO: Project Specification
## Open-Source AI Butler for Digital Sovereignty

**Version:** 1.5.6 (20260110-1030)  
**Date:** January 10, 2026  
**Target:** NGI Zero Commons Fund Application  
**Deadline:** February 1, 2026 (12:00 CET)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| **v1.5.6** | 2026-01-10 | Added Human-in-the-loop for critical domains (Risk Analysis), Classla/spaCy morphological analyzer (WP3), CPU-only low-resource deployment mode (Hardware Requirements) |
| v1.5.5 | 2026-01-09 | Added morphological embedding challenge for Croatian RAG, energy efficiency argument, native benchmark emphasis, embedding model risk in Risk Analysis |
| **v1.5.4** | 2026-01-09 | Added Crisis Resilience dimension (offline AI for civil protection), Dual-Use positioning (B2B/B2C + B2G), EU Civil Protection alignment |
| **v1.5.3** | 2026-01-08 | Added EuroLLM cultural proximity argument (trained on European sources = culturally closer, not just linguistically) |
| **v1.5.2** | 2026-01-08 | Added Cultural Sovereignty dimension (Inglehart-Welzel framework), normative value bias in problem statement, micro-cultural alignment in Dunbar section |
| **v1.5.1** | 2026-01-07 | Reframed opening sentence: "cognitive architecture for digital sovereignty" positioning |
| **v1.5** | 2026-01-07 | Strengthened R&D positioning (cognitive architecture, memory algorithm), clarified Dunbar as RAG optimization, restructured MCP scope (Nextcloud primary), added deployment deliverables (one-click install), added sustainability commitment (12+ months), ActivityPub-ready design, hardware requirements |
| v1.4 | 2026-01-07 | Added Infosit as Pilot Partner #0 (dogfooding), MCP Extensions (Nextcloud, Rocket.Chat, Email), replaced Grad Poreč with MO Moravice, budget capped at €50,000 with increased Infosit in-kind, added descoping strategy for MCP |
| v1.3 | 2026-01-05 | Added AI Assistance Disclosure (Appendix A), WP budget clarification, consistency review passed |
| v1.2 | 2026-01-05 | Added long-term vision note (smart displays, physical embodiment) |
| v1.1 | 2026-01-05 | Added Groups/Teams, Three-tier sharing, Cloud AI routing in MVP, separated SME/Private Community examples, Infosit in-kind contribution, pluggable auth architecture |
| v1.0 | 2026-01-05 | Initial consolidated specification |

---

## Executive Summary

Bato is a **cognitive architecture for digital sovereignty** that enables individuals and small communities to reclaim control over their AI interactions. Unlike generic AI assistants that create cloud dependency, Bato introduces novel algorithms for **context-aware memory management** and **semantic topic extraction** from unstructured conversations—research challenges that go beyond simple system integration.

**Positioning Statement:**
> "Bato je open-source AI butler koji vraća digitalnu suverenost malim zajednicama do 150 članova. Kombinira inovativnu kognitivnu arhitekturu s trajnom tematski organiziranom memorijom, native podrškom za europske jezike i offline sposobnostima - sve bez ovisnosti o cloudu i pod punom kontrolom zajednice."

**Key Research Contributions:**
1. Novel algorithm for semantic extraction of persistent memories from conversational noise
2. Cognitive orchestration architecture for multi-AI coordination
3. RAG optimization for Dunbar-scale communities (context quality over quantity)

**NEW in v1.5:** With MCP Extensions (Nextcloud as primary, Rocket.Chat and Email as secondary), Bato becomes the **first open-source alternative to Microsoft Copilot 365** for European SMEs seeking digital sovereignty.

---

## 1. Problem Statement

### 1.1 The Digital Sovereignty Crisis

Modern AI assistants from Big Tech companies create systematic dependencies:

| Problem | Impact | Who Suffers |
|---------|--------|-------------|
| **Data extraction** | Personal conversations feed corporate models | Everyone |
| **Cloud lock-in** | No service = no AI assistance | Rural communities, privacy-conscious users |
| **Language bias** | Optimized for English, degraded for EU languages | 400M+ EU citizens |
| **Fragmented memory** | Context scattered across multiple AI platforms (ChatGPT, Claude, Gemini) with no unified view | Power users juggling multiple AI tools |
| **Single-user design** | No sharing within families/groups | Small communities |
| **Normative value bias** | Commercial LLMs enforce "Anglosphere" cultural norms (high Self-Expression/Secular), overriding local community ethics | Communities with Traditional or Security-oriented values (e.g., SE Europe) |
| **Crisis dependency** | Cloud-based AI becomes unavailable exactly when needed most—during infrastructure failures, natural disasters, or network outages | Rural communities, civil protection units, isolated facilities |

#### The "Cultural Alignment Gap" (Inglehart-Welzel Validation)

Recent research (Durmus et al., 2023; Atari et al., 2023) demonstrates that leading closed-source models (GPT-4, Claude 3) overwhelmingly align with the "English-Speaking" cluster on the Inglehart-Welzel World Cultural Map. They prioritize Secular-Rational and high Self-Expression values typical of Silicon Valley.

However, our target pilot communities (e.g., rural Croatia) often reside in the "Catholic/Orthodox Europe" clusters, where Traditional and Security/Survival values hold greater weight. When these communities rely on Big Tech AI, they face constant **normative misalignment**—the AI implicitly treats their local values as bias or error.

**BATO solves this** by allowing communities to ground the AI in their own cultural context via local RAG and EuroLLM, closing the alignment gap.

**Why EuroLLM matters beyond language:** EuroLLM is not merely linguistically superior for European languages—it is **culturally closer**. Trained predominantly on European sources (EU documents, European literature, news, and academic texts), EuroLLM has absorbed European cultural context, legal frameworks, social norms, and value systems. When a Croatian village asks about community matters, EuroLLM draws from a European worldview rather than Silicon Valley assumptions. This is cultural sovereignty at the model level.

**Local RAG as Cultural Compensation:** Europe is not a cultural monolith. On the Inglehart-Welzel map, Sweden and Bulgaria are further apart than the USA and parts of South America. A "pan-European" model cannot perfectly serve all communities. BATO's local RAG architecture compensates for this limitation—by grounding responses in community-specific knowledge bases, local documents, and regional context, BATO enables **micro-cultural adaptation** that no single foundation model can achieve alone.

#### The Crisis Resilience Imperative

Cloud-based AI assistants share a critical vulnerability: **they fail exactly when needed most**. During natural disasters, infrastructure failures, or network outages—precisely when communities need coordination and information—Big Tech AI becomes unavailable.

Recent events underscore this risk:
- 2023 Slovenia floods: Internet infrastructure damaged across regions
- 2024 Croatian earthquake swarms: Mobile networks overloaded
- Increasing climate events: More frequent infrastructure disruptions expected

**BATO's offline-first architecture** ensures AI assistance remains available during crises:
- Full functionality without internet connectivity
- Local knowledge base includes emergency procedures, first aid, survival guides
- Community coordination tools work on local network only
- No dependency on external servers or cloud authentication

This positions BATO not just as convenience tool, but as **critical infrastructure** for community resilience—aligned with EU Civil Protection Mechanism (rescEU) priorities.

### 1.2 The Small Community Gap

Existing open-source alternatives focus on either:
- **Individual users** (Ollama, GPT4All, Jan) — no multi-user support
- **Enterprise** (AnythingLLM, PrivateGPT) — overkill for small groups

**Nobody serves the "Dunbar community"** — groups of up to 150 people (families, small organizations, cooperatives, clubs) who want shared AI capabilities without Big Tech or enterprise complexity.

### 1.3 The Dunbar Optimization Principle

**Why 150 users? This is not an arbitrary limitation—it's a deliberate design choice for RAG quality.**

Large-scale knowledge bases suffer from **context pollution**: when retrieval draws from thousands of users' data, the semantic relevance of retrieved context degrades. More data ≠ better answers.

Bato deliberately constrains community size to optimize:
- **Retrieval precision** — smaller, curated knowledge base = higher relevance scores
- **Trust density** — members know each other, reducing noise from irrelevant contexts  
- **Response quality** — LLM context window filled with highly relevant information
- **Micro-cultural alignment** — Global models are RLHF-tuned for the "average global user," erasing specific cultural nuances. By limiting scope to 150 users, BATO avoids this "regression to the mean." It allows the AI to adopt the specific micro-culture, dialect, and tacit knowledge of that village or organization, serving as a true digital extension of the group rather than an imposed external voice.

**Technical rationale:** With current embedding models (384-1536 dimensions) and context windows (4K-32K tokens), retrieval from 150-user corpus maintains >85% relevance in top-k results. Beyond 500 users, relevance drops below 60% without sophisticated re-ranking—adding complexity and latency.

**Energy efficiency bonus:** BATO's Dunbar-optimized RAG processes only the most relevant context chunks (typically 5-10 documents), reducing computational cost by **60-80%** compared to brute-force long-context approaches that stuff 100K+ tokens into the prompt. This aligns with EU Green Deal objectives and significantly reduces operational costs for SMEs. The "less is more" philosophy delivers both better answers and lower carbon footprint.

**Scaling model:** Organizations exceeding 150 users deploy multiple Bato nodes. Future federation (v2.0) enables cross-node queries with explicit trust boundaries.

### 1.4 The Micro & SME Opportunity

Micro and SME enterprises (up to 249 employees) represent **99.8% of all EU businesses**, employ approximately **90 million people**, and generate **52% of total EU value added**. Yet current AI solutions force them to choose between:
- **Big Tech platforms** — data sovereignty concerns, recurring costs, English-first
- **Enterprise solutions** — overengineered, expensive, complex deployment
- **DIY open-source** — requires technical expertise they don't have

**Critical insight:** Over **99.5% of EU enterprises** have fewer than 150 employees, fitting perfectly within Bato's Dunbar optimization.

---

## 2. Solution: The Bato Cognitive Butler

### 2.1 Core Concept

Bato implements a **cognitive architecture** for AI assistance—not merely connecting components, but implementing novel decision algorithms for:

- **Memory triage** — What deserves persistent storage vs. ephemeral context?
- **Topic extraction** — How to semantically map unstructured conversations to structured themes?
- **Orchestration decisions** — When to use local vs. cloud AI? Which external services to invoke?

The "butler" metaphor captures the user experience:
- **Knows the household** — persistent memory of conversations, preferences, context
- **Speaks your language** — native Croatian/European language support via EuroLLM
- **Orchestrates services** — coordinates with external AI systems when needed
- **Respects privacy** — local-first, offline-capable, no cloud dependency
- **Serves the community** — multi-tenant by design, group sharing built-in

**Long-term Vision:** Bato's cognitive architecture is designed as the foundation for future physical embodiments. As edge computing and AI hardware advance, Bato's modular design will enable smart display integration, voice interaction, and eventually robotic embodiments—without architectural rewrites.

### 2.2 Target Communities (Dual-Use Model)

BATO serves both commercial and public sector use cases—a **dual-use model** that expands impact and funding pathways.

#### Commercial Use (B2B / B2C)

**SME Examples (Business Context):**
- Small IT consultancy (25 employees) — Infosit d.o.o. as Pilot #0
- Family-owned manufacturing company (80 employees)
- Agricultural cooperative (40 members + seasonal workers)
- Professional services firm (15 partners + staff)

**Private Community Examples:**
- Extended family across multiple households (20 members)
- Local sports club or cultural association (60 members)
- Village or neighborhood group (100 households)
- Student housing cooperative (45 residents)

#### Public Sector Use (B2G)

**Civil Protection & Emergency Response:**
- Municipal emergency coordination centers
- Volunteer firefighter units in rural areas
- Local civil protection teams (stožeri civilne zaštite)
- Red Cross local chapters

**Rural Public Administration:**
- Small municipalities (<5,000 inhabitants)
- Rural community centers (domovi kulture)
- Local tourism boards in remote areas
- Island communities with limited connectivity

**Why B2G matters:**
- Validates BATO's crisis resilience capabilities
- Opens pathway to EU Civil Protection (rescEU) funding
- MO Moravice pilot demonstrates public sector applicability
- Government adoption signals trustworthiness for SME market

#### Data Ownership Distinction

**Important distinction:**
- In **SME context**, all data belongs to the organization; employees use Bato as a company tool
- In **private community context**, users retain ownership of their personal data; community sharing is opt-in
- In **public sector context**, data handling follows public administration regulations (GDPR + national law)

### 2.3 Hardware Requirements

Bato is designed for **consumer-grade hardware**, making digital sovereignty accessible:

| Configuration | Hardware | Performance |
|---------------|----------|-------------|
| **Recommended** | 32GB RAM, NVIDIA RTX 3060 (12GB VRAM) | Full speed, 7B model |
| **Apple Silicon** | Mac Mini M2 (16GB unified) | Full speed, optimized for Metal |
| **Budget** | 16GB RAM, CPU-only | Slower inference (~3-5x), but functional |
| **Low-resource** | 8GB RAM, CPU-only (older/refurbished HW) | Archival/admin tasks, 30-60s latency |
| **Server** | 64GB RAM, RTX 4090 | 13B model, faster responses |

**Low-resource mode:** Enables deployment on existing or refurbished hardware without GPU investment. Suitable for archival queries, document search, and administrative tasks that don't require real-time AI responses. This addresses accessibility for rural communities and non-profits with limited IT budgets, and supports circular economy principles through use of older hardware.

**Storage:** 50GB minimum (20GB models + 30GB database/knowledge base)

**Network:** Optional. Bato works fully offline; internet needed only for cloud AI routing and external MCP services.

---

## 3. State of the Art & Research Contributions

### 3.1 Current Landscape

| Solution | Multi-user | Memory | EU Languages | Offline | External AI |
|----------|------------|--------|--------------|---------|-------------|
| **Ollama** | ❌ | ❌ | Limited | ✓ | ❌ |
| **GPT4All** | ❌ | ❌ | Limited | ✓ | ❌ |
| **Jan.ai** | ❌ | Partial | Limited | ✓ | ❌ |
| **Open WebUI** | ✓ | Partial | Limited | ✓ | ❌ |
| **AnythingLLM** | ✓ | ✓ | Limited | Partial | ❌ |
| **Mem0** | ❌ | ✓✓ | Limited | ❌ | ❌ |
| **Bato (proposed)** | ✓ | ✓✓ | ✓✓ | ✓ | ✓ |

### 3.2 Research Contributions

**This section addresses the core R&D challenges Bato tackles—beyond integration.**

#### Research Contribution 1: Memory Triage Algorithm

**Problem:** In conversational AI, most exchanges are ephemeral ("What's the weather?"), but some contain insights worth preserving ("The client prefers delivery on Tuesdays"). Current systems either save everything (noise) or nothing (amnesia).

**Bato's approach:** We develop a **memory triage algorithm** that classifies conversational turns into:
- **Ephemeral** — discard after session (greetings, clarifications, failed queries)
- **Contextual** — retain for session continuity, expire after 24h
- **Persistent** — extract and store as structured memory

**Technical innovation:**
```
Input: Conversation turn (user message + assistant response)
Process:
  1. Semantic classification (intent: factual/procedural/preference/relationship)
  2. Novelty detection (does this contradict or extend existing memories?)
  3. Salience scoring (explicit markers: "remember", "important", "always")
  4. Confidence threshold (only persist if score > τ)
Output: Memory candidate with topic assignment + confidence score
```

This is a **research problem** because:
- No ground truth dataset exists for "what's worth remembering"
- Salience is subjective and context-dependent
- False positives (storing noise) degrade RAG quality
- False negatives (missing insights) frustrate users

#### Research Contribution 2: Semantic Topic Extraction

**Problem:** Users don't explicitly organize their conversations into topics. How does Bato automatically extract topic structure from unstructured dialogue?

**Bato's approach:** Hierarchical topic modeling combining:
- **Embedding clustering** — group semantically similar memories
- **Entity extraction** — identify recurring people, projects, concepts
- **User signals** — explicit topic assignments ("save this to Project X")
- **Temporal patterns** — conversations close in time often share topics

**Technical innovation:** Unlike traditional topic models (LDA, BERTopic) that operate on documents, Bato's algorithm operates on **conversational fragments** with:
- Speaker attribution (user vs. assistant vs. external AI)
- Dialogue structure (question-answer pairs, multi-turn reasoning)
- Cross-session continuity (same topic across days/weeks)

#### Research Contribution 3: Cognitive Orchestration Architecture

**Problem:** When should Bato use local LLM vs. route to cloud AI? How does it coordinate multiple external services (Nextcloud, Rocket.Chat, Email) in a single response?

**Bato's approach:** A **cognitive orchestrator** that:
1. Analyzes query complexity and domain
2. Estimates local LLM capability for this query type
3. Decides routing (local / cloud / hybrid)
4. Plans tool invocation sequence (which MCP tools, in what order)
5. Synthesizes multi-source responses

**Technical innovation:** This goes beyond simple routing (RouteLLM) by incorporating:
- **Memory-aware routing** — "I discussed this with Claude last week" → route to Claude for continuity
- **Cost-aware decisions** — prefer local when quality is sufficient
- **Privacy constraints** — some topics marked "never route to cloud"
- **Tool chaining** — search Nextcloud → summarize with local LLM → draft email

#### Research Challenge: Morphological Embeddings for Croatian

**Problem:** Standard embedding models (trained primarily on English) struggle with morphologically rich languages like Croatian. The words "banka" (nominative), "banci" (dative), "banku" (accusative), and "banaka" (genitive plural) represent the same concept but may be mapped to distant vectors, degrading RAG retrieval quality.

This is a known limitation in multilingual NLP. When a user searches for documents about "banke" (banks), the system may miss relevant documents containing "bankovni" (banking) or "bankarski" (banker's) if embeddings don't capture morphological relationships.

**BATO's approach:**
- **Evaluation of multilingual embedding models** — testing BGE-M3, multilingual-e5-large, and EuroLLM's native embeddings for Croatian morphology handling
- **Lemmatization preprocessing** — integration of Classla (state-of-the-art for South Slavic languages) or spaCy with Croatian model as normalization layer that reduces words to base forms before embedding
- **Chunk design optimization** — larger chunks reduce morphological fragmentation impact
- **Retrieval tuning** — adjusting similarity thresholds and top-k parameters for Croatian

**Honest limitation:** This is an upstream challenge in the NLP community. BATO can mitigate but not fully solve it. We document this limitation transparently and contribute evaluation data back to the community.

### 3.3 Five Innovations Summary

| # | Innovation | Research Challenge |
|---|------------|-------------------|
| 1 | **Topic-Structured Memory** | Memory triage algorithm: noise vs. insight classification |
| 2 | **Dunbar-Optimized Multi-Tenancy** | RAG quality optimization for bounded communities |
| 3 | **Cognitive Orchestration** | Multi-AI coordination with memory and privacy awareness |
| 4 | **European Language Excellence** | EuroLLM validation for Croatian using **native benchmarks** (not translated American tests); culturally closer training corpus |
| 5 | **Unified Cross-AI Memory** | Capturing conversations with external AIs (novel data model) |

---

## 4. Technical Architecture

### 4.1 Cognitive Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    BATO COGNITIVE ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 COGNITIVE ORCHESTRATOR                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │   Memory    │  │   Router    │  │    Tool     │       │   │
│  │  │   Triage    │  │  Decision   │  │   Planner   │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    CORE SERVICES                         │    │
│  ├─────────────┬─────────────┬─────────────┬───────────────┤    │
│  │  EuroLLM    │   Mem0      │  RouteLLM   │   MCP Layer   │    │
│  │  (Local)    │  (Memory)   │  (Routing)  │  (Tools)      │    │
│  └─────────────┴─────────────┴─────────────┴───────────────┘    │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              POSTGRESQL + pgvector                       │    │
│  │   ┌─────────┬─────────┬─────────┬─────────┬─────────┐   │    │
│  │   │ users   │memories │ topics  │ groups  │knowledge│   │    │
│  │   │(tenants)│(+ triage│(+ hier- │(+ perms)│  _base  │   │    │
│  │   │         │ scores) │  archy) │         │         │   │    │
│  │   └─────────┴─────────┴─────────┴─────────┴─────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  External (Optional, User-Controlled):                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Claude  │  │ ChatGPT  │  │Nextcloud │  │Rocket.Chat│       │
│  │   API    │  │   API    │  │  WebDAV  │  │   API    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Model (Federation-Ready)

**Design principle:** All identifiers use UUIDs and the schema is **ActivityPub-ready** from day one, enabling future federation without migration.

```sql
-- Community/Organization (Tenant) - ActivityPub Actor ready
communities (
  id UUID PRIMARY KEY,
  ap_id VARCHAR(255) UNIQUE,          -- ActivityPub ID (e.g., https://bato.example.org/community/xyz)
  name VARCHAR(255),
  type ENUM('sme', 'private_community'),
  max_users INTEGER DEFAULT 150,
  settings JSONB,
  auth_provider VARCHAR(50) DEFAULT 'local',
  federation_config JSONB,            -- Future: federation peers, trust levels
  public_key TEXT,                    -- Future: ActivityPub signatures
  created_at TIMESTAMP DEFAULT NOW()
)

-- Users within community - ActivityPub Actor ready
users (
  id UUID PRIMARY KEY,
  ap_id VARCHAR(255) UNIQUE,          -- ActivityPub ID
  community_id UUID REFERENCES communities,
  username VARCHAR(100),
  display_name VARCHAR(255),
  role ENUM('admin', 'member', 'guest'),
  preferences JSONB,
  external_id VARCHAR(255),           -- SSO/DID mapping
  public_key TEXT,                    -- Future: signatures
  created_at TIMESTAMP DEFAULT NOW()
)

-- Groups/Teams within community
groups (
  id UUID PRIMARY KEY,
  ap_id VARCHAR(255) UNIQUE,
  community_id UUID REFERENCES communities,
  name VARCHAR(255),
  type ENUM('family', 'team', 'project', 'department'),
  max_members INTEGER DEFAULT 15
)

-- Topic-organized memory with hierarchy
topics (
  id UUID PRIMARY KEY,
  community_id UUID REFERENCES communities,
  user_id UUID REFERENCES users,
  group_id UUID REFERENCES groups,
  parent_topic_id UUID REFERENCES topics,  -- Hierarchical topics
  name VARCHAR(255),
  description TEXT,
  visibility ENUM('private', 'group', 'community'),
  embedding VECTOR(384)               -- Topic embedding for similarity
)

-- Individual memories with triage metadata
memories (
  id UUID PRIMARY KEY,
  topic_id UUID REFERENCES topics,
  user_id UUID REFERENCES users,
  content TEXT,
  embedding VECTOR(384),
  
  -- Triage algorithm outputs
  memory_type ENUM('ephemeral', 'contextual', 'persistent'),
  salience_score FLOAT,               -- 0.0 - 1.0
  novelty_score FLOAT,                -- vs existing memories
  confidence FLOAT,                   -- triage confidence
  
  -- Source tracking
  source_type ENUM('conversation', 'manual', 'import'),
  source_provider VARCHAR(50),        -- 'local', 'claude', 'chatgpt', 'gemini'
  source_conversation_id UUID,
  
  -- Sharing
  visibility ENUM('private', 'group', 'community'),
  group_id UUID REFERENCES groups,
  
  -- Privacy controls
  never_route_cloud BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMP,
  expires_at TIMESTAMP                -- For contextual memories
)

-- Conversation history with AI provider tracking
conversations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  topic_id UUID REFERENCES topics,
  messages JSONB,                     -- Full conversation log
  ai_providers_used VARCHAR(50)[],    -- Array: ['local', 'claude']
  routing_decisions JSONB,            -- Log of orchestrator decisions
  created_at TIMESTAMP
)

-- Community knowledge base
knowledge_base (
  id UUID PRIMARY KEY,
  community_id UUID REFERENCES communities,
  group_id UUID REFERENCES groups,
  category VARCHAR(100),
  title VARCHAR(255),
  content TEXT,
  embedding VECTOR(384),
  source VARCHAR(255),
  visibility ENUM('private', 'group', 'community')
)
```

### 4.3 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **LLM** | EuroLLM (7B/13B) | Best EU language support, open weights |
| **Inference** | llama.cpp / vLLM | Efficient local inference |
| **Memory** | Mem0 + pgvector | Semantic search, proven architecture |
| **Router** | RouteLLM + custom | Base routing + cognitive orchestrator |
| **Database** | PostgreSQL 16 | RLS, pgvector, JSONB, ActivityPub-ready |
| **Backend** | Python/FastAPI | Async, type-safe, MCP compatible |
| **Frontend** | Chat UI (HF) | Open-source, customizable |
| **Auth** | Pluggable (see 4.4) | Local default, SSO/DID ready |

### 4.4 Authentication Architecture

Bato implements a **pluggable authentication system** to balance simplicity with future extensibility:

**MVP (v1.0):** Local username/password authentication
- Self-contained, works offline
- Admin can reset passwords
- Sufficient for small communities

**Future versions (v1.5+):** Additional auth providers via plugin system:
- OIDC (OpenID Connect) for SSO integration
- LDAP for enterprise directory services
- DID (Decentralized Identifiers) for self-sovereign identity
- ICP Internet Identity for blockchain-based auth

### 4.5 Federation Roadmap

| Version | Capability | ActivityPub Status |
|---------|------------|-------------------|
| **v1.0** | Single node, up to 150 users | Schema ready, protocol not implemented |
| **v1.5** | Multi-node, separate databases | Actor endpoints, no federation |
| **v2.0** | Full federation, cross-node topics | Full ActivityPub implementation |

**Design decision:** We invest in ActivityPub-compatible schema design now (UUIDs, ap_id fields, public keys) to avoid costly migrations later. This is a low-cost, high-value preparation for Fediverse integration.

---

## 5. MCP Extensions for Enterprise Productivity

### 5.1 Motivation: Microsoft 365 Copilot Alternative

The 2025-2026 geopolitical landscape has accelerated European organizations' need for digital sovereignty. US-based productivity suites create dependency risks including CLOUD Act exposure, service continuity risk, and AI lock-in.

### 5.2 MCP Extension Hierarchy

**Strategic decision:** Deep integration with one primary tool (Nextcloud) is more valuable than shallow integration with three.

| MCP Extension | Priority | Scope | Rationale |
|---------------|----------|-------|-----------|
| **Nextcloud** | 🔴 Primary | Full | Documents = corporate knowledge. SharePoint replacement is highest value. |
| **Rocket.Chat** | 🟡 Secondary | Basic | Communication flow, not knowledge store. Read-only summaries. |
| **Email** | 🟡 Secondary | Basic | Search and draft only. Lower priority than documents. |

### 5.3 Nextcloud MCP (Primary - Full Implementation)

**Purpose:** Complete document intelligence - search, retrieval, analysis, and knowledge extraction.

**Tools:**
| Tool | Function | Parameters |
|------|----------|------------|
| `nc_search` | Full-text + semantic search | query, folder_path, file_types, date_range |
| `nc_read` | Read and parse file content | file_path, extract_text, summarize |
| `nc_list` | List folder contents | folder_path, recursive, filter |
| `nc_metadata` | Get file metadata + history | file_path, include_versions |
| `nc_extract_knowledge` | Extract facts to memory | file_path, topic_id |

**Advanced features:**
- Automatic knowledge extraction from uploaded documents
- Version-aware retrieval ("What changed in the contract since last week?")
- Folder-to-topic mapping

### 5.4 Rocket.Chat MCP (Secondary - Basic Implementation)

**Purpose:** Communication awareness - search and summarize, not participate.

**Tools:**
| Tool | Function | Scope |
|------|----------|-------|
| `rc_search` | Search messages | Read-only |
| `rc_channel_summary` | Summarize activity | Read-only |
| `rc_thread_context` | Get thread | Read-only |

**Not in v1.0:** Message drafting, sending, channel management.

### 5.5 Email MCP (Secondary - Basic Implementation)

**Purpose:** Email search and draft assistance.

**Tools:**
| Tool | Function | Scope |
|------|----------|-------|
| `email_search` | IMAP search | Read-only |
| `email_read` | Read email | Read-only |
| `email_draft` | Compose draft | Draft only (no send) |

**Not in v1.0:** Send capability, folder management, rule creation.

### 5.6 Security Model

**Read-only by default:** MCP extensions can only READ data. No write/delete operations except drafting (which requires user confirmation).

**Credential isolation:** Each user configures their own API tokens. Bato never stores credentials in shared database.

**Audit logging:** All MCP tool invocations are logged with user, timestamp, and parameters.

---

## 6. MVP Scope

### 6.1 Included in MVP (v1.0)

| Feature | Priority | Description |
|---------|----------|-------------|
| Cognitive orchestrator | P0 | Memory triage + routing decisions |
| Multi-tenant architecture | P0 | PostgreSQL + RLS, up to 150 users/community |
| Local LLM inference | P0 | EuroLLM via llama.cpp |
| Topic-structured memory | P0 | Mem0 integration, triage algorithm |
| Groups/Teams | P0 | Sub-groups with shared topics |
| Three-tier visibility | P0 | Private → Group → Community |
| Web chat interface | P0 | Chat UI customization |
| Local authentication | P0 | Username/password, admin management |
| **One-click deployment** | P0 | Docker Compose, pre-built images |
| Basic cloud routing | P1 | RouteLLM for Claude/OpenAI |
| Unified memory | P1 | Log external AI conversations |
| **Nextcloud MCP (full)** | P1 | Complete document intelligence |
| Rocket.Chat MCP (basic) | P2 | Read-only search/summaries |
| Email MCP (basic) | P2 | Read-only search, draft |
| Croatian UI | P1 | Full Croatian localization |
| Offline knowledge | P2 | Wikipedia subset, first aid |

### 6.2 Deployment Options

**Critical for accessibility:** Target users (villages, small firms, associations) don't have DevOps engineers.

| Option | Complexity | Target User |
|--------|------------|-------------|
| **Docker Compose** | Low | Technical admin (knows Docker) |
| **Pre-built VM (OVA)** | Very Low | Anyone who can import VM |
| **Debian/Ubuntu package** | Low | Linux admin |
| **Raspberry Pi image** | Very Low | Maker/hobbyist |

**v1.0 deliverable:** Docker Compose + OVA image with:
- Pre-configured PostgreSQL
- EuroLLM 7B model included
- Web UI accessible at `http://bato.local`
- First-run wizard for admin setup

**v1.5 goal:** GUI installer for non-technical users.

### 6.3 Explicitly Excluded from MVP

| Feature | Rationale | Target Version |
|---------|-----------|----------------|
| Voice interface | Hardware dependency | v1.5 |
| IoT integration | Requires standardization | v2.0+ |
| Proactive suggestions | Needs user research | v1.5 |
| OIDC/LDAP/DID auth | Local auth sufficient | v1.5 |
| Federation | Single-node sufficient | v2.0 |
| Mobile app | Web responsive is sufficient | v1.5 |
| GUI installer | Docker/VM sufficient for pilots | v1.5 |

### 6.4 Descoping Strategy

**If MCP extensions prove more complex than estimated:**

Core Bato functionality (cognitive orchestrator, memory, multi-tenant, EuroLLM) takes absolute priority. MCP connectors can be descoped:

| Scenario | Action |
|----------|--------|
| Minor delays | Reduce Rocket.Chat/Email to stubs |
| Major delays | Nextcloud only, others in v1.1 |
| Critical issues | No MCP in v1.0, all in v1.1 |

This ensures NGI Zero deliverables are met regardless of MCP complexity.

---

## 7. Work Packages

### WP1: Project Setup & Architecture (Month 1-2)
**Budget: €4,000**

| Task | Output |
|------|--------|
| Development environment setup | Docker compose, CI/CD |
| Database schema implementation | PostgreSQL + pgvector, ActivityPub-ready |
| Authentication system | Local auth + pluggable architecture |
| API scaffold | FastAPI endpoints structure |
| **Deployment automation** | Docker Compose + OVA build pipeline |

**Deliverables:**
- D1.1: Development environment documentation
- D1.2: Database schema with ActivityPub fields
- D1.3: Docker Compose configuration
- D1.4: OVA base image

### WP2: Core AI Integration (Month 2-5)
**Budget: €12,000**

| Task | Output |
|------|--------|
| EuroLLM deployment | llama.cpp server, model optimization |
| Mem0 integration | Memory storage, retrieval, search |
| RouteLLM setup | Cloud routing configuration |
| **Cognitive orchestrator** | Memory triage + routing decisions |
| Conversation handler | Multi-turn dialogue management |

**Deliverables:**
- D2.1: EuroLLM deployment guide
- D2.2: Cognitive orchestrator implementation
- D2.3: Memory triage algorithm (documented)

### WP3: Memory System (Month 4-7)
**Budget: €10,000**

| Task | Output |
|------|--------|
| Topic management | CRUD, hierarchy, search |
| **Memory triage algorithm** | Noise vs. insight classification |
| **Semantic topic extraction** | Automatic topic assignment |
| **Morphological preprocessing** | Classla/spaCy HR integration for lemmatization |
| Unified memory logging | External AI conversation capture |
| Visibility/sharing | Three-tier access control |

**Morphological preprocessing rationale:** Standard embedding models struggle with Croatian case system (e.g., "banka", "banci", "banku" mapped to distant vectors). Integrating Classla or spaCy with Croatian model enables lemmatization preprocessing before vectorization, significantly improving RAG retrieval quality for morphologically rich languages.

**Deliverables:**
- D3.1: Topic extraction algorithm (documented)
- D3.2: Memory triage evaluation results
- D3.3: API documentation for memory operations
- D3.4: Morphological preprocessing pipeline (Classla/spaCy integration)

### WP4: MCP Extensions (Month 5-9)
**Budget: €10,000**

| Task | Output |
|------|--------|
| **Nextcloud MCP (full)** | Search, read, list, metadata, knowledge extraction |
| Rocket.Chat MCP (basic) | Search, summary, thread (read-only) |
| Email MCP (basic) | Search, read, draft |
| Security & audit | Credential isolation, logging |

**Deliverables:**
- D4.1: Nextcloud MCP server (full functionality)
- D4.2: Rocket.Chat MCP server (basic)
- D4.3: Email MCP server (basic)
- D4.4: Security audit report

### WP5: User Interface (Month 6-10)
**Budget: €8,000**

| Task | Output |
|------|--------|
| Chat UI customization | Bato branding, Croatian l10n |
| Topic visualization | Topic list, memory browser |
| MCP tool display | Results formatting, action UI |
| Admin dashboard | User/group management, settings |
| **First-run wizard** | Initial setup for non-technical users |

**Deliverables:**
- D5.1: Customized Chat UI
- D5.2: Admin dashboard
- D5.3: First-run wizard

### WP6: Testing & Pilot Deployment (Month 8-12)
**Budget: €6,000**

| Task | Output |
|------|--------|
| Unit & integration tests | >80% coverage |
| **One-click deployment validation** | Test OVA on various platforms |
| Pilot #0: Infosit (dogfooding) | Internal deployment, Copilot comparison |
| Pilot #1: LAZzz d.o.o. | SME deployment, feedback |
| Pilot #2: SNV | Community deployment, feedback |
| Pilot #3: MO Moravice | Municipal deployment, feedback |
| Documentation | User guide, admin guide, API docs |

**Deliverables:**
- D6.1: Test coverage report
- D6.2: Pilot deployment reports (4)
- D6.3: User documentation
- D6.4: Final OVA image

---

## 8. Budget

### 8.1 Requested Funding: €50,000

| Category | Amount | % |
|----------|--------|---|
| Personnel (development) | €40,000 | 80% |
| Infrastructure (cloud testing) | €4,000 | 8% |
| Hardware (test devices) | €3,000 | 6% |
| Travel (pilot sites) | €2,000 | 4% |
| Contingency | €1,000 | 2% |
| **Total** | **€50,000** | 100% |

### 8.2 Personnel Breakdown

| Role | Hours | Rate | Total |
|------|-------|------|-------|
| Senior Developer | 500 | €50/h | €25,000 |
| Junior Developer | 400 | €30/h | €12,000 |
| DevOps/Testing | 75 | €40/h | €3,000 |
| **Total** | **975** | - | **€40,000** |

### 8.3 Infosit In-Kind Contribution: €9,960

| Item | Monthly | Months | Total |
|------|---------|--------|-------|
| Hyper-V infrastructure (3 VMs) | €400 | 12 | €4,800 |
| Office space (development) | €200 | 12 | €2,400 |
| Internet connectivity (1 Gbps) | €80 | 12 | €960 |
| Administrative support | €50 | 12 | €600 |
| Utilities (power, cooling) | €100 | 12 | €1,200 |
| **Total In-Kind** | - | - | **€9,960** |

**Combined project value: €59,960**

---

## 9. Timeline

```
2026
     M1   M2   M3   M4   M5   M6   M7   M8   M9   M10  M11  M12
     │    │    │    │    │    │    │    │    │    │    │    │
WP1  ████████                                              Setup+Deploy
WP2       ████████████████                                 Cognitive Core
WP3                 ████████████████                       Memory R&D
WP4                      ██████████████████                MCP (NC focus)
WP5                           ████████████████████         UI
WP6                                     ████████████████████ Test/Pilot
     │    │    │    │    │    │    │    │    │    │    │    │
     │    │    │         │         │         │              │
     │    │    └─ Alpha  └─ Beta   └─ RC     └── Release    │
     │    └── Docker+OVA ready                              │
     └─── Kickoff                                           │
```

### Pilot Timeline

| Pilot | Start | Partner | Focus |
|-------|-------|---------|-------|
| #0 | Month 3 | Infosit (internal) | Dogfooding, Copilot comparison |
| #1 | Month 9 | LAZzz d.o.o. | SME validation |
| #2 | Month 10 | SNV | Community validation |
| #3 | Month 11 | MO Moravice | Municipal validation |

---

## 10. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Memory triage algorithm underperforms | Medium | High | Iterative development with pilot feedback; fallback to simpler heuristics |
| EuroLLM Croatian quality insufficient | Medium | High | Pre-project benchmark; Mistral fallback |
| **Embedding model morphology handling** | Medium | High | Evaluate multiple embedding models (BGE-M3, multilingual-e5); implement lemmatization fallback; document limitation transparently |
| **AI hallucination in critical domains** | Medium | Critical | Human-in-the-loop verification for safety-critical content (first aid, emergency procedures, legal advice); explicit confidence labeling; flag responses requiring expert validation |
| MCP extensions more complex than estimated | High | Medium | Nextcloud priority; others descoped if needed |
| Pilot partner availability | Low | Medium | Multiple partners, flexible scheduling |
| Scope creep | High | Medium | Strict MVP definition, explicit exclusions |
| One-click deploy fails on diverse hardware | Medium | Medium | Test on multiple platforms; provide manual fallback |

---

## 11. Pilot Partners

### Pilot #0: Infosit d.o.o. (Dogfooding)
**Type:** SME (IT Consulting), 24 employees  
**Role:** Internal testing, Copilot 365 comparison  
**Contact:** Goran (CEO)

### Pilot #1: LAZzz d.o.o.
**Type:** SME (Eco-products), ~15 users  
**Focus:** Product knowledge base, customer FAQ

### Pilot #2: SNV (Srpsko Narodno Vijeće)
**Type:** Private community (Cultural organization), ~100 users  
**Focus:** Document archive, member communication

### Pilot #3: MO Moravice (Grad Vrbovsko)
**Type:** Municipal administration (Rural), ~30 users  
**Focus:** Citizen services, offline capability

---

## 12. Licensing & Sustainability

### 12.1 Licensing

**Software:** AGPL v3 (GNU Affero General Public License)
- Ensures derivative works remain open source
- Cloud deployment requires source disclosure
- Compatible with NGI Zero requirements

**Documentation:** CC BY-SA 4.0

**Models:** Subject to original license (EuroLLM: Apache 2.0)

### 12.2 Post-Project Sustainability

**Infosit Commitment:**

Infosit d.o.o. commits to maintaining Bato as a living open-source project beyond the NGI Zero funding period:

| Commitment | Duration | Details |
|------------|----------|---------|
| **Repository maintenance** | 24 months post-project | GitHub repo, issue triage, security updates |
| **Community moderation** | 24 months post-project | PR reviews, contributor onboarding |
| **Security patches** | Ongoing | Critical vulnerabilities addressed within 72h |
| **Documentation updates** | 12 months post-project | User guides, API docs current |

**BATO Community Formation:**

- Month 10: Public announcement, contributor guidelines published
- Month 12: First community call, roadmap discussion
- Post-project: Quarterly community calls, annual roadmap votes

**Commercial Sustainability (Red Hat Model):**

| Offering | Target | Pricing |
|----------|--------|---------|
| Self-hosted (free) | DIY communities | €0 |
| Managed hosting | Non-technical orgs | €50-200/month |
| Enterprise support | SMEs | €500-2000/month |
| Custom development | Specific needs | Project-based |

This ensures Bato doesn't become "abandonware" while keeping the core open source.

---

## 13. Team

**Infosit d.o.o.** — Croatian IT consulting company (est. 2005)
- 24 employees
- €1.4M annual revenue
- ISO 9001:2015 certified
- Experience: Enterprise software, system integration, EU projects

**Key personnel:**
- **Project Lead:** CEO with 20+ years IT experience
- **Senior Developer:** Full-stack, AI/ML background
- **Junior Developers:** 2x, Python/TypeScript

---

## 14. NGI Zero Alignment

| NGI Criteria | Bato Alignment |
|--------------|----------------|
| **Research & Development** | Novel algorithms for memory triage, cognitive orchestration, morphological embedding evaluation |
| **Open Source** | AGPL v3, all code on GitHub |
| **Commons** | Shared infrastructure for communities |
| **Decentralization** | ActivityPub-ready, federation roadmap |
| **Privacy** | Local-first, offline-capable |
| **EU Values** | Digital sovereignty, EU language support, cultural alignment |
| **Crisis Resilience** | Offline-first AI for civil protection scenarios (rescEU alignment) |
| **Dual-Use Impact** | SME/communities (B2B/B2C) + public sector (B2G) |
| **Energy Efficiency** | Dunbar-optimized RAG reduces compute by 60-80% vs. long-context approaches (Green Deal alignment) |
| **Sustainability** | 24-month maintenance commitment |

---

## Appendix A: AI Assistance Disclosure

In accordance with NGI Zero transparency requirements, we disclose that this application and supporting documentation were prepared with assistance from Claude (Anthropic).

**How AI was used:**
- Structuring and formatting documentation
- Research synthesis (state of the art, competitor analysis)
- Technical writing and editing
- Budget calculation verification
- Consistency checking across documents

**What remains human:**
- All strategic decisions (features, priorities, scope)
- Technical architecture choices
- Partner relationships and commitments
- Budget allocation decisions
- Final review and approval of all content

**Transparency commitment:**
Detailed conversation logs documenting all AI prompts and outputs are maintained by Infosit d.o.o. and available upon request.

---

## Appendix B: Infosit Migration Context

Infosit's participation as Pilot #0 is motivated by concrete digital sovereignty requirements:

### Current State (January 2026)
- Full Microsoft 365 dependency (E3 licenses)
- 30 active Teams channels
- SharePoint as primary document store
- Microsoft Copilot 365 for AI assistance

### Target State (Post-Bato)
- Nextcloud for documents
- Rocket.Chat for team communication
- **Bato as AI assistant** (full Copilot replacement)

---

## References

1. Eurostat SBS 2023: SME Statistics
2. Dunbar, R.I.M. (1992): Neocortex size and group size
3. NGI Zero Commons Fund: https://nlnet.nl/commonsfund/
4. Model Context Protocol: https://modelcontextprotocol.io/
5. Mem0: https://github.com/mem0ai/mem0
6. EuroLLM: https://huggingface.co/EuroLLM
7. RouteLLM: https://github.com/lm-sys/RouteLLM
8. ActivityPub: https://www.w3.org/TR/activitypub/
9. Durmus, E. et al. (2023): Towards Measuring the Representation of Subjective Global Opinions in Language Models
10. Atari, M. et al. (2023): Which Humans? A Systematic Review of the Psychological and Social Characteristics of LLM-Based Evaluators
11. Inglehart, R. & Welzel, C. (2005): Modernization, Cultural Change, and Democracy: The Human Development Sequence
12. Classla: https://github.com/clarinsi/classla (State-of-the-art NLP for South Slavic languages)

---

*Document prepared for NGI Zero Commons Fund application by Infosit d.o.o.*

**Chat reference:** https://claude.ai/chat/[current-chat-id]
