from openai import OpenAI

from app.core.config import Settings
from app.schemas.optimization import AIOptimizationPayload, TaskType
from app.services.local_optimizer import STRATEGIES
from app.services.prompt_analyzer import PromptAnalysis


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
        strategy = STRATEGIES[analysis.task_type]
        system_prompt = (
            "Tu es un architecte de prompts senior. Transforme la demande sans changer son intention ni sa langue. "
            "Adapte réellement la stratégie à la catégorie : ne te contente jamais d'allonger le texte. "
            "Rends l'objectif, le contexte, les contraintes, le livrable et les critères de réussite actionnables. "
            "N'invente aucun fait manquant : utilise des champs [À préciser] et liste les informations manquantes. "
            "Les améliorations doivent décrire des changements concrets. "
            "Pour la cybersécurité, reste strictement légal, autorisé et défensif."
        )
        user_prompt = (
            f"Catégorie détectée : {analysis.task_type.value}\n"
            f"Structure recommandée : {', '.join(strategy['sections'])}\n"
            f"Faiblesses détectées : {'; '.join(analysis.weaknesses) or 'aucune majeure'}\n\n"
            f"Prompt original :\n{prompt}"
        )
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=AIOptimizationPayload,
        )
        if response.output_parsed is None:
            raise RuntimeError("The model returned no structured optimization")
        return response.output_parsed


def provider_label(task_type: TaskType) -> str:
    return f"OpenAI / {task_type.value}"

