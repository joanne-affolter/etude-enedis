import streamlit as st
from st_supabase_connection import SupabaseConnection
import pickle
import os
import json
import base64
import zlib

st.set_page_config(layout="wide", page_title="Étude ENEDIS")

import datetime
from helpers import (
    html_to_pdf,
    insert_image_to_fields,
    insert_images_to_fields,
    render_prefinancement_table_html,
    generate_material_html_table,
    process_excel,
    insert_images_to_fields_titles,
    MATERIEL_RACCORDEMENT_AU_RESEAU,
    MATERIEL_ADAPTATION_PIED_DE_COLONNE,
    MATERIEL_CONSTRUCTION_OUVRAGES_COLLECTIFS,
    MATERIEL_CONSTRUCTION_TRAVEE,
    MATERIEL_CREATION_DI,
    MATERIEL_CABLES_ET_ACCESSOIRES,
    MATERIEL_TRAVAUX_ANNEXES,
    MATERIEL_TRAVAUX_ANNEXES_EXT,
    RACCORDEMENT,
    DERIVATION_COLLECTIVE,
    DERIVATION_COLLECTIVE_EXTERIEUR,
    DI_COFFRET_EXPLOITATION,
    MATERIEL_DI_BOX_FERME,
    MATERIEL_DI_MUR_EXTERIEUR,
    MATERIEL_DI_PARKING_SOL,
    EXTENSION_RESEAU,
)


def save_state(project_name: str) -> bool:
    dir_path = "Streamlit_app/saved_states"
    os.makedirs(dir_path, exist_ok=True)

    filepath = os.path.join(dir_path, f"{project_name}.pkl")

    with open(filepath, "wb") as f:
        pickle.dump(dict(st.session_state), f)

    return True


def list_saved_states_old():
    path = "Streamlit_app/saved_states"
    if not os.path.exists(path):
        os.makedirs(path)
        return []

    files = [f.replace(".pkl", "") for f in os.listdir(path) if f.endswith(".pkl")]
    return files


def list_saved_states():
    conn = st.connection("supabase", type=SupabaseConnection)
    result = conn.client.table("projects_state").select("project_name").execute()
    if result.data:
        project_names = []

        for row in result.data:
            if row["project_name"] not in project_names:
                project_names.append(row["project_name"])

        return project_names
    return []


def load_state(project_name: str) -> bool:
    filepath = f"Streamlit_app/saved_states/{project_name}.pkl"
    if not os.path.exists(filepath):
        st.sidebar.error(f"Aucun projet trouvé avec le nom **{project_name}** ❌")
        return False

    with open(filepath, "rb") as f:
        saved_state = pickle.load(f)
        print(saved_state)

    # Empêche de modifier les clés déjà utilisées dans des widgets
    forbidden_keys = ["nom_projet_sidebar"]

    for key, value in saved_state.items():
        if key not in forbidden_keys:
            st.session_state[key] = value

    st.rerun()  # 🔁 rerun pour forcer les widgets à prendre les valeurs chargées

    return True


MAX_CHUNK_SIZE = 500_000  # 500 KB limit per row (safe for Supabase free tier)


def save_state_to_supabase(project_name, chunk_size=50000):
    conn = st.connection("supabase", type=SupabaseConnection)

    try:
        update_dynamic_lists_before_saving()
        # ➔ Compress first!
        pickled_state = pickle.dumps(dict(st.session_state))
        compressed = zlib.compress(pickled_state)
        encoded = base64.b64encode(compressed).decode("utf-8")

        # ➔ Split encoded string into chunks
        chunks = [
            encoded[i : i + chunk_size] for i in range(0, len(encoded), chunk_size)
        ]

        # ➔ Delete existing rows for this project_name
        conn.client.table("projects_state").delete().eq(
            "project_name", project_name
        ).execute()

        # ➔ Insert new chunks
        for idx, chunk in enumerate(chunks):
            conn.client.table("projects_state").insert(
                {"project_name": project_name, "state": chunk, "part_number": idx}
            ).execute()

        st.toast(
            f"Projet **{project_name}** sauvegardé en {len(chunks)} morceau(x) (compressed pickled)"
        )
        st.rerun()

        return True

    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        return False


def load_state_from_supabase(project_name):
    conn = st.connection("supabase", type=SupabaseConnection)

    try:
        # 1. Fetch all chunks for the project
        result = (
            conn.client.table("projects_state")
            .select("part_number, state")
            .eq("project_name", project_name)
            .order("part_number", desc=False)
            .execute()
        )

        if not result.data:
            st.warning(f"❌ Projet **{project_name}** non trouvé.")
            return False

        # 2. Reconstruct the full encoded string
        chunks_sorted = sorted(result.data, key=lambda x: x["part_number"])
        full_encoded = "".join(chunk["state"] for chunk in chunks_sorted)

        # 3. Decode from base64
        decoded_bytes = base64.b64decode(full_encoded)

        try:
            # Try to decompress
            pickled = zlib.decompress(decoded_bytes)
            loaded_state = pickle.loads(pickled)
            st.toast(f"✅ Projet **{project_name}** chargé (compressed version)")
        except zlib.error:
            # If decompression fails, fallback to direct pickle
            loaded_state = pickle.loads(decoded_bytes)
            st.toast(f"✅ Projet **{project_name}** chargé (uncompressed version)")

        # 4. Restore session state
        for key, value in loaded_state.items():
            st.session_state[key] = value

        st.rerun()
        return True

    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return False


def delete_state_from_supabase(project_name):
    conn = st.connection("supabase", type=SupabaseConnection)
    try:
        result = (
            conn.client.table("projects_state")
            .delete()
            .eq("project_name", project_name)
            .execute()
        )
        st.toast(f"Projet **{project_name}** supprimé avec succès ✅")
        st.rerun()  # pour que les widgets prennent les nouvelles valeurs

        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression : {e}")
        return False


