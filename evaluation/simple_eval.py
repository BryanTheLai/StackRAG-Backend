#!/usr/bin/env python3
"""
Simple evaluation script that tests individual components without the agent orchestration.
This bypasses the Gemini model issues and focuses on the retrieval and evaluation metrics.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List

import pandas as pd
from litellm import completion
from supabase import create_client

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from evaluation.config import (
    GOLDEN_DATASET_PATH, EVAL_RESULTS_PATH, JUDGE_MODEL,
    CONTEXT_PRECISION_PROMPT, FAITHFULNESS_PROMPT, ANSWER_CORRECTNESS_PROMPT,
    TEST_USER_EMAIL, TEST_USER_PASSWORD, SUPABASE_URL, SUPABASE_KEY
)
from api.v1.dependencies import Session
from src.llm.tools.FunctionCaller import RetrievalService
from src.llm.OpenAIClient import OpenAIClient
from src.storage.SupabaseService import SupabaseService

async def get_test_session() -> Session:
    """Create authenticated session for testing."""
    auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    response = await asyncio.to_thread(
        auth_client.auth.sign_in_with_password,
        {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    if not response.session or not response.user:
        raise Exception("Authentication failed")
    
    return Session(
        user_id=response.user.id, 
        token=response.session.access_token
    )

def create_authenticated_client(session: Session):
    """Create authenticated Supabase client."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.options.headers["Authorization"] = f"Bearer {session.token}"
    return client

async def llm_judge(prompt: str, model: str = JUDGE_MODEL) -> str:
    """Call LLM judge for evaluation."""
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        
        content = response.choices[0].message.content.strip().upper()
        
        if "YES" in content:
            return "YES"
        elif "NO" in content:
            return "NO"
        else:
            return "UNKNOWN"
            
    except Exception as e:
        print(f"  ❌ Error in LLM Judge: {e}")
        return "ERROR"

def test_retrieval_only(question: str, session: Session, supabase_client) -> Dict[str, Any]:
    """Test only the retrieval component without the full RAG pipeline."""
    print(f"  🔍 Testing retrieval for: {question}")
    
    try:
        retrieval = RetrievalService(
            openai_client=OpenAIClient(),
            supabase_service=SupabaseService(supabase_client=supabase_client),
            user_id=session.user_id
        )
        
        # Test retrieval
        result = retrieval.retrieve_chunks(question, 5)
        
        # Parse the JSON result
        chunks_data = json.loads(result)
        
        # Create a mock answer based on the retrieved chunks
        if chunks_data:
            # Extract key financial data from chunks
            financial_data = []
            for chunk in chunks_data:
                chunk_text = chunk.get('chunk_text', '')
                if any(term in chunk_text.lower() for term in ['revenue', 'income', 'profit', 'expense']):
                    financial_data.append(chunk_text)
            
            if financial_data:
                mock_answer = f"Based on the retrieved documents: {financial_data[0][:200]}..."
            else:
                mock_answer = "Retrieved documents but no specific financial data found."
        else:
            mock_answer = "No relevant documents found."
        
        print(f"  ✅ Retrieved {len(chunks_data)} chunks")
        print(f"  📝 Mock answer: {mock_answer[:100]}...")
        
        return {
            "final_answer": mock_answer,
            "retrieved_context": result,
            "chunk_count": len(chunks_data),
            "response_length": len(mock_answer)
        }
        
    except Exception as e:
        print(f"  ❌ Retrieval error: {e}")
        return {
            "final_answer": f"ERROR: {str(e)}",
            "retrieved_context": "ERROR: Could not retrieve context",
            "chunk_count": 0,
            "response_length": 0
        }

