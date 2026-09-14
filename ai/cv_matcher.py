import json
import re
import time

import ollama

from core.cv_loader import (
    charger_cvs
)


MODELE = "gpt-oss:20b"


def extraire_json(texte):

    if not texte:
        raise ValueError(
            "Réponse IA vide"
        )

    texte = texte.strip()

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

        return json.loads(
            texte
        )

    except json.JSONDecodeError:

        debut = texte.find("{")
        fin = texte.rfind("}")

        if (
            debut == -1
            or fin == -1
            or fin <= debut
        ):
            raise ValueError(
                "Aucun JSON valide trouvé."
            )

        return json.loads(
            texte[
                debut:fin + 1
            ]
        )


def normaliser_score(score):

    try:
        score = float(score)

    except (
        TypeError,
        ValueError
    ):
        return 0

    if 0 < score <= 10:
        score *= 10

    return int(
        round(
            max(
                0,
                min(
                    100,
                    score
                )
            )
        )
    )


def simplifier_offre(offre):

    return {
        "source":
            offre.get(
                "source",
                ""
            ),

        "titre":
            offre.get(
                "titre",
                ""
            ),

        "entreprise":
            offre.get(
                "entreprise",
                ""
            ),

        "lieu":
            offre.get(
                "lieu",
                ""
            ),

        "contrat":
            offre.get(
                "contrat",
                ""
            ),

        "experience":
            offre.get(
                "experience",
                ""
            ),

        "description":
            offre.get(
                "description",
                ""
            )
    }


def comparer_cvs(
    offre
):

    cvs = charger_cvs()

    cv_ingenieur = cvs[
        "INGENIEUR"
    ]

    cv_technicien = cvs[
        "TECHNICIEN"
    ]

    offre_json = json.dumps(
        simplifier_offre(
            offre
        ),
        ensure_ascii=False
    )

    prompt = f"""
Tu es un recruteur spécialisé dans les métiers
de la chimie.

Tu dois déterminer lequel des DEUX CV réels
ci-dessous est le plus adapté à l'offre.

Tu dois exclusivement utiliser les informations
présentes dans les CV et dans l'offre.

==============================
OFFRE
==============================

{offre_json}


==============================
CV INGÉNIEUR
==============================

{cv_ingenieur["texte"]}


==============================
CV TECHNICIEN
==============================

{cv_technicien["texte"]}


==============================
MISSION
==============================

Évalue indépendamment les deux CV.

Pour chacun, prends en compte :

- adéquation avec les missions ;
- compétences techniques réellement démontrées ;
- niveau de diplôme attendu ;
- niveau de responsabilité du poste ;
- cohérence du positionnement ;
- expérience pertinente ;
- risque éventuel de surqualification ;
- lisibilité du parcours pour un recruteur.

IMPORTANT :

1. N'invente aucune compétence.

2. Une compétence absente du CV est considérée
comme non démontrée.

3. Les stages sont de vraies expériences,
mais ne deviennent jamais plusieurs années
d'expérience industrielle.

4. Ne choisis pas automatiquement le CV ingénieur
parce que le candidat possède un Master.

5. Ne choisis pas automatiquement le CV technicien
parce que l'intitulé contient "technicien".

6. Pour un poste d'assistant ingénieur,
les deux CV doivent être réellement comparés.

7. HPLC et LC-MS ne doivent pas être considérées
comme maîtrisées en autonomie si le CV indique
seulement des notions ou de l'interprétation.

8. Le score de chaque CV doit être compris
entre 0 et 100.

9. NE JAMAIS noter sur 10.

10. Si aucun CV n'est raisonnablement adapté,
choisis AUCUN.


Réponds UNIQUEMENT avec ce JSON :

{{
  "score_cv_ingenieur": 0,
  "score_cv_technicien": 0,
  "cv_recommande": "AUCUN",
  "raison_cv": "",
  "points_forts_cv_choisi": [],
  "faiblesses_cv_choisi": [],
  "adaptations_recommandees": []
}}

Valeurs autorisées pour cv_recommande :

INGENIEUR
TECHNICIEN
AUCUN
"""

    debut = time.time()

    derniere_erreur = None

    for tentative in range(
        1,
        3
    ):

        try:

            reponse = ollama.chat(
                model=MODELE,

                messages=[
                    {
                        "role":
                            "user",

                        "content":
                            prompt
                    }
                ],

                format="json",

                think="low",

                options={
                    "temperature": 0
                },

                keep_alive="30m"
            )

            contenu = reponse[
                "message"
            ][
                "content"
            ]

            resultat = extraire_json(
                contenu
            )

            resultat[
                "score_cv_ingenieur"
            ] = normaliser_score(
                resultat.get(
                    "score_cv_ingenieur",
                    0
                )
            )

            resultat[
                "score_cv_technicien"
            ] = normaliser_score(
                resultat.get(
                    "score_cv_technicien",
                    0
                )
            )

            if resultat.get(
                "cv_recommande"
            ) not in (
                "INGENIEUR",
                "TECHNICIEN",
                "AUCUN"
            ):

                resultat[
                    "cv_recommande"
                ] = "AUCUN"

            # Vérification de cohérence supplémentaire
            score_ingenieur = resultat[
                "score_cv_ingenieur"
            ]

            score_technicien = resultat[
                "score_cv_technicien"
            ]

            if (
                score_ingenieur < 45
                and
                score_technicien < 45
            ):

                resultat[
                    "cv_recommande"
                ] = "AUCUN"

            resultat[
                "fichier_cv"
            ] = ""

            if (
                resultat[
                    "cv_recommande"
                ]
                == "INGENIEUR"
            ):

                resultat[
                    "fichier_cv"
                ] = cv_ingenieur[
                    "chemin"
                ]

            elif (
                resultat[
                    "cv_recommande"
                ]
                == "TECHNICIEN"
            ):

                resultat[
                    "fichier_cv"
                ] = cv_technicien[
                    "chemin"
                ]

            resultat[
                "temps_matching_secondes"
            ] = round(
                time.time()
                - debut,
                1
            )

            return resultat

        except Exception as erreur:

            derniere_erreur = erreur

            print(
                f"⚠️ Matching CV "
                f"{tentative}/2 : "
                f"{erreur}"
            )

    raise RuntimeError(
        f"Échec matching CV : "
        f"{derniere_erreur}"
    )