def init_state():
    defaults = {
        # Infos Générales
        "adresse_site": "",
        "num_affaire": "",
        "date_saisie": datetime.date.today(),
        "date_construction_immeuble": datetime.date.today(),
        "avec_sans_prefinancement": "Non",
        "parking_interieur": "Non",
        "parking_exterieur": "Non",
        "nombre_parkings": 1,
        "nombre_de_niveaux": 1,
        "nombre_places_stationnement": 0,
        # Infos Fonctionnelles
        "date_visite_technique": datetime.date.today(),
        "date_ag": datetime.date.today(),
        "date_debut_chantier": datetime.date.today(),
        "date_fin_chantier": datetime.date.today(),
        # Contacts
        "reference_pole_enedis": "",
        "adresse_pole_enedis": "",
        "nom_charge_projet": "",
        "tel_charge_projet": "",
        "email_charge_projet": "",
        "nom_prestataire": "",
        "tel_prestataire": "",
        "email_prestataire": "",
        "nom_syndic": "",
        "adresse_syndic": "",
        "nom_interlocuteur_syndic": "",
        "tel_syndic": "",
        "email_syndic": "",
        # Infos Techniques
        "description_technique_0": "",
        "description_technique_1": "",
        "description_technique_2": "",
        "nb_places_0": "",
        "nb_places_1": "",
        "nb_places_2": "",
        "puissance_irve_0": "",
        "puissance_irve_1": "",
        "puissance_irve_2": "",
        "type_chauffage": "Electrique Individuel",
        "coffret": "ECP2D",
        "plan_reseau": [],
        "documents": None,
        # Accès
        "moyen_acces_copro": "",
        "moyen_acces_parking": "",
        "facade_acces_copro": [],
        "facade_acces_parking": [],
        # Préfinancement
        "prefinancement_enedis": [],
        "prefinancement_demandeur": [],
        # Images
        "etats_avant_travaux": {},
        "plan_reseau2": [],
        "img_arrivee_reseau": {},
        "img_parametres_generaux": {},
        "img_distribution_parking": {},
        "img_plans_apres_travaux": {},
        "img_synoptique": {},
        "img_calcul_colonne_electrique": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def section_infos_generales():
    st.header("Informations Générales")
    st.session_state.adresse_site = st.text_input(
        "Adresse Site", value=st.session_state.adresse_site
    )
    st.session_state.num_affaire = st.text_input(
        "Numéro d'affaire", value=st.session_state.num_affaire
    )
    st.session_state.date_construction_immeuble = st.date_input(
        "Date de construction de l'immeuble",
        value=st.session_state.date_construction_immeuble,
    )
    st.session_state.avec_sans_prefinancement = st.radio(
        "Préfinancement",
        ["Oui", "Non"],
        horizontal=True,
        index=["Oui", "Non"].index(st.session_state.avec_sans_prefinancement),
    )

    st.write("")
    st.write("")
    st.session_state.parking_interieur = st.radio(
        "Parking intérieur",
        ["Oui", "Non"],
        horizontal=True,
        index=["Oui", "Non"].index(st.session_state.parking_interieur),
    )
    st.session_state.parking_exterieur = st.radio(
        "Parking extérieur",
        ["Oui", "Non"],
        horizontal=True,
        index=["Oui", "Non"].index(st.session_state.parking_exterieur),
    )
    st.session_state.nombre_parkings = st.number_input(
        "Nombre de parkings",
        value=st.session_state.nombre_parkings,
    )
    st.session_state.nombre_de_niveaux = st.number_input(
        "Nombre de niveaux",
        step=1,
        min_value=1,
        value=st.session_state.nombre_de_niveaux,
    )
    st.session_state.nombre_places_stationnement = st.number_input(
        "Nombre de places de stationnement (total)",
        value=st.session_state.nombre_places_stationnement,
    )


def section_infos_fonctionnelles():
    st.header("Informations Fonctionnelles")
    st.session_state.date_visite_technique = st.date_input(
        "Date de visite technique", value=st.session_state.date_visite_technique
    )
    st.session_state.date_ag = st.date_input("Date AG", value=st.session_state.date_ag)
    st.session_state.date_debut_chantier = st.date_input(
        "Date de début de chantier", value=st.session_state.date_debut_chantier
    )
    st.session_state.date_fin_chantier = st.date_input(
        "Date de fin de chantier", value=st.session_state.date_fin_chantier
    )


def update_dynamic_lists_before_saving():
    dynamic_mappings = {
        "nb_places": int(st.session_state.get("nombre_parkings", 1)),
        "puissance_irve": int(st.session_state.get("nombre_parkings", 1)),
        "description_technique": int(st.session_state.get("nombre_parkings", 1)),
    }

    for field_name, count in dynamic_mappings.items():
        new_list = []
        for i in range(count):
            widget_key = (
                f"{field_name[:-1]}_{i}"
                if field_name != "description_technique"
                else f"description_{i}"
            )
            new_list.append(
                st.session_state.get(
                    widget_key,
                    0
                    if "nb_places" in field_name or "puissance_irve" in field_name
                    else "",
                )
            )
        st.session_state[field_name] = new_list


def section_technique():
    st.header("Informations Techniques")

    st.session_state.type_chauffage = st.selectbox(
        "Type de chauffage",
        [
            "Electrique Individuel",
            "Electrique Collectif",
            "Gaz Individuel",
            "Gaz Collectif",
            "Autre",
        ],
        index=[
            "Electrique Individuel",
            "Electrique Collectif",
            "Gaz Individuel",
            "Gaz Collectif",
            "Autre",
        ].index(st.session_state.type_chauffage),
    )

    st.session_state.coffret = st.selectbox(
        "Coffret",
        ["ECP2D", "ECP3D", "REMBT"],
        index=["ECP2D", "ECP3D", "REMBT"].index(st.session_state.coffret),
    )

    st.write("")
    st.write("")
    st.markdown("#### 📝 Description de la solution technique")

    for i in range(int(st.session_state.nombre_parkings)):
        description_label = f"Parking {i + 1}"

        var_name = f"description_technique_{i}"

        # Initialize if missing (important!)
        if var_name not in st.session_state:
            st.session_state[var_name] = ""

        st.text_input(
            f"Description de la solution technique - {description_label}",
            value=st.session_state[var_name],
            key=f"description_technique_{i}",
        )

    st.write("")
    st.write("")
    st.markdown("#### 🚘 Nombre de places par parking")
    for i in range(int(st.session_state.nombre_parkings)):
        label = f"Parking {i + 1}"

        var_name = f"nb_places_{i}"

        if var_name not in st.session_state:
            st.session_state[var_name] = 0

        st.number_input(
            f"Nombre de places - {label}",
            value=st.session_state[var_name],
            key=f"nb_places_{i}",
        )

    st.write("")
    st.write("")
    st.markdown("#### ⚡️ Puissance IRVE")
    for i in range(int(st.session_state.nombre_parkings)):
        puissance_irve_label = f"Parking {i + 1}"

        var_name = f"puissance_irve_{i}"

        if var_name not in st.session_state:
            st.session_state[var_name] = 0

        st.number_input(
            f"Puissance IRVE - {puissance_irve_label} (KVA)",
            value=st.session_state[var_name],
            key=f"puissance_irve_{i}",
        )

    st.write("")
    st.write("")
    st.markdown("#### 📷 Photos")
    plan_reseau_upload = st.file_uploader(
        "Plan Réseau (Avant Travaux)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="plan_reseau_key",
    )
    if plan_reseau_upload:
        st.session_state["plan_reseau"] = plan_reseau_upload

    if len(st.session_state.plan_reseau) > 0:
        if st.button(f"Supprimer les photos", key=f"delete_plan_reseau"):
            st.session_state.plan_reseau = []

    if len(st.session_state.plan_reseau) > 0:
        for img in st.session_state["plan_reseau"]:
            st.image(img, width=200)
            st.write("")
            st.write("")

    st.write("")
    st.write("")
    st.markdown("#### 📄 Documents")
    st.markdown(
        """Remplissez le fichier 'Template Etude ENEDIS - Solution Technique' sur Google Sheets, puis téléchargez-le au format Excel. Vous pouvez rajouter dupliquer la feuille 'Parking' si vous en avez plus d'un."""
    )
    documents_upload = st.file_uploader(
        "Description de la solution technique",
        type=["xlsx"],
        key="documents_key",
    )

    if documents_upload:
        st.session_state["documents"] = documents_upload
    if st.session_state.documents:
        doc = st.session_state["documents"]
        st.markdown(
            doc.name,
            unsafe_allow_html=True,
        )


def section_contact():
    st.header("Contact")

    st.markdown("#### Pôle ENEDIS")
    st.session_state.reference_pole_enedis = st.text_input(
        "Référence - Pôle ENEDIS", value=st.session_state.reference_pole_enedis
    )
    st.session_state.adresse_pole_enedis = st.text_input(
        "Adresse - Pôle ENEDIS", value=st.session_state.adresse_pole_enedis
    )

    st.write("")
    st.write("")
    st.markdown("#### Maître d'ouvrage")
    st.session_state.nom_charge_projet = st.text_input(
        "Nom - Maître d'ouvrage", value=st.session_state.nom_charge_projet
    )
    st.session_state.tel_charge_projet = st.text_input(
        "Téléphone - Maître d'ouvrage", value=st.session_state.tel_charge_projet
    )
    st.session_state.email_charge_projet = st.text_input(
        "Email - Maître d'ouvrage", value=st.session_state.email_charge_projet
    )

    st.write("")
    st.write("")
    st.markdown("#### Prestataire")
    st.session_state.nom_prestataire = st.text_input(
        "Nom - Prestataire", value=st.session_state.nom_prestataire
    )
    st.session_state.tel_prestataire = st.text_input(
        "Téléphone - Prestataire", value=st.session_state.tel_prestataire
    )
    st.session_state.email_prestataire = st.text_input(
        "Email - Prestataire", value=st.session_state.email_prestataire
    )

    st.write("")
    st.write("")
    st.markdown("#### Syndic")
    st.session_state.nom_syndic = st.text_input(
        "Nom - Syndic", value=st.session_state.nom_syndic
    )
    st.session_state.adresse_syndic = st.text_input(
        "Adresse - Syndic", value=st.session_state.adresse_syndic
    )

    st.write("")
    st.write("")
    st.markdown("#### Interlocuteur Syndic")
    st.session_state.nom_interlocuteur_syndic = st.text_input(
        "Nom - Interlocuteur Syndic", value=st.session_state.nom_interlocuteur_syndic
    )
    st.session_state.tel_syndic = st.text_input(
        "Téléphone - Interlocuteur Syndic", value=st.session_state.tel_syndic
    )
    st.session_state.email_syndic = st.text_input(
        "Email - Interlocuteur Syndic", value=st.session_state.email_syndic
    )


def section_acces():
    st.header("Accès")
    st.session_state.moyen_acces_copro = st.text_input(
        "Moyen d'accès à la copropriété", value=st.session_state.moyen_acces_copro
    )
    st.session_state.moyen_acces_parking = st.text_input(
        "Moyen d'accès au parking", value=st.session_state.moyen_acces_parking
    )

    st.write("")
    st.write("")
    st.markdown("#### 📷 Photos")
    copro_upload = st.file_uploader(
        "Façade et accès copropriété",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="facade_acces_copro_key",
    )
    if copro_upload:
        st.session_state["facade_acces_copro"] = copro_upload

    if len(st.session_state.facade_acces_copro) > 0:
        if st.button(f"Supprimer les photos", key=f"delete_facade_acces_copro"):
            st.session_state.facade_acces_copro = []

    if len(st.session_state.facade_acces_copro) > 0:
        for img in st.session_state["facade_acces_copro"]:
            st.image(img, width=200)
            st.write("")
            st.write("")

    parking_upload = st.file_uploader(
        "Façade et accès parking",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="facade_acces_parking_key",
    )
    if parking_upload:
        st.session_state["facade_acces_parking"] = parking_upload

    if len(st.session_state.facade_acces_parking) > 0:
        if st.button(f"Supprimer les photos", key=f"delete_facade_acces_parking"):
            st.session_state.facade_acces_parking = []

    if len(st.session_state.facade_acces_parking) > 0:
        for img in st.session_state["facade_acces_parking"]:
            st.image(img, width=200)
            st.write("")
            st.write("")


def section_images():
    st.header("Images à fournir")

    st.markdown("#### Etat avant Travaux")
    uploaded_file_arrivee_reseau = st.file_uploader(
        "Arrivée réseau",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="arrivee_reseau_key",
    )
    if uploaded_file_arrivee_reseau:
        st.session_state.etats_avant_travaux["Arrivée réseau"] = (
            uploaded_file_arrivee_reseau
        )

    if len(st.session_state.etats_avant_travaux.get("Arrivée réseau", [])) > 0:
        if st.button(f"Supprimer les photos", key=f"delete_arrivee_reseau"):
            st.session_state.etats_avant_travaux["Arrivée réseau"] = []

    if len(st.session_state.etats_avant_travaux.get("Arrivée réseau", [])) > 0:
        for img in st.session_state.etats_avant_travaux["Arrivée réseau"]:
            st.image(img, width=200)
            st.write("")
            st.write("")

    for i in range(int(st.session_state.nombre_de_niveaux)):
        niveau_label = f"Niveau -{i}" if i > 0 else "Niveau 0"

        uploaded_files = st.file_uploader(
            f"{niveau_label}",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"etats_avant_travaux_{niveau_label}",
        )

        if uploaded_files:
            st.session_state.etats_avant_travaux[niveau_label] = uploaded_files

        if len(st.session_state.etats_avant_travaux.get(niveau_label, [])) > 0:
            if st.button(f"Supprimer les photos", key=f"delete_{niveau_label}"):
                st.session_state.etats_avant_travaux[niveau_label] = []

        if len(st.session_state.etats_avant_travaux.get(niveau_label, [])) > 0:
            for img in st.session_state.etats_avant_travaux[niveau_label]:
                st.image(img, width=200)
                st.write("")
                st.write("")

    st.write("")
    st.write("")
    st.markdown("#### Etat après Travaux")

    st.markdown(f"##### 📍 Plan Réseau")
    plan_reseau_upload2 = st.file_uploader(
        "",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="plan_reseau2_key",
    )
    if plan_reseau_upload2:
        st.session_state["plan_reseau2"] = plan_reseau_upload2

    if len(st.session_state.plan_reseau2) > 0:
        if st.button(f"Supprimer les photos", key=f"delete_plan_reseau2"):
            st.session_state.plan_reseau2 = []

    if len(st.session_state.plan_reseau2) > 0:
        for img in st.session_state["plan_reseau2"]:
            st.image(img, width=200)
            st.write("")
            st.write("")

    render_image_section("Paramètres généraux", "img_parametres_generaux")
    render_image_section("Arrivée réseau et pied de colonne", "img_arrivee_reseau")
    render_image_section("Distribution du parking", "img_distribution_parking")
    render_image_section("Plans après travaux", "img_plans_apres_travaux")
    render_image_section("Synoptique", "img_synoptique")
    render_image_section(
        "Calcul de colonne électrique", "img_calcul_colonne_electrique"
    )


def section_prefinancement():
    st.header("Préfinancement")

    st.markdown("#### Travaux annexes - ENEDIS")

    descriptifs = [
        "Confection de niche sur façade, encastrement du coffret sur façade, pose de coffret sur mur, etc.",
        "Création d'un placard technique",
        "Création de tranchée, pose de fourreaux",
        "Percements supérieurs à 50 mm, etc.",
        "Fourniture et pose de socles pour accueillir les bornes, etc.",
        "Études et travaux spécialisés commandées à des prestataires habilités",
        "Fourniture et pose d'armoire, coffret pour l'infrastructure collective, etc.",
        "Déroulage de la terre C15-100 en partie collective (hors Dérivation Individuelle)",
        "En fonction du DTA (Dossier Technique d'Amiante) ou si absence de DTA, réalisation d’un RAT (Repérage Avant Travaux).",
        "Réalisation de travaux en sous-section IV si présence d'amiante",
    ]

    if "prefinancement_enedis" not in st.session_state:
        st.session_state.prefinancement_enedis = []

    for i, texte in enumerate(descriptifs):
        checked = st.checkbox(texte, key=f"pref_check_{i}")

        if checked and texte not in st.session_state.prefinancement_enedis:
            st.session_state.prefinancement_enedis.append(texte)
        elif not checked and texte in st.session_state.prefinancement_enedis:
            st.session_state.prefinancement_enedis.remove(texte)

    st.write("")
    st.write("")
    st.markdown("#### Travaux annexes - Demandeur")
    descriptifs = [
        "Pose de caniveaux permettant le passage de canalisations électriques, création de dos d’âne sur toit terrasse, etc.",
        "Terrassement sur revêtement particulier",
        "Réalisation DTA (Dossier Technique d'Amiante), placé sous la responsabilité du Demandeur",
        "Travaux imposés par la norme C15-100",
    ]

    if "prefinancement_demandeur" not in st.session_state:
        st.session_state.prefinancement_demandeur = []

    for i, texte in enumerate(descriptifs):
        checked = st.checkbox(texte, key=f"prefinancement_demandeur_{i}")

        if checked and texte not in st.session_state.prefinancement_demandeur:
            st.session_state.prefinancement_demandeur.append(texte)
        elif not checked and texte in st.session_state.prefinancement_demandeur:
            st.session_state.prefinancement_demandeur.remove(texte)


def materiel():
    st.header("Matériel")

    st.subheader("Matériel pour Parking Intérieur")

    with st.expander("Raccordement au réseau (hors câble)", expanded=False):
        if "materiel_interieur_raccordement_au_reseau" not in st.session_state:
            st.session_state.materiel_interieur_raccordement_au_reseau = {
                row["code"]: 0 for row in MATERIEL_RACCORDEMENT_AU_RESEAU
            }
        for row in MATERIEL_RACCORDEMENT_AU_RESEAU:
            st.session_state.materiel_interieur_raccordement_au_reseau[row["code"]] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_interieur_raccordement_au_reseau[
                        row["code"]
                    ],
                    key=f"qte_{row['code']}",
                )
            )

    with st.expander("Construction adaptation du pied de colonne", expanded=False):
        if "materiel_interieur_adaptation_pied_de_colonne" not in st.session_state:
            st.session_state.materiel_interieur_adaptation_pied_de_colonne = {
                row["code"]: 0 for row in MATERIEL_ADAPTATION_PIED_DE_COLONNE
            }
        for row in MATERIEL_ADAPTATION_PIED_DE_COLONNE:
            st.session_state.materiel_interieur_adaptation_pied_de_colonne[
                row["code"]
            ] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_interieur_adaptation_pied_de_colonne[
                    row["code"]
                ],
                key=f"qte_{row['code']}",
            )

    with st.expander(
        "Construction des ouvrages collectifs (hors câble)", expanded=False
    ):
        if "materiel_interieur_construction_ouvrages" not in st.session_state:
            st.session_state.materiel_interieur_construction_ouvrages = {
                row["code"]: 0 for row in MATERIEL_CONSTRUCTION_OUVRAGES_COLLECTIFS
            }
        for row in MATERIEL_CONSTRUCTION_OUVRAGES_COLLECTIFS:
            st.session_state.materiel_interieur_construction_ouvrages[row["code"]] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_interieur_construction_ouvrages[
                        row["code"]
                    ],
                    key=f"qte_{row['code']}",
                )
            )

    with st.expander("Construction d’une travée (hors câble)", expanded=False):
        if "materiel_construction_travee" not in st.session_state:
            st.session_state.materiel_construction_travee = {
                row["code"]: 0 for row in MATERIEL_CONSTRUCTION_TRAVEE
            }
        for row in MATERIEL_CONSTRUCTION_TRAVEE:
            st.session_state.materiel_construction_travee[row["code"]] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_construction_travee[row["code"]],
                    key=f"qte_{row['code']}",
                )
            )

    with st.expander("Création des DI", expanded=False):
        if "materiel_creation_di" not in st.session_state:
            st.session_state.materiel_creation_di = {
                row["code"]: 0 for row in MATERIEL_CREATION_DI
            }
        for row in MATERIEL_CREATION_DI:
            st.session_state.materiel_creation_di[row["code"]] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_creation_di[row["code"]],
                key=f"qte_creation_di_{row['code']}",
            )

    with st.expander("Câbles et accessoires installés", expanded=False):
        if "materiel_cables_et_accessoires" not in st.session_state:
            st.session_state.materiel_cables_et_accessoires = {
                row["code"] or row["libelle"]: 0
                for row in MATERIEL_CABLES_ET_ACCESSOIRES
            }
        for row in MATERIEL_CABLES_ET_ACCESSOIRES:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_cables_et_accessoires[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_cables_et_accessoires[key],
                key=f"qte_cables_{key}",
            )

    with st.expander("Travaux Annexes", expanded=False):
        if "materiel_travaux_annexes" not in st.session_state:
            st.session_state.materiel_travaux_annexes = {
                row["code"] or row["libelle"]: 0 for row in MATERIEL_TRAVAUX_ANNEXES
            }
        for row in MATERIEL_TRAVAUX_ANNEXES:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_travaux_annexes[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_travaux_annexes[key],
                key=f"qte_travaux_annexes_{key}",
            )

    st.subheader("Matériel pour Parking Extérieur")

    with st.expander(
        "Extension réseau (départ monobloc, etc.), liaison réseau, etc.", expanded=False
    ):
        if "extension_reseau" not in st.session_state:
            st.session_state.extension_reseau = {
                row["code"] or row["libelle"]: 0 for row in EXTENSION_RESEAU
            }

        for row in EXTENSION_RESEAU:
            key = row["code"] or row["libelle"]
            if key not in st.session_state.extension_reseau:
                st.session_state.extension_reseau[key] = 0

            st.session_state.extension_reseau[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.extension_reseau[key],
                key=f"qte_extension_reseau_{key}",
            )
    with st.expander("Raccordement", expanded=False):
        if "materiel_raccordement" not in st.session_state:
            st.session_state.materiel_raccordement = {
                row["code"] or row["libelle"]: 0 for row in RACCORDEMENT
            }
        for row in RACCORDEMENT:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_raccordement[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_raccordement[key],
                key=f"qte_raccordement_{key}",
            )

    with st.expander(
        "Câble dérivation collective (valeurs pré-remplies pour si pleine terre, sinon à adapter)",
        expanded=False,
    ):
        if "materiel_derivation_collective" not in st.session_state:
            st.session_state.materiel_derivation_collective = {
                row["code"] or row["libelle"]: 0 for row in DERIVATION_COLLECTIVE
            }
        for row in DERIVATION_COLLECTIVE:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_derivation_collective[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_derivation_collective[key],
                key=f"qte_derivation_collective_{key}",
            )

    with st.expander(
        "Dérivation collective (plutôt appelée travée en parking extérieur)",
        expanded=False,
    ):
        if "materiel_derivation_parking_exterieur" not in st.session_state:
            st.session_state.materiel_derivation_parking_exterieur = {
                row["code"] or row["libelle"]: 0
                for row in DERIVATION_COLLECTIVE_EXTERIEUR
            }
        for row in DERIVATION_COLLECTIVE_EXTERIEUR:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_derivation_parking_exterieur[key] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_derivation_parking_exterieur[key],
                    key=f"qte_derivation_parking_exterieur_{key}",
                )
            )

    with st.expander("DI coffret exploitation", expanded=False):
        if "materiel_di_coffret_exploitation" not in st.session_state:
            st.session_state.materiel_di_coffret_exploitation = {
                row["code"] or row["libelle"]: 0 for row in DI_COFFRET_EXPLOITATION
            }
        for row in DI_COFFRET_EXPLOITATION:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_coffret_exploitation[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_coffret_exploitation[key],
                key=f"qte_di_coffret_exploitation_{key}",
            )

    with st.expander("Travaux Annexes", expanded=False):
        if "materiel_travaux_annexes_ext" not in st.session_state:
            st.session_state.materiel_travaux_annexes_ext = {
                row["code"] or row["libelle"]: 0 for row in MATERIEL_TRAVAUX_ANNEXES_EXT
            }
        for row in MATERIEL_TRAVAUX_ANNEXES_EXT:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_travaux_annexes_ext[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_travaux_annexes_ext[key],
                key=f"qte_travaux_annexes_ext_{key}",
            )

    with st.expander("DI box fermé", expanded=False):
        if "materiel_di_box_ferme" not in st.session_state:
            st.session_state.materiel_di_box_ferme = {
                row["code"] or row["libelle"]: 0 for row in MATERIEL_DI_BOX_FERME
            }

        for row in MATERIEL_DI_BOX_FERME:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_box_ferme[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_box_ferme[key],
                key=f"qte_di_box_ferme_{key}",
            )

    with st.expander("DI mur extérieur", expanded=False):
        if "materiel_di_mur_exterieur" not in st.session_state:
            st.session_state.materiel_di_mur_exterieur = {
                row["code"] or row["libelle"]: 0 for row in MATERIEL_DI_MUR_EXTERIEUR
            }

        for row in MATERIEL_DI_MUR_EXTERIEUR:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_mur_exterieur[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_mur_exterieur[key],
                key=f"qte_di_mur_exterieur_{key}",
            )

    with st.expander(
        "DI Parking extérieur sans mur, installation au sol (raccordement direct REMBT)",
        expanded=False,
    ):
        if "materiel_di_parking_sol" not in st.session_state:
            st.session_state.materiel_di_parking_sol = {
                row["code"] or row["libelle"]: 0 for row in MATERIEL_DI_PARKING_SOL
            }

        for row in MATERIEL_DI_PARKING_SOL:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_parking_sol[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_parking_sol[key],
                key=f"qte_di_parking_sol_{key}",
            )


