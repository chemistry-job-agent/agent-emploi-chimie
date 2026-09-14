import re
import unicodedata

from core.strategy import analyser_strategie


# ============================================================
# OUTILS
# ============================================================

def normaliser_texte(texte):
    if texte is None:
        return ""

    texte = str(texte).lower().strip()

    texte = unicodedata.normalize(
        "NFKD",
        texte
    )

    texte = "".join(
        caractere
        for caractere in texte
        if not unicodedata.combining(caractere)
    )

    return " ".join(
        texte.split()
    )


def limiter_score(score):
    return max(
        0,
        min(
            100,
            int(round(score))
        )
    )


def convertir_booleen(valeur):
    if isinstance(valeur, bool):
        return valeur

    if valeur is None:
        return False

    if isinstance(valeur, (int, float)):
        return valeur != 0

    texte = normaliser_texte(
        valeur
    )

    return texte in {
        "true",
        "vrai",
        "oui",
        "yes",
        "1"
    }


# ============================================================
# CONTRAT
# ============================================================

def evaluer_contrat(offre):
    contrat = normaliser_texte(
        offre.get(
            "contrat",
            ""
        )
    )

    titre = normaliser_texte(
        offre.get(
            "titre",
            ""
        )
    )

    texte = (
        contrat
        + " "
        + titre
    )

    # Priorité principale
    if "cdi" in texte:
        return 8, "CDI : +8"

    # Acceptable
    if "cdd" in texte:
        return 3, "CDD : +3"

    # Moins intéressant
    if "interim" in texte:
        return -3, "Intérim : -3"

    # Pas une cible prioritaire
    if "alternance" in texte:
        return -12, "Alternance : -12"

    if "stage" in texte:
        return -15, "Stage : -15"

    return 0, "Contrat neutre : 0"


# ============================================================
# STRATEGIE GEOGRAPHIQUE
# ============================================================

def evaluer_strategie(offre):
    strategie = analyser_strategie(
        offre
    )

    bonus = int(
        strategie.get(
            "bonus_strategique",
            0
        )
        or 0
    )

    pays = strategie.get(
        "pays",
        "INCONNU"
    )

    zone = strategie.get(
        "zone",
        "INCONNUE"
    )

    pipeline = strategie.get(
        "pipeline",
        "INTERNATIONAL"
    )

    score_geo = int(
        strategie.get(
            "score_geographique",
            50
        )
        or 50
    )

    score_opportunite = int(
        strategie.get(
            "score_opportunite",
            50
        )
        or 50
    )

    raison = (
        f"Stratégie : "
        f"{pays} / {zone} / {pipeline} "
        f"| géographie {score_geo}/100 "
        f"| opportunité {score_opportunite}/100 "
        f"| bonus +{bonus}"
    )

    return (
        bonus,
        raison,
        strategie
    )


# Compatibilité avec d'éventuels anciens scripts
# qui utilisent encore evaluer_localisation().
def evaluer_localisation(offre):
    bonus, raison, _ = (
        evaluer_strategie(
            offre
        )
    )

    return bonus, raison


# ============================================================
# EXPERIENCE DEMANDEE
# ============================================================

def extraire_experience_demandee(offre):
    experience = normaliser_texte(
        offre.get(
            "experience",
            ""
        )
    )

    description = normaliser_texte(
        offre.get(
            "description",
            ""
        )
    )

    texte = (
        experience
        + " "
        + description
    )

    # Exemples détectés :
    #
    # 5 ans
    # 5 années
    # minimum 5 ans
    # au moins 5 ans

    motifs = [
        r"minimum\s+(\d+)\s+ans?",
        r"au moins\s+(\d+)\s+ans?",
        r"(\d+)\s+ans?\s+minimum",
        r"(\d+)\s+annees?",
        r"(\d+)\s+ans?"
    ]

    valeurs = []

    for motif in motifs:
        correspondances = re.findall(
            motif,
            texte
        )

        for valeur in correspondances:
            try:
                nombre = int(
                    valeur
                )

                # Évite de prendre des nombres absurdes
                # provenant d'autres informations.
                if 1 <= nombre <= 15:
                    valeurs.append(
                        nombre
                    )

            except ValueError:
                pass

    if not valeurs:
        return None

    return max(
        valeurs
    )


def evaluer_experience(offre):
    annees = extraire_experience_demandee(
        offre
    )

    if annees is None:
        return (
            0,
            "Expérience demandée non quantifiée : 0"
        )

    if annees <= 1:
        return (
            0,
            f"Expérience demandée : "
            f"{annees} an(s) : 0"
        )

    if annees == 2:
        return (
            -1,
            "2 ans d'expérience demandés : -1"
        )

    if annees == 3:
        return (
            -2,
            "3 ans d'expérience demandés : -2"
        )

    if annees == 4:
        return (
            -4,
            "4 ans d'expérience demandés : -4"
        )

    if annees >= 5:
        return (
            -6,
            f"{annees} ans d'expérience demandés : -6"
        )

    return 0, "Expérience : 0"


