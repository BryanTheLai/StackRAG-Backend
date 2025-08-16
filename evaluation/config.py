# evaluation/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- General Settings ---
# Detect if we're running from the evaluation directory or project root
current_dir = os.getcwd()
if current_dir.endswith("evaluation"):
    # Running from evaluation directory
    GOLDEN_DATASET_PATH = "golden_dataset.json"
    EVAL_RESULTS_PATH = "eval_results.csv"
else:
    # Running from project root
    GOLDEN_DATASET_PATH = "evaluation/golden_dataset.json"
    EVAL_RESULTS_PATH = "evaluation/eval_results.csv"

# --- Supabase Test User Credentials ---
# These are used to create an authenticated session for the eval run
TEST_USER_EMAIL = os.getenv("TEST_EMAIL")
TEST_USER_PASSWORD = os.getenv("TEST_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# --- LLM-as-a-Judge Settings ---
# Using LiteLLM, you can easily swap this to any other model
JUDGE_MODEL = "gemini/gemini-2.5-flash-lite"

# --- Evaluation Prompts ---
# Using f-strings for easy injection of variables
CONTEXT_PRECISION_PROMPT = """
You are evaluating a financial RAG system. Your task is to determine if the retrieved context contains information that could help answer the user's financial question.

User Question: "{question}"

Retrieved Context:
---
{retrieved_context}
---

Does the retrieved context contain relevant financial information that could help answer this question? Be lenient - even partial relevance counts.

Answer with only: YES or NO
"""

FAITHFULNESS_PROMPT = """
You are evaluating if an AI assistant stayed grounded in the provided context. Your task is to check if the answer uses information from the context without making up facts.

Retrieved Context:
---
{retrieved_context}
---

Generated Answer:
---
{generated_answer}
---

Does the answer stick to information available in the context? It's OK if the answer is incomplete, as long as what's there is grounded. Allow reasonable interpretations and calculations based on the context.

Answer with only: YES or NO
"""

ANSWER_CORRECTNESS_PROMPT = """
You are evaluating a financial AI assistant's response quality. Compare the generated answer against the ideal answer to see if it delivers the core message correctly.

User Question: "{question}"

What the answer should convey (Ideal Answer):
---
{ideal_answer}
---

What the AI actually answered:
---
{generated_answer}
---

Does the generated answer convey the same core financial information and message as the ideal answer? Focus on:
- Key financial figures (allowing for minor formatting differences)
- Main conclusions or insights
- Overall helpfulness to the user

Minor wording differences are fine. The goal is whether the user gets the right information.

Answer with only: YES or NO
"""

# --- Comprehensive LLM Judge Prompts for JSON Output ---

COMPREHENSIVE_EVALUATION_PROMPT = """
You are a financial evaluation expert. Analyze the AI system's performance across multiple dimensions and provide a comprehensive JSON evaluation.

User Question: "{question}"

Expected Answer:
---
{ideal_answer}
---

Generated Answer:
---
{generated_answer}
---

Retrieved Context (if available):
---
{retrieved_context}
---

Evaluate the system performance across these dimensions:

1. **Number Accuracy**: Are the numerical values (revenue, expenses, profits, etc.) extracted and reported correctly? Consider scaling (thousands vs actual amounts).

2. **Answer Correctness**: Does the answer provide the right information to address the user's question? Focus on core message delivery.

3. **Faithfulness**: Does the answer stick to information available in the retrieved context without hallucinating facts?

4. **RAG Success**: Did the system successfully retrieve relevant information and generate a coherent response?

For each metric, determine if it PASSES or FAILS based on these simple criteria:
- PASS: The system performs adequately for this dimension
- FAIL: The system has significant issues in this dimension

Be logical and not overly strict. If the user asks for revenue and the system shows revenue (even with minor formatting differences), that should PASS.

Respond with ONLY a JSON object in this exact format:
{{
  "number_accuracy": "PASS" or "FAIL",
  "answer_correctness": "PASS" or "FAIL", 
  "faithfulness": "PASS" or "FAIL",
  "rag_success": "PASS" or "FAIL",
  "explanation": "Brief explanation of the evaluation reasoning"
}}
"""
