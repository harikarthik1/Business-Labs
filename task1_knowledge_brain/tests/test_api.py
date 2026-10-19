import os
import pytest
from fastapi.testclient import TestClient
from task1_knowledge_brain.app.main import app
from task1_knowledge_brain.app.storage import db
from task1_knowledge_brain.app.retrieval import retriever

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_data():
    # Insert known test articles into SQLite db with a clean slate
    db.init_db()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM expert_tasks;")
        conn.execute("DELETE FROM chunks;")
        conn.execute("DELETE FROM articles;")
        conn.commit()
    db.upsert_article(
        url="https://support.brilliantdirectories.com/support/solutions/articles/5000558357-can-i-send-a-mass-email",
        title="Can I Send A Mass Email Campaign Using Brilliant Directories?",
        body_text="Brilliant Directories has an integrated newsletter and mass email marketing feature located under My Members > Send Newsletter. You can send email blasts to all registered members or specific membership tiers.",
        published_at="2024-01-01T00:00:00Z",
        images=["https://support.brilliantdirectories.com/images/email-campaign.png"],
    )
    db.upsert_article(
        url="https://support.brilliantdirectories.com/support/solutions/articles/5000558401-how-to-import-categories",
        title="How To Import Categories Via CSV File",
        body_text="To import member categories into Brilliant Directories, navigate to My Members > Member Categories > Import Categories. Ensure your CSV file has headers for Top Category, Sub Category, and Sub-Sub Category.",
        published_at="2024-02-01T00:00:00Z",
        images=[],
    )
    retriever.build_index()

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["articles_count"] >= 2
    assert data["vector_store_ready"] is True

def test_query_successful_with_citation():
    response = client.post(
        "/query",
        json={"query": "Can I send a mass email campaign to members?", "top_k": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["insufficient_evidence"] is False
    assert len(data["sources"]) > 0
    assert "email" in data["sources"][0]["title"].lower()
    assert data["sources"][0]["relevance_score"] > 0.35
    assert len(data["sources"][0]["images"]) > 0

def test_query_insufficient_evidence_for_unrelated_topic():
    # Query completely outside Brilliant Directories knowledge
    response = client.post(
        "/query",
        json={"query": "What is the warp drive warp factor speed limit in Starfleet?", "top_k": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["insufficient_evidence"] is True
    assert len(data["sources"]) == 0
    assert "INSUFFICIENT_EVIDENCE" in data["answer"] or "insufficient" in data["answer"].lower()

def test_expert_review_lifecycle():
    # 1. Ask question not yet answered
    unknown_q = "How do I connect Brilliant Directories to custom COBOL mainframe?"
    initial_query = client.post("/query", json={"query": unknown_q})
    assert initial_query.status_code == 200
    assert initial_query.json()["insufficient_evidence"] is True

    # 2. Create expert task
    create_res = client.post(
        "/expert-tasks",
        json={
            "question": unknown_q,
            "context": "Enterprise client ticket #4092",
            "suggested_answer": None
        }
    )
    assert create_res.status_code == 201
    task_data = create_res.json()
    task_id = task_data["task_id"]
    assert task_data["status"] == "pending_review"

    # 3. Expert answers and approves task
    approved_text = "To integrate Brilliant Directories with COBOL mainframes, use the Webhook Notification Manager to dispatch member event payloads to an intermediate API bridge."
    answer_res = client.post(
        f"/expert-tasks/{task_id}/answer",
        json={
            "approved_answer": approved_text,
            "expert_name": "Chief Architect",
            "source_reference": "Verified Enterprise Architecture"
        }
    )
    assert answer_res.status_code == 200
    assert answer_res.json()["status"] == "incorporated"

    # 4. Subsequent query now finds the answer and cites the approved expert response!
    followup_query = client.post("/query", json={"query": "connect Brilliant Directories to custom COBOL mainframe"})
    assert followup_query.status_code == 200
    f_data = followup_query.json()
    assert f_data["insufficient_evidence"] is False
    assert len(f_data["sources"]) > 0
    assert "COBOL" in f_data["sources"][0]["title"] or "COBOL" in f_data["answer"]
