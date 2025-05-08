
# AI CFO Assistant: Technical Reference Guide

**Version:** 1.2

## Table of Contents

*   [Chapter 1: Introduction](#chapter-1-introduction)
    *   [1.1 Project Overview](#11-project-overview)
    *   [1.2 The Problem: Financial Insight Bottleneck](#12-the-problem-financial-insight-bottleneck)
    *   [1.3 The Solution: AI CFO Assistant](#13-the-solution-ai-cfo-assistant)
    *   [1.4 Core Design Goal: Reliability](#14-core-design-goal-reliability)
    *   [1.5 Key Objectives](#15-key-objectives)
    *   [1.6 Scope](#16-scope)
    *   [1.7 Technology Overview](#17-technology-overview)
    *   [1.8 Document Purpose](#18-document-purpose)
*   [Chapter 2: System Architecture](#chapter-2-system-architecture)
    *   [2.1 Architecture Design](#21-architecture-design)
    *   [2.2 Ingestion Pipeline Diagram (Conceptual)](#22-ingestion-pipeline-diagram-conceptual)
    *   [2.3 Component Roles](#23-component-roles)
    *   [2.4 Data Flow (Ingestion)](#24-data-flow-ingestion)
*   [Chapter 3: Data Ingestion Pipeline](#chapter-3-data-ingestion-pipeline)
    *   [3.1 Input: Financial PDFs & User Context](#31-input-financial-pdfs--user-context)
    *   [3.2 Parsing with Multimodal AI (`FinancialDocParser`)](#32-parsing-with-multimodal-ai-financialdocparser)
    *   [3.3 Metadata Extraction (`MetadataExtractor`)](#33-metadata-extraction-metadataextractor)
    *   [3.4 Sectioning (`Sectioner`)](#34-sectioning-sectioner)
    *   [3.5 Analogous Structure: Financial Document "AST"](#35-analogous-structure-financial-document-ast)
*   [Chapter 4: Embedding & Storage (Supabase)](#chapter-4-embedding--storage-supabase)
    *   [4.1 Chunking (`ChunkingService`)](#41-chunking-chunkingservice)
    *   [4.2 Embedding Strategy (`EmbeddingService`)](#42-embedding-strategy-embeddingservice)
    *   [4.3 Supabase Backend](#43-supabase-backend)
    *   [4.4 Database Structure](#44-database-structure)
    *   [4.5 Storage Structure & Security](#45-storage-structure--security)
    *   [4.6 Persistence (`SupabaseService`)](#46-persistence-supabaseservice)
*   [Chapter 5: Retrieval Process (Future Work)](#chapter-5-retrieval-process-future-work)
    *   [5.1 How Retrieval Works](#51-how-retrieval-works)
    *   [5.2 Goal: Context Provider, Not Just RAG](#52-goal-context-provider-not-just-rag)
    *   [5.3 Handling Complex Queries](#53-handling-complex-queries)
    *   [5.4 Identifying Key Details & Filters](#54-identifying-key-details--filters)
    *   [5.5 Filtering by Details (Inc. User ID)](#55-filtering-by-details-inc-user-id)
    *   [5.6 Finding Relevant Text (Multi-Method Approach)](#56-finding-relevant-text-multi-method-approach)
    *   [5.7 Refining Results (Re-ranking)](#57-refining-results-re-ranking)
    *   [5.8 Final Selection](#58-final-selection)
*   [Chapter 6: Answer Generation & Tools (Future Work)](#chapter-6-answer-generation--tools-future-work)
    *   [6.1 Choosing the AI Model](#61-choosing-the-ai-model)
    *   [6.2 Preparing Context](#62-preparing-context)
    *   [6.3 Guiding the AI (Prompting)](#63-guiding-the-ai-prompting)
    *   [6.4 Using Calculation Tools](#64-using-calculation-tools)
    *   [6.5 Managing Tool Use (Function Calling)](#65-managing-tool-use-function-calling)
*   [Chapter 7: Final Output & Sources (Future Work)](#chapter-7-final-output--sources-future-work)
    *   [7.1 Cleaning the Answer](#71-cleaning-the-answer)
    *   [7.2 Basic Checks](#72-basic-checks)
    *   [7.3 Showing Sources](#73-showing-sources)
*   [Chapter 8: Evaluation (Future Work)](#chapter-8-evaluation-future-work)
    *   [8.1 Why Evaluate?](#81-why-evaluate)
    *   [8.2 The Need for Rigorous, Quantitative Evals](#82-the-need-for-rigorous-quantitative-evals)
    *   [8.3 Test Data](#83-test-data)
    *   [8.4 Creating Test Cases](#84-creating-test-cases)
    *   [8.5 Measuring Performance](#85-measuring-performance)
    *   [8.6 Automation](#86-automation)
    *   [8.7 Improving with Evaluation](#87-improving-with-evaluation)
*   [Chapter 9: Building the System (Current State)](#chapter-9-building-the-system-current-state)
    *   [9.1 Technology Summary](#91-technology-summary)
    *   [9.2 Key Libraries Used](#92-key-libraries-used)
    *   [9.3 Setup](#93-setup)
    *   [9.4 Configuration](#94-configuration)
    *   [9.5 Code Structure](#95-code-structure)
    *   [9.6 Version Control](#96-version-control)
    *   [9.7 Development Philosophy: Agility and Iteration](#97-development-philosophy-agility-and-iteration)
*   [Chapter 10: Monitoring & Logs (Future Work)](#chapter-10-monitoring--logs-future-work)
    *   [10.1 Why Log?](#101-why-log)
    *   [10.2 Log Details](#102-log-details)
    *   [10.3 How Logging Works](#103-how-logging-works)
    *   [10.4 Using Logs](#104-using-logs)
*   [Chapter 11: Running the System](#chapter-11-running-the-system)
    *   [11.1 Testing Setup (Notebooks)](#111-testing-setup-notebooks)
    *   [11.2 Production Ideas](#112-production-ideas)
    *   [11.3 Handling More Users](#113-handling-more-users)
    *   [11.4 Managing Costs](#114-managing-costs)
    *   [11.5 User Experience: Streaming Responses](#115-user-experience-streaming-responses)
*   [Chapter 12: Next Steps](#chapter-12-next-steps)
    *   [12.1 Immediate Next Steps](#121-immediate-next-steps)
    *   [12.2 Future Enhancements](#122-future-enhancements)
*   [Chapter 13: Strategic Considerations and Future Vision](#chapter-13-strategic-considerations-and-future-vision)
    *   [13.1 Market Validation: The Office of the CFO Needs](#131-market-validation-the-office-of-the-cfo-needs)
    *   [13.2 The "Bitter Lesson": Vertical vs. Horizontal AI Applications](#132-the-bitter-lesson-vertical-vs-horizontal-ai-applications)
    *   [13.3 Implications of Opaque AI Reasoning](#133-implications-of-opaque-ai-reasoning)
    *   [13.4 Impact of Future Models](#134-impact-of-future-models)
    *   [13.5 Defending Against General Agents](#135-defending-against-general-agents)
    *   [13.6 Evolution: Becoming Infrastructure](#136-evolution-becoming-infrastructure)
*   [Appendix](#appendix)
    *   [A. Example AI Prompts](#a-example-ai-prompts)
    *   [B. Database Setup SQL (`database_setup.sql`)](#b-database-setup-sql-database_setupsql)
    *   [C. Storage Setup SQL (`storage_setup.sql`)](#c-storage-setup-sql-storage_setupsql)
    *   [D. Key Terms](#d-key-terms)

---

## Chapter 1: Introduction

### 1.1 Project Overview

This guide details the **AI CFO Assistant** ingestion pipeline and discusses the strategic considerations for the full system. This system enables Small and Medium Businesses (SMEs) to securely upload their financial documents and receive reliable, context-aware answers to questions about their finances. It leverages Retrieval-Augmented Generation (RAG), AI Tool Use (Function Calling), and a robust backend built on Supabase.

### 1.2 The Problem: Financial Insight Bottleneck

SMEs often struggle to extract timely insights from complex PDF financial reports. Data is siloed, difficult to search, and requires expertise to interpret, hindering informed decision-making.

### 1.3 The Solution: AI CFO Assistant

The assistant provides a secure, intelligent interface to financial documents. Users upload reports; the system processes them; users ask questions in natural language. The system retrieves relevant information *only from the user's documents*, performs necessary calculations using validated tools, generates a factual answer, and cites the specific sources used.

### 1.4 Core Design Goal: Reliability

Accuracy and trustworthiness are paramount for financial data. The system prioritizes **Reliability** by:

1.  **Grounded Answers:** Answers are derived solely from the user-provided documents.
2.  **Accurate Calculations:** Math is performed by reliable, deterministic Python tools, not the LLM.
3.  **Verifiable Sources:** Answers include citations linking back to specific document sections.
4.  **Data Privacy:** User data is strictly isolated via multi-tenancy controls.

### 1.5 Key Objectives

*   Accurately parse and extract data from complex financial PDFs.
*   Implement an effective context retrieval pipeline for information retrieval.
*   Integrate reliable calculation tools via LLM Function Calling.
*   Ensure AI answers are grounded in provided context and avoid hallucination.
*   Establish an automated evaluation framework for reliability metrics.
*   Build a functional Proof-of-Concept.
*   **Implement secure multi-tenancy using user accounts and data isolation.**
*   **Design for flexibility to adapt to rapid AI advancements.**

### 1.6 Scope

**In Scope (Ingestion Pipeline - Completed):**

*   Handling PDF financial reports.
*   AI-driven text, layout, and metadata extraction (`FinancialDocParser`, `MetadataExtractor`).
*   Structuring content as Markdown.
*   Storing full extracted Markdown (`documents.full_markdown_content`).
*   Segmenting Markdown into logical sections (`Sectioner`).
*   Chunking section content (`ChunkingService` with `chonkie`).
*   Generating context-aware embeddings (`EmbeddingService` with OpenAI).
*   Securely storing original files, metadata, sections, chunks, and embeddings in Supabase (`SupabaseService`).
*   Enforcing multi-tenancy via Supabase Auth (`user_id`) and RLS.

**In Scope (Future Work - Query/API):**

*   Context retrieval logic (filtering, search methods, re-ranking).
*   Answer generation LLM integration with tool use.
*   Calculation tool implementation.
*   API layer (e.g., FastAPI) for user interaction (upload, query).
*   User authentication handling in the API.
*   Automated evaluation framework.
*   System logging (to Supabase).
*   **Streaming responses for improved user experience.**

**Out of Scope (Initial):**

*   Non-financial documents, non-PDF formats (DOCX, XLSX), heavily scanned PDFs.
*   Direct integration with accounting software.
*   Financial advice or forecasting.
*   Advanced visualization.
*   Highly polished UI/UX.

### 1.7 Technology Overview

*   **Language:** Python 3.x
*   **AI Models:**
    *   Google Gemini API (`google-genai`): For multimodal parsing and structured metadata extraction.
    *   OpenAI API (`openai`): For text embeddings (`text-embedding-3-small`).
*   **Backend:** **Supabase**
    *   Database: PostgreSQL with `pgvector` extension.
    *   Authentication: Supabase Auth.
    *   File Storage: Supabase Storage.
*   **PDF Parsing:** `pymupdf` (Fitz)
*   **Chunking:** `chonkie` (`RecursiveChunker`)
*   **Data Validation:** `pydantic`
*   **Configuration:** `.env` files (`python-dotenv`)
*   **Key Python Libraries:** `supabase-py`, `google-genai`, `openai`, `pymupdf`, `chonkie`, `pydantic`.
*   **Web Framework (Future):** FastAPI

### 1.8 Document Purpose

This technical reference guide documents the design, implementation, and rationale for the AI CFO Assistant's ingestion pipeline and outlines the strategic considerations for its future development in the context of the rapidly evolving AI landscape. It serves as a guide for developers and stakeholders involved in the project.

---

## Chapter 2: System Architecture

### 2.1 Architecture Design

The system utilizes a modular, service-oriented architecture centered around a pipeline for ingesting financial documents and a future pipeline for querying them. Supabase provides the core backend infrastructure (DB, Auth, Storage), enabling secure multi-tenancy through user identification (`user_id`) and Row-Level Security (RLS). The ingestion pipeline focuses on preparing data for the query process, ensuring structural understanding and context are preserved.

### 2.2 Ingestion Pipeline Diagram (Conceptual)

```mermaid
graph LR
    A[User Uploads PDF (via API)] --> B(Authenticate User);
    B --> C{Get User ID};
    C --> D[FinancialDocParser: PDF -> Markdown];
    D --> E[MetadataExtractor: Markdown Snippet -> Metadata];
    C --> F(SupabaseService);
    D --> G[Sectioner: Markdown -> Sections];
    E --> F; % Metadata needed for saving document
    A --> F; % PDF Buffer needed for storage
    D --> F; % Full Markdown needed for saving document
    F -- Stores File --> H[Supabase Storage (User-Specific Path)];
    F -- Saves Doc Record --> I[DB: documents table (with full_markdown)];
    G --> J[ChunkingService: Sections -> Chunks];
    E --> J; % Metadata needed for chunk enrichment
    I -- Doc ID --> G; % Doc ID needed for sectioning
    I -- Doc ID --> J; % Doc ID needed for chunking
    C -- User ID --> G; % User ID needed for sectioning
    C -- User ID --> J; % User ID needed for chunking
    G -- Sections Data --> K(SupabaseService);
    K -- Saves Sections --> L[DB: sections table];
    J -- Chunks Data --> M[EmbeddingService: Augment Text & Embed];
    L -- Section IDs --> J; % Section IDs needed for chunking
    M -- Chunks w/ Embeddings --> N(SupabaseService);
    N -- Saves Chunks --> O[DB: chunks table];
    F -- Updates Status --> I; % Mark document as completed/failed
```

*Note: The diagram shows the flow. The `IngestionPipeline` class orchestrates these calls.*

### 2.3 Component Roles

*   **Ingestion Pipeline Orchestrator (`pipeline.py`):** Manages the overall sequence of ingestion steps.
*   **AI Clients (`llm/`):** Interface with Gemini and OpenAI APIs.
*   **`FinancialDocParser`:** Converts PDF to structured Markdown using multimodal AI.
*   **`MetadataExtractor`:** Extracts document-level metadata (type, company, dates, summary) from Markdown snippet using text LLM and Pydantic schema.
*   **`Sectioner`:** Splits full Markdown into logical sections based on headings and page markers.
*   **`ChunkingService`:** Breaks section Markdown into smaller chunks using `chonkie` and copies metadata.
*   **`EmbeddingService`:** Generates vector embeddings for chunks using context-augmented text.
*   **`SupabaseService`:** Handles all interactions with Supabase (DB inserts/updates, Storage uploads), ensuring `user_id` is applied correctly for RLS.
*   **Supabase Auth:** Manages user accounts and authentication, providing the crucial `user_id`.
*   **Supabase Storage:** Stores original PDF files securely, segregated by `user_id`.
*   **Supabase PostgreSQL:** The core database for storing all structured data.
    *   **`pgvector` Extension:** Enables efficient storage and similarity searching of vector embeddings.

### 2.4 Data Flow (Ingestion)

1.  **Input:** API receives PDF buffer, `user_id`, filename, `doc_type`.
2.  **`IngestionPipeline.run` initiated.**
3.  **Parse (`FinancialDocParser`):** Produces `combined_markdown` string.
4.  **Extract Metadata (`MetadataExtractor`):** Produces `FinancialDocumentMetadata` object.
5.  **Upload (`SupabaseService`):** PDF buffer uploaded to Storage path (`{user_id}/{temp_doc_id}/{filename}`). Returns `storage_path`.
6.  **Save Document (`SupabaseService`):** Metadata, IDs, paths, `combined_markdown` -> Insert into `documents`. Returns final `document_id`.
7.  **Section (`Sectioner`):** `combined_markdown`, `document_id`, `user_id` -> `List[SectionData]`.
8.  **Save Sections (`SupabaseService`):** `List[SectionData]` -> Bulk insert into `sections`. Returns `List[section_id]`.
9.  **Add Section IDs:** Pipeline adds generated `section_id`s to `sections_data`.
10. **Chunk (`ChunkingService`):** `List[SectionData]` (with IDs), `document_metadata`, IDs -> `List[ChunkData]`.
11. **Embed (`EmbeddingService`):** `List[ChunkData]` -> Adds `embedding` vector to `List[ChunkData]`.
12. **Save Chunks (`SupabaseService`):** `List[ChunkData]` (with embeddings) -> Bulk insert into `chunks`.
13. **Update Status (`SupabaseService`):** `document_id`, 'completed' -> Update `documents`.
14. **Output:** `PipelineResult` dictionary returned.

---

## Chapter 3: Data Ingestion Pipeline

*(This chapter details the first few stages covered by the implemented services)*

### 3.1 Input: Financial PDFs & User Context

The pipeline starts when an authenticated user uploads a financial document (PDF). The system receives the file content as an in-memory buffer, the original filename, the file type (`doc_type`), and crucially, the unique identifier (`user_id`) of the authenticated user from Supabase Auth.

### 3.2 Parsing with Multimodal AI (`FinancialDocParser`)

*   **Purpose:** Accurately convert the visual PDF content into structured Markdown.
*   **Implementation:** The `FinancialDocParser` service uses `pymupdf` to render each page as a PNG image. These images are processed concurrently by sending them to a multimodal AI model (Gemini via `GeminiClient.generate_content`) with a specific prompt (`PDF_ANNOTATION_PROMPT`) requesting accurate Markdown conversion, including tables and formatting. Basic retry logic for API errors is included.
*   **Output:** A single `combined_markdown` string containing all page content, interleaved with custom page separators (`--- Page X Start ---`, `--- Page X End ---`). This full string is stored in the `documents.full_markdown_content` column.

### 3.3 Metadata Extraction (`MetadataExtractor`)

*   **Purpose:** Extract key document-level details required for filtering and context.
*   **Implementation:** The `MetadataExtractor` service takes the initial portion (e.g., first 16k characters) of the `combined_markdown`. It sends this snippet to a text-based LLM (Gemini via `GeminiClient.generate_content`) using a prompt (`METADATA_EXTRACTION_PROMPT`) designed for structured extraction. Crucially, it leverages Gemini's capability to return JSON conforming to a predefined Pydantic schema (`FinancialDocumentMetadata`), ensuring type safety and handling of missing values with placeholders (`-1`, `""`, `"1900-01-01"`).
*   **Output:** A `FinancialDocumentMetadata` object.

### 3.4 Sectioning (`Sectioner`)

*   **Purpose:** Segment the full `combined_markdown` into logical sections based on document structure.
*   **Implementation:** The `Sectioner` service uses custom Python logic with regular expressions to identify Markdown headings (`#`, `##`, etc.) as section boundaries. It collects the text content between headings and uses the page separators (`--- Page X Start ---`) to determine the `page_numbers` array associated with each section. It also assigns a sequential `section_index`.
*   **Output:** A list of `SectionData` dictionaries, ready to be saved to the `sections` table. Each dictionary contains `document_id`, `user_id`, `section_heading`, `page_numbers`, `content_markdown` (for that specific section), and `section_index`.

### 3.5 Analogous Structure: Financial Document "AST"

Just as Abstract Syntax Trees (ASTs) capture the structural essence of code, the parsing, metadata extraction, and sectioning stages aim to create an analogous structural representation of financial documents. By converting the visual PDF into structured Markdown, identifying logical sections, and extracting key metadata, we are building a representation that allows the system to understand the document's hierarchy and components beyond just raw text. This structured view (like headings, tables, or metadata) is crucial for accurate filtering and providing the LLM with context rooted in the document's original organization.

---

## Chapter 4: Embedding & Storage (Supabase)

*(This chapter details the latter stages of ingestion covered by the implemented services)*

### 4.1 Chunking (`ChunkingService`)

*   **Purpose:** Further divide section content into smaller, fixed-size chunks suitable for embedding, while retaining context.
*   **Implementation:** The `ChunkingService` iterates through the `SectionData` list. For each section's `content_markdown`, it uses `chonkie.RecursiveChunker` configured with the "markdown" recipe and a specific `chunk_size` (e.g., 512 tokens). For every chunk generated by `chonkie`, it creates a `ChunkData` dictionary, copying key metadata (like `doc_specific_type`, `doc_year`, `company_name`, `section_heading`) from the document/section level into dedicated fields within the chunk data structure. Positional information (`chunk_index`, `start/end_char_index`) is also included.
*   **Output:** A flat list (`List[ChunkData]`) of all chunks from all sections.

### 4.2 Embedding Strategy (`EmbeddingService`)

*   **Purpose:** Generate meaningful vector representations (embeddings) for each chunk.
*   **Implementation:** The `EmbeddingService` takes the `List[ChunkData]`. For each chunk, it constructs an "augmented text" string by pre-pending key copied metadata (e.g., "Document Type: Invoice. Year: 2024...") to the `chunk_text`. This list of augmented strings is sent to the embedding model API (OpenAI `text-embedding-3-small` via `OpenAIClient`). The resulting embedding vectors are added back to the corresponding `ChunkData` dictionaries under the `embedding` key, along with the `embedding_model` name.
*   **Output:** The `List[ChunkData]`, now enriched with embedding vectors.

### 4.3 Supabase Backend

Supabase provides the integrated backend infrastructure:

*   **Supabase Auth:** Handles user sign-up, login, and provides the unique `user_id` (UUID) necessary for multi-tenancy.
*   **Supabase Storage:** Stores the original uploaded PDF files privately. Access is controlled via RLS policies based on user ID prefixes in the file path.
*   **Supabase PostgreSQL:** The core database for storing all structured data.
    *   **`pgvector` Extension:** Enables efficient storage and similarity searching of vector embeddings.

### 4.4 Database Structure

The PostgreSQL database schema is defined in `scripts/database_setup.sql` (see Appendix B) and includes:

*   **`documents` table:** Stores document metadata, `user_id`, storage path, status, and the `full_markdown_content`. Indexed for filtering. RLS enabled.
*   **`sections` table:** Stores logical sections, their specific `content_markdown`, page numbers, index, and links (`document_id`, `user_id`). Indexed. RLS enabled.
*   **`chunks` table:** Stores the final text chunks, their vector `embedding` (`vector(1536)` type), copied metadata for filtering, and links (`section_id`, `document_id`, `user_id`). Indexed, including HNSW index on `embedding`. RLS enabled.

### 4.5 Storage Structure & Security

*   **Bucket:** A private bucket `financial-pdfs` is used.
*   **Path Structure:** Files are uploaded to `{user_id}/{document_id}/{filename}`.
*   **RLS Policies:** Defined in `scripts/storage_setup.sql` (see Appendix C), these policies on `storage.objects` ensure users can only `SELECT`, `INSERT`, `UPDATE`, or `DELETE` files where the *first segment* of the path matches their own `auth.uid()`.

### 4.6 Persistence (`SupabaseService`)

*   **Purpose:** Abstract all direct interactions with Supabase Storage and Database.
*   **Implementation:** The `SupabaseService` class uses the `supabase-py` client library. It assumes an authenticated client context is available.
    *   `upload_pdf_to_storage`: Uploads PDF bytes to the correct user-specific path.
    *   `save_document_record`: Inserts data into the `documents` table.
    *   `save_sections_batch`: Bulk inserts into the `sections` table.
    *   `save_chunks_batch`: Bulk inserts into the `chunks` table (including vectors).
    *   `update_document_status`: Updates the `documents.status` field.
*   **RLS Compliance:** Correctly includes the `user_id` in database operations, relying on the authenticated client session for Supabase to enforce RLS policies.

---

## Chapter 5: Retrieval Process (Future Work)

*(This chapter outlines the planned functionality for querying the ingested data)*

### 5.1 How Retrieval Works

Finding the right information involves understanding the query, filtering data (critically by user), searching for semantic similarity, and refining the results.

### 5.2 Goal: Context Provider, Not Just RAG

The objective of the retrieval process is to act as an effective **context provider** for the Language Model, not strictly to implement a traditional embedding-based RAG pipeline. While embeddings and vector search are valuable tools, the focus is on providing the LLM with the most relevant and necessary information from the user's documents, regardless of the specific method used to find it. This might involve combining multiple techniques.

### 5.3 Handling Complex Queries

A planned step involves using an LLM to decompose complex questions into simpler sub-queries for sequential processing.

### 5.4 Identifying Key Details & Filters

The system will parse the user query to extract explicit filters like dates, company names, or report types.

### 5.5 Filtering by Details (Inc. User ID)

The **first and most critical filter** applied to any database query (sections or chunks) will be `WHERE user_id = [authenticated_user_id]`. Additional metadata filters (year, type, company) identified from the query will further narrow the search space within the user's data.

### 5.6 Finding Relevant Text (Multi-Method Approach)

Finding the right context may involve a combination of techniques, driven by the specific query and the structure of financial data:

*   **Vector Search:** Using the `pgvector` extension to find chunks semantically similar to the query embedding *within the filtered set*.
*   **Keyword Search:** Leveraging database full-text search capabilities to find exact terms or phrases mentioned in the query.
*   **Metadata-Driven Lookup:** Directly retrieving sections or chunks based on extracted metadata (e.g., find all sections from the "Balance Sheet" of the "2024 Annual Report").
*   **Structure-Aware Navigation:** Potentially, in the future, understanding that a query about "Net Profit" might require looking at sections related to "Revenue" and "Expenses" within the same reporting period.

The goal is to use the most effective method or combination of methods for a given financial query type to ensure high precision and recall.

### 5.7 Refining Results (Re-ranking)

The initial chunks/sections retrieved via various search methods will likely be re-ranked using a more computationally intensive cross-encoder model or domain-specific logic to improve the relevance ordering before passing to the answer generation stage.

### 5.8 Final Selection

A predefined number of top-ranked, relevant sections/chunks will be selected to form the context for the Answer Generation LLM.

---

# Chapter 6: Answer Generation & Tools

This is where the final answer is created, using the retrieved information and potentially external tools for calculations.

## 6.1 Choosing the AI Model

We use a powerful AI model (like Gemini 1.5 Pro) for generating answers.

*   **Why this model?** It can handle a lot of text at once (large context window), understands instructions well, and can reliably use external tools (function calling).

## 6.2 Preparing Context

We build the input for the AI by combining:

*   The user's original question.
*   Detailed instructions for the AI (see next section).
*   Descriptions of the available calculation tools.
*   The full text and metadata of the top document sections found during retrieval.

Clear formatting and separators are used so the AI understands the different parts.

## 6.3 Guiding the AI (Prompting)

Prompting (giving instructions to the AI) is critical for reliability:

*   **Be Clear:** Instructions must be simple and direct ("MUST", "MUST NOT").
*   **Set the Role:** Tell the AI it's a helpful, factual financial assistant.
*   **Stay Grounded:** The MOST important rule is to *only* use the provided document text.
*   **Refuse Gracefully:** Tell it exactly what to say if the answer is *not* in the documents.
*   **Cite Sources:** Instruct it to add citations after facts.
*   **Use Tools:** Tell it when and how to use the calculation tools.
*   **Show Examples:** Include a few examples of good answers, refusals, and tool use to demonstrate expected behavior.

## 6.4 Using Calculation Tools

For accuracy, calculations are handled by our own Python code, not the AI's internal (sometimes unreliable) math skills. This is critical for financial reliability.

*   We define simple functions for needed calculations (like summing numbers, finding ratios).
*   These functions handle errors (like dividing by zero) and ensure deterministic, auditable results.
*   We create structured descriptions (schemas) for these tools so the AI knows they exist and how to use them.

## 6.5 Managing Tool Use

The system controls the conversation with the AI:

1.  Send the prompt, context, and tool descriptions.
2.  The AI might respond with a request to use a tool (e.g., "Call `calculate_ratio` with X and Y").
3.  The system runs the specified Python function with the arguments the AI provided.
4.  The system sends the function's result (the calculated number) back to the AI.
5.  The AI reads the result and generates the final answer incorporating the calculation.

Financial tasks requiring calculation tools, like "variance analysis," "generating flux verbiage for key metrics," or deriving inputs for "forecasting" or "multivariate analysis," are specific examples of where this tool use will be critical. Future tools could also support tasks like simplified "Monte Carlo simulation to estimate financial outcomes" using extracted data.

---

# Chapter 7: Final Output & Sources

The raw answer from the AI needs final processing before showing it to the user.

## 7.1 Cleaning the Answer

*   Remove any extra text the AI might add.
*   Make sure formatting (like numbers) is consistent.

## 7.2 Basic Checks

We run quick checks on the answer:

*   Do any numbers in the answer appear in the original source text? (This is a simple check, not perfect, especially for calculated numbers).
*   If the question wasn't answerable, did the AI give the correct "refusal" message?

These checks help catch obvious errors.

## 7.3 Showing Sources

To build trust, we show the user which document sections were used.

*   We keep track of the top sections sent to the AI.
*   We use their metadata (filename, heading) to create simple citations like "[Report Name, Section Title]".
*   These citations are added to the final answer. This provides verifiability back to the original document structure.

---

# Chapter 8: Evaluation

## 8.1 Why Evaluate?

Because reliability is key, we don't just hope it works; we **prove it works** using objective testing. Evaluation helps us measure performance, find problems, see if changes improve things, and show how reliable the system is.

## 8.2 The Need for Rigorous, Quantitative Evals

Reliability is paramount for financial data. As seen in high-stakes domains like autonomous vehicles or code generation, you "can't just yolo" AI systems. Building trust and ensuring accuracy requires a rigorous, quantitative evaluation framework. This framework serves as the "hill to climb," guiding development and validating improvements.

## 8.3 Test Data

We test using financial PDF documents that we create ourselves (synthetic data). This gives us control and ensures we know the correct answers. We generate reports across different periods and types.

## 8.4 Creating Test Cases

We create a dataset of questions and their *correct* answers (Golden Dataset). Each test case includes:

*   The question.
*   The perfect, accurate answer.
*   The exact document sections that contain the answer (ground truth).
*   Any numbers involved.
*   Whether the question should *not* be answerable (requiring a refusal).

A key part of this dataset is including cases where the correct response is to refuse because the information isn't available.

## 8.5 Measuring Performance

We measure several things automatically using our Golden Dataset:

*   **Number Accuracy:** Are the numbers in the answer correct compared to our ground truth?
*   **Faithfulness:** Does the answer *only* use information from the provided document sections? (We use another AI model to check this).
*   **Source Accuracy:** Do the provided citations point to the correct source sections?
*   **Finding Performance:** How well did the system find the relevant sections in the first place?
*   **Refusal Accuracy:** Did it correctly refuse to answer when it should have?
*   **Structured Extraction Accuracy:** For tasks like table or key metric extraction, evaluate if the structured data output matches the ground truth.

## 8.6 Automation

We use an automated script to run all the test cases against the system and calculate these metrics. This lets us quickly see how changes affect performance.

## 8.7 Improving with Evaluation

Testing isn't just the end; it's part of development. We:

1.  Run tests to see where the system is weak (e.g., struggles with specific table formats, misinterprets dates, hallucinates numbers).
2.  Make targeted changes (e.g., improve prompts, adjust retrieval settings, enhance parsing logic, fix calculation tools).
3.  Run tests again to see if it improved (and didn't break anything else).
4.  Keep track of results to show progress and demonstrate reliability gains.

---

## Chapter 9: Building the System (Current State)

### 9.1 Technology Summary

*   **Code:** Python 3.x
*   **AI APIs:** Google Gemini (`google-genai`), OpenAI (`openai`)
*   **Backend:** Supabase (PostgreSQL + `pgvector`, Auth, Storage)
*   **PDF Parsing:** `pymupdf`
*   **Chunking:** `chonkie`
*   **Data Models:** `pydantic`
*   **Environment:** `.env` files (`python-dotenv`)
*   **Web Framework (Future):** FastAPI

### 9.2 Key Libraries Used

*   `supabase-py`: Supabase client.
*   `google-genai`: Gemini API interaction.
*   `openai`: OpenAI API interaction (embeddings).
*   `pymupdf`: PDF rendering.
*   `chonkie`: Recursive Markdown chunking.
*   `pydantic`: Metadata schema definition and validation.
*   `python-dotenv`: Loading environment variables.
*   `fastapi`/`uvicorn` (Future): Web serving.

### 9.3 Setup

*   Python virtual environment (`.venv`).
*   `requirements.txt` for dependencies.
*   `.env` file for storing API keys and Supabase credentials (excluded from Git).

### 9.4 Configuration

*   API Keys and Supabase URL/Key stored in `.env`.
*   AI model names are hardcoded in client/service classes (could be moved to config).
*   Chunking parameters (`chunk_size`, `min_characters_per_chunk`) are configurable in `ChunkingService.__init__`.

### 9.5 Code Structure

The implementation follows the structure outlined in Chapter 2.3, using `src/llm/` for AI clients and `src/services/` for processing logic, orchestrated by `src/pipeline.py`. Future API code will likely reside in `src/api/`.

### 9.6 Version Control

Git and GitHub are used for version control. The `.gitignore` file prevents secrets (`.env`) and generated files (`__pycache__`, `.venv`) from being committed.

### 9.7 Development Philosophy: Agility and Iteration

Given the rapid pace of AI advancements, the system is designed with modularity (Service-Oriented Architecture) to facilitate quick iteration and adaptation. Components (like the embedding model, chunking strategy, or even the core LLM used for generation) can be swapped out or updated with minimal impact on other parts of the system. This aligns with the need for agility in a fast-moving technology space, allowing the project to pivot or adjust strategies as new models and capabilities emerge.

---

*(Chapters 10 describes future logging; Chapter 11 discusses deployment)*

## Chapter 10: Monitoring & Logs (Future Work)
## Chapter 11: Running the System

### 11.1 Testing Setup (Notebooks)

The ingestion pipeline components and the end-to-end flow were developed and tested using Jupyter notebooks located in the `notebooks/` directory. These notebooks demonstrate individual service functionality and the final integrated pipeline execution against a configured Supabase project.

### 11.2 Production Ideas

A production deployment would involve wrapping the `IngestionPipeline` and the query/generation logic within a web framework like FastAPI, deploying it as a scalable service (e.g., using Docker containers on a cloud platform), and likely implementing background task queues for handling the potentially long-running ingestion process triggered by API uploads.

### 11.3 Handling More Users

The current design supports multi-tenancy via `user_id` and RLS. Scaling requires attention to database indexing (already implemented), potential database connection pooling, API rate limits for AI services, and potentially scaling the application instances running the pipeline.

### 11.4 Managing Costs

Costs primarily involve AI API usage (Gemini, OpenAI) and Supabase resource consumption. Tracking token counts (possible via API responses or estimations) and Supabase usage metrics is important. Model selection, efficient prompting/processing (like using snippets for metadata), and optimizing retrieval queries help manage costs.

### 11.5 User Experience: Streaming Responses

To provide a responsive user experience, especially during the potentially long-running retrieval and answer generation steps, the API will be designed to stream responses. This will leverage Server-Sent Events (SSE) via FastAPI's `StreamingResponse`. The backend generator will yield status updates (e.g., "Retrieving documents...", "Generating answer...") and LLM tokens as they are produced, allowing the frontend to display progress and the answer incrementally.

---

## Chapter 12: Next Steps

### 12.1 Immediate Next Steps

The immediate next steps involve building the "query" side of the application and the user interface:

1.  **Implement Context Retrieval Logic:** Create services and database queries (`SupabaseService` read methods) to perform filtering (by `user_id` and metadata) and implement the multi-method search approach (vector search, keyword search, metadata lookup). Implement re-ranking if desired.
2.  **Implement Calculation Tools:** Create the Python functions for required financial calculations, covering specific needs like variance analysis or ratio calculations.
3.  **Implement Answer Generation:** Create the service to interact with the answer LLM, manage context, handle tool calls (including extracting arguments from retrieved text), and generate the final answer, cleaning, and sources.
4.  **Develop API Layer (FastAPI):** Build endpoints for `/upload-document` (triggering `IngestionPipeline`) and `/ask-question` (triggering Retrieval and Generation). Implement authentication middleware and the streaming response mechanism for `/ask-question`.
5.  **Develop Frontend:** Create a user interface for login, upload, and querying, designed to handle and display streamed updates and answers.

### 12.2 Future Enhancements

*   Support for other file types (DOCX, XLSX).
*   OCR for scanned PDFs.
*   More sophisticated table extraction and financial statement recognition.
*   Advanced context retrieval techniques (e.g., graph-based methods leveraging document structure, query transformation).
*   Fine-tuning embedding or re-ranking models.
*   More robust error handling and logging.
*   User feedback mechanisms for continuous improvement.
*   Integration with calendars or other external data sources (with strict access controls).

---

## Chapter 13: Strategic Considerations and Future Vision

This chapter discusses the strategic landscape for AI applications, drawing insights from the "AI Founder's Bitter Lesson" and "Linguistic Imperialism" articles, and how they shape the long-term vision and defense strategy for the AI CFO Assistant.

### 13.1 Market Validation: The Office of the CFO Needs

Market analysis, such as insights from VC articles on the "Office of the CFO," strongly validates the core problem: the difficulty SMEs face in extracting insights from financial documents. Key pain points identified directly inform the value proposition and desired features:

*   Automating tasks within document-intensive workflows (e.g., processing reports).
*   Supporting strategic and analytical activities (e.g., FP&A, forecasting) by synthesizing data from disparate sources.
*   Addressing specific financial analysis needs (e.g., variance analysis, flux commentary, inputs for forecasting, multivariate analysis).
*   A clear need for reliable calculation capabilities for financial metrics.

This confirms that the focus on document processing, context retrieval, and tool-assisted generation for these specific financial tasks aligns with expressed market demand.

### 13.2 The "Bitter Lesson": Vertical vs. Horizontal AI Applications

The "Bitter Lesson" posits that general methods that leverage computation tend to outperform specific, hand-engineered solutions over time. Applied to AI products, this suggests that "vertical workflows" (like the AI CFO Assistant, specializing in a domain and using engineering to make current models work) may be vulnerable to powerful, general "horizontal agents" built by large labs as AI capabilities advance.

*   **Challenge:** As models become better at understanding documents, extracting information, and acting agentically, a general agent with file access could potentially replicate core functionalities of the AI CFO Assistant without needing the specific engineering steps (parsing, chunking, embedding, RAG) designed to work around current model limitations.
*   **Implication:** Reliance solely on the AI processing pipeline as a differentiator is risky in the long term. The value proposition must extend beyond being "AI that reads PDFs better."

### 13.3 Implications of Opaque AI Reasoning

As AI models become more autonomous through RL training, their internal reasoning ("Chain-of-Thought") may become less human-interpretable, residing in opaque "latent space." This raises concerns about auditing and understanding *why* an AI made a specific decision or calculation, especially in high-stakes environments.

*   **Relevance:** While less critical for the current, less autonomous pipeline, this is a significant concern if the system evolves towards more agentic financial tasks (e.g., initiating transactions, making complex recommendations).
*   **Validation of Design:** This reinforces the importance of the system's design decisions:
    *   Using **deterministic calculation tools** for mathematical operations ensures that numerical results are derived transparently and are fully auditable by human users, regardless of the LLM's internal process.
    *   Enforcing **grounded answers with source citations** provides a verifiable link between the AI's output and the original human-readable document text, offering a crucial layer of transparency and trust even if the AI's internal path to the answer is opaque.

### 13.4 Impact of Future Models

Should models reach a "GPT-5 level" capable of reasoning natively over entire document sets (large context window, inherent structure understanding), several components of the current architecture would likely become less critical or redundant:

*   **Reduced/Eliminated:** `ChunkingService`, `EmbeddingService`, `pgvector` for chunk search, external vector retrieval logic.
*   **Shifted Role:** `Sectioner` and `MetadataExtractor` might still be useful for providing structured input or filtering *before* sending to the large model, but their output wouldn't strictly be needed for managing context window limitations.
*   **Unchanged:** Supabase (DB, Storage, Auth, RLS), API Layer, Calculation Tools, Grounded Answer/Citation logic, Initial PDF-to-Text Conversion.

The core value would shift from data preparation for limited models to orchestrating interaction with highly capable models, ensuring security, reliability, and verifiability.

### 13.5 Defending Against General Agents

In a future where general agents can access files and replicate basic document AI capabilities, the AI CFO Assistant must defend its position by focusing on aspects where general agents are inherently weaker or less suitable for enterprise finance:

1.  **Trust and Security Moat:** The primary defense is the system's design as a **secure, multi-tenant platform for sensitive financial data**. This includes guaranteed data isolation (RLS), auditable access, and compliance focus – properties a generic agent accessing dispersed files cannot easily replicate. Trust in handling confidential financial information is paramount.
2.  **Reliability and Accuracy for Domain-Specific Tasks:** Demonstrating superior, validated accuracy for *specific financial analysis tasks* (parsing complex tables, calculating nuanced metrics, identifying specific data points) using deterministic tools and rigorous evaluation (Chapter 8) provides a critical advantage over a general agent's potentially less reliable output in a high-stakes domain.
3.  **Domain-Specific User Experience & Workflow Integration:** Tailoring the interface and functionality specifically to financial workflows (e.g., dedicated views for comparing balance sheets, integrated calculation interfaces) provides a more effective tool than a generic chat or command-line interface.
4.  **Regulatory and Compliance Readiness:** Building features necessary for financial compliance and auditability adds a layer of value beyond raw AI capability.

### 13.6 Evolution: Becoming Infrastructure

Rather than being replaced, the AI CFO Assistant could evolve to become a specialized piece of infrastructure used by general agents. This involves exposing its core capabilities as reliable, secure services:

*   **Secure Financial Document Access API:** Providing authorized access to user-specific documents and metadata, enforcing RLS at the API level.
*   **Structured Financial Data Extraction Service:** Offering an API to reliably extract structured data (tables, key figures, entities) from specified documents, providing clean inputs for agents.
*   **Domain-Specific Calculation Service:** Exposing deterministic financial calculations as callable functions that agents can invoke with specific inputs.
*   **Grounded Financial Retrieval Service:** Providing an API to retrieve relevant document sections, formatted with necessary source information for citation.

By offering these secure, reliable, domain-specific primitives, the AI CFO Assistant can become a valuable component in the future AI ecosystem, enabling general agents to interact with sensitive financial data and perform complex analyses accurately and verifiably, rather than attempting to replicate these complex, high-trust functions themselves. This leverages the system's strengths (security, reliability, domain expertise) in a way that complements the general capabilities of future AI.

---

## Appendix

### A. Example AI Prompts

*(Referenced prompts from `FinancialDocParser` and `MetadataExtractor` are included in their respective code files)*

### B. Database Setup SQL (`database_setup.sql`)

*(Contents of `scripts/database_setup.sql` as provided previously)*

### C. Storage Setup SQL (`storage_setup.sql`)

*(Contents of `scripts/storage_setup.sql` as provided previously)*

### D. Key Terms

*   **AI Model (LLM):** Large language model (e.g., Gemini).
*   **API:** Application Programming Interface.
*   **AST (Abstract Syntax Tree):** A structural representation of code; concept applied analogously to financial documents.
*   **Chunking:** Splitting text into smaller pieces (`chonkie`).
*   **Context Provider:** The role of the retrieval process, focused on finding relevant information for the LLM.
*   **Embedding:** Numerical vector representation of text meaning (via OpenAI).
*   **Function Calling / Tool Use:** LLM requesting execution of external code.
*   **Grounded Answer:** An answer derived solely from provided source material.
*   **Ingestion:** Processing and storing documents.
*   **Markdown:** Text formatting language.
*   **Metadata:** Data *about* the document (type, date, company, summary).
*   **Multi-tenancy:** Supporting multiple users with isolated data.
*   **`pgvector`:** PostgreSQL extension for vector storage and search.
*   **Pipeline:** The sequence of steps in a process (`IngestionPipeline`).
*   **Pydantic:** Python library for data validation and schema definition.
*   **RAG:** Retrieval-Augmented Generation.
*   **Reliability:** Core design goal focused on accuracy, trust, and verifiability.
*   **Retrieval:** Finding relevant information.
*   **RLS (Row-Level Security):** Database feature enforcing data access rules per user.
*   **Sectioning:** Dividing a document into logical parts based on headings.
*   **Semantic Search:** Searching based on meaning using embeddings.
*   **Service:** A modular code component with a specific responsibility.
*   **SSE (Server-Sent Events):** Protocol for streaming updates from server to browser.
*   **StreamingResponse:** FastAPI class for sending data incrementally via SSE.
*   **Structured Extraction:** Identifying and pulling out data into defined fields (like from tables or key figures).
*   **Supabase:** Backend-as-a-Service platform used for DB, Auth, Storage.
*   **Vector:** A list of numbers representing data (like text embeddings).
*   **Vertical Workflow:** An AI application specialized for a narrow domain using engineered steps.

---