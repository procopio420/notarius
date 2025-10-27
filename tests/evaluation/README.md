# RAG Evaluation System

This package provides a comprehensive evaluation system for the RAG (Retrieval-Augmented Generation) components of the Notarius system.

## Overview

The RAG evaluation system consists of three main components:

1. **Golden Q&A Sets** - Curated test cases with expected inputs and outputs
2. **RAG Metrics** - Comprehensive metrics for evaluating different aspects of the system
3. **Evaluation Runner** - Automated evaluation framework that runs tests and generates reports

## Components

### Golden Q&A Sets (`golden_qa_sets.py`)

Contains curated test cases for evaluating the system:

- **GoldenQuery**: Represents a test query with expected outcomes
- **GoldenAnswer**: Represents the expected answer for a query
- **GoldenQASets**: Collection of all test cases

#### Query Categories:
- Procuração (Power of Attorney)
- Contrato (Contract)
- Testamento (Will)
- Escritura (Deed)
- Certidão (Certificate)

#### Difficulty Levels:
- Easy: Simple, straightforward queries
- Medium: Moderate complexity queries
- Hard: Complex queries with multiple requirements

#### Jurisdictions:
- RJ (Rio de Janeiro)
- SP (São Paulo)

### RAG Metrics (`rag_metrics.py`)

Comprehensive metrics for evaluating system performance:

#### Retrieval Metrics:
- Hit@K: Precision at different K values
- MRR: Mean Reciprocal Rank
- nDCG: Normalized Discounted Cumulative Gain
- Precision/Recall: Standard information retrieval metrics

#### Grounding Metrics:
- Grounding Confidence: Overall confidence in grounding
- Citation Quality: Quality of retrieved citations
- Citation Coverage: Coverage of expected citations
- False Grounding Rate: Rate of incorrect grounding
- Grounding Consistency: Consistency of grounding results

#### PII Protection Metrics:
- PII Detection Rate: Rate of PII detection
- PII Tokenization Rate: Rate of successful tokenization
- PII Detokenization Rate: Rate of successful detokenization
- PII Leak Rate: Rate of PII leaks
- PII Accuracy: Overall PII protection accuracy

#### Intent Parsing Metrics:
- Act Type Accuracy: Accuracy of act type identification
- Entity Extraction Accuracy: Accuracy of entity extraction
- Confidence Calibration: Calibration of confidence scores
- Intent Consistency: Consistency of intent parsing

### Evaluation Runner (`evaluation_runner.py`)

Automated evaluation framework:

- **EvaluationRunner**: Main evaluation class
- **run_evaluation()**: Function to run evaluation with default settings
- **Evaluation Report**: Comprehensive report with metrics and recommendations

## Usage

### Basic Usage

```python
from tests.evaluation import run_evaluation

# Run evaluation with default settings
report = await run_evaluation()

# Run evaluation with custom settings
report = await run_evaluation(
    max_queries=50,
    categories=["procuração", "contrato"],
    difficulties=["easy", "medium"],
    save_report=True,
    print_summary=True
)
```

### Advanced Usage

```python
from tests.evaluation import get_evaluation_runner, get_rag_evaluator

# Get evaluation runner
runner = get_evaluation_runner()

# Run evaluation
report = await runner.run_evaluation(
    max_queries=100,
    categories=["procuração"],
    difficulties=["hard"]
)

# Save report
runner.save_report(report, "custom_report.json")

# Print summary
runner.print_summary(report)
```

### Custom Evaluation

```python
from tests.evaluation import get_rag_evaluator, get_golden_qa_sets

# Get evaluator and test data
evaluator = get_rag_evaluator()
golden_qa_sets = get_golden_qa_sets()

# Get test query
query = golden_qa_sets.queries[0]

# Evaluate retrieval
retrieval_results = [...]  # Your retrieval results
retrieval_metrics = evaluator.evaluate_retrieval(
    query.query, retrieval_results, query
)

# Evaluate grounding
draft_data = {...}  # Your draft data
answer = golden_qa_sets.get_answer_by_query_id(query.query)
grounding_metrics = evaluator.evaluate_grounding(draft_data, answer)

# Evaluate overall
overall_metrics = evaluator.evaluate_overall(
    query.query, retrieval_results, draft_data, pii_data, intent_data, query, answer
)
```

## Evaluation Report

The evaluation report includes:

### Summary
- Total queries evaluated
- Success/failure rates
- Average evaluation time
- Overall performance score

### Component Performance
- Retrieval performance metrics
- Grounding performance metrics
- PII protection performance metrics
- Intent parsing performance metrics

