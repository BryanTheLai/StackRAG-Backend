# evaluation/evaluator.py
"""
Clean evaluation framework for RAG system performance testing.
"""
import asyncio
import json
import time
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from litellm import completion

from config import JUDGE_MODEL, COMPREHENSIVE_EVALUATION_PROMPT


@dataclass
class TestCase:
    """Single test case definition."""
    test_id: str
    question: str
    ideal_answer: str
    tags: List[str]


@dataclass
class EvaluationResult:
    """Evaluation result for a single test case."""
    test_id: str
    question: str
    ideal_answer: str
    generated_answer: str
    retrieved_context: str
    tags: List[str]
    
    # Performance metrics
    execution_time: float
    execution_success: bool
    execution_error: Optional[str]
    
    # Quality metrics (PASS/FAIL)
    number_accuracy: str
    answer_correctness: str
    faithfulness: str
    rag_success: str
    evaluation_explanation: str
    
    # Cost estimation
    estimated_tokens: int
    estimated_cost: float


class RAGEvaluator:
    """Main evaluation class for RAG system testing."""
    
    def __init__(self, session, supabase_client, delay_between_tests: float = 5.0):
        self.session = session
        self.supabase_client = supabase_client
        self.judge_model = JUDGE_MODEL
        self.delay_between_tests = delay_between_tests
    
    async def get_rag_response(self, question: str, max_retries: int = 3) -> Dict[str, Any]:
        """Get response from RAG system with context extraction and retry logic."""
        from src.llm.workflow.react_rag import run_react_rag
        
        for attempt in range(max_retries):
            start_time = time.time()
            
            try:
                final_answer = ""
                retrieved_context = ""
                
                # Stream response and extract context
                async for chunk in run_react_rag(self.session, self.supabase_client, question, []):
                    final_answer += chunk
                    
                    # Extract context from chunks (simplified)
                    if '"content":' in chunk and len(chunk) > 50:
                        retrieved_context += chunk + "\n"
                
                # Clean up context
                if retrieved_context:
                    # Extract actual content from JSON-like structures
                    content_matches = re.findall(r'"content":\s*"([^"]+)"', retrieved_context)
                    if content_matches:
                        retrieved_context = "\n".join(content_matches[:5])
                    else:
                        retrieved_context = retrieved_context[:1000]  # Limit size
                
                execution_time = time.time() - start_time
                
                return {
                    "answer": final_answer.strip(),
                    "context": retrieved_context or "No context extracted",
                    "success": True,
                    "execution_time": execution_time,
                    "error": None
                }
                
            except Exception as e:
                error_str = str(e)
                execution_time = time.time() - start_time
                
                # Check if it's a rate limit error
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10  # Exponential backoff: 10s, 20s, 30s
                        print(f"    ⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                
                return {
                    "answer": f"ERROR: {error_str}",
                    "context": "Error occurred during retrieval",
                    "success": False,
                    "execution_time": execution_time,
                    "error": error_str
                }
        
        # If all retries failed
        return {
            "answer": "ERROR: All retry attempts failed",
            "context": "Error occurred during retrieval",
            "success": False,
            "execution_time": 0.0,
            "error": "Maximum retries exceeded"
        }
    
    async def evaluate_with_llm(self, question: str, generated_answer: str, 
                               ideal_answer: str, retrieved_context: str) -> Dict[str, str]:
        """Evaluate response using LLM judge."""
        
        if "ERROR:" in generated_answer:
            return {
                "number_accuracy": "FAIL",
                "answer_correctness": "FAIL", 
                "faithfulness": "FAIL",
                "rag_success": "FAIL",
                "explanation": "System error prevented proper evaluation"
            }
        
        prompt = COMPREHENSIVE_EVALUATION_PROMPT.format(
            question=question,
            ideal_answer=ideal_answer,
            generated_answer=generated_answer,
            retrieved_context=retrieved_context
        )
        
        try:
            response = completion(
                model=self.judge_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response with better error handling
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Fallback parsing
                    result = {
                        "number_accuracy": "FAIL",
                        "answer_correctness": "FAIL",
                        "faithfulness": "FAIL",
                        "rag_success": "FAIL",
                        "explanation": f"JSON parsing failed. Raw response: {content[:200]}..."
                    }
            
            return {
                "number_accuracy": result.get("number_accuracy", "FAIL"),
                "answer_correctness": result.get("answer_correctness", "FAIL"),
                "faithfulness": result.get("faithfulness", "FAIL"), 
                "rag_success": result.get("rag_success", "FAIL"),
                "explanation": result.get("explanation", "No explanation provided")
            }
            
        except Exception as e:
            return {
                "number_accuracy": "FAIL",
                "answer_correctness": "FAIL",
                "faithfulness": "FAIL",
                "rag_success": "FAIL",
                "explanation": f"LLM evaluation failed: {str(e)}"
            }
    
    def estimate_cost(self, text: str) -> tuple[int, float]:
        """Estimate tokens and cost for given text."""
        tokens = int(len(text) / 3.5 * 1.1) if text else 0
        cost = (tokens / 1000) * 0.00125  # Gemini pricing
        return tokens, cost
    
    async def evaluate_test_case(self, test_case: TestCase, max_retries: int = 3) -> EvaluationResult:
        """Evaluate a single test case."""
        print(f"  Evaluating {test_case.test_id}: {test_case.question[:60]}...")
        
        # Get RAG response with retry logic
        response = await self.get_rag_response(test_case.question, max_retries)
        
        # Estimate cost
        tokens, cost = self.estimate_cost(response["answer"])
        
        # Evaluate with LLM judge
        evaluation = await self.evaluate_with_llm(
            test_case.question,
            response["answer"],
            test_case.ideal_answer,
            response["context"]
        )
        
        result = EvaluationResult(
            test_id=test_case.test_id,
            question=test_case.question,
            ideal_answer=test_case.ideal_answer,
            generated_answer=response["answer"],
            retrieved_context=response["context"],
            tags=test_case.tags,
            execution_time=response["execution_time"],
            execution_success=response["success"],
            execution_error=response["error"],
            number_accuracy=evaluation["number_accuracy"],
            answer_correctness=evaluation["answer_correctness"],
            faithfulness=evaluation["faithfulness"],
            rag_success=evaluation["rag_success"],
            evaluation_explanation=evaluation["explanation"],
            estimated_tokens=tokens,
            estimated_cost=cost
        )
        
        # Print quick status
        status = f"✓" if all(x == "PASS" for x in [
            evaluation["number_accuracy"],
            evaluation["answer_correctness"], 
            evaluation["faithfulness"],
            evaluation["rag_success"]
        ]) else "✗"
        
        print(f"    {status} Time: {response['execution_time']:.1f}s, Cost: ${cost:.4f}")
        
        return result
    
    async def run_evaluation(self, test_cases: List[TestCase], max_retries: int = 3) -> List[EvaluationResult]:
        """Run evaluation on all test cases."""
        results = []
        
        print(f"\n🚀 Starting evaluation of {len(test_cases)} test cases")
        print("=" * 60)
        
        for i, test_case in enumerate(test_cases):
            print(f"\n[{i+1}/{len(test_cases)}] {test_case.test_id}")
            
            try:
                result = await self.evaluate_test_case(test_case, max_retries)
                results.append(result)
                
            except Exception as e:
                print(f"    ERROR: {str(e)}")
                # Create error result
                error_result = EvaluationResult(
                    test_id=test_case.test_id,
                    question=test_case.question,
                    ideal_answer=test_case.ideal_answer,
                    generated_answer=f"SYSTEM_ERROR: {str(e)}",
                    retrieved_context="Error occurred",
                    tags=test_case.tags,
                    execution_time=0.0,
                    execution_success=False,
                    execution_error=str(e),
                    number_accuracy="FAIL",
                    answer_correctness="FAIL",
                    faithfulness="FAIL",
                    rag_success="FAIL",
                    evaluation_explanation=f"Test execution failed: {str(e)}",
                    estimated_tokens=0,
                    estimated_cost=0.0
                )
                results.append(error_result)
            
            # Rate limiting - wait between test cases to avoid API limits
            if i < len(test_cases) - 1:
                print(f"    ⏳ Waiting {self.delay_between_tests}s before next test...")
                await asyncio.sleep(self.delay_between_tests)
        
        print("\n" + "=" * 60)
        print("✅ Evaluation completed!")
        
        return results
