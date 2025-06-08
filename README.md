# AI CFO Assistant: Technical Reference Guide
**Version:** 1.5

1. Problem: Are you solving a sufficiently painful, must-have problem?
    - No

2. Persona: Are you targeting the right users who feel this pain most acutely?
    - I dont even know who my users are

3. Promise: Is your value proposition clear and compelling to this persona?
    - No

4. Product: Is your solution effectively delivering on the promise for the problem and persona?
    - No

A reliable assistant for financial documents combining deterministic Python tools and an LLM.

## Contents
1. [Overview](#overview)
2. [Ingestion Pipeline](#ingestion-pipeline)
3. [Retrieval](#retrieval)
4. [Answer Generation & Tools](#answer-generation--tools)
5. [Output & Validation](#output--validation)
6. [Evaluation](#evaluation)
7. [Monitoring & Logging](#monitoring--logging)
8. [Next Steps](#next-steps)
9. [Strategy & Vision](#strategy--vision)
10. [Glossary](#glossary)

---

## Overview
- **Goal:** Accurate, auditable answers from financial documents.
- **Core:** Python-based calculation + LLM for context.
- **State:** Proof-of-Concept; API and evaluation partial; logging and re-ranking planned.

---

## Ingestion Pipeline
- Parse PDFs & text into structured AST-like nodes.
- Extract metadata and sections for indexing.

---

## Retrieval
- Semantic search for relevant text chunks.
- Future: advanced re-ranking and query decomposition.

---

## Answer Generation & Tools
- Strict prompts ensure clarity, grounding (*use only ingested text*), and graceful refusal.
- Offload numerical tasks to Python tools for transparency.

---

## Output & Validation
- Post-process LLM responses.
- Validate calculations against source data.
- Handle unanswerable queries with standard refusal.

---

## Evaluation
- Maintain a golden dataset of Q&A with ground-truth sections.
- Automate test runs and metric calculation.
- Key metrics: accuracy (numbers, sources), faithfulness, retrieval precision/recall, refusal correctness.
- Iterative loop: test → diagnose → fix → re-test.

---

## Monitoring & Logging
- Plan production logging of events, errors, and usage.
- Use Supabase (or similar) for audit trails.

---

## Next Steps
- Integrate with QuickBooks, cloud storage, email.
- Build dashboards and export (CSV/XLSX).
- Enhance table parsing, OCR for scanned docs.
- Improve error handling and model fine-tuning.

---

## Strategy & Vision
- Balance domain-specific reliability with general AI advances.
- Strengthen security, compliance, and specialized workflows to maintain trust and differentiation.

---

## Glossary
- **AST:** Structured representation of document sections.
- **RAG:** Retrieval-Augmented Generation.
- **Faithfulness:** Answers based only on retrieved context.
- **Semantic Search:** Embedding-based retrieval.
- **Supabase:** Backend-as-a-Service platform.
- **SSE:** Server-Sent Events for streaming.
- **Proof-of-Concept:** Early functional version for testing.