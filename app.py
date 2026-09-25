import os
import time

import redis
from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

app = Flask(__name__)

ALERT_THRESHOLD = 25

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP recues",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Temps de traitement des requetes HTTP en secondes",
    ["method", "endpoint"],
)


def get_redis_client():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )


def alert_threshold():
    """Seuil d'alerte au-dessus duquel une notification est declenchee."""
    return ALERT_THRESHOLD


def sanitize_input(value):
    """Echappe les caracteres dangereux d'une entree utilisateur."""
    return value.replace("<", "&lt;").replace(">", "&gt;")


@app.before_request
def start_request_timer():
    if request.path != "/metrics":
        g.request_start_time = time.perf_counter()


@app.after_request
def record_request_metrics(response):
    if request.path != "/metrics":
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=request.path,
            status=str(response.status_code),
        ).inc()

        start_time = getattr(g, "request_start_time", None)

        if start_time is not None:
            duration = time.perf_counter() - start_time

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                endpoint=request.path,
            ).observe(duration)

    return response


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/health")
def health():
    try:
        client = get_redis_client()
        client.ping()
        return jsonify(status="ok", redis="ok"), 200
    except redis.RedisError:
        return jsonify(status="error", redis="unavailable"), 503


@app.route("/status")
def status():
    return jsonify(
        service="projet-devops-groupe-demo",
        version="1.0",
        deploy_color=os.getenv("DEPLOY_COLOR", "unknown"),
        commit_sha=os.getenv("COMMIT_SHA", "unknown"),
    ), 200


@app.route("/visits")
def visits():
    client = get_redis_client()
    count = client.incr("visits")
    return jsonify(visits=count), 200


@app.route("/simulate-error")
def simulate_error():
    return jsonify(
        status="error",
        message="Simulated application error",
    ), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
