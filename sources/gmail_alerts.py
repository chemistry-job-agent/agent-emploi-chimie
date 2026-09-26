import base64
import json
import time

from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from sources.alert_inbox import (
    extraire_html,
    extraire_texte,
)

from sources.linkedin_alerts import (
    extraire_offres_linkedin_html,
    extraire_offres_linkedin_texte,
)

from sources.linkedin_enricher import (
    enrichir_offre_linkedin,
    linkedin_description_complete,
)


# ============================================================
# CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

CREDENTIALS_FILE = Path(
    "credentials.json"
)

TOKEN_FILE = Path(
    "token.json"
)

STATE_FILE = Path(
    "gmail_processed.json"
)


LABELS_EMPLOI = {
    "AGENT-EMPLOI/LinkedIn":
        "LinkedIn",

    "AGENT-EMPLOI/APEC":
        "Apec",

    "AGENT-EMPLOI/INDEED":
        "Indeed",
}


# ============================================================
# CONNEXION GMAIL
# ============================================================

def creer_nouvelle_authentification():

    if not CREDENTIALS_FILE.exists():

        raise FileNotFoundError(
            "credentials.json introuvable."
        )

    flow = (
        InstalledAppFlow
        .from_client_secrets_file(
            str(
                CREDENTIALS_FILE
            ),
            SCOPES,
        )
    )

    credentials = (
        flow.run_local_server(
            port=0
        )
    )

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    return credentials


def connexion_gmail():

    credentials = None

    if TOKEN_FILE.exists():

        try:

            credentials = (
                Credentials
                .from_authorized_user_file(
                    str(
                        TOKEN_FILE
                    ),
                    SCOPES,
                )
            )

        except Exception:

            credentials = None

    if credentials and credentials.valid:

        return build(
            "gmail",
            "v1",
            credentials=credentials,
        )

    if (
        credentials
        and credentials.expired
        and credentials.refresh_token
    ):

        try:

            credentials.refresh(
                Request()
            )

            TOKEN_FILE.write_text(
                credentials.to_json(),
                encoding="utf-8",
            )

        except RefreshError:

            print(
                "⚠️ Jeton Gmail expiré ou révoqué."
            )

            print(
                "🔐 Nouvelle authentification Gmail..."
            )

            try:

                TOKEN_FILE.unlink(
                    missing_ok=True
                )

            except Exception:
                pass

            credentials = (
                creer_nouvelle_authentification()
            )

    else:

        credentials = (
            creer_nouvelle_authentification()
        )

    return build(
        "gmail",
        "v1",
        credentials=credentials,
    )


# ============================================================
# MEMOIRE DES MAILS
# ============================================================

def charger_messages_traites():

    if not STATE_FILE.exists():
        return set()

    try:

        donnees = json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )

        return set(
            donnees
        )

    except Exception:

        return set()


