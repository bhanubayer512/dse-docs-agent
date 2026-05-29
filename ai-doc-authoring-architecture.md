# AI-Driven Automated Document Authoring System
## Engineering Workflow Integration — Architecture

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                        AI-DRIVEN AUTOMATED DOCUMENT AUTHORING SYSTEM                                ║
║                              Engineering Workflow Integration                                        ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  TRIGGER LAYER  — What kicks off the pipeline                                                       │
│                                                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────┐ │
│   │  PR Merged   │    │ ADO Story /  │    │  Scheduled   │    │  Manual Trigger                  │ │
│   │  to main /   │    │ Task moves   │    │  Nightly     │    │  (Dev invokes from CLI / Portal) │ │
│   │  release     │    │ to "Done"    │    │  Batch Run   │    │                                  │ │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └───────────────┬──────────────────┘ │
│          └───────────────────┴───────────────────┴────────────────────────────┘                    │
│                                           │                                                         │
│                                    [Event Bus / Webhook]                                            │
│                                    Azure Service Bus / GitHub Actions Webhook                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  DATA INGESTION LAYER  — Pulling raw context from engineering sources                               │
│                                                                                                     │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────────────────┐ │
│  │   ADO BOARD CONNECTOR │   │   GIT / REPO CONNECTOR│   │       PR CONNECTOR                    │ │
│  │                       │   │                       │   │                                       │ │
│  │  • User Stories       │   │  • Commit messages    │   │  • PR title & description             │ │
│  │  • Tasks & Sub-tasks  │   │  • Commit diffs       │   │  • Reviewer comments                  │ │
│  │  • Acceptance criteria│   │  • File change summary│   │  • Review decisions                   │ │
│  │  • Story points       │   │  • Branch lineage     │   │  • Linked work items                  │ │
│  │  • Tags & Area paths  │   │  • Author metadata    │   │  • PR labels & milestones             │ │
│  │  • Sprint / iteration │   │  • Timestamps         │   │  • Squash/merge metadata              │ │
│  │                       │   │                       │   │                                       │ │
│  │  [Azure DevOps REST]  │   │  [GitHub / ADO Git    │   │  [GitHub GraphQL API /                │ │
│  │                       │   │   REST API]           │   │   ADO REST API]                       │ │
│  └───────────┬───────────┘   └───────────┬───────────┘   └─────────────────┬─────────────────────┘ │
│              └───────────────────────────┴──────────────────────────────────┘                      │
│                                          │                                                          │
│                               [Context Aggregator]                                                 │
│                    Correlates: Story ↔ Commits ↔ PR ↔ Code Changes                                │
│                    Produces a unified "Feature Snapshot" JSON payload                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE BASE / CONTEXT STORE  — Long-term memory the agent reads before writing                 │
│                                                                                                     │
│  ┌─────────────────────────┐   ┌─────────────────────────┐   ┌───────────────────────────────────┐ │
│  │  USER CONTEXT LIBRARY   │   │  ENGINEERING STANDARDS  │   │  PREVIOUS DOCS CORPUS             │ │
│  │                         │   │                         │   │                                   │ │
│  │  • Existing user-facing │   │  • API naming rules     │   │  • Prior release notes            │ │
│  │    documentation        │   │  • Architecture docs    │   │  • Past feature guides            │ │
│  │  • User personas        │   │  • Coding conventions   │   │  • Changelog history              │ │
│  │  • Glossary (user terms │   │  • System design ADRs   │   │  • Indexed via vector embeddings  │ │
│  │    vs tech terms)       │   │  • Security guidelines  │   │    (semantic similarity search)   │ │
│  │  • UX/UI patterns       │   │                         │   │                                   │ │
│  │  • Support ticket themes│   │  [Confluence / Wiki /   │   │  [Azure Blob + Vector DB          │ │
│  │                         │   │   Markdown in repo]     │   │   e.g. Azure AI Search /          │ │
│  │  [Curated doc store]    │   │                         │   │   Pinecone / pgvector]            │ │
│  └──────────┬──────────────┘   └───────────┬─────────────┘   └──────────────────┬────────────────┘ │
│             └───────────────────────────────┴──────────────────────────────────  │                  │
│                                          RAG RETRIEVAL                            │                  │
│                          (Retrieve top-K relevant chunks per feature snapshot)   │                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  AI AGENT CORE  — The Document Authoring Brain                                                      │
│                                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                        ORCHESTRATOR AGENT  (Claude / GPT-4o / Azure OpenAI)                 │   │
│  │                                                                                             │   │
│  │   INPUT CONTEXT ASSEMBLY:                                                                   │   │
│  │   ┌──────────────────────────────────────────────────────────────────────────────────────┐  │   │
│  │   │  Feature Snapshot  +  RAG chunks (user docs)  +  RAG chunks (eng docs)  +  Persona   │  │   │
│  │   └──────────────────────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                                             │   │
│  │   PERSONA ROUTER:                                                                           │   │
│  │   ┌────────────────────────────┐       ┌────────────────────────────┐                      │   │
│  │   │  USER-FACING MODE          │       │  ENGINEERING MODE          │                      │   │
│  │   │                            │       │                            │                      │   │
│  │   │  System prompt emphasizes: │       │  System prompt emphasizes: │                      │   │
│  │   │  • Plain language          │       │  • Technical precision     │                      │   │
│  │   │  • "What does this mean    │       │  • Implementation details  │                      │   │
│  │   │    for ME as a user?"      │       │  • API changes, schemas    │                      │   │
│  │   │  • Benefit-driven writing  │       │  • Dependency impact       │                      │   │
│  │   │  • No jargon               │       │  • Migration guides        │                      │   │
│  │   │  • Task-oriented (How-To)  │       │  • Architecture decisions  │                      │   │
│  │   └────────────────────────────┘       └────────────────────────────┘                      │   │
│  │                                                                                             │   │
│  │   SUB-AGENTS / TOOLS CALLED BY ORCHESTRATOR:                                               │   │
│  │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │   │
│  │   │ Story Analyst│ │ Code Diff    │ │ Tone & Style │ │ Consistency  │ │ Screenshot /   │  │   │
│  │   │ Sub-Agent    │ │ Summarizer   │ │ Enforcer     │ │ Checker      │ │ Diagram Gen    │  │   │
│  │   │              │ │ Sub-Agent    │ │ Sub-Agent    │ │ Sub-Agent    │ │ Sub-Agent      │  │   │
│  │   │ Extracts     │ │              │ │              │ │              │ │                │  │   │
│  │   │ intent from  │ │ Translates   │ │ Matches      │ │ Checks doc   │ │ Generates      │  │   │
│  │   │ acceptance   │ │ raw diffs to │ │ brand voice  │ │ doesn't      │ │ Mermaid/       │  │   │
│  │   │ criteria     │ │ plain impact │ │ & reading    │ │ contradict   │ │ PlantUML       │  │   │
│  │   │              │ │ statements   │ │ level        │ │ existing docs│ │ diagrams       │  │   │
│  │   └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                     │
│  DRAFT OUTPUT:  Structured Markdown / JSON doc payload per audience                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  REVIEW & APPROVAL GATE  — Human in the loop before publishing                                      │
│                                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                              │  │
│  │   Draft PR created in Docs repo  ──►  Reviewers assigned (Tech Writer / PM / Dev Lead)      │  │
│  │                                                                                              │  │
│  │   ┌─────────────────────────┐        ┌──────────────────────────────────────────────────┐  │  │
│  │   │  AUTO-CHECKS (CI)       │        │  HUMAN REVIEW PORTAL                             │  │  │
│  │   │                         │        │                                                  │  │  │
│  │   │  • Spell / grammar check│        │  • Side-by-side diff view (old doc vs new doc)  │  │  │
│  │   │  • Reading level score  │        │  • Inline comment → agent re-generates section  │  │  │
│  │   │  • Broken link check    │        │  • Approve / Request Changes / Reject            │  │  │
│  │   │  • Terminology validator│        │  • One-click "Regenerate this section"           │  │  │
│  │   │    (user glossary match) │        │                                                  │  │  │
│  │   │  • Duplicate content    │        │  (Web portal or PR comments trigger agent loop)  │  │  │
│  │   │    detection            │        │                                                  │  │  │
│  │   └─────────────────────────┘        └──────────────────────────────────────────────────┘  │  │
│  │                                                                                              │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                            ┌───────────────┴───────────────┐
                            │         APPROVED               │
                            ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  DELIVERY LAYER  — Publishing to the right audience                                                 │