# ============================================================
# CV
# ============================================================

def evaluer_cv(analyse):
    cv_recommande = analyse.get(
        "cv_recommande",
        "AUCUN"
    )

    score_ingenieur = int(
        analyse.get(
            "score_cv_ingenieur",
            0
        )
        or 0
    )

    score_technicien = int(
        analyse.get(
            "score_cv_technicien",
            0
        )
        or 0
    )

    meilleur_score = max(
        score_ingenieur,
        score_technicien
    )

    if cv_recommande == "AUCUN":
        return (
            -10,
            "Aucun CV adapté : -10"
        )

    if meilleur_score < 50:
        return (
            -8,
            "CV recommandé faible : -8"
        )

    if meilleur_score < 60:
        return (
            -4,
            "CV recommandé moyennement adapté : -4"
        )

    if meilleur_score >= 80:
        return (
            2,
            "CV très bien adapté : +2"
        )

    return (
        0,
        "CV correctement adapté : 0"
    )


# ============================================================
# DECISION
# ============================================================

def determiner_decision(
    score_final,
    blocage_critique=False
):
    if blocage_critique:
        return "IGNORER"

    if score_final >= 85:
        return "PRIORITE_HAUTE"

    if score_final >= 72:
        return "POSTULER"

    if score_final >= 58:
        return "A_ETUDIER"

    return "IGNORER"


# ============================================================
# SCORE FINAL
# ============================================================

def calculer_score_final(
    offre,
    analyse
):
    compatibilite = int(
        analyse.get(
            "compatibilite",
            0
        )
        or 0
    )

    blocage_critique = convertir_booleen(
        analyse.get(
            "blocage_critique",
            False
        )
    )

    # --------------------------------------------------------
    # CONTRAT
    # --------------------------------------------------------

    bonus_contrat, raison_contrat = (
        evaluer_contrat(
            offre
        )
    )

    # --------------------------------------------------------
    # STRATEGIE / GEOGRAPHIE
    # --------------------------------------------------------

    (
        bonus_strategique,
        raison_strategie,
        strategie
    ) = evaluer_strategie(
        offre
    )

    # --------------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------------

    (
        penalite_experience,
        raison_experience
    ) = evaluer_experience(
        offre
    )

    # --------------------------------------------------------
    # CV
    # --------------------------------------------------------

    ajustement_cv, raison_cv = (
        evaluer_cv(
            analyse
        )
    )

    # --------------------------------------------------------
    # SCORE BRUT
    # --------------------------------------------------------

    score_avant_plafonds = (
        compatibilite
        + bonus_contrat
        + bonus_strategique
        + penalite_experience
        + ajustement_cv
    )

    score_final = limiter_score(
        score_avant_plafonds
    )

    # --------------------------------------------------------
    # BLOCAGE CRITIQUE
    # --------------------------------------------------------

    if blocage_critique:
        score_final = min(
            score_final,
            45
        )

    # --------------------------------------------------------
    # AUCUN CV ADAPTE
    # --------------------------------------------------------

    if (
        analyse.get(
            "cv_recommande",
            "AUCUN"
        )
        == "AUCUN"
    ):
        score_final = min(
            score_final,
            55
        )

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    decision = determiner_decision(
        score_final,
        blocage_critique
    )

    # --------------------------------------------------------
    # RESULTAT DETAILLE
    # --------------------------------------------------------

    return {
        # -------------------------
        # Score IA
        # -------------------------

        "score_gpt":
            compatibilite,

        # -------------------------
        # Ajustements
        # -------------------------

        "bonus_contrat":
            bonus_contrat,

        # Conservé pour compatibilité avec
        # les anciens fichiers / scripts.
        "bonus_localisation":
            bonus_strategique,

        "bonus_strategique":
            bonus_strategique,

        "ajustement_experience":
            penalite_experience,

        "ajustement_cv":
            ajustement_cv,

        # -------------------------
        # Stratégie internationale
        # -------------------------

        "pays":
            strategie.get(
                "pays",
                "INCONNU"
            ),

        "zone":
            strategie.get(
                "zone",
                "INCONNUE"
            ),

        "pipeline":
            strategie.get(
                "pipeline",
                "INTERNATIONAL"
            ),

        "score_geographique":
            strategie.get(
                "score_geographique",
                50
            ),

        "score_opportunite":
            strategie.get(
                "score_opportunite",
                50
            ),

        # -------------------------
        # Score
        # -------------------------

        "score_avant_plafonds":
            limiter_score(
                score_avant_plafonds
            ),

        "score_final":
            score_final,

        "decision":
            decision,

        # -------------------------
        # Raisons
        # -------------------------

        "raisons_score": [
            raison_contrat,
            raison_strategie,
            raison_experience,
            raison_cv
        ]
    }