def render_image_section(name_bigsection: str, key: str):
    # Initialiser le dictionnaire des sections si besoin
    if "sections_dict" not in st.session_state:
        st.session_state.sections_dict = {}

    # Initialiser la sous-liste de sections pour cette grande section
    if name_bigsection not in st.session_state.sections_dict:
        st.session_state.sections_dict[name_bigsection] = []

    st.write("")
    st.write("")
    st.markdown(f"##### 📍 {name_bigsection}")

    # Formulaire pour ajouter une sous-section
    with st.form(f"form_{name_bigsection}"):
        new_section_name = st.text_input(
            "Nom de la nouvelle section", key=f"input_{name_bigsection}"
        )
        submitted = st.form_submit_button("Ajouter")
        if submitted and new_section_name:
            if new_section_name not in st.session_state.sections_dict[name_bigsection]:
                st.session_state.sections_dict[name_bigsection].append(new_section_name)

    # Affichage des sous-sections et upload photo
    for sub in st.session_state.sections_dict[name_bigsection]:
        with st.expander(sub, expanded=False):
            if sub in st.session_state.sections_dict[name_bigsection]:
                if st.button(
                    f"Supprimer la section {sub}",
                    key=f"delete_sec_{name_bigsection}_{sub}",
                ):
                    st.session_state.sections_dict[name_bigsection].remove(sub)

            uploaded_files = st.file_uploader(
                label="",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"upload_{name_bigsection}_{sub}",
            )
            if key in st.session_state and sub in st.session_state[key]:
                if st.button(
                    f"Supprimer les photos", key=f"delete_{name_bigsection}_{sub}"
                ):
                    st.session_state[key][sub] = []

            # Add to session state (with key = new_section_name)
            if uploaded_files:
                if key not in st.session_state:
                    st.session_state[key] = {}
                st.session_state[key][sub] = uploaded_files

            if key in st.session_state and sub in st.session_state[key]:
                for img in st.session_state[key][sub]:
                    st.image(img, caption=img.name, width=200)


