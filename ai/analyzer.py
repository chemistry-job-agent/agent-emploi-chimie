import json
import re
import time
from functools import lru_cache
from pathlib import Path

import ollama

from core.cv_loader import charger_cvs


# ============================================================
# CONFIGURATION
# ============================================================

MODELE = "gpt-oss:20b"

ANALYSE_VERSION = "fullcv_v1"

PROFIL_PATH = Path("profil.json")


# ============================================================
# JSON SCHEMA
# ============================================================

ANALYSE_SCHEMA = {
    "type": "object",
    "properties": {
        "compatibilite": {
            "type": "integer"
        },

        "type_poste": {
            "type": "string",
            "enum": [
                "INGENIEUR",
                "ASSISTANT_INGENIEUR",
                "TECHNICIEN",
                "AUTRE"
            ]
        },

        "blocage_critique": {
            "type": "boolean"
        },

        "exigences_obligatoires": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "exigences_importantes": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "bonus": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "forces": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "manques": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "score_cv_ingenieur": {
            "type": "integer"
        },

        "score_cv_technicien": {
            "type": "integer"
        },

        "cv_recommande": {
            "type": "string",
            "enum": [
                "INGENIEUR",
                "TECHNICIEN",
                "AUCUN"
            ]
        },

        "raison_cv": {
            "type": "string"
        },

        "points_forts_cv_choisi": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "faiblesses_cv_choisi": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "adaptations_recommandees": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "resume": {
            "type": "string"
        }
    },

    "required": [
        "compatibilite",
        "type_poste",
        "blocage_critique",
        "exigences_obligatoires",
        "exigences_importantes",
        "bonus",
        "forces",
        "manques",
        "score_cv_ingenieur",
        "score_cv_technicien",
        "cv_recommande",
        "raison_cv",
        "points_forts_cv_choisi",
        "faiblesses_cv_choisi",
        "adaptations_recommandees",
        "resume"
    ],

    "additionalProperties": False
}


# ============================================================
# CHARGEMENT DU PROFIL
# ============================================================

@lru_cache(maxsize=1)
def charger_profil():
    if not PROFIL_PATH.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {PROFIL_PATH}"
        )

    with open(
        PROFIL_PATH,
        "r",
        encoding="utf-8"
    ) as fichier:
        return json.load(fichier)


# ============================================================
# SIMPLIFICATION DE L'OFFRE
# ============================================================

def simplifier_offre(offre):
    return {
        "source": offre.get("source", ""),
        "source_id": offre.get("source_id", ""),
        "titre": offre.get("titre", ""),
        "entreprise": offre.get("entreprise", ""),
        "lieu": offre.get("lieu", ""),
        "contrat": offre.get("contrat", ""),
        "description": offre.get("description", ""),
        "date_publication": offre.get(
            "date_publication",
            ""
        ),
        "experience": offre.get("experience", ""),
        "salaire": offre.get("salaire", ""),
        "url": offre.get("url", "")
    }


# ============================================================
# EXTRACTION JSON
# ============================================================

def extraire_json(texte):
    if not texte:
        raise ValueError(
            "La réponse de GPT-OSS est vide."
        )

    texte = texte.strip()

    # Protection si le modèle ajoute malgré tout
    # des balises Markdown.
    texte = re.sub(
        r"^```(?:json)?\s*",
        "",
        texte,
        flags=re.IGNORECASE
    )

    texte = re.sub(
        r"\s*```$",
        "",
        texte
    )

    try:
        return json.loads(texte)

    except json.JSONDecodeError:
        debut = texte.find("{")
        fin = texte.rfind("}")

        if (
            debut == -1
            or fin == -1
            or fin <= debut
        ):
            raise ValueError(
                "Aucun JSON valide trouvé dans "
                "la réponse de GPT-OSS."
            )

        bloc_json = texte[
            debut:fin + 1
        ]

        return json.loads(
            bloc_json
        )


# ============================================================
# SCORES
# ============================================================

def normaliser_score(valeur):
    try:
        score = float(valeur)

    except (
        TypeError,
        ValueError
    ):
        return 0

    # Protection si le modèle note accidentellement
    # sur 10 malgré les instructions.
    if 0 < score <= 10:
        score *= 10

    score = max(
        0,
        min(
            100,
            score
        )
    )

    return int(
        round(score)
    )


# ============================================================
# ANALYSE PRINCIPALE
# ============================================================

