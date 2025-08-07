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
- Create Dataset
    - User Demo: 1 sop? 1 report? idk, what do i need to make the demo go smoothly and showcase the full power of the app?
        - For 2 accounts
        1. 1 annual report
        2. 2 simple 1 page quaterly reports
        3. 1 competitor annual report
    - Eval
        ```json
        [
            {
                "question_id": "TC001",
                "question": "What was the total revenue for MegaCorp in 2023?",
                "ground_truth_answer": "The total revenue for MegaCorp in 2023 was $45.2 million.",
                "ground_truth_context_ids": ["chunk_id_from_financial_highlights_table"],
                "expected_doc_id": "id_of_megacorp_annual_report_2023.pdf"
            },
        ```

- evaluate_rag.ipynb
    1. Context Precision: Of the chunks you retrieved, how many were actually relevant?
    2. Context Recall: Of the chunks you should have retrieved, how many did you actually get?
    3. Answer Correctness (LLM-as-a-Judge): This is a modern, effective technique. You ask a powerful LLM (like GPT-4 or Gemini 1.5 Pro) to rate the correctness of your agent's answer.
    4. Report Results: Calculate the averages and display them.

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