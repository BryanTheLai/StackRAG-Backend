Okay, let's streamline and update the technical reference guide to reflect the move to Supabase, incorporate multi-tenancy and authentication, and simplify the overall presentation.

Here's the revised documentation:

---

# AI CFO Assistant: Technical Reference Guide (Simplified)

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
    *   [2.2 Core Pipeline Diagram](#22-core-pipeline-diagram)
    *   [2.3 Component Roles](#23-component-roles)
    *   [2.4 Data Flow](#24-data-flow)
*   [Chapter 3: Data Ingestion](#chapter-3-data-ingestion)
    *   [3.1 Input: Financial PDFs](#31-input-financial-pdfs)
    *   [3.2 Parsing with AI](#32-parsing-with-ai)
    *   [3.3 Structuring Data](#33-structuring-data)
    *   [3.4 Breaking into Chunks](#34-breaking-into-chunks)
*   [Chapter 4: Embedding & Storage](#chapter-4-embedding--storage)
    *   [4.1 Embedding Strategy](#41-embedding-strategy)
    *   [4.2 Database: Supabase](#42-database-supabase)
    *   [4.3 Data Structure](#43-data-structure)
    *   [4.4 Efficient Search](#44-efficient-search)
    *   [4.5 Adding Data](#45-adding-data)
*   [Chapter 5: Retrieval Process](#chapter-5-retrieval-process)
    *   [5.1 How Retrieval Works](#51-how-retrieval-works)
    *   [5.2 Handling Complex Queries](#52-handling-complex-queries)
    *   [5.3 Identifying Key Details](#53-identifying-key-details)
    *   [5.4 Filtering by Details](#54-filtering-by-details)
    *   [5.5 Finding Similar Text](#55-finding-similar-text)
    *   [5.6 Refining Results](#56-refining-results)
    *   [5.7 Final Selection](#57-final-selection)
*   [Chapter 6: Answer Generation & Tools](#chapter-6-answer-generation--tools)
    *   [6.1 Choosing the AI Model](#61-choosing-the-ai-model)
    *   [6.2 Preparing Context](#62-preparing-context)
    *   [6.3 Guiding the AI](#63-guiding-the-ai)
    *   [6.4 Using Calculation Tools](#64-using-calculation-tools)
    *   [6.5 Managing Tool Use](#65-managing-tool-use)
*   [Chapter 7: Final Output & Sources](#chapter-7-final-output--sources)
    *   [7.1 Cleaning the Answer](#71-cleaning-the-answer)
    *   [7.2 Basic Checks](#72-basic-checks)
    *   [7.3 Showing Sources](#73-showing-sources)
*   [Chapter 8: Evaluation](#chapter-8-evaluation)
    *   [8.1 Why Evaluate?](#81-why-evaluate)
    *   [8.2 Test Data](#82-test-data)
    *   [8.3 Creating Test Cases](#83-creating-test-cases)
    *   [8.4 Measuring Performance](#84-measuring-performance)
    *   [8.5 Automation](#85-automation)
    *   [8.6 Improving with Evaluation](#86-improving-with-evaluation)
*   [Chapter 9: Building the System](#chapter-9-building-the-system)
    *   [9.1 Technology Summary](#91-technology-summary)
    *   [9.2 Key Libraries](#92-key-libraries)
    *   [9.3 Setup](#93-setup)
    *   [9.4 Configuration](#94-configuration)
    *   [9.5 Code Structure](#95-code-structure)
    *   [9.6 Version Control](#96-version-control)
*   [Chapter 10: Monitoring & Logs](#chapter-10-monitoring--logs)
    *   [10.1 Why Log?](#101-why-log)
    *   [10.2 Log Details](#102-log-details)
    *   [10.3 How Logging Works](#103-how-logging-works)
    *   [10.4 Using Logs](#104-using-logs)
*   [Chapter 11: Running the System](#chapter-11-running-the-system)
    *   [11.1 Demo Setup](#111-demo-setup)
    *   [11.2 Production Ideas](#112-production-ideas)
    *   [11.3 Handling More Users](#113-handling-more-users)
    *   [11.4 Managing Costs](#114-managing-costs)
*   [Chapter 12: Next Steps](#chapter-12-next-steps)
    *   [12.1 Based on Testing](#121-based-on-testing)
    *   [12.2 Adding Features](#122-adding-features)
    *   [12.3 User Experience](#123-user-experience)
*   [Appendix](#appendix)
    *   [A. Example Instructions for AI Models](#a-example-instructions-for-ai-models)
    *   [B. Database Structure (SQL)](#b-database-structure-sql)
    *   [C. Calculation Tool Instructions (JSON)](#c-calculation-tool-instructions-json)
    *   [D. Code Snippets (API Calls)](#d-code-snippets-api-calls)
    *   [E. Key Terms](#e-key-terms)

---

---

# Chapter 1: Introduction

## 1.1 Project Overview

This guide explains how the **AI CFO Assistant** works. It's a project to help Small and Medium Businesses (SMEs) get clear, reliable answers from their financial documents. The system uses modern AI, specifically a method called RAG (Retrieval-Augmented Generation) along with AI models that can use external tools, to answer questions based *only* on the documents you provide.

## 1.2 The Problem: Financial Insight Bottleneck

Getting useful insights from financial reports is hard for many SMEs. Reports are often PDFs, difficult to search, scattered across different files, and require financial know-how to fully understand. This means valuable information is locked away.

## 1.3 The Solution: AI CFO Assistant

The Assistant acts as a smart interface for your financial reports. You upload your documents, and you can ask questions in simple English. The system then finds the right information, does any needed calculations, and gives you a direct answer, showing you exactly where it got the information.

*   **Understand:** Figures out what your question means.
*   **Find:** Pulls relevant parts from your uploaded documents.
*   **Calculate:** Uses trusted tools for math.
*   **Answer:** Creates a clear response using *only* the found information.
*   **Show Sources:** Tells you which document sections were used.

## 1.4 Core Design Goal: Reliability

Financial data is sensitive, so being right is crucial. The main goal is **Reliability**. We avoid AI making things up (hallucinations) by focusing on:

1.  **Correct Numbers:** Figures are accurate, either directly from documents or calculated correctly by tools.
2.  **Grounded Answers:** The answer comes *only* from the documents you provided, not from outside knowledge.
3.  **Clear Sources:** You can see exactly which parts of which documents support the answer.

## 1.5 Key Objectives

*   Process complex financial PDFs accurately.
*   Build a smart system that finds the right document sections.
*   Use tools reliably for calculations via the AI.
*   Make sure the AI only uses provided document context.
*   Create a way to automatically test how reliable the system is.
*   Build a basic working version.
*   **New:** Add user accounts and keep each user's data separate (multi-tenancy).

## 1.6 Scope

**What's Included:**

*   Handling standard PDF financial reports (Income, Balance, Cash Flow).
*   Extracting text and tables using advanced AI.
*   Turning extracted info into structured text (Markdown + metadata).
*   Breaking down text into smart sections (chunks).
*   Creating searchable data representations (embeddings).
*   Storing and searching data in a database.
*   Filtering results using document details (metadata).
*   Refining search results with a re-ranker.
*   Breaking down complex questions if needed.
*   Generating answers using a capable AI model.
*   Using tools for calculations (sum, average, ratio, percent change).
*   Ensuring the AI stays grounded and refuses if info is missing.
*   Showing where the information came from.
*   Building automated reliability tests.
*   Recording system activity (logging).
*   Creating simple ways to interact (like a web page or command line).
*   **New:** Handling user accounts and keeping data separate for each user/organization.

**What's Not Included (Initially):**

*   Non-financial documents (legal, etc.).
*   Scanned PDFs that need advanced image processing.
*   Perfectly extracting *all* complex table details if the AI struggles.
*   Connecting directly to live accounting systems.
*   Providing financial advice or forecasts.
*   Fancy data charts or visuals.
*   Advanced security beyond user accounts and data separation.
*   A full, polished app interface.
*   Training the AI models ourselves (using existing ones via API).
*   Advanced search features (like combined keyword/vector search).
*   Spreadsheet files (.xlsx, .csv).

## 1.7 Technology Overview

*   **Main Code:** Python.
*   **AI Models (LLMs):** Accessed through APIs (like Google Gemini) for parsing, understanding questions, and generating answers with tool use.
*   **Embedding Model:** An API for creating searchable numerical representations of text (like Nomic via Fireworks AI).
*   **Database & Backend:** **Supabase**. This gives us a PostgreSQL database for structured data and vector search (`pgvector`), plus built-in user accounts (Auth) and file storage (Storage).
*   **Re-ranker:** A smaller AI model for refining search results, often run using a Python library locally or on cloud compute.
*   **Key Python Libraries:** Tools for interacting with APIs, the database (Supabase client), handling text, managing settings, and running evaluations.
*   **Interface (Optional):** Simple demo using libraries like Streamlit or just command-line scripts.
*   **Evaluation:** Custom Python code to run tests using pre-set questions and expected answers.

## 1.8 Document Purpose

This document is a technical guide for the AI CFO Assistant project. It explains the design, how things work, and why certain choices were made. It's for developers, evaluators, and anyone wanting to understand the technology behind it.

---

# Chapter 2: System Architecture

## 2.1 Architecture Design

The system is built around **RAG (Retrieval-Augmented Generation)** and **Function Calling**. RAG finds relevant info first, so the AI doesn't guess. Function Calling lets the AI use external tools (our Python code) for precise tasks like calculations.

This setup makes the system reliable by grounding the AI in your data and handling math accurately. It's also modular, meaning we can update parts (like switching AI models) without rebuilding everything.

**New:** The system also includes user **Authentication** and manages data to ensure one user's documents and questions are kept separate from another's (**Multi-tenancy**). This is built using Supabase's features.

## 2.2 Core Pipeline Diagram

## 2.3 Component Roles

*   **1. PDF Parser (AI Model):** Reads PDF content, including tables and layout, using a capable AI model (like Gemini Vision).
*   **2. Format (Markdown+Metadata):** Converts parser output into a structured text format (Markdown) and pulls out key document details (metadata) like report type, date, and *user/organization ID*.
*   **3. Break into Sections:** Splits the formatted text into smaller, logical chunks based on headings. Handles very large sections by splitting them further.
*   **4. Create Embeddings:** Turns text chunks into numerical vectors using an Embedding AI model. Adds metadata text to the chunk before embedding for better search.
*   **5. Save Data & Vectors (Supabase Postgres):** Stores all processed data (original text, metadata, embeddings) in the Supabase PostgreSQL database, ensuring each piece of data is linked to the **user/organization ID**.
*   **6. User Authentication + Get User ID:** Confirms the user's identity and retrieves their unique ID or their organization's ID using Supabase Auth. This ID is crucial for ensuring data privacy in multi-tenancy.
*   **7. Breakdown Query?:** Uses a smaller AI to check if the user's question needs to be broken into simpler steps (like comparing two periods).
*   **8. Identify Filters:** Looks at the question (and the user ID) to find details like dates, report types, and the required user/organization ID that can filter the data search.
*   **9. Filter Data (in DB):** Uses the identified filters, **including the user/organization ID**, to query the database and narrow down potential relevant sections.
*   **10. Find Similar Text:** Performs a vector search in the database (within the filtered data) to find text chunks semantically similar to the user's question.
*   **11. Map to Full Sections:** Groups the search results back to their original, larger sections.
*   **12. Re-rank Relevance:** Uses a specific model (cross-encoder) to re-score the relevance of the candidate full sections, picking the best ones.
*   **13. Assemble Context:** Gathers the text and metadata of the top re-ranked sections to create the input text for the main Answer AI.
*   **14. Answer AI + Tool Use:** The main AI model (like Gemini 1.5 Pro) reads the context, understands the question, generates a natural language answer, and, importantly, asks to use calculation tools when needed. It uses tool instructions (Appendix C) to know how.
*   **15. Calculation Tools:** Reliable Python functions that perform specific calculations (like ratios, sums) when the Answer AI requests them. They return results back to the AI.
*   **16. Clean & Check:** Tidies up the AI's raw answer and runs basic checks (like confirming numbers appear in the source text).
*   **17. Generate Sources:** Creates clear citations showing which document sections were used to answer the question.
*   **Logging (Supabase Logs Table):** Records details of the query process (input, retrieved sections, AI interaction, tool use, output) in a dedicated database table for review and debugging, **linked to the user ID**.

## 2.4 Data Flow

*   **Adding a Document:** User logs in -> Document is processed (Parsed, Formatted, Chunked, Embedded) -> Data (text, metadata, embeddings) is saved in Supabase, *tagged with the user's/organization's ID*.
*   **Asking a Question:** User logs in -> Question comes in with user credentials -> User ID is verified -> Question is analyzed and filters (including User ID) are found -> Database is queried, filtering *only* for the user's data -> Relevant sections are retrieved, re-ranked, and assembled -> Answer AI generates response using the context and tools -> Answer is cleaned and sources are added -> Result shown to user -> Process details are logged *with the User ID*.

---

# Chapter 3: Data Ingestion

## 3.1 Input: Financial PDFs

The system starts with financial reports like Income Statements, Balance Sheets, and Cash Flow statements, usually in PDF format. These can look very different and contain tricky layouts, especially tables. We handle these variations as part of the process.

## 3.2 Parsing with AI

To read these complex PDFs, we use a powerful AI model (like Gemini Vision) that can understand both text and visual layout. We give the AI the PDF and tell it exactly what we want back: all the text, organized by headings, with tables clearly marked, and important document details pulled out.

*   We interact with this AI via its API.
*   Prompts (our instructions to the AI) are key to getting good results.
*   We handle potential API errors or usage limits.

## 3.3 Structuring Data

The AI's output needs to be consistent. We convert it into **Markdown** format. At the top of each Markdown file, we add key document details (like report type, dates, and importantly, the **User ID / Organization ID** it belongs to) in a structured format called **YAML Front Matter**. This makes it easy to identify and filter documents later.

## 3.4 Breaking into Chunks

Large documents are broken into smaller, meaningful pieces called chunks. We split the Markdown primarily based on headings (like `# Revenue` or `## Operating Expenses`) because these usually mark logical sections. If a section is still too big for the Embedding AI, we split it further, ensuring we keep track of which larger section each small chunk came from.

---

# Chapter 4: Embedding & Storage

After breaking documents into chunks and adding metadata, we turn them into a format computers can easily search by meaning: vector embeddings. We store these embeddings and the original text in our database.

## 4.1 Embedding Strategy

A simple text-to-vector conversion isn't enough because the same words can mean different things in different contexts (e.g., "Revenue" from Q1 2023 vs Q1 2024). To add context, we add important details like the report type and date (from the YAML metadata) to the chunk's text *before* creating the embedding. This helps the vector capture the context, making search more accurate.

*   We use a high-quality Embedding AI model for this, accessed via an API.
*   Adding metadata helps distinguish similar text from different documents or periods.
*   We send multiple chunks at once to the API (batching) for speed.

## 4.2 Database: Supabase

We use **Supabase** as our backend. It's a platform that provides a hosted PostgreSQL database.

*   **Why Supabase?** It offers a powerful PostgreSQL database with the `pgvector` extension for vector search, plus built-in features like User Authentication and File Storage, simplifying development. It scales well and is easy to use.
*   **`pgvector`:** This extension lets us store vector embeddings directly in our PostgreSQL database and run very fast "find similar vector" searches.

## 4.3 Data Structure

Our database (Supabase Postgres) has tables to hold everything:

*   `documents`: Info about the original PDF file, including its **user/organization ID**.
*   `sections`: The larger logical sections (from headings), their text, metadata, and **user/organization ID**.
*   `embeddings`: The smaller text chunks, their vector embeddings, a link back to their `section_id`, and the **user/organization ID**.
*   `query_logs`: Records of user queries, retrieval steps, and AI responses, linked to the **user ID**.

**Key for Multi-tenancy:** Every table storing user-specific data *must* include a `user_id` or `organization_id` column. Database policies (Row-Level Security in Postgres) can then enforce that users only see and query their own data.

*(See Appendix B for SQL table details)*

## 4.4 Efficient Search

To make retrieval fast, we use database indexes:

*   **Vector Index:** An index (`hnsw` type) on the embedding vectors allows quick similarity searches (`pgvector`).
*   **Metadata Index:** An index on the metadata (JSONB) allows fast filtering by report type, date, or **user/organization ID**.
*   **Standard Indexes:** Indexes on IDs and foreign keys speed up linking data between tables.

## 4.5 Adding Data

A process manages saving data to the database after parsing, chunking, and embedding. This ensures that all pieces of a document's data are saved correctly and linked to the correct **user/organization ID**. Transactions are used to ensure everything for one document saves or fails together.

---

# Chapter 5: Retrieval Process

The goal of retrieval is to find the best document sections needed to answer the user's question, making sure to only look at the data that belongs to the current **user/organization**.

## 5.1 How Retrieval Works

It's a multi-step process:

1.  Understand the query (possibly break it down).
2.  Identify filters (especially the **user/organization ID**).
3.  Filter the database using metadata.
4.  Search for similar text vectors within the filtered data.
5.  Refine the list of results.

## 5.2 Handling Complex Queries

Some questions ("Compare revenue Q1 vs Q2") need multiple data points. A small AI model can break these down into simpler lookup steps ("Find revenue Q1", "Find revenue Q2"). The system then processes each simple step.

## 5.3 Identifying Key Details

Before searching the database, we analyze the query (and use the authenticated user's ID) to pull out important details like specific dates, report types, and keywords.

## 5.4 Filtering by Details

We use the extracted details, **especially the user/organization ID**, to build a database query. This ensures we only search within the correct user's data from the right documents or time periods. This filtering happens *before* the more complex vector search.

## 5.5 Finding Similar Text

We turn the user's query into a vector embedding. Then, we search the database (using `pgvector`) *within the results of the metadata filter* to find the text chunks whose embeddings are most similar to the query's embedding. We get a list of the top matching chunks.

## 5.6 Refining Results

Vector search is good, but a separate model (a cross-encoder) can do a more detailed comparison of the query against the full text of the candidate sections found. This re-ranks the results to put the most relevant sections at the very top.

## 5.7 Final Selection

From the re-ranked list, we pick the top few sections to send to the Answer AI. The number depends on how much text the AI model can handle at once.

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

## 6.3 Guiding the AI

Prompting (giving instructions to the AI) is critical for reliability:

*   **Be Clear:** Instructions must be simple and direct ("MUST", "MUST NOT").
*   **Set the Role:** Tell the AI it's a helpful, factual financial assistant.
*   **Stay Grounded:** The MOST important rule is to *only* use the provided document text.
*   **Refuse Gracefully:** Tell it exactly what to say if the answer is *not* in the documents.
*   **Cite Sources:** Instruct it to add citations after facts.
*   **Use Tools:** Tell it when and how to use the calculation tools.
*   **Show Examples:** Include a few examples of good answers, refusals, and tool use to demonstrate expected behavior.

## 6.4 Using Calculation Tools

For accuracy, calculations are handled by our own Python code, not the AI's internal (sometimes unreliable) math skills.

*   We define simple functions for needed calculations (like summing numbers, finding ratios).
*   These functions handle errors (like dividing by zero).
*   We create structured descriptions (schemas) for these tools so the AI knows they exist and how to use them.

## 6.5 Managing Tool Use

The system controls the conversation with the AI:

1.  Send the prompt, context, and tool descriptions.
2.  The AI might respond with a request to use a tool (e.g., "Call `calculate_ratio` with X and Y").
3.  The system runs the specified Python function with the arguments the AI provided.
4.  The system sends the function's result (the calculated number) back to the AI.
5.  The AI reads the result and generates the final answer incorporating the calculation.

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
*   These citations are added to the final answer.

---

# Chapter 8: Evaluation

## 8.1 Why Evaluate?

Because reliability is key, we don't just hope it works; we **prove it works** using objective testing. Evaluation helps us measure performance, find problems, see if changes improve things, and show how reliable the system is.

## 8.2 Test Data

We test using financial PDF documents that we create ourselves (synthetic data). This gives us control and ensures we know the correct answers. We generate reports across different periods and types.

## 8.3 Creating Test Cases

We create a dataset of questions and their *correct* answers (Golden Dataset). Each test case includes:

*   The question.
*   The perfect, accurate answer.
*   The exact document sections that contain the answer (ground truth).
*   Any numbers involved.
*   Whether the question should *not* be answerable (requiring a refusal).

A key part of this dataset is including cases where the correct response is to refuse because the information isn't available.

## 8.4 Measuring Performance

We measure several things automatically:

*   **Number Accuracy:** Are the numbers in the answer correct compared to our ground truth?
*   **Faithfulness:** Does the answer *only* use information from the provided document sections? (We use another AI model to check this).
*   **Source Accuracy:** Do the provided citations point to the correct source sections?
*   **Finding Performance:** How well did the system find the relevant sections in the first place?
*   **Refusal Accuracy:** Did it correctly refuse to answer when it should have?

## 8.5 Automation

We use an automated script to run all the test cases against the system and calculate these metrics. This lets us quickly see how changes affect performance.

## 8.6 Improving with Evaluation

Testing isn't just the end; it's part of development. We:

1.  Run tests to see where the system is weak.
2.  Make targeted changes (e.g., improve prompts, adjust retrieval settings).
3.  Run tests again to see if it improved (and didn't break anything else).
4.  Keep track of results to show progress.

---

# Chapter 9: Building the System

## 9.1 Technology Summary

*   **Code:** Python.
*   **AI APIs:** For parsing, embedding, asking questions, and using tools (e.g., Google Gemini, Fireworks AI).
*   **Database & Backend:** **Supabase** (Postgres with `pgvector`, Auth, Storage).
*   **Refining Search:** A Python library (like `sentence-transformers`).
*   **Settings:** YAML files.
*   **Secrets:** Environment variables (`.env`).

## 9.2 Key Libraries

We use Python libraries for:

*   Talking to Supabase (`supabase-py`).
*   Interacting with AI APIs.
*   Handling text and embeddings (`sentence-transformers`).
*   Loading settings (`PyYAML`, `python-dotenv`).
*   Basic file handling.
*   Logging.
*   Building simple interfaces (like Streamlit).

## 9.3 Setup

*   Use a virtual environment for Python libraries.
*   Keep sensitive details (API keys, database passwords) in a `.env` file that is *not* saved in code version control.
*   Load `.env` variables when the system starts.

## 9.4 Configuration

We use configuration files (like `config.yaml`) to easily change settings without changing code. This includes:

*   Which AI models to use.
*   Search settings (how many results to get).
*   File paths.
*   Prompts (or paths to prompt files).
*   **New:** Supabase connection details (from `.env`).

## 9.5 Code Structure

We organize the code into logical parts (modules) in a `src` folder:

*   `src/parsing.py`: Handles reading PDFs and formatting.
*   `src/chunking.py`: Breaks text into sections.
*   `src/embedding.py`: Creates vectors.
*   `src/storage.py`: Interacts with the database (Supabase).
*   `src/retrieval.py`: Manages finding relevant sections.
*   `src/generation.py`: Handles asking the AI and using tools.
*   `src/tools.py`: The calculation functions.
*   `src/evaluation.py`: Runs tests.
*   `src/postprocessing.py`: Cleans answers and adds sources.
*   **New:** Add components for handling user authentication and passing the user context through the pipeline.

This structure makes the code easier to understand, test, and maintain.

## 9.6 Version Control

We use Git (and GitHub) to track changes, work on features safely, and keep a history of the code. We make sure secrets are ignored.

---

# Chapter 10: Monitoring & Logs

## 10.1 Why Log?

Logs are records of what the system did. They are essential for:

*   Finding out why something went wrong (debugging).
*   Seeing which parts are slow (performance).
*   Getting data for evaluation.
*   Understanding how users are using the system.
*   Tracking costs (API usage).

## 10.2 Log Details

We save detailed information about each user question (query) processed. This includes:

*   The original question.
*   **New:** The **User ID**.
*   Which filters were used.
*   Which sections were found, re-ranked, and actually used by the AI.
*   The exact prompt sent to the Answer AI.
*   The raw response from the AI.
*   Details about any tool calls (what the AI asked for, what the tool returned).
*   The final answer and sources shown to the user.
*   Success or failure status and any error messages.
*   How long each step took.
*   Estimated cost (based on AI tokens used).

This information is stored in a dedicated table in Supabase (like `query_logs`).

## 10.3 How Logging Works

We use Python's built-in logging system, configured to save these detailed records to the Supabase database table.

## 10.4 Using Logs

We can look at the logs to:

*   Trace exactly what happened for a specific user's question.
*   Analyze performance trends over time.
*   Figure out API costs.
*   Provide data for automated evaluation scripts.

---

# Chapter 11: Running the System

## 11.1 Demo Setup

For the project demonstration, we can run the system locally or on a simple cloud setup.

*   **CLI:** Run scripts from the command line (good for testing).
*   **Streamlit:** A simple web page interface (good for showing how it works).
*   **Docker:** Packaging the app in a container ensures it runs the same everywhere and makes deployment easier.

Supabase provides managed services for the database, auth, and storage, which simplifies things greatly compared to managing them yourself.

## 11.2 Production Ideas

For a real-world version:

*   Use a more robust web framework (like FastAPI) to build an API backend.
*   Deploy to a cloud platform (AWS, GCP, Azure) using managed services or containers for scalability.
*   Use Supabase's managed services for the database, auth, and storage.

## 11.3 Handling More Users

*   **Database:** Supabase handles database scaling, but indexing (especially with the **user/organization ID**) is crucial for performance as data grows.
*   **APIs:** AI API rate limits can be a bottleneck. We need retry logic and maybe queues.
*   **Application Code:** The part of the system that runs the RAG pipeline needs to be able to handle many requests at once (concurrency), possibly by running multiple copies (scaling instances) if using a framework like FastAPI.

## 11.4 Managing Costs

AI API costs can be high. We track token usage via logs. We can optimize by:

*   Choosing cost-effective AI models where possible.
*   Making prompts concise.
*   Batching API calls.
*   Monitoring Supabase usage.

---

# Chapter 12: Next Steps

The project provides a solid base. Here are ideas for making it better:

## 12.1 Based on Testing

The evaluation results tell us where to focus:

*   If finding the right info is hard, we could fine-tune the Embedding or Re-ranker models on financial data.
*    If the AI isn't following instructions or refuses wrongly, we could fine-tune a smaller Answer AI model specifically for our task and maybe run it on a fast platform like Groq.

## 12.2 Adding Features

*   Handle scanned PDFs using OCR (converting images of text to text).
*   Improve table extraction for even more complex tables.
*   Allow asking questions that compare data across many different documents or years.
*   Connect to live accounting software APIs (like QuickBooks).
*   Add more specific calculation tools.
*   Handle other types of business documents (contracts, etc.).

## 12.3 User Experience

*   Build a nicer, professional web interface.
*   Add ways for users to give feedback on answers.
*   Add charts and graphs to visualize financial data.

---

# Appendix

## A. Example Instructions for AI Models

These are simplified examples of the text we send to the AI models to guide their behavior.

**A.1 AI Parser Instructions (for Gemini Vision):**

```text
SYSTEM: You are a tool to extract structured text from financial PDF reports.
Read the PDF page by page.
Output the content as Markdown.
Use headings (#, ##) for sections.
Use Markdown format for tables.
Extract these details and put them at the very top in YAML:
report_type (Income Statement, Balance Sheet, Cash Flow)
company_name
period_end_date (YYYY-MM-DD)
fiscal_year
currency
---
[PDF Content is provided here]
```

**A.2 Query Breakdown Instructions (for a small AI):**

```text
SYSTEM: Analyze this financial question.
If it needs multiple steps or data points to answer, list the simple lookup steps needed.
If it's simple, just give the original question back.
Respond ONLY in JSON: {"needs_decomposition": true/false, "sub_queries": [...] or "original_query": "..."}
---
User Query: [User's question]
```

**A.3 Answer AI Instructions (for Gemini 1.5 Pro):**

```text
SYSTEM: You are a reliable AI Financial Assistant.
ONLY use the text in the [CONTEXT SECTIONS].
DO NOT use outside knowledge.
If the answer is NOT in [CONTEXT SECTIONS], say "The provided documents do not contain sufficient information to answer this question." EXACTLY.
Use the [AVAILABLE TOOLS] for calculations.
Cite your sources: add "[{Source Filename}, Section: '{Section Heading}']" after each fact/number from the context.
---
AVAILABLE TOOLS:
[Tool schemas - like Appendix C JSON]
---
[CONTEXT SECTIONS]:
### SECTION 1 ###
Metadata: {source_filename: ..., section_heading: ...}
Text: [Full text of retrieved section 1]
### SECTION 2 ###
...
---
USER QUERY: [User's question]
---
Your Answer:
```

**A.4 Evaluation AI Instructions (for a judge AI):**

```text
SYSTEM: Evaluate if an AI's answer is based ONLY on provided text.
---
PROVIDED TEXT:
[Full text of all sections given to the Answer AI]
---
AI ANSWER:
[The final answer the system produced]
---
QUESTION: Is *every* fact/number in the AI ANSWER directly supported by the PROVIDED TEXT? Answer ONLY 'Yes' or 'No'.
```

## E. Key Terms

*   **AI CFO Assistant:** The system that answers financial questions from documents.
*   **AI Model (LLM):** Large language model like Gemini, used for understanding text, generating answers, and using tools.
*   **API:** Way software talks to other software (like our code talking to AI models or Supabase).
*   **Attribution:** Showing the original document sections used for an answer.
*   **Chunking:** Breaking documents into smaller text pieces.
*   **Context Window:** How much text an AI model can read at once.
*   **Cross-Encoder:** A model that re-ranks search results for better accuracy.
*   **Embedding:** A number list (vector) that represents text meaning.
*   **Faithfulness:** An answer only using the provided documents, not guessing.
*   **Function Calling (Tool Use):** When an AI asks to run external code (our tools) for tasks like calculations.
*   **Golden Dataset:** Test questions with known correct answers and sources.
*   **Graceful Refusal:** The system saying it cannot answer because the info isn't in the documents.
*   **Ingestion:** The process of reading, processing, and saving a document.
*   **Logging:** Recording system activity for debugging and analysis.
*   **Markdown:** Simple text formatting.
*   **Metadata:** Details about documents or sections (like date, type, heading).
*   **Multi-tenancy:** Designing the system so data for different users/organizations is kept separate and secure.
*   **`pgvector`:** A feature for PostgreSQL databases to store and search vector embeddings.
*   **Prompt Engineering:** Writing clear instructions for the AI.
*   **RAG (Retrieval-Augmented Generation):** Finding relevant info (Retrieval) before asking the AI to generate an answer (Generation) using that info.
*   **Re-ranking:** Sorting search results to put the most relevant first.
*   **Retrieval:** The process of finding relevant document sections.
*   **Row-Level Security (RLS):** A database feature (in Postgres/Supabase) to control which rows users can access based on their identity, crucial for multi-tenancy.
*   **Semantic Search:** Searching based on meaning, not just keywords (using embeddings).
*   **SME:** Small or Medium Enterprise.
*   **Supabase:** Our chosen backend platform providing managed Postgres (`pgvector`), User Authentication, and File Storage.
*   **Synthetic Data:** Test data we create ourselves.
*   **Tool:** A specific function (like a calculation) that the AI can ask the system to perform.
*   **User Authentication (Auth):** Verifying who the user is.
*   **Vector Database:** A database good at storing and searching vector embeddings.
*   **YAML:** A format for structured data used in document metadata.

---