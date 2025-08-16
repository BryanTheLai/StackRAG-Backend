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
You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system. Your task is to determine if the provided context is relevant for answering the user's question.

User Question: "{question}"

Retrieved Context:
---
{retrieved_context}
---

Is the Retrieved Context relevant to the User Question?
Answer with only a single word: YES or NO.
"""

FAITHFULNESS_PROMPT = """
You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system. Your task is to determine if the generated answer is grounded in the provided context and does not introduce outside information (hallucinate).

Retrieved Context:
---
{retrieved_context}
---
Generated Answer:
---
{generated_answer}
---

Does the Generated Answer contain any information NOT present in the Retrieved Context?
Answer with only a single word: YES or NO.
"""

ANSWER_CORRECTNESS_PROMPT = """
You are an expert evaluator for a financial AI assistant. Your task is to determine if the Generated Answer is a correct and complete response to the User Question, based on the Ideal Answer.

User Question: "{question}"

Ideal Answer (Ground Truth):
---
{ideal_answer}
---
Generated Answer:
---
{generated_answer}
---

Is the Generated Answer functionally correct and complete compared to the Ideal Answer? Minor differences in phrasing are acceptable, but key facts and numbers must be accurate.
Answer with only a single word: YES or NO.
"""