def generation_pdf():
    # st.header("Génération du PDF")
    if True:
        with open("template_interieur_exterieur.html", "r", encoding="utf-8") as f:
            template_html = f.read()

        date_str = st.session_state.date_saisie.strftime("%d/%m/%Y")
        date_construction_str = str(st.session_state.date_construction_immeuble.year)
        date_visite_str = st.session_state.date_visite_technique.strftime("%d/%m/%Y")
        date_ag_str = st.session_state.date_ag.strftime("%d/%m/%Y")
        date_debut_str = st.session_state.date_debut_chantier.strftime("%d/%m/%Y")
        date_fin_str = st.session_state.date_fin_chantier.strftime("%d/%m/%Y")

        # Merge fields from variables
        puissance_IRVE = [
            f"({i + 1}) {str(st.session_state.get(f'nb_places_{i}', 0))} places - {str(st.session_state.get(f'puissance_irve_{i}', 0))} KVA"
            for i in range(int(st.session_state.nombre_parkings))
        ]

        puissance_IRVE_str = " <br> ".join(puissance_IRVE)

        description_technique = [
            f"({i + 1}) {st.session_state.get(f'description_technique_{i}', '')}"
            for i in range(int(st.session_state.nombre_parkings))
        ]

        description_technique_str = " <br> ".join(description_technique)

        # Create Prefinancement table
        prefinancement_enedis = render_prefinancement_table_html(
            "enedis", st.session_state.prefinancement_enedis
        )
        prefinancement_demandeur = render_prefinancement_table_html(
            "demandeur", st.session_state.prefinancement_demandeur
        )

        # Create materiel table
        material_parking_interieur = ""
        material_parking_exterieur = ""

        material_parking_interieur += generate_material_html_table(
            "Raccordement au réseau (hors câble)",
            MATERIEL_RACCORDEMENT_AU_RESEAU,
            "materiel_interieur_raccordement_au_reseau",
        )
        material_parking_interieur += generate_material_html_table(
            "Construction adaptation du pied de colonne",
            MATERIEL_ADAPTATION_PIED_DE_COLONNE,
            "materiel_interieur_adaptation_pied_de_colonne",
        )
        material_parking_interieur += generate_material_html_table(
            "Ouvrages collectifs (hors câble)",
            MATERIEL_CONSTRUCTION_OUVRAGES_COLLECTIFS,
            "materiel_interieur_construction_ouvrages",
        )

        material_parking_interieur += generate_material_html_table(
            "Travée (hors câble)",
            MATERIEL_CONSTRUCTION_TRAVEE,
            "materiel_construction_travee",
        )

        material_parking_interieur += generate_material_html_table(
            "Création des DI", MATERIEL_CREATION_DI, "materiel_creation_di"
        )
        material_parking_interieur += generate_material_html_table(
            "Câbles et accessoires",
            MATERIEL_CABLES_ET_ACCESSOIRES,
            "materiel_cables_et_accessoires",
        )
        material_parking_interieur += generate_material_html_table(
            "Travaux Annexes", MATERIEL_TRAVAUX_ANNEXES, "materiel_travaux_annexes"
        )
        material_parking_exterieur += generate_material_html_table(
            "Extension réseau", EXTENSION_RESEAU, "extension_reseau"
        )
        material_parking_exterieur += generate_material_html_table(
            "Raccordement", RACCORDEMENT, "materiel_raccordement"
        )
        material_parking_exterieur += generate_material_html_table(
            "Dérivation collective",
            DERIVATION_COLLECTIVE,
            "materiel_derivation_collective",
        )
        material_parking_exterieur += generate_material_html_table(
            "Travée (parking extérieur)",
            DERIVATION_COLLECTIVE_EXTERIEUR,
            "materiel_derivation_parking_exterieur",
        )
        material_parking_exterieur += generate_material_html_table(
            "DI coffret exploitation",
            DI_COFFRET_EXPLOITATION,
            "materiel_di_coffret_exploitation",
        )
        material_parking_exterieur += generate_material_html_table(
            "Travaux Annexes",
            MATERIEL_TRAVAUX_ANNEXES_EXT,
            "materiel_travaux_annexes_ext",
        )
        material_parking_exterieur += generate_material_html_table(
            "DI box fermé", MATERIEL_DI_BOX_FERME, "materiel_di_box_ferme"
        )
        material_parking_exterieur += generate_material_html_table(
            "DI mur extérieur", MATERIEL_DI_MUR_EXTERIEUR, "materiel_di_mur_exterieur"
        )
        material_parking_exterieur += generate_material_html_table(
            "DI sol (extérieur sans mur)",
            MATERIEL_DI_PARKING_SOL,
            "materiel_di_parking_sol",
        )

        # Process xlsx file
        excel_file = st.session_state.documents
        if excel_file:
            xlsx_html = process_excel(excel_file)
        else:
            xlsx_html = ""

        fields = {
            # Infos Générales
            "{ADRESSE_SITE}": st.session_state.adresse_site,
            "{NUMERO_AFFAIRE}": st.session_state.num_affaire,
            "{DATE}": date_str,
            "{NOMBRE_PLACES_STATIONNEMENT}": str(
                st.session_state.nombre_places_stationnement
            )
            + " places",
            "{ANNEE_CONSTRUCTION_IMMEUBLE}": date_construction_str,
            "{AVEC_SANS_PREFINANCEMENT}": st.session_state.avec_sans_prefinancement,
            # Contacts
            "{REFERENCE_POLE_ENEDIS}": st.session_state.reference_pole_enedis,
            "{ADRESSE_POLE_ENEDIS}": st.session_state.adresse_pole_enedis,
            "{NOM_CHARGE_PROJET}": st.session_state.nom_charge_projet,
            "{TEL_CHARGE_PROJET}": st.session_state.tel_charge_projet,
            "{EMAIL_CHARGE_PROJET}": st.session_state.email_charge_projet,
            "{NOM_PRESTATAIRE}": st.session_state.nom_prestataire,
            "{TEL_PRESTATAIRE}": st.session_state.tel_prestataire,
            "{EMAIL_PRESTATAIRE}": st.session_state.email_prestataire,
            "{NOM_SYNDIC}": st.session_state.nom_syndic,
            "{ADRESSE_SYNDIC}": st.session_state.adresse_syndic,
            "{NOM_INTERLOCUTEUR_SYNDIC}": st.session_state.nom_interlocuteur_syndic,
            "{TEL_SYNDIC}": st.session_state.tel_syndic,
            "{EMAIL_SYNDIC}": st.session_state.email_syndic,
            # Infos Fonctionnelles
            "{DATE_VISITE_TECHNIQUE}": date_visite_str,
            "{DATE_AG}": date_ag_str,
            "{DATE_DEBUT_CHANTIER}": date_debut_str,
            "{DATE_FIN_CHANTIER}": date_fin_str,
            # Infos Techniques
            "{DESCRIPTION_TECHNIQUE}": description_technique_str,
            "{PUISSANCE_IRVE}": puissance_IRVE_str,
            "{TYPE_CHAUFFAGE}": st.session_state.type_chauffage,
            "{EXCEL_FILE}": xlsx_html,
            # Accès
            "{MOYEN_DACCES_COPRO}": st.session_state.moyen_acces_copro,
            "{MOYEN_DACCES_PARKING}": st.session_state.moyen_acces_parking,
            "{COFFRET}": st.session_state.coffret,
            # Prefinancement
            "{PREFINANCEMENT_ENEDIS}": prefinancement_enedis,
            "{PREFINANCEMENT_DEMANDEUR}": prefinancement_demandeur,
            # Matériel
            "{MATERIEL_PARKING_INTERIEUR}": material_parking_interieur,
            "{MATERIEL_PARKING_EXTERIEUR}": material_parking_exterieur,
        }

        insert_image_to_fields(
            st.session_state.plan_reseau, "{IMG_PLAN_RESEAU}", "Plan Réseau", fields
        )
        insert_image_to_fields(
            st.session_state.facade_acces_copro,
            "{IMG_FACADE_ACCES_COPRO}",
            "Façade et accès copropriété",
            fields,
        )
        insert_image_to_fields(
            st.session_state.facade_acces_parking,
            "{IMG_FACADE_ACCES_PARKING}",
            "Façade et accès parking",
            fields,
        )
        insert_images_to_fields(
            st.session_state.etats_avant_travaux,
            "{IMAGE_AVANT_TRAVAUX}",
            "État avant travaux",
            fields,
        )

        insert_image_to_fields(
            st.session_state.plan_reseau2,
            "{PLAN_RESEAU_2}",
            "Plan Réseau 2",
            fields,
        )

        insert_images_to_fields_titles(
            st.session_state.img_parametres_generaux,
            "{IMG_PARAMETRES_GENERAUX}",
            "Paramètres généraux",
            fields,
        )

        insert_images_to_fields_titles(
            st.session_state.img_arrivee_reseau,
            "{IMG_ARRIVEE_RESEAU}",
            "Arrivée réseau et pied de colonne",
            fields,
        )
        insert_images_to_fields_titles(
            st.session_state.img_distribution_parking,
            "{IMG_DISTRIBUTION_PARKING}",
            "Distribution du parking",
            fields,
        )
        insert_images_to_fields_titles(
            st.session_state.img_plans_apres_travaux,
            "{IMG_PLANS_APRES_TRAVAUX}",
            "Plans après travaux",
            fields,
        )
        insert_images_to_fields_titles(
            st.session_state.img_synoptique,
            "{IMG_SYNOPTIQUE}",
            "Synoptique",
            fields,
        )
        insert_images_to_fields_titles(
            st.session_state.img_calcul_colonne_electrique,
            "{IMG_CALCUL_COLONNE_ELECTRIQUE}",
            "Calcul de colonne électrique",
            fields,
        )

        for key, value in fields.items():
            template_html = template_html.replace(key, value)

        pdf = html_to_pdf(template_html)
        if pdf:
            return pdf
        return None


