# evaluation/data_loader.py
"""
Data loading utilities for evaluation.
"""
import json
from typing import List
from evaluator import TestCase
from config import GOLDEN_DATASET_PATH


def load_test_cases() -> List[TestCase]:
    """Load test cases from golden dataset."""
    print("📊 Loading test dataset...")
    
    with open(GOLDEN_DATASET_PATH, 'r') as f:
        dataset = json.load(f)
    
    # Validate and convert to TestCase objects
    test_cases = []
    required_fields = ['test_id', 'question', 'ideal_answer', 'tags']
    
    for item in dataset:
        # Validate required fields
        missing = [field for field in required_fields if field not in item]
        if missing:
            raise ValueError(f"Missing fields in {item.get('test_id', 'unknown')}: {missing}")
        
        test_case = TestCase(
            test_id=item['test_id'],
            question=item['question'],
            ideal_answer=item['ideal_answer'],
            tags=item['tags']
        )
        test_cases.append(test_case)
    
    print(f"✅ Loaded {len(test_cases)} test cases")
    
    # Show tag distribution
    all_tags = [tag for case in test_cases for tag in case.tags]
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    print(f"📋 Tag distribution: {dict(sorted(tag_counts.items()))}")
    
    return test_cases