│                                                                                                     │
│  ┌──────────────────────────────────────┐    ┌──────────────────────────────────────────────────┐  │
│  │   USER-FACING OUTPUT                 │    │   ENGINEERING-FACING OUTPUT                      │  │
│  │                                      │    │                                                  │  │
│  │  ┌──────────────────────────────┐    │    │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Help Center / Docs Portal   │    │    │  │  Internal Wiki / Confluence                │  │  │
│  │  │  (e.g., Zendesk, Mintlify,   │    │    │  │  (auto-published page with version tag)    │  │  │
│  │  │   Docusaurus, GitBook)       │    │    │  └────────────────────────────────────────────┘  │  │
│  │  └──────────────────────────────┘    │    │  ┌────────────────────────────────────────────┐  │  │
│  │  ┌──────────────────────────────┐    │    │  │  GitHub / ADO Repo — CHANGELOG.md          │  │  │
│  │  │  In-app Tooltips / Callouts  │    │    │  │  auto-committed to release branch          │  │  │
│  │  │  (Feature flag aware —       │    │    │  └────────────────────────────────────────────┘  │  │
│  │  │   shows only for users with  │    │    │  ┌────────────────────────────────────────────┐  │  │
│  │  │   access to new feature)     │    │    │  │  API Reference Docs (OpenAPI / Swagger)    │  │  │
│  │  └──────────────────────────────┘    │    │  │  auto-updated from code annotations        │  │  │
│  │  ┌──────────────────────────────┐    │    │  └────────────────────────────────────────────┘  │  │
│  │  │  Release Notes Email /       │    │    │  ┌────────────────────────────────────────────┐  │  │
│  │  │  In-app notification         │    │    │  │  ADO Wiki — linked back to original Story  │  │  │
│  │  └──────────────────────────────┘    │    │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────┘    └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  FEEDBACK & LEARNING LOOP  — The system gets smarter over time                                      │
│                                                                                                     │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │  User Feedback Signals │  │  Review Edit Tracking  │  │  Model Fine-Tuning / Prompt Tuning   │  │
│  │                        │  │                        │  │                                      │  │
│  │  • Was this helpful?   │  │  • Track every human   │  │  • Store (draft → approved) pairs    │  │
│  │    👍 / 👎 on articles  │  │    edit made during    │  │  • Periodic fine-tune or few-shot    │  │
│  │  • Support ticket       │  │    review              │  │    prompt update to reduce           │  │
│  │    deflection rate      │  │  • Feed diffs back     │  │    reviewer edits over time          │  │
│  │  • Search queries that  │  │    into prompt         │  │                                      │  │
│  │    hit no results       │  │    improvement loop    │  │                                      │  │
│  └────────────────────────┘  └────────────────────────┘  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════════════════════════
                              DATA FLOW SUMMARY — End to End
