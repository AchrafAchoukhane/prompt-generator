import re

from app.schemas.optimization import AIOptimizationPayload, TaskType
from app.services.prompt_analyzer import PromptAnalysis, normalize


STRATEGIES: dict[TaskType, dict[str, object]] = {
    TaskType.GENERAL: {
        "role": "Agis comme un expert du domaine concerné, orienté vers des résultats concrets.",
        "sections": ("Objectif", "Contexte", "Contraintes", "Livrable attendu", "Critères de réussite"),
        "method": (
            "Commence par reformuler l'objectif en une phrase précise.",
            "Sépare les faits fournis, les contraintes et les hypothèses nécessaires.",
            "Produis directement le livrable demandé, sans contenu générique inutile.",
        ),
        "output": ("Réponse structurée avec des titres courts", "Résultat final directement exploitable"),
        "improvements": ("Clarification de l'objectif", "Séparation du contexte et des contraintes", "Ajout d'un livrable vérifiable"),
    },
    TaskType.IMAGE_GENERATION: {
        "role": "Agis comme un directeur artistique spécialisé en prompts de génération d'images.",
        "sections": ("Sujet et intention", "Direction artistique", "Composition et cadrage", "Lumière et palette", "Détails à préserver", "Éléments à éviter", "Paramètres de sortie"),
        "method": (
            "Décris clairement le sujet principal, l'action et l'environnement.",
            "Précise uniquement les choix visuels utiles : style, composition, lumière, palette et niveau de détail.",
            "Ajoute les éléments à éviter sans contredire l'intention initiale.",
        ),
        "output": ("Un prompt visuel final prêt à copier", "Une courte liste des paramètres ou exclusions utiles"),
        "improvements": ("Structuration du brief visuel", "Précision de la composition et de la lumière", "Ajout d'éléments négatifs utiles"),
    },
    TaskType.CODE_GENERATION: {
        "role": "Agis comme un architecte logiciel et développeur senior orienté produit.",
        "sections": ("Objectif fonctionnel", "Contexte technique", "Entrées et sorties", "Exigences d'implémentation", "Cas limites", "Tests et critères d'acceptation", "Format de livraison"),
        "method": (
            "Reformule le besoin en fonctionnalités et parcours utilisateur mesurables.",
            "Propose une architecture adaptée au MVP avant de détailler l'implémentation.",
            "Explicite les hypothèses de stack, les modèles de données et les contrats d'API.",
            "Inclue la gestion des erreurs, la sécurité, les tests et les commandes d'exécution.",
            "Distingue clairement le MVP des améliorations futures.",
        ),
        "output": (
            "1. Synthèse du besoin",
            "2. Fonctionnalités et parcours utilisateur",
            "3. Architecture proposée",
            "4. Plan d'implémentation ou code",
            "5. Tests et critères d'acceptation",
            "6. Instructions de lancement",
        ),
        "improvements": ("Clarification du produit à construire", "Ajout de l'architecture et du parcours utilisateur", "Définition des tests et du format de livraison"),
    },
    TaskType.WRITING: {
        "role": "Agis comme un rédacteur professionnel attentif au public, au message et au ton.",
        "sections": ("But du texte", "Public cible", "Message central", "Ton et voix", "Structure", "Longueur et contraintes", "Appel à l'action"),
        "method": (
            "Identifie l'intention du texte et son lecteur principal.",
            "Adapte le vocabulaire, le ton et la structure au canal demandé.",
            "Supprime les répétitions et termine par l'action attendue du lecteur.",
        ),
        "output": ("Texte final prêt à publier", "Variantes de titre ou d'objet si elles sont utiles"),
        "improvements": ("Alignement sur le lecteur", "Définition du ton et de la structure", "Ajout d'un objectif éditorial mesurable"),
    },
    TaskType.RESEARCH: {
        "role": "Agis comme un analyste de recherche rigoureux et transparent sur ses sources.",
        "sections": ("Question de recherche", "Périmètre", "Méthode", "Sources attendues", "Axes d'analyse", "Gestion des incertitudes", "Format de synthèse"),
        "method": (
            "Délimite la question, la période, la géographie et les critères de comparaison.",
            "Privilégie les sources primaires et distingue faits, interprétations et incertitudes.",
            "Présente une synthèse argumentée avec des citations vérifiables.",
        ),
        "output": ("Synthèse structurée", "Tableau comparatif si pertinent", "Sources et limites"),
        "improvements": ("Délimitation du périmètre", "Ajout d'exigences sur les sources", "Séparation des faits, hypothèses et limites"),
    },
    TaskType.DATA_ANALYSIS: {
        "role": "Agis comme un data analyst capable de relier les données à une décision métier.",
        "sections": ("Question métier", "Données disponibles", "Préparation des données", "Analyses et métriques", "Visualisations", "Contrôles de qualité", "Livrables"),
        "method": (
            "Traduis la demande en questions analytiques et indicateurs mesurables.",
            "Vérifie la qualité des données et documente les transformations.",
            "Présente les résultats, limites et recommandations de façon décisionnelle.",
        ),
        "output": ("Méthode d'analyse", "Résultats et visualisations", "Conclusions et recommandations"),
        "improvements": ("Traduction en question analytique", "Définition des métriques et contrôles", "Précision des livrables de données"),
    },
    TaskType.CYBERSECURITY: {
        "role": "Agis comme un consultant en cybersécurité travaillant exclusivement dans un cadre autorisé et défensif.",
        "sections": ("Objectif défensif", "Périmètre autorisé", "Environnement", "Menaces ou contrôles à évaluer", "Preuves attendues", "Mesures de sécurité", "Remédiations et rapport"),
        "method": (
            "Confirme le périmètre autorisé et évite toute action destructive.",
            "Classe les constats par risque, preuve et impact.",
            "Propose des remédiations vérifiables et priorisées.",
        ),
        "output": ("Périmètre et méthode", "Constats priorisés", "Plan de remédiation"),
        "improvements": ("Définition d'un périmètre explicitement autorisé", "Priorisation des preuves et remédiations", "Ajout de garde-fous opérationnels"),
    },
    TaskType.LEARNING: {
        "role": "Agis comme un pédagogue qui adapte l'explication au niveau réel de l'apprenant.",
        "sections": ("Objectif pédagogique", "Niveau de départ", "Compétences visées", "Progression", "Exemples", "Exercices", "Vérification des acquis"),
        "method": (
            "Explique progressivement avec un vocabulaire adapté.",
            "Utilise au moins un exemple concret avant l'exercice.",
            "Vérifie la compréhension et corrige les erreurs fréquentes.",
        ),
        "output": ("Explication progressive", "Exemple résolu", "Exercice avec correction"),
        "improvements": ("Adaptation au niveau de l'apprenant", "Création d'une progression pédagogique", "Ajout d'exercices et de vérifications"),
    },
}