def analyser_offre(offre):
    profil = charger_profil()

    cvs = charger_cvs()

    if "INGENIEUR" not in cvs:
        raise KeyError(
            "Le CV INGENIEUR est absent de charger_cvs()."
        )

    if "TECHNICIEN" not in cvs:
        raise KeyError(
            "Le CV TECHNICIEN est absent de charger_cvs()."
        )

    cv_ingenieur = cvs[
        "INGENIEUR"
    ]

    cv_technicien = cvs[
        "TECHNICIEN"
    ]

    texte_cv_ingenieur = cv_ingenieur.get(
        "texte",
        ""
    )

    texte_cv_technicien = cv_technicien.get(
        "texte",
        ""
    )

    if not texte_cv_ingenieur.strip():
        raise ValueError(
            "Le texte du CV ingénieur est vide."
        )

    if not texte_cv_technicien.strip():
        raise ValueError(
            "Le texte du CV technicien est vide."
        )

    profil_json = json.dumps(
        profil,
        ensure_ascii=False,
        indent=2
    )

    offre_json = json.dumps(
        simplifier_offre(offre),
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
Tu es un recruteur spécialisé dans :

- la chimie ;
- la synthèse organique ;
- la R&D ;
- la chimie médicinale ;
- la chimie pharmaceutique ;
- la chimie analytique ;
- les laboratoires de recherche ;
- les laboratoires industriels ;
- l'industrie chimique ;
- l'industrie pharmaceutique.

Tu dois analyser UNE offre d'emploi pour le candidat
présenté ci-dessous.

Tu disposes volontairement :

1. de son profil structuré ;
2. du texte COMPLET de son CV ingénieur ;
3. du texte COMPLET de son CV technicien ;
4. de l'offre d'emploi.

Tu dois réaliser l'analyse générale ET le choix du CV
dans UNE SEULE réponse.


============================================================
PROFIL STRUCTURÉ DU CANDIDAT
============================================================

{profil_json}


============================================================
CV INGÉNIEUR COMPLET
============================================================

{texte_cv_ingenieur}


============================================================
CV TECHNICIEN COMPLET
============================================================

{texte_cv_technicien}


============================================================
OFFRE D'EMPLOI
============================================================

{offre_json}


============================================================
RÈGLES ABSOLUES
============================================================

1. N'invente JAMAIS une compétence.

2. N'invente JAMAIS une expérience.

3. N'invente JAMAIS une durée d'expérience.

4. N'invente JAMAIS un diplôme.

5. N'invente JAMAIS une certification.

6. N'invente JAMAIS une responsabilité.

7. Toute affirmation concernant le candidat doit être
directement justifiable par :
- le profil structuré ;
- le CV ingénieur ;
- ou le CV technicien.

8. Ne déduis pas automatiquement la maîtrise d'une
technique à partir d'une technique voisine.

9. Si HPLC ou LC-MS sont uniquement présentées comme
des notions ou comme de l'interprétation de résultats,
ne les présente jamais comme une maîtrise pratique
autonome.

10. Les stages sont de vraies expériences
professionnelles en laboratoire.

11. Les stages ne doivent toutefois jamais être
transformés artificiellement en plusieurs années
d'expérience industrielle.

12. Le Master 2 du candidat ne doit pas provoquer
automatiquement le rejet d'un poste de technicien.

13. Pour un poste de technicien, évalue réellement
l'éventuel risque de surqualification.

14. Ne choisis pas automatiquement le CV ingénieur
simplement parce que le candidat possède un Master 2.

15. Ne choisis pas automatiquement le CV technicien
simplement parce que l'annonce contient le mot
"technicien".

16. Pour un poste d'assistant ingénieur, compare
réellement les deux CV.

17. Une annonce demandant 2 ou 3 années d'expérience
peut constituer une faiblesse importante sans être
automatiquement éliminatoire.

18. Si un doctorat est explicitement obligatoire et
qu'aucune équivalence Master n'est acceptée, cela peut
constituer un blocage critique.

19. Distingue précisément :
- les exigences obligatoires ;
- les exigences importantes ;
- les compétences simplement souhaitées ou bonus.

20. Une compétence seulement souhaitée ne doit jamais
être considérée automatiquement comme éliminatoire.

21. Les postes principalement commerciaux,
technico-commerciaux, business development,
enseignement ou management senior doivent recevoir
une faible compatibilité avec ce candidat.

22. Ne recommande une modification du CV que si elle
reste totalement véridique.


============================================================
ÉVALUATION DE LA COMPATIBILITÉ
============================================================

Utilise une note de 0 à 100.

95 à 100 :
correspondance exceptionnelle.

85 à 94 :
très bonne candidature.

75 à 84 :
bonne candidature.

65 à 74 :
candidature crédible mais avec certaines faiblesses.

50 à 64 :
correspondance moyenne.

30 à 49 :
mauvaise correspondance.

0 à 29 :
très faible intérêt.


Prends notamment en compte :

- missions ;
- compétences techniques ;
- niveau d'études ;
- spécialité scientifique ;
- expérience ;
- autonomie demandée ;
- environnement laboratoire ou industriel ;
- responsabilités ;
- secteur ;
- exigences réellement obligatoires.


============================================================
CHOIX ENTRE LES DEUX CV
============================================================

Attribue séparément :

- un score au CV ingénieur ;
- un score au CV technicien.

Les deux scores doivent être compris entre 0 et 100.

Pour chaque CV, évalue notamment :

- cohérence avec le titre du poste ;
- compétences mises en avant ;
- expériences mises en avant ;
- niveau de responsabilité ;
- niveau de diplôme attendu ;
- risque éventuel de surqualification ;
- vocabulaire utilisé ;
- lisibilité du positionnement pour le recruteur.

Le meilleur CV n'est pas nécessairement celui dont
le titre ressemble le plus au titre de l'annonce.

Si aucun des deux CV ne paraît raisonnablement adapté,
choisis AUCUN.


============================================================
ADAPTATIONS AUTORISÉES
============================================================

Tu peux recommander :

- un changement d'ordre de certaines compétences ;
- une reformulation fidèle ;
- une meilleure mise en avant d'une expérience ;
- une adaptation du titre ;
- une adaptation du profil ;
- l'utilisation de mots-clés déjà justifiés par
l'expérience réelle du candidat.

Tu ne peux PAS recommander :

- une compétence inexistante ;
- une expérience inexistante ;
- une fausse durée d'expérience ;
- une fausse maîtrise technique ;
- une fausse expérience industrielle ;
- une fausse certification.


============================================================
FORMAT DE SORTIE
============================================================

Réponds uniquement conformément au JSON Schema fourni.

Pour "type_poste", utilise exclusivement :

- INGENIEUR
- ASSISTANT_INGENIEUR
- TECHNICIEN
- AUTRE

Pour "cv_recommande", utilise exclusivement :

- INGENIEUR
- TECHNICIEN
- AUCUN

Tous les scores doivent être des nombres entiers
entre 0 et 100.

Ne note jamais sur 10.

Le champ "resume" doit expliquer brièvement pourquoi
la candidature est ou n'est pas intéressante.

Le champ "raison_cv" doit expliquer pourquoi le CV
retenu est plus approprié que l'autre.
"""

    debut = time.time()

    derniere_erreur = None

    # Deux tentatives maximum en cas de problème ponctuel.
    for tentative in range(
        1,
        3
    ):
        try:
            reponse = ollama.chat(
                model=MODELE,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                format=ANALYSE_SCHEMA,

                # On veut ici une réponse structurée rapide.
                think="low",

                options={
                    "temperature": 0,

                    # Plus grand que le contexte par défaut
                    # afin d'accepter l'offre + les 2 CV.
                    "num_ctx": 12288
                },

                keep_alive="30m"
            )

            contenu = reponse[
                "message"
            ][
                "content"
            ]

            analyse = extraire_json(
                contenu
            )

            # =================================================
            # NORMALISATION
            # =================================================

            analyse[
                "compatibilite"
            ] = normaliser_score(
                analyse.get(
                    "compatibilite",
                    0
                )
            )

            analyse[
                "score_cv_ingenieur"
            ] = normaliser_score(
                analyse.get(
                    "score_cv_ingenieur",
                    0
                )
            )

            analyse[
                "score_cv_technicien"
            ] = normaliser_score(
                analyse.get(
                    "score_cv_technicien",
                    0
                )
            )

            # =================================================
            # TYPE DE POSTE
            # =================================================

            types_valides = {
                "INGENIEUR",
                "ASSISTANT_INGENIEUR",
                "TECHNICIEN",
                "AUTRE"
            }

            if analyse.get(
                "type_poste"
            ) not in types_valides:
                analyse[
                    "type_poste"
                ] = "AUTRE"

            # =================================================
            # CV RECOMMANDÉ
            # =================================================

            cvs_valides = {
                "INGENIEUR",
                "TECHNICIEN",
                "AUCUN"
            }

            if analyse.get(
                "cv_recommande"
            ) not in cvs_valides:
                analyse[
                    "cv_recommande"
                ] = "AUCUN"

            score_ingenieur = analyse[
                "score_cv_ingenieur"
            ]

            score_technicien = analyse[
                "score_cv_technicien"
            ]

            # Si aucun des deux CV n'atteint 45/100,
            # on force AUCUN.
            if (
                score_ingenieur < 45
                and
                score_technicien < 45
            ):
                analyse[
                    "cv_recommande"
                ] = "AUCUN"

            # =================================================
            # CHEMIN DU CV
            # =================================================

            analyse[
                "fichier_cv"
            ] = ""

            if (
                analyse[
                    "cv_recommande"
                ]
                == "INGENIEUR"
            ):
                analyse[
                    "fichier_cv"
                ] = str(
                    cv_ingenieur.get(
                        "chemin",
                        ""
                    )
                )

            elif (
                analyse[
                    "cv_recommande"
                ]
                == "TECHNICIEN"
            ):
                analyse[
                    "fichier_cv"
                ] = str(
                    cv_technicien.get(
                        "chemin",
                        ""
                    )
                )

            # =================================================
            # MÉTADONNÉES
            # =================================================

            analyse[
                "blocage_critique"
            ] = bool(
                analyse.get(
                    "blocage_critique",
                    False
                )
            )

            analyse[
                "modele"
            ] = MODELE

            analyse[
                "analyse_version"
            ] = ANALYSE_VERSION

            analyse[
                "temps_ia_secondes"
            ] = round(
                time.time() - debut,
                1
            )

            return analyse

        except Exception as erreur:
            derniere_erreur = erreur

            print(
                f"⚠️ Analyse IA "
                f"{tentative}/2 : "
                f"{erreur}"
            )

    raise RuntimeError(
        "Échec de l'analyse GPT-OSS "
        f"après 2 tentatives : {derniere_erreur}"
    )