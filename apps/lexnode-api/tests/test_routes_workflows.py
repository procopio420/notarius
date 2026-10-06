"""High-level workflow tests for LexNode API routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main import app
from app.routes import retrieval as retrieval_routes
from app.routes import indexer as indexer_routes
from app.routes import crawler as crawler_routes
from app.services.database import get_db


pytestmark = pytest.mark.usefixtures("client")


@pytest.fixture
def override_db():
    """Override the database dependency with a dummy session."""

    async def _override():
        yield MagicMock(name="session")

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


def test_retrieve_documents_success(client, override_db):
    results = [
        {"doc_id": "doc-1", "score": 0.92},
        {"doc_id": "doc-2", "score": 0.81},
    ]

    retrieval_mock = AsyncMock(return_value=results)

    with patch.object(retrieval_routes.retrieval_service, "retrieve", retrieval_mock):
        response = client.post(
            "/api/v1/lexnode/retrieve",
            json={
                "query": "procuração pública",
                "constraints": {"jurisdiction": "RJ", "document_types": ["procuração"]},
                "top_k": 5,
            },
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["hits"] == results
    assert data["trace"]["results_count"] == len(results)

    retrieval_mock.assert_awaited_once()
    kwargs = retrieval_mock.await_args.kwargs
    assert kwargs["query"] == "procuração pública"
    assert kwargs["jurisdiction"] == "RJ"
    assert kwargs["document_types"] == ["procuração"]
    assert kwargs["limit"] == 5


def test_retrieve_documents_failure(client, override_db):
    retrieval_mock = AsyncMock(side_effect=RuntimeError("boom"))

    with patch.object(retrieval_routes.retrieval_service, "retrieve", retrieval_mock):
        response = client.post(
            "/api/v1/lexnode/retrieve",
            json={"query": "procuração pública"},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Retrieval failed"
    retrieval_mock.assert_awaited_once()


def test_retrieve_template_success(client, override_db):
    templates = [
        {"id": "tpl-1", "document_type": "procuracao", "relevance_score": 0.9},
    ]
    finder_mock = AsyncMock(return_value=templates)

    with patch.object(
        retrieval_routes.template_matcher,
        "find_template_by_type_and_jurisdiction",
        finder_mock,
    ):
        response = client.post(
            "/api/v1/lexnode/retrieve-template",
            json={
                "document_type": "procuracao",
                "jurisdiction": "RJ",
                "limit": 3,
            },
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["templates"] == templates
    finder_mock.assert_awaited_once()
    kwargs = finder_mock.await_args.kwargs
    assert kwargs["document_type"] == "procuracao"
    assert kwargs["jurisdiction"] == "RJ"
    assert kwargs["limit"] == 3


def test_grounded_draft_success(client, override_db):
    sections = [
        {"title": "Qualificação", "confidence": 0.9},
        {"title": "Cláusulas", "confidence": 0.8},
    ]

    metrics_mock = MagicMock()
    metrics_mock.record_lexnode_retrieve = MagicMock()
    metrics_mock.record_error = MagicMock()

    with patch(
        "app.routes.retrieval.get_metrics_collector",
        return_value=metrics_mock,
        create=True,
    ), patch(
        "app.routes.retrieval.get_correlation_id",
        return_value="corr-123",
        create=True,
    ), patch.object(
        retrieval_routes,
        "_generate_draft_sections",
        AsyncMock(return_value=sections),
    ):
        response = client.post(
            "/api/v1/lexnode/grounded-draft",
            json={
                "act_type": "procuracao",
                "variables": {"PARTY_1_NAME": "Fulano"},
                "constraints": {"jurisdiction": "RJ"},
            },
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["sections"] == sections
    assert data["confidence"] == pytest.approx(0.85)
    metrics_mock.record_lexnode_retrieve.assert_called_once()
    metrics_mock.record_error.assert_not_called()


def test_grounded_draft_failure_records_error(client, override_db):
    metrics_mock = MagicMock()
    metrics_mock.record_lexnode_retrieve = MagicMock()
    metrics_mock.record_error = MagicMock()

    with patch(
        "app.routes.retrieval.get_metrics_collector",
        return_value=metrics_mock,
        create=True,
    ), patch(
        "app.routes.retrieval.get_correlation_id",
        return_value="corr-123",
        create=True,
    ), patch.object(
        retrieval_routes,
        "_generate_draft_sections",
        AsyncMock(side_effect=RuntimeError("generation failed")),
    ):
        response = client.post(
            "/api/v1/lexnode/grounded-draft",
            json={
                "act_type": "procuracao",
                "variables": {},
            },
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Grounded draft generation failed"
    metrics_mock.record_error.assert_called_once_with("grounded_draft_error")


def test_index_document_success(client, override_db):
    with patch.object(
        indexer_routes.normalizer_service,
        "normalize_document",
        return_value={"title": "doc"},
    ) as normalize_mock, patch.object(
        indexer_routes.indexer_service,
        "index_document",
        AsyncMock(return_value="doc-123"),
    ) as index_mock:
        response = client.post(
            "/api/v1/lexnode/index",
            json={"document": {"title": "doc"}},
        )

    assert response.status_code == 200
    data = response.json()
    assert data == {"document_id": "doc-123", "status": "indexed"}
    normalize_mock.assert_called_once()
    index_mock.assert_awaited_once()


def test_index_batch_success(client, override_db):
    with patch.object(
        indexer_routes.normalizer_service,
        "normalize_document",
        side_effect=lambda doc: {**doc, "normalized": True},
    ) as normalize_mock, patch.object(
        indexer_routes.indexer_service,
        "index_batch",
        AsyncMock(return_value=["doc-1", "doc-2"]),
    ) as index_mock:
        response = client.post(
            "/api/v1/lexnode/index-batch",
            json={"documents": [{"title": "A"}, {"title": "B"}]},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["indexed_count"] == 2
    assert data["failed_count"] == 0
    assert data["document_ids"] == ["doc-1", "doc-2"]
    assert normalize_mock.call_count == 2
    index_mock.assert_awaited_once()


def test_crawl_invalid_source(client, override_db):
    response = client.post(
        "/api/v1/lexnode/crawl",
        json={"source": "invalid"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid source. Must be 'cnj' or 'cgj_rj'"


def test_crawl_start_job_submits_background_task(client, override_db):
    with patch.object(
        crawler_routes, "_run_crawl_job", new=AsyncMock()
    ) as crawl_mock:
        response = client.post(
            "/api/v1/lexnode/crawl",
            json={"source": "cnj"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    assert data["job_id"].startswith("crawl_cnj_")
    crawl_mock.assert_awaited_once()
    kwargs = crawl_mock.await_args.kwargs
    assert kwargs["source"] == "cnj"
    assert kwargs["job_id"] == data["job_id"]


def test_crawl_status_returns_mock_payload(client, override_db):
    response = client.get("/api/v1/lexnode/crawl/demo-job/status")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "demo-job"
    assert data["status"] == "running"
    assert data["documents_found"] == 0
    assert data["documents_processed"] == 0


def test_list_crawl_sources(client):
    response = client.get("/api/v1/lexnode/crawl/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert any(source["id"] == "cnj" for source in data["sources"])