async def run_simple_evaluation():
    """Run a simplified evaluation focusing on retrieval and metrics."""
    print("\n" + "="*60)
    print("🚀 STARTING SIMPLE EVALUATION RUN")
    print("="*60)
    
    # Setup
    session = await get_test_session()
    supabase_client = create_authenticated_client(session)
    print(f"✅ Authenticated as user: {session.user_id}")
    
    # Load dataset
    with open(GOLDEN_DATASET_PATH, 'r') as f:
        dataset = json.load(f)
    
    print(f"✅ Loaded {len(dataset)} test cases")
    
    results = []
    
    # Test each case
    for i, test_case in enumerate(dataset):
        print(f"\n{'='*40}")
        print(f"📋 Test {i+1}/{len(dataset)}: {test_case['test_id']}")
        print(f"❓ Question: {test_case['question']}")
        print(f"{'='*40}")
        
        # Test retrieval
        sut_output = test_retrieval_only(test_case['question'], session, supabase_client)
        
        generated_answer = sut_output['final_answer']
        retrieved_context = sut_output['retrieved_context']
        
        # Run evaluations
        print("  🔍 Running evaluations...")
        
        # Context Precision
        if "ERROR" not in retrieved_context:
            context_precision_prompt = CONTEXT_PRECISION_PROMPT.format(
                question=test_case['question'],
                retrieved_context=retrieved_context[:1000]  # Limit context length
            )
            context_precision = await llm_judge(context_precision_prompt)
        else:
            context_precision = "NO"
        
        # Faithfulness
        if "ERROR" not in retrieved_context and "ERROR" not in generated_answer:
            faithfulness_prompt = FAITHFULNESS_PROMPT.format(
                retrieved_context=retrieved_context[:1000],
                generated_answer=generated_answer
            )
            faithfulness = await llm_judge(faithfulness_prompt)
        else:
            faithfulness = "NO"
        
        # Answer Correctness
        correctness_prompt = ANSWER_CORRECTNESS_PROMPT.format(
            question=test_case['question'],
            ideal_answer=test_case['ideal_answer'],
            generated_answer=generated_answer
        )
        answer_correctness = await llm_judge(correctness_prompt)
        
        # Number Accuracy (simple check)
        import re
        def extract_numbers(text):
            return set(re.findall(r'[\$€£]?\d{1,3}(?:,\d{3})*(?:\.\d+)?%?', text))
        
        ideal_numbers = extract_numbers(test_case['ideal_answer'])
        generated_numbers = extract_numbers(generated_answer)
        
        if ideal_numbers and not generated_numbers:
            number_accuracy = "NO"
        elif not ideal_numbers:
            number_accuracy = "YES"
        else:
            missing = ideal_numbers - generated_numbers
            number_accuracy = "NO" if missing else "YES"
        
        print(f"  📊 Results:")
        print(f"    Context Precision: {context_precision}")
        print(f"    Faithfulness: {faithfulness}")
        print(f"    Answer Correctness: {answer_correctness}")
        print(f"    Number Accuracy: {number_accuracy}")
        
        # Store results
        result = {
            **test_case,
            "generated_answer": generated_answer,
            "retrieved_context": retrieved_context,
            "context_precision": context_precision,
            "faithfulness": faithfulness,
            "answer_correctness": answer_correctness,
            "number_accuracy": number_accuracy,
            "response_length": len(generated_answer),
            "context_length": len(retrieved_context)
        }
        
        results.append(result)
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(EVAL_RESULTS_PATH, index=False)
    print(f"\n💾 Results saved to: {EVAL_RESULTS_PATH}")
    
    # Quick summary
    metrics = ['context_precision', 'faithfulness', 'answer_correctness', 'number_accuracy']
    print(f"\n📊 Quick Summary:")
    for metric in metrics:
        yes_count = (results_df[metric] == 'YES').sum()
        total = len(results_df)
        print(f"  {metric}: {yes_count}/{total} ({(yes_count/total)*100:.1f}%)")
    
    print("\n🎉 Simple evaluation completed!")
    return results_df

if __name__ == "__main__":
    asyncio.run(run_simple_evaluation())
