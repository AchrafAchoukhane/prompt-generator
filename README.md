# Prompt Generator

Prompt Generator transforme une demande libre en prompt clair, structuré et adapté à son type de tâche. Le MVP détecte huit catégories, explique les faiblesses du prompt, calcule un score avant/après, optimise la demande et conserve l'historique dans PostgreSQL.

## Architecture

```text
Prompt Generator/
├── frontend/                  # React 19 + Vite + TypeScript
│   ├── app/                  # Interface et composants
│   └── tests/                # Tests structurels du frontend
├── backend/                   # FastAPI + SQLAlchemy
│   ├── app/api/routes/       # API REST /api/v1
│   ├── app/core/             # Configuration et base de données
│   ├── app/models/           # Modèles SQLAlchemy
│   ├── app/schemas/          # Contrats JSON Pydantic
│   ├── app/services/         # Analyse, stratégies et fournisseur IA
│   ├── alembic/              # Migration PostgreSQL
│   └── tests/                # Tests unitaires et API
├── docker-compose.yml        # PostgreSQL local
└── .env.example              # Variables attendues, sans secret réel
```

Le score est déterministe et explicable : objectif (20), contexte (15), public (10), format (15), contraintes (15), spécificité métier (15) et critères de réussite (10). Le modèle d'IA améliore le texte, mais ne choisit pas lui-même son score.

## Prérequis

- Python 3.11 ou plus récent
- Node.js 22.13 ou plus récent
- pnpm 11.7 ou plus récent
- Docker Desktop avec Docker Compose

## Premier démarrage sous PowerShell

Depuis la racine du projet :

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
```

Modifiez ensuite `.env` : choisissez un vrai `POSTGRES_PASSWORD`, reportez-le dans `DATABASE_URL`, puis ajoutez éventuellement `OPENAI_API_KEY`. Aucune clé n'est nécessaire pour essayer l'application : le moteur local déterministe prend automatiquement le relais.

Démarrez PostgreSQL et préparez le backend :

```powershell
docker compose up -d db
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install --upgrade pip
backend/.venv/Scripts/python -m pip install -e ".\backend[dev]"
Set-Location backend
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Dans un deuxième terminal, démarrez le frontend :

```powershell
Set-Location frontend
pnpm install
pnpm dev
```

Ouvrez ensuite `http://localhost:3000`. L'API est disponible sur `http://localhost:8000`, sa documentation interactive sur `http://localhost:8000/docs`.

## Tests et vérifications

```powershell
# Backend
Set-Location backend
.venv/Scripts/python -m pytest

# Frontend
Set-Location ../frontend
pnpm test
pnpm build
```

Vérification rapide de l'API :

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/v1/optimizations `
  -ContentType "application/json" `
  -Body '{"prompt":"Rédige un email pour annoncer notre nouveau produit"}'
```

## API REST

- `GET /api/v1/health` : santé de l'API, de la base et configuration IA.
- `POST /api/v1/optimizations` : analyse, optimise et persiste un prompt.
- `GET /api/v1/optimizations` : historique paginé (`limit`, `offset`).
- `GET /api/v1/optimizations/{id}` : détail d'une optimisation.

Toutes les réponses applicatives sont en JSON. Les erreurs de validation suivent le format JSON standard de FastAPI.

## Fournisseur IA

L'adaptateur OpenAI utilise la Responses API et des sorties structurées Pydantic. Sa configuration se trouve uniquement dans `.env` :

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
```

Si la clé est absente ou si le fournisseur échoue, l'optimisation continue avec le moteur local par catégorie. L'historique indique quel moteur a produit chaque résultat.

## Arrêt

Arrêtez les serveurs avec `Ctrl+C`, puis PostgreSQL avec :

```powershell
docker compose down
```

Les données restent dans le volume `postgres_data`. Pour les supprimer explicitement, utilisez `docker compose down --volumes`.
