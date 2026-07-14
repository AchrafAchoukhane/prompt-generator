from app.schemas.optimization import AIOptimizationPayload, TaskType
from app.services.prompt_analyzer import PromptAnalysis


STRATEGIES: dict[TaskType, dict[str, object]] = {
    TaskType.GENERAL: {
        "sections": ("Objectif", "Contexte", "Contraintes", "Livrable attendu", "Critères de réussite"),
        "improvements": ("Clarification de l'objectif", "Séparation du contexte et des contraintes", "Ajout d'un livrable vérifiable"),
    },
    TaskType.IMAGE_GENERATION: {
        "sections": ("Sujet et intention", "Direction artistique", "Composition et cadrage", "Lumière et palette", "Détails à préserver", "Éléments à éviter", "Paramètres de sortie"),
        "improvements": ("Structuration du brief visuel", "Précision de la composition et de la lumière", "Ajout d'éléments négatifs utiles"),
    },
    TaskType.CODE_GENERATION: {
        "sections": ("Objectif fonctionnel", "Contexte technique", "Entrées et sorties", "Exigences d'implémentation", "Cas limites", "Tests et critères d'acceptation", "Format de livraison"),
        "improvements": ("Clarification du contrat technique", "Ajout des cas limites et des tests", "Définition du format de livraison"),
    },
    TaskType.WRITING: {
        "sections": ("But du texte", "Public cible", "Message central", "Ton et voix", "Structure", "Longueur et contraintes", "Appel à l'action"),
        "improvements": ("Alignement sur le lecteur", "Définition du ton et de la structure", "Ajout d'un objectif éditorial mesurable"),
    },
    TaskType.RESEARCH: {
        "sections": ("Question de recherche", "Périmètre", "Méthode", "Sources attendues", "Axes d'analyse", "Gestion des incertitudes", "Format de synthèse"),
        "improvements": ("Délimitation du périmètre", "Ajout d'exigences sur les sources", "Séparation des faits, hypothèses et limites"),
    },
    TaskType.DATA_ANALYSIS: {
        "sections": ("Question métier", "Données disponibles", "Préparation des données", "Analyses et métriques", "Visualisations", "Contrôles de qualité", "Livrables"),
        "improvements": ("Traduction en question analytique", "Définition des métriques et contrôles", "Précision des livrables de données"),
    },
    TaskType.CYBERSECURITY: {
        "sections": ("Objectif défensif", "Périmètre autorisé", "Environnement", "Menaces ou contrôles à évaluer", "Preuves attendues", "Mesures de sécurité", "Remédiations et rapport"),
        "improvements": ("Définition d'un périmètre explicitement autorisé", "Priorisation des preuves et remédiations", "Ajout de garde-fous opérationnels"),
    },
    TaskType.LEARNING: {
        "sections": ("Objectif pédagogique", "Niveau de départ", "Compétences visées", "Progression", "Exemples", "Exercices", "Vérification des acquis"),
        "improvements": ("Adaptation au niveau de l'apprenant", "Création d'une progression pédagogique", "Ajout d'exercices et de vérifications"),
    },
}


def optimize_locally(prompt: str, analysis: PromptAnalysis) -> AIOptimizationPayload:
    strategy = STRATEGIES[analysis.task_type]
    sections = strategy["sections"]
    questions = analysis.missing_information
    placeholders = questions + ["Préciser si nécessaire"] * max(0, len(sections) - len(questions))

    lines = [
        f"TÂCHE — {analysis.task_type.value}",
        "",
        "Demande de départ :",
        prompt.strip(),
        "",
        "Consigne structurée :",
    ]
    for index, section in enumerate(sections):
        if index == 0:
            value = prompt.strip()
        else:
            value = f"[À préciser : {placeholders[index - 1]}]"
        lines.extend((f"{section} :", value, ""))

    if analysis.task_type == TaskType.CYBERSECURITY:
        lines.extend((
            "Garde-fou :",
            "Rester dans un cadre légal, autorisé et défensif. Refuser toute action hors périmètre et privilégier des recommandations sûres.",
            "",
        ))

    lines.extend((
        "Règles de réponse :",
        "- Ne pas inventer les informations absentes ; signaler les hypothèses.",
        "- Privilégier la précision et l'utilité plutôt que la longueur.",
        "- Vérifier le résultat par rapport aux critères annoncés avant de conclure.",
    ))

    return AIOptimizationPayload(
        optimized_prompt="\n".join(lines),
        improvements=list(strategy["improvements"]),
        missing_information=analysis.missing_information,
    )

