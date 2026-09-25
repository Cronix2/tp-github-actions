# TP DevOps - CI/CD et dÃ©ploiement Blue/Green

[![CI](https://github.com/Cronix2/tp-github-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/Cronix2/tp-github-actions/actions/workflows/ci.yml)

Application Flask conteneurisÃ©e avec Docker et intÃ©grÃ©e dans une chaÃ®ne CI/CD GitHub Actions.

Le projet met en Å“uvre :

- une application Flask exÃ©cutÃ©e avec Gunicorn ;
- Redis avec stockage persistant ;
- Docker et Docker Compose ;
- des healthchecks ;
- un reverse proxy Nginx ;
- un dÃ©ploiement Blue/Green ;
- des smoke tests ;
- un rollback automatique ;
- la traÃ§abilitÃ© du commit Git dÃ©ployÃ© ;
- une CI multi-version Python ;
- la publication automatique des images dans GitHub Container Registry.

## Architecture

L'architecture est composÃ©e de quatre services :

- `web-blue` : environnement Blue de l'application Flask ;
- `web-green` : environnement Green de l'application Flask ;
- `nginx` : reverse proxy exposÃ© sur le port 8080 ;
- `redis` : stockage persistant utilisÃ© par l'application.

Nginx dirige le trafic vers l'un des deux environnements applicatifs.

```text
                    +----------------+
                    |     Client     |
                    +-------+--------+
                            |
                            v
                    +----------------+
                    |     Nginx      |
                    |    :8080       |
                    +-------+--------+
                            |
                   Blue ou Green
                      /          \
                     v            v
             +-----------+   +-----------+
             | web-blue  |   | web-green |
             |   :5000   |   |   :5000   |
             +-----+-----+   +-----+-----+
                   \             /
                    \           /
                     v         v
                    +-----------+
                    |   Redis   |
                    |   :6379   |
                    +-----------+Les services communiquent sur le rÃ©seau Docker app-network.

Le volume redis-data assure la persistance des donnÃ©es Redis.

Endpoints
Healthcheck
GET /health

Lorsque Redis est disponible :

{
  "status": "ok",
  "redis": "ok"
}

Lorsque Redis est indisponible, l'application retoune HTTP 503.

Status
GET /status

Exemple :

{
  "commit_sha": "05408a23264e77dfbeb5d24099457279e05e1b6c",
  "deploy_color": "blue",
  "service": "projet-devops-groupe-demo",
  "version": "1.0"
}

deploy_color permet d'identifier l'environnement Blue/Green actuellement servi.

commit_sha permet de vÃ©rifier prÃ©cisÃ©ment la rÃ©vision Git exÃ©cutÃ©e par le conteneur.

Compteur de visites
GET /visits

Le compteur est stockÃ© dans Redis et persiste lors du redÃ©marrage des services applicatifs.

Docker

Construction de l'image :

docker build -t tp-devops:multistage .

Le Dockerfile utilise une construction multi-stage avec une image finale basÃ©e sur python:3.12-slim.

L'application est exÃ©cutÃ©e avec Gunicorn et un utilisateur non-root appuser.

Docker Compose

DÃ©marrage de l'environnement complet :

docker compose up -d --build

VÃ©rification :

docker compose ps

AccÃ¨s Ã  l'application :

http://localhost:8080

ArrÃªt :

docker compose down

Les services web-blue et web-green disposent chacun d'un healthcheck HTTP sur /health.

Redis dispose Ã©galement d'un healthcheck utilisant :

redis-cli ping
DÃ©ploiement Blue/Green

Le script :

deploy/deploy.sh

automatise la bascule entre les environnements Blue et Green.

Il rÃ©alise les opÃ©rations suivantes :

dÃ©termine l'environnement actuellement utilisÃ© par Nginx ;
sÃ©lectionne l'environnement cible ;
vÃ©rifie que le conteneur cible est healthy ;
exÃ©cute un smoke test sur /status ;
vÃ©rifie la couleur de dÃ©ploiement ;
vÃ©rifie le SHA du commit attendu ;
modifie la configuration Nginx ;
valide la configuration avec nginx -t ;
recharge Nginx sans interruption ;
vÃ©rifie le rÃ©sultat via l'endpoint public ;
effectue un rollback automatique en cas d'Ã©chec.

ExÃ©cution :

export COMMIT_SHA=$(git rev-parse HEAD)
./deploy/deploy.sh

Exemple de bascule :

Active deployment : blue
Target deployment : green
Smoke test successful.
Deployment successful: blue -> green
Rollback

Si la vÃ©rification aprÃ¨s bascule Ã©choue, le script restaure automatiquement l'environnement prÃ©cÃ©demment actif.

Le rollback remet la configuration Nginx dans son Ã©tat prÃ©cÃ©dent puis recharge le reverse proxy.

Un rollback Git peut Ã©galement Ãªtre rÃ©alisÃ© avec :

git revert <commit>

La CI reconstruit alors automatiquement l'image correspondant Ã  l'Ã©tat restaurÃ©.

Tests

Installation des dÃ©pendances :

pip install -r requirements.txt

Lint :

flake8 .

Tests :

pytest -v

Ã‰tat actuel :

4 passed
CI/CD GitHub Actions

Le workflow GitHub Actions est exÃ©cutÃ© sur les push et les pull_request.

Les tests sont exÃ©cutÃ©s avec une matrice Python :

Python 3.11
Python 3.12
Python 3.13

Pour chaque version, la CI :

installe les dÃ©pendances ;
exÃ©cute Flake8 ;
exÃ©cute les tests avec couverture.

Le rapport de couverture HTML de Python 3.13 est publiÃ© comme artifact GitHub Actions.

Sur la branche main, aprÃ¨s validation des tests :

test
  |
  v
build-and-push
  |
  v
deploy
GitHub Container Registry

AprÃ¨s validation des tests sur main, l'image Docker est publiÃ©e dans GHCR avec deux tags :

ghcr.io/cronix2/tp-github-actions:latest
ghcr.io/cronix2/tp-github-actions:<commit-sha>

Le tag basÃ© sur le SHA Git permet d'identifier prÃ©cisÃ©ment l'image correspondant Ã  un commit.

SÃ©curitÃ© et fiabilitÃ©

Le projet applique plusieurs bonnes pratiques :

utilisateur non-root dans l'image Docker ;
image finale minimale ;
healthchecks applicatifs ;
healthcheck Redis ;
dÃ©pendances entre services basÃ©es sur leur Ã©tat de santÃ© ;
validation Nginx avant rechargement ;
smoke test avant bascule ;
vÃ©rification de la couleur Blue/Green ;
vÃ©rification du SHA Git ;
rollback automatique ;
utilisation de GITHUB_TOKEN pour l'authentification GHCR.
Validation finale

Le dÃ©ploiement Blue/Green a Ã©tÃ© testÃ© localement.

Une bascule Blue vers Green a Ã©tÃ© rÃ©alisÃ©e avec succÃ¨s avec :

deploy.sh exit code = 0

L'endpoint /status exposÃ© par Nginx a ensuite confirmÃ© :

deploy_color = green
commit_sha = commit attendu
version = 1.0

L'endpoint /health a Ã©galement confirmÃ© :

status = ok
redis = ok

La chaÃ®ne CI/CD complÃ¨te a enfin Ã©tÃ© validÃ©e aprÃ¨s merge sur main.n

---

## Observabilite — Prometheus & Grafana

Le projet integre une stack d'observabilite permettant de superviser l'application Flask en temps reel.

### Demarrage de la stack

L'ensemble des services peut etre lance avec une seule commande :

```bash
docker compose up -d --buildVerification :

docker compose ps
Acces aux interfaces
Application : http://localhost:8080
Prometheus : http://localhost:9090
Grafana : http://localhost:3000
Prometheus

Prometheus collecte automatiquement les metriques exposees par les deux instances applicatives :

web-blue:5000
web-green:5000

L'endpoint de metriques est :

/metrics

Les principales metriques applicatives sont :

http_requests_total : compteur total des requetes HTTP, avec labels method, endpoint et status ;
http_request_duration_seconds : histogramme du temps de traitement des requetes HTTP.

La configuration Prometheus se trouve dans :

monitoring/prometheus/prometheus.yml

Les regles d'alerte sont definies dans :

monitoring/prometheus/alerts.yml
Grafana

Grafana utilise Prometheus comme datasource par defaut.

La datasource est provisionnee automatiquement au demarrage depuis :

monitoring/grafana/provisioning/datasources/prometheus.yml

Le dashboard est egalement provisionne automatiquement.

Dashboard :

TP5 - Application Monitoring

UID :

tp5-monitoring

Fichier JSON :

monitoring/grafana/dashboards/tp5-monitoring.json

Le dashboard contient notamment :

debit de requetes HTTP par endpoint ;
repartition des codes HTTP ;
latence HTTP p95 ;
nombre de targets Prometheus disponibles.
Requetes PromQL principales

Debit de requetes par endpoint :

sum by (endpoint) (rate(http_requests_total[1m]))

Taux d'erreur HTTP :

sum(rate(http_requests_total{status=~"5.."}[1m]))
/
sum(rate(http_requests_total[1m]))

Latence p95 :

histogram_quantile(
  0.95,
  sum by (le, endpoint) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
Alerte Prometheus

Une alerte nommee :

HighHTTPErrorRate

se declenche lorsque le taux de reponses HTTP 5xx depasse :

5 %

pendant au moins :

30 secondes

Cette temporisation permet d'eviter le declenchement d'une alerte sur un simple pic ponctuel.

La regle a ete validee en provoquant volontairement des erreurs via :

/simulate-error

et en observant les etats successifs :

inactive -> pending -> firing
Arret de la stack
docker compose down

