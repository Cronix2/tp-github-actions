import redis

from app import alert_threshold, sanitize_input, app


def test_alert_threshold():
    assert alert_threshold() == 25


def test_sanitize_input_escapes_html():
    assert sanitize_input("<script>") == "&lt;script&gt;"


def test_health_endpoint_when_redis_available(monkeypatch):
    class FakeRedis:
        def ping(self):
            return True

    monkeypatch.setattr("app.get_redis_client", lambda: FakeRedis())

    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "redis": "ok",
    }


def test_health_endpoint_when_redis_unavailable(monkeypatch):
    class FakeRedis:
        def ping(self):
            raise redis.RedisError("Redis unavailable")

    monkeypatch.setattr("app.get_redis_client", lambda: FakeRedis())

    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json() == {
        "status": "error",
        "redis": "unavailable",
    }


def test_metrics_endpoint_exposes_http_counter():
    client = app.test_client()

    client.get("/status")
    response = client.get("/metrics")

    assert response.status_code == 200

    metrics = response.get_data(as_text=True)

    assert "http_requests_total" in metrics
    assert 'endpoint="/status"' in metrics
    assert 'method="GET"' in metrics
    assert 'status="200"' in metrics


def test_metrics_endpoint_does_not_count_itself():
    client = app.test_client()

    first_response = client.get("/metrics")
    first_metrics = first_response.get_data(as_text=True)

    second_response = client.get("/metrics")
    second_metrics = second_response.get_data(as_text=True)

    first_lines = sorted(
        line
        for line in first_metrics.splitlines()
        if line.startswith("http_requests_total")
    )

    second_lines = sorted(
        line
        for line in second_metrics.splitlines()
        if line.startswith("http_requests_total")
    )

    assert first_lines == second_lines
    assert 'endpoint="/metrics"' not in second_metrics