### Category Performance
- Performance by document category
- Performance by difficulty level
- Performance by jurisdiction

### Recommendations
- Actionable recommendations for improvement
- Performance thresholds and targets
- Specific areas needing attention

## Running Evaluations

### Command Line

```bash
# Run evaluation with default settings
python -m tests.evaluation.evaluation_runner

# Run evaluation with custom settings
python -m tests.evaluation.evaluation_runner --max-queries 50 --categories procuração,contrato
```

### Programmatic

```python
import asyncio
from tests.evaluation import run_evaluation

# Run evaluation
asyncio.run(run_evaluation(max_queries=100))
```

## Configuration

### Environment Variables

- `LEXNODE_URL`: URL for LexNode service (default: http://localhost:8001)
- `INTENT_ENGINE_URL`: URL for Intent Engine service (default: http://localhost:8003)
- `NOTARIUS_URL`: URL for Notarius service (default: http://localhost:8000)

### Custom Settings

```python
# Custom evaluation settings
report = await run_evaluation(
    max_queries=100,
    categories=["procuração", "contrato"],
    difficulties=["easy", "medium", "hard"],
    save_report=True,
    print_summary=True
)
```

## Metrics Interpretation

### Overall Score
- 0.9-1.0: Excellent performance
- 0.8-0.9: Good performance
- 0.7-0.8: Acceptable performance
- 0.6-0.7: Below average performance
- 0.0-0.6: Poor performance

### Component Scores
- Each component is scored 0.0-1.0
- Higher scores indicate better performance
- Component scores are weighted in overall score calculation

### Recommendations
- Based on performance thresholds
- Specific to identified weaknesses
- Actionable and prioritized

## Adding New Test Cases

### Adding New Queries

```python
from tests.evaluation.golden_qa_sets import GoldenQuery

# Create new query
new_query = GoldenQuery(
    query="Fazer procuração para João Silva, CPF 123.456.789-00",
    expected_act_type="procuração",
    expected_entities=["João Silva", "123.456.789-00"],
    expected_jurisdiction="rj",
    expected_document_type="procuração",
    expected_confidence_threshold=0.9,
    expected_citations_count=3,
    expected_grounding_confidence=0.85,
    expected_pii_types=["cpf", "name"],
    expected_metadata={"purpose": "venda de imóvel"},
    difficulty="easy",
    category="procuração"
)

# Add to golden Q&A sets
golden_qa_sets.queries.append(new_query)
```

### Adding New Answers

```python
from tests.evaluation.golden_qa_sets import GoldenAnswer

# Create new answer
new_answer = GoldenAnswer(
    query_id="procuração_002",
    expected_draft_structure={
        "title": "PROCURAÇÃO",
        "sections": ["outorgante", "outorgado", "poderes"],
        "required_clauses": ["identificação das partes", "poderes outorgados"]
    },
    expected_citations=[
        {
            "uri": "https://example.com/doc1",
            "anchor": "Art. 1",
            "title": "Test Document",
            "snippet": "Test snippet",
            "score": 0.9
        }
    ],
    expected_confidence_score=0.9,
    expected_grounding_confidence=0.85,
    expected_pii_tokenization={
        "PARTY_1_NAME": "token_joao_silva",
        "PARTY_1_CPF": "token_cpf_12345678900"
    },
    expected_metadata={"purpose": "venda de imóvel"}
)

# Add to golden Q&A sets
golden_qa_sets.answers.append(new_answer)
```

## Best Practices

1. **Regular Evaluation**: Run evaluations regularly to track performance
2. **Comprehensive Testing**: Test across all categories and difficulty levels
3. **Performance Monitoring**: Monitor metrics over time for trends
4. **Actionable Recommendations**: Focus on recommendations that can be implemented
5. **Baseline Establishment**: Establish performance baselines for comparison
6. **Continuous Improvement**: Use evaluation results to guide system improvements

## Troubleshooting

### Common Issues

1. **Service Unavailable**: Ensure all services are running and accessible
2. **Timeout Errors**: Increase timeout values for slow services
3. **Memory Issues**: Reduce max_queries for large evaluations
4. **Network Issues**: Check network connectivity between services

### Debug Mode

```python
# Enable debug mode for detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run evaluation with debug output
report = await run_evaluation(max_queries=10)
```

## Contributing

When adding new test cases or metrics:

1. Follow the existing patterns and conventions
2. Add comprehensive tests for new functionality
3. Update documentation as needed
4. Ensure backward compatibility
5. Test with various scenarios and edge cases
