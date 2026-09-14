import json

from pathlib import Path


# ============================================================
# SOURCES
# ============================================================

from sources.collector import (
    collecter_toutes_les_offres
)

from sources.gmail_alerts import (
    collecter_alertes_gmail
)


# ============================================================
# CORE
# ============================================================

from core.database import (
    initialiser_base,
    enregistrer_liste_offres,
    offre_deja_analysee,
    enregistrer_analyse,
    recuperer_analyses,
    compter_offres,
    compter_analyses
)

from core.prefilter import (
    prefiltrer_offres
)

from core.deduplicator import (
    dedoublonner_offres
)

from core.scorer import (
    calculer_score_final
)


# ============================================================
# IA
# ============================================================

from ai.analyzer import (
    analyser_offre,
    ANALYSE_VERSION
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_ANALYSES_IA = 5

NOMBRE_PAR_RECHERCHE = 10

SEUIL_PREFILTRE = 18

MAX_EMAILS_PAR_SOURCE = 100

RESULTATS_PATH = Path(
    "resultats_v2.json"
)


# ============================================================
# RECHERCHES FRANCE TRAVAIL
# ============================================================

RECHERCHES = [

    # --------------------------------------------------------
    # INGÉNIEUR
    # --------------------------------------------------------

    "ingénieur chimiste",
    "ingénieur chimie",
    "ingénieur R&D chimie",
    "ingénieur chimie organique",
    "ingénieur synthèse",
    "ingénieur synthèse organique",
    "ingénieur développement chimie",
    "ingénieur analytique",
    "ingénieur laboratoire chimie",

    # --------------------------------------------------------
    # ASSISTANT INGÉNIEUR
    # --------------------------------------------------------

    "assistant ingénieur chimie",
    "assistant ingénieur R&D",
    "assistant ingénieur laboratoire",
    "assistant ingénieur synthèse",

    # --------------------------------------------------------
    # CHIMISTE
    # --------------------------------------------------------

    "chimiste",
    "chimiste R&D",
    "chimiste organicien",
    "chimiste synthèse",
    "chimiste synthèse organique",
    "chimiste analytique",

    # --------------------------------------------------------
    # TECHNICIEN
    # --------------------------------------------------------

    "technicien chimiste",
    "technicien supérieur chimiste",
    "technicien R&D chimie",
    "technicien laboratoire chimie",
    "technicien synthèse",
    "technicien synthèse organique",
    "technicien analytique",

    # --------------------------------------------------------
    # AUTRES INTITULÉS
    # --------------------------------------------------------

    "analyste chimiste",
    "chargé d'études chimie",
    "chargé développement chimie"
]


# ============================================================
# AFFICHAGE
# ============================================================

def separateur():
    print(
        "=" * 78
    )


def afficher_entete():

    print()

    separateur()

    print(
        "AGENT EMPLOI CHIMIE V2"
    )

    print(
        f"Moteur IA : {ANALYSE_VERSION}"
    )

    print(
        "Sources : France Travail + Gmail"
    )

    print(
        "Gmail : LinkedIn + Apec + Indeed"
    )

    separateur()

    print()


# ============================================================
# STATISTIQUES DES SOURCES
# ============================================================

def afficher_statistiques_sources(
    offres
):

    compteurs = {}

    for offre in offres:

        source = offre.get(
            "source",
            "Inconnue"
        )

        compteurs[
            source
        ] = (
            compteurs.get(
                source,
                0
            )
            + 1
        )

    print()
    print(
        "📊 RÉPARTITION PAR SOURCE"
    )

    for source, nombre in sorted(
        compteurs.items()
    ):

        print(
            f"   {source} : "
            f"{nombre}"
        )


# ============================================================
# COLLECTE FRANCE TRAVAIL
# ============================================================

def collecter_france_travail():

    print()
    print(
        "🇫🇷 FRANCE TRAVAIL"
    )

    print()

    try:

        offres = (
            collecter_toutes_les_offres(
                recherches_france_travail=
                    RECHERCHES,

                nombre_par_recherche=
                    NOMBRE_PAR_RECHERCHE
            )
        )

        print()

        print(
            f"✅ France Travail : "
            f"{len(offres)} offre(s)"
        )

        return offres

    except Exception as erreur:

        print()

        print(
            f"❌ Erreur France Travail : "
            f"{erreur}"
        )

        return []


# ============================================================
# COLLECTE GMAIL
# ============================================================

def collecter_gmail():

    print()
    print(
        "📧 GMAIL - ALERTES EMPLOI"
    )

    print(
        "   LinkedIn / Apec / Indeed"
    )

    print()

    try:

        offres = collecter_alertes_gmail(
            max_messages_par_source=
                MAX_EMAILS_PAR_SOURCE,

            afficher_progression=True
        )

        print()

        print(
            f"✅ Gmail : "
            f"{len(offres)} "
            f"nouvelle(s) offre(s)"
        )

        return offres

    except Exception as erreur:

        print()

        print(
            f"⚠️ Gmail indisponible : "
            f"{erreur}"
        )

        print(
            "➡️ L'agent continue avec "
            "France Travail."
        )

        return []


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    afficher_entete()

    # ========================================================
    # 1. SQLITE
    # ========================================================

    print(
        "🗄️ INITIALISATION SQLITE"
    )

    initialiser_base()

    print(
        "✅ Base prête."
    )

    print(
        f"📚 Offres mémorisées : "
        f"{compter_offres()}"
    )

    print(
        f"🧠 Analyses mémorisées : "
        f"{compter_analyses(ANALYSE_VERSION)}"
    )

    # ========================================================
    # 2. FRANCE TRAVAIL
    # ========================================================

    offres_ft = (
        collecter_france_travail()
    )

    # ========================================================
    # 3. GMAIL
    # ========================================================

    offres_gmail = (
        collecter_gmail()
    )

    # ========================================================
    # 4. FUSION
    # ========================================================

    print()
    print(
        "🔗 FUSION DES SOURCES"
    )

    offres = (
        offres_ft
        + offres_gmail
    )

    print(
        f"Avant dédoublonnage : "
        f"{len(offres)}"
    )

    if not offres:

        print()

        print(
            "❌ Aucune offre collectée."
        )

        return

    # ========================================================
    # 5. DÉDOUBLONNAGE GLOBAL
    # ========================================================

    offres = dedoublonner_offres(
        offres
    )

    print(
        f"Après dédoublonnage : "
        f"{len(offres)}"
    )

    afficher_statistiques_sources(
        offres
    )

    # ========================================================
    # 6. ENREGISTREMENT SQLITE
    # ========================================================

    print()
    print(
        "💾 ENREGISTREMENT EN BASE"
    )

    stats_db = (
        enregistrer_liste_offres(
            offres
        )
    )

    print(
        f"🆕 Nouvelles : "
        f"{stats_db.get('nouvelles', 0)}"
    )

    print(
        f"♻️ Déjà connues : "
        f"{stats_db.get('deja_connues', 0)}"
    )

    # ========================================================
    # 7. PRÉFILTRE
    # ========================================================

    print()
    print(
        "🔬 PRÉFILTRAGE PYTHON"
    )

    retenues, rejetees = (
        prefiltrer_offres(
            offres,
            seuil=
                SEUIL_PREFILTRE
        )
    )

    print(
        f"✅ Retenues : "
        f"{len(retenues)}"
    )

    print(
        f"❌ Écartées : "
        f"{len(rejetees)}"
    )

    if not retenues:

        print()

        print(
            "Aucune offre ne passe "
            "le préfiltre."
        )

        return

    # ========================================================
    # 8. ÉVITER LES RÉANALYSES
    # ========================================================

    jamais_analysees = []

    deja_analysees = 0

    for offre in retenues:

        offre_id = offre.get(
            "_db_id"
        )

        if (
            offre_id
            and offre_deja_analysee(
                offre_id,
                ANALYSE_VERSION
            )
        ):

            deja_analysees += 1

            continue

        jamais_analysees.append(
            offre
        )

    print()

    print(
        f"♻️ Déjà analysées par GPT-OSS : "
        f"{deja_analysees}"
    )

    print(
        f"🆕 Jamais analysées : "
        f"{len(jamais_analysees)}"
    )

    # ========================================================
    # 9. PRIORITÉ AU MEILLEUR PRÉFILTRE
    # ========================================================

    jamais_analysees.sort(
        key=lambda offre:
            offre.get(
                "_score_prefiltre",
                0
            ),
        reverse=True
    )

    # ========================================================
    # 10. LOT GPT-OSS
    # ========================================================

    a_analyser = (
        jamais_analysees[
            :MAX_ANALYSES_IA
        ]
    )

    print()

    print(
        f"🧠 GPT-OSS analysera "
        f"{len(a_analyser)} offre(s)"
    )

    print(
        f"   Maximum : "
        f"{MAX_ANALYSES_IA} "
        f"par lancement"
    )

    print(
        "   1 appel GPT-OSS par offre"
    )

    print(
        "   Profil + CV ingénieur complet "
        "+ CV technicien complet"
    )

    print()

    # ========================================================
    # 11. ANALYSE GPT-OSS
    # ========================================================

    analyses_reussies = 0

    analyses_echouees = 0

    for numero, offre in enumerate(
        a_analyser,
        start=1
    ):

        separateur()

        print(
            f"[{numero}/"
            f"{len(a_analyser)}] "
            f"{offre.get('titre', '')}"
        )

        print(
            f"Entreprise : "
            f"{offre.get('entreprise', '')}"
        )

        print(
            f"Lieu : "
            f"{offre.get('lieu', '')}"
        )

        print(
            f"Contrat : "
            f"{offre.get('contrat', '')}"
        )

        print(
            f"Source : "
            f"{offre.get('source', '')}"
        )

        print(
            f"Préfiltre : "
            f"{offre.get('_score_prefiltre', 0)}"
        )

        print()

        try:

            # ================================================
            # GPT-OSS
            # ================================================

            print(
                "🧠 Analyse complète GPT-OSS..."
            )

            analyse = (
                analyser_offre(
                    offre
                )
            )

            # ================================================
            # SCORE FINAL
            # ================================================

            score = (
                calculer_score_final(
                    offre,
                    analyse
                )
            )

            analyse.update(
                score
            )

            # ================================================
            # SQLITE
            # ================================================

            offre_id = offre.get(
                "_db_id"
            )

            if not offre_id:

                raise RuntimeError(
                    "Identifiant SQLite absent."
                )

            enregistrer_analyse(
                offre_id=
                    offre_id,

                analyse=
                    analyse,

                score_prefiltre=
                    offre.get(
                        "_score_prefiltre",
                        0
                    ),

                analyse_version=
                    ANALYSE_VERSION
            )

            analyses_reussies += 1

            # ================================================
            # AFFICHAGE
            # ================================================

            print()

            print(
                "✅ Analyse enregistrée."
            )

            print()

            print(
                f"🧠 GPT : "
                f"{analyse.get('compatibilite', 0)}"
                f"/100"
            )

            print(
                f"⭐ SCORE FINAL : "
                f"{analyse.get('score_final', 0)}"
                f"/100"
            )

            print(
                f"🚦 DÉCISION : "
                f"{analyse.get('decision', '')}"
            )

            print()

            print(
                f"🧪 Type de poste : "
                f"{analyse.get('type_poste', 'AUTRE')}"
            )

            print(
                f"🚫 Blocage critique : "
                f"{analyse.get('blocage_critique', False)}"
            )

            print()

            print(
                f"📄 CV ingénieur : "
                f"{analyse.get('score_cv_ingenieur', 0)}"
                f"/100"
            )

            print(
                f"📄 CV technicien : "
                f"{analyse.get('score_cv_technicien', 0)}"
                f"/100"
            )

            print(
                f"✅ CV recommandé : "
                f"{analyse.get('cv_recommande', 'AUCUN')}"
            )

            if analyse.get(
                "fichier_cv"
            ):

                print(
                    f"📁 "
                    f"{analyse.get('fichier_cv')}"
                )

            print()

            print(
                "📊 Ajustements :"
            )

            print(
                f"   Contrat : "
                f"{analyse.get('bonus_contrat', 0):+d}"
            )

            print(
                f"   Localisation : "
                f"{analyse.get('bonus_localisation', 0):+d}"
            )

            print(
                f"   Expérience : "
                f"{analyse.get('ajustement_experience', 0):+d}"
            )

            print(
                f"   CV : "
                f"{analyse.get('ajustement_cv', 0):+d}"
            )

            print()

            print(
                f"💬 "
                f"{analyse.get('resume', '')}"
            )

            print()

            print(
                f"⏱️ Temps IA : "
                f"{analyse.get('temps_ia_secondes', 0)} s"
            )

            print()

        except Exception as erreur:

            analyses_echouees += 1

            print()

            print(
                "❌ ERREUR PENDANT L'ANALYSE"
            )

            print(
                str(erreur)
            )

            print()

    # ========================================================
    # 12. RÉCUPÉRER TOUTES LES ANALYSES
    # ========================================================

    resultats = (
        recuperer_analyses(
            ANALYSE_VERSION
        )
    )

    # Sécurité pour les anciennes entrées.
    for resultat in resultats:

        if (
            "score_final"
            not in resultat
        ):

            resultat[
                "score_final"
            ] = resultat.get(
                "compatibilite",
                0
            )

        if (
            "decision"
            not in resultat
        ):

            resultat[
                "decision"
            ] = "A_ETUDIER"

    # ========================================================
    # 13. CLASSEMENT
    # ========================================================

    resultats.sort(
        key=lambda resultat:
            resultat.get(
                "score_final",
                0
            ),
        reverse=True
    )

    # ========================================================
    # 14. EXPORT JSON
    # ========================================================

    with open(
        RESULTATS_PATH,
        "w",
        encoding="utf-8"
    ) as fichier:

        json.dump(
            resultats,
            fichier,
            ensure_ascii=False,
            indent=2
        )

    # ========================================================
    # 15. BILAN
    # ========================================================

    print()

    separateur()

    print(
        "BILAN DU LANCEMENT"
    )

    separateur()

    print()

    print(
        f"🇫🇷 France Travail : "
        f"{len(offres_ft)} offre(s)"
    )

    print(
        f"📧 Gmail : "
        f"{len(offres_gmail)} nouvelle(s) offre(s)"
    )

    print(
        f"✅ Analyses réussies : "
        f"{analyses_reussies}"
    )

    print(
        f"❌ Analyses échouées : "
        f"{analyses_echouees}"
    )

    print(
        f"♻️ Réanalyses évitées : "
        f"{deja_analysees}"
    )

    print(
        f"🧠 Total d'analyses mémorisées : "
        f"{len(resultats)}"
    )

    # ========================================================
    # 16. TOP 10
    # ========================================================

    print()

    separateur()

    print(
        "TOP 10 - SCORE FINAL"
    )

    separateur()

    if not resultats:

        print()

        print(
            "Aucune analyse mémorisée."
        )

    else:

        for position, resultat in enumerate(
            resultats[:10],
            start=1
        ):

            print()

            print(
                f"{position}. "
                f"{resultat.get('titre', '')}"
            )

            print(
                f"   "
                f"{resultat.get('entreprise', '')}"
            )

            print(
                f"   📍 "
                f"{resultat.get('lieu', '')}"
            )

            print(
                f"   🧠 GPT : "
                f"{resultat.get('compatibilite', 0)}"
                f"/100"
            )

            print(
                f"   ⭐ FINAL : "
                f"{resultat.get('score_final', 0)}"
                f"/100"
            )

            print(
                f"   🚦 "
                f"{resultat.get('decision', '')}"
            )

            print(
                f"   📄 "
                f"{resultat.get('cv_recommande', 'AUCUN')}"
            )

            if resultat.get(
                "blocage_critique",
                False
            ):

                print(
                    "   🚫 BLOCAGE CRITIQUE"
                )

            if resultat.get(
                "url"
            ):

                print(
                    f"   🔗 "
                    f"{resultat.get('url')}"
                )

    print()

    separateur()

    print(
        f"💾 Classement complet : "
        f"{RESULTATS_PATH}"
    )

    print(
        "🗄️ Base : "
        "agent_emploi_v2.db"
    )

    separateur()

    print()


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()