def sauvegarder_messages_traites(
    messages
):

    STATE_FILE.write_text(
        json.dumps(
            sorted(
                messages
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# ============================================================
# LIBELLES GMAIL
# ============================================================

def recuperer_libelles(
    service
):

    resultat = (
        service.users()
        .labels()
        .list(
            userId="me"
        )
        .execute()
    )

    libelles = {}

    for libelle in resultat.get(
        "labels",
        [],
    ):

        nom = libelle.get(
            "name",
            "",
        )

        identifiant = libelle.get(
            "id",
            "",
        )

        if nom:

            libelles[
                nom
            ] = identifiant

    return libelles


def trouver_label_id(
    libelles,
    nom_recherche
):

    if nom_recherche in libelles:

        return libelles[
            nom_recherche
        ]

    recherche = (
        nom_recherche
        .casefold()
    )

    for nom_reel, identifiant in (
        libelles.items()
    ):

        if (
            nom_reel.casefold()
            == recherche
        ):

            return identifiant

    return None


# ============================================================
# DECODAGE GMAIL
# ============================================================

def decoder_base64url(
    data
):

    if not data:
        return ""

    try:

        contenu = (
            base64
            .urlsafe_b64decode(
                data.encode(
                    "utf-8"
                )
            )
        )

        return contenu.decode(
            "utf-8",
            errors="ignore",
        )

    except Exception:

        return ""


def parcourir_payload(
    payload,
    htmls,
    textes
):

    mime_type = payload.get(
        "mimeType",
        "",
    )

    body = payload.get(
        "body",
        {},
    )

    data = body.get(
        "data"
    )

    if data:

        contenu = decoder_base64url(
            data
        )

        if mime_type == "text/html":

            htmls.append(
                contenu
            )

        elif mime_type == "text/plain":

            textes.append(
                contenu
            )

    for partie in payload.get(
        "parts",
        [],
    ):

        parcourir_payload(
            partie,
            htmls,
            textes,
        )


def extraire_corps_email(
    message
):

    payload = message.get(
        "payload",
        {},
    )

    htmls = []
    textes = []

    parcourir_payload(
        payload,
        htmls,
        textes,
    )

    if htmls:

        return (
            "\n".join(
                htmls
            ),
            True,
        )

    return (
        "\n".join(
            textes
        ),
        False,
    )


# ============================================================
# HEADERS
# ============================================================

def extraire_headers(
    message
):

    resultat = {}

    headers = (
        message
        .get(
            "payload",
            {},
        )
        .get(
            "headers",
            [],
        )
    )

    for header in headers:

        nom = header.get(
            "name",
            "",
        )

        valeur = header.get(
            "value",
            "",
        )

        resultat[
            nom
        ] = valeur

    return resultat


# ============================================================
# MESSAGES D'UN LIBELLE
# ============================================================

def lister_messages(
    service,
    label_id,
    max_messages=100,
):

    messages = []

    page_token = None

    while (
        len(
            messages
        )
        < max_messages
    ):

        limite = min(
            100,
            max_messages
            - len(
                messages
            ),
        )

        arguments = {
            "userId":
                "me",

            "labelIds":
                [
                    label_id
                ],

            "maxResults":
                limite,
        }

        if page_token:

            arguments[
                "pageToken"
            ] = page_token

        resultat = (
            service.users()
            .messages()
            .list(
                **arguments
            )
            .execute()
        )

        messages.extend(
            resultat.get(
                "messages",
                [],
            )
        )

        page_token = resultat.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return messages[
        :max_messages
    ]


# ============================================================
# ENRICHISSEMENT LINKEDIN
# ============================================================

def enrichir_offres_linkedin(
    offres
):

    resultat = []

    total = len(
        offres
    )

    for index, offre in enumerate(
        offres,
        start=1,
    ):

        print(
            f"      🌐 LinkedIn "
            f"{index}/{total} : "
            f"{offre.get('titre', '')}"
        )

        offre = enrichir_offre_linkedin(
            offre
        )

        resultat.append(
            offre
        )

        donnees = offre.get(
            "donnees_brutes",
            {},
        )

        if not isinstance(
            donnees,
            dict
        ):

            donnees = {}

        if linkedin_description_complete(
            offre
        ):

            print(
                "         ✅ Description complète : "
                f"{len(offre.get('description', ''))} "
                "caractères"
            )

        else:

            print(
                "         ⚠️ Enrichissement incomplet : "
                f"{donnees.get('linkedin_enrichissement_erreur', '')}"
            )

        if index < total:

            time.sleep(
                1
            )

    return resultat


# ============================================================
# EXTRACTION SELON LA SOURCE
# ============================================================

def extraire_offres_source(
    contenu,
    est_html,
    source_attendue,
):

    # --------------------------------------------------------
    # LINKEDIN
    # --------------------------------------------------------

    if source_attendue == "LinkedIn":

        if est_html:

            offres = (
                extraire_offres_linkedin_html(
                    contenu
                )
            )

        else:

            offres = (
                extraire_offres_linkedin_texte(
                    contenu
                )
            )

        return enrichir_offres_linkedin(
            offres
        )

    # --------------------------------------------------------
    # APEC / INDEED
    # --------------------------------------------------------

    if est_html:

        offres = extraire_html(
            contenu
        )

    else:

        offres = extraire_texte(
            contenu
        )

    return [
        offre
        for offre in offres
        if offre.get(
            "source"
        )
        == source_attendue
    ]


# ============================================================
# TRAITEMENT D'UN MAIL
# ============================================================

def traiter_message(
    service,
    message_id,
    source_attendue,
):

    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )

    headers = extraire_headers(
        message
    )

    sujet = headers.get(
        "Subject",
        "",
    )

    expediteur = headers.get(
        "From",
        "",
    )

    date_email = headers.get(
        "Date",
        "",
    )

    contenu, est_html = (
        extraire_corps_email(
            message
        )
    )

    if not contenu.strip():

        print(
            "   ⚠️ Corps vide : "
            f"{sujet}"
        )

        return []

    offres = extraire_offres_source(
        contenu,
        est_html,
        source_attendue,
    )

    for offre in offres:

        source_id = str(
            offre.get(
                "source_id",
                "",
            )
        )

        if (
            not offre.get(
                "titre"
            )
            or offre.get(
                "titre"
            )
            == "Offre emploi chimie"
        ):

            offre[
                "titre"
            ] = (
                f"Offre {source_attendue} "
                f"{source_id}"
            )

        donnees = offre.get(
            "donnees_brutes",
            {},
        )

        if not isinstance(
            donnees,
            dict
        ):

            donnees = {
                "contenu":
                    str(
                        donnees
                    )
            }

        donnees[
            "gmail_message_id"
        ] = message_id

        donnees[
            "gmail_subject"
        ] = sujet

        donnees[
            "gmail_from"
        ] = expediteur

        donnees[
            "gmail_date"
        ] = date_email

        offre[
            "donnees_brutes"
        ] = donnees

    return offres


# ============================================================
# VALIDATION D'UN MAIL
# ============================================================

def verifier_mail_complet(
    source,
    offres
):

    if not offres:
        return False

    if source != "LinkedIn":
        return True

    for offre in offres:

        if not linkedin_description_complete(
            offre
        ):

            return False

    return True


# ============================================================
# COLLECTE PRINCIPALE
# ============================================================

def collecter_alertes_gmail(
    max_messages_par_source=100,
    afficher_progression=True,
    memoriser=True,
    retraiter_deja_traites=False,
):

    service = connexion_gmail()

    libelles = recuperer_libelles(
        service
    )

    deja_traites = (
        charger_messages_traites()
    )

    toutes_offres = []

    nouveaux_messages_traites = set(
        deja_traites
    )

    if afficher_progression:

        print()
        print(
            "📧 GMAIL - ALERTES EMPLOI"
        )

    for nom_libelle, source in (
        LABELS_EMPLOI.items()
    ):

        label_id = trouver_label_id(
            libelles,
            nom_libelle,
        )

        if not label_id:

            if afficher_progression:

                print(
                    f"⚠️ {nom_libelle} : "
                    "libellé absent"
                )

            continue

        messages = lister_messages(
            service,
            label_id,
            max_messages=
                max_messages_par_source,
        )

        if retraiter_deja_traites:

            nouveaux = messages

        else:

            nouveaux = [
                message
                for message in messages
                if message.get(
                    "id"
                )
                not in deja_traites
            ]

        if afficher_progression:

            print(
                f"📨 {source} : "
                f"{len(messages)} mail(s), "
                f"{len(nouveaux)} à traiter"
            )

        for message in nouveaux:

            message_id = message.get(
                "id"
            )

            if not message_id:
                continue

            try:

                offres = traiter_message(
                    service,
                    message_id,
                    source,
                )

                # ------------------------------------------------
                # LINKEDIN :
                # seules les offres enrichies vont dans le pipeline
                # ------------------------------------------------

                if source == "LinkedIn":

                    offres_valides = [
                        offre
                        for offre in offres
                        if linkedin_description_complete(
                            offre
                        )
                    ]

                else:

                    offres_valides = offres

                toutes_offres.extend(
                    offres_valides
                )

                if afficher_progression:

                    print(
                        f"   → {len(offres)} "
                        "offre(s) détectée(s)"
                    )

                    if source == "LinkedIn":

                        print(
                            f"   → {len(offres_valides)} "
                            "offre(s) enrichie(s) et exploitable(s)"
                        )

                mail_complet = verifier_mail_complet(
                    source,
                    offres,
                )

                # ------------------------------------------------
                # MEMOIRE
                # ------------------------------------------------

                if (
                    memoriser
                    and mail_complet
                ):

                    nouveaux_messages_traites.add(
                        message_id
                    )

                elif (
                    memoriser
                    and not mail_complet
                ):

                    if afficher_progression:

                        print(
                            "   ⚠️ Mail NON mémorisé : "
                            "il sera retenté au prochain lancement."
                        )

            except Exception as erreur:

                print(
                    f"   ❌ Mail {message_id} : "
                    f"{erreur}"
                )

    if memoriser:

        sauvegarder_messages_traites(
            nouveaux_messages_traites
        )

    # ========================================================
    # DEDOUBLONNAGE SOURCE + SOURCE_ID
    # ========================================================

    offres_uniques = []

    vus = set()

    for offre in toutes_offres:

        source = str(
            offre.get(
                "source",
                "",
            )
        )

        source_id = str(
            offre.get(
                "source_id",
                "",
            )
        )

        if source_id:

            cle = (
                source,
                source_id,
            )

        else:

            cle = (
                source,
                offre.get(
                    "url",
                    "",
                ),
                offre.get(
                    "titre",
                    "",
                ),
            )

        if cle in vus:
            continue

        vus.add(
            cle
        )

        offres_uniques.append(
            offre
        )

    if afficher_progression:

        print()

        print(
            f"✅ Gmail : "
            f"{len(offres_uniques)} "
            "offre(s) exploitable(s)"
        )

    return offres_uniques


# ============================================================
# TEST DIRECT NON DESTRUCTIF
# ============================================================

if __name__ == "__main__":

    offres = collecter_alertes_gmail(
        max_messages_par_source=20,
        afficher_progression=True,
        memoriser=False,
        retraiter_deja_traites=True,
    )

    print()

    print(
        "=" * 78
    )

    print(
        f"TOTAL EXPLOITABLE : "
        f"{len(offres)}"
    )

    print(
        "=" * 78
    )

    for offre in offres:

        print()

        print(
            f"SOURCE      : "
            f"{offre.get('source', '')}"
        )

        print(
            f"SOURCE ID   : "
            f"{offre.get('source_id', '')}"
        )

        print(
            f"TITRE       : "
            f"{offre.get('titre', '')}"
        )

        print(
            f"ENTREPRISE  : "
            f"{offre.get('entreprise', '')}"
        )

        print(
            f"LIEU        : "
            f"{offre.get('lieu', '')}"
        )

        donnees = offre.get(
            "donnees_brutes",
            {},
        )

        if not isinstance(
            donnees,
            dict
        ):

            donnees = {}

        print(
            f"ENRICHI     : "
            f"{donnees.get('linkedin_enrichi', '')}"
        )

        print(
            f"DESC.       : "
            f"{len(offre.get('description', '') or '')} "
            "caractères"
        )

        print(
            f"URL         : "
            f"{offre.get('url', '')}"
        )

        print(
            "-" * 78
        )