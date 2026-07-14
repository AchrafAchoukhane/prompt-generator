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
- Ollama avec le modèle `qwen3:4b-instruct` pour l'optimisation IA locale sans clé
- Docker Desktop avec Docker Compose uniquement pour le mode PostgreSQL complet

## Démarrage simple sans clé API

Installez Ollama une seule fois, puis téléchargez le modèle :

```powershell
winget install --id Ollama.Ollama --exact
ollama pull qwen3:4b-instruct
```

Ollama démarre normalement avec Windows. Si l'API locale n'est pas disponible, lancez `ollama serve` dans un terminal et laissez-le ouvert.

Depuis la racine du projet, préparez puis lancez le backend avec SQLite pour un essai immédiat :

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install --upgrade pip
backend/.venv/Scripts/python -m pip install -e ".\backend[dev]"
Copy-Item backend/.env.runtime.example backend/.env.runtime
Set-Location backend
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000 --env-file .env.runtime
```

Dans un deuxième terminal PowerShell, depuis la racine du projet :

```powershell
Set-Location frontend
pnpm install
pnpm dev
```

Ouvrez `http://localhost:3000`. Une optimisation peut prendre deux à cinq minutes sur un PC sans carte graphique dédiée ; le modèle reste ensuite chargé trente minutes pour accélérer les appels suivants.

## Démarrage complet avec PostgreSQL

Depuis la racine du projet :

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
```

Modifiez ensuite `.env` : choisissez un vrai `POSTGRES_PASSWORD` et reportez-le dans `DATABASE_URL`. Aucune clé API n'est nécessaire avec `AI_PROVIDER=ollama`.

Démarrez PostgreSQL et préparez le backend :

```powershell
docker compose up -d db
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install --upgrade pip
backend/.venv/Scripts/python -m pip install -e ".\backend[dev]"
Set-Location backend
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000 --env-file ../.env
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
$resultat = Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/v1/optimizations `
  -ContentType "application/json" `
  -Body '{"prompt":"Je veux créer une application pour un restaurant où les clients réservent une table en choisissant la date et le nombre de personnes. Le restaurant doit voir les réservations. Je ne sais pas quelle technologie utiliser et le site doit fonctionner sur téléphone."}'

$resultat | Select-Object task_type, original_score, optimized_score, provider, model
$resultat.optimized_prompt
```

Avec Ollama lancé, la réponse attendue contient notamment :

```text
task_type       : Code Generation
provider        : ollama
model           : qwen3:4b-instruct
original_score  : un score inférieur au score optimisé
optimized_score : un score supérieur au score original
```

Le champ `optimized_prompt` doit décrire un MVP de réservation web responsive, distinguer les fonctionnalités demandées des hypothèses techniques et ne pas recopier le texte original. `improvements` et `missing_information` doivent contenir des listes spécifiques au restaurant.

## API REST

- `GET /api/v1/health` : santé de l'API, de la base et configuration IA.
- `POST /api/v1/optimizations` : analyse, optimise et persiste un prompt.
- `GET /api/v1/optimizations` : historique paginé (`limit`, `offset`).
- `GET /api/v1/optimizations/{id}` : détail d'une optimisation.

Toutes les réponses applicatives sont en JSON. Les erreurs de validation suivent le format JSON standard de FastAPI.

## Fournisseurs IA

Par défaut, le backend appelle l'API locale d'Ollama et valide sa réponse avec un schéma JSON Pydantic :

```dotenv
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b-instruct
OLLAMA_TIMEOUT_SECONDS=420
```

OpenAI reste disponible en option :

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
```

Si le fournisseur choisi est indisponible, l'optimisation continue avec le moteur déterministe par catégorie. L'interface et l'historique indiquent quel moteur a produit chaque résultat (`ollama`, `openai` ou `local`).

## Arrêt

Arrêtez les serveurs avec `Ctrl+C`, puis PostgreSQL avec :

```powershell
docker compose down
```

Les données restent dans le volume `postgres_data`. Pour les supprimer explicitement, utilisez `docker compose down --volumes`.
