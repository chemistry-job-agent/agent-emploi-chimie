import base64
import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from sources.alert_inbox import (
    extraire_html,
    extraire_texte
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
    "AGENT-EMPLOI/LINKEDIN": "LinkedIn",
    "AGENT-EMPLOI/APEC": "Apec",
    "AGENT-EMPLOI/INDEED": "Indeed"
}


# ============================================================
# CONNEXION GMAIL
# ============================================================

def connexion_gmail():
    credentials = None

    if TOKEN_FILE.exists():

        credentials = (
            Credentials
            .from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES
            )
        )

    if (
        not credentials
        or not credentials.valid
    ):

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):

            credentials.refresh(
                Request()
            )

        else:

            if not CREDENTIALS_FILE.exists():

                raise FileNotFoundError(
                    "credentials.json introuvable."
                )

            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    str(CREDENTIALS_FILE),
                    SCOPES
                )
            )

            credentials = (
                flow.run_local_server(
                    port=0
                )
            )

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


# ============================================================
# MÉMOIRE DES MAILS DÉJÀ TRAITÉS
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
            sorted(messages),
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# ============================================================
# LIBELLÉS GMAIL
# ============================================================

def recuperer_libelles(service):

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
        []
    ):

        nom = libelle.get(
            "name",
            ""
        )

        identifiant = libelle.get(
            "id",
            ""
        )

        if nom:
            libelles[
                nom
            ] = identifiant

    return libelles


# ============================================================
# DÉCODAGE DU CONTENU GMAIL
# ============================================================

def decoder_base64url(data):

    if not data:
        return ""

    try:

        contenu = (
            base64.urlsafe_b64decode(
                data.encode(
                    "utf-8"
                )
            )
        )

        return contenu.decode(
            "utf-8",
            errors="ignore"
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
        ""
    )

    body = payload.get(
        "body",
        {}
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
        []
    ):

        parcourir_payload(
            partie,
            htmls,
            textes
        )


def extraire_corps_email(
    message
):

    payload = message.get(
        "payload",
        {}
    )

    htmls = []
    textes = []

    parcourir_payload(
        payload,
        htmls,
        textes
    )

    if htmls:

        return (
            "\n".join(htmls),
            True
        )

    return (
        "\n".join(textes),
        False
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
            {}
        )
        .get(
            "headers",
            []
        )
    )

    for header in headers:

        nom = header.get(
            "name",
            ""
        )

        valeur = header.get(
            "value",
            ""
        )

        resultat[
            nom
        ] = valeur

    return resultat


# ============================================================
# MESSAGES D'UN LIBELLÉ
# ============================================================

def lister_messages(
    service,
    label_id,
    max_messages=100
):

    messages = []

    page_token = None

    while (
        len(messages)
        < max_messages
    ):

        limite = min(
            100,
            max_messages
            - len(messages)
        )

        resultat = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=[
                    label_id
                ],
                maxResults=limite,
                pageToken=page_token
            )
            .execute()
        )

        messages.extend(
            resultat.get(
                "messages",
                []
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
# EXTRACTION D'UN MAIL
# ============================================================

def traiter_message(
    service,
    message_id,
    source_attendue
):

    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full"
        )
        .execute()
    )

    headers = extraire_headers(
        message
    )

    sujet = headers.get(
        "Subject",
        ""
    )

    expediteur = headers.get(
        "From",
        ""
    )

    date_email = headers.get(
        "Date",
        ""
    )

    contenu, est_html = (
        extraire_corps_email(
            message
        )
    )

    if not contenu.strip():

        print(
            f"   ⚠️ Corps vide : "
            f"{sujet}"
        )

        return []

    if est_html:

        offres = extraire_html(
            contenu
        )

    else:

        offres = extraire_texte(
            contenu
        )

    # --------------------------------------------------------
    # GARDE UNIQUEMENT LA SOURCE DU LIBELLÉ
    # --------------------------------------------------------

    offres = [
        offre
        for offre in offres
        if offre.get(
            "source"
        )
        == source_attendue
    ]

    # --------------------------------------------------------
    # AJOUT DES MÉTADONNÉES GMAIL
    # --------------------------------------------------------

    for offre in offres:

        source_id = str(
            offre.get(
                "source_id",
                ""
            )
        )

        # Évite que plusieurs offres dont le titre
        # n'a pas été extrait aient exactement le
        # même fingerprint SQLite.
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
            {}
        )

        if not isinstance(
            donnees,
            dict
        ):

            donnees = {
                "contenu":
                    str(donnees)
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
# COLLECTE PRINCIPALE
# ============================================================

def collecter_alertes_gmail(
    max_messages_par_source=100,
    afficher_progression=True
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

        label_id = libelles.get(
            nom_libelle
        )

        if not label_id:

            if afficher_progression:

                print(
                    f"⚠️ {nom_libelle} : "
                    f"libellé absent"
                )

            continue

        messages = lister_messages(
            service,
            label_id,
            max_messages=
                max_messages_par_source
        )

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
                f"{len(nouveaux)} nouveau(x)"
            )

        for message in nouveaux:

            message_id = (
                message.get(
                    "id"
                )
            )

            if not message_id:
                continue

            try:

                offres = traiter_message(
                    service,
                    message_id,
                    source
                )

                toutes_offres.extend(
                    offres
                )

                if afficher_progression:

                    print(
                        f"   → "
                        f"{len(offres)} offre(s) "
                        f"extraite(s)"
                    )

                # On mémorise uniquement le mail si
                # l'analyse du message s'est déroulée
                # correctement.
                nouveaux_messages_traites.add(
                    message_id
                )

            except Exception as erreur:

                print(
                    f"   ❌ Mail "
                    f"{message_id} : "
                    f"{erreur}"
                )

    sauvegarder_messages_traites(
        nouveaux_messages_traites
    )

    # ========================================================
    # DÉDOUBLONNAGE EXACT SOURCE / ID
    # ========================================================

    offres_uniques = []

    vus = set()

    for offre in toutes_offres:

        cle = (
            offre.get(
                "source",
                ""
            ),

            offre.get(
                "source_id",
                ""
            )
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
            f"nouvelle(s) offre(s)"
        )

    return offres_uniques


# ============================================================
# TEST DIRECT
# ============================================================

if __name__ == "__main__":

    offres = collecter_alertes_gmail()

    print()

    print("=" * 70)

    print(
        f"TOTAL EXTRAIT : "
        f"{len(offres)}"
    )

    print("=" * 70)

    for offre in offres:

        print()

        print(
            f"[{offre.get('source')}] "
            f"{offre.get('titre')}"
        )

        print(
            offre.get(
                "url",
                ""
            )
        )