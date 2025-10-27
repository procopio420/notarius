"""
Tests for RAG evaluation system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from .golden_qa_sets import GoldenQuery, GoldenAnswer, get_golden_qa_sets
from .rag_metrics import RAGEvaluator, get_rag_evaluator
from .evaluation_runner import EvaluationRunner, get_evaluation_runner


class TestGoldenQASets:
    """Test golden Q&A sets functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.golden_qa_sets = get_golden_qa_sets()
    
    def test_golden_qa_sets_creation(self):
        """Test that golden Q&A sets are created correctly."""
        assert len(self.golden_qa_sets.queries) > 0
        assert len(self.golden_qa_sets.answers) > 0
    
    def test_get_queries_by_category(self):
        """Test getting queries by category."""
        procuração_queries = self.golden_qa_sets.get_queries_by_category("procuração")
        assert len(procuração_queries) > 0
        
        for query in procuração_queries:
            assert query.category == "procuração"
    
    def test_get_queries_by_difficulty(self):
        """Test getting queries by difficulty."""
        easy_queries = self.golden_qa_sets.get_queries_by_difficulty("easy")
        assert len(easy_queries) > 0
        
        for query in easy_queries:
            assert query.difficulty == "easy"
    
    def test_get_queries_by_jurisdiction(self):
        """Test getting queries by jurisdiction."""
        rj_queries = self.golden_qa_sets.get_queries_by_jurisdiction("rj")
        assert len(rj_queries) > 0
        
        for query in rj_queries:
            assert query.expected_jurisdiction == "rj"
    
    def test_get_all_categories(self):
        """Test getting all categories."""
        categories = self.golden_qa_sets.get_all_categories()
        assert len(categories) > 0
        assert "procuração" in categories
        assert "contrato" in categories
    
    def test_get_all_difficulties(self):
        """Test getting all difficulties."""
        difficulties = self.golden_qa_sets.get_all_difficulties()
        assert len(difficulties) > 0
        assert "easy" in difficulties
        assert "medium" in difficulties
        assert "hard" in difficulties
    
    def test_get_statistics(self):
        """Test getting statistics."""
        stats = self.golden_qa_sets.get_statistics()
        
        assert "total_queries" in stats
        assert "total_answers" in stats
        assert "categories" in stats
        assert "difficulties" in stats
        assert "jurisdictions" in stats
        assert "average_confidence_threshold" in stats
        assert "average_grounding_confidence" in stats
        assert "average_citations_count" in stats
        
        assert stats["total_queries"] > 0
        assert stats["total_answers"] > 0
        assert 0.0 <= stats["average_confidence_threshold"] <= 1.0
        assert 0.0 <= stats["average_grounding_confidence"] <= 1.0


