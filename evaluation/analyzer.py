# evaluation/analyzer.py
"""
Analysis and visualization tools for evaluation results.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any
from evaluator import EvaluationResult


class ResultAnalyzer:
    """Analyze and visualize evaluation results."""
    
    def __init__(self, results: List[EvaluationResult]):
        self.results = results
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame for analysis."""
        data = []
        for result in self.results:
            data.append({
                'test_id': result.test_id,
                'question': result.question,
                'generated_answer': result.generated_answer,
                'tags': ','.join(result.tags),
                'execution_time': result.execution_time,
                'execution_success': result.execution_success,
                'number_accuracy': result.number_accuracy,
                'answer_correctness': result.answer_correctness,
                'faithfulness': result.faithfulness,
                'rag_success': result.rag_success,
                'estimated_cost': result.estimated_cost,
                'evaluation_explanation': result.evaluation_explanation
            })
        return pd.DataFrame(data)
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate core performance metrics."""
        df = self.df
        
        metrics = {
            'total_tests': len(df),
            'execution_success_rate': (df['execution_success'] == True).mean() * 100,
            'number_accuracy': (df['number_accuracy'] == 'PASS').mean() * 100,
            'answer_correctness': (df['answer_correctness'] == 'PASS').mean() * 100,
            'faithfulness': (df['faithfulness'] == 'PASS').mean() * 100,
            'rag_success': (df['rag_success'] == 'PASS').mean() * 100,
            'avg_execution_time': df['execution_time'].mean(),
            'total_cost': df['estimated_cost'].sum(),
            'avg_cost': df['estimated_cost'].mean()
        }
        
        # Overall score (average of 4 quality metrics)
        metrics['overall_score'] = (
            metrics['number_accuracy'] + 
            metrics['answer_correctness'] + 
            metrics['faithfulness'] + 
            metrics['rag_success']
        ) / 4
        
        return metrics
    
    def analyze_by_tags(self) -> Dict[str, float]:
        """Analyze performance by test tags."""
        tag_performance = {}
        
        for _, row in self.df.iterrows():
            tags = row['tags'].split(',') if row['tags'] else []
            is_correct = row['answer_correctness'] == 'PASS'
            
            for tag in tags:
                tag = tag.strip()
                if tag not in tag_performance:
                    tag_performance[tag] = []
                tag_performance[tag].append(is_correct)
        
        # Calculate success rates
        tag_scores = {}
        for tag, results in tag_performance.items():
            if results:  # Only if we have data
                tag_scores[tag] = sum(results) / len(results) * 100
        
        return tag_scores
    
    def identify_failures(self) -> List[Dict[str, Any]]:
        """Identify and categorize test failures."""
        failures = []
        
        for _, row in self.df.iterrows():
            failed_metrics = []
            
            if row['number_accuracy'] == 'FAIL':
                failed_metrics.append('Number Accuracy')
            if row['answer_correctness'] == 'FAIL':
                failed_metrics.append('Answer Correctness')
            if row['faithfulness'] == 'FAIL':
                failed_metrics.append('Faithfulness')
            if row['rag_success'] == 'FAIL':
                failed_metrics.append('RAG Success')
            
            if failed_metrics:
                failures.append({
                    'test_id': row['test_id'],
                    'failed_metrics': failed_metrics,
                    'question': row['question'][:80] + '...',
                    'explanation': row['evaluation_explanation']
                })
        
        return failures
    
    def create_visualizations(self):
        """Create comprehensive result visualizations."""
        metrics = self.calculate_metrics()
        tag_scores = self.analyze_by_tags()
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('RAG System Evaluation Results', fontsize=16, fontweight='bold')
        
        # 1. Core metrics bar chart
        ax1 = axes[0, 0]
        metric_names = ['Number\nAccuracy', 'Answer\nCorrectness', 'Faithfulness', 'RAG\nSuccess']
        scores = [
            metrics['number_accuracy'],
            metrics['answer_correctness'], 
            metrics['faithfulness'],
            metrics['rag_success']
        ]
        
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
        bars = ax1.bar(metric_names, scores, color=colors)
        ax1.set_title('Core Quality Metrics')
        ax1.set_ylabel('Pass Rate (%)')
        ax1.set_ylim(0, 100)
        
        # Add percentage labels on bars
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{score:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 2. Performance by tags
        ax2 = axes[0, 1]
        if tag_scores:
            tags = list(tag_scores.keys())
            scores = list(tag_scores.values())
            
            bars = ax2.bar(tags, scores, color='#9b59b6')
            ax2.set_title('Performance by Test Category')
            ax2.set_ylabel('Success Rate (%)')
            ax2.set_ylim(0, 100)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            for bar, score in zip(bars, scores):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{score:.0f}%', ha='center', va='bottom', fontsize=8)
        else:
            ax2.text(0.5, 0.5, 'No tag data available', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=12)
            ax2.set_title('Performance by Test Category')
        
        # 3. Execution time distribution
        ax3 = axes[1, 0]
        ax3.hist(self.df['execution_time'], bins=10, color='#1abc9c', alpha=0.7)
        ax3.set_title('Execution Time Distribution')
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Number of Tests')
        ax3.axvline(metrics['avg_execution_time'], color='red', linestyle='--', 
                   label=f'Avg: {metrics["avg_execution_time"]:.1f}s')
        ax3.legend()
        
        # 4. Cost analysis
        ax4 = axes[1, 1]
        perf_labels = ['Total Cost\n(USD)', 'Avg Time\n(seconds)', 'Success Rate\n(%)']
        perf_values = [
            metrics['total_cost'],
            metrics['avg_execution_time'],
            metrics['execution_success_rate']
        ]
        
        # Normalize for display
        max_val = max(perf_values) if max(perf_values) > 0 else 1
        normalized_values = [v/max_val*100 for v in perf_values]
        
        bars = ax4.bar(perf_labels, normalized_values, color=['#e67e22', '#34495e', '#27ae60'])
        ax4.set_title('Performance Summary (Normalized)')
        ax4.set_ylabel('Normalized Value')
        
        # Add actual values as text
        labels = [f'${perf_values[0]:.4f}', f'{perf_values[1]:.1f}s', f'{perf_values[2]:.1f}%']
        for bar, label in zip(bars, labels):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
                    label, ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.show()
    
    def print_summary(self):
        """Print comprehensive results summary."""
        metrics = self.calculate_metrics()
        failures = self.identify_failures()
        
        print("\n" + "="*60)
        print("🎯 EVALUATION SUMMARY")
        print("="*60)
        
        print(f"📊 Tests Executed: {metrics['total_tests']}")
        print(f"✅ Execution Success: {metrics['execution_success_rate']:.1f}%")
        print(f"🔢 Number Accuracy: {metrics['number_accuracy']:.1f}%")
        print(f"📝 Answer Correctness: {metrics['answer_correctness']:.1f}%")
        print(f"🎯 Faithfulness: {metrics['faithfulness']:.1f}%")
        print(f"🚀 RAG Success: {metrics['rag_success']:.1f}%")
        
        print(f"\n⏱️  Average Execution Time: {metrics['avg_execution_time']:.1f}s")
        print(f"💰 Total Cost: ${metrics['total_cost']:.4f}")
        print(f"💸 Average Cost per Test: ${metrics['avg_cost']:.4f}")
        
        # Overall assessment
        overall = metrics['overall_score']
        if overall >= 90:
            status = "🟢 EXCELLENT - Production Ready"
        elif overall >= 80:
            status = "🟡 GOOD - Minor Improvements Needed"
        elif overall >= 60:
            status = "🟠 MODERATE - Significant Work Required"
        else:
            status = "🔴 POOR - Major Rework Needed"
        
        print(f"\n🎖️  Overall Score: {overall:.1f}%")
        print(f"📈 Status: {status}")
        
        # Detailed failure analysis by metric type
        if failures:
            print(f"\n❌ Failed Tests: {len(failures)}")
            print("-" * 60)
            
            # Group failures by metric type
            metric_failures = {}
            for failure in failures:
                for metric in failure['failed_metrics']:
                    if metric not in metric_failures:
                        metric_failures[metric] = []
                    metric_failures[metric].append(failure['test_id'])
            
            # Show failures by metric
            for metric, test_ids in metric_failures.items():
                print(f"🔴 {metric} Failures ({len(test_ids)} tests):")
                print(f"   Test IDs: {', '.join(test_ids)}")
                print()
            
            # Show detailed failure summary
            print("📋 Detailed Failure Summary:")
            print("-" * 40)
            for failure in failures[:8]:  # Show up to 8 failures
                print(f"• {failure['test_id']}: {', '.join(failure['failed_metrics'])}")
                print(f"  Question: {failure['question'][:80]}...")
                print(f"  Issue: {failure['explanation'][:120]}...")
                print()
        else:
            print("\n🎉 All tests passed!")
        
        print("="*60)
    
    def save_results(self, filepath: str):
        """Save results to CSV file."""
        self.df.to_csv(filepath, index=False)
        print(f"💾 Results saved to: {filepath}")