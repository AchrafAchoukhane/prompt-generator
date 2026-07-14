import pytest

from app.schemas.optimization import TaskType
from app.services.local_optimizer import optimize_locally
from app.services.prompt_analyzer import analyze_prompt, detect_task_type


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("Crée une image produit avec une lumière studio", TaskType.IMAGE_GENERATION),
        ("Développe une API FastAPI avec des tests", TaskType.CODE_GENERATION),
        ("Rédige un article de blog pour des débutants", TaskType.WRITING),
        ("Recherche des sources récentes et compare les études", TaskType.RESEARCH),
        ("Analyse ce CSV et calcule les KPI", TaskType.DATA_ANALYSIS),
        ("Réalise un audit de sécurité défensif de cette API", TaskType.CYBERSECURITY),
        ("Explique les fractions avec un exercice", TaskType.LEARNING),
    ],
)
def test_detect_task_type(prompt: str, expected: TaskType) -> None:
    assert detect_task_type(prompt) == expected


def test_local_optimizer_is_category_aware_and_improves_score() -> None:
    original = "Fais une image d'un café"
    analysis = analyze_prompt(original)
    result = optimize_locally(original, analysis)
    optimized = analyze_prompt(result.optimized_prompt)

    assert analysis.task_type == TaskType.IMAGE_GENERATION
    assert "Composition et cadrage" in result.optimized_prompt
    assert "Éléments à éviter" in result.optimized_prompt
    assert optimized.score > analysis.score

