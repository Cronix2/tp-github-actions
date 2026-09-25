import os

import redis
from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

app = Flask(__name__)

ALERT_THRESHOLD = 25

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP recues",
    ["method", "endpoint", "status"],
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


@app.after_request
def record_request_metrics(response):
    if request.path != "/metrics":
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=request.path,
            status=str(response.status_code),
        ).inc()

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