═══════════════════════════════════════════════════════════════════════════════════════════════════════

  ADO Story "Done"
       │
       ├──[ADO Connector]──► User Story + Acceptance Criteria
       ├──[Git Connector]───► Commit history scoped to story branch
       ├──[PR Connector]────► PR details, diffs, reviewer comments
       │
       └──► Context Aggregator ──► Feature Snapshot
                                         │
                              ┌──────────┴──────────┐
                              │   RAG Retrieval      │
                              │   (user docs corpus  │
                              │   + eng standards)   │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   Orchestrator Agent │
                              │   + Persona Router   │
                              └──────────┬──────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          │                             │
                   [User Draft]                 [Eng Draft]
                          │                             │
                   ┌──────▼─────────────────────────────▼──────┐
                   │           Review & Approval Gate           │
                   └──────────────────┬─────────────────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                   [User Docs Portal]    [Internal Wiki / CHANGELOG]


═══════════════════════════════════════════════════════════════════════════════════════════════════════
                                   KEY TECHNOLOGY CHOICES
═══════════════════════════════════════════════════════════════════════════════════════════════════════

  Layer                  │ Recommended Stack
  ───────────────────────┼──────────────────────────────────────────────────────────────────
  Orchestration          │ LangGraph / AutoGen / Azure AI Agent Service
  LLM                    │ Claude 3.5 Sonnet / Azure OpenAI GPT-4o
  Vector DB / RAG        │ Azure AI Search + pgvector  OR  Pinecone
  Event Bus              │ Azure Service Bus / GitHub Actions / ADO Pipelines
  ADO Integration        │ Azure DevOps REST API + Webhooks
  Git Integration        │ GitHub API v4 (GraphQL) / ADO Git REST API
  Docs Delivery          │ Mintlify / Docusaurus / Confluence REST API
  Review Portal          │ Custom Next.js thin UI  OR  PR-based review in ADO/GitHub
  Secret / Config        │ Azure Key Vault
  Observability          │ Azure Monitor + LangSmith (LLM traces)
```

---

## Key Design Decisions Explained

### 🧠 Dual Persona Architecture
The agent doesn't just write one doc — it **routes through two system prompts** based on audience. The
**user-facing prompt** is seeded with the existing user documentation corpus via RAG, so the agent
naturally mirrors the tone, terminology, and structure users already recognize. The **engineering
prompt** pulls from ADRs, architecture docs, and coding standards.

### 🔗 Story ↔ Commit ↔ PR Correlation
The **Context Aggregator** is the critical linchpin. It joins data by:
- Story ID in commit messages / branch names
- Work item links in PR descriptions
- ADO-GitHub integration tags

This ensures the agent only synthesizes signals **relevant to that feature**, not the entire repo
history.

### 🔄 Human-in-the-Loop is Non-Negotiable
The review gate prevents hallucinated or inaccurate docs from shipping. Crucially, **every human
correction is logged** — this becomes training signal to reduce future edits over time.

### 📚 RAG over Fine-Tuning (initially)
Grounding the agent in your **existing user documentation** via RAG is faster and safer than
fine-tuning. The feedback loop then tells you *when* fine-tuning is worth the investment.
