# TP DevOps - Docker, Compose et Registry

[![CI](https://github.com/Cronix2/tp-github-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/Cronix2/tp-github-actions/actions/workflows/ci.yml)

Application Flask conteneurisée réalisée dans le cadre du TP DevOps.

Le projet reprend le même dépôt que le TP GitHub Actions et ajoute la conteneurisation Docker, l'optimisation de l'image, Docker Compose, Redis, des healthchecks et la publication de l'image sur GitHub Container Registry.

## Architecture

L'application est composée de deux services :

- `web` : application Flask exécutée avec Gunicorn
- `redis` : stockage persistant du compteur de visites

Les deux services communiquent sur un réseau Docker dédié.

Un volume Docker persistant est associé à Redis afin de conserver les données.

## Endpoints

### Healthcheck

```text
GET /health
```

Réponse :

```json
{
  "status": "ok",
  "redis": "ok"
}
```

Si Redis est indisponible, l'endpoint renvoie HTTP 503 avec :

{
  "status": "error",
  "redis": "unavailable"
}


### Statut

```text
GET /status
```

Réponse :

```json
{
  "service": "projet-devops-groupe-demo",
  "version": "1.0"
}
```

### Compteur de visites

```text
GET /visits
```

Le compteur est incrémenté et stocké dans Redis.

Exemple :

```json
{
  "visits": 4
}
```

Le compteur reste disponible après le redémarrage du service `web`.

## Docker

### Construction

```bash
docker build -t tp-devops:multistage .
```

### Lancement

```bash
docker run --rm -p 5000:5000 tp-devops:multistage
```

L'application est accessible sur le port `5000`.

## Optimisation de l'image

Une première image utilisant `python:3.12` avait une taille de contenu d'environ :

```text
418 MB
```

Après passage à un Dockerfile multi-stage avec `python:3.12-slim`, la taille est passée à environ :

```text
54.2 MB
```

Cela représente une réduction d'environ 87 %.

L'application est également exécutée avec un utilisateur non-root `appuser` et Gunicorn est utilisé à la place du serveur de développement Flask.

## Docker Compose

Démarrage de l'application complète :

```bash
docker compose up -d --build
```

Vérification :

```bash
docker compose ps
```

Arrêt :

```bash
docker compose down
```

Le fichier Compose configure :

- le service Flask `web`
- le service `redis`
- un réseau Docker dédié
- un volume persistant Redis
- un healthcheck Redis avec `redis-cli ping`
- un healthcheck HTTP sur `/health`
- une dépendance conditionnelle permettant à `web` d'attendre que Redis soit healthy

## Tests

Installation des dépendances :

```bash
pip install -r requirements.txt
```

Exécution des tests :

```bash
pytest -v
```

Résultat obtenu :

```text
3 passed
```

Vérification Flake8 :

```bash
flake8 .
```

## Registry

L'image est publiée sur GitHub Container Registry.

Tags disponibles :

```text
ghcr.io/cronix2/tp-github-actions:latest
ghcr.io/cronix2/tp-github-actions:v1.0.0
```

Récupération de l'image :

```bash
docker pull ghcr.io/cronix2/tp-github-actions:v1.0.0
```

L'image versionnée a été supprimée localement puis téléchargée de nouveau depuis GHCR afin de valider sa disponibilité.

## CI

Le dépôt conserve la CI GitHub Actions mise en place lors du TP précédent afin d'exécuter automatiquement les contrôles du projet.