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
