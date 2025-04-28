# AI CFO Assistant: Technical Reference Guide

## Table of Contents

*   [Chapter 1: Introduction](#chapter-1-introduction)
    *   [1.1 Project Overview](#11-project-overview)
    *   [1.2 The Problem: Financial Insight Bottleneck for SMEs](#12-the-problem-financial-insight-bottleneck-for-smes)
    *   [1.3 The Solution: AI CFO Assistant](#13-the-solution-ai-cfo-assistant)
    *   [1.4 Core Design Philosophy: Reliability First](#14-core-design-philosophy-reliability-first)
    *   [1.5 Key Objectives](#15-key-objectives)
    *   [1.6 Scope Definition](#16-scope-definition)
        *   [1.6.1 In Scope](#161-in-scope)
        *   [1.6.2 Out of Scope](#162-out-of-scope)
    *   [1.7 High-Level Technology Stack (Flexible Description)](#17-high-level-technology-stack-flexible-description)
    *   [1.8 Document Purpose & Audience](#18-document-purpose--audience)
*   [Chapter 2: System Architecture](#chapter-2-system-architecture)
    *   [2.1 Architectural Overview (RAG + Function Calling)](#21-architectural-overview-rag--function-calling)
    *   [2.2 Core Pipeline Stages Diagram](#22-core-pipeline-stages-diagram)
    *   [2.3 Component Descriptions](#23-component-descriptions)
        *   [2.3.1 PDF Parser (Multimodal LLM)](#231-pdf-parser-multimodal-llm)
        *   [2.3.2 Markdown Formatter & Metadata Extractor](#232-markdown-formatter--metadata-extractor)
        *   [2.3.3 Semantic Chunker (Heading-Based)](#233-semantic-chunker-heading-based)
        *   [2.3.4 Embedding Generator (Embedding Service API)](#234-embedding-generator-embedding-service-api)
        *   [2.3.5 Vector Store (Postgres + pgvector Compatible)](#235-vector-store-postgres--pgvector-compatible)
        *   [2.3.6 Query Decomposer (LLM)](#236-query-decomposer-llm)
        *   [2.3.7 Metadata Filter](#237-metadata-filter)
        *   [2.3.8 Vector Retriever](#238-vector-retriever)
        *   [2.3.9 Cross-Encoder Re-ranker](#239-cross-encoder-re-ranker)
        *   [2.3.10 Context Assembler](#2310-context-assembler)
        *   [2.3.11 Calculation Tool Executor](#2311-calculation-tool-executor)
        *   [2.3.12 Generator & Function Calling Orchestrator (Large Context LLM)](#2312-generator--function-calling-orchestrator-large-context-llm)
        *   [2.3.13 Post-processor & Validator](#2313-post-processor--validator)
        *   [2.3.14 Citation Generator](#2314-citation-generator)
        *   [2.3.15 Logging Service](#2315-logging-service)
    *   [2.4 Data Flow](#24-data-flow)
        *   [2.4.1 Ingestion Flow](#241-ingestion-flow)
        *   [2.4.2 Query Flow (Simple Query)](#242-query-flow-simple-query)
        *   [2.4.3 Query Flow (Complex Query with Calculation)](#243-query-flow-complex-query-with-calculation)
*   [Chapter 3: Data Ingestion & Processing](#chapter-3-data-ingestion--processing)
    *   [3.1 Input Format: Financial PDFs](#31-input-format-financial-pdfs)
    *   [3.2 Parsing with Multimodal LLM API](#32-parsing-with-multimodal-llm-api)
        *   [3.2.1 API Interaction](#321-api-interaction)
        *   [3.2.2 Prompting for Structured Output](#322-prompting-for-structured-output)
        *   [3.2.3 Handling Layouts and Tables](#323-handling-layouts-and-tables)
        *   [3.2.4 Error Handling & Rate Limits](#324-error-handling--rate-limits)
    *   [3.3 Structuring Output: Markdown + YAML Front Matter](#33-structuring-output-markdown--yaml-front-matter)
        *   [3.3.1 Standard Metadata Schema (YAML)](#331-standard-metadata-schema-yaml)
        *   [3.3.2 Markdown Formatting Conventions](#332-markdown-formatting-conventions)
        *   [3.3.3 Mapping Content to Page Numbers (Challenge)](#333-mapping-content-to-page-numbers-challenge)
    *   [3.4 Semantic Chunking Strategy](#34-semantic-chunking-strategy)
        *   [3.4.1 Primary Split: Markdown Headings](#341-primary-split-markdown-headings)
        *   [3.4.2 Handling Large Sections](#342-handling-large-sections)
            *   [3.4.2.1 Recursive Splitting Logic](#3421-recursive-splitting-logic)
            *   [3.4.2.2 Maintaining Parent Section Linkage](#3422-maintaining-parent-section-linkage)
        *   [3.4.3 Chunk Representation](#343-chunk-representation)
*   [Chapter 4: Embedding & Storage](#chapter-4-embedding--storage)
    *   [4.1 Embedding Strategy: Context-Awareness](#41-embedding-strategy-context-awareness)
        *   [4.1.1 Embedding Model Selection Criteria](#411-embedding-model-selection-criteria)
        *   [4.1.2 Metadata Prepending Technique](#412-metadata-prepending-technique)
        *   [4.1.3 Implementation via Embedding Service API](#413-implementation-via-embedding-service-api)
            *   [4.1.3.1 API Call Structure](#4131-api-call-structure)
            *   [4.1.3.2 Batching Considerations](#4132-batching-considerations)
    *   [4.2 Vector Database Selection (Postgres + pgvector Compatible)](#42-vector-database-selection-postgres--pgvector-compatible)
        *   [4.2.1 Rationale for Choice (Serverless, Compatibility)](#421-rationale-for-choice-serverless-compatibility)
        *   [4.2.2 Enabling `pgvector`](#422-enabling-pgvector)
    *   [4.3 Database Schema Design](#43-database-schema-design)
        *   [4.3.1 `documents` Table](#431-documents-table)
        *   [4.3.2 `sections` Table](#432-sections-table)
        *   [4.3.3 `embeddings` Table](#433-embeddings-table)
        *   [4.3.4 `query_logs` Table](#434-query_logs-table)
        *   [4.3.5 Relationships (ERD Diagram)](#435-relationships-erd-diagram)
    *   [4.4 Indexing Strategy](#44-indexing-strategy)
        *   [4.4.1 Vector Indexing (HNSW on `embedding_vector`)](#441-vector-indexing-hnsw-on-embedding_vector)
        *   [4.4.2 Metadata Indexing (GIN on `metadata` JSONB)](#442-metadata-indexing-gin-on-metadata-jsonb)
        *   [4.4.3 Standard Indexes (FKs, IDs)](#443-standard-indexes-fks-ids)
    *   [4.5 Data Insertion Process](#45-data-insertion-process)
        *   [4.5.1 Orchestration Script](#451-orchestration-script)
        *   [4.5.2 Transaction Management](#452-transaction-management)
*   [Chapter 5: Retrieval Pipeline](#chapter-5-retrieval-pipeline)
    *   [5.1 Overview of Retrieval Goals](#51-overview-of-retrieval-goals)
    *   [5.2 Query Decomposition (for Complex Queries)](#52-query-decomposition-for-complex-queries)
        *   [5.2.1 Triggering Decomposition](#521-triggering-decomposition)
        *   [5.2.2 LLM Model & Prompting for Decomposition](#522-llm-model--prompting-for-decomposition)
        *   [5.2.3 Handling Sub-query Execution](#523-handling-sub-query-execution)
    *   [5.3 Query Analysis & Metadata Extraction](#53-query-analysis--metadata-extraction)
        *   [5.3.1 Identifying Entities (Dates, Report Types)](#531-identifying-entities-dates-report-types)
        *   [5.3.2 Methods (Regex, Keywords, LLM Call)](#532-methods-regex-keywords-llm-call)
    *   [5.4 Metadata Filtering](#54-metadata-filtering)
        *   [5.4.1 Constructing SQL `WHERE` Clauses](#541-constructing-sql-where-clauses)
        *   [5.4.2 Querying `sections.metadata` JSONB](#542-querying-sectionsmetadata-jsonb)
    *   [5.5 Vector Search](#55-vector-search)
        *   [5.5.1 Query Embedding](#551-query-embedding)
        *   [5.5.2 Using `pgvector` Similarity Operators](#552-using-pgvector-similarity-operators)
        *   [5.5.3 Retrieving Top K Candidates](#553-retrieving-top-k-candidates)
    *   [5.6 Hybrid Search Considerations (Future)](#56-hybrid-search-considerations-future)
        *   [5.6.1 Need for Keyword Search (Specific Terms)](#561-need-for-keyword-search-specific-terms)
        *   [5.6.2 Integration Options (BM25, FTS)](#562-integration-options-bm25-fts)
        *   [5.6.3 Result Fusion (RRF)](#563-result-fusion-rrf)
    *   [5.7 Re-ranking with Cross-Encoders](#57-re-ranking-with-cross-encoders)
        *   [5.7.1 Rationale: Enhancing Top-K Relevance](#571-rationale-enhancing-top-k-relevance)
        *   [5.7.2 Re-ranker Model Selection Criteria](#572-re-ranker-model-selection-criteria)
        *   [5.7.3 Process: Re-ranking Full Parent Sections](#573-process-re-ranking-full-parent-sections)
        *   [5.7.4 Implementation (`sentence-transformers` or API)](#574-implementation-sentence-transformers-or-api)
    *   [5.8 Final Context Selection](#58-final-context-selection)
*   [Chapter 6: Generation & Function Calling](#chapter-6-generation--function-calling)
    *   [6.1 Generator Model Selection (Large Context LLM)](#61-generator-model-selection-large-context-llm)
        *   [6.1.1 Rationale (Context Window, Function Calling Capability)](#611-rationale-context-window-function-calling-capability)
    *   [6.2 Context Assembly for Prompting](#62-context-assembly-for-prompting)
        *   [6.2.1 Including Metadata](#621-including-metadata)
        *   [6.2.2 Including Full Re-ranked Section Text](#622-including-full-re-ranked-section-text)
        *   [6.2.3 Formatting and Delimiters](#623-formatting-and-delimiters)
    *   [6.3 Prompt Engineering for Reliability](#63-prompt-engineering-for-reliability)
        *   [6.3.1 Core Principles (Clarity, Specificity)](#631-core-principles-clarity-specificity)
        *   [6.3.2 Persona Setting](#632-persona-setting)
        *   [6.3.3 Strict Context-Only Constraints (CRITICAL INSTRUCTION)](#633-strict-context-only-constraints-critical-instruction)
        *   [6.3.4 Graceful Refusal Instruction](#634-graceful-refusal-instruction)
        *   [6.3.5 Citation Requirements](#635-citation-requirements)
        *   [6.3.6 Tool Usage Instructions](#636-tool-usage-instructions)
        *   [6.3.7 Few-Shot Examples (Recommended)](#637-few-shot-examples-recommended)
            *   [6.3.7.1 Example: Successful Contextual Answer + Citation](#6371-example-successful-contextual-answer--citation)
            *   [6.3.7.2 Example: Correct Refusal When Info Absent](#6372-example-correct-refusal-when-info-absent)
            *   [6.3.7.3 Example: Tool Use for Calculation](#6373-example-tool-use-for-calculation)
    *   [6.4 Defining Calculation Tools](#64-defining-calculation-tools)
        *   [6.4.1 Identifying Necessary Tools (Sum, Avg, Ratio, Change %)](#641-identifying-necessary-tools-sum-avg-ratio-change-)
        *   [6.4.2 Implementing Tools as Python Functions](#642-implementing-tools-as-python-functions)
            *   [6.4.2.1 Input/Output Definitions](#6421-inputoutput-definitions)
            *   [6.4.2.2 Error Handling (Division by Zero, Type Errors)](#6422-error-handling-division-by-zero-type-errors)
        *   [6.4.3 Creating Tool Schemas (JSON for LLM API)](#643-creating-tool-schemas-json-for-llm-api)
    *   [6.5 Function Calling Orchestration](#65-function-calling-orchestration)
        *   [6.5.1 Initial LLM API Call (with Tools)](#651-initial-llm-api-call-with-tools)
        *   [6.5.2 Handling `function_call` Response](#652-handling-function_call-response)
        *   [6.5.3 Executing the Local Python Tool](#653-executing-the-local-python-tool)
        *   [6.5.4 Sending `function_response` Back to LLM](#654-sending-function_response-back-to-llm)
        *   [6.5.5 Receiving the Final Natural Language Answer](#655-receiving-the-final-natural-language-answer)
*   [Chapter 7: Post-processing & Attribution](#chapter-7-post-processing--attribution)
    *   [7.1 Answer Clean-up](#71-answer-clean-up)
        *   [7.1.1 Removing Extraneous Prefixes/Suffixes](#711-removing-extraneous-prefixessuffixes)
        *   [7.1.2 Standardizing Formatting](#712-standardizing-formatting)
    *   [7.2 Basic Validation Checks](#72-basic-validation-checks)
        *   [7.2.1 Numerical Cross-Referencing (Heuristic)](#721-numerical-cross-referencing-heuristic)
            *   [7.2.1.1 Extracting Numbers from Response](#7211-extracting-numbers-from-response)
            *   [7.2.1.2 Checking Presence in Cited Context](#7212-checking-presence-in-cited-context)
            *   [7.2.1.3 Limitations](#7213-limitations)
        *   [7.2.2 Checking for Refusal Message](#722-checking-for-refusal-message)
    *   [7.3 Citation Generation](#73-citation-generation)
        *   [7.3.1 Identifying Used Context Sections](#731-identifying-used-context-sections)
        *   [7.3.2 Mapping Section IDs to Document Metadata](#732-mapping-section-ids-to-document-metadata)
        *   [7.3.3 Standard Citation Format](#733-standard-citation-format)
*   [Chapter 8: Evaluation Framework](#chapter-8-evaluation-framework)
    *   [8.1 Evaluation Philosophy: Proving Reliability](#81-evaluation-philosophy-proving-reliability)
    *   [8.2 Source Data: Synthetic Financial PDFs](#82-source-data-synthetic-financial-pdfs)
        *   [8.2.1 Creation Method (Excel/Sheets -> PDF Recommended)](#821-creation-method-excelsheets---pdf-recommended)
        *   [8.2.2 Content & Structure Guidelines](#822-content--structure-guidelines)
        *   [8.2.3 Timeframe & Volume](#823-timeframe--volume)
    *   [8.3 Golden Dataset Creation](#83-golden-dataset-creation)
        *   [8.3.1 Structure Per Entry (Query, Ideal Answer, Ground Truth Chunks/Sections, Numerical Values)](#831-structure-per-entry-query-ideal-answer-ground-truth-chunkssections-numerical-values)
        *   [8.3.2 Query Type Coverage](#832-query-type-coverage)
        *   [8.3.3 Including Cases Requiring Refusal (CRITICAL)](#833-including-cases-requiring-refusal-critical)
        *   [8.3.4 Manual Verification & Annotation Guideline](#834-manual-verification--annotation-guideline)
    *   [8.4 Metrics Definitions & Implementation](#84-metrics-definitions--implementation)
        *   [8.4.1 Numerical Accuracy (Exact Match + Normalization)](#841-numerical-accuracy-exact-match--normalization)
        *   [8.4.2 Faithfulness (LLM-as-judge Methodology & Prompt)](#842-faithfulness-llm-as-judge-methodology--prompt)
        *   [8.4.3 Attribution Accuracy (Precision/Recall/F1 of Citations)](#843-attribution-accuracy-precisionrecallf1-of-citations)
        *   [8.4.4 Retrieval Performance (Precision@K, Recall@K, MRR)](#844-retrieval-performance-precisionk-recallk-mrr)
        *   [8.4.5 Refusal Accuracy (Did it refuse correctly?)](#845-refusal-accuracy-did-it-refuse-correctly)
    *   [8.5 Automated Evaluation Script (`evaluate.py`)](#85-automated-evaluation-script-evaluatepy)
        *   [8.5.1 Input: Golden Dataset, System Endpoint/Functions](#851-input-golden-dataset-system-endpointfunctions)
        *   [8.5.2 Process: Run Queries, Collect Responses, Calculate Metrics](#852-process-run-queries-collect-responses-calculate-metrics)
        *   [8.5.3 Output: Metrics Report (CSV, JSON, or Formatted Text)](#853-output-metrics-report-csv-json-or-formatted-text)
    *   [8.6 Evaluation Strategy: Baseline & Iteration](#86-evaluation-strategy-baseline--iteration)
*   [Chapter 9: Implementation Details & Configuration](#chapter-9-implementation-details--configuration)
    *   [9.1 Core Technology Stack Summary](#91-core-technology-stack-summary)
    *   [9.2 Key Python Libraries](#92-key-python-libraries)
    *   [9.3 Environment Setup](#93-environment-setup)
        *   [9.3.1 `requirements.txt`](#931-requirementstxt)
        *   [9.3.2 Environment Variables (`.env`) for Secrets](#932-environment-variables-env-for-secrets)
            *   [9.3.2.1 API Keys (LLM, Embedding Service)](#9321-api-keys-llm-embedding-service)
            *   [9.3.2.2 Database Credentials](#9322-database-credentials)
    *   [9.4 Configuration Management](#94-configuration-management)
        *   [9.4.1 Using YAML or Python Files for Config](#941-using-yaml-or-python-files-for-config)
        *   [9.4.2 Configurable Parameters (Model Names, Thresholds, Prompts)](#942-configurable-parameters-model-names-thresholds-prompts)
    *   [9.5 Recommended Code Structure (Modularity)](#95-recommended-code-structure-modularity)
        *   [9.5.1 Example Directory Layout (`src/`, `scripts/`, `config/`, `data/`)](#951-example-directory-layout-src-scripts-config-data)
        *   [9.5.2 Modules (e.g., `parsing`, `embedding`, `retrieval`, `generation`, `evaluation`, `tools`)](#952-modules-eg-parsing-embedding-retrieval-generation-evaluation-tools)
    *   [9.6 Version Control (Git & GitHub)](#96-version-control-git--github)
*   [Chapter 10: Logging & Observability](#chapter-10-logging--observability)
    *   [10.1 Importance of Logging in RAG Systems](#101-importance-of-logging-in-rag-systems)
    *   [10.2 Logging Schema (`query_logs` Table Deep Dive)](#102-logging-schema-query_logs-table-deep-dive)
        *   [10.2.1 Capturing Key Information at Each Stage](#1021-capturing-key-information-at-each-stage)
        *   [10.2.2 Linking Logs to Evaluation Results](#1022-linking-logs-to-evaluation-results)
    *   [10.3 Logging Implementation](#103-logging-implementation)
        *   [10.3.1 Using Python's `logging` Module](#1031-using-pythons-logging-module)
        *   [10.3.2 Writing Logs to Database](#1032-writing-logs-to-database)
    *   [10.4 Use Cases](#104-use-cases)
        *   [10.4.1 Debugging Failures](#1041-debugging-failures)
        *   [10.4.2 Performance Analysis (Latency)](#1042-performance-analysis-latency)
        *   [10.4.3 Cost Estimation](#1043-cost-estimation)
        *   [10.4.4 Auditing & Compliance (Future)](#1044-auditing--compliance-future)
*   [Chapter 11: Deployment & Scalability (Considerations)](#chapter-11-deployment--scalability-considerations)
    *   [11.1 FYP Deployment (Local / Simple Cloud)](#111-fyp-deployment-local--simple-cloud)
        *   [11.1.1 Running via CLI or Streamlit App](#1111-running-via-cli-or-streamlit-app)
        *   [11.1.2 Containerization (Docker)](#1112-containerization-docker)
    *   [11.2 Production Deployment Considerations (Beyond FYP)](#112-production-deployment-considerations-beyond-fyp)
        *   [11.2.1 Web Application Framework (Flask, FastAPI)](#1121-web-application-framework-flask-fastapi)
        *   [11.2.2 Cloud Platforms (AWS, GCP, Azure)](#1122-cloud-platforms-aws-gcp-azure)
        *   [11.2.3 Serverless vs. VMs](#1123-serverless-vs-vms)
    *   [11.3 Scalability Factors](#113-scalability-factors)
        *   [11.3.1 Database (Vector Store Scaling)](#1131-database-vector-store-scaling)
        *   [11.3.2 API Rate Limits & Quotas (LLM, Embedding Service)](#1132-api-rate-limits--quotas-llm-embedding-service)
        *   [11.3.3 Concurrent Users](#1133-concurrent-users)
        *   [11.3.4 Computation (Re-ranking, Tool Execution)](#1134-computation-re-ranking-tool-execution)
    *   [11.4 Cost Management](#114-cost-management)
*   [Chapter 12: Future Work & Enhancements](#chapter-12-future-work--enhancements)
    *   [12.1 Based on Evaluation Results (Targeted Improvements)](#121-based-on-evaluation-results-targeted-improvements)
        *   [12.1.1 Fine-tuning Embedding Model](#1211-fine-tuning-embedding-model)
        *   [12.1.2 Fine-tuning Re-ranker](#1212-fine-tuning-re-ranker)
        *   [12.1.3 Fine-tuning Generator (Smaller Model / Specialized Deployment?)](#1213-fine-tuning-generator-smaller-model--specialized-deployment)
    *   [12.2 Expanding Capabilities](#122-expanding-capabilities)
        *   [12.2.1 Handling Scanned/Image-based PDFs](#1221-handling-scannedimage-based-pdfs)
        *   [12.2.2 Advanced Table Understanding & Extraction](#1222-advanced-table-understanding--extraction)
        *   [12.2.3 Complex Cross-Document Analysis & Trends](#1223-complex-cross-document-analysis--trends)
        *   [12.2.4 Integration with Live Accounting Systems](#1224-integration-with-live-accounting-systems)
        *   [12.2.5 Expanding Calculation Toolset](#1225-expanding-calculation-toolset)
        *   [12.2.6 Supporting Other Document Types (Compliance, Legal)](#1226-supporting-other-document-types-compliance-legal)
    *   [12.3 Enhancing User Experience](#123-enhancing-user-experience)
        *   [12.3.1 Production-Grade UI/UX](#1231-production-grade-uiux)
        *   [12.3.2 User Feedback Mechanisms](#1232-user-feedback-mechanisms)
        *   [12.3.3 Visualization Capabilities](#1233-visualization-capabilities)
*   [Appendix](#appendix)
    *   [A. Example Prompts](#a-example-prompts)
        *   [A.1 Multimodal LLM Parser Prompt](#a1-multimodal-llm-parser-prompt)
        *   [A.2 LLM Query Decomposer Prompt](#a2-llm-query-decomposer-prompt)
        *   [A.3 Large Context LLM Generator Prompt (Full Example)](#a3-large-context-llm-generator-prompt-full-example)
        *   [A.4 LLM-as-judge Faithfulness Prompt](#a4-llm-as-judge-faithfulness-prompt)
    *   [B. Database Schema (SQL DDL)](#b-database-schema-sql-ddl)
    *   [C. Calculation Tool Schemas (JSON Examples)](#c-calculation-tool-schemas-json-examples)
    *   [D. API Usage Snippets](#d-api-usage-snippets)
        *   [D.1 Embedding Service API Call](#d1-embedding-service-api-call)
        *   [D.2 LLM API Call (Basic Generation)](#d2-llm-api-call-basic-generation)
        *   [D.3 LLM API Call (Function Calling Flow)](#d3-llm-api-call-function-calling-flow)
    *   [E. Glossary of Terms](#e-glossary-of-terms)

---

---

# Chapter 1: Introduction

## 1.1 Project Overview

This document provides a comprehensive technical reference for the **AI CFO Assistant**, a Final Year Project (FYP) designed to provide Small and Medium Enterprises (SMEs) with reliable, accurate, and verifiable insights derived directly from their financial documents. The system leverages state-of-the-art Artificial Intelligence (AI) techniques, specifically Retrieval-Augmented Generation (RAG) combined with Large Language Models (LLMs) capable of tool use (function calling), to answer natural language questions based solely on user-provided context.

## 1.2 The Problem: Financial Insight Bottleneck for SMEs

SMEs are vital economic contributors but often operate under significant resource constraints. While their financial performance is documented in standard reports like Income Statements, Balance Sheets, and Cash Flow Statements (typically PDFs), extracting timely and actionable intelligence from these documents presents several challenges:

1.  **Manual Effort:** Searching through multiple PDF reports for specific figures or trends is time-consuming and inefficient.
2.  **Expertise Gap:** SME owners or managers may lack the deep financial expertise required to interpret reports fully or calculate key metrics quickly.
3.  **Data Silos:** Information needed might be scattered across multiple reports or sections, requiring manual aggregation.
4.  **Unstructured Data:** Financial reports, while having structure, contain significant unstructured text (notes, explanations) and complex layouts (tables) that traditional data analysis tools struggle with.

These factors create a bottleneck, preventing SMEs from fully leveraging their own financial data for informed decision-making.

## 1.3 The Solution: AI CFO Assistant

The AI CFO Assistant aims to bridge this gap by providing an intelligent interface to an SME's financial documents. Users can upload their reports (initially focusing on core financial statements in PDF format) and ask questions in natural language (e.g., "What was our gross profit margin last quarter?", "Compare cash balance between Q1 and Q2 2023", "List the main operating expenses for FY2024").

The system utilizes a sophisticated RAG pipeline to:

1.  **Understand** the user's query.
2.  **Retrieve** the most relevant sections from the uploaded documents.
3.  **Perform** necessary calculations accurately using integrated tools.
4.  **Generate** a concise, accurate answer based *strictly* on the retrieved information.
5.  **Provide** clear citations linking the answer back to the source document sections.

## 1.4 Core Design Philosophy: Reliability First

Given the high stakes associated with financial information, the paramount design principle for this project is **Reliability**. Generic LLMs are known to "hallucinate" or generate plausible but incorrect information. To combat this, the AI CFO Assistant is explicitly designed to be trustworthy, focusing on three pillars:

1.  **Numerical Accuracy:** Ensuring that all figures presented are correct, whether directly retrieved or calculated. Calculations are delegated to deterministic Python functions via LLM function calling.
2.  **Faithfulness (Strict Context Adherence):** Guaranteeing that all generated textual answers are derived *solely and verifiably* from the information contained within the provided document context. The system is explicitly instructed *not* to use external knowledge and to refuse to answer if the information is not present in the provided context.
3.  **Attribution:** Providing clear, accurate citations for every piece of information presented, allowing users to easily trace answers back to the source document and section.

This focus on reliability aligns with best practices in AI Engineering, prioritizing robust evaluation and explicit safety mechanisms over simply maximizing capability.

## 1.5 Key Objectives

The primary technical objectives for this FYP are:

1.  **Implement Advanced Parsing:** Utilize high-capability multimodal LLMs to accurately parse complex financial PDF layouts, including tables, into structured Markdown with embedded metadata.
2.  **Develop Context-Aware Retrieval:** Implement a RAG pipeline featuring semantic chunking, metadata-infused embeddings from a high-performance model, metadata filtering, vector search, and cross-encoder re-ranking to find the most relevant document sections.
3.  **Enable Reliable Calculations:** Integrate LLM function calling capabilities from a large-context model to delegate calculations to validated, external Python tools, ensuring numerical precision.
4.  **Enforce Strict Grounding:** Employ rigorous prompt engineering techniques to ensure the LLM generator adheres strictly to the provided context and refuses appropriately when information is missing.
5.  **Build a Robust Evaluation Framework:** Create a comprehensive evaluation suite using a synthetic golden dataset to quantitatively measure Numerical Accuracy, Faithfulness, Attribution Accuracy, and Retrieval Performance.
6.  **Deliver a Functional Prototype:** Produce a working system (CLI or basic UI) demonstrating the core capabilities and evaluated reliability.

## 1.6 Scope Definition

### 1.6.1 In Scope

*   Processing core financial statement PDFs (Income Statement, Balance Sheet, Cash Flow Statement).
*   Parsing text and basic table structures using a multimodal LLM.
*   Generating structured Markdown with YAML metadata.
*   Semantic chunking based on Markdown headings.
*   Context-aware embedding using a suitable model and metadata prepending.
*   Storage and retrieval using a vector database supporting `pgvector`.
*   Metadata filtering based on query analysis.
*   Cross-encoder re-ranking of retrieved sections.
*   Query decomposition for complex queries using an LLM.
*   Generating answers using a capable LLM with a large context window.
*   Performing calculations via LLM function calling to predefined Python tools (sum, average, ratio, percentage change).
*   Enforcing context-only adherence and graceful refusal via prompting.
*   Providing section-level attribution/citations.
*   Building and executing an automated evaluation pipeline based on a synthetic dataset.
*   Logging key system interactions.
*   Developing a basic CLI or Streamlit interface for demonstration.

### 1.6.2 Out of Scope

*   Handling non-financial documents (legal, compliance, HR).
*   Processing scanned/image-only PDFs without OCR capabilities (though the chosen multimodal LLM might handle some).
*   Advanced, pixel-perfect table extraction and manipulation beyond the chosen LLM's parsing capabilities.
*   Real-time data integration with accounting systems.
*   Complex financial modeling, forecasting, or providing financial advice.
*   Sophisticated visualization of financial data.
*   User authentication, multi-tenancy, or production-grade security hardening.
*   Building a polished, production-ready user interface.
*   Fine-tuning of embedding or generator models (listed as potential Future Work).
*   Integration of keyword search alongside vector search (listed as potential Future Work).
*   Handling spreadsheet formats (.xlsx, .csv).

## 1.7 High-Level Technology Stack (Flexible Description)

*   **Core Language:** Python (Version 3.10 or later recommended).
*   **Large Language Models (LLMs):** Accessed primarily via APIs. Requires:
    *   A high-capability **Multimodal LLM** for advanced PDF parsing (understanding text, layout, tables).
    *   A large-context window **Generator LLM** supporting robust instruction following and **Function Calling / Tool Use** for reliable calculations and potentially query decomposition.
*   **Text Embedding Model:** A high-performance model optimized for semantic retrieval tasks, likely accessed via an **Embedding API Provider** for efficiency and scalability. The specific model will be chosen based on performance benchmarks relevant to retrieval (e.g., MTEB) and cost considerations.
*   **Vector Database:** A database solution offering vector storage and search capabilities, ideally compatible with **PostgreSQL** and supporting the **`pgvector` extension**. A managed cloud or serverless option (like NeonDB or equivalent) is preferred for ease of use and scalability.
*   **Re-ranker Model:** A **Cross-Encoder Model** suitable for computing fine-grained relevance between query-passage pairs. This may run locally using libraries like `sentence-transformers` or potentially accessed via an API if available and efficient.
*   **Key Python Libraries:** Core libraries will include:
    *   Clients for interacting with chosen **LLM API(s)** and **Embedding API(s)** (e.g., `google-generativeai`, `openai`, `anthropic`, `requests`).
    *   A **Database Client** compatible with the chosen PostgreSQL/pgvector solution (e.g., `psycopg2`, `asyncpg`).
    *   Libraries for NLP tasks, specifically **`sentence-transformers`** for handling embeddings and re-rankers locally.
    *   Utilities for configuration (`PyYAML`), environment management (`python-dotenv`), data handling (`pandas` potentially), logging (`logging`), and Markdown parsing (`mistune` potentially).
*   **Interface (Optional):** A simple interface using **Streamlit** (web app) or **`argparse`** (Command Line Interface) for demonstration and testing.
*   **Evaluation:** **Custom Python scripts** leveraging standard libraries (`numpy`, `scikit-learn` for metrics calculation) to implement the evaluation framework against the golden dataset.

## 1.8 Document Purpose & Audience

This document serves as the central technical reference for the AI CFO Assistant project. Its purpose is to:

*   Detail the system's architecture, design choices, and implementation specifics.
*   Provide a clear guide for understanding, reproducing, and potentially extending the project.
*   Document the evaluation methodology and rationale behind the reliability focus.

The intended audience includes:

*   The project developer(s).
*   The FYP supervisor and examiners.
*   Future developers who may build upon this work.
*   Anyone seeking to understand the technical underpinnings of applying reliable RAG and function calling to financial document analysis.


---

# Chapter 2: System Architecture

## 2.1 Architectural Overview (RAG + Function Calling)

The AI CFO Assistant is built upon an advanced **Retrieval-Augmented Generation (RAG)** architecture, enhanced with **Function Calling** capabilities. This hybrid approach aims to leverage the strengths of Large Language Models (LLMs) for natural language understanding and generation while mitigating their weaknesses (hallucination, lack of specific knowledge) by grounding them firmly in user-provided documents and ensuring numerical precision through external tools.

The core principle is to **retrieve** the most relevant information from a pre-processed corpus of financial documents before attempting to **generate** an answer. Furthermore, when calculations are required, the system delegates these tasks to reliable, deterministic **external tools** (Python functions) invoked via the LLM's function calling mechanism.

This architecture prioritizes modularity, allowing individual components to be potentially swapped or upgraded (e.g., changing the embedding model or the LLM provider) with minimal disruption to the overall workflow, facilitating rapid iteration and experimentation.

## 2.2 Core Pipeline Stages Diagram

The following diagram illustrates the key stages and data flow within the AI CFO Assistant system, covering both the initial document ingestion process and the query handling process.

```mermaid
graph TD
    subgraph Ingestion Pipeline
        direction LR
        A[Financial PDF Reports] --> B(1. PDF Parser / Extractor <br> Multimodal LLM);
        B --> C(2. Markdown Formatter <br> + YAML Metadata Extraction);
        C --> D(3. Semantic Chunker <br> Heading-Based);
        D --> E(4. Embedding Generator <br> Context-Aware);
        E --> F[(5. Vector Store <br> + Metadata <br> NeonDB/pgvector)];
    end

    subgraph Query Pipeline
        direction TB
        G[User Query] --> H{6. Query Decomposer <br> (If Complex)};
        H -- Simple Query --> I(7. Query Analyzer <br> + Metadata Extractor);
        H -- Sub-queries --> I;
        I --> J(8. Metadata Filter <br> DB Query);
        J -- Filtered Section IDs --> F;
        F -- Potential Chunks/Embeddings --> K(9. Vector Retriever);
        K -- Relevant Embeddings/Chunks --> L(10. Parent Section Mapper);
        L -- Candidate Parent Section IDs --> F;
        F -- Full Parent Section Text --> M(11. Cross-Encoder <br> Re-ranker);
        M -- Top K Parent Sections --> N(12. Context Assembler);
        N --> O{13. Generator LLM <br> + Function Calling <br> Orchestrator};
        subgraph Function Calling Loop
           direction LR
           O -- Request Tool Call --> P(14. Calculation Tool Executor <br> Python Functions);
           P -- Tool Result --> O;
        end
        O -- Final Natural Language Response --> Q(15. Post-processor <br> + Validator);
        Q --> R(16. Citation Generator);
        R --> S[Formatted Answer + Citations];
    end

    subgraph Shared Services
        direction TB
        T[(Logging Service <br> NeonDB `query_logs`)]
    end

    %% Connections between pipelines and services
    G --> T; %% Log Input Query
    O --> T; %% Log LLM Interaction
    Q --> T; %% Log Final Output
    R --> T; %% Log Citations

    %% Styling
    style F fill:#f9f,stroke:#333,stroke-width:2px
    style O fill:#ccf,stroke:#333,stroke-width:2px
    style T fill:#ddd,stroke:#333,stroke-width:1px
    style P fill:#ffcc99,stroke:#333,stroke-width:1px
```
**Figure 2.1:** Core AI CFO Assistant Architecture (Ingestion & Query Pipelines)

## 2.3 Component Descriptions

This section describes the role and function of each numbered component in the architecture diagram (Figure 2.1).

### 2.3.1 PDF Parser (Gemini Vision)

*   **Responsibility:** To process input financial PDF documents and extract their content, including text, layout structure, and potentially table data.
*   **Technology:** Utilizes a high-capability **Multimodal LLM** (e.g., Google Gemini Pro/Vision API) chosen for its ability to understand visual layout and extract information from complex formats often found in financial reports.
*   **Output:** Raw extracted content, ideally preserving structural information (headings, lists, tables) for downstream processing.

### 2.3.2 Markdown Formatter & Metadata Extractor

*   **Responsibility:** To convert the raw output from the parser into a standardized, clean **Markdown** format. It also extracts or infers key **document-level metadata** (e.g., Report Type, Company Name, Currency, Period/Date) and embeds this as **YAML front matter** within the Markdown file.
*   **Technology:** Python scripts using string manipulation, potentially regular expressions, and YAML libraries (`PyYAML`). May involve prompting the parser LLM to structure its output suitably.
*   **Output:** A Markdown string for each document, prepended with a YAML block containing structured metadata.

### 2.3.3 Semantic Chunker (Heading-Based)

*   **Responsibility:** To divide the Markdown document into smaller, semantically coherent **chunks** (sections). The primary strategy is to split based on Markdown headings (`#`, `##`, etc.), preserving logical units of text. Handles sections exceeding token limits via recursive splitting.
*   **Technology:** Python scripts, potentially using Markdown parsing libraries (`mistune`) or regex to identify heading boundaries. Incorporates token counting logic (e.g., using `tiktoken`).
*   **Output:** A list of text chunks (sections or sub-sections), each associated with its parent document and source metadata.

### 2.3.4 Embedding Generator (Nomic + Fireworks AI)

*   **Responsibility:** To convert text chunks into numerical **vector embeddings** that capture their semantic meaning. Implements the **context-aware embedding** strategy by prepending YAML metadata text to the chunk text before generating the embedding.
*   **Technology:** Interacts with a high-performance **Text Embedding Model API** (e.g., `nomic-embed-text-v1.5` via Fireworks AI). Python code handles formatting the input string (`metadata_text + chunk_text`) and managing API calls.
*   **Output:** Vector embeddings corresponding to each (potentially metadata-infused) text chunk.

### 2.3.5 Vector Store (NeonDB + pgvector)

*   **Responsibility:** To store the processed data persistently and enable efficient retrieval. Stores original document metadata, section text, chunk text (if split), associated metadata (parsed YAML), and the generated vector embeddings.
*   **Technology:** A **PostgreSQL-compatible database** with the **`pgvector` extension** enabled (e.g., NeonDB). Includes appropriate tables and indexes (HNSW for vectors, GIN for JSONB metadata).
*   **Output:** Provides data storage and retrieval capabilities via SQL queries.

### 2.3.6 Query Decomposer (Gemini)

*   **Responsibility:** To analyze complex user queries (e.g., those requiring comparisons, multi-step reasoning, or calculations involving multiple data points) and break them down into simpler, actionable **sub-queries**.
*   **Technology:** Utilizes an **LLM API** (e.g., Gemini Flash/Pro) with specific prompting designed for query decomposition.
*   **Output:** One or more simpler sub-queries to be processed sequentially or in parallel by the subsequent pipeline stages. For simple queries, this stage might be bypassed.

### 2.3.7 Metadata Filter

*   **Responsibility:** To narrow down the search space within the database *before* performing expensive vector searches. Analyzes the user query (or sub-query) to identify potential filters (e.g., specific dates, report types, keywords matching metadata fields).
*   **Technology:** Python logic performing query analysis (regex, keyword matching, potentially a small LLM call). Constructs SQL `WHERE` clauses to query the `sections.metadata` JSONB field in the database.
*   **Output:** A filtered set of `section_id`s or `embedding_id`s to be considered by the retriever.

### 2.3.8 Vector Retriever

*   **Responsibility:** To find the stored embeddings most semantically similar to the user's query embedding *within the filtered set*.
*   **Technology:** Executes vector similarity search queries against the `embeddings` table in the database using `pgvector` operators (e.g., cosine distance `<=>`).
*   **Output:** A ranked list of candidate `embedding_id`s and their associated similarity scores.

### 2.3.9 Cross-Encoder Re-ranker

*   **Responsibility:** To refine the relevance ranking of the initial retrieval results. Takes the candidate sections identified by the retriever (specifically, their full parent section text) and computes a more accurate relevance score against the user query.
*   **Technology:** Uses a **Cross-Encoder model** (e.g., `ms-marco-MiniLM-L-6-v2`) loaded via libraries like `sentence-transformers`. Runs locally or on dedicated compute.
*   **Output:** A re-ranked list of the top K most relevant parent `section_id`s.

### 2.3.10 Context Assembler

*   **Responsibility:** To gather all necessary information required for the final generation prompt. Retrieves the full original text and metadata for the top K re-ranked parent sections.
*   **Technology:** Python code interacting with the database (`sections` table) based on the re-ranker output. Formats the collected information according to the generator's prompt template.
*   **Output:** The assembled context string (metadata + full section texts) ready for prompting.

### 2.3.11 Calculation Tool Executor

*   **Responsibility:** To execute predefined, reliable **Python functions** for performing specific financial calculations (e.g., sum, average, ratio, percentage change) when requested by the Generator LLM.
*   **Technology:** A collection of well-defined Python functions implementing the required calculations. Includes robust error handling.
*   **Output:** The structured result of the calculation (e.g., a number, boolean, simple dict).

### 2.3.12 Generator & Function Calling Orchestrator (Gemini 1.5 Pro)

*   **Responsibility:** To generate the final natural language answer based *only* on the assembled context and the user query. It also orchestrates the **Function Calling** loop: identifies when a calculation tool is needed, parses the required arguments, receives the tool's result, and incorporates it into the final response. Enforces strict context adherence and refusal instructions via prompt engineering.
*   **Technology:** Interacts with a large-context window **Generator LLM API** supporting function calling (e.g., Gemini 1.5 Pro). Manages the multi-turn conversation flow required for tool use.
*   **Output:** Raw natural language response potentially containing calculation results.

### 2.3.13 Post-processor & Validator

*   **Responsibility:** To clean up the raw LLM response (remove extraneous text) and perform basic validation checks (e.g., heuristic numerical cross-referencing against cited context).
*   **Technology:** Python string manipulation, regular expressions.
*   **Output:** A cleaner, potentially validated natural language response.

### 2.3.14 Citation Generator

*   **Responsibility:** To extract the identifiers of the source sections used during context assembly and format them into clear, user-readable citations according to a predefined standard.
*   **Technology:** Python code mapping internal `section_id`s back to document metadata (filename, inferred page, section heading).
*   **Output:** A list or string of formatted citations.

### 2.3.15 Logging Service

*   **Responsibility:** To record key information about each query interaction for debugging, analysis, evaluation, and observability.
*   **Technology:** Python's standard `logging` module configured to write structured logs to a dedicated table (e.g., `query_logs`) in the **NeonDB database**.
*   **Output:** Persisted log records.

## 2.4 Data Flow

The following describes the typical sequence of operations for key system workflows.

### 2.4.1 Ingestion Flow

1.  User uploads a **Financial PDF Report** (A).
2.  **PDF Parser** (B) extracts content using multimodal LLM.
3.  **Markdown Formatter** (C) cleans the output, extracts/embeds YAML metadata.
4.  **Semantic Chunker** (D) splits Markdown into sections/sub-chunks based on headings and token limits.
5.  **Embedding Generator** (E) prepends metadata to each chunk/sub-chunk and generates vector embeddings via API.
6.  Data (metadata, original section text, chunk text, embeddings) is inserted into the **Vector Store** (F) tables (`documents`, `sections`, `embeddings`) with appropriate indexing.

### 2.4.2 Query Flow (Simple Query - No Decomposition/Calculation)

1.  User submits a **Query** (G).
2.  **Query Analyzer** (I) potentially extracts metadata filters.
3.  **Metadata Filter** (J) queries the DB to get a list of potentially relevant section/embedding IDs.
4.  **Vector Retriever** (K) performs similarity search on the filtered set using the query embedding.
5.  **Parent Section Mapper** (L) identifies the parent sections of the top retrieved embeddings.
6.  **Cross-Encoder Re-ranker** (M) retrieves full parent section text and re-scores them against the query.
7.  **Context Assembler** (N) gathers context (metadata + full text) for the top K re-ranked sections.
8.  **Generator LLM** (O) receives the query and assembled context, generates a natural language response based strictly on the context, following prompt instructions (including refusal if info is absent).
9.  **Post-processor** (Q) cleans the response.
10. **Citation Generator** (R) formats citations based on the context sections used.
11. **Formatted Answer + Citations** (S) are presented to the user.
12. Interaction details are logged (T).

### 2.4.3 Query Flow (Complex Query with Calculation)

1.  User submits a **Query** (G) requiring calculation (e.g., "What is the current ratio?").
2.  **Query Decomposer** (H) might break it down (e.g., "Find Total Current Assets", "Find Total Current Liabilities"). Execution proceeds for sub-queries similar to the simple flow until step 7 (Context Assembler).
3.  **Context Assembler** (N) gathers context relevant to the calculation (e.g., sections containing asset and liability figures).
4.  **Generator LLM** (O) receives the query/sub-query, assembled context, and *tool schemas*. It determines a calculation is needed (e.g., `calculate_ratio`).
5.  LLM (O) outputs a `function_call` request specifying the tool name (`calculate_ratio`) and arguments derived *only* from the provided context (e.g., `numerator=145000`, `denominator=40000`).
6.  **Calculation Tool Executor** (P) receives the request, executes the local `calculate_ratio(145000, 40000)` Python function.
7.  Tool Executor (P) returns the structured result (e.g., `{"ratio": 3.625}`) back to the Orchestrator (O).
8.  LLM (O) receives the tool result and generates the final natural language answer incorporating it (e.g., "Based on the balance sheet, the current ratio is 3.63.").
9.  **Post-processor** (Q) cleans the response.
10. **Citation Generator** (R) formats citations for the context sections used to derive the *inputs* to the calculation.
11. **Formatted Answer + Citations** (S) are presented.
12. Interaction details, including tool calls/results, are logged (T).




---

# Chapter 3: Data Ingestion & Processing

## 3.1 Input Format: Financial PDFs

The primary input for the AI CFO Assistant is standard financial reports provided by SMEs, typically in **Portable Document Format (PDF)**. These documents commonly include:

*   **Income Statement (Profit & Loss):** Details revenues, costs, and expenses over a period.
*   **Balance Sheet:** Shows assets, liabilities, and equity at a specific point in time.
*   **Cash Flow Statement:** Tracks the movement of cash through operating, investing, and financing activities.

**Challenges with Financial PDFs:**

*   **Varied Layouts:** SMEs use different accounting software or templates, leading to diverse formatting, column structures, and presentation styles.
*   **Mixed Content:** Reports contain text, numbers, tables, headers, footers, and sometimes charts or logos.
*   **Table Complexity:** Tables can span multiple pages, have merged cells, or lack clear borders, making programmatic extraction difficult for traditional tools.
*   **Scanned Documents (Out of Scope initially):** Some PDFs might be scanned images rather than text-based, requiring Optical Character Recognition (OCR). While the chosen multimodal LLM might handle some OCR implicitly, pixel-perfect scanned document handling is initially out of scope.

The goal of the ingestion phase is to reliably extract the meaningful content and structure from these varied PDFs into a consistent, machine-readable format.

## 3.2 Parsing with Gemini Pro/Vision API

To overcome the challenges of parsing complex financial PDFs, this system leverages a powerful **Multimodal Large Language Model API**, such as Google's Gemini Pro with Vision capabilities.

### 3.2.1 API Interaction

*   **Input:** The PDF document is typically provided to the API either as raw bytes or via a reference (e.g., a Google Cloud Storage URI).
*   **Process:** The API uses its underlying models, trained on vast amounts of text and image data, to analyze the document's visual layout and textual content simultaneously.
*   **Output:** The API returns the extracted information, typically as structured text (e.g., JSON containing text blocks, tables, potentially coordinates). The exact format depends on the specific API endpoint and prompting.

### 3.2.2 Prompting for Structured Output

Effective parsing relies heavily on providing clear instructions (prompting) to the multimodal LLM. The prompt should guide the model to:

1.  **Extract All Text:** Ensure all relevant textual content is captured.
2.  **Identify Structure:** Recognize headings, paragraphs, lists, and especially tables.
3.  **Preserve Table Integrity:** Extract table data row by row, maintaining associations between headers and cell values.
4.  **Output Format:** Request the output in a specific, easily parseable format, ideally structured **Markdown** that reflects the document's hierarchy. It should also be prompted to identify and extract key document-level **metadata**.

*(See Appendix A.1 for an example parser prompt)*

### 3.2.3 Handling Layouts and Tables

The key advantage of using a multimodal model like Gemini Vision is its ability to interpret visual layout cues (whitespace, lines, font sizes) to understand document structure, particularly complex tables that might confuse text-only parsers. It should ideally convert tabular data into Markdown tables or a similar structured text format within the output.

### 3.2.4 Error Handling & Rate Limits

*   **API Errors:** Implement robust error handling (e.g., using try-except blocks, retry mechanisms with exponential backoff) for potential API issues (network errors, server errors, invalid requests).
*   **Rate Limits:** Be mindful of API rate limits. For ingesting many documents, implement throttling or process documents sequentially to avoid exceeding limits. Check the specific provider's documentation for limits.
*   **Parsing Failures:** Log documents that fail parsing after retries for manual inspection. Consider alternative parsing strategies (e.g., simpler text extraction libraries) as a fallback for problematic documents, though this might sacrifice structural information.

## 3.3 Structuring Output: Markdown + YAML Front Matter

The raw output from the parser LLM needs to be transformed into a standardized format suitable for chunking and embedding. The chosen format is **Markdown with YAML Front Matter**.

### 3.3.1 Standard Metadata Schema (YAML)

A block of YAML enclosed in triple-dashed lines (`---`) is prepended to the start of each document's Markdown representation. This block contains critical document-level metadata extracted or inferred during parsing. A consistent schema is essential for later filtering.

**Example YAML Schema:**

```yaml
---
document_id: "SynthWidgets_IS_2024_Q1"  # Unique identifier (e.g., filename based)
source_filename: "SynthWidgets_IncomeStatement_Q1_2024.pdf"
report_type: "Income Statement"          # E.g., "Income Statement", "Balance Sheet", "Cash Flow Statement"
company_name: "SynthWidgets Inc."        # Extracted company name
period_start_date: "2024-01-01"          # Optional, if applicable
period_end_date: "2024-03-31"            # End date for IS/CF, or As-of date for BS
fiscal_year: 2024
fiscal_quarter: Q1                      # Optional, if applicable (Q1, Q2, Q3, Q4)
currency: "USD"                         # Extracted currency
parsing_timestamp: "2024-07-28T10:30:00Z"
parser_model: "gemini-1.5-pro-vision"    # Model used for parsing
# Add other relevant fields as needed, e.g., specific subsidiary, department
---
```

*   **Extraction:** This metadata might be directly extracted by the parser LLM (if prompted correctly) or inferred using regex/heuristics applied to the extracted text (e.g., finding dates, report titles).
*   **Consistency:** Ensure dates are standardized (e.g., ISO 8601 format), report types use consistent naming, etc.

### 3.3.2 Markdown Formatting Conventions

The body of the document following the YAML block should adhere to standard Markdown conventions:

*   **Headings:** Use `#`, `##`, `###`, etc., to represent the document's heading structure accurately. This is *crucial* for the heading-based chunking strategy.
*   **Tables:** Represent extracted tables using Markdown table syntax (`| Header | Header |\n|---|---|\n| Cell | Cell |`).
*   **Lists:** Use standard bullet (`*`, `-`) or numbered lists.
*   **Paragraphs:** Separate paragraphs with blank lines.

The goal is a clean, semantically structured representation of the original PDF content.

### 3.3.3 Mapping Content to Page Numbers (Challenge)

Reliably mapping specific Markdown content back to the *exact page number* in the original PDF can be challenging, especially if the parser LLM doesn't provide precise coordinate or page information for every extracted element.

*   **Possible Approaches:**
    1.  **LLM Assistance:** Prompt the parser LLM to explicitly include page number markers (e.g., `<!-- Page 3 -->`) in its output where page breaks occur. This depends heavily on the LLM's capability.
    2.  **Heuristics:** If the LLM output preserves sequential order, try to correlate unique phrases or figures in the Markdown back to the original PDF pages using simpler text extraction libraries alongside the LLM parser for cross-referencing.
    3.  **Accept Limitation:** If precise page mapping is unreliable, the attribution might need to be at the *document* or *section* level rather than the page level. The `section_heading` metadata becomes more important in this case.
*   **Decision:** For this FYP, we will initially rely on the parser LLM's ability to structure output sequentially. If possible, we will prompt for page markers. If not, attribution will primarily rely on `document_id` and `section_heading` derived from the Markdown structure. The `page_number` field in the database might store an estimated or starting page for a section if exact mapping isn't feasible.

## 3.4 Semantic Chunking Strategy

Once documents are in the structured Markdown format, they need to be broken down into manageable chunks for embedding and retrieval. A purely fixed-size chunking approach often breaks semantic context mid-sentence or table. Therefore, a **semantic chunking** strategy is employed.

### 3.4.1 Primary Split: Markdown Headings

*   **Logic:** The primary splitting mechanism uses the Markdown heading structure (`#`, `##`, `###`, etc.). Each distinct section defined by a heading (and its subsequent content until the next heading of the same or higher level) is treated as a potential chunk.
*   **Rationale:** Headings typically demarcate logical topics or sections within financial reports (e.g., "Assets", "Operating Expenses", "Notes to Financial Statements"), preserving contextual coherence.
*   **Implementation:** Requires parsing the Markdown structure to identify heading levels and the content belonging to each section.

### 3.4.2 Handling Large Sections (> 8K Tokens)

Some sections, especially detailed notes or long tables converted to Markdown, might exceed the maximum input token limit of the chosen embedding model (e.g., `nomic-embed-text-v1.5` has an 8192 token limit).

#### 3.4.2.1 Recursive Splitting Logic

If a section identified by headings exceeds the token limit:

1.  **Attempt Sub-Heading Split:** First, try splitting based on the *next level down* of headings (e.g., if splitting by `##` resulted in a large chunk, try splitting that chunk by `###`).
2.  **Fallback Splitting:** If further heading splits are not possible or still result in oversized chunks, apply recursive character splitting using sensible separators in order of preference (e.g., `\n\n` (double newline), `\n` (single newline), sentence terminators (`.`, `?`, `!`), then finally by character if necessary).
3.  **Overlap:** Consider adding a small overlap (e.g., 50-100 tokens) between recursively split sub-chunks to maintain some context across breaks, although this adds redundancy. The necessity of overlap should be evaluated.
4.  **Token Counting:** Use a tokenizer compatible with the embedding model (e.g., `tiktoken` for models aligned with OpenAI tokenization, or a model-specific tokenizer if available) to accurately measure chunk size during the splitting process.

#### 3.4.2.2 Maintaining Parent Section Linkage

When a large section is split into sub-chunks using recursive methods:

*   Each sub-chunk **must** retain the metadata (especially `document_id` and the original parent `section_heading`) of the parent section it came from.
*   A mechanism (e.g., storing the parent `section_id` in the `embeddings` table) is needed to link these sub-chunks back to their original logical parent section. This is crucial for the re-ranking strategy (re-ranking full parent sections).

### 3.4.3 Chunk Representation

Each final chunk (whether a full section or a sub-chunk resulting from a split) will consist of:

*   The **text content** of the chunk.
*   Associated **metadata** inherited from the document/parent section (including `document_id`, `section_heading`, `report_type`, `period_end_date`, etc.).
*   A flag indicating if it's a **full section** or a **sub-chunk**.
*   (If a sub-chunk) A reference to its **parent section ID**.

This structured information is then passed to the embedding stage.




---

# Chapter 4: Embedding & Storage

After parsing and chunking the financial documents into manageable, semantically relevant sections (or sub-chunks), the next critical step is to convert this textual information into a format that enables efficient semantic search. This involves generating vector embeddings and storing them, along with associated metadata and original text, in a specialized database.

## 4.1 Embedding Strategy: Context-Awareness

Simply embedding the raw text of each chunk might not be sufficient for financial documents where the same phrase (e.g., "Total Revenue") can appear in reports from different periods or companies. To disambiguate and provide richer context for retrieval, a **context-aware embedding** strategy is employed.

### 4.1.1 Model Selection: `nomic-embed-text-v1.5`

*   **Rationale:** The choice of embedding model significantly impacts retrieval quality. `nomic-embed-text-v1.5` is selected as a strong candidate due to:
    *   **High Performance:** Often ranks highly on massive text embedding benchmarks (MTEB), indicating strong performance on diverse retrieval tasks.
    *   **Large Context Length:** Supports up to 8192 tokens, accommodating potentially large financial report sections generated by the heading-based chunking strategy.
    *   **Accessibility:** Available via efficient APIs (like Fireworks AI), avoiding the need for local hosting and management of large embedding models.
*   **Flexibility:** While Nomic is the initial choice, the architecture allows swapping this component if evaluation suggests another model (e.g., from Cohere, OpenAI, Voyage AI, or newer models) offers better performance on this specific financial dataset. Configuration management (Chapter 9) facilitates this.

### 4.1.2 Metadata Prepending Technique

*   **Concept:** Before generating the embedding for a text chunk (or sub-chunk), key metadata extracted from the document's YAML front matter (and potentially the section heading) is converted into a concise text format and prepended to the actual chunk text.
*   **Example Input String for Embedding:**
    ```
    Metadata: Report Type=Income Statement; Period End Date=2024-03-31; Section=Operating Expenses; ---
    [Actual text content of the 'Operating Expenses' section chunk...]
    ```
*   **Rationale:** This technique injects crucial context (like the document type, date, and section topic) directly into the string being embedded. The resulting vector embedding implicitly encodes not just the chunk's content but also its surrounding context, leading to more precise retrieval. For example, it helps differentiate "Operating Expenses" from Q1 2024 versus Q1 2023.
*   **Implementation:** Requires careful formatting of the metadata into a consistent, concise string format using key-value pairs or similar, separated from the main text by a clear delimiter (like `---`). Ensure the combined length does not exceed the embedding model's token limit.

### 4.1.3 Implementation via Fireworks AI API

*   **Rationale for API:** Using a managed API provider like Fireworks AI simplifies deployment, scaling, and maintenance compared to self-hosting embedding models. It offers pay-as-you-go pricing and access to state-of-the-art models.
*   **API Call Structure:**
    1.  Construct the input string (metadata + chunk text).
    2.  Make an HTTP POST request to the Fireworks AI embedding endpoint for the chosen model (`nomic-embed-text-v1.5`).
    3.  The request body typically contains the input string(s).
    4.  The API response contains the generated vector embedding(s).
    *(See Appendix D.1 for an example API call snippet)*
*   **Batching Considerations:** Embedding APIs often support sending multiple text inputs in a single request (batching). This is significantly more efficient (lower latency, potentially lower cost) than sending one request per chunk. The ingestion script should batch chunks before calling the embedding API, respecting any batch size limits imposed by the provider.

## 4.2 Vector Database: NeonDB

A specialized database is required to store the text chunks, their vector embeddings, and associated metadata, while enabling efficient vector similarity search.

### 4.2.1 Rationale for Choice (Serverless, Postgres Compatibility)

*   **NeonDB** is selected as the vector database solution due to:
    *   **Serverless Architecture:** Automatically scales resources based on demand, simplifying infrastructure management and potentially reducing costs for variable workloads.
    *   **PostgreSQL Compatibility:** Fully compatible with PostgreSQL, allowing the use of standard SQL for metadata filtering alongside vector operations. This leverages existing SQL knowledge and tooling.
    *   **`pgvector` Support:** Natively supports the popular `pgvector` extension for efficient vector storage and similarity search capabilities within Postgres.
    *   **Managed Service:** Reduces the operational burden of database setup, maintenance, backups, and scaling.
*   **Flexibility:** If requirements change, other PostgreSQL providers supporting `pgvector` (like AWS RDS, Google Cloud SQL) or dedicated vector databases could potentially be used, although NeonDB's serverless nature is attractive for development and potential future scaling.

### 4.2.2 Enabling `pgvector`

The `pgvector` extension needs to be explicitly enabled within the NeonDB database instance. This is typically done via a simple SQL command:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
This command only needs to be run once per database.

## 4.3 Database Schema Design

A well-designed schema is crucial for organizing the data and facilitating efficient queries. The following tables form the core schema:

### 4.3.1 `documents` Table

Stores metadata about each uploaded source PDF document.

*   `document_id` (VARCHAR PRIMARY KEY): Unique identifier (e.g., derived from filename or UUID).
*   `source_filename` (TEXT NOT NULL): Original filename of the uploaded PDF.
*   `parsed_markdown_content` (TEXT): The full Markdown content generated by the parser (optional, could be large).
*   `yaml_metadata` (JSONB): The full YAML front matter extracted from the Markdown.
*   `upload_timestamp` (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP): When the document was uploaded/processed.
*   `parser_model_used` (VARCHAR): The model identifier used for parsing (e.g., 'gemini-1.5-pro-vision').
*   `parsing_status` (VARCHAR): e.g., 'Success', 'Failed', 'Processing'.

### 4.3.2 `sections` Table

Stores information about the logical sections identified by Markdown headings.

*   `section_id` (BIGSERIAL PRIMARY KEY): Auto-incrementing unique identifier for the section.
*   `document_id` (VARCHAR NOT NULL REFERENCES documents(document_id)): Foreign key linking to the source document.
*   `section_heading` (TEXT): The text of the Markdown heading defining this section (e.g., "Operating Expenses").
*   `section_level` (INTEGER): The Markdown heading level (1 for `#`, 2 for `##`, etc.).
*   `original_section_text` (TEXT NOT NULL): The full, original text content of this entire section (potentially large).
*   `metadata` (JSONB NOT NULL): Combined metadata (document-level YAML + section-specific info like heading).
*   `token_count` (INTEGER): Estimated token count of `original_section_text`.
*   `requires_split` (BOOLEAN DEFAULT FALSE): Flag indicating if this section was too large and needed recursive splitting.

### 4.3.3 `embeddings` Table

Stores the actual text chunks (if split) and their corresponding vector embeddings.

*   `embedding_id` (BIGSERIAL PRIMARY KEY): Auto-incrementing unique identifier for the embedding.
*   `section_id` (BIGINT NOT NULL REFERENCES sections(section_id)): Foreign key linking to the parent logical section.
*   `chunk_sequence` (INTEGER DEFAULT 0): Order of this chunk within the parent section (0 if `is_full_section` is true, 1, 2, 3... if split).
*   `chunk_text` (TEXT): The specific text content represented by this embedding. This is the *full section text* if `is_full_section` is true, otherwise it's the text of the sub-chunk.
*   `embedding_vector` (vector(1024) NOT NULL): The vector embedding generated by the embedding model (adjust dimension based on Nomic's output, e.g., 1024).
*   `is_full_section` (BOOLEAN NOT NULL): True if this embedding represents the entire `sections.original_section_text`, False if it represents a sub-chunk from recursive splitting.
*   `embedding_model_used` (VARCHAR): The model identifier used for generating this embedding (e.g., 'nomic-embed-text-v1.5').

### 4.3.4 `query_logs` Table

Stores detailed information about each query interaction for debugging and analysis. (Detailed structure in Chapter 10).

*   `log_id` (BIGSERIAL PRIMARY KEY)
*   `timestamp` (TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)
*   `user_query` (TEXT)
*   `decomposed_sub_queries` (JSONB)
*   `metadata_filters_applied` (JSONB)
*   `retrieved_embedding_ids` (BIGINT[])
*   `reranked_section_ids` (BIGINT[])
*   `final_context_section_ids` (BIGINT[])
*   `llm_prompt` (TEXT)
*   `raw_llm_response` (TEXT)
*   `tool_calls` (JSONB)
*   `tool_responses` (JSONB)
*   `final_response` (TEXT)
*   `citations_generated` (JSONB)
*   `latency_ms_total` (INTEGER)
*   `evaluation_results` (JSONB) -- Placeholder for linking to evaluation scores
*   ... (Other relevant fields)

### 4.3.5 Relationships (ERD Diagram)

*(An Entity-Relationship Diagram should be included here visually showing the links: `documents` -> `sections` -> `embeddings`, and `query_logs` potentially linking back)*

```mermaid
erDiagram
    DOCUMENTS ||--o{ SECTIONS : contains
    SECTIONS ||--o{ EMBEDDINGS : has
    QUERY_LOGS {
        BIGSERIAL log_id PK
        TIMESTAMPTZ timestamp
        TEXT user_query
        JSONB decomposed_sub_queries
        JSONB metadata_filters_applied
        BIGINT[] retrieved_embedding_ids
        BIGINT[] reranked_section_ids
        BIGINT[] final_context_section_ids
        TEXT llm_prompt
        TEXT raw_llm_response
        JSONB tool_calls
        JSONB tool_responses
        TEXT final_response
        JSONB citations_generated
        INTEGER latency_ms_total
        JSONB evaluation_results
    }

    DOCUMENTS {
        VARCHAR document_id PK
        TEXT source_filename
        TEXT parsed_markdown_content
        JSONB yaml_metadata
        TIMESTAMPTZ upload_timestamp
        VARCHAR parser_model_used
        VARCHAR parsing_status
    }

    SECTIONS {
        BIGSERIAL section_id PK
        VARCHAR document_id FK
        TEXT section_heading
        INTEGER section_level
        TEXT original_section_text
        JSONB metadata
        INTEGER token_count
        BOOLEAN requires_split
    }

    EMBEDDINGS {
        BIGSERIAL embedding_id PK
        BIGINT section_id FK
        INTEGER chunk_sequence
        TEXT chunk_text
        vector embedding_vector
        BOOLEAN is_full_section
        VARCHAR embedding_model_used
    }

```
**Figure 4.1:** Database Entity-Relationship Diagram

## 4.4 Indexing Strategy

Efficient retrieval relies heavily on appropriate database indexing.

### 4.4.1 Vector Indexing (HNSW on `embedding_vector`)

*   **Purpose:** To enable fast Approximate Nearest Neighbor (ANN) search for vector similarity.
*   **Method:** Create an index on the `embeddings.embedding_vector` column using the `hnsw` (Hierarchical Navigable Small Worlds) index type provided by `pgvector`.
    ```sql
    CREATE INDEX idx_embeddings_vector_hnsw ON embeddings USING hnsw (embedding_vector vector_cosine_ops);
    -- Or use vector_l2_ops for Euclidean distance if preferred
    ```
*   **Parameters:** HNSW indexes have parameters (`m`, `ef_construction`, `ef_search`) that can be tuned to trade off between index build time, search speed, and accuracy (recall). Start with `pgvector` defaults and tune later if performance analysis indicates a need.

### 4.4.2 Metadata Indexing (GIN on `metadata` JSONB)

*   **Purpose:** To speed up filtering queries based on key-value pairs within the `sections.metadata` JSONB column.
*   **Method:** Create a GIN (Generalized Inverted Index) index on the `metadata` column.
    ```sql
    CREATE INDEX idx_sections_metadata_gin ON sections USING gin (metadata jsonb_path_ops);
    ```
*   **Benefit:** Allows efficient searching for sections matching specific criteria like `metadata @> '{"report_type": "Balance Sheet"}'` or `metadata->>'fiscal_year' = '2023'`.

### 4.4.3 Standard Indexes (FKs, IDs)

*   Ensure standard B-tree indexes are created on Primary Keys (`document_id`, `section_id`, `embedding_id`, `log_id`) and Foreign Keys (`sections.document_id`, `embeddings.section_id`) for efficient joins and lookups. PostgreSQL typically creates indexes for PKs automatically.

## 4.5 Data Insertion Process

The process of populating the database after parsing, chunking, and embedding.

### 4.5.1 Orchestration Script

A Python script (`ingest.py` or similar) should orchestrate the entire ingestion pipeline:
1.  Take a PDF file path as input.
2.  Call the Parser (Component B).
3.  Format to Markdown + YAML (Component C).
4.  Chunk the Markdown (Component D).
5.  For each chunk/sub-chunk:
    *   Prepare input for embedding (prepend metadata).
    *   Call Embedding Generator API (Component E) in batches.
    *   Prepare data records for insertion.
6.  Insert data into `documents`, `sections`, and `embeddings` tables in the database (Component F).

### 4.5.2 Transaction Management

Use database transactions to ensure atomicity. If any step in processing and inserting data for a single document fails (e.g., embedding API error, database error), the entire transaction for that document should be rolled back to avoid incomplete or inconsistent data. Insert into `documents`, then `sections`, then `embeddings` within a single transaction per document.




---

# Chapter 5: Retrieval Pipeline

The goal of the Retrieval Pipeline is to efficiently identify and retrieve the most relevant context sections from the stored knowledge base (Vector Store) that are needed to answer a given user query. This involves several stages designed to progressively narrow down the search space and increase the relevance of the final context provided to the generator LLM.

## 5.1 Overview of Retrieval Goals

Effective retrieval is crucial for the AI CFO Assistant's reliability. The primary goals are:

1.  **Relevance:** Retrieve sections that directly contain the information needed to answer the query.
2.  **Completeness:** Retrieve *all* necessary sections, especially for queries requiring information synthesis from multiple parts of a document or across documents (within filtering constraints).
3.  **Precision:** Avoid retrieving irrelevant sections that could confuse the generator LLM or lead to inaccurate answers.
4.  **Efficiency:** Perform retrieval quickly enough for an interactive user experience.

The multi-stage pipeline described below is designed to achieve these goals.

## 5.2 Query Decomposition (for Complex Queries)

Not all user queries are simple lookups. Complex questions might require comparisons, calculations involving multiple steps, or reasoning across different concepts.

### 5.2.1 Triggering Decomposition

*   **Heuristics:** Simple keyword triggers (e.g., "compare", "difference", "trend", "calculate X using Y and Z") can suggest a query might need decomposition.
*   **LLM Analysis (Preferred):** A more robust approach is to make an initial, lightweight LLM call (e.g., using Gemini Flash) specifically tasked with analyzing the query's complexity.
    *   **Prompt:** "Analyze the following user query about financial reports. Does it require multiple distinct pieces of information or steps to answer fully? If yes, break it down into the simplest possible sub-queries. If no, repeat the original query."
*   **Decision:** If the analysis yields sub-queries, the pipeline processes each one. If not, the original query proceeds directly.

### 5.2.2 Gemini Model & Prompting

*   **Model:** A fast and capable model like Gemini Flash or Pro is suitable.
*   **Prompt:** Needs to guide the LLM effectively. Examples:
    *   "User Query: Compare revenue between Q1 and Q2 2024." -> "Sub-queries: [Find revenue for Q1 2024, Find revenue for Q2 2024]"
    *   "User Query: What is the current ratio for the latest period?" -> "Sub-queries: [Find Total Current Assets for the latest period, Find Total Current Liabilities for the latest period]"
    *(See Appendix A.2 for prompt details)*

### 5.2.3 Handling Sub-query Execution

*   **Sequential/Parallel:** Depending on the sub-queries, they might be executed sequentially (if one depends on the result of another) or in parallel (if they are independent lookups). The orchestrator needs to manage this flow.
*   **Context Aggregation:** The context retrieved for each sub-query needs to be appropriately aggregated before being passed to the final generation stage.

## 5.3 Query Analysis & Metadata Extraction

Before searching the vector store, the system analyzes the query (or sub-query) to extract potential filters that can significantly prune the search space.

### 5.3.1 Identifying Entities (Dates, Report Types)

*   **Dates/Periods:** Look for explicit dates ("March 31, 2024"), fiscal quarters ("Q3 2023"), years ("FY2022"), or relative terms ("last quarter", "latest period").
*   **Report Types:** Identify mentions of specific reports ("Balance Sheet", "Income Statement", "P&L").
*   **Other Keywords:** Potentially extract company names (if handling multiple SMEs), specific currencies, or other fields present in the `sections.metadata` JSONB.

### 5.3.2 Methods (Regex, Keywords, LLM Call)

*   **Regex/Keywords:** Use regular expressions and keyword matching for well-defined patterns (dates, standard report names). This is fast and reliable for known formats.
*   **LLM Call (Optional):** For more complex natural language understanding (e.g., interpreting "last quarter" based on the current date or latest ingested data), a small LLM call could be used for Named Entity Recognition (NER) tailored to financial contexts. However, regex/keywords might be sufficient initially.

## 5.4 Metadata Filtering

This step applies the extracted filters to the database, significantly reducing the number of sections/embeddings that need to be considered for vector search.

### 5.4.1 Constructing SQL `WHERE` Clauses

Based on the extracted metadata filters, dynamically construct the `WHERE` clause for the SQL query against the `sections` table.

*   **Example:** If the query is "What was revenue in Q1 2024?" and metadata extraction identifies `fiscal_quarter='Q1'` and `fiscal_year=2024`:
    ```sql
    -- Pseudo-SQL for filtering sections
    SELECT section_id
    FROM sections
    WHERE metadata->>'fiscal_quarter' = 'Q1'
      AND metadata->>'fiscal_year' = '2024'
      -- Potentially add report_type filter if identifiable
      -- AND metadata->>'report_type' = 'Income Statement'
    ```

### 5.4.2 Querying `sections.metadata` JSONB

*   Leverage the GIN index created on the `sections.metadata` column (Chapter 4) for efficient execution of these filtering queries.
*   The output of this stage is a list of `section_id`s that match the filtering criteria.

## 5.5 Vector Search

Vector search finds the stored embeddings semantically closest to the user's query embedding *within the filtered set of sections*.

### 5.5.1 Query Embedding (Nomic)

*   The user query (or sub-query) text is embedded using the same context-aware embedding model (`nomic-embed-text-v1.5` via Fireworks AI) used during ingestion. *Crucially, metadata is typically **not** prepended to the user query* before embedding, as the filtering stage has already narrowed the search based on metadata. Embedding just the query text focuses on semantic content similarity.

### 5.5.2 Using `pgvector` Similarity Operators

*   The query vector is used in a SQL query against the `embeddings` table, joined with the filtered `section_id`s.
*   The `<=>` (cosine distance) or `<->` (L2 distance) operators from `pgvector` are used to calculate similarity and find the nearest neighbors.
    ```sql
    -- Pseudo-SQL for vector search on filtered embeddings
    SELECT emb.embedding_id, emb.section_id, emb.embedding_vector <=> %(query_vector)s AS distance
    FROM embeddings emb
    JOIN sections s ON emb.section_id = s.section_id
    WHERE s.section_id = ANY(%(filtered_section_ids)s) -- Filter results from previous step
    ORDER BY distance ASC -- Find closest vectors
    LIMIT 50; -- Retrieve top K initial candidates (e.g., 50)
    ```

### 5.5.3 Retrieving Top K Candidates

*   Retrieve a relatively large number of initial candidates (e.g., K=25 to 50) from the vector search stage. This ensures that potentially relevant chunks, even if not perfectly ranked by vector similarity alone, have a chance to be evaluated by the more sophisticated re-ranker.
*   The output is a ranked list of `embedding_id`s (and potentially their `section_id`s) and distances.

## 5.6 Hybrid Search Considerations (Future)

While the initial implementation focuses on metadata filtering + vector search, a true **hybrid search** approach combining dense (vector) and sparse (keyword) retrieval could be beneficial, especially for finding specific financial terms, acronyms, or exact numerical figures that vector search might overlook.

### 5.6.1 Need for Keyword Search (Specific Terms)

*   Keywords like "EBITDA", specific invoice numbers, exact low-frequency figures, or unique proper nouns might be better captured by traditional keyword search algorithms (like BM25 or PostgreSQL's Full-Text Search).

### 5.6.2 Integration Options (BM25, FTS)

*   PostgreSQL offers built-in Full-Text Search (FTS) capabilities that can be indexed and queried alongside vector search.
*   Alternatively, libraries implementing algorithms like BM25 could be used outside the database, searching the text content retrieved based on metadata filtering.

### 5.6.3 Result Fusion (RRF)

*   If both vector and keyword searches are performed, their results need to be combined intelligently. **Reciprocal Rank Fusion (RRF)** is a common and effective technique that combines ranked lists from different retrievers without needing score normalization.

*   **Note:** Implementing full hybrid search adds complexity and is designated as **Future Work** (Chapter 12) unless initial evaluation reveals significant shortcomings in the metadata+vector approach for critical query types.

## 5.7 Re-ranking with Cross-Encoders

Vector search provides initial candidates, but **Cross-Encoders** offer a more computationally intensive but generally more accurate method for assessing relevance by directly comparing the query text against the *full text* of potential context passages.

### 5.7.1 Rationale: Enhancing Top-K Relevance

*   Cross-encoders process the query and a candidate chunk *together*, allowing for deeper interaction modeling compared to embedding models which process them separately. This often leads to better identification of true relevance, especially for nuanced queries.
*   They help push the most relevant sections to the very top ranks (Top 3-5) needed for the generator's limited context window.

### 5.7.2 Model Selection (e.g., `ms-marco-MiniLM-L-6-v2`)

*   Choose a model trained for passage re-ranking tasks. Models fine-tuned on datasets like MS MARCO are common choices (e.g., `ms-marco-MiniLM-L-6-v2`, `ms-marco-MiniLM-L-12-v2`, or newer variants). These models are relatively small and fast compared to large generator LLMs.

### 5.7.3 Process: Re-ranking Full Parent Sections

1.  **Identify Parents:** Using the `embedding_id`s returned by the vector search (Step 5.5.3), identify the unique parent `section_id`s they belong to (using the mapping stored in the `embeddings` table).
2.  **Retrieve Full Text:** Fetch the `original_section_text` from the `sections` table for these unique parent section IDs.
3.  **Score:** For each `(query, original_section_text)` pair, use the cross-encoder model to compute a relevance score.
4.  **Re-rank:** Sort the parent sections based on their cross-encoder scores in descending order.

### 5.7.4 Implementation (`sentence-transformers`)

*   The `sentence-transformers` library provides easy-to-use interfaces for loading and using pre-trained cross-encoder models.
*   The re-ranking logic typically involves iterating through the candidate sections, preparing input pairs for the model, and collecting scores. This step can be computationally intensive if many candidates are re-ranked; optimize by limiting the number of candidates fed to the re-ranker (e.g., top 25-50 from vector search).

## 5.8 Final Context Selection

*   Based on the re-ranked list from the cross-encoder, select the final **Top K** parent sections (e.g., K=3 to 5, configurable) whose full text will be assembled and passed as context to the generator LLM. The choice of K depends on the generator LLM's context window size and the desired balance between providing sufficient context and avoiding overwhelming the LLM with potentially irrelevant information.



---

# Chapter 6: Generation & Function Calling

This chapter details the process of generating the final natural language answer for the user. This stage takes the carefully retrieved and re-ranked context sections, the original user query (or sub-query), and leverages a powerful Large Language Model (LLM) with function calling capabilities to synthesize a reliable, accurate, and well-cited response. Ensuring the LLM adheres strictly to the provided context and performs calculations correctly are the primary challenges addressed here.

## 6.1 Generator Model: Gemini 1.5 Pro (1M Context)

The choice of the generator LLM is pivotal for the system's capabilities and reliability. **Gemini 1.5 Pro** (or a similarly capable model) is selected for several key reasons:

### 6.1.1 Rationale (Context Window, Function Calling)

1.  **Large Context Window (1 Million Tokens):** Financial analysis often requires considering substantial context. While the retrieval pipeline selects the Top K most relevant sections, having a large context window allows feeding the *full text* of these sections (which can be lengthy) to the LLM without truncation. This maximizes the information available to the generator for synthesizing accurate answers and performing calculations based on comprehensive data.
2.  **Robust Function Calling / Tool Use:** This is non-negotiable for achieving reliable numerical accuracy. Gemini 1.5 Pro offers a sophisticated function calling mechanism, allowing the LLM to delegate specific calculations to external, deterministic Python code, rather than attempting (and potentially failing at) arithmetic internally.
3.  **Strong Instruction Following:** Advanced models like Gemini 1.5 Pro generally exhibit better adherence to complex instructions, which is critical for enforcing the strict context-only constraints and specific output formatting requirements (like citations).
4.  **Multilingual & Multimodal Potential (Future):** While not the primary focus, the underlying model's capabilities offer potential for future extensions (e.g., handling reports in other languages).

*   **Flexibility:** As with other components, if alternative models emerge offering comparable (or superior) large-context performance, function calling reliability, and instruction following at a suitable cost, the architecture allows for evaluation and potential swapping via configuration.

## 6.2 Context Assembly for Prompting

Before calling the generator LLM, the system meticulously assembles the final prompt content. This involves combining the user's query with the retrieved information in a structured way.

### 6.2.1 Including Metadata

*   The YAML metadata associated with each of the Top K retrieved parent sections is included in the prompt, typically formatted as text (e.g., `Source Document: [filename], Report Type: [type], Period End Date: [date], Section Heading: [heading]`).
*   This provides essential context to the LLM about the origin and nature of the text segments that follow.

### 6.2.2 Including Full Re-ranked Section Text

*   The **complete original text** (`original_section_text` from the `sections` table) for each of the Top K re-ranked parent sections is included.
*   Using the full section text, rather than potentially smaller sub-chunks initially retrieved by vector search, gives the LLM maximum local context for understanding the information within that section.

### 6.2.3 Formatting and Delimiters

*   The prompt structure uses clear delimiters to separate different parts of the input: the user query, instructions, tool schemas, and the context sections.
*   Each context section should be clearly demarcated, including its associated metadata.

**Example Prompt Structure Snippet:**

```
USER_QUERY: [User's original query or sub-query]

---
CRITICAL INSTRUCTIONS:
[Detailed instructions from Section 6.3]
---
AVAILABLE TOOLS:
[JSON schemas for calculation tools - Section 6.4.3]
---
PROVIDED CONTEXT SECTIONS:

### CONTEXT SECTION 1 ###
Metadata: Source Document=DocA.pdf, Report Type=Balance Sheet, Period End Date=2024-03-31, Section Heading=Current Assets
Text:
[Full text of the 'Current Assets' section...]

### CONTEXT SECTION 2 ###
Metadata: Source Document=DocA.pdf, Report Type=Balance Sheet, Period End Date=2024-03-31, Section Heading=Current Liabilities
Text:
[Full text of the 'Current Liabilities' section...]

### CONTEXT SECTION 3 ###
...
---
Answer the USER_QUERY based *only* on the instructions and the PROVIDED CONTEXT SECTIONS above.
```

## 6.3 Prompt Engineering for Reliability

The prompt is the primary mechanism for controlling the LLM's behavior and ensuring it meets the system's reliability requirements. It must be meticulously crafted.

### 6.3.1 Core Principles (Clarity, Specificity)

*   Instructions must be unambiguous, explicit, and leave little room for interpretation.
*   Use strong modal verbs ("MUST", "MUST NOT", "DO NOT").
*   Place critical instructions prominently.

### 6.3.2 Persona Setting

*   Define the AI's role clearly to guide its tone and focus.
    *   Example: `"You are an AI Financial Assistant. Your sole purpose is to accurately answer questions based strictly on the provided financial document excerpts. Prioritize factual correctness and clear attribution above all else."`

### 6.3.3 Strict Context-Only Constraints (CRITICAL INSTRUCTION)

*   This is the most crucial part for preventing hallucinations and ensuring faithfulness.
    *   Example: `"CRITICAL INSTRUCTION: You MUST answer the query using ONLY the information contained within the 'PROVIDED CONTEXT SECTIONS' above. Do NOT use any prior knowledge, training data, real-time information, or any information source external to these exact text sections and their associated metadata. Verify that every piece of information in your answer comes directly from the provided context."`

### 6.3.4 Graceful Refusal Instruction

*   Explicitly teach the model *how* to respond when the necessary information isn't available in the context.
    *   Example: `"If the information needed to answer the query accurately and completely is not present in the 'PROVIDED CONTEXT SECTIONS', you MUST respond EXACTLY with the following phrase and nothing else: 'The provided documents do not contain sufficient information to answer this question.' Do NOT attempt to infer, guess, estimate, or synthesize information not explicitly present in the context."`

### 6.3.5 Citation Requirements

*   Specify the exact format for citing sources within the answer.
    *   Example: `"For every factual statement or numerical figure you provide, you MUST cite the source using the following format: '[Source Document Name, Section Heading]'. If information comes from multiple sections, cite all relevant ones. Place citations directly after the information they support."` (Adjust format based on available metadata).

### 6.3.6 Tool Usage Instructions

*   Clearly instruct the LLM on when and how to use the provided calculation tools.
    *   Example: `"For any calculations required to answer the query (e.g., ratios, sums, averages, percentage changes), you MUST use the provided 'AVAILABLE TOOLS'. Do NOT perform calculations directly. Ensure the input arguments you provide to the tools are derived solely from numerical figures found within the 'PROVIDED CONTEXT SECTIONS'."`

### 6.3.7 Few-Shot Examples (Recommended)

*   Including 1-3 examples within the prompt can significantly improve the LLM's adherence to complex instructions and output formats. These examples should cover key scenarios.

#### 6.3.7.1 Example: Successful Contextual Answer + Citation

*   **Input Context Snippet:** `Metadata: Source Document=DocB.pdf, ..., Section Heading=Revenue Text: ...Total Sales Revenue was $150,000...`
*   **Input Query:** `What was the Sales Revenue?`
*   **Desired Output Example:** `The Sales Revenue was $150,000 [DocB.pdf, Revenue].`

#### 6.3.7.2 Example: Correct Refusal When Info Absent

*   **Input Context Snippet:** (Context does *not* mention marketing expenses)
*   **Input Query:** `What were the marketing expenses?`
*   **Desired Output Example:** `The provided documents do not contain sufficient information to answer this question.`

#### 6.3.7.3 Example: Tool Use for Calculation

*   **Input Context Snippet:** `Metadata: ...Section Heading=Assets Text: ...Total Current Assets: $145,000... --- Metadata: ...Section Heading=Liabilities Text: ...Total Current Liabilities: $40,000...`
*   **Input Query:** `Calculate the current ratio.`
*   **Desired Output Example (Illustrative LLM Thought Process leading to tool call):** `To calculate the current ratio, I need Total Current Assets and Total Current Liabilities. From the context, Total Current Assets are $145,000 [DocA.pdf, Assets] and Total Current Liabilities are $40,000 [DocA.pdf, Liabilities]. I will use the 'calculate_ratio' tool with numerator=145000 and denominator=40000.`
    *   *(LLM then makes the function call)*
    *   *(After receiving the result, e.g., `{"ratio": 3.625}`)*
*   **Final Desired Output Example:** `The current ratio is 3.63, calculated from Total Current Assets of $145,000 [DocA.pdf, Assets] and Total Current Liabilities of $40,000 [DocA.pdf, Liabilities].`

*(See Appendix A.3 for a more complete generator prompt example)*

## 6.4 Defining Calculation Tools

To ensure numerical accuracy, calculations are delegated to external Python functions via the LLM's function calling mechanism.

### 6.4.1 Identifying Necessary Tools (Sum, Avg, Ratio, Change %)

Based on common financial analysis needs, define a set of core calculation tools. Initial candidates include:

*   `sum_list(numbers: list[float]) -> float`: Calculates the sum of a list of numbers.
*   `calculate_average(numbers: list[float]) -> float`: Calculates the average of a list of numbers.
*   `calculate_ratio(numerator: float, denominator: float) -> float`: Calculates the division of two numbers.
*   `calculate_percentage_change(value_old: float, value_new: float) -> float`: Calculates the percentage change between two values.
*   *(Add others as needed, e.g., specific financial ratios like Gross Profit Margin)*

### 6.4.2 Implementing Tools as Python Functions

Each tool is implemented as a standard Python function.

#### 6.4.2.1 Input/Output Definitions

*   Functions should have clearly typed arguments and return values matching the intended calculation.
*   Inputs will typically be numbers (float/int) or lists of numbers.
*   Outputs will typically be a single number or a simple structure (e.g., a dictionary) containing the result.

#### 6.4.2.2 Error Handling (Division by Zero, Type Errors)

*   Implement robust error handling within each function.
*   Handle potential `TypeError` if inputs are not numbers.
*   Handle `ZeroDivisionError` gracefully (e.g., return `None`, `NaN`, or raise a specific custom exception that the orchestrator can catch).
*   The function should signal failure clearly if inputs are invalid or the calculation cannot be performed.

**Example `calculate_ratio` function:**

```python
import math

def calculate_ratio(numerator: float, denominator: float) -> dict | None:
    """Calculates the ratio of numerator / denominator."""
    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
        # Could return an error message dict instead
        return {"error": "Invalid input types, numerator and denominator must be numbers."}
    if denominator == 0:
         # Indicate division by zero clearly
        return {"error": "Division by zero error.", "ratio": None} # Or return math.inf or None directly
    try:
        ratio = numerator / denominator
        # Round for practical presentation, maybe 2-3 decimal places
        return {"ratio": round(ratio, 3)}
    except Exception as e:
        # Catch any unexpected errors
        return {"error": f"Calculation error: {str(e)}"}

```

### 6.4.3 Creating Tool Schemas (JSON for Gemini API)

The LLM needs a structured description (schema) of each available tool, including its name, purpose, and required parameters (name, type, description). This is typically provided in JSON format as part of the API call.

**Example JSON Schema for `calculate_ratio`:**

```json
{
  "name": "calculate_ratio",
  "description": "Calculates the ratio by dividing a numerator by a denominator (numerator / denominator).",
  "parameters": {
    "type": "object",
    "properties": {
      "numerator": {
        "type": "number",
        "description": "The value of the numerator (the number being divided)."
      },
      "denominator": {
        "type": "number",
        "description": "The value of the denominator (the number dividing the numerator). Cannot be zero."
      }
    },
    "required": ["numerator", "denominator"]
  }
}
```
*(See Appendix C for more tool schema examples)*

## 6.5 Function Calling Orchestration

The system needs logic to manage the interaction flow when the LLM decides to use a tool.

### 6.5.1 Initial Gemini API Call (with Tools)

*   The prompt (assembled context, query, instructions) and the list of available tool schemas are sent to the Gemini API.

### 6.5.2 Handling `function_call` Response

*   Instead of returning a final text answer immediately, the API response might contain a `function_call` object. This object specifies the name of the tool the LLM wants to use and the arguments it derived from the context.

### 6.5.3 Executing the Local Python Tool

1.  The orchestration logic parses the `function_call` response to get the tool name and arguments.
2.  It finds the corresponding local Python function (e.g., `calculate_ratio`).
3.  It executes the function with the provided arguments, capturing the return value (which could be the result or an error structure).

### 6.5.4 Sending `function_response` Back to Gemini

*   A second API call is made to Gemini. This call includes:
    *   The history of the conversation so far (original prompt, initial LLM response with the `function_call`).
    *   A new `function_response` part containing the structured result returned by the local Python tool execution.

### 6.5.5 Receiving the Final Natural Language Answer

*   Gemini processes the tool's result in the context of the original query and context.
*   It then generates the final natural language answer that incorporates the calculation result. This final response should *not* contain another `function_call` (unless multiple calculation steps are needed sequentially).

This orchestration ensures that complex logic and arithmetic are handled by reliable code, while the LLM focuses on understanding, context retrieval guidance, and natural language synthesis incorporating the verified tool outputs.


---

# Chapter 7: Post-processing & Attribution

Once the Generator LLM (Chapter 6) has produced a raw response, potentially incorporating results from function calls, a final set of steps are necessary to ensure the answer presented to the user is clean, meets basic validation criteria, and, crucially, provides clear attribution back to the source documents. This stage acts as a quality control layer, enhancing reliability and trustworthiness.

## 7.1 Answer Clean-up

Raw LLM outputs can sometimes contain artifacts or inconsistencies that should be removed before final presentation.

### 7.1.1 Removing Extraneous Prefixes/Suffixes

*   **Problem:** LLMs might occasionally include conversational filler, preambles ("Okay, here is the answer..."), or sign-offs ("I hope this helps!") despite instructions to be direct. They might also sometimes repeat parts of the prompt or instructions.
*   **Solution:** Implement simple string processing logic (e.g., using Python's string methods or regular expressions) to detect and remove common, predefined extraneous phrases from the beginning and end of the raw response. This ensures the final answer is concise and directly addresses the query. Care must be taken not to accidentally remove essential parts of the actual answer.

### 7.1.2 Standardizing Formatting

*   **Problem:** The LLM might format numbers, dates, or lists slightly inconsistently across different answers.
*   **Solution:** Apply light formatting rules to standardize the output. For instance:
    *   Ensure consistent decimal places for currency values (unless precision demands otherwise).
    *   Standardize date formats if extracted.
    *   Ensure consistent list formatting (e.g., bullet points).
*   **Note:** Heavy reformatting should be avoided as it risks altering the meaning intended by the LLM. The goal is consistency, not rewriting.

## 7.2 Basic Validation Checks

These are heuristic checks designed to catch common, obvious errors. They are not a substitute for the rigorous evaluation framework (Chapter 8) but serve as a quick, automated sanity check on the generated output.

### 7.2.1 Numerical Cross-Referencing (Heuristic)

*   **Goal:** To provide a basic check against numerically hallucinated values *that were supposedly extracted directly* from the context (this does *not* validate calculations performed by tools).
*   **Process:**
    1.  **Extract Numbers:** Use regular expressions to identify and extract numerical figures from the final *generated text answer*. Handle different formats (commas, decimals, potential negatives in parentheses).
    2.  **Retrieve Context:** Access the text content of the Top K context sections that were *provided* to the generator LLM for this specific query (this information must be available from the orchestration logic or logs).
    3.  **Search Context:** For each number extracted from the answer, check if that exact number (or a close, normalized representation) exists as plain text within the combined context provided to the LLM.
    4.  **Flagging:** If a number appears in the answer but *cannot* be found verbatim in the provided context, it *might* indicate a hallucination or misrepresentation (or it could be a result of a calculation). This check could trigger a warning flag internally or be logged for review. It should *not* necessarily block the answer unless confidence is very low, as it's an imperfect heuristic.
*   **Limitations:**
    *   Does not validate numbers resulting from function calls (tool calculations). The validation for those happens by trusting the Python tool's code.
    *   May produce false positives/negatives if number formats are subtly different (e.g., "1,234.50" vs "1234.5"). Requires robust normalization.
    *   Doesn't understand the *meaning* or *context* of the number, only its textual presence.

### 7.2.2 Checking for Refusal Message

*   **Goal:** To verify if the LLM correctly produced the predefined refusal message when it was instructed to (because the information was not in the context).
*   **Process:** Compare the final cleaned-up answer against the exact refusal string defined in the prompt instructions (e.g., `"The provided documents do not contain sufficient information to answer this question."`).
*   **Importance:** This validates the LLM's adherence to a critical negative constraint. Discrepancies should be logged, as they indicate potential issues with prompt adherence or faithfulness. This check is particularly useful when evaluating against the Golden Dataset entries designed to require refusal (Chapter 8).

## 7.3 Citation Generation

Providing clear and accurate attribution is fundamental to the AI CFO Assistant's reliability principle. Users must be able to trace information back to its source.

### 7.3.1 Identifying Used Context Sections

*   **Challenge:** Precisely determining *which specific sentence* within the provided context sections led to a *specific part* of the LLM's answer is extremely difficult and often unreliable, even if prompting for it.
*   **Pragmatic Approach:** The most robust and straightforward approach is to consider **all Top K context sections** that were provided to the Generator LLM (after re-ranking) as the potential sources for the *entire* generated answer. Therefore, the citations will reference these Top K parent sections.
*   **Implementation:** The list of `section_id`s for these Top K sections must be passed from the Context Assembler (Component 12) or retrieved from the logs for the current query.

### 7.3.2 Mapping Section IDs to Document Metadata

*   For each `section_id` identified in the previous step:
    1.  Query the `sections` table in the database to retrieve its associated metadata (stored in the `metadata` JSONB column).
    2.  Query the `documents` table (using the `document_id` from the section) to retrieve relevant document-level metadata.
    3.  Extract the necessary fields for the citation format (e.g., `source_filename`, `section_heading`, potentially `period_end_date` or inferred page number).

### 7.3.3 Standard Citation Format

*   **Definition:** Define a clear, consistent, and user-friendly format for displaying citations.
*   **Example Format:** `[Source: {source_filename}, Section: '{section_heading}', Period: {period_end_date}]`
*   **Implementation:** Construct the citation string(s) using the retrieved metadata for each of the Top K source sections. Append these formatted citations clearly to the end of the generated answer or integrate them contextually if feasible (though appending is simpler). If multiple sections form the basis of the answer, list all relevant citations.

**Example Final Output Structure:**

```
Based on the provided documents, the Net Income for Q1 2024 was $32,000. The primary operating expenses included Salaries & Wages ($40,000) and Rent Expense ($15,000).

[Source: SynthWidgets_IncomeStatement_Q1_2024.pdf, Section: 'SynthWidgets Inc. - Income Statement', Period: 2024-03-31]
[Source: SynthWidgets_IncomeStatement_Q1_2024.pdf, Section: 'Operating Expenses', Period: 2024-03-31]
```

By performing these post-processing and attribution steps, the system delivers a final output that is not only responsive to the user's query but also cleaned, heuristically validated, and transparently linked back to the underlying source documents, significantly enhancing user trust and the overall reliability of the AI CFO Assistant.



---

# Chapter 8: Evaluation Framework

## 8.1 Evaluation Philosophy: Proving Reliability

The AI CFO Assistant operates in a high-stakes domain where accuracy and trustworthiness are paramount. Simply demonstrating functionality is insufficient; **proving reliability** through rigorous, quantitative evaluation is a core objective of this project. This aligns with the principle of **Evaluation-Driven Development**, where objective measurements guide refinement and validate improvements.

The evaluation framework is designed to:

1.  **Quantify Key Reliability Aspects:** Measure performance against the core requirements of Numerical Accuracy, Faithfulness (Context Adherence), Attribution Accuracy, and Retrieval Effectiveness.
2.  **Identify Weaknesses:** Pinpoint specific components or stages in the RAG pipeline that are underperforming.
3.  **Measure Improvement:** Objectively assess the impact of changes (e.g., prompt tuning, component upgrades, potential future fine-tuning) by comparing evaluation results before and after modifications.
4.  **Build Confidence:** Provide concrete evidence supporting claims about the system's reliability and limitations.

This framework relies heavily on a meticulously crafted **Golden Dataset**.

## 8.2 Source Data: Synthetic Financial PDFs

As detailed in Chapter 3 and discussed previously, the system will be primarily evaluated against a corpus of **synthetically generated financial PDF documents**.

### 8.2.1 Creation Method (Excel/Sheets -> PDF Recommended)

*   The recommended method involves creating financial statement templates (Income Statement, Balance Sheet, Cash Flow Statement) in spreadsheet software (Excel, Google Sheets), populating them with plausible (but not necessarily perfectly balanced) data using simple formulas, and saving each report/period as a separate PDF. This mimics common SME workflows and provides reasonably realistic PDF structures.
*   *Alternative (Simpler Start):* Generating structured Markdown with YAML and converting to PDF using tools like `pandoc` can bootstrap the process but yields overly clean PDFs that don't test parsing robustness as effectively.

### 8.2.2 Content & Structure Guidelines

*   Include standard line items found in IS, BS, CF reports.
*   Use consistent section headings (e.g., "Revenue", "Operating Expenses", "Current Assets").
*   Vary numerical values across periods to allow for trend analysis queries.
*   Ensure metadata (Report Type, Period End Date, Currency) is present and accurate within the source data (or added during YAML generation).

### 8.2.3 Timeframe & Volume

*   Generate quarterly reports for a defined period (e.g., Q1 2020 - Q1 2025, ~21 periods).
*   The corpus should contain approximately 60-70 individual PDF report files (21 periods * 3 report types). This provides sufficient data for diverse test queries.

## 8.3 Golden Dataset Creation

The Golden Dataset is the cornerstone of the evaluation framework. It consists of question-answer pairs specifically designed to test the system against the synthetic PDF corpus. Its quality dictates the validity of the evaluation results.

### 8.3.1 Structure Per Entry (Query, Ideal Answer, Ground Truth Chunks/Sections, Numerical Values)

Each entry in the Golden Dataset (e.g., stored in a JSON or CSV file) must contain:

1.  `query_id` (str): A unique identifier for the test case.
2.  `query_text` (str): The natural language question posed to the system.
3.  `query_type` (str): Categorization (e.g., 'Simple Lookup', 'Calculation', 'Comparison', 'Refusal Expected').
4.  `ideal_answer_text` (str): The factually correct and ideally formatted answer. For refusal cases, this must be the exact predefined refusal message.
5.  `ground_truth_section_ids` (list[int]): A list of the specific `section_id`(s) from the `sections` table that contain *all* the necessary information to answer the query correctly. This requires manual identification by cross-referencing the query, ideal answer, and the ingested/chunked data.
6.  `ground_truth_embedding_ids` (list[int], optional): If recursive splitting occurs, list the specific `embedding_id`(s) corresponding to the sub-chunks needed. Useful for detailed retrieval evaluation. Defaults to mapping from `ground_truth_section_ids` if sections aren't split.
7.  `ground_truth_numerical_values` (dict, optional): If the answer involves specific numbers, store them here in a structured format (e.g., `{"Revenue": 150000, "Net Income": 32000}`) for programmatic comparison. Includes results of necessary calculations.
8.  `requires_calculation` (bool): True if answering requires using a calculation tool.
9.  `expected_tool_calls` (list[dict], optional): If calculation is required, specify the expected tool name and arguments.

### 8.3.2 Query Type Coverage

The dataset must include a diverse range of query types representative of potential user needs:

*   **Simple Lookups:** Retrieving single data points ("What was Cash on March 31, 2024?").
*   **List Extraction:** Asking for multiple items ("List major operating expenses in Q1.").
*   **Basic Calculations:** Requiring tool use ("What is the Gross Profit Margin for FY2023?").
*   **Comparisons:** Comparing values across periods or categories ("Compare revenue Q1 vs Q2 2024.").
*   **Trend Questions:** Asking about changes over time ("Describe the trend in Net Income over 2023.").
*   **Queries Requiring Synthesis:** Needing information from multiple sections (e.g., calculating ratios using figures from different parts of the Balance Sheet).
*   **Ambiguous Queries:** Queries that might retrieve irrelevant information without proper filtering/ranking.
*   **Refusal Queries:** Questions where the answer is *deliberately not present* in the source documents.

### 8.3.3 Including Cases Requiring Refusal (CRITICAL)

*   A significant portion (target 15-25%) of the Golden Dataset **must** consist of queries where the correct answer is the predefined refusal message (e.g., "The provided documents do not contain sufficient information...").
*   These queries should test:
    *   Asking for data from periods *outside* the range covered by the documents.
    *   Asking about metrics or line items *not included* in the synthetic reports.
    *   Asking questions deliberately unrelated to finance or the document content.
*   This is essential for evaluating the system's adherence to the context-only and graceful refusal constraints.

### 8.3.4 Manual Verification & Annotation Guideline

*   **Manual Effort:** Creating the Golden Dataset is labor-intensive. Every `ideal_answer_text`, `ground_truth_section_ids`, and `ground_truth_numerical_values` entry **must be manually verified** against the synthetic source documents and the ingested data in the database by the developer. Do not rely solely on LLM suggestions for creating these ground truths.
*   **Annotation Guideline:** Create a separate document outlining the rules used for annotation:
    *   How was the `ideal_answer_text` formulated (extractive, abstractive)?
    *   What was the precise rule for selecting `ground_truth_section_ids` (e.g., "minimal set of sections containing all necessary facts")?
    *   How were numerical values normalized?
    *   How were query types categorized?
    *   This guideline ensures consistency during creation and interpretation of results.

## 8.4 Metrics Definitions & Implementation

These metrics quantify the system's performance against the Golden Dataset.

### 8.4.1 Numerical Accuracy (Exact Match + Normalization)

*   **Definition:** Measures the correctness of numerical figures presented in the final answer, comparing them against `ground_truth_numerical_values`.
*   **Scope:** Applies to both directly retrieved numbers and numbers resulting from tool calculations.
*   **Implementation:**
    1.  Define a robust function `extract_numbers(text)` using regex to find and normalize numbers (handle commas, $, %, parentheses for negatives).
    2.  Extract numbers from `final_response`.
    3.  Extract expected numbers from `ground_truth_numerical_values`.
    4.  Compare extracted numbers to expected numbers. For simple lookups, check for exact matches. For calculated answers, compare the final calculated value.
    5.  **Metric:** Percentage of queries where *all* relevant numerical values in the response match the ground truth. (Or calculate precision/recall of correctly reported numbers across all queries).

### 8.4.2 Faithfulness (LLM-as-judge Methodology & Prompt)

*   **Definition:** Measures the degree to which the generated answer is strictly grounded in the *provided context*.
*   **Method:** LLM-as-judge.
    1.  For each query response, retrieve the exact `final_context_section_ids` that were fed to the generator LLM (from logs). Fetch the corresponding `original_section_text`.
    2.  Use a capable LLM (e.g., Gemini Pro, Claude 3.5 Sonnet, GPT-4o) as the judge.
    3.  **Prompt the Judge:** (See Appendix A.4 for full prompt)
        ```
        You are an impartial evaluator assessing an AI Assistant's answer based *only* on the provided context.
        Context Chunks:
        [Insert concatenated text of the context sections provided to the generator]
        ---
        Generated Answer:
        [Insert the AI CFO Assistant's final_response text]
        ---
        Question: Is every factual statement and numerical figure within the 'Generated Answer' directly and solely supported by the information present in the 'Context Chunks'? Answer ONLY 'Yes' or 'No'.
        ```
    4.  Record the 'Yes'/'No' output.
*   **Metric:** Percentage of queries judged as 'Yes' (fully faithful).
*   **Caveats:** Document the judge model/prompt used. Acknowledge potential judge biases and limitations. Manual review of 'No' cases is recommended.

### 8.4.3 Attribution Accuracy (Precision/Recall/F1 of Citations)

*   **Definition:** Measures how accurately the generated citations correspond to the actual source sections containing the necessary information.
*   **Implementation:**
    1.  Parse the `citations_generated` from the system's output for a query (extract the cited `section_id`s or their identifiers). Let this be `Cited_Sections`.
    2.  Retrieve the `ground_truth_section_ids` for that query from the Golden Dataset. Let this be `Ground_Truth_Sections`.
    3.  Calculate:
        *   `True_Positives (TP) = |Cited_Sections ∩ Ground_Truth_Sections|`
        *   `False_Positives (FP) = |Cited_Sections - Ground_Truth_Sections|` (Cited irrelevant sections)
        *   `False_Negatives (FN) = |Ground_Truth_Sections - Cited_Sections|` (Failed to cite relevant sections)
    4.  **Precision:** `TP / (TP + FP)`
    5.  **Recall:** `TP / (TP + FN)`
    6.  **F1 Score:** `2 * (Precision * Recall) / (Precision + Recall)`
*   **Metric:** Average Precision, Recall, and F1 score across all non-refusal queries in the Golden Dataset.

### 8.4.4 Retrieval Performance (Precision@K, Recall@K, MRR)

*   **Definition:** Measures the effectiveness of the retrieval pipeline (Filter + Vector Search + Re-ranker) *before* generation.
*   **Implementation:**
    1.  For each golden query, execute only the retrieval steps up to and including the re-ranker (Component M). Get the final ranked list of Top K `reranked_section_ids`.
    2.  Retrieve the `ground_truth_section_ids` for that query.
    3.  Calculate:
        *   **Precision@K:** Fraction of the top K retrieved sections that are in the ground truth set.
        *   **Recall@K:** Fraction of the *total* ground truth sections that are found within the top K retrieved sections.
        *   **Mean Reciprocal Rank (MRR):** Average of `1 / rank` for the first relevant section found across all queries (where `rank` is the position in the retrieved list). Gives a sense of how high up the first correct result appears.
*   **Metric:** Average Precision@K, Recall@K (e.g., K=3, 5), and MRR across all non-refusal queries.

### 8.4.5 Refusal Accuracy

*   **Definition:** Measures the system's ability to correctly refuse to answer when the information is not in the context.
*   **Scope:** Applies only to queries in the Golden Dataset explicitly designed to require refusal.
*   **Implementation:**
    1.  For each refusal query, check if the `final_response` exactly matches the predefined refusal message.
    2.  **Metric:** Percentage of refusal queries where the system produced the correct refusal message.

## 8.5 Automated Evaluation Script (`evaluate.py`)

To enable efficient iteration, the evaluation process must be automated.

### 8.5.1 Input: Golden Dataset, System Endpoint/Functions

*   The script takes the path to the Golden Dataset file (e.g., `golden_dataset.json`).
*   It needs access to the AI CFO Assistant's core query processing function or API endpoint.

### 8.5.2 Process: Run Queries, Collect Responses, Calculate Metrics

1.  Load the Golden Dataset.
2.  For each entry in the dataset:
    *   Send the `query_text` to the AI CFO Assistant.
    *   Receive the `final_response` and `citations_generated`.
    *   Access logged data (e.g., `final_context_section_ids`) for the query.
    *   Calculate Numerical Accuracy using `ground_truth_numerical_values`.
    *   Call the LLM-as-judge for Faithfulness evaluation using the logged context and response.
    *   Calculate Attribution Accuracy using `citations_generated` and `ground_truth_section_ids`.
    *   (Optionally run retrieval-only mode to calculate Retrieval Metrics).
    *   Calculate Refusal Accuracy if it's a refusal query.
3.  Aggregate results across all queries.

### 8.5.3 Output: Metrics Report (CSV, JSON, or Formatted Text)

*   The script outputs a summary report containing the average scores for all defined metrics (Overall Accuracy, Faithfulness Rate, Avg. Attribution F1, Avg. Retrieval Recall@5, Refusal Accuracy, etc.).
*   Optionally, output detailed results per query for failure analysis.

## 8.6 Evaluation Strategy: Baseline & Iteration

1.  **Establish Baseline:** After implementing the initial version of the full pipeline, run the `evaluate.py` script to establish baseline performance across all metrics.
2.  **Analyze Bottlenecks:** Identify the metrics with the lowest scores. This indicates the weakest parts of the system (e.g., low Retrieval Recall suggests issues in retrieval/ranking; low Faithfulness suggests problems in generation/prompting).
3.  **Implement Enhancements:** Make targeted changes to address the identified bottlenecks (e.g., improve prompts, tune re-ranker parameters, fix bugs).
4.  **Re-evaluate:** Run `evaluate.py` again after *each significant change* to objectively measure its impact on all metrics. Ensure improvements in one area don't negatively affect others (regression testing).
5.  **Document:** Record the evaluation scores for each iteration/version of the system in the project documentation or an experiment tracking tool.

This systematic, data-driven approach ensures that development efforts are focused on areas that yield the most significant improvements in overall system reliability.


---

# Chapter 9: Implementation Details & Configuration

This chapter delves into the practical aspects of building the AI CFO Assistant, covering the technology stack, library choices, environment setup, configuration management, recommended code structure, and version control practices. Adhering to good implementation practices is crucial for maintainability, reproducibility, and enabling the rapid iteration central to this project's methodology.

## 9.1 Core Technology Stack Summary

As outlined flexibly in Chapter 1, the system relies on a combination of core programming language features, specialized libraries, and external API services.

*   **Language:** Python (Version 3.10 or later recommended for features like improved type hinting and structural pattern matching).
*   **LLM Services:** APIs for Multimodal Parsing, Query Decomposition, and Generation/Function Calling (e.g., Google Gemini family). Requires API keys and client libraries.
*   **Embedding Service:** API for a high-performance text embedding model (e.g., Nomic via Fireworks AI). Requires API key and client interaction (e.g., `requests` or provider-specific library).
*   **Vector Database:** Managed PostgreSQL service with `pgvector` extension enabled (e.g., NeonDB). Requires database connection credentials.
*   **Local Compute:** Primarily for orchestration logic, running the cross-encoder re-ranker, executing calculation tools, and potentially lightweight query analysis.

## 9.2 Key Python Libraries

Beyond the specific API client libraries provided by Google, Fireworks AI (or alternatives), the following Python libraries are essential or highly recommended:

*   **Database Interaction:**
    *   `psycopg2-binary` or `asyncpg`: Standard PostgreSQL adapters for Python to interact with NeonDB. `asyncpg` is preferred if building an asynchronous application (e.g., with FastAPI).
    *   `SQLAlchemy` (Optional): Provides an Object-Relational Mapper (ORM) which can simplify database interactions compared to writing raw SQL, especially for complex inserts and updates. Can be used with `psycopg2` or `asyncpg`.
*   **NLP & Embeddings:**
    *   `sentence-transformers`: Essential for easily downloading, caching, and running cross-encoder models locally for the re-ranking step. Can also be used for managing embedding models if self-hosting is ever considered.
    *   `tiktoken` (or similar): A fast tokenizer useful for accurately counting tokens to ensure chunk sizes stay within embedding model limits, especially if using models aligned with OpenAI tokenization. Check compatibility with the chosen embedding model.
*   **API Interaction:**
    *   `requests`: Standard library for making HTTP requests, necessary if interacting directly with REST APIs for embeddings or other services.
    *   `google-generativeai`: Official Python client library for interacting with the Gemini API suite.
*   **Configuration & Environment:**
    *   `PyYAML`: For loading configuration parameters from YAML files (`config.yaml`).
    *   `python-dotenv`: For loading sensitive credentials (API keys, DB passwords) from a `.env` file into environment variables, keeping secrets out of the codebase.
*   **Data Handling & Utilities:**
    *   `pandas` (Optional but recommended): Useful for handling the Golden Dataset (loading from CSV/JSON, manipulating data) and potentially for structuring data before inserting into the database.
    *   `numpy`: Often a dependency for ML/NLP libraries; provides numerical computing capabilities.
    *   `PyMuPDF` / `pdfplumber` (Contingency): If the primary Gemini Vision parsing fails dramatically for some PDFs, these libraries could be used as fallbacks for basic text extraction, although they lack multimodal understanding.
    *   `mistune` (Optional): A fast Markdown parser, potentially useful for implementing the heading-based chunking strategy if more robust parsing than regex is needed.
    *   `logging`: Python's built-in logging module for implementing the essential logging described in Chapter 10.
*   **Interface (Optional):**
    *   `streamlit`: For rapidly building a simple web-based UI for demonstration.
    *   `argparse`: For creating a command-line interface (CLI).

*(A complete list should be maintained in a `requirements.txt` file).*

## 9.3 Environment Setup

Consistent development and deployment environments are critical.

### 9.3.1 `requirements.txt`

*   A `requirements.txt` file must list all direct Python dependencies with specific version numbers (or minimum compatible versions) to ensure reproducibility. Use `pip freeze > requirements.txt` after setting up the environment.
*   It's highly recommended to use a virtual environment tool (`venv`, `conda`) to isolate project dependencies.
    ```bash
    # Example setup using venv
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

### 9.3.2 Environment Variables (`.env`) for Secrets

*   **NEVER** commit API keys, database passwords, or other sensitive credentials directly into the Git repository.
*   Use a `.env` file (add this file to `.gitignore`) to store these secrets.
*   Use the `python-dotenv` library to load these variables into the environment when the application starts.

**Example `.env` file:**

```dotenv
# Google AI API Key
GEMINI_API_KEY="your_gemini_api_key_here"

# Fireworks AI API Key
FIREWORKS_API_KEY="your_fireworks_api_key_here"

# NeonDB Connection String (or individual components)
DATABASE_URL="postgresql://user:password@host:port/dbname"
# Alternatively:
# DB_USER="your_db_user"
# DB_PASSWORD="your_db_password"
# DB_HOST="your_neon_host"
# DB_PORT="5432"
# DB_NAME="your_db_name"
```

**Example Python code using `dotenv`:**

```python
import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

gemini_api_key = os.getenv("GEMINI_API_KEY")
db_url = os.getenv("DATABASE_URL")

# Use these variables to configure API clients and DB connections
```

## 9.4 Configuration Management

Hardcoding parameters like model names, file paths, retrieval thresholds, or prompts makes the system inflexible and difficult to iterate on.

### 9.4.1 Using YAML or Python Files for Config

*   Store non-sensitive configuration parameters in a dedicated file, typically `config.yaml` or `config.py`. YAML is often preferred for its human-readable structure.
*   Load this configuration file at application startup.

### 9.4.2 Configurable Parameters (Model Names, Thresholds, Prompts)

The configuration file should define parameters such as:

*   **Model Identifiers:**
    *   `PARSER_MODEL_ID: "gemini-1.5-pro-vision-001"`
    *   `EMBEDDING_MODEL_ID: "nomic-embed-text-v1.5"` (Potentially with API provider info)
    *   `GENERATOR_MODEL_ID: "gemini-1.5-pro-001"`
    *   `DECOMPOSER_MODEL_ID: "gemini-1.5-flash-001"`
    *   `RERANKER_MODEL_ID: "ms-marco-MiniLM-L-6-v2"`
*   **API Endpoints:** Base URLs for embedding or other custom APIs.
*   **Retrieval Parameters:**
    *   `VECTOR_SEARCH_LIMIT: 50` (Initial candidates from vector search)
    *   `RERANKER_TOP_K: 5` (Final context sections for generator)
*   **Chunking Parameters:**
    *   `CHUNK_TOKEN_LIMIT: 8000`
    *   `CHUNK_OVERLAP_TOKENS: 100` (If using overlap in recursive splitting)
*   **Prompt Templates:** Store paths to prompt template files or the templates themselves (especially useful if prompts are long or complex).
*   **File Paths:** Paths to data directories, log files, Golden Dataset.
*   **Database Settings:** (If not using DATABASE_URL) Separate DB host, port, name.

**Example `config.yaml` snippet:**

```yaml
models:
  parser: "gemini-1.5-pro-vision-001"
  embedding: "nomic-embed-text-v1.5" # Reference specific implementation/provider if needed
  generator: "gemini-1.5-pro-001"
  reranker: "ms-marco-MiniLM-L-6-v2"

retrieval:
  vector_search_limit: 50
  reranker_top_k: 5

chunking:
  token_limit: 8000

paths:
  golden_dataset: "data/evaluation/golden_dataset.json"
  log_file: "logs/app.log" # Or configure DB logging

prompts:
  generator_template_path: "config/prompts/generator_v3.prompt"
  # ... other prompts
```

**Example Python code loading config:**

```python
import yaml

def load_config(path="config/config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
generator_model_id = config['models']['generator']
reranker_top_k = config['retrieval']['reranker_top_k']
# ... use other config values
```

## 9.5 Recommended Code Structure (Modularity)

A well-organized codebase is essential for maintainability and collaboration. Employing a modular structure makes it easier to understand, test, and modify individual components.

### 9.5.1 Example Directory Layout (`src/`, `scripts/`, `config/`, `data/`)

```
aí-cfo-assistant/
├── .env                  # Store API keys, DB credentials (add to .gitignore!)
├── .gitignore            # Git ignore file
├── config/               # Configuration files and prompt templates
│   ├── config.yaml
│   └── prompts/
│       ├── generator.prompt
│       └── ...
├── data/                 # Data files (synthetic PDFs, golden dataset)
│   ├── source_pdfs/
│   │   └── ...
│   └── evaluation/
│       └── golden_dataset.json
├── notebooks/            # Jupyter notebooks for experimentation, analysis
├── scripts/              # Standalone scripts (ingestion, evaluation)
│   ├── ingest.py
│   └── evaluate.py
├── src/                  # Main source code library
│   ├── __init__.py
│   ├── parsing.py        # PDF Parsing, Markdown formatting
│   ├── chunking.py       # Semantic chunking logic
│   ├── embedding.py      # Embedding generation, API interaction
│   ├── storage.py        # Database schema setup, interaction logic
│   ├── retrieval.py      # Full retrieval pipeline (decomp, filter, search, rerank)
│   ├── generation.py     # Generator prompting, function calling orchestration
│   ├── tools.py          # Calculation tool functions
│   ├── evaluation_utils.py # Helper functions for evaluation metrics
│   ├── postprocessing.py # Answer cleanup, validation, citation generation
│   └── logging_config.py # Setup for logging
├── tests/                # Unit and integration tests
│   ├── test_parsing.py
│   └── ...
├── requirements.txt      # Python dependencies
├── README.md             # Project overview
└── main_cli.py           # Example CLI entry point
# Or main_streamlit.py    # Example Streamlit app entry point
```

### 9.5.2 Modules (e.g., `parsing`, `embedding`, `retrieval`, `generation`, `evaluation`, `tools`)

*   Break down the core logic into distinct Python modules (`.py` files within `src/`) based on functionality, as shown in the example layout.
*   Each module should encapsulate related functions and classes (e.g., `retrieval.py` contains functions for filtering, vector search, re-ranking).
*   Use clear function/class names and docstrings to explain purpose, arguments, and return values.
*   Strive for low coupling (modules should depend on each other minimally) and high cohesion (related logic should reside within the same module).

## 9.6 Version Control (Git & GitHub)

*   Use **Git** for version control from the very beginning of the project.
*   Commit changes frequently with clear, descriptive messages.
*   Use a `.gitignore` file to exclude virtual environments (`venv/`), `.env` files, sensitive data, large intermediate files, and IDE/OS-specific files.
*   Utilize branches for developing new features or implementing enhancements (`feature/improve-reranking`, `fix/parsing-bug`). Merge back to the main branch (`main` or `master`) after testing.
*   Host the repository on a platform like **GitHub** for backup, collaboration (if applicable), and potentially showcasing the project.

By following these implementation practices, the AI CFO Assistant project will be more robust, easier to manage, and well-prepared for the iterative development and evaluation cycles required to achieve its reliability goals.



---

# Chapter 10: Logging & Observability

In complex systems like RAG pipelines involving multiple API calls, data transformations, and probabilistic components (LLMs), understanding *what* happened during a query, *why* it happened, and *where* things might have gone wrong is crucial. Comprehensive **Logging** provides the raw data for this **Observability**. This chapter details the logging strategy, schema, implementation, and use cases for the AI CFO Assistant.

## 10.1 Importance of Logging in RAG Systems

Effective logging serves multiple critical purposes:

1.  **Debugging:** When a query produces an incorrect, unfaithful, or poorly cited answer, detailed logs are the primary tool for tracing the execution flow, inspecting intermediate data (like retrieved chunks and LLM prompts), and identifying the root cause of the failure.
2.  **Performance Analysis:** Logging latency at different stages (retrieval, re-ranking, LLM generation, tool execution) helps pinpoint performance bottlenecks.
3.  **Evaluation & Analysis:** Logs provide the necessary data (e.g., the exact context sent to the LLM) required by the evaluation framework (Chapter 8) to calculate metrics like Faithfulness. Analyzing aggregated logs can reveal patterns, common failure modes, or frequently retrieved sections.
4.  **Cost Monitoring:** Logging token counts for LLM and embedding API calls allows for cost estimation and tracking.
5.  **Reproducibility:** Logs capture the state and inputs/outputs of various components, aiding in reproducing specific query behaviors.
6.  **Auditing & Compliance (Future):** While not a primary FYP focus, robust logs form the foundation for future audit trails required in production environments, especially in finance.

Simply put, without good logging, operating and improving a non-trivial RAG system becomes exponentially harder.

## 10.2 Logging Schema (`query_logs` Table Deep Dive)

The `query_logs` table in the NeonDB database serves as the central repository for interaction data. Each row should represent a single end-to-end query processed by the system. The schema needs to capture sufficient detail from each stage:

*(Referencing schema from Chapter 4, adding detail and rationale)*

```sql
-- query_logs Table Definition (PostgreSQL syntax)
CREATE TABLE IF NOT EXISTS query_logs (
    log_id BIGSERIAL PRIMARY KEY,                          -- Unique identifier for the log entry
    session_id VARCHAR(255),                             -- Optional: Identifier for a user session (if applicable)
    query_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- When the query processing started
    user_query TEXT NOT NULL,                              -- The original query input by the user

    -- Query Processing Stages
    decomposed_sub_queries JSONB,                        -- JSON array of sub-queries if decomposition occurred, else NULL
    metadata_filters_applied JSONB,                    -- JSON object representing filters applied (e.g., {'fiscal_year': 2023})
    retrieval_method VARCHAR(50),                        -- Method used ('MetadataFilter+Vector', 'Hybrid', etc.)

    -- Retrieval Results
    retrieved_embedding_ids BIGINT[],                    -- Array of embedding_ids from initial retrieval (vector/hybrid)
    retrieved_embedding_scores FLOAT[],                  -- Corresponding similarity scores (optional)
    reranked_section_ids BIGINT[],                       -- Array of section_ids after re-ranking (ordered)
    reranked_section_scores FLOAT[],                     -- Corresponding cross-encoder scores (ordered)
    final_context_section_ids BIGINT[] NOT NULL,         -- Array of section_ids actually used as context for the generator

    -- Generation Stage
    llm_prompt TEXT NOT NULL,                              -- The full prompt sent to the generator LLM (including context)
    generator_model_id VARCHAR(100),                     -- Identifier of the generator model used
    raw_llm_response TEXT,                               -- The raw text output from the generator LLM
    tool_calls JSONB,                                    -- JSON array of objects detailing requested tool calls (name, args)
    tool_responses JSONB,                                -- JSON array of objects detailing results returned by tools

    -- Final Output & Evaluation Links
    final_response TEXT,                                 -- The final, cleaned-up response shown to the user
    citations_generated JSONB,                           -- JSON array of formatted citation strings or objects
    evaluation_results JSONB,                            -- Optional: Store calculated metrics if evaluated automatically (link to evaluation run ID)
    status VARCHAR(50) DEFAULT 'Success',                -- 'Success', 'Failure', 'Refused'
    error_message TEXT,                                  -- Store error details if processing failed

    -- Performance & Cost
    latency_ms_total INTEGER,                            -- Total processing time in milliseconds
    latency_ms_retrieval INTEGER,                        -- Time spent in retrieval stages (filter, search, rerank)
    latency_ms_generation INTEGER,                       -- Time spent waiting for generator LLM (including tool calls)
    token_count_prompt INTEGER,                          -- Tokens in the generator prompt
    token_count_completion INTEGER,                      -- Tokens in the raw LLM completion
    estimated_cost_usd DECIMAL(10, 6)                    -- Estimated API costs for this query

);

-- Create indexes for potential querying of logs
CREATE INDEX idx_query_logs_timestamp ON query_logs (query_timestamp);
-- Add other indexes as needed, e.g., on status or user_id if implemented
```

### 10.2.1 Capturing Key Information at Each Stage

*   **Input:** Log the raw query and any session identifiers.
*   **Decomposition/Filtering:** Log sub-queries and applied filters to understand how the search was scoped.
*   **Retrieval:** Log the IDs (and ideally scores) from both the initial retrieval and after re-ranking. Crucially, log the final `final_context_section_ids` – this is essential for Faithfulness evaluation.
*   **Generation:** Log the *exact prompt* sent to the generator, the model used, the raw response, and detailed information about any tool calls (requested name, arguments) and their results.
*   **Output:** Log the final processed response and the generated citations.
*   **Status/Errors:** Log success/failure status and any error messages encountered.
*   **Performance:** Log total latency and potentially break it down by major stages (retrieval vs. generation). Log token counts for cost tracking.

### 10.2.2 Linking Logs to Evaluation Results

The `evaluation_results` JSONB field (or a separate linking table) can be used to associate a specific query log entry with the detailed evaluation metrics calculated for it when running the automated evaluation pipeline (Chapter 8). This allows tracing back from a poor evaluation score to the specific log data for that query to understand the failure.

## 10.3 Logging Implementation

### 10.3.1 Using Python's `logging` Module

*   Leverage Python's built-in `logging` module for flexibility and standardization.
*   Configure the logger (e.g., in `src/logging_config.py`) to:
    *   Set appropriate logging levels (e.g., INFO for standard flow, DEBUG for verbose details, ERROR for failures).
    *   Define a structured log format (e.g., JSON) that includes timestamp, log level, module name, and the detailed message/data payload. JSON formatting makes logs easier to parse and query later.
    *   Configure handlers to direct logs to the desired destinations (e.g., console for development, file for persistence, database handler).

**Example `logging_config.py` (Conceptual):**

```python
import logging
import logging.handlers
# Assume a custom handler for writing to Postgres/NeonDB exists
# from .db_log_handler import PostgresLogHandler

def setup_logging(config):
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Basic JSON Formatter example
    # json_format = logging.JSONFormatter(
    #     '{"asctime": "%(asctime)s", "name": "%(name)s", "levelname": "%(levelname)s", "message": "%(message)s"}'
    # )

    logger = logging.getLogger('AI_CFO') # Root logger for the application
    logger.setLevel(logging.INFO) # Set minimum level

    # Console Handler (for development)
    ch = logging.StreamHandler()
    ch.setFormatter(log_format)
    logger.addHandler(ch)

    # File Handler (optional persistence)
    # log_file = config.get('paths', {}).get('log_file', 'logs/app.log')
    # fh = logging.FileHandler(log_file)
    # fh.setFormatter(log_format) # Or JSON formatter
    # logger.addHandler(fh)

    # Database Handler (Primary destination)
    # db_handler = PostgresLogHandler(
    #     host=config['database']['host'], # Load credentials securely
    #     # ... other db params
    #     table_name='query_logs'
    # )
    # db_handler.setFormatter(json_format) # DB handler likely expects structured data
    # logger.addHandler(db_handler)

    # Add more handlers as needed

    # Example usage in other modules:
    # import logging
    # logger = logging.getLogger('AI_CFO.retrieval')
    # logger.info("Starting retrieval for query X", extra={'query_id': 'xyz'})
    # logger.debug("Retrieved embedding IDs: %s", retrieved_ids, extra={'query_id': 'xyz'})

```

### 10.3.2 Writing Logs to NeonDB

*   Implement a custom logging handler or use direct database insertion logic within the application flow to write structured log data to the `query_logs` table.
*   Structure the data according to the schema defined in Section 10.2.
*   Ensure database writes are efficient and potentially batched if logging volume is high, being careful not to significantly impact overall query latency. Asynchronous logging might be considered in a production system.

## 10.4 Use Cases

Leveraging the logged data enables several critical activities:

### 10.4.1 Debugging Failures

*   When a user reports an incorrect answer, query the `query_logs` table for that interaction.
*   Inspect the `user_query`, `metadata_filters_applied`, `retrieved_embedding_ids`, `reranked_section_ids`, `final_context_section_ids`, `llm_prompt`, `raw_llm_response`, `tool_calls`, `final_response`, and `error_message` fields.
*   This allows tracing the error: Was it incorrect filtering? Poor retrieval? Bad re-ranking? Hallucination despite context? Failed tool call? Incorrect prompt?

### 10.4.2 Performance Analysis (Latency)

*   Query the `query_logs` table, aggregating latency fields (`latency_ms_total`, `latency_ms_retrieval`, `latency_ms_generation`).
*   Calculate average, median, and percentile latencies.
*   Identify queries with unusually high latency and investigate the corresponding logs to see which stage took the longest.

### 10.4.3 Cost Estimation

*   Query and aggregate `token_count_prompt` and `token_count_completion` fields.
*   Apply pricing models for the specific LLM and embedding APIs used (from `generator_model_id`, `embedding_model_used`) to estimate query costs and track overall API expenditure.

### 10.4.4 Auditing & Compliance (Future)

*   In a production setting, these logs form the basis of an audit trail, recording who queried what, when, what information was retrieved, and what answer was provided. Additional fields (like `user_id`) would be needed for full auditing.

Effective logging is not an afterthought but a fundamental requirement for building, evaluating, and maintaining a reliable and understandable AI system like the AI CFO Assistant.


---

# Chapter 11: Deployment & Scalability (Considerations)

While the primary focus of the Final Year Project (FYP) is to develop and rigorously evaluate a reliable prototype of the AI CFO Assistant, it's important to consider how such a system might be deployed and scaled beyond the initial development environment. This chapter explores deployment options suitable for the FYP demonstration and discusses key factors influencing scalability and potential production deployment paths.

## 11.1 FYP Deployment (Local / Simple Cloud)

For the purpose of the FYP demonstration and evaluation, a simple deployment strategy is sufficient and appropriate. The goal is to showcase the core functionality and reliability proved by the evaluation framework.

### 11.1.1 Running via CLI or Streamlit App

*   **Command Line Interface (CLI):**
    *   **Implementation:** Use Python's `argparse` module to create a script (`main_cli.py`) that accepts user queries (and potentially PDF file paths for ingestion) as command-line arguments. The script orchestrates the RAG pipeline and prints the final response and citations to the console.
    *   **Pros:** Simple to implement, excellent for automated testing and evaluation scripts, requires minimal dependencies beyond the core logic.
    *   **Cons:** Less user-friendly for interactive demonstration compared to a GUI.
*   **Simple Web App (Streamlit):**
    *   **Implementation:** Use the `streamlit` library to rapidly build an interactive web interface (`main_streamlit.py`). This allows users to upload PDFs (via `st.file_uploader`), input queries in a text box (`st.text_input`), click a button to process, and see the formatted response and citations displayed dynamically on the page (`st.write`, `st.markdown`).
    *   **Pros:** Provides a much better visual demonstration experience, allows easier interaction, still relatively simple to develop.
    *   **Cons:** Adds a web framework dependency, might require slightly more effort to integrate with automated evaluation scripts compared to a pure CLI.
*   **Recommendation:** Develop **both**. Use the CLI for backend logic testing and automated evaluation runs. Use the Streamlit app for interactive demos and showcasing the user-facing potential.

### 11.1.2 Containerization (Docker)

*   **Concept:** Encapsulating the application, its dependencies (Python interpreter, libraries listed in `requirements.txt`), and necessary configurations into a standardized container image using Docker.
*   **Benefits for FYP:**
    *   **Consistency:** Ensures the application runs identically on any machine with Docker installed (developer's laptop, supervisor's machine, presentation environment), eliminating "it works on my machine" issues.
    *   **Dependency Management:** Packages all necessary libraries, simplifying setup for others who need to run or evaluate the project.
    *   **Simplified Deployment:** Makes it easier to deploy the demo application (e.g., the Streamlit app) to simple cloud services if desired.
*   **Implementation:** Create a `Dockerfile` that:
    1.  Starts from a base Python image (e.g., `python:3.11-slim`).
    2.  Sets up a working directory.
    3.  Copies `requirements.txt` and installs dependencies using `pip`.
    4.  Copies the project source code (`src/`, `config/`, etc.) into the container.
    5.  Copies entry point scripts (`main_cli.py`, `main_streamlit.py`).
    6.  Defines environment variables (though secrets are better injected at runtime).
    7.  Specifies the command to run when the container starts (e.g., `CMD ["streamlit", "run", "main_streamlit.py"]`).
*   **Recommendation:** Strongly recommended for ensuring reproducibility and simplifying demonstration setup.

## 11.2 Production Deployment Considerations (Beyond FYP)

Moving beyond the FYP requires addressing aspects typical of production software systems.

### 11.2.1 Web Application Framework (Flask, FastAPI)

*   For a multi-user web application, a more robust framework than Streamlit is needed.
*   **FastAPI:** A modern, high-performance Python framework ideal for building APIs. Its asynchronous nature (`async/await`) is well-suited for handling I/O-bound operations like waiting for LLM APIs or database queries, potentially improving concurrency and throughput. Good choice if the core logic will be exposed as an API consumed by a separate frontend.
*   **Flask/Django:** More traditional, mature frameworks suitable for building both APIs and server-rendered web applications. Django includes more built-in features (ORM, admin interface), while Flask is more lightweight and flexible.
*   **Choice:** Depends on architectural decisions (API-first vs. monolithic) and team familiarity. FastAPI is often favored for new API-centric AI applications.

### 11.2.2 Cloud Platforms (AWS, GCP, Azure)

*   Deploying to a major cloud provider offers scalability, reliability, and a wide range of managed services.
*   **Compute Options:**
    *   **Virtual Machines (VMs):** (EC2, Compute Engine, Azure VMs) Provide full control but require manual management of OS, patching, scaling.
    *   **Container Orchestration:** (Kubernetes - EKS, GKE, AKS) Standard for managing containerized applications (like the Docker image). Handles scaling, load balancing, self-healing but has a steeper learning curve.
    *   **Serverless Functions:** (AWS Lambda, Google Cloud Functions, Azure Functions) Suitable for specific, event-driven parts of the pipeline (e.g., triggering ingestion on file upload) but might be challenging for orchestrating the entire stateful RAG query flow.
    *   **Managed App Platforms:** (AWS App Runner, Google Cloud Run, Azure App Service) Simplify deployment of containerized web applications, handling scaling and load balancing automatically. Often a good balance between control and ease of use.
*   **Database:** Use managed database services (like NeonDB, AWS RDS, Cloud SQL, Azure Database for PostgreSQL) that support `pgvector`.
*   **API Integration:** Cloud platforms offer secure ways to manage API keys (Secrets Manager, Key Vault) and integrate with cloud-native AI services if desired (though this project relies primarily on external APIs).

### 11.2.3 Serverless vs. VMs

*   **Serverless (Functions/Managed Apps):** Pros: Automatic scaling, pay-per-use, reduced operational overhead. Cons: Potential cold starts, execution time limits, less control over the environment, managing state across function calls can be complex for RAG.
*   **VMs/Containers:** Pros: More control, no cold starts (if always running), suitable for long-running processes. Cons: Need to manage scaling, patching, potentially higher idle costs.
*   **Hybrid:** Often the best approach. Use serverless functions for event triggers (e.g., file uploads) and a containerized application (on Cloud Run, App Runner, or Kubernetes) for the main API/query processing logic.

## 11.3 Scalability Factors

Scaling the AI CFO Assistant involves considering bottlenecks across its components.

### 11.3.1 Database (NeonDB Auto-scaling)

*   **Strength:** Using a serverless database like NeonDB largely handles database read/write scaling automatically.
*   **Considerations:** Ensure appropriate indexing (vector and metadata) is maintained. Monitor query performance under load. Extremely high ingestion or query rates might eventually require tuning NeonDB compute endpoints or considering read replicas (if supported/needed).

### 11.3.2 API Rate Limits & Quotas (Gemini, Fireworks AI)

*   **Bottleneck:** External APIs have usage limits (requests per minute, tokens per minute). Heavy usage can lead to throttling (HTTP 429 errors).
*   **Mitigation:**
    *   Implement **retry logic with exponential backoff** for API calls.
    *   Monitor usage against quotas provided by the API vendors.
    *   Consider batching requests where possible (especially for embeddings).
    *   Investigate higher usage tiers or enterprise plans if limits are consistently hit in production.
    *   Potentially introduce application-level rate limiting or queuing for user requests if backend APIs are the bottleneck.

### 1.3.3 Concurrent Users

*   **Impact:** More users mean more simultaneous queries hitting the system.
*   **Scalability:** Requires scaling the *application compute* layer (the Python code orchestrating the RAG pipeline).
    *   If containerized, the orchestrator (Kubernetes, Cloud Run) needs to automatically launch more container instances based on CPU/memory usage or request load.
    *   If using asynchronous frameworks (FastAPI + asyncpg), a single instance can handle more concurrent I/O-bound requests efficiently.

### 11.3.4 Computation (Re-ranking, Tool Execution)

*   **Re-ranking:** The cross-encoder step can be CPU-intensive, especially if re-ranking many candidates or using a large model. This might become a bottleneck under high load.
    *   *Mitigation:* Optimize the number of candidates re-ranked. Use efficient model implementations. Consider deploying the re-ranker as a separate microservice that can be scaled independently, potentially using GPU instances if necessary (though likely overkill initially).
*   **Tool Execution:** Python calculation tools are generally fast, but complex tools or high concurrency could load the application instances. Ensure tools are efficient and stateless.

## 11.4 Cost Management

Running AI systems, especially those relying on powerful LLM APIs, requires careful cost consideration.

*   **API Costs:**
    *   **LLMs (Gemini):** Priced based on input/output tokens, potentially higher for Vision or 1.5 Pro models. Function calling might incur additional overhead. Track token counts diligently (log them!).
    *   **Embeddings (Fireworks AI):** Priced based on the number of tokens processed/embeddings generated. Batching helps efficiency.
*   **Database Costs (NeonDB):** Typically based on storage used, compute time, and data transfer. Serverless models adjust compute costs based on usage.
*   **Compute Costs:** Costs for running the application containers/VMs (CPU, memory, runtime duration).
*   **Monitoring:** Implement cost tracking by correlating logged token counts and API usage with provider pricing. Set up budget alerts in cloud platforms.
*   **Optimization:**
    *   Use caching where appropriate (e.g., cache embeddings for identical chunks if re-ingestion occurs, though usually embedding is done once).
    *   Choose the most cost-effective models that meet performance requirements (e.g., use Gemini Flash instead of Pro where sufficient).
    *   Optimize prompts to be concise while effective.
    *   Tune database/compute resources to match actual load.

By considering these deployment and scalability factors early, even during the FYP stage, the project maintains a path towards potential real-world application and avoids architectural choices that might hinder future growth.

---

# Chapter 12: Future Work & Enhancements

The AI CFO Assistant developed during this Final Year Project establishes a strong foundation for providing reliable financial insights to SMEs. However, the field of AI and RAG is rapidly evolving, and numerous avenues exist for future enhancements to improve capabilities, robustness, and user experience. This chapter outlines potential directions, categorized by focus area.

## 12.1 Based on Evaluation Results (Targeted Improvements)

The most immediate future work should be directly informed by the quantitative results obtained from the Evaluation Framework (Chapter 8). Addressing identified weaknesses is key to further improving reliability.

### 12.1.1 Fine-tuning Embeddings (Nomic or Alternative)

*   **Trigger:** If Retrieval Performance metrics (Recall@K, MRR) are consistently low despite effective chunking and metadata filtering, indicating the base embedding model struggles to capture the semantic nuances of financial text or differentiate between similar concepts across different contexts.
*   **Approach:**
    *   **Data:** Curate a domain-specific dataset of query-relevant passage pairs derived from the financial corpus (potentially expanding the Golden Dataset or using LLMs to generate synthetic pairs, followed by validation).
    *   **Method:** Employ Parameter-Efficient Fine-Tuning (PEFT) techniques like LoRA (Low-Rank Adaptation) to adapt the chosen embedding model (`nomic-embed-text-v1.5` or a successor) to the financial domain with significantly less data and compute than full fine-tuning. (Ref: *AI Engineering*, Chapter 7).
    *   **Goal:** Improve the model's ability to rank truly relevant sections higher during the initial vector search phase.
    *   **Evaluation:** Re-run the full evaluation pipeline, paying close attention to Retrieval Metrics, to quantify the improvement.

### 12.1.2 Fine-tuning Re-ranker

*   **Trigger:** If initial vector retrieval recall is acceptable, but the cross-encoder re-ranker fails to consistently place the most relevant sections within the final Top K (e.g., low Precision@K even if Recall@50 was high), or if it misinterprets relevance for financial queries.
*   **Approach:**
    *   **Data:** Create a dataset of `(query, relevant_passage, irrelevant_passage)` triplets or `(query, passage, relevance_score)` pairs specific to the financial domain.
    *   **Method:** Fine-tune the chosen cross-encoder model (e.g., `ms-marco-MiniLM-L-6-v2`) on this dataset to better learn financial relevance signals.
    *   **Goal:** Improve the precision of the final Top K context sections selected for the generator.
    *   **Evaluation:** Re-evaluate, focusing on the impact on end-to-end metrics (Faithfulness, Accuracy) as well as specific re-ranking effectiveness.

### 12.1.3 Fine-tuning Generator (Smaller Model on Groq?)

*   **Trigger:**
    1.  If rigorous prompt engineering (Chapter 6) proves insufficient to consistently achieve high Faithfulness scores or correct Refusal behavior, even with high-quality retrieved context.
    2.  If the cost or latency of the large generator model (e.g., Gemini 1.5 Pro) becomes prohibitive for the target use case.
*   **Approach:**
    *   **Model Selection:** Choose a smaller, performant open-source model known for good instruction following (e.g., Llama 3.1, Mistral, Phi-3 variants) that is supported by ultra-low-latency inference providers like Groq.
    *   **Data:** Prepare a high-quality dataset of `(prompt, ideal_completion)` pairs based on the Golden Dataset and potentially augmented with synthetic examples generated by the larger model (Gemini 1.5 Pro), ensuring examples cover grounded answers, correct tool use, and proper refusal.
    *   **Method:** Use PEFT/LoRA to fine-tune the smaller model specifically for the task of context-grounded, tool-using financial Q&A with strict refusal capabilities.
    *   **Deployment:** Deploy the fine-tuned model artifact to an inference platform like Groq for significant speed improvements and potentially lower cost per query.
    *   **Goal:** Achieve comparable or even superior reliability (faithfulness, refusal accuracy) with significantly lower latency and cost compared to the larger base model.
    *   **Evaluation:** Rigorously compare the fine-tuned smaller model's performance against the baseline large model across all key metrics.

## 12.2 Expanding Capabilities

Beyond optimizing the current pipeline, new features can be added to broaden the Assistant's utility.

### 12.2.1 Handling Scanned/Image-based PDFs

*   **Problem:** The current system relies on text-based PDFs. SMEs might have older, scanned reports.
*   **Solution:** Integrate robust Optical Character Recognition (OCR) capabilities. While Gemini Vision handles some implicit OCR, dedicated OCR engines (e.g., Tesseract - open source, or cloud services like AWS Textract, Google Document AI) might be needed for higher accuracy on lower-quality scans. The output needs to be integrated into the existing Markdown conversion process. Evaluate the quality trade-offs.

### 12.2.2 Advanced Table Understanding & Extraction

*   **Problem:** While Gemini Vision parses tables, extracting specific data points programmatically or understanding complex table structures (merged cells, hierarchical rows/columns) might still be challenging for downstream tool use or precise querying.
*   **Solution:** Explore specialized table extraction models or techniques. This could involve:
    *   Fine-tuning models specifically for table structure recognition.
    *   Developing more sophisticated prompting for the multimodal LLM to output table data in a highly structured format (e.g., JSON representation of the table).
    *   Integrating libraries designed for DataFrame extraction from documents.

### 12.2.3 Complex Cross-Document Analysis & Trends

*   **Problem:** The current system primarily focuses on queries answerable within one or a few closely related sections, often filtered by period. Analyzing trends over multiple years or synthesizing information requiring data points scattered across many different reports is harder.
*   **Solution:**
    *   **Enhanced Query Decomposition:** Improve the decomposer LLM's ability to break down trend analysis queries into specific data point lookups across multiple periods.
    *   **Graph RAG (Advanced):** Explore representing entities (e.g., accounts like 'Revenue', 'Net Income') and their values over time as nodes and edges in a graph database (like Neo4j). This could enable more complex relationship and trend queries, though it significantly increases system complexity. (Ref: *AI Engineering*, Chapter 6 discussion on knowledge graphs).
    *   **Summarization Techniques:** Implement multi-document summarization steps within the RAG pipeline to condense information from multiple retrieved sections before final generation.

### 12.2.4 Integration with Live Accounting Systems

*   **Problem:** The current system relies on static, uploaded PDFs. Real-time insights require access to live accounting data.
*   **Solution:** Develop integrations (via APIs) with popular SME accounting platforms (QuickBooks Online, Xero, Sage, etc.). This would allow querying up-to-the-minute data but requires handling API authentication, data mapping, and potentially combining structured API data with unstructured PDF data (a significant architectural shift).

### 12.2.5 Expanding Calculation Toolset

*   **Problem:** The initial set of calculation tools is basic. More sophisticated financial analysis requires a broader range of metrics.
*   **Solution:** Add more Python functions and corresponding LLM tool schemas for standard financial ratios (e.g., Debt-to-Equity, Return on Equity, Inventory Turnover), discounted cash flow (DCF) components, or other relevant calculations based on user needs. Ensure rigorous testing and error handling for all new tools.

### 12.2.6 Supporting Other Document Types (Compliance, Legal)

*   **Problem:** SMEs deal with more than just financial reports.
*   **Solution:** Extend the ingestion pipeline to handle other common business documents (contracts, policy manuals, compliance reports). This would require:
    *   Adapting the parser/chunking strategy if document structures differ significantly.
    *   Updating the metadata schema to include new document types.
    *   Evaluating if retrieval/generation needs tuning for different types of text (legal vs. financial).
    *   Potentially implementing a classifier to route queries or tailor retrieval based on inferred document type relevance.

## 12.3 Enhancing User Experience

Improving the user interface and interaction can significantly increase the Assistant's value.

### 12.3.1 Production-Grade UI/UX

*   **Problem:** The FYP demo interface (CLI/Streamlit) is basic.
*   **Solution:** Develop a dedicated web front-end using modern frameworks (React, Vue, Angular) communicating with a robust backend API (built using FastAPI/Flask/Django). Focus on intuitive design, clear presentation of answers and citations, document management features, and user account management.

### 12.3.2 User Feedback Mechanisms

*   **Problem:** Lack of direct feedback hinders continuous improvement.
*   **Solution:** Integrate mechanisms for users to rate answer quality (e.g., thumbs up/down), flag incorrect information, provide corrections, or suggest missing context. This feedback is invaluable for identifying system weaknesses and potentially creating data for future fine-tuning (Ref: *AI Engineering*, Chapter 10).

### 12.3.3 Visualization Capabilities

*   **Problem:** Financial data is often best understood visually.
*   **Solution:** Integrate charting libraries (e.g., Plotly, Chart.js, Matplotlib) to generate visualizations (bar charts, line graphs, pie charts) based on retrieved or calculated data. This could be implemented as another tool called by the LLM or as a post-processing step in the UI.

These future work directions highlight the potential evolution of the AI CFO Assistant from a focused FYP prototype into a more comprehensive and powerful tool for SMEs. The iterative, evaluation-driven approach established in the initial project provides the ideal framework for tackling these enhancements systematically.




---

# Appendix

This appendix provides supplementary materials referenced in the main chapters, including example prompts, database schemas, tool definitions, API usage snippets, and a glossary.

## A. Example Prompts

Effective prompt engineering is crucial for controlling LLM behavior. These examples illustrate the types of prompts used in various stages of the AI CFO Assistant pipeline. Note that these are illustrative and should be refined based on testing and evaluation. Placeholders like `[User Query]` or `[Context Chunk Text]` indicate where dynamic content is inserted.

### A.1 Gemini Vision Parser Prompt

This prompt guides the multimodal LLM during the initial PDF parsing stage (Chapter 3). It requests structured Markdown output and metadata extraction.

```text
SYSTEM: You are an expert document analysis AI specialized in parsing financial reports (PDFs). Your task is to analyze the provided PDF document page by page and generate a single, coherent Markdown representation of its content, including accurate extraction of key metadata.

**Instructions:**

1.  **Extract All Relevant Text:** Capture all text content, including headers, paragraphs, list items, table contents, and footnotes. Preserve the relative order of content as much as possible.
2.  **Identify Structure:** Use Markdown headings (`#`, `##`, `###`, etc.) to accurately represent the document's heading hierarchy. Use Markdown lists (`*`, `-`, `1.`) for list items.
3.  **Format Tables:** Represent all tables using standard Markdown table syntax. Ensure correct association between table headers and cell values. If a table spans multiple pages, attempt to merge it logically.
4.  **Extract Metadata:** Identify the following metadata from the document content and format it as a YAML front matter block at the VERY BEGINNING of the output:
    *   `report_type`: (e.g., "Income Statement", "Balance Sheet", "Cash Flow Statement")
    *   `company_name`: The name of the company the report belongs to.
    *   `period_end_date`: The primary date the report refers to (e.g., "YYYY-MM-DD" for Balance Sheet As-Of date or Income/Cash Flow period end).
    *   `period_start_date`: (Optional) The start date for Income/Cash Flow statements, if clearly stated.
    *   `fiscal_year`: The fiscal year derived from the period end date.
    *   `fiscal_quarter`: (Optional) The fiscal quarter (Q1, Q2, Q3, Q4) if identifiable.
    *   `currency`: The currency symbol or code used (e.g., "USD", "$", "EUR", "€"). Standardize to ISO code if possible.
    *   `source_filename`: [You will need to provide this filename to the prompt context if possible, otherwise instruct the model to use a placeholder if it cannot be inferred]
5.  **Page Number Markers (Attempt):** If possible, insert comments like `<!-- Page X -->` in the Markdown where page breaks occur in the original PDF. This is a best-effort instruction.
6.  **Clean Output:** Do not include any explanatory text outside of the YAML block and the Markdown representation of the document content. Ensure valid Markdown syntax.

**Output Format Example:**

```yaml
---
document_id: "[Placeholder - To be filled post-processing]"
source_filename: "[Provided Filename or Placeholder]"
report_type: "Income Statement"
company_name: "Example Corp"
period_start_date: "2024-01-01"
period_end_date: "2024-03-31"
fiscal_year: 2024
fiscal_quarter: Q1
currency: "USD"
parsing_timestamp: "[Placeholder - To be filled post-processing]"
parser_model: "[Model ID used]"
---

# Example Corp - Income Statement

**For the Quarter Ended March 31, 2024**

## Revenue
*   Sales Revenue: $500,000
*   Service Revenue: $50,000

*Total Revenue: $550,000*

<!-- Page 1 -->

## Cost of Goods Sold
| Item        | Amount |
| :---------- | -----: |
| Material Cost | 150,000 |
| Labor Cost    | 100,000 |
| **Total COGS**| **250,000** |

*Gross Profit: $300,000*

... (rest of the document content in Markdown) ...
```

**Input:** [Provide the PDF document content/reference to the Gemini Vision API]

**Output:** A single string containing the YAML front matter followed by the Markdown body.
```

### A.2 Gemini Query Decomposer Prompt

This prompt is used in the optional query decomposition stage (Chapter 5) to break down complex user questions.

```text
SYSTEM: You are an AI assistant specialized in analyzing user queries related to financial reports. Your task is to determine if a query requires multiple distinct pieces of information or calculation steps to be answered comprehensively.

**Instructions:**

1.  Analyze the `User Query` provided below.
2.  **If** the query is simple and likely answerable by retrieving one or two related pieces of information directly (e.g., "What was revenue?", "Find net income for Q1"), respond **ONLY** with the original query text itself within a JSON structure like: `{"needs_decomposition": false, "original_query": "[Original Query Text]"}`.
3.  **If** the query is complex and requires multiple steps, comparisons, calculations involving different base figures, or information from potentially disparate sections/periods (e.g., "Compare revenue and net income trend over the last 4 quarters", "What is the debt-to-equity ratio?"), break it down into the simplest possible, logically sequenced sub-queries that need to be answered to fulfill the original request. Respond **ONLY** with a JSON structure like: `{"needs_decomposition": true, "sub_queries": ["Sub-query 1", "Sub-query 2", ...]}`.
    *   Sub-queries should be phrased as simple lookup questions (e.g., "Find Total Debt for YYYY-MM-DD", "Find Total Equity for YYYY-MM-DD", "Find Revenue for Q1 YYYY", "Find Revenue for Q2 YYYY").
    *   Do not attempt to answer the query, only decompose it.

**User Query:**
`[User Query Text]`

**Your JSON Response:**
```

### A.3 Gemini 1.5 Pro Generator Prompt (Full Example)

This is the main prompt used for the final answer generation (Chapter 6). It incorporates instructions, context, tool schemas, and few-shot examples.

```text
SYSTEM: You are the AI CFO Assistant. Your sole purpose is to accurately answer questions based strictly on the provided financial document excerpts ('PROVIDED CONTEXT SECTIONS'). You must prioritize factual correctness, strict adherence to the provided context, and clear attribution.

---
CRITICAL INSTRUCTIONS (Follow PRECISELY):

1.  **CONTEXT ADHERENCE:** You MUST answer the query using ONLY the information contained within the 'PROVIDED CONTEXT SECTIONS' below. Do NOT use any prior knowledge, training data, real-time information, the current date, or any information source external to these exact text sections and their associated metadata. Verify that every piece of information in your answer comes directly from the provided context.
2.  **REFUSAL:** If the information needed to answer the query accurately and completely is NOT present in the 'PROVIDED CONTEXT SECTIONS', you MUST respond EXACTLY with the following phrase and nothing else: 'The provided documents do not contain sufficient information to answer this question.' Do NOT attempt to infer, guess, estimate, or synthesize information not explicitly present in the context.
3.  **CALCULATIONS & TOOLS:** For any calculations required (e.g., ratios, sums, averages, percentage changes), you MUST use the provided 'AVAILABLE TOOLS'. Do NOT perform calculations directly in your response text. Ensure the input arguments you provide to the tools are derived solely from numerical figures found within the 'PROVIDED CONTEXT SECTIONS'.
4.  **CITATIONS:** For EVERY factual statement or numerical figure you provide in your answer (including numbers used as inputs for tool calls), you MUST cite the source using the following format, placed immediately after the information it supports: '[{source_filename}, Section: "{section_heading}"]'. If information comes from multiple sections, cite all relevant ones consecutively.
5.  **CLARITY & CONCISENESS:** Provide direct answers to the query. Avoid conversational filler or opinions. Be precise with financial terminology found in the context.
---
AVAILABLE TOOLS:
[
  {
    "name": "calculate_ratio",
    "description": "Calculates the ratio by dividing a numerator by a denominator (numerator / denominator). Returns the result rounded to 3 decimal places.",
    "parameters": {
      "type": "object",
      "properties": {
        "numerator": { "type": "number", "description": "The value of the numerator (the number being divided)." },
        "denominator": { "type": "number", "description": "The value of the denominator (the number dividing the numerator). Cannot be zero." }
      },
      "required": ["numerator", "denominator"]
    }
  },
  {
    "name": "calculate_percentage_change",
    "description": "Calculates the percentage change between an old value and a new value: ((new_value - old_value) / abs(old_value)) * 100. Handles zero old value appropriately. Returns the percentage rounded to 2 decimal places.",
    "parameters": {
        "type": "object",
        "properties": {
            "value_old": { "type": "number", "description": "The starting or previous period's value." },
            "value_new": { "type": "number", "description": "The ending or current period's value." }
        },
        "required": ["value_old", "value_new"]
    }
  }
  # Add schemas for other tools like sum_list, calculate_average here...
]
---
FEW-SHOT EXAMPLES:

1.  **Query:** What was the Net Income in Q1 2024?
    **Context Section:** Metadata: {source_filename: rep_Q1_2024.pdf, section_heading: 'Income Statement'} Text: '...Net Income $32,000...'
    **Answer:** The Net Income in Q1 2024 was $32,000 [rep_Q1_2024.pdf, Section: "Income Statement"].

2.  **Query:** What was the marketing budget for 2023?
    **Context Section:** (Context contains financial data but no mention of a marketing budget line item)
    **Answer:** The provided documents do not contain sufficient information to answer this question.

3.  **Query:** Calculate the current ratio for Q1 2024.
    **Context Section 1:** Metadata: {source_filename: bs_Q1_2024.pdf, section_heading: 'Current Assets'} Text: '...Total Current Assets $145,000...'
    **Context Section 2:** Metadata: {source_filename: bs_Q1_2024.pdf, section_heading: 'Current Liabilities'} Text: '...Total Current Liabilities $40,000...'
    **Answer (Illustrative thought process leading to tool call):** I need Total Current Assets ($145,000 [bs_Q1_2024.pdf, Section: "Current Assets"]) and Total Current Liabilities ($40,000 [bs_Q1_2024.pdf, Section: "Current Liabilities"]). I will use the 'calculate_ratio' tool.
    **(Function Call: calculate_ratio(numerator=145000, denominator=40000))**
    **(Function Response: {"ratio": 3.625})**
    **Final Answer:** The current ratio for Q1 2024 is 3.625, calculated using Total Current Assets of $145,000 [bs_Q1_2024.pdf, Section: "Current Assets"] and Total Current Liabilities of $40,000 [bs_Q1_2024.pdf, Section: "Current Liabilities"].

---
PROVIDED CONTEXT SECTIONS:

### CONTEXT SECTION 1 ###
Metadata: {source_filename: '[Actual Filename]', section_heading: '[Actual Heading]', ... [Other Metadata]}
Text:
[Full text of the first retrieved and re-ranked section...]

### CONTEXT SECTION 2 ###
Metadata: {source_filename: '[Actual Filename]', section_heading: '[Actual Heading]', ... [Other Metadata]}
Text:
[Full text of the second retrieved and re-ranked section...]

### CONTEXT SECTION ... ###
...

---
USER QUERY:
`[User's original query or sub-query]`

---
Answer the USER QUERY based *only* on the instructions and the PROVIDED CONTEXT SECTIONS above. Remember to use tools for calculations and cite all information. If the information is not present, state the exact refusal message.
```

### A.4 LLM-as-judge Faithfulness Prompt

This prompt is used by the evaluation framework (Chapter 8) to assess if the generated answer is grounded in the provided context.

```text
SYSTEM: You are an impartial and meticulous AI Evaluator. Your task is to determine if an AI Assistant's answer is STRICTLY supported ONLY by the provided context text. Do not use any outside knowledge or assess the factual correctness of the context itself. Focus solely on whether the answer derives faithfully from the given text.

---
PROVIDED CONTEXT CHUNKS:
[Insert concatenated text of the context sections that were originally provided to the generator LLM for this specific query]
---
AI ASSISTANT'S GENERATED ANSWER:
[Insert the AI CFO Assistant's final_response text for this specific query]
---
EVALUATION QUESTION:

Is every single factual statement, claim, and numerical figure presented in the 'AI ASSISTANT'S GENERATED ANSWER' directly and solely supported by the information explicitly present in the 'PROVIDED CONTEXT CHUNKS'?

Consider these points:
*   Does the answer introduce information not found in the context?
*   Does the answer contradict information in the context?
*   Are numbers or specific details misrepresented compared to the context?
*   Ignore citation formatting issues, focus only on the factual claims of the answer itself versus the context.

Answer **ONLY 'Yes' or 'No'**.

Your Answer:
```

These examples provide a starting point. Continuous refinement based on observed LLM behavior and evaluation results is essential for maximizing reliability.

---

## B. Database Schema (SQL DDL)

This section provides the SQL `CREATE TABLE` statements required to set up the database schema for the AI CFO Assistant within a PostgreSQL database (like NeonDB) where the `pgvector` extension has already been enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).

**Notes:**

*   Ensure the `vector` extension is enabled in your database before running these commands.
*   The dimension of the `vector` type (e.g., `vector(1024)`) **must** match the output dimension of the chosen embedding model (e.g., `nomic-embed-text-v1.5` outputs 1024 dimensions). Adjust if using a different model.
*   Consider adding further constraints (e.g., `NOT NULL` where appropriate, specific `CHECK` constraints) based on evolving requirements.
*   Indexing statements are included here for completeness, as they are crucial for performance.

```sql
-- Enable vector extension if not already done
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ##############################################
-- # Table: documents
-- # Stores metadata about each ingested PDF file
-- ##############################################
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR PRIMARY KEY,                          -- Unique identifier (e.g., derived from filename or UUID)
    source_filename TEXT NOT NULL,                            -- Original filename of the uploaded PDF
    parsed_markdown_content TEXT,                             -- Full Markdown content (can be large, consider storage implications)
    yaml_metadata JSONB,                                      -- Parsed YAML front matter as JSONB
    upload_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,   -- When the document processing started
    ingestion_complete_timestamp TIMESTAMPTZ,                 -- When processing finished (NULL if in progress/failed)
    parser_model_used VARCHAR(100),                           -- Identifier of the multimodal LLM used for parsing
    parsing_status VARCHAR(50) DEFAULT 'Pending',             -- e.g., 'Pending', 'Processing', 'Success', 'Failed'
    error_message TEXT                                        -- Store parsing error details if status is 'Failed'
);

COMMENT ON TABLE documents IS 'Stores metadata about each ingested PDF source document.';
COMMENT ON COLUMN documents.document_id IS 'Unique identifier for the document, potentially derived from filename or a generated UUID.';
COMMENT ON COLUMN documents.source_filename IS 'Original filename of the PDF as uploaded.';
COMMENT ON COLUMN documents.parsed_markdown_content IS 'The full Markdown text extracted and formatted from the PDF by the parser (can be large).';
COMMENT ON COLUMN documents.yaml_metadata IS 'Structured metadata extracted/inferred from the document, stored as JSONB.';
COMMENT ON COLUMN documents.upload_timestamp IS 'Timestamp when the document processing pipeline was initiated.';
COMMENT ON COLUMN documents.ingestion_complete_timestamp IS 'Timestamp when the document processing pipeline finished successfully.';
COMMENT ON COLUMN documents.parser_model_used IS 'Identifier for the specific parsing model version used (e.g., gemini-1.5-pro-vision-001).';
COMMENT ON COLUMN documents.parsing_status IS 'Current status of the ingestion process for this document.';
COMMENT ON COLUMN documents.error_message IS 'Details of any error encountered during parsing or processing.';


-- ##############################################
-- # Table: sections
-- # Stores logical sections identified within documents
-- ##############################################
CREATE TABLE IF NOT EXISTS sections (
    section_id BIGSERIAL PRIMARY KEY,                         -- Auto-incrementing unique identifier for the section
    document_id VARCHAR NOT NULL,                             -- Foreign key reference to the documents table
    section_heading TEXT,                                     -- Text of the Markdown heading defining this section (NULL if no heading)
    section_level INTEGER,                                    -- Markdown heading level (1 for #, 2 for ##, etc., NULL if no heading)
    original_section_text TEXT NOT NULL,                      -- Full, original text content of this entire logical section
    metadata JSONB NOT NULL,                                  -- Combined metadata (document-level YAML + section-specific info)
    token_count INTEGER,                                      -- Estimated token count of original_section_text (using relevant tokenizer)
    requires_split BOOLEAN DEFAULT FALSE,                     -- Flag indicating if this section exceeded token limit and was split further

    -- Foreign Key Constraint
    CONSTRAINT fk_document
        FOREIGN KEY(document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE -- If a document is deleted, delete its sections
);

COMMENT ON TABLE sections IS 'Stores logical sections extracted from documents, typically based on Markdown headings.';
COMMENT ON COLUMN sections.section_id IS 'Unique identifier for each logical section.';
COMMENT ON COLUMN sections.document_id IS 'References the parent document this section belongs to.';
COMMENT ON COLUMN sections.section_heading IS 'The heading text that defines the start of this section.';
COMMENT ON COLUMN sections.section_level IS 'The level of the Markdown heading (e.g., 1 for #, 2 for ##).';
COMMENT ON COLUMN sections.original_section_text IS 'The complete text content belonging to this logical section.';
COMMENT ON COLUMN sections.metadata IS 'Combined document and section metadata relevant for filtering and context (JSONB).';
COMMENT ON COLUMN sections.token_count IS 'Estimated number of tokens in original_section_text.';
COMMENT ON COLUMN sections.requires_split IS 'Indicates if this section was too large for a single embedding.';

-- Index for efficient filtering based on metadata
CREATE INDEX IF NOT EXISTS idx_sections_metadata_gin ON sections USING gin (metadata jsonb_path_ops);
-- Index for FK relationship
CREATE INDEX IF NOT EXISTS idx_sections_document_id ON sections (document_id);


-- ##############################################
-- # Table: embeddings
-- # Stores text chunks (full sections or sub-chunks) and their vectors
-- ##############################################
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id BIGSERIAL PRIMARY KEY,                       -- Auto-incrementing unique identifier for the embedding entry
    section_id BIGINT NOT NULL,                               -- Foreign key reference to the parent logical section
    chunk_sequence INTEGER DEFAULT 0 NOT NULL,                -- Order of this chunk within the parent section (0 if full, 1, 2... if split)
    chunk_text TEXT NOT NULL,                                 -- The specific text content represented by this embedding
    embedding_vector vector(1024) NOT NULL,                   -- The vector embedding (ADJUST DIMENSION 1024 AS NEEDED)
    is_full_section BOOLEAN NOT NULL,                         -- True if embedding represents the entire section text, False if a sub-chunk
    embedding_model_used VARCHAR(100),                      -- Identifier for the embedding model version used

    -- Foreign Key Constraint
    CONSTRAINT fk_section
        FOREIGN KEY(section_id)
        REFERENCES sections(section_id)
        ON DELETE CASCADE -- If a section is deleted, delete its embeddings
);

COMMENT ON TABLE embeddings IS 'Stores text chunks (full sections or split sub-chunks) and their corresponding vector embeddings.';
COMMENT ON COLUMN embeddings.embedding_id IS 'Unique identifier for each embedding vector and its associated text.';
COMMENT ON COLUMN embeddings.section_id IS 'References the parent logical section this chunk belongs to.';
COMMENT ON COLUMN embeddings.chunk_sequence IS 'Order of this chunk if the parent section was split (0 for full sections).';
COMMENT ON COLUMN embeddings.chunk_text IS 'The actual text content that was embedded.';
COMMENT ON COLUMN embeddings.embedding_vector IS 'The numerical vector representation of the chunk_text (with prepended metadata). Dimension must match model output.';
COMMENT ON COLUMN embeddings.is_full_section IS 'Distinguishes embeddings of entire sections vs. smaller sub-chunks.';
COMMENT ON COLUMN embeddings.embedding_model_used IS 'Identifier for the specific embedding model version used.';

-- Vector index for similarity search (using cosine distance here)
-- NOTE: Index creation can take time on large tables.
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw ON embeddings USING hnsw (embedding_vector vector_cosine_ops);
-- Other distance metrics: vector_l2_ops (Euclidean), vector_ip_ops (Inner Product)

-- Index for FK relationship
CREATE INDEX IF NOT EXISTS idx_embeddings_section_id ON embeddings (section_id);
-- Index potentially useful for retrieving specific chunks of split sections
CREATE INDEX IF NOT EXISTS idx_embeddings_section_sequence ON embeddings (section_id, chunk_sequence);


-- ##############################################
-- # Table: query_logs
-- # Stores detailed logs for each query interaction
-- ##############################################
CREATE TABLE IF NOT EXISTS query_logs (
    log_id BIGSERIAL PRIMARY KEY,                          -- Unique identifier for the log entry
    session_id VARCHAR(255),                             -- Optional: Identifier for a user session
    query_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- When the query processing started
    user_query TEXT NOT NULL,                              -- The original query input by the user

    -- Query Processing Stages
    decomposed_sub_queries JSONB,                        -- JSON array of sub-queries if decomposition occurred, else NULL
    metadata_filters_applied JSONB,                    -- JSON object representing filters applied (e.g., {'fiscal_year': 2023})
    retrieval_method VARCHAR(50),                        -- Method used ('MetadataFilter+Vector', 'Hybrid', etc.)

    -- Retrieval Results (Storing IDs allows joining back to original data if needed)
    retrieved_embedding_ids BIGINT[],                    -- Array of embedding_ids from initial retrieval
    retrieved_embedding_scores FLOAT[],                  -- Corresponding similarity scores (optional)
    reranked_section_ids BIGINT[],                       -- Array of section_ids after re-ranking (ordered)
    reranked_section_scores FLOAT[],                     -- Corresponding cross-encoder scores (ordered)
    final_context_section_ids BIGINT[] NOT NULL,         -- Array of section_ids actually used as context for the generator

    -- Generation Stage
    llm_prompt TEXT,                                     -- Full prompt sent to the generator LLM (can be large)
    generator_model_id VARCHAR(100),                     -- Identifier of the generator model used
    raw_llm_response TEXT,                               -- Raw text output from the generator LLM
    tool_calls JSONB,                                    -- JSON array of objects detailing requested tool calls (name, args)
    tool_responses JSONB,                                -- JSON array of objects detailing results returned by tools

    -- Final Output & Evaluation Links
    final_response TEXT,                                 -- Final, cleaned-up response shown to the user
    citations_generated JSONB,                           -- JSON array of formatted citation strings or objects
    evaluation_run_id VARCHAR(100),                      -- Optional: Identifier linking to a specific evaluation run
    evaluation_scores JSONB,                             -- Optional: Store calculated metrics if evaluated automatically

    -- Status & Errors
    status VARCHAR(50) DEFAULT 'Success',                -- 'Success', 'Failure', 'Refused' (when LLM refuses correctly)
    error_message TEXT,                                  -- Store error details if processing failed
    error_stage VARCHAR(100),                            -- Stage where error occurred (e.g., 'Parsing', 'Retrieval', 'Generation')

    -- Performance & Cost
    latency_ms_total INTEGER,                            -- Total processing time in milliseconds
    latency_ms_parsing INTEGER,                          -- Optional: Latency for parsing stage
    latency_ms_retrieval INTEGER,                        -- Latency for retrieval + reranking stages
    latency_ms_generation INTEGER,                       -- Latency for generator LLM (including tool calls)
    token_count_prompt INTEGER,                          -- Tokens in the generator prompt
    token_count_completion INTEGER,                      -- Tokens in the raw LLM completion (response + tool calls/responses)
    estimated_cost_usd DECIMAL(10, 6)                    -- Estimated API costs for this query
);

COMMENT ON TABLE query_logs IS 'Stores detailed logs of each user query interaction for debugging, analysis, and evaluation.';
COMMENT ON COLUMN query_logs.final_context_section_ids IS 'CRITICAL: The exact section_ids whose content was provided to the generator LLM.';
COMMENT ON COLUMN query_logs.llm_prompt IS 'Stores the full prompt for reproducibility and debugging prompt issues.';
COMMENT ON COLUMN query_logs.evaluation_run_id IS 'Optional identifier to link logs to specific runs of the evaluation script.';
COMMENT ON COLUMN query_logs.evaluation_scores IS 'Optional field to store per-query metrics calculated during evaluation.';

-- Create indexes for potential querying of logs
CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs (query_timestamp);
CREATE INDEX IF NOT EXISTS idx_query_logs_status ON query_logs (status);
-- Add other indexes based on common log analysis queries (e.g., on session_id, generator_model_id)

```

This schema provides a robust structure for storing the ingested data and the logs necessary for operating and evaluating the AI CFO Assistant. Remember to adjust the `vector(1024)` dimension based on your final embedding model choice.


---

## C. Calculation Tool Schemas (JSON Examples)

The Generator LLM (e.g., Gemini 1.5 Pro) requires structured descriptions (schemas) of the available tools (Python functions) to understand their purpose, required inputs, and expected outputs. These schemas are typically provided in JSON format within the API call.

Below are example schemas for the core calculation tools identified in Chapter 6. These schemas adhere to the format generally expected by function calling APIs like Google's Gemini API.

**Notes:**

*   Parameter descriptions should be clear and informative, guiding the LLM on what values to extract from the context.
*   Mark parameters as `required` if the tool cannot function without them.
*   The `type` field should accurately reflect the expected Python data type (`number` for float/int, `array` for list, `string` for str, etc.).

**1. Tool: `calculate_ratio`**

*   **Python Function Purpose:** Calculates `numerator / denominator`.
*   **JSON Schema:**
    ```json
    {
      "name": "calculate_ratio",
      "description": "Calculates the ratio by dividing a numerator by a denominator (result = numerator / denominator). Use this for financial ratios like Current Ratio, Debt-to-Equity, etc. Returns the result rounded to 3 decimal places or an error message.",
      "parameters": {
        "type": "object",
        "properties": {
          "numerator": {
            "type": "number",
            "description": "The value of the numerator (the number being divided, e.g., Total Current Assets)."
          },
          "denominator": {
            "type": "number",
            "description": "The value of the denominator (the number dividing the numerator, e.g., Total Current Liabilities). Must not be zero."
          }
        },
        "required": ["numerator", "denominator"]
      }
    }
    ```

**2. Tool: `calculate_percentage_change`**

*   **Python Function Purpose:** Calculates `((new_value - old_value) / abs(old_value)) * 100`.
*   **JSON Schema:**
    ```json
    {
      "name": "calculate_percentage_change",
      "description": "Calculates the percentage change between an old value (starting/previous period) and a new value (ending/current period). Handles zero old value appropriately. Returns the percentage increase or decrease rounded to 2 decimal places or an error message.",
      "parameters": {
        "type": "object",
        "properties": {
          "value_old": {
            "type": "number",
            "description": "The starting or previous period's value (e.g., Revenue Q1)."
          },
          "value_new": {
            "type": "number",
            "description": "The ending or current period's value (e.g., Revenue Q2)."
          }
        },
        "required": ["value_old", "value_new"]
      }
    }
    ```

**3. Tool: `sum_list`**

*   **Python Function Purpose:** Calculates the sum of a list of numbers.
*   **JSON Schema:**
    ```json
    {
      "name": "sum_list",
      "description": "Calculates the sum total of a list of provided numerical values. Use this for aggregating line items (e.g., summing specific operating expenses). Returns the total sum or an error message.",
      "parameters": {
        "type": "object",
        "properties": {
          "numbers": {
            "type": "array",
            "description": "A list of numerical values to be summed.",
            "items": {
              "type": "number"
            }
          }
        },
        "required": ["numbers"]
      }
    }
    ```

**4. Tool: `calculate_average`**

*   **Python Function Purpose:** Calculates the average of a list of numbers.
*   **JSON Schema:**
    ```json
    {
      "name": "calculate_average",
      "description": "Calculates the arithmetic mean (average) of a list of provided numerical values. Use this for finding average values over a period or across categories. Returns the average value or an error message.",
      "parameters": {
        "type": "object",
        "properties": {
          "numbers": {
            "type": "array",
            "description": "A list of numerical values to be averaged.",
            "items": {
              "type": "number"
            }
          }
        },
        "required": ["numbers"]
      }
    }
    ```

**5. Tool: `calculate_gross_profit_margin` (Example of a Specific Ratio)**

*   **Python Function Purpose:** Calculates `((Revenue - COGS) / Revenue) * 100`. Could also be implemented using `calculate_ratio` if Gross Profit is already calculated. This shows defining more specific tools.
*   **JSON Schema:**
    ```json
    {
      "name": "calculate_gross_profit_margin",
      "description": "Calculates the Gross Profit Margin percentage using Total Revenue and Cost of Goods Sold (COGS). Formula: ((Revenue - COGS) / Revenue) * 100. Returns the percentage rounded to 2 decimal places or an error message.",
      "parameters": {
        "type": "object",
        "properties": {
          "total_revenue": {
            "type": "number",
            "description": "The Total Revenue figure for the period."
          },
          "cost_of_goods_sold": {
            "type": "number",
            "description": "The Cost of Goods Sold (COGS) figure for the period. Should typically be positive, even if representing an expense."
          }
        },
        "required": ["total_revenue", "cost_of_goods_sold"]
      }
    }
    ```

**Integration:**

These JSON schema objects are collected into a list and provided as the `tools` parameter in the request to the Gemini API (or equivalent function calling API) during the generation step (Chapter 6). The LLM uses these descriptions to determine which tool to call and what arguments to extract from the context.


---

## D. API Usage Snippets

This section provides conceptual Python code snippets demonstrating how to interact with the core external APIs used in the system: the Embedding API (using Fireworks AI as an example) and the LLM API (using Google Gemini as an example).

**Notes:**

*   These are simplified examples focusing on the API call structure. Real implementation requires proper error handling, configuration loading, authentication, and potentially asynchronous execution.
*   Replace placeholder API keys and model IDs with actual values loaded securely (e.g., from environment variables as shown in Chapter 9).
*   Refer to the official documentation of the specific API providers (Google AI, Fireworks AI, etc.) for the most up-to-date details, parameters, and error codes.

### D.1 Fireworks AI Embedding Call

This snippet shows how to get embeddings for batched text inputs using `nomic-embed-text-v1.5` via the Fireworks AI API, typically using the `requests` library.

```python
import requests
import json
import os
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/embeddings"

# Assume 'config' dictionary holds model ID, loaded from config.yaml
EMBEDDING_MODEL_ID = "nomic-embed-text-v1.5" # Example, use config['models']['embedding']
# Adjust model path as per Fireworks documentation, e.g.:
# EMBEDDING_MODEL_PATH = f"models/fireworks/{EMBEDDING_MODEL_ID}" # Might vary based on provider naming
EMBEDDING_MODEL_PATH = f"nomic-embed-text-v1.5" # Check Fireworks AI documentation for correct path

def get_embeddings_fireworks_batch(text_list: list[str], model_name: str = EMBEDDING_MODEL_PATH) -> list[list[float]] | None:
    """
    Gets embeddings for a list of text strings using Fireworks AI API.

    Args:
        text_list: A list of strings to embed.
        model_name: The model identifier/path on Fireworks AI.

    Returns:
        A list of embedding vectors (each a list of floats), or None if an error occurs.
    """
    if not FIREWORKS_API_KEY:
        print("Error: FIREWORKS_API_KEY not found in environment variables.")
        return None
    if not text_list:
        return []

    payload = {
        "input": text_list,
        "model": model_name,
        # Add other parameters like "encoding_format": "float" if needed
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIREWORKS_API_KEY}"
    }

    try:
        response = requests.post(FIREWORKS_API_URL, headers=headers, json=payload, timeout=60) # Add timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        response_data = response.json()

        if "data" in response_data and isinstance(response_data["data"], list):
            embeddings = [item["embedding"] for item in response_data["data"]]
            # Optional: Add validation for embedding dimension here
            return embeddings
        else:
            print(f"Error: Unexpected response format from Fireworks API: {response_data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error calling Fireworks AI API: {e}")
        # Log the error details here
        return None
    except Exception as e:
        print(f"An unexpected error occurred during embedding: {e}")
        # Log the error details here
        return None

# --- Example Usage ---
# Assume chunk_data_list contains strings like "Metadata: ... --- Chunk Text..."
# text_batch = [item['embedding_input_text'] for item in chunk_data_list]
# if text_batch:
#     embeddings_batch = get_embeddings_fireworks_batch(text_batch)
#     if embeddings_batch and len(embeddings_batch) == len(chunk_data_list):
#         # Process the embeddings (e.g., store in database)
#         for i, embedding in enumerate(embeddings_batch):
#             chunk_data_list[i]['embedding_vector'] = embedding
#             # ... DB insertion logic ...
#     else:
#         print("Failed to retrieve embeddings for the batch.")

```

### D.2 Gemini API Call (Basic Generation)

This snippet shows a basic call to the Gemini API for text generation, suitable for tasks like Query Decomposition or potentially simple generation without function calling.

```python
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# Assume 'config' dictionary holds model ID
GENERATION_MODEL_ID = "gemini-1.5-flash-001" # Example for decomposition, use config[...]

def generate_basic_response(prompt: str, model_id: str = GENERATION_MODEL_ID) -> str | None:
    """Generates a text response from Gemini based on a prompt."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found.")
        return None

    try:
        # Select the model
        model = genai.GenerativeModel(model_id)

        # Set generation configuration (optional, tune as needed)
        generation_config = genai.types.GenerationConfig(
            temperature=0.1, # Lower temperature for more deterministic output
            # max_output_tokens=...,
            # top_p=...,
            # top_k=...
        )

        # Make the API call
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            # Add safety_settings if needed
        )

        # Extract the text response
        # Accessing response parts might vary slightly based on API version/updates
        if response.candidates and response.candidates[0].content.parts:
             return response.candidates[0].content.parts[0].text
        else:
             # Handle cases where response might be blocked or empty
             print(f"Warning: Received empty or blocked response from Gemini. Block reason: {response.prompt_feedback.block_reason if response.prompt_feedback else 'N/A'}")
             return None # Or return specific error indicator

    except Exception as e:
        print(f"Error calling Gemini API for basic generation: {e}")
        # Log error details
        return None

# --- Example Usage ---
# user_query = "Compare revenue between Q1 and Q2 2024."
# decomposer_prompt = f"""
# SYSTEM: [Instructions for decomposition...]
# User Query:
# `{user_query}`
# Your JSON Response:
# """
# json_response_str = generate_basic_response(decomposer_prompt)
# if json_response_str:
#     try:
#         decomposition_result = json.loads(json_response_str)
#         print(decomposition_result)
#         # Process the decomposition result
#     except json.JSONDecodeError:
#         print(f"Error: Failed to parse decomposition response as JSON: {json_response_str}")

```

### D.3 Gemini API Call (Function Calling Flow)

This snippet demonstrates the more complex flow involving function calling for the main generator (Gemini 1.5 Pro).

```python
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
# Assume calculation tools are defined in 'src.tools'
from src import tools # Your module where calculate_ratio etc. live

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Assume 'config' holds model ID, and tool_schemas holds JSON schemas from Appendix C
GENERATOR_MODEL_ID_PRO = "gemini-1.5-pro-001" # Example, use config[...]
# Load tool schemas (e.g., from JSON files or defined directly)
# tool_schemas = load_tool_schemas_from_config(config)
# Example:
tool_schemas = [
    {
      "name": "calculate_ratio",
      "description": "Calculates the ratio by dividing a numerator by a denominator...",
      "parameters": { "type": "object", "properties": { "numerator": {"type": "number"}, "denominator": {"type": "number"} }, "required": ["numerator", "denominator"]}
    },
    # ... other tool schemas
]

# Map tool names to actual Python functions
available_tools = {
    "calculate_ratio": tools.calculate_ratio,
    "calculate_percentage_change": tools.calculate_percentage_change,
    "sum_list": tools.sum_list,
    # ... map other tools
}

def generate_with_function_calling(prompt: str, model_id: str = GENERATOR_MODEL_ID_PRO, tools_list: list = tool_schemas) -> str | None:
    """Generates response, handling function calls if requested by the model."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found.")
        return None

    try:
        # Select the model, enabling function calling
        model = genai.GenerativeModel(
            model_id,
            tools=tools_list # Provide the schemas here
        )

        # Start the chat session (function calling often uses chat interface)
        chat = model.start_chat(enable_automatic_function_calling=False) # Manual control needed

        # --- First API Call ---
        # Send the prompt containing context, query, instructions, and tool schemas
        print("--- Sending Initial Prompt to LLM ---")
        response = chat.send_message(prompt)
        print("--- Received Initial Response from LLM ---")

        # Check for function call request
        # Accessing response parts can change slightly with library updates
        response_part = response.candidates[0].content.parts[0] if (response.candidates and response.candidates[0].content.parts) else None

        if response_part and response_part.function_call:
            function_call = response_part.function_call
            tool_name = function_call.name
            tool_args = dict(function_call.args) # Convert proto Map to dict

            print(f"--- LLM requested Tool Call: {tool_name}({tool_args}) ---")

            # --- Execute Local Tool ---
            if tool_name in available_tools:
                tool_function = available_tools[tool_name]
                try:
                    # IMPORTANT: Validate tool_args against schema if possible before calling
                    api_response = tool_function(**tool_args)
                    print(f"--- Tool '{tool_name}' executed. Result: {api_response} ---")

                    # --- Second API Call (Send Tool Response) ---
                    # Send the tool execution result back to the LLM
                    response = chat.send_message(
                        genai.types.Part.from_function_response(
                            name=tool_name,
                            response=api_response # Send the structured result back
                        )
                    )
                    print("--- Sent Tool Response to LLM. Waiting for final answer... ---")
                    # The final answer should be in this second response
                    response_part = response.candidates[0].content.parts[0] if (response.candidates and response.candidates[0].content.parts) else None

                except Exception as e:
                    print(f"Error executing tool '{tool_name}': {e}")
                    # Handle tool execution error - maybe send an error message back?
                    # For now, return None or raise
                    return f"Error executing calculation tool: {tool_name}. Details: {e}"
            else:
                print(f"Error: LLM requested unknown tool: {tool_name}")
                return f"Error: Assistant requested an unknown tool: {tool_name}"

        # --- Extract Final Answer ---
        # Whether after a tool call or directly from the first response
        if response_part and response_part.text:
            final_answer = response_part.text
            print("--- Received Final Answer from LLM ---")
            return final_answer
        else:
            # Handle cases where response might be blocked or empty after potential tool call
            print(f"Warning: Received empty or blocked final response from Gemini. Block reason: {response.prompt_feedback.block_reason if response.prompt_feedback else 'N/A'}")
            return None # Or specific error indicator

    except Exception as e:
        print(f"Error during Gemini API call with function calling: {e}")
        # Log error details
        return None

# --- Example Usage ---
# Assume 'final_prompt' is constructed as per Chapter 6
# final_answer_text = generate_with_function_calling(final_prompt)
# if final_answer_text:
#     print("\nFinal AI CFO Response:")
#     print(final_answer_text)
#     # Proceed with post-processing and citation generation
# else:
#     print("\nFailed to generate a final response.")

```

These snippets provide a practical foundation for interacting with the necessary APIs. Remember to build robust error handling, logging, and configuration management around these core interactions in the actual implementation.


---

## E. Glossary of Terms

This glossary defines key terms and acronyms used throughout this technical reference guide, specific to the AI CFO Assistant project and the broader fields of RAG, LLMs, and AI Engineering.

*   **AI CFO Assistant:** The name of the Final Year Project system described in this document, designed to provide reliable financial insights from SME documents using RAG and function calling.
*   **API (Application Programming Interface):** A set of rules and protocols that allows different software applications to communicate with each other. Used extensively in this project to interact with LLMs and embedding services.
*   **ANN (Approximate Nearest Neighbor):** A class of algorithms used in vector search to find vectors that are *close* to a query vector quickly, without guaranteeing the absolute closest match. HNSW is an example. Essential for efficient retrieval in large vector databases.
*   **Attribution:** The process of linking specific claims or pieces of information in a generated answer back to their source(s) within the original documents. A key pillar of the system's reliability.
*   **Attribution Accuracy:** A set of metrics (Precision, Recall, F1) measuring how correctly the system's generated citations point to the actual ground truth source sections/chunks containing the relevant information. (Evaluated in Chapter 8).
*   **Audit Trail:** An immutable, chronological record of system activities, crucial for security, compliance, and accountability. Comprehensive logging (Chapter 10) forms the basis of an audit trail.
*   **Batching:** Processing multiple items (e.g., text chunks for embedding, queries) together in a single request to an API or system component for improved efficiency (latency, cost).
*   **Chunking:** The process of breaking down large documents into smaller, manageable pieces (chunks) for embedding and retrieval. Semantic chunking aims to preserve logical context. (Chapter 3).
*   **CLI (Command Line Interface):** A text-based interface for interacting with the system, often used for development, testing, and scripting. (Chapter 11).
*   **Configuration Management:** The practice of managing system parameters (model IDs, thresholds, paths, prompts) externally (e.g., in YAML files) rather than hardcoding them, enabling flexibility and iteration. (Chapter 9).
*   **Context Assembler:** The component in the RAG pipeline responsible for gathering the final set of retrieved and re-ranked context sections to be included in the prompt for the generator LLM. (Chapter 2, Chapter 6).
*   **Context Window:** The maximum number of tokens (words, sub-words) that an LLM can process as input at one time. Larger context windows (like Gemini 1.5 Pro's 1M) allow more information to be considered during generation.
*   **Context-Aware Embedding:** An embedding strategy where contextual metadata (e.g., document date, type, section heading) is prepended to the text chunk before generating its vector embedding, aiming for more precise retrieval. (Chapter 4).
*   **Cross-Encoder:** A type of Transformer model used for re-ranking tasks. It processes a query and a candidate passage *together* to compute a fine-grained relevance score, generally more accurate but slower than embedding models (bi-encoders). (Chapter 5).
*   **DDL (Data Definition Language):** SQL commands used to define database structures, such as `CREATE TABLE`, `ALTER TABLE`. (Appendix B).
*   **Dense Retrieval:** Retrieval based on vector embeddings, capturing semantic similarity. Contrasted with sparse retrieval (keyword search).
*   **Docker:** A platform for developing, shipping, and running applications in containers, ensuring consistency across environments. (Chapter 11).
*   **Embedding (Vector Embedding):** A numerical representation (typically a high-dimensional vector of floating-point numbers) of a piece of text, capturing its semantic meaning. Generated by embedding models. (Chapter 4).
*   **Embedding Model:** A deep learning model (often Transformer-based) trained to convert text into dense vector embeddings. (e.g., Nomic Embed Text, BGE, Ada). (Chapter 4).
*   **Evaluation-Driven Development:** An approach where development priorities and design choices are guided by quantitative results from a rigorous evaluation framework. (Chapter 8).
*   **Faithfulness (Groundedness):** An evaluation metric measuring the degree to which an LLM's generated answer adheres strictly to the information present in the provided source context, avoiding hallucination or outside knowledge. (Chapter 8).
*   **Few-Shot Learning/Prompting:** Providing a few examples of the desired input/output format within the LLM's prompt to help it understand the task and desired behavior better. (Chapter 6).
*   **Fine-tuning:** Further training a pre-trained model (like an embedding model or LLM) on a smaller, task-specific dataset to improve its performance on that particular task. (Chapter 12).
*   **Fireworks AI:** A cloud platform providing efficient API access to various AI models, including embedding models like Nomic. (Used as an example API provider).
*   **Function Calling (Tool Use):** A capability of some LLMs (like Gemini 1.5 Pro) allowing them to request the execution of external code (tools/functions) based on the user query and context, providing arguments and receiving structured results back. Used here for reliable calculations. (Chapter 6).
*   **Gemini:** A family of multimodal Large Language Models developed by Google. Different versions (Flash, Pro, Vision, 1.5 Pro) are used for various tasks in this project (parsing, decomposition, generation).
*   **Generative AI:** AI models capable of creating new content (text, images, etc.) based on patterns learned from training data. LLMs are a primary example.
*   **GIN (Generalized Inverted Index):** A type of PostgreSQL index suitable for indexing composite types, including JSONB, enabling efficient searching within JSON structures. Used for metadata filtering. (Chapter 4).
*   **Git / GitHub:** Git is a distributed version control system. GitHub is a popular platform for hosting Git repositories. Used for managing project source code. (Chapter 9).
*   **GLM (Grounded Language Model):** A type of LLM specifically trained or fine-tuned to prioritize faithfulness to provided context over other generative capabilities, aiming to minimize hallucinations. (Mentioned in background context).
*   **Golden Dataset:** A manually curated dataset used for evaluating the system, containing representative queries, ideal answers, ground truth source information, and expected numerical values. (Chapter 8).
*   **Graceful Refusal:** The ability of the system to explicitly and correctly state when it cannot answer a query because the necessary information is not present in the provided context, rather than guessing. A key reliability feature enforced via prompting. (Chapter 6, Chapter 8).
*   **Groq:** A company and platform providing ultra-low-latency inference for specific open-source LLMs on specialized hardware (LPUs). Mentioned as a potential deployment target for fine-tuned models. (Chapter 12).
*   **Hallucination:** The tendency of LLMs to generate plausible-sounding but factually incorrect or nonsensical information not grounded in the provided context or their training data. RAG aims to minimize this.
*   **HNSW (Hierarchical Navigable Small Worlds):** An efficient algorithm for approximate nearest neighbor search in high-dimensional vector spaces, commonly used for indexing vector embeddings in databases like `pgvector`. (Chapter 4).
*   **Hybrid Search:** A retrieval strategy combining both dense (vector/semantic) search and sparse (keyword/lexical) search to leverage the strengths of both approaches. (Considered Future Work, Chapter 5).
*   **Ingestion Pipeline:** The sequence of steps involved in processing source documents (PDFs) and preparing them for storage and retrieval (Parsing, Formatting, Chunking, Embedding, Storing). (Chapter 2, Chapter 3, Chapter 4).
*   **LLM (Large Language Model):** A type of deep learning model with billions of parameters, trained on vast amounts of text data, capable of understanding and generating human-like language. (e.g., Gemini, GPT, Llama).
*   **LoRA (Low-Rank Adaptation):** A popular Parameter-Efficient Fine-Tuning (PEFT) technique that significantly reduces the computational cost and data requirements for fine-tuning large models by training only small "adapter" matrices. (Chapter 12).
*   **Markdown:** A lightweight markup language with plain-text formatting syntax, used as the standardized intermediate format for parsed document content. (Chapter 3).
*   **Metadata:** Structured data describing other data. In this project, includes document-level information (type, date, currency) and section-level information (heading) stored alongside text chunks. Used for filtering and context-aware embedding. (Chapter 3, Chapter 4).
*   **Metadata Filtering:** The process of using SQL `WHERE` clauses on stored metadata fields to narrow down the search space before performing vector search, improving retrieval efficiency and relevance. (Chapter 5).
*   **MRR (Mean Reciprocal Rank):** An evaluation metric for retrieval systems that measures the average inverse rank of the *first* relevant item found across a set of queries. Higher is better. (Chapter 8).
*   **Multimodal LLM:** An LLM capable of processing and understanding information from multiple modalities (types of data), such as text *and* images (like the layout of a PDF). Gemini Vision is an example. (Chapter 3).
*   **NeonDB:** A serverless, managed PostgreSQL database platform that supports the `pgvector` extension, used as the vector store in this project. (Chapter 4).
*   **NLI (Natural Language Inference):** A task in NLP focused on determining the logical relationship (entailment, contradiction, neutral) between a premise and a hypothesis. Can be used for evaluating faithfulness. (Mentioned in background context).
*   **Nomic Embed Text:** A specific high-performance text embedding model used as the primary choice in this project. (Chapter 4).
*   **Numerical Accuracy:** An evaluation metric measuring the correctness of numerical figures reported by the system compared to ground truth values. (Chapter 8).
*   **Observability:** The ability to understand the internal state and behavior of a system based on its outputs (logs, metrics, traces). Crucial for debugging and monitoring complex AI systems. (Chapter 10).
*   **Parsing:** The process of analyzing an input document (PDF) and extracting its content and structure into a more usable format (Markdown). (Chapter 3).
*   **PEFT (Parameter-Efficient Fine-Tuning):** Techniques (like LoRA) for fine-tuning large pre-trained models by updating only a small fraction of their parameters, making tuning much more accessible. (Chapter 12).
*   **`pgvector`:** A popular open-source extension for PostgreSQL that adds vector similarity search capabilities to the database. (Chapter 4).
*   **Pipeline:** A sequence of processing stages where the output of one stage becomes the input for the next. The RAG system is implemented as a pipeline. (Chapter 2).
*   **Post-processing:** Steps performed on the raw output of the generator LLM before presenting it to the user, including cleanup, basic validation, and citation formatting. (Chapter 7).
*   **Precision@K:** A retrieval evaluation metric measuring the fraction of the top K retrieved items that are relevant. (Chapter 8).
*   **Prompt Engineering:** The art and science of designing effective prompts (instructions) to guide LLMs towards desired behaviors and outputs. (Chapter 6).
*   **Query Decomposition:** The process of breaking down a complex user query into multiple simpler sub-queries that can be processed individually. (Chapter 5).
*   **RAG (Retrieval-Augmented Generation):** An AI architecture that enhances LLM generation by first retrieving relevant context passages from an external knowledge base (like processed documents) and providing this context within the LLM's prompt. (Core concept).
*   **Recall@K:** A retrieval evaluation metric measuring the fraction of *all* relevant items that are found within the top K retrieved items. (Chapter 8).
*   **Re-ranking:** The process of taking an initial list of candidate documents/chunks (e.g., from vector search) and applying a more sophisticated model (like a cross-encoder) to re-order them for better relevance before final selection. (Chapter 5).
*   **Reliability:** The core design philosophy, encompassing accuracy, faithfulness, attribution, and robustness.
*   **Retrieval:** The process of finding and fetching the most relevant information (chunks/sections) from the vector store based on a user query. (Chapter 5).
*   **RRF (Reciprocal Rank Fusion):** A method for combining ranked lists from multiple retrieval sources (e.g., vector search and keyword search) into a single, improved ranking. (Mentioned in Chapter 5).
*   **Semantic Chunking:** A chunking strategy that aims to divide documents along logical boundaries (like headings or paragraphs) to preserve meaning and context, rather than arbitrary fixed sizes. (Chapter 3).
*   **Semantic Search:** Searching based on meaning and context (using vector embeddings) rather than just keyword matching.
*   **SME (Small and Medium Enterprise):** The target user group for the AI CFO Assistant.
*   **Streamlit:** A Python library for rapidly creating simple web applications, suitable for demos and prototypes. (Chapter 11).
*   **Synthetic Data:** Artificially generated data used for training or evaluation when real-world data is unavailable or insufficient. Used here for creating the financial PDF corpus and potentially for fine-tuning data augmentation. (Chapter 8).
*   **Token:** A basic unit of text processed by LLMs and tokenizers (can be a word, sub-word, or character). Model context windows and API pricing are often based on token counts.
*   **Tool Use:** See **Function Calling**.
*   **Vector Database:** A database optimized for storing and querying high-dimensional vector embeddings, typically supporting efficient Approximate Nearest Neighbor (ANN) search. (Chapter 4).
*   **YAML (YAML Ain't Markup Language):** A human-readable data serialization standard, often used for configuration files and, in this project, for embedding metadata within Markdown. (Chapter 3).

---
This concludes the Appendix and the main body of the AI CFO Assistant Technical Reference Guide.