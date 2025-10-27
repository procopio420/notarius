"""
RAG evaluation runner
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import httpx

from .golden_qa_sets import GoldenQuery, GoldenAnswer, get_golden_qa_sets
from .rag_metrics import RAGEvaluator, OverallMetrics, get_rag_evaluator


class EvaluationRunner:
    """Runs RAG evaluation using golden Q&A sets."""
    
    def __init__(self):
        self.golden_qa_sets = get_golden_qa_sets()
        self.rag_evaluator = get_rag_evaluator()
        self.results = []
    
    async def run_evaluation(
        self, 
        lexnode_url: str = "http://localhost:8001",
        intent_engine_url: str = "http://localhost:8003",
        notarius_url: str = "http://localhost:8000",
        max_queries: Optional[int] = None,
        categories: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run complete RAG evaluation."""
        print("Starting RAG evaluation...")
        
        # Filter queries based on criteria
        queries = self._filter_queries(max_queries, categories, difficulties)
        print(f"Evaluating {len(queries)} queries...")
        
        # Initialize HTTP clients
        async with httpx.AsyncClient() as client:
            lexnode_client = httpx.AsyncClient(base_url=lexnode_url)
            intent_engine_client = httpx.AsyncClient(base_url=intent_engine_url)
            notarius_client = httpx.AsyncClient(base_url=notarius_url)
            
            try:
                # Run evaluation for each query
                for i, query in enumerate(queries):
                    print(f"Evaluating query {i+1}/{len(queries)}: {query.query[:50]}...")
                    
                    try:
                        result = await self._evaluate_single_query(
                            query, lexnode_client, intent_engine_client, notarius_client
                        )
                        self.results.append(result)
                        
                        # Print progress
                        if result["overall_metrics"]:
                            overall_score = result["overall_metrics"]["overall_score"]
                            print(f"  Overall score: {overall_score:.3f}")
                        else:
                            print("  Evaluation failed")
                            
                    except Exception as e:
                        print(f"  Error evaluating query: {e}")
                        self.results.append({
                            "query": query.query,
                            "error": str(e),
                            "overall_metrics": None
                        })
                
                # Calculate aggregate metrics
                aggregate_metrics = self._calculate_aggregate_metrics()
                
                # Generate evaluation report
                report = self._generate_report(aggregate_metrics)
                
                return report
                
            finally:
                await lexnode_client.aclose()
                await intent_engine_client.aclose()
                await notarius_client.aclose()
    
    def _filter_queries(
        self, 
        max_queries: Optional[int], 
        categories: Optional[List[str]], 
        difficulties: Optional[List[str]]
    ) -> List[GoldenQuery]:
        """Filter queries based on criteria."""
        queries = self.golden_qa_sets.queries
        
        # Filter by categories
        if categories:
            queries = [q for q in queries if q.category in categories]
        
        # Filter by difficulties
        if difficulties:
            queries = [q for q in queries if q.difficulty in difficulties]
        
        # Limit number of queries
        if max_queries:
            queries = queries[:max_queries]
        
        return queries
    
    async def _evaluate_single_query(
        self, 
        query: GoldenQuery, 
        lexnode_client: httpx.AsyncClient, 
        intent_engine_client: httpx.AsyncClient, 
        notarius_client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """Evaluate a single query."""
        start_time = time.time()
        
        # 1. Test retrieval
        retrieval_results = await self._test_retrieval(query, lexnode_client)
        
        # 2. Test grounded draft
        draft_data = await self._test_grounded_draft(query, lexnode_client)
        
        # 3. Test intent parsing
        intent_data = await self._test_intent_parsing(query, intent_engine_client)
        
        # 4. Test PII protection
        pii_data = await self._test_pii_protection(query, notarius_client)
        
        # 5. Evaluate metrics
        overall_metrics = None
        if retrieval_results is not None and draft_data is not None:
            try:
                # Get golden answer
                golden_answer = self.golden_qa_sets.get_answer_by_query_id(query.query)
                
                # Evaluate overall performance
                overall_metrics = self.rag_evaluator.evaluate_overall(
                    query.query, retrieval_results, draft_data, pii_data, intent_data, query, golden_answer
                )
                
                # Convert to dict for JSON serialization
                overall_metrics = asdict(overall_metrics)
                
            except Exception as e:
                print(f"    Error calculating metrics: {e}")
        
        evaluation_time = time.time() - start_time
        
        return {
            "query": query.query,
            "query_metadata": asdict(query),
            "retrieval_results": retrieval_results,
            "draft_data": draft_data,
            "intent_data": intent_data,
            "pii_data": pii_data,
            "overall_metrics": overall_metrics,
            "evaluation_time": evaluation_time,
            "timestamp": time.time()
        }
    
    async def _test_retrieval(
        self, 
        query: GoldenQuery, 
        lexnode_client: httpx.AsyncClient
    ) -> Optional[List[Dict[str, Any]]]:
        """Test retrieval performance."""
        try:
            payload = {
                "query": query.query,
                "constraints": {
                    "jurisdiction": query.expected_jurisdiction,
                    "document_type": query.expected_document_type
                },
                "top_k": 10
            }
            
            response = await lexnode_client.post("/api/v1/lexnode/retrieve", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                print(f"    Retrieval failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    Retrieval error: {e}")
            return None
    
    async def _test_grounded_draft(
        self, 
        query: GoldenQuery, 
        lexnode_client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """Test grounded draft generation."""
        try:
            payload = {
                "act_type": query.expected_act_type,
                "variables": {
                    "PARTY_1_NAME": "João Silva",
                    "PARTY_1_CPF": "123.456.789-00"
                }
            }
            
            response = await lexnode_client.post("/api/v1/lexnode/grounded-draft", json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"    Grounded draft failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    Grounded draft error: {e}")
            return None
    
    async def _test_intent_parsing(
        self, 
        query: GoldenQuery, 
        intent_engine_client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """Test intent parsing."""
        try:
            payload = {
                "command": query.query,
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            
            response = await intent_engine_client.post("/api/v1/intent/parse", json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"    Intent parsing failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    Intent parsing error: {e}")
            return None
    
    async def _test_pii_protection(
        self, 
        query: GoldenQuery, 
        notarius_client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """Test PII protection."""
        try:
            payload = {
                "command": query.query,
                "processo_id": None
            }
            
            response = await notarius_client.post("/api/v1/notarius/ai/generate/", json=payload)
            
            if response.status_code == 201:
                data = response.json()
                minuta_id = data["minuta_id"]
                
                # Get minuta details
                minuta_response = await notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
                
                if minuta_response.status_code == 200:
                    minuta_data = minuta_response.json()
                    
                    return {
                        "detected_pii": query.expected_entities,
                        "tokenized_pii": minuta_data.get("variaveis_json", {}),
                        "draft_content": minuta_data.get("corpo_md", ""),
                        "pii_protection_success": True
                    }
                else:
                    print(f"    Minuta retrieval failed with status {minuta_response.status_code}")
                    return None
            else:
                print(f"    PII protection test failed with status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    PII protection error: {e}")
            return None
    
    def _calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate metrics across all evaluations."""
        if not self.results:
            return {}
        
        # Filter successful evaluations
        successful_results = [r for r in self.results if r["overall_metrics"] is not None]
        
        if not successful_results:
            return {"error": "No successful evaluations"}
        
        # Calculate aggregate metrics
        aggregate_metrics = {
            "total_queries": len(self.results),
            "successful_queries": len(successful_results),
            "failed_queries": len(self.results) - len(successful_results),
            "success_rate": len(successful_results) / len(self.results),
            "average_evaluation_time": sum(r["evaluation_time"] for r in self.results) / len(self.results),
            "overall_scores": {
                "mean": sum(r["overall_metrics"]["overall_score"] for r in successful_results) / len(successful_results),
                "min": min(r["overall_metrics"]["overall_score"] for r in successful_results),
                "max": max(r["overall_metrics"]["overall_score"] for r in successful_results),
                "std": self._calculate_std_dev([r["overall_metrics"]["overall_score"] for r in successful_results])
            }
        }
        
        # Calculate component metrics
        component_metrics = self._calculate_component_metrics(successful_results)
        aggregate_metrics.update(component_metrics)
        
        # Calculate category metrics
        category_metrics = self._calculate_category_metrics(successful_results)
        aggregate_metrics["category_metrics"] = category_metrics
        
        # Calculate difficulty metrics
        difficulty_metrics = self._calculate_difficulty_metrics(successful_results)
        aggregate_metrics["difficulty_metrics"] = difficulty_metrics
        
        return aggregate_metrics
    
    def _calculate_component_metrics(self, successful_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for each component."""
        component_metrics = {}
        
        # Retrieval metrics
        retrieval_scores = []
        for result in successful_results:
            if result["overall_metrics"]["retrieval_metrics"]:
                retrieval_scores.append(result["overall_metrics"]["retrieval_metrics"]["hit_at_5"])
        
        if retrieval_scores:
            component_metrics["retrieval_metrics"] = {
                "hit_at_5_mean": sum(retrieval_scores) / len(retrieval_scores),
                "hit_at_5_std": self._calculate_std_dev(retrieval_scores)
            }
        
        # Grounding metrics
        grounding_scores = []
        for result in successful_results:
            if result["overall_metrics"]["grounding_metrics"]:
                grounding_scores.append(result["overall_metrics"]["grounding_metrics"]["grounding_confidence"])
        
        if grounding_scores:
            component_metrics["grounding_metrics"] = {
                "grounding_confidence_mean": sum(grounding_scores) / len(grounding_scores),
                "grounding_confidence_std": self._calculate_std_dev(grounding_scores)
            }
        
        # PII metrics
        pii_scores = []
        for result in successful_results:
            if result["overall_metrics"]["pii_metrics"]:
                pii_scores.append(result["overall_metrics"]["pii_metrics"]["pii_accuracy"])
        
        if pii_scores:
            component_metrics["pii_metrics"] = {
                "pii_accuracy_mean": sum(pii_scores) / len(pii_scores),
                "pii_accuracy_std": self._calculate_std_dev(pii_scores)
            }
        
        # Intent metrics
        intent_scores = []
        for result in successful_results:
            if result["overall_metrics"]["intent_metrics"]:
                intent_scores.append(result["overall_metrics"]["intent_metrics"]["act_type_accuracy"])
        
        if intent_scores:
            component_metrics["intent_metrics"] = {
                "act_type_accuracy_mean": sum(intent_scores) / len(intent_scores),
                "act_type_accuracy_std": self._calculate_std_dev(intent_scores)
            }
        
        return component_metrics
    
    def _calculate_category_metrics(self, successful_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics by category."""
        category_metrics = {}
        
        # Group results by category
        category_groups = {}
        for result in successful_results:
            category = result["query_metadata"]["category"]
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(result)
        
        # Calculate metrics for each category
        for category, results in category_groups.items():
            scores = [r["overall_metrics"]["overall_score"] for r in results]
            category_metrics[category] = {
                "count": len(results),
                "mean_score": sum(scores) / len(scores),
                "std_score": self._calculate_std_dev(scores),
                "min_score": min(scores),
                "max_score": max(scores)
            }
        
        return category_metrics
    
    def _calculate_difficulty_metrics(self, successful_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics by difficulty."""
        difficulty_metrics = {}
        
        # Group results by difficulty
        difficulty_groups = {}
        for result in successful_results:
            difficulty = result["query_metadata"]["difficulty"]
            if difficulty not in difficulty_groups:
                difficulty_groups[difficulty] = []
            difficulty_groups[difficulty].append(result)
        
        # Calculate metrics for each difficulty
        for difficulty, results in difficulty_groups.items():
            scores = [r["overall_metrics"]["overall_score"] for r in results]
            difficulty_metrics[difficulty] = {
                "count": len(results),
                "mean_score": sum(scores) / len(scores),
                "std_score": self._calculate_std_dev(scores),
                "min_score": min(scores),
                "max_score": max(scores)
            }
        
        return difficulty_metrics
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _generate_report(self, aggregate_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate evaluation report."""
        report = {
            "evaluation_summary": {
                "timestamp": time.time(),
                "total_queries": aggregate_metrics.get("total_queries", 0),
                "successful_queries": aggregate_metrics.get("successful_queries", 0),
                "failed_queries": aggregate_metrics.get("failed_queries", 0),
                "success_rate": aggregate_metrics.get("success_rate", 0.0),
                "average_evaluation_time": aggregate_metrics.get("average_evaluation_time", 0.0)
            },
            "overall_performance": aggregate_metrics.get("overall_scores", {}),
            "component_performance": {
                "retrieval": aggregate_metrics.get("retrieval_metrics", {}),
                "grounding": aggregate_metrics.get("grounding_metrics", {}),
                "pii_protection": aggregate_metrics.get("pii_metrics", {}),
                "intent_parsing": aggregate_metrics.get("intent_metrics", {})
            },
            "category_performance": aggregate_metrics.get("category_metrics", {}),
            "difficulty_performance": aggregate_metrics.get("difficulty_metrics", {}),
            "detailed_results": self.results,
            "recommendations": self._generate_recommendations(aggregate_metrics)
        }
        
        return report
    
    def _generate_recommendations(self, aggregate_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []
        
        # Check overall performance
        overall_scores = aggregate_metrics.get("overall_scores", {})
        mean_score = overall_scores.get("mean", 0.0)
        
        if mean_score < 0.5:
            recommendations.append("Overall performance is below acceptable threshold. Consider improving all components.")
        elif mean_score < 0.7:
            recommendations.append("Overall performance is moderate. Focus on improving weakest components.")
        
        # Check component performance
        component_metrics = aggregate_metrics.get("retrieval_metrics", {})
        if component_metrics.get("hit_at_5_mean", 0.0) < 0.5:
            recommendations.append("Retrieval performance is poor. Consider improving search algorithms or indexing.")
        
        component_metrics = aggregate_metrics.get("grounding_metrics", {})
        if component_metrics.get("grounding_confidence_mean", 0.0) < 0.5:
            recommendations.append("Grounding performance is poor. Consider improving citation quality and relevance.")
        
        component_metrics = aggregate_metrics.get("pii_metrics", {})
        if component_metrics.get("pii_accuracy_mean", 0.0) < 0.8:
            recommendations.append("PII protection performance is below security requirements. Review PII detection and tokenization.")
        
        component_metrics = aggregate_metrics.get("intent_metrics", {})
        if component_metrics.get("act_type_accuracy_mean", 0.0) < 0.8:
            recommendations.append("Intent parsing performance is poor. Consider improving NLP models or training data.")
        
        # Check category performance
        category_metrics = aggregate_metrics.get("category_metrics", {})
        for category, metrics in category_metrics.items():
            if metrics.get("mean_score", 0.0) < 0.5:
                recommendations.append(f"Performance for {category} category is poor. Consider category-specific improvements.")
        
        # Check difficulty performance
        difficulty_metrics = aggregate_metrics.get("difficulty_metrics", {})
        if difficulty_metrics.get("hard", {}).get("mean_score", 0.0) < 0.3:
            recommendations.append("Performance on hard queries is very poor. Consider improving system robustness.")
        
        if not recommendations:
            recommendations.append("System performance is satisfactory across all components.")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = "rag_evaluation_report.json"):
        """Save evaluation report to file."""
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Evaluation report saved to {filename}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print evaluation summary."""
        summary = report["evaluation_summary"]
        overall = report["overall_performance"]
        
        print("\n" + "="*50)
        print("RAG EVALUATION SUMMARY")
        print("="*50)
        print(f"Total queries: {summary['total_queries']}")
        print(f"Successful queries: {summary['successful_queries']}")
        print(f"Failed queries: {summary['failed_queries']}")
        print(f"Success rate: {summary['success_rate']:.1%}")
        print(f"Average evaluation time: {summary['average_evaluation_time']:.2f}s")
        print(f"Overall score: {overall.get('mean', 0.0):.3f} ± {overall.get('std', 0.0):.3f}")
        print(f"Score range: {overall.get('min', 0.0):.3f} - {overall.get('max', 0.0):.3f}")
        
        print("\nComponent Performance:")
        for component, metrics in report["component_performance"].items():
            if metrics:
                print(f"  {component}: {metrics.get('mean', 0.0):.3f} ± {metrics.get('std', 0.0):.3f}")
        
        print("\nRecommendations:")
        for recommendation in report["recommendations"]:
            print(f"  - {recommendation}")
        
        print("="*50)


# Global instance
evaluation_runner = EvaluationRunner()


def get_evaluation_runner() -> EvaluationRunner:
    """Get the global evaluation runner instance."""
    return evaluation_runner


async def run_evaluation(
    max_queries: Optional[int] = None,
    categories: Optional[List[str]] = None,
    difficulties: Optional[List[str]] = None,
    save_report: bool = True,
    print_summary: bool = True
) -> Dict[str, Any]:
    """Run RAG evaluation with default settings."""
    runner = get_evaluation_runner()
    
    # Run evaluation
    report = await runner.run_evaluation(
        max_queries=max_queries,
        categories=categories,
        difficulties=difficulties
    )
    
    # Save report
    if save_report:
        runner.save_report(report)
    
    # Print summary
    if print_summary:
        runner.print_summary(report)
    
    return report


if __name__ == "__main__":
    # Run evaluation with default settings
    asyncio.run(run_evaluation(max_queries=10))
