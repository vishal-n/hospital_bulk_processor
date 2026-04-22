from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validate_csv_success() -> None:
    csv_content = "name,address,phone\nGeneral Hospital,123 Main St,555-1234\n"
    response = client.post(
        "/hospitals/validate-csv",
        files={"file": ("hospitals.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["total_hospitals"] == 1


def test_bulk_create_success(monkeypatch) -> None:
    async def fake_create_hospital(payload):
        return {"id": 123, **payload}

    async def fake_activate_batch(batch_id):
        return {"batch_id": batch_id, "activated": True}

    monkeypatch.setattr("app.main.directory_client.create_hospital", fake_create_hospital)
    monkeypatch.setattr("app.main.directory_client.activate_batch", fake_activate_batch)

    csv_content = "name,address,phone\nGeneral Hospital,123 Main St,555-1234\n"
    response = client.post(
        "/hospitals/bulk",
        files={"file": ("hospitals.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_hospitals"] == 1
    assert payload["processed_hospitals"] == 1
    assert payload["failed_hospitals"] == 0
    assert payload["batch_activated"] is True
