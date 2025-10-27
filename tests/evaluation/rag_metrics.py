"""
RAG evaluation metrics implementation
"""

import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

from .golden_qa_sets import GoldenQuery, GoldenAnswer, get_golden_qa_sets


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval evaluation."""
    hit_at_1: float
    hit_at_5: float
    hit_at_10: float
    mrr: float  # Mean Reciprocal Rank
    ndcg_at_5: float
    ndcg_at_10: float
    precision_at_5: float
    precision_at_10: float
    recall_at_5: float
    recall_at_10: float
    f1_at_5: float
    f1_at_10: float


@dataclass
class GroundingMetrics:
    """Metrics for grounding evaluation."""
    grounding_confidence: float
    citation_quality: float
    citation_coverage: float
    false_grounding_rate: float
    grounding_consistency: float


@dataclass
class PIIMetrics:
    """Metrics for PII protection evaluation."""
    pii_detection_rate: float
    pii_tokenization_rate: float
    pii_detokenization_rate: float
    pii_leak_rate: float
    pii_accuracy: float


@dataclass
class IntentMetrics:
    """Metrics for intent parsing evaluation."""
    act_type_accuracy: float
    entity_extraction_accuracy: float
    confidence_calibration: float
    intent_consistency: float


@dataclass
class OverallMetrics:
    """Overall evaluation metrics."""
    retrieval_metrics: RetrievalMetrics
    grounding_metrics: GroundingMetrics
    pii_metrics: PIIMetrics
    intent_metrics: IntentMetrics
    overall_score: float


class RAGEvaluator:
    """RAG evaluation system."""
    
    def __init__(self):
        self.golden_qa_sets = get_golden_qa_sets()
    
    def evaluate_retrieval(
        self, 
        query: str, 
        results: List[Dict[str, Any]], 
        golden_query: GoldenQuery
    ) -> RetrievalMetrics:
        """Evaluate retrieval performance."""
        if not results:
            return RetrievalMetrics(
                hit_at_1=0.0, hit_at_5=0.0, hit_at_10=0.0,
                mrr=0.0, ndcg_at_5=0.0, ndcg_at_10=0.0,
                precision_at_5=0.0, precision_at_10=0.0,
                recall_at_5=0.0, recall_at_10=0.0,
                f1_at_5=0.0, f1_at_10=0.0
            )
        
        # Calculate hit@k metrics
        hit_at_1 = 1.0 if results[0]["score"] > 0.5 else 0.0
        hit_at_5 = sum(1.0 for r in results[:5] if r["score"] > 0.5) / 5.0
        hit_at_10 = sum(1.0 for r in results[:10] if r["score"] > 0.5) / 10.0
        
        # Calculate MRR
        mrr = 0.0
        for i, result in enumerate(results):
            if result["score"] > 0.5:
                mrr = 1.0 / (i + 1)
                break
        
        # Calculate nDCG
        scores = [r["score"] for r in results]
        ndcg_at_5 = self._calculate_ndcg(scores[:5])
        ndcg_at_10 = self._calculate_ndcg(scores[:10])
        
        # Calculate precision and recall
        precision_at_5, recall_at_5 = self._calculate_precision_recall(results[:5], golden_query)
        precision_at_10, recall_at_10 = self._calculate_precision_recall(results[:10], golden_query)
        
        # Calculate F1 scores
        f1_at_5 = 2 * (precision_at_5 * recall_at_5) / (precision_at_5 + recall_at_5) if (precision_at_5 + recall_at_5) > 0 else 0.0
        f1_at_10 = 2 * (precision_at_10 * recall_at_10) / (precision_at_10 + recall_at_10) if (precision_at_10 + recall_at_10) > 0 else 0.0
        
        return RetrievalMetrics(
            hit_at_1=hit_at_1, hit_at_5=hit_at_5, hit_at_10=hit_at_10,
            mrr=mrr, ndcg_at_5=ndcg_at_5, ndcg_at_10=ndcg_at_10,
            precision_at_5=precision_at_5, precision_at_10=precision_at_10,
            recall_at_5=recall_at_5, recall_at_10=recall_at_10,
            f1_at_5=f1_at_5, f1_at_10=f1_at_10
        )
    
    def evaluate_grounding(
        self, 
        draft_data: Dict[str, Any], 
        golden_answer: GoldenAnswer
    ) -> GroundingMetrics:
        """Evaluate grounding performance."""
        # Grounding confidence
        grounding_confidence = draft_data.get("confidence", 0.0)
        
        # Citation quality
        citations = draft_data.get("citations", [])
        citation_quality = self._calculate_citation_quality(citations, golden_answer.expected_citations)
        
        # Citation coverage
        citation_coverage = self._calculate_citation_coverage(citations, golden_answer.expected_citations)
        
        # False grounding rate
        false_grounding_rate = self._calculate_false_grounding_rate(draft_data, golden_answer)
        
        # Grounding consistency
        grounding_consistency = self._calculate_grounding_consistency(draft_data, golden_answer)
        
        return GroundingMetrics(
            grounding_confidence=grounding_confidence,
            citation_quality=citation_quality,
            citation_coverage=citation_coverage,
            false_grounding_rate=false_grounding_rate,
            grounding_consistency=grounding_consistency
        )
    
    def evaluate_pii_protection(
        self, 
        pii_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> PIIMetrics:
        """Evaluate PII protection performance."""
        # PII detection rate
        pii_detection_rate = self._calculate_pii_detection_rate(pii_data, golden_query)
        
        # PII tokenization rate
        pii_tokenization_rate = self._calculate_pii_tokenization_rate(pii_data, golden_query)
        
        # PII detokenization rate
        pii_detokenization_rate = self._calculate_pii_detokenization_rate(pii_data, golden_query)
        
        # PII leak rate
        pii_leak_rate = self._calculate_pii_leak_rate(pii_data, golden_query)
        
        # PII accuracy
        pii_accuracy = self._calculate_pii_accuracy(pii_data, golden_query)
        
        return PIIMetrics(
            pii_detection_rate=pii_detection_rate,
            pii_tokenization_rate=pii_tokenization_rate,
            pii_detokenization_rate=pii_detokenization_rate,
            pii_leak_rate=pii_leak_rate,
            pii_accuracy=pii_accuracy
        )
    
    def evaluate_intent_parsing(
        self, 
        intent_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> IntentMetrics:
        """Evaluate intent parsing performance."""
        # Act type accuracy
        act_type_accuracy = self._calculate_act_type_accuracy(intent_data, golden_query)
        
        # Entity extraction accuracy
        entity_extraction_accuracy = self._calculate_entity_extraction_accuracy(intent_data, golden_query)
        
        # Confidence calibration
        confidence_calibration = self._calculate_confidence_calibration(intent_data, golden_query)
        
        # Intent consistency
        intent_consistency = self._calculate_intent_consistency(intent_data, golden_query)
        
        return IntentMetrics(
            act_type_accuracy=act_type_accuracy,
            entity_extraction_accuracy=entity_extraction_accuracy,
            confidence_calibration=confidence_calibration,
            intent_consistency=intent_consistency
        )
    
    def evaluate_overall(
        self, 
        query: str, 
        retrieval_results: List[Dict[str, Any]], 
        draft_data: Dict[str, Any], 
        pii_data: Dict[str, Any], 
        intent_data: Dict[str, Any], 
        golden_query: GoldenQuery, 
        golden_answer: GoldenAnswer
    ) -> OverallMetrics:
        """Evaluate overall RAG performance."""
        # Evaluate individual components
        retrieval_metrics = self.evaluate_retrieval(query, retrieval_results, golden_query)
        grounding_metrics = self.evaluate_grounding(draft_data, golden_answer)
        pii_metrics = self.evaluate_pii_protection(pii_data, golden_query)
        intent_metrics = self.evaluate_intent_parsing(intent_data, golden_query)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            retrieval_metrics, grounding_metrics, pii_metrics, intent_metrics
        )
        
        return OverallMetrics(
            retrieval_metrics=retrieval_metrics,
            grounding_metrics=grounding_metrics,
            pii_metrics=pii_metrics,
            intent_metrics=intent_metrics,
            overall_score=overall_score
        )
    
    def _calculate_ndcg(self, scores: List[float]) -> float:
        """Calculate nDCG for a list of scores."""
        if not scores:
            return 0.0
        
        # Calculate DCG
        dcg = 0.0
        for i, score in enumerate(scores):
            dcg += score / math.log2(i + 2)  # i+2 because log2(1) = 0
        
        # Calculate IDCG (ideal DCG with sorted scores)
        ideal_scores = sorted(scores, reverse=True)
        idcg = 0.0
        for i, score in enumerate(ideal_scores):
            idcg += score / math.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def _calculate_precision_recall(
        self, 
        results: List[Dict[str, Any]], 
        golden_query: GoldenQuery
    ) -> Tuple[float, float]:
        """Calculate precision and recall for retrieval results."""
        if not results:
            return 0.0, 0.0
        
        # Count relevant results
        relevant_count = sum(1 for r in results if r["score"] > 0.5)
        
        # Precision = relevant results / total results
        precision = relevant_count / len(results)
        
        # Recall = relevant results / expected relevant results
        expected_relevant = golden_query.expected_citations_count
        recall = relevant_count / expected_relevant if expected_relevant > 0 else 0.0
        
        return precision, recall
    
    def _calculate_citation_quality(
        self, 
        actual_citations: List[Dict[str, Any]], 
        expected_citations: List[Dict[str, Any]]
    ) -> float:
        """Calculate citation quality score."""
        if not actual_citations or not expected_citations:
            return 0.0
        
        # Calculate average score of actual citations
        avg_score = sum(c.get("score", 0.0) for c in actual_citations) / len(actual_citations)
        
        # Calculate overlap with expected citations
        overlap = 0.0
        for actual_citation in actual_citations:
            for expected_citation in expected_citations:
                if self._citations_match(actual_citation, expected_citation):
                    overlap += 1.0
                    break
        
        overlap_score = overlap / len(expected_citations)
        
        # Combine average score and overlap
        return (avg_score + overlap_score) / 2.0
    
    def _calculate_citation_coverage(
        self, 
        actual_citations: List[Dict[str, Any]], 
        expected_citations: List[Dict[str, Any]]
    ) -> float:
        """Calculate citation coverage score."""
        if not expected_citations:
            return 1.0
        
        covered = 0.0
        for expected_citation in expected_citations:
            for actual_citation in actual_citations:
                if self._citations_match(actual_citation, expected_citation):
                    covered += 1.0
                    break
        
        return covered / len(expected_citations)
    
    def _calculate_false_grounding_rate(
        self, 
        draft_data: Dict[str, Any], 
        golden_answer: GoldenAnswer
    ) -> float:
        """Calculate false grounding rate."""
        # Check if confidence is too high for the quality of results
        confidence = draft_data.get("confidence", 0.0)
        expected_confidence = golden_answer.expected_confidence_score
        
        # If confidence is much higher than expected, it might be false grounding
        if confidence > expected_confidence * 1.5:
            return 0.5  # 50% false grounding rate
        
        # Check if citations are relevant
        citations = draft_data.get("citations", [])
        if not citations:
            return 0.0
        
        # Check if average citation score is too low
        avg_citation_score = sum(c.get("score", 0.0) for c in citations) / len(citations)
        if avg_citation_score < 0.3:
            return 0.3  # 30% false grounding rate
        
        return 0.0
    
    def _calculate_grounding_consistency(
        self, 
        draft_data: Dict[str, Any], 
        golden_answer: GoldenAnswer
    ) -> float:
        """Calculate grounding consistency score."""
        # Check if the draft structure matches expected structure
        draft_structure = draft_data.get("draft_structure", {})
        expected_structure = golden_answer.expected_draft_structure
        
        if not draft_structure or not expected_structure:
            return 0.0
        
        # Calculate structure similarity
        structure_similarity = self._calculate_structure_similarity(draft_structure, expected_structure)
        
        # Check if confidence is consistent with quality
        confidence = draft_data.get("confidence", 0.0)
        expected_confidence = golden_answer.expected_confidence_score
        
        confidence_consistency = 1.0 - abs(confidence - expected_confidence)
        
        return (structure_similarity + confidence_consistency) / 2.0
    
    def _calculate_pii_detection_rate(
        self, 
        pii_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate PII detection rate."""
        detected_pii = pii_data.get("detected_pii", [])
        expected_pii_types = golden_query.expected_pii_types
        
        if not expected_pii_types:
            return 1.0  # No PII expected, so 100% detection rate
        
        detected_types = set(pii.get("type") for pii in detected_pii)
        expected_types = set(expected_pii_types)
        
        return len(detected_types.intersection(expected_types)) / len(expected_types)
    
    def _calculate_pii_tokenization_rate(
        self, 
        pii_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate PII tokenization rate."""
        tokenized_pii = pii_data.get("tokenized_pii", {})
        expected_pii_types = golden_query.expected_pii_types
        
        if not expected_pii_types:
            return 1.0  # No PII expected, so 100% tokenization rate
        
        tokenized_types = set(tokenized_pii.keys())
        expected_types = set(expected_pii_types)
        
        return len(tokenized_types.intersection(expected_types)) / len(expected_types)
    
    def _calculate_pii_detokenization_rate(
        self, 
        pii_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate PII detokenization rate."""
        detokenized_pii = pii_data.get("detokenized_pii", {})
        tokenized_pii = pii_data.get("tokenized_pii", {})
        
        if not tokenized_pii:
            return 1.0  # No PII to detokenize, so 100% detokenization rate
        
        return len(detokenized_pii) / len(tokenized_pii)
    
    def _calculate_pii_leak_rate(
        self, 
        pii_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate PII leak rate."""
        # Check if any PII is present in non-tokenized form
        draft_content = pii_data.get("draft_content", "")
        expected_entities = golden_query.expected_entities
        
        leaks = 0.0
        for entity in expected_entities:
            if entity in draft_content:
                leaks += 1.0
        
        return leaks / len(expected_entities) if expected_entities else 0.0
    
    def _calculate_pii_accuracy(
        self, 
        pii_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate PII accuracy score."""
        # Combine detection, tokenization, and detokenization rates
        detection_rate = self._calculate_pii_detection_rate(pii_data, golden_query)
        tokenization_rate = self._calculate_pii_tokenization_rate(pii_data, golden_query)
        detokenization_rate = self._calculate_pii_detokenization_rate(pii_data, golden_query)
        leak_rate = self._calculate_pii_leak_rate(pii_data, golden_query)
        
        # Accuracy = (detection + tokenization + detokenization) / 3 - leak_rate
        accuracy = (detection_rate + tokenization_rate + detokenization_rate) / 3.0 - leak_rate
        
        return max(0.0, accuracy)
    
    def _calculate_act_type_accuracy(
        self, 
        intent_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate act type accuracy."""
        predicted_act_type = intent_data.get("intent", {}).get("act_type", "")
        expected_act_type = golden_query.expected_act_type
        
        return 1.0 if predicted_act_type == expected_act_type else 0.0
    
    def _calculate_entity_extraction_accuracy(
        self, 
        intent_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate entity extraction accuracy."""
        extracted_entities = intent_data.get("pii_extracted", [])
        expected_entities = golden_query.expected_entities
        
        if not expected_entities:
            return 1.0  # No entities expected, so 100% accuracy
        
        extracted_values = set(entity.get("value", "") for entity in extracted_entities)
        expected_values = set(expected_entities)
        
        return len(extracted_values.intersection(expected_values)) / len(expected_values)
    
    def _calculate_confidence_calibration(
        self, 
        intent_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate confidence calibration score."""
        predicted_confidence = intent_data.get("confidence", 0.0)
        expected_confidence = golden_query.expected_confidence_threshold
        
        # Calibration is better when predicted confidence is close to expected confidence
        return 1.0 - abs(predicted_confidence - expected_confidence)
    
    def _calculate_intent_consistency(
        self, 
        intent_data: Dict[str, Any], 
        golden_query: GoldenQuery
    ) -> float:
        """Calculate intent consistency score."""
        # Check if intent is consistent with query
        intent = intent_data.get("intent", {})
        act_type = intent.get("act_type", "")
        expected_act_type = golden_query.expected_act_type
        
        # Check if metadata is consistent
        metadata = intent.get("metadata", {})
        expected_metadata = golden_query.expected_metadata
        
        act_type_consistency = 1.0 if act_type == expected_act_type else 0.0
        metadata_consistency = self._calculate_metadata_consistency(metadata, expected_metadata)
        
        return (act_type_consistency + metadata_consistency) / 2.0
    
    def _calculate_metadata_consistency(
        self, 
        actual_metadata: Dict[str, Any], 
        expected_metadata: Dict[str, Any]
    ) -> float:
        """Calculate metadata consistency score."""
        if not expected_metadata:
            return 1.0  # No metadata expected, so 100% consistency
        
        consistent_fields = 0.0
        for key, expected_value in expected_metadata.items():
            actual_value = actual_metadata.get(key)
            if actual_value == expected_value:
                consistent_fields += 1.0
        
        return consistent_fields / len(expected_metadata)
    
    def _calculate_structure_similarity(
        self, 
        actual_structure: Dict[str, Any], 
        expected_structure: Dict[str, Any]
    ) -> float:
        """Calculate structure similarity score."""
        if not actual_structure or not expected_structure:
            return 0.0
        
        # Check if required sections are present
        actual_sections = set(actual_structure.get("sections", []))
        expected_sections = set(expected_structure.get("sections", []))
        
        if not expected_sections:
            return 1.0  # No sections expected, so 100% similarity
        
        section_similarity = len(actual_sections.intersection(expected_sections)) / len(expected_sections)
        
        # Check if required clauses are present
        actual_clauses = set(actual_structure.get("required_clauses", []))
        expected_clauses = set(expected_structure.get("required_clauses", []))
        
        if not expected_clauses:
            return section_similarity  # No clauses expected, so only section similarity matters
        
        clause_similarity = len(actual_clauses.intersection(expected_clauses)) / len(expected_clauses)
        
        return (section_similarity + clause_similarity) / 2.0
    
    def _citations_match(
        self, 
        actual_citation: Dict[str, Any], 
        expected_citation: Dict[str, Any]
    ) -> bool:
        """Check if two citations match."""
        # Check if URIs match
        actual_uri = actual_citation.get("uri", "")
        expected_uri = expected_citation.get("uri", "")
        
        if actual_uri and expected_uri:
            return actual_uri == expected_uri
        
        # Check if anchors match
        actual_anchor = actual_citation.get("anchor", "")
        expected_anchor = expected_citation.get("anchor", "")
        
        if actual_anchor and expected_anchor:
            return actual_anchor == expected_anchor
        
        # Check if titles match
        actual_title = actual_citation.get("title", "")
        expected_title = expected_citation.get("title", "")
        
        if actual_title and expected_title:
            return actual_title == expected_title
        
        return False
    
    def _calculate_overall_score(
        self, 
        retrieval_metrics: RetrievalMetrics, 
        grounding_metrics: GroundingMetrics, 
        pii_metrics: PIIMetrics, 
        intent_metrics: IntentMetrics
    ) -> float:
        """Calculate overall evaluation score."""
        # Weighted average of all metrics
        weights = {
            "retrieval": 0.3,
            "grounding": 0.3,
            "pii": 0.2,
            "intent": 0.2
        }
        
        # Calculate component scores
        retrieval_score = (
            retrieval_metrics.hit_at_5 + 
            retrieval_metrics.ndcg_at_5 + 
            retrieval_metrics.f1_at_5
        ) / 3.0
        
        grounding_score = (
            grounding_metrics.grounding_confidence + 
            grounding_metrics.citation_quality + 
            grounding_metrics.citation_coverage + 
            (1.0 - grounding_metrics.false_grounding_rate)
        ) / 4.0
        
        pii_score = (
            pii_metrics.pii_detection_rate + 
            pii_metrics.pii_tokenization_rate + 
            pii_metrics.pii_detokenization_rate + 
            pii_metrics.pii_accuracy
        ) / 4.0
        
        intent_score = (
            intent_metrics.act_type_accuracy + 
            intent_metrics.entity_extraction_accuracy + 
            intent_metrics.confidence_calibration + 
            intent_metrics.intent_consistency
        ) / 4.0
        
        # Calculate weighted overall score
        overall_score = (
            weights["retrieval"] * retrieval_score +
            weights["grounding"] * grounding_score +
            weights["pii"] * pii_score +
            weights["intent"] * intent_score
        )
        
        return overall_score


# Global instance
rag_evaluator = RAGEvaluator()


def get_rag_evaluator() -> RAGEvaluator:
    """Get the global RAG evaluator instance."""
    return rag_evaluator