def _clean_prompt(prompt: str) -> str:
    cleaned = re.sub(r"[ \t]+", " ", prompt.strip())
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([,.;:!?])(?=\S)", r"\1 ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _reformulate_mission(prompt: str, task_type: TaskType) -> str:
    text = normalize(prompt)
    describes_prompt_product = (
        task_type == TaskType.CODE_GENERATION
        and "prompt" in text
        and any(term in text for term in ("prompt generator", "amelior", "optimis", "plus performante"))
        and any(term in text for term in ("interface", "application", "projet", "outil", "espace"))
    )
    if describes_prompt_product:
        return (
            "Conçois et développe une application web appelée « Prompt Generator ». "
            "Son objectif est d'améliorer la qualité des réponses produites par une IA lorsque la demande initiale "
            "est vague, imprécise ou mal formulée.\n\n"
            "L'utilisateur doit pouvoir saisir un prompt en langage naturel. Le système analyse cette demande, "
            "puis génère une version plus claire, précise et performante sans modifier l'intention d'origine. "
            "L'interface affiche le prompt original, le prompt optimisé et la liste concrète des améliorations apportées.\n\n"
            "L'optimisation doit s'adapter au type de tâche demandé, notamment la génération d'images, plutôt que "
            "d'appliquer le même gabarit à tous les prompts."
        )
    return _clean_prompt(prompt)


def optimize_locally(prompt: str, analysis: PromptAnalysis) -> AIOptimizationPayload:
    strategy = STRATEGIES[analysis.task_type]
    method = strategy["method"]
    output = strategy["output"]
    questions = analysis.missing_information[:3]

    lines = [
        "PROMPT OPTIMISÉ",
        "",
        "Rôle",
        str(strategy["role"]),
        "",
        "Mission",
        _reformulate_mission(prompt, analysis.task_type),
        "",
        "Approche attendue",
        *(f"- {item}" for item in method),
        "",
        "Format du livrable",
        *(f"- {item}" for item in output),
        "",
        "Critères de qualité",
        "- Respecter l'intention et les informations réellement fournies.",
        "- Être précis, directement exploitable et éviter les répétitions.",
        "- Signaler clairement les hypothèses au lieu d'inventer des informations.",
    ]

    if analysis.task_type == TaskType.CYBERSECURITY:
        lines.append("- Rester dans un cadre légal, autorisé et strictement défensif.")

    if questions:
        lines.extend(("", "Questions utiles avant de finaliser"))
        lines.extend(f"- {question}" for question in questions)
        lines.extend((
            "- Si ces réponses ne sont pas disponibles, avancer avec des hypothèses minimales et les annoncer.",
        ))

    improvements = [
        *strategy["improvements"],
        "Suppression de la répétition du prompt original",
        "Remplacement des champs vides par des questions non bloquantes",
    ]
    return AIOptimizationPayload(
        optimized_prompt="\n".join(lines),
        improvements=list(dict.fromkeys(improvements)),
        missing_information=questions,
    )
