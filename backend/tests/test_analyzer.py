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
    assert "directeur artistique" in result.optimized_prompt
    assert "prompt visuel final" in result.optimized_prompt
    assert "[À préciser" not in result.optimized_prompt
    assert optimized.score > analysis.score


def test_product_request_is_not_misclassified_from_an_example_image_mention() -> None:
    original = (
        "Je compte faire un projet de prompt generator parce que j'utilise souvent l'IA. "
        "Je veux une interface où écrire un prompt naturel, voir le nouveau prompt amélioré "
        "et les points améliorés. Ces prompts peuvent servir à générer une image ou autre chose."
    )

    analysis = analyze_prompt(original)
    result = optimize_locally(original, analysis)

    assert analysis.task_type == TaskType.CODE_GENERATION
    assert "architecte logiciel" in result.optimized_prompt
    assert "application web appelée « Prompt Generator »" in result.optimized_prompt
    assert "saisir un prompt en langage naturel" in result.optimized_prompt
    assert "Architecture proposée" in result.optimized_prompt
    assert "Direction artistique" not in result.optimized_prompt
    assert "Je compte faire un projet" not in result.optimized_prompt
    assert "[À préciser" not in result.optimized_prompt
