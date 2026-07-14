import json

import httpx

from app.core.config import Settings
from app.schemas.optimization import AIOptimizationPayload, TaskType
from app.services.ai_provider import OllamaProvider, enforce_prompt_grounding
from app.services.prompt_analyzer import PromptAnalysis
from app.schemas.optimization import ScoreBreakdown


def test_ollama_provider_uses_structured_output_schema():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        payload = AIOptimizationPayload(
            optimized_prompt="Crée une application web de réservation de tables avec un parcours mobile responsive.",
            improvements=["Le livrable et le parcours utilisateur sont précisés."],
            missing_information=["Les horaires d'ouverture du restaurant."],
        )
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": payload.model_dump_json()}},
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://ollama.test",
    )
    provider = OllamaProvider(
        Settings(
            database_url="sqlite://",
            ai_provider="ollama",
            ollama_base_url="http://ollama.test",
            ollama_model="qwen3:4b-instruct",
        ),
        client=client,
    )
    analysis = PromptAnalysis(
        task_type=TaskType.CODE_GENERATION,
        score=42,
        weaknesses=["Le format du livrable n'est pas défini."],
        missing_information=[],
        breakdown=ScoreBreakdown(
            objective=12,
            context=8,
            audience=4,
            output_format=4,
            constraints=4,
            specificity=6,
            success_criteria=4,
        ),
    )

    result = provider.optimize("Je veux une application pour mon restaurant.", analysis)
    client.close()

    assert result.optimized_prompt.startswith("Crée une application web")
    assert captured["model"] == "qwen3:4b-instruct"
    assert captured["stream"] is False
    assert captured["format"]["type"] == "object"
    assert captured["keep_alive"] == "30m"
    assert captured["options"]["temperature"] == 0
    assert captured["options"]["num_predict"] == 1100
    assert "Catégorie détectée : Code Generation" in captured["messages"][1]["content"]


def test_prompt_grounding_removes_unsupported_requirements_and_resolved_questions():
    payload = AIOptimizationPayload(
        optimized_prompt=(
            "Crée une application web responsive. Les réservations sont visibles en temps réel. "
            "Hypothèse technique : React et SQLite."
        ),
        improvements=["Ajout d'une mise à jour en temps réel."],
        missing_information=[
            "Quel type de base de données faut-il utiliser ?",
            "Quel est le nombre maximal de personnes ?",
        ],
    )

    grounded = enforce_prompt_grounding(
        "Je veux une application qui fonctionne sur téléphone.",
        payload,
    )

    assert "temps réel" not in grounded.optimized_prompt
    assert "temps réel" not in grounded.improvements[0]
    assert grounded.missing_information == ["Quel est le nombre maximal de personnes ?"]
