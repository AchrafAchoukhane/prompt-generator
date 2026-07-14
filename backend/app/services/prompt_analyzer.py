import re
import unicodedata
from dataclasses import dataclass

from app.schemas.optimization import ScoreBreakdown, TaskType


CATEGORY_KEYWORDS: dict[TaskType, tuple[str, ...]] = {
    TaskType.IMAGE_GENERATION: (
        "image", "photo", "illustration", "affiche", "logo", "visuel", "midjourney",
        "stable diffusion", "dall-e", "portrait", "render", "rendu 3d",
    ),
    TaskType.CODE_GENERATION: (
        "code", "coder", "programme", "fonction", "api", "backend", "frontend", "react",
        "python", "javascript", "typescript", "sql", "bug", "debug", "algorithme",
        "application", "interface", "site web", "outil", "plateforme", "logiciel", "projet web",
    ),
    TaskType.WRITING: (
        "redige", "ecris", "article", "email", "newsletter", "post", "texte", "histoire",
        "scenario", "copywriting", "communique", "publication", "blog",
    ),
    TaskType.RESEARCH: (
        "recherche", "sources", "bibliographie", "revue de litterature", "etat de l'art",
        "etude", "veille", "comparer", "comparatif", "enquete",
    ),
    TaskType.DATA_ANALYSIS: (
        "donnees", "data", "dataset", "csv", "excel", "tableau", "statistique", "kpi",
        "correlation", "visualisation", "graphique", "regression",
    ),
    TaskType.CYBERSECURITY: (
        "cybersecurite", "securite", "vulnerabilite", "pentest", "phishing", "malware",
        "cve", "incident", "soc", "siem", "menace", "audit de securite",
    ),
    TaskType.LEARNING: (
        "explique", "apprendre", "cours", "tutoriel", "lecon", "quiz", "exercice",
        "pedagogique", "enseigne", "revision", "comprendre",
    ),
}

CATEGORY_INTENT_PATTERNS: dict[TaskType, tuple[str, ...]] = {
    TaskType.IMAGE_GENERATION: (
        r"\b(?:cree|genere|fais|produis|imagine|concois)\w*\s+(?:moi\s+)?(?:une?|des?)\s+"
        r"(?:image|photo|illustration|affiche|logo|visuel|portrait)s?\b",
        r"\b(?:prompt|brief)\s+(?:pour|d')\s*(?:une?|des?)?\s*"
        r"(?:image|photo|illustration|affiche|logo|visuel|portrait)s?\b",
    ),
    TaskType.CODE_GENERATION: (
        r"\b(?:developpe|cree|construis|code|implemente|concois)\w*\b.{0,80}\b"
        r"(?:application|interface|site|api|programme|outil|plateforme|backend|frontend)\b",
        r"\b(?:je veux|je souhaite|je compte)\b.{0,100}\b(?:faire|creer|developper|construire|concevoir)\b"
        r".{0,80}\b(?:projet|application|interface|site|outil|plateforme)\b",
        r"\b(?:je veux|je souhaite|j'ai besoin d')\b.{0,60}\b"
        r"(?:application|interface|site|outil|plateforme)\b",
    ),
    TaskType.WRITING: (
        r"\b(?:redige|ecris|reformule|corrige)\w*\b.{0,60}\b"
        r"(?:article|email|newsletter|post|texte|histoire|scenario|communique)\b",
    ),
    TaskType.RESEARCH: (
        r"\b(?:recherche|trouve|compare|etudie)\w*\b.{0,80}\b"
        r"(?:sources|etudes|informations|publications|bibliographie)\b",
    ),
    TaskType.DATA_ANALYSIS: (
        r"\b(?:analyse|explore|nettoie|visualise)\w*\b.{0,80}\b"
        r"(?:donnees|data|dataset|csv|excel|tableau|kpi|statistiques?)\b",
    ),
    TaskType.CYBERSECURITY: (
        r"\b(?:audite|analyse|evalue|teste)\w*\b.{0,80}\b"
        r"(?:securite|vulnerabilite|pentest|menace|incident|cve)\b",
    ),
    TaskType.LEARNING: (
        r"\b(?:explique|enseigne|apprends-moi|cree\s+un\s+cours)\w*\b",
    ),
}

