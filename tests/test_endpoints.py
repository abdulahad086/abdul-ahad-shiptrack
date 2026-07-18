def test_create_application(client, auth_headers):
    payload = {
        "name": "checkout-api",
        "repo_url": "https://github.com/acme/checkout-api",
    }
    response = client.post("/applications", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "checkout-api"
    assert data["repo_url"] == "https://github.com/acme/checkout-api"
    assert "created_at" in data


def test_create_deployment(client, auth_headers):
    # Create application first
    app_payload = {
        "name": "checkout-api",
        "repo_url": "https://github.com/acme/checkout-api",
    }
    app_resp = client.post("/applications", json=app_payload, headers=auth_headers)
    app_id = app_resp.json()["id"]

    payload = {
        "application_id": app_id,
        "version": "1.4.0",
        "environment": "prod",
        "status": "pending",
    }
    response = client.post("/deployments", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["application_id"] == app_id
    assert data["version"] == "1.4.0"
    assert data["environment"] == "prod"
    assert "deployed_at" in data


def test_bad_semver_rejected(client, auth_headers):
    payload = {
        "application_id": 1,
        "version": "v1.2",
        "environment": "prod",
        "status": "pending",
    }
    response = client.post("/deployments", json=payload, headers=auth_headers)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "version" in data["error"]["message"]


def test_deployment_not_found(client):
    response = client.get("/deployments/99999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert len(data["error"]["message"]) > 0


def test_write_requires_api_key(client):
    payload = {
        "application_id": 1,
        "version": "1.0.0",
        "environment": "prod",
        "status": "pending",
    }
    # No key
    response = client.post("/deployments", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "unauthorized"

    # Wrong key
    response_wrong = client.post(
        "/deployments", json=payload, headers={"X-API-Key": "wrong-key"}
    )
    assert response_wrong.status_code == 401
    data_wrong = response_wrong.json()
    assert data_wrong["error"]["code"] == "unauthorized"

    # GET is public
    response_get = client.get("/deployments")
    assert response_get.status_code == 200


def test_audit_log_written(client, auth_headers, audit_log_path):
    app_payload = {
        "name": "audit-api",
        "repo_url": "https://github.com/acme/audit-api",
    }
    response = client.post("/applications", json=app_payload, headers=auth_headers)
    assert response.status_code == 201
    app_id = response.json()["id"]

    # Assert audit log entry is written
    assert audit_log_path.exists()
    content = audit_log_path.read_text()
    assert "CREATE_APPLICATION" in content
    assert f"application_id={app_id}" in content
    assert "name=audit-api" in content


def test_rollback_creates_new_deployment(client, auth_headers):
    # Create app
    app_payload = {
        "name": "rollback-api",
        "repo_url": "https://github.com/acme/rollback-api",
    }
    app_resp = client.post("/applications", json=app_payload, headers=auth_headers)
    app_id = app_resp.json()["id"]

    # Create succeeded v1.0.0
    client.post(
        "/deployments",
        json={
            "application_id": app_id,
            "version": "1.0.0",
            "environment": "prod",
            "status": "succeeded",
        },
        headers=auth_headers,
    )

    # Create succeeded v2.0.0
    dep2 = client.post(
        "/deployments",
        json={
            "application_id": app_id,
            "version": "2.0.0",
            "environment": "prod",
            "status": "succeeded",
        },
        headers=auth_headers,
    ).json()

    v2_id = dep2["id"]

    # Rollback
    rollback_resp = client.post(f"/deployments/{v2_id}/rollback", headers=auth_headers)
    assert rollback_resp.status_code == 201
    new_dep = rollback_resp.json()

    # Assert a NEW row exists with version == "1.0.0", environment == "prod"
    assert new_dep["version"] == "1.0.0"
    assert new_dep["environment"] == "prod"
    assert new_dep["status"] == "succeeded"
    assert new_dep["id"] != v2_id

    # Assert v2 row now status == "rolled_back"
    v2_resp = client.get(f"/deployments/{v2_id}")
    assert v2_resp.json()["status"] == "rolled_back"


def test_rollback_no_previous_version(client, auth_headers):
    # Create app
    app_payload = {
        "name": "no-prev-api",
        "repo_url": "https://github.com/acme/no-prev-api",
    }
    app_resp = client.post("/applications", json=app_payload, headers=auth_headers)
    app_id = app_resp.json()["id"]

    # Create succeeded v1.0.0
    dep = client.post(
        "/deployments",
        json={
            "application_id": app_id,
            "version": "1.0.0",
            "environment": "prod",
            "status": "succeeded",
        },
        headers=auth_headers,
    ).json()

    v1_id = dep["id"]

    # Get count before rollback
    deps_before = len(client.get("/deployments").json())

    # Rollback
    rollback_resp = client.post(f"/deployments/{v1_id}/rollback", headers=auth_headers)
    assert rollback_resp.status_code == 409
    assert rollback_resp.json()["error"]["code"] == "invalid_rollback"

    # Assert deployment count did not increase
    deps_after = len(client.get("/deployments").json())
    assert deps_before == deps_after