def main():
    init_state()
    section = st.radio(
        "Choisissez une section :",
        (
            "Informations Générales",
            "Informations Fonctionnelles",
            "Informations Techniques",
            "Contacts",
            "Accès",
            "Préfinancement",
            "Images à fournir",
            "Matériel",
        ),
    )

    if section == "Informations Générales":
        section_infos_generales()
    elif section == "Informations Fonctionnelles":
        section_infos_fonctionnelles()
    elif section == "Informations Techniques":
        section_technique()
    elif section == "Contacts":
        section_contact()
    elif section == "Accès":
        section_acces()
    elif section == "Préfinancement":
        section_prefinancement()
    elif section == "Images à fournir":
        section_images()
    elif section == "Matériel":
        materiel()

    st.sidebar.markdown("### Charger un document")

    saved_projects = list_saved_states()

    if saved_projects:
        selected_project = st.sidebar.selectbox("Projets disponibles :", saved_projects)

        if st.sidebar.button("Charger"):
            # load_state(selected_project)
            load_state_from_supabase(selected_project)

        if st.sidebar.button("Supprimer"):
            # delete_state(selected_project)
            delete_state_from_supabase(selected_project)

    else:
        st.sidebar.write("Aucun état sauvegardé pour le moment.")

    st.sidebar.markdown("### Sauvegarder un document")
    project_name = st.sidebar.text_input(
        "Nom du projet", value="", key="nom_projet_sidebar"
    )

    if st.sidebar.button("Sauvegarder"):
        # success = save_state(project_name)
        success = save_state_to_supabase(project_name)
        if success:
            st.sidebar.success(f"Projet **{project_name}** sauvegardé avec succès ✅")

    # 📄 Génération du PDF
    st.sidebar.markdown("### Exporter en PDF")
    if st.sidebar.button("Exporter"):
        pdf = generation_pdf()  # cette fonction doit RETURN le pdf

        if pdf:
            st.session_state.generated_pdf = pdf
            st.sidebar.success("Le PDF a été généré avec succès 🎉")
        else:
            st.sidebar.error("⚠️ Erreur lors de la génération du PDF.")

    # Afficher le bouton de téléchargement uniquement si le PDF a été généré
    if "generated_pdf" in st.session_state:
        st.sidebar.download_button(
            label="📥 Télécharger le PDF",
            data=st.session_state.generated_pdf,
            file_name="etude_enedis.pdf",
            mime="application/pdf",
        )

    # réinitialiser le state
    st.sidebar.markdown("### Réinitialiser le formulaire")
    if st.sidebar.button("Réinitialiser"):
        for key in st.session_state.keys():
            if key not in ["generated_pdf", "nom_projet_sidebar"]:
                del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()
