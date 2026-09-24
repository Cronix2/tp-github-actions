#!/bin/sh
set -eu

NGINX_CONF="./deploy/nginx/default.conf"

echo "=== Blue/Green deployment ==="

# Determine the environment currently used by Nginx
if grep -q "web-blue:5000" "$NGINX_CONF"; then
    ACTIVE="blue"
    TARGET="green"
else
    ACTIVE="green"
    TARGET="blue"
fi

echo "Active deployment : $ACTIVE"
echo "Target deployment : $TARGET"

# Find the target container through Docker Compose
TARGET_ID=$(docker compose ps -q "web-$TARGET")

if [ -z "$TARGET_ID" ]; then
    echo "ERROR: web-$TARGET is not running."
    exit 1
fi

# Check target health
echo "Checking health of web-$TARGET..."

STATUS=$(docker inspect \
    --format='{{.State.Health.Status}}' \
    "$TARGET_ID" 2>/dev/null || echo "unknown")

echo "Health status: $STATUS"

if [ "$STATUS" != "healthy" ]; then
    echo "ERROR: web-$TARGET is not healthy."
    exit 1
fi

# Smoke test the target before sending production traffic to it
echo "Running smoke test on web-$TARGET..."

RESULT=$(docker exec starter-app2-nginx-1 \
    wget -qO- "http://web-$TARGET:5000/status")

echo "$RESULT"

if ! echo "$RESULT" | grep -q "\"deploy_color\":\"$TARGET\""; then
    echo "ERROR: smoke test failed."
    exit 1
fi

echo "Smoke test successful."

# Switch Nginx configuration to the target environment
echo "Switching Nginx from $ACTIVE to $TARGET..."

sed -i "s/web-$ACTIVE:5000/web-$TARGET:5000/" "$NGINX_CONF"

# Validate the new Nginx configuration before reloading
if ! docker exec starter-app2-nginx-1 nginx -t; then
    echo "ERROR: invalid Nginx configuration. Rolling back."
    sed -i "s/web-$TARGET:5000/web-$ACTIVE:5000/" "$NGINX_CONF"
    exit 1
fi

# Reload Nginx without stopping the reverse proxy
if ! docker exec starter-app2-nginx-1 nginx -s reload; then
    echo "ERROR: Nginx reload failed. Rolling back."

    sed -i "s/web-$TARGET:5000/web-$ACTIVE:5000/" "$NGINX_CONF"
    docker exec starter-app2-nginx-1 nginx -s reload

    exit 1
fi

echo "Checking deployment through Nginx..."

FINAL_RESULT=""
COUNT=0
MAX_RETRIES=10

while [ "$COUNT" -lt "$MAX_RETRIES" ]; do
    FINAL_RESULT=$(docker exec starter-app2-nginx-1 \
        wget -qO- "http://127.0.0.1/status" 2>/dev/null || true)

    if echo "$FINAL_RESULT" | grep -q "\"deploy_color\":\"$TARGET\""; then
        break
    fi

    COUNT=$((COUNT + 1))
    sleep 1
done

echo "$FINAL_RESULT"

# Roll back if the public endpoint does not expose the target deployment
if ! echo "$FINAL_RESULT" | grep -q "\"deploy_color\":\"$TARGET\""; then
    echo "ERROR: final verification failed. Rolling back."

    sed -i "s/web-$TARGET:5000/web-$ACTIVE:5000/" "$NGINX_CONF"

    docker exec starter-app2-nginx-1 nginx -t
    docker exec starter-app2-nginx-1 nginx -s reload

    exit 1
fi

echo "Deployment successful: $ACTIVE -> $TARGET"
