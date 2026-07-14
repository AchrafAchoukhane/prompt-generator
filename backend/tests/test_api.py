def test_health_endpoint(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_complete_optimization_workflow_and_history(client) -> None:
    prompt = "Rédige un email pour annoncer notre nouveau produit"
    created = client.post("/api/v1/optimizations", json={"prompt": prompt})

    assert created.status_code == 201
    body = created.json()
    assert body["original_prompt"] == prompt
    assert body["task_type"] == "Writing"
    assert body["optimized_score"] > body["original_score"]
    assert body["optimized_score"] <= 82
    assert body["optimized_prompt"]
    assert body["improvements"]
    assert body["provider"] == "local"

    history = client.get("/api/v1/optimizations")
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["id"] == body["id"]

    detail = client.get(f"/api/v1/optimizations/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["optimized_prompt"] == body["optimized_prompt"]


def test_prompt_validation(client) -> None:
    response = client.post("/api/v1/optimizations", json={"prompt": "x"})
    assert response.status_code == 422