class TestRAGEvaluator:
    """Test RAG evaluator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_evaluator = get_rag_evaluator()
        self.golden_qa_sets = get_golden_qa_sets()
    
    def test_evaluate_retrieval(self):
        """Test retrieval evaluation."""
        # Create mock results
        results = [
            {"score": 0.9, "title": "Test Document 1", "content": "Test content 1"},
            {"score": 0.7, "title": "Test Document 2", "content": "Test content 2"},
            {"score": 0.5, "title": "Test Document 3", "content": "Test content 3"},
            {"score": 0.3, "title": "Test Document 4", "content": "Test content 4"},
            {"score": 0.1, "title": "Test Document 5", "content": "Test content 5"}
        ]
        
        # Get a test query
        query = self.golden_qa_sets.queries[0]
        
        # Evaluate retrieval
        metrics = self.rag_evaluator.evaluate_retrieval("test query", results, query)
        
        # Check metrics
        assert 0.0 <= metrics.hit_at_1 <= 1.0
        assert 0.0 <= metrics.hit_at_5 <= 1.0
        assert 0.0 <= metrics.hit_at_10 <= 1.0
        assert 0.0 <= metrics.mrr <= 1.0
        assert 0.0 <= metrics.ndcg_at_5 <= 1.0
        assert 0.0 <= metrics.ndcg_at_10 <= 1.0
        assert 0.0 <= metrics.precision_at_5 <= 1.0
        assert 0.0 <= metrics.precision_at_10 <= 1.0
        assert 0.0 <= metrics.recall_at_5 <= 1.0
        assert 0.0 <= metrics.recall_at_10 <= 1.0
        assert 0.0 <= metrics.f1_at_5 <= 1.0
        assert 0.0 <= metrics.f1_at_10 <= 1.0
    
    def test_evaluate_grounding(self):
        """Test grounding evaluation."""
        # Create mock draft data
        draft_data = {
            "confidence": 0.8,
            "citations": [
                {
                    "uri": "https://example.com/doc1",
                    "anchor": "Art. 1",
                    "title": "Test Document 1",
                    "snippet": "Test snippet 1",
                    "score": 0.9
                },
                {
                    "uri": "https://example.com/doc2",
                    "anchor": "Art. 2",
                    "title": "Test Document 2",
                    "snippet": "Test snippet 2",
                    "score": 0.7
                }
            ]
        }
        
        # Get a test answer
        answer = self.golden_qa_sets.answers[0]
        
        # Evaluate grounding
        metrics = self.rag_evaluator.evaluate_grounding(draft_data, answer)
        
        # Check metrics
        assert 0.0 <= metrics.grounding_confidence <= 1.0
        assert 0.0 <= metrics.citation_quality <= 1.0
        assert 0.0 <= metrics.citation_coverage <= 1.0
        assert 0.0 <= metrics.false_grounding_rate <= 1.0
        assert 0.0 <= metrics.grounding_consistency <= 1.0
    
    def test_evaluate_pii_protection(self):
        """Test PII protection evaluation."""
        # Create mock PII data
        pii_data = {
            "detected_pii": [
                {"type": "cpf", "value": "123.456.789-00"},
                {"type": "name", "value": "João Silva"}
            ],
            "tokenized_pii": {
                "PARTY_1_CPF": "token_cpf_12345678900",
                "PARTY_1_NAME": "token_joao_silva"
            },
            "detokenized_pii": {
                "PARTY_1_CPF": "123.456.789-00",
                "PARTY_1_NAME": "João Silva"
            },
            "draft_content": "Procuração para PARTY_1_NAME, CPF PARTY_1_CPF"
        }
        
        # Get a test query
        query = self.golden_qa_sets.queries[0]
        
        # Evaluate PII protection
        metrics = self.rag_evaluator.evaluate_pii_protection(pii_data, query)
        
        # Check metrics
        assert 0.0 <= metrics.pii_detection_rate <= 1.0
        assert 0.0 <= metrics.pii_tokenization_rate <= 1.0
        assert 0.0 <= metrics.pii_detokenization_rate <= 1.0
        assert 0.0 <= metrics.pii_leak_rate <= 1.0
        assert 0.0 <= metrics.pii_accuracy <= 1.0
    
    def test_evaluate_intent_parsing(self):
        """Test intent parsing evaluation."""
        # Create mock intent data
        intent_data = {
            "intent": {
                "act_type": "procuração",
                "parties": [
                    {
                        "role": "outorgante",
                        "pii_extracted": ["João Silva", "123.456.789-00"]
                    }
                ],
                "metadata": {
                    "purpose": "venda de imóvel",
                    "jurisdiction": "sp"
                }
            },
            "pii_extracted": [
                {"type": "name", "value": "João Silva"},
                {"type": "cpf", "value": "123.456.789-00"}
            ],
            "confidence": 0.9
        }
        
        # Get a test query
        query = self.golden_qa_sets.queries[0]
        
        # Evaluate intent parsing
        metrics = self.rag_evaluator.evaluate_intent_parsing(intent_data, query)
        
        # Check metrics
        assert 0.0 <= metrics.act_type_accuracy <= 1.0
        assert 0.0 <= metrics.entity_extraction_accuracy <= 1.0
        assert 0.0 <= metrics.confidence_calibration <= 1.0
        assert 0.0 <= metrics.intent_consistency <= 1.0
    
    def test_evaluate_overall(self):
        """Test overall evaluation."""
        # Create mock data
        query = self.golden_qa_sets.queries[0]
        answer = self.golden_qa_sets.answers[0]
        
        retrieval_results = [
            {"score": 0.9, "title": "Test Document 1", "content": "Test content 1"},
            {"score": 0.7, "title": "Test Document 2", "content": "Test content 2"}
        ]
        
        draft_data = {
            "confidence": 0.8,
            "citations": [
                {
                    "uri": "https://example.com/doc1",
                    "anchor": "Art. 1",
                    "title": "Test Document 1",
                    "snippet": "Test snippet 1",
                    "score": 0.9
                }
            ]
        }
        
        pii_data = {
            "detected_pii": [{"type": "cpf", "value": "123.456.789-00"}],
            "tokenized_pii": {"PARTY_1_CPF": "token_cpf_12345678900"},
            "detokenized_pii": {"PARTY_1_CPF": "123.456.789-00"},
            "draft_content": "Procuração para PARTY_1_NAME, CPF PARTY_1_CPF"
        }
        
        intent_data = {
            "intent": {
                "act_type": "procuração",
                "parties": [{"role": "outorgante", "pii_extracted": ["João Silva"]}],
                "metadata": {"purpose": "venda de imóvel"}
            },
            "pii_extracted": [{"type": "name", "value": "João Silva"}],
            "confidence": 0.9
        }
        
        # Evaluate overall
        metrics = self.rag_evaluator.evaluate_overall(
            query.query, retrieval_results, draft_data, pii_data, intent_data, query, answer
        )
        
        # Check metrics
        assert 0.0 <= metrics.overall_score <= 1.0
        assert metrics.retrieval_metrics is not None
        assert metrics.grounding_metrics is not None
        assert metrics.pii_metrics is not None
        assert metrics.intent_metrics is not None
    
    def test_calculate_ndcg(self):
        """Test nDCG calculation."""
        # Test with perfect scores
        perfect_scores = [1.0, 1.0, 1.0, 1.0, 1.0]
        ndcg = self.rag_evaluator._calculate_ndcg(perfect_scores)
        assert ndcg == 1.0
        
        # Test with decreasing scores
        decreasing_scores = [1.0, 0.8, 0.6, 0.4, 0.2]
        ndcg = self.rag_evaluator._calculate_ndcg(decreasing_scores)
        assert 0.0 <= ndcg <= 1.0
        
        # Test with empty scores
        empty_scores = []
        ndcg = self.rag_evaluator._calculate_ndcg(empty_scores)
        assert ndcg == 0.0
    
    def test_calculate_precision_recall(self):
        """Test precision and recall calculation."""
        # Create mock results
        results = [
            {"score": 0.9, "title": "Test Document 1", "content": "Test content 1"},
            {"score": 0.7, "title": "Test Document 2", "content": "Test content 2"},
            {"score": 0.5, "title": "Test Document 3", "content": "Test content 3"},
            {"score": 0.3, "title": "Test Document 4", "content": "Test content 4"},
            {"score": 0.1, "title": "Test Document 5", "content": "Test content 5"}
        ]
        
        # Get a test query
        query = self.golden_qa_sets.queries[0]
        
        # Calculate precision and recall
        precision, recall = self.rag_evaluator._calculate_precision_recall(results, query)
        
        # Check metrics
        assert 0.0 <= precision <= 1.0
        assert 0.0 <= recall <= 1.0
    
    def test_citations_match(self):
        """Test citation matching."""
        # Test matching citations
        citation1 = {
            "uri": "https://example.com/doc1",
            "anchor": "Art. 1",
            "title": "Test Document 1"
        }
        citation2 = {
            "uri": "https://example.com/doc1",
            "anchor": "Art. 1",
            "title": "Test Document 1"
        }
        
        assert self.rag_evaluator._citations_match(citation1, citation2)
        
        # Test non-matching citations
        citation3 = {
            "uri": "https://example.com/doc2",
            "anchor": "Art. 2",
            "title": "Test Document 2"
        }
        
        assert not self.rag_evaluator._citations_match(citation1, citation3)


class TestEvaluationRunner:
    """Test evaluation runner functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluation_runner = get_evaluation_runner()
    
    def test_filter_queries(self):
        """Test query filtering."""
        # Test filtering by category
        procuração_queries = self.evaluation_runner._filter_queries(
            categories=["procuração"]
        )
        assert len(procuração_queries) > 0
        for query in procuração_queries:
            assert query.category == "procuração"
        
        # Test filtering by difficulty
        easy_queries = self.evaluation_runner._filter_queries(
            difficulties=["easy"]
        )
        assert len(easy_queries) > 0
        for query in easy_queries:
            assert query.difficulty == "easy"
        
        # Test limiting number of queries
        limited_queries = self.evaluation_runner._filter_queries(max_queries=5)
        assert len(limited_queries) <= 5
    
    def test_calculate_std_dev(self):
        """Test standard deviation calculation."""
        # Test with known values
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        std_dev = self.evaluation_runner._calculate_std_dev(values)
        assert std_dev > 0.0
        
        # Test with single value
        single_value = [1.0]
        std_dev = self.evaluation_runner._calculate_std_dev(single_value)
        assert std_dev == 0.0
        
        # Test with empty list
        empty_values = []
        std_dev = self.evaluation_runner._calculate_std_dev(empty_values)
        assert std_dev == 0.0
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Test with good performance
        good_metrics = {
            "overall_scores": {"mean": 0.8, "std": 0.1},
            "retrieval_metrics": {"hit_at_5_mean": 0.8},
            "grounding_metrics": {"grounding_confidence_mean": 0.8},
            "pii_metrics": {"pii_accuracy_mean": 0.9},
            "intent_metrics": {"act_type_accuracy_mean": 0.9},
            "category_metrics": {"procuração": {"mean_score": 0.8}},
            "difficulty_metrics": {"hard": {"mean_score": 0.6}}
        }
        
        recommendations = self.evaluation_runner._generate_recommendations(good_metrics)
        assert len(recommendations) > 0
        
        # Test with poor performance
        poor_metrics = {
            "overall_scores": {"mean": 0.3, "std": 0.2},
            "retrieval_metrics": {"hit_at_5_mean": 0.2},
            "grounding_metrics": {"grounding_confidence_mean": 0.2},
            "pii_metrics": {"pii_accuracy_mean": 0.5},
            "intent_metrics": {"act_type_accuracy_mean": 0.5},
            "category_metrics": {"procuração": {"mean_score": 0.2}},
            "difficulty_metrics": {"hard": {"mean_score": 0.1}}
        }
        
        recommendations = self.evaluation_runner._generate_recommendations(poor_metrics)
        assert len(recommendations) > 0
        assert any("poor" in rec.lower() or "improve" in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_evaluate_single_query_mock(self):
        """Test single query evaluation with mocked services."""
        # Get a test query
        query = self.evaluation_runner.golden_qa_sets.queries[0]
        
        # Mock HTTP clients
        mock_lexnode_client = Mock()
        mock_intent_engine_client = Mock()
        mock_notarius_client = Mock()
        
        # Mock responses
        mock_lexnode_client.post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "results": [
                    {"score": 0.9, "title": "Test Document 1", "content": "Test content 1"}
                ]
            }
        )
        
        mock_intent_engine_client.post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "intent": {
                    "act_type": "procuração",
                    "parties": [{"role": "outorgante", "pii_extracted": ["João Silva"]}],
                    "metadata": {"purpose": "venda de imóvel"}
                },
                "pii_extracted": [{"type": "name", "value": "João Silva"}],
                "confidence": 0.9
            }
        )
        
        mock_notarius_client.post.return_value = Mock(
            status_code=201,
            json=lambda: {"minuta_id": "test-minuta-id"}
        )
        
        mock_notarius_client.get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "corpo_md": "Procuração para PARTY_1_NAME, CPF PARTY_1_CPF",
                "variaveis_json": {
                    "PARTY_1_NAME": "token_joao_silva",
                    "PARTY_1_CPF": "token_cpf_12345678900"
                }
            }
        )
        
        # Evaluate single query
        result = await self.evaluation_runner._evaluate_single_query(
            query, mock_lexnode_client, mock_intent_engine_client, mock_notarius_client
        )
        
        # Check result
        assert "query" in result
        assert "query_metadata" in result
        assert "retrieval_results" in result
        assert "draft_data" in result
        assert "intent_data" in result
        assert "pii_data" in result
        assert "overall_metrics" in result
        assert "evaluation_time" in result
        assert "timestamp" in result
        
        # Check that services were called
        assert mock_lexnode_client.post.called
        assert mock_intent_engine_client.post.called
        assert mock_notarius_client.post.called
        assert mock_notarius_client.get.called
