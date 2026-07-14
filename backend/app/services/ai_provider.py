import json
import re
from typing import Any

import httpx
from openai import OpenAI

from app.core.config import Settings
from app.schemas.optimization import AIOptimizationPayload
from app.services.local_optimizer import STRATEGIES
from app.services.prompt_analyzer import PromptAnalysis, normalize


REALTIME_PATTERN = re.compile(r"\b(?:en\s+)?temps\s+r[ée]el(?:le)?s?\b", re.IGNORECASE)
DATABASE_TECHNOLOGIES = ("sqlite", "postgresql", "mysql", "mongodb", "firebase", "supabase")


def enforce_prompt_grounding(
    original_prompt: str,
    payload: AIOptimizationPayload,
) -> AIOptimizationPayload:
    original = normalize(original_prompt)
    optimized_prompt = payload.optimized_prompt
    improvements = list(payload.improvements)

    realtime_was_requested = any(
        marker in original for marker in ("temps reel", "real time", "real-time", "instantane")
    )
    if not realtime_was_requested:
        optimized_prompt = REALTIME_PATTERN.sub("", optimized_prompt)
        improvements = [REALTIME_PATTERN.sub("", item) for item in improvements]
        optimized_prompt = re.sub(r"[ \t]{2,}", " ", optimized_prompt)
        improvements = [re.sub(r"[ \t]{2,}", " ", item).strip() for item in improvements]
        optimized_prompt = re.sub(r"[ \t]+([,.;:])", r"\1", optimized_prompt)
        improvements = [re.sub(r"[ \t]+([,.;:])", r"\1", item) for item in improvements]

    optimized = normalize(optimized_prompt)
    database_is_selected = any(technology in optimized for technology in DATABASE_TECHNOLOGIES)
    missing_information = []
    for item in payload.missing_information:
        normalized_item = normalize(item)
        asks_for_database_choice = (
            "base de donnees" in normalized_item
            and any(term in normalized_item for term in ("type", "technologie", "choix"))
        )
        if database_is_selected and asks_for_database_choice:
            continue
        missing_information.append(item)

    return payload.model_copy(
        update={
            "optimized_prompt": optimized_prompt.strip(),
            "improvements": improvements,
            "missing_information": missing_information,
        }
    )


def _build_messages(prompt: str, analysis: PromptAnalysis) -> list[dict[str, str]]:
    strategy = STRATEGIES[analysis.task_type]
    schema = json.dumps(
        AIOptimizationPayload.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    system_prompt = (
        "Tu es un architecte de prompts senior. Tu transformes une demande naturelle en un prompt "
        "immédiatement utilisable par une autre IA. Réponds dans la langue du prompt original. "
        "Réécris réellement la demande : corrige la langue, supprime les répétitions, hiérarchise le besoin "
        "et rends les attentes vérifiables. Ne recopie pas un long paragraphe brut dans une rubrique. "
        "Conserve l'intention et tous les faits fournis. Lorsque l'utilisateur demande une recommandation "
        "ou dit ne pas connaître la technologie, propose des choix raisonnables sous forme d'hypothèses "
        "explicites au lieu de renvoyer uniquement des questions génériques. N'invente jamais une donnée "
        "métier propre à l'utilisateur, une métrique chiffrée, une fonctionnalité ou un mode de livraison "
        "non demandé. Utilise [À préciser] seulement si une information est indispensable "
        "et ne peut pas recevoir de valeur par défaut sûre. Le prompt optimisé doit rester proportionné à "
        "la tâche : plus clair et plus actionnable, pas simplement plus long. Formate optimized_prompt en "
        "Markdown lisible avec des titres courts et des listes à puces ; évite le paragraphe monolithique. "
        "Pour Code Generation, précise les utilisateurs, fonctionnalités, règles métier, architecture ou "
        "choix de stack, données, API, responsive, sécurité, tests, critères d'acceptation et commandes "
        "uniquement lorsque ces éléments sont pertinents. Distingue les exigences données par l'utilisateur "
        "des hypothèses techniques que tu proposes, limite le périmètre au MVP et indique explicitement ce "
        "qui reste hors périmètre. Une exigence absente du texte original ne doit jamais être ajoutée comme "
        "obligatoire : place-la dans les informations manquantes ou les évolutions futures. « Fonctionner sur "
        "téléphone » signifie par défaut une interface web responsive, pas une application native. Voir une "
        "liste complète n'implique pas du temps réel. N'ajoute pas d'authentification, paiement, fonctionnement "
        "hors ligne, notification, seuil de performance chiffré, dépôt Git ou archive ZIP si ce n'est pas demandé. "
        "Si la stack est inconnue, place ta recommandation sous un titre « Hypothèses techniques proposées » "
        "et demande à l'IA cible de la justifier. Pour Image Generation, traite le sujet, le style, "
        "la composition, la lumière, la palette et le format. N'utilise jamais un gabarit d'image pour un "
        "projet logiciel. Pour la cybersécurité, reste strictement légal, autorisé et défensif. "
        "optimized_prompt doit contenir au maximum 350 mots. Dans improvements, fournis exactement quatre "
        "changements courts, précis et réellement effectués. Dans missing_information, liste au maximum cinq "
        "informations spécifiques qui amélioreraient encore le résultat ; aucune question passe-partout. "
        "N'ajoute aucun préambule. La sortie doit être un JSON complet respectant exactement le schéma fourni."
    )
    user_prompt = (
        f"Catégorie détectée : {analysis.task_type.value}\n"
        f"Structure conseillée : {', '.join(strategy['sections'])}\n"
        f"Faiblesses détectées : {'; '.join(analysis.weaknesses) or 'aucune majeure'}\n"
        f"Schéma JSON obligatoire : {schema}\n\n"
        f"Demande originale :\n{prompt.strip()}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


class OpenAIProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider")
        self.model = settings.openai_model
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=2,
        )

    def optimize(self, prompt: str, analysis: PromptAnalysis) -> AIOptimizationPayload:
        response = self.client.responses.parse(
            model=self.model,
            input=_build_messages(prompt, analysis),
            text_format=AIOptimizationPayload,
        )
        if response.output_parsed is None:
            raise RuntimeError("The model returned no structured optimization")
        return enforce_prompt_grounding(prompt, response.output_parsed)


class OllamaProvider:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.model = settings.ollama_model
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.timeout = settings.ollama_timeout_seconds
        self.client = client

    def optimize(self, prompt: str, analysis: PromptAnalysis) -> AIOptimizationPayload:
        request_body: dict[str, Any] = {
            "model": self.model,
            "messages": _build_messages(prompt, analysis),
            "stream": False,
            "format": AIOptimizationPayload.model_json_schema(),
            "keep_alive": "30m",
            "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 1100},
        }

        if self.client is not None:
            response = self.client.post("/api/chat", json=request_body)
        else:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.post("/api/chat", json=request_body)

        response.raise_for_status()
        data = response.json()
        if data.get("done_reason") == "length":
            raise RuntimeError("Ollama output exceeded the configured generation limit")
        content = data.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama returned no structured optimization")
        payload = AIOptimizationPayload.model_validate_json(content)
        return enforce_prompt_grounding(prompt, payload)
