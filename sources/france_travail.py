import os
import requests

from dotenv import load_dotenv


load_dotenv()


TOKEN_URL = (
    "https://entreprise.francetravail.fr/"
    "connexion/oauth2/access_token"
    "?realm=/partenaire"
)

API_URL = (
    "https://api.francetravail.io/"
    "partenaire/offresdemploi/v2/offres/search"
)

SCOPE = "api_offresdemploiv2 o2dsoffre"


def obtenir_token():

    client_id = os.getenv(
        "FT_CLIENT_ID"
    )

    client_secret = os.getenv(
        "FT_CLIENT_SECRET"
    )

    if not client_id:
        raise RuntimeError(
            "FT_CLIENT_ID absent du fichier .env"
        )

    if not client_secret:
        raise RuntimeError(
            "FT_CLIENT_SECRET absent du fichier .env"
        )

    reponse = requests.post(
        TOKEN_URL,
        data={
            "grant_type":
                "client_credentials",

            "client_id":
                client_id,

            "client_secret":
                client_secret,

            "scope":
                SCOPE
        },
        timeout=30
    )

    reponse.raise_for_status()

    donnees = reponse.json()

    token = donnees.get(
        "access_token"
    )

    if not token:
        raise RuntimeError(
            "France Travail n'a pas renvoyé "
            "de token d'accès."
        )

    return token


def rechercher_un_mot_cle(
    token,
    mot_cle,
    nombre=20
):

    nombre = max(
        1,
        min(nombre, 150)
    )

    reponse = requests.get(
        API_URL,

        headers={
            "Authorization":
                f"Bearer {token}",

            "Accept":
                "application/json"
        },

        params={
            "motsCles":
                mot_cle,

            "range":
                f"0-{nombre - 1}"
        },

        timeout=30
    )

    # 204 = aucune offre trouvée
    if reponse.status_code == 204:
        return []

    if reponse.status_code not in (
        200,
        206
    ):
        raise RuntimeError(
            f"France Travail HTTP "
            f"{reponse.status_code} : "
            f"{reponse.text[:300]}"
        )

    donnees = reponse.json()

    return donnees.get(
        "resultats",
        []
    )


def rechercher_offres(
    recherches,
    nombre_par_recherche=20,
    afficher_progression=True
):

    token = obtenir_token()

    offres_uniques = {}

    total = len(
        recherches
    )

    for numero, recherche in enumerate(
        recherches,
        start=1
    ):

        if afficher_progression:

            print(
                f"[{numero}/{total}] "
                f"🔎 {recherche}"
            )

        try:

            resultats = rechercher_un_mot_cle(
                token=token,
                mot_cle=recherche,
                nombre=nombre_par_recherche
            )

        except Exception as erreur:

            print(
                f"   ⚠️ {erreur}"
            )

            continue

        for offre in resultats:

            identifiant = offre.get(
                "id"
            )

            if not identifiant:
                continue

            offres_uniques[
                identifiant
            ] = offre

        if afficher_progression:

            print(
                f"   → {len(resultats)} "
                f"offre(s)"
            )

    return list(
        offres_uniques.values()
    )