ACTION_WORDS = (
    "cree", "genere", "analyse", "explique", "redige", "ecris", "compare", "construis",
    "developpe", "propose", "resume", "traduis", "corrige", "optimise", "identifie",
    "create", "generate", "analyze", "write", "explain", "compare", "build", "summarize",
)
CONTEXT_MARKERS = (
    "contexte", "dans le cadre", "parce que", "afin de", "pour mon", "pour notre", "je suis",
    "nous sommes", "a partir de", "voici les donnees", "background", "context", "because",
)
AUDIENCE_MARKERS = (
    "public", "audience", "lecteur", "utilisateur", "client", "debutant", "expert", "enfant",
    "etudiant", "direction", "equipe", "persona", "target audience", "for beginners",
)
FORMAT_MARKERS = (
    "format", "tableau", "liste", "json", "markdown", "etapes", "plan", "bullet", "section",
    "schema", "code complet", "reponse courte", "csv", "yaml", "structure",
)
CONSTRAINT_MARKERS = (
    "contrainte", "maximum", "minimum", "sans", "avec", "doit", "ne doit pas", "limite",
    "ton", "style", "langue", "mots", "caracteres", "deadline", "budget", "obligatoire",
)
SUCCESS_MARKERS = (
    "critere", "reussite", "qualite", "valider", "verification", "test", "mesurable",
    "objectif atteint", "definition of done", "acceptance criteria", "sources fiables",
)


@dataclass(frozen=True)
class PromptAnalysis:
    task_type: TaskType
    score: int
    breakdown: ScoreBreakdown
    weaknesses: list[str]
    missing_information: list[str]


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _count_markers(text: str, markers: tuple[str, ...]) -> int:
    return sum(1 for marker in markers if normalize(marker) in text)


def detect_task_type(prompt: str) -> TaskType:
    text = normalize(prompt)
    scored: dict[TaskType, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        keyword_score = sum(
            2 if " " in keyword else 1
            for keyword in keywords
            if normalize(keyword) in text
        )
        intent_score = sum(
            8 for pattern in CATEGORY_INTENT_PATTERNS.get(category, ()) if re.search(pattern, text)
        )
        scored[category] = keyword_score + intent_score

    best_category, best_score = max(scored.items(), key=lambda item: item[1])
    return best_category if best_score > 0 else TaskType.GENERAL


def analyze_prompt(prompt: str) -> PromptAnalysis:
    text = normalize(prompt)
    words = re.findall(r"\b[\w'-]+\b", text)
    task_type = detect_task_type(prompt)
    category_hits = _count_markers(text, CATEGORY_KEYWORDS.get(task_type, ()))

    has_action = any(re.search(rf"\b{re.escape(word)}\w*\b", text) for word in ACTION_WORDS)
    objective = min(20, (10 if len(words) >= 4 else 5) + (10 if has_action else 0))
    context_hits = _count_markers(text, CONTEXT_MARKERS)
    context = min(15, context_hits * 7 + (4 if len(words) >= 35 else 0))
    audience = min(10, _count_markers(text, AUDIENCE_MARKERS) * 7)
    output_format = min(15, _count_markers(text, FORMAT_MARKERS) * 6)
    numeric_constraint = bool(re.search(r"\b\d+(?:[.,]\d+)?\s*(?:mots?|pages?|minutes?|heures?|%|px|ko|mo)?\b", text))
    constraints = min(15, _count_markers(text, CONSTRAINT_MARKERS) * 4 + (5 if numeric_constraint else 0))
    specificity = min(15, category_hits * 3 + min(6, len(set(words)) // 12))
    success_criteria = min(10, _count_markers(text, SUCCESS_MARKERS) * 5)

    breakdown = ScoreBreakdown(
        objective=objective,
        context=context,
        audience=audience,
        output_format=output_format,
        constraints=constraints,
        specificity=specificity,
        success_criteria=success_criteria,
    )
    score = sum(breakdown.model_dump().values())

    checks = (
        (objective < 16, "L'objectif ou l'action attendue manque de netteté.", "Quel résultat concret doit être obtenu ?"),
        (context < 8, "Le contexte utile est insuffisant.", "Quel contexte, point de départ ou matériau doit être pris en compte ?"),
        (audience < 6, "Le public cible ou le niveau attendu n'est pas défini.", "À qui le résultat est-il destiné ?"),
        (output_format < 8, "Le format de sortie n'est pas spécifié.", "Quel format de livrable souhaitez-vous ?"),
        (constraints < 8, "Les contraintes de longueur, ton, stack ou périmètre sont floues.", "Quelles contraintes sont obligatoires ?"),
        (specificity < 8, "Les détails propres à la tâche sont trop génériques.", "Quels éléments spécifiques au domaine faut-il inclure ?"),
        (success_criteria < 5, "Aucun critère de réussite vérifiable n'est donné.", "Comment reconnaître une réponse réussie ?"),
    )
    weaknesses = [weakness for condition, weakness, _ in checks if condition]
    missing_information = [question for condition, _, question in checks if condition][:5]

    return PromptAnalysis(task_type, score, breakdown, weaknesses, missing_information)
