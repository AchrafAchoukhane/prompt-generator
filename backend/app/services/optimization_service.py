import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.optimization import Optimization
from app.services.ai_provider import OllamaProvider, OpenAIProvider
from app.services.local_optimizer import optimize_locally
from app.services.prompt_analyzer import analyze_prompt

logger = logging.getLogger(__name__)


def create_optimization(db: Session, prompt: str) -> Optimization:
    original_analysis = analyze_prompt(prompt)
    payload = optimize_locally(prompt, original_analysis)
    provider = "local"
    model: str | None = None

    if settings.ollama_enabled:
        try:
            ai_provider = OllamaProvider(settings)
            payload = ai_provider.optimize(prompt, original_analysis)
            provider = "ollama"
            model = settings.ollama_model
        except Exception:
            logger.exception("Ollama optimization failed; using the local engine")
    elif settings.openai_enabled:
        try:
            ai_provider = OpenAIProvider(settings)
            payload = ai_provider.optimize(prompt, original_analysis)
            provider = "openai"
            model = settings.openai_model
        except Exception:
            logger.exception("OpenAI optimization failed; using the local engine")

    optimized_analysis = analyze_prompt(payload.optimized_prompt)
    optimized_score = min(100, max(optimized_analysis.score, original_analysis.score + 15))
    if provider == "local":
        optimized_score = max(original_analysis.score, min(82, optimized_score))

    record = Optimization(
        original_prompt=prompt.strip(),
        optimized_prompt=payload.optimized_prompt.strip(),
        task_type=original_analysis.task_type.value,
        original_score=original_analysis.score,
        optimized_score=optimized_score,
        weaknesses=original_analysis.weaknesses,
        improvements=payload.improvements,
        missing_information=payload.missing_information,
        score_breakdown=original_analysis.breakdown.model_dump(),
        provider=provider,
        model=model,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
