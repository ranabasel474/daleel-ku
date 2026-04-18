import uuid
from unittest import mock

#Checks that the health endpoint returns 200
def test_health_check(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "running"
    assert "system" in data

#Checks that creating a session returns 201 and a valid session ID
def test_create_session(client):
    fake_id = str(uuid.uuid4())

    mock_result = mock.MagicMock()
    mock_result.data = [{"session_id": fake_id}]

    #Patch the name used inside routes.chat
    with mock.patch("routes.chat.supabase_admin") as mock_admin:
        mock_admin.table.return_value.insert.return_value.execute.return_value = mock_result
        res = client.post("/api/session")

    assert res.status_code == 201
    data = res.get_json()
    assert "session_id" in data
    uuid.UUID(data["session_id"])

#Checks that a valid query returns 200 and a response
def test_query_valid(client):
    mock_log = mock.MagicMock()
    mock_log.data = []

    with mock.patch("routes.chat.detect_query_type", return_value="general"), \
         mock.patch("routes.chat.search_query", return_value="some retrieved context"), \
         mock.patch("routes.chat.generate_response",
                    return_value={"answer": "Test answer.", "was_answered": True}), \
         mock.patch("routes.chat.supabase_admin") as mock_admin:

        mock_admin.table.return_value.insert.return_value.execute.return_value = mock_log

        res = client.post(
            "/api/query",
            json={"message": "What are the admission requirements?"},
        )

    assert res.status_code == 200
    data = res.get_json()
    assert "response" in data
    assert data["response"] == "Test answer."
    assert data["was_answered"] is True

#Checks that an empty query returns 400
def test_query_empty_message(client):
    res = client.post("/api/query", json={"message": ""})
    assert res.status_code == 400
    assert "error" in res.get_json()

#Checks that an overly long query (>1000 characters) returns 400
def test_query_too_long(client):
    res = client.post("/api/query", json={"message": "a" * 1001})
    assert res.status_code == 400
    assert "error" in res.get_json()

#Checks that admin documents return 401 without auth
def test_admin_documents_no_auth(client):
    res = client.get("/api/admin/documents")
    assert res.status_code == 401
    assert "error" in res.get_json()
