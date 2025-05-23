import streamlit as st
from st_supabase_connection import SupabaseConnection
import pickle
import os
import json
import base64
import zlib

import datetime

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


def list_saved_states():
    conn = st.connection("supabase", type=SupabaseConnection)
    result = conn.client.table("projects_state2").select("project_name").execute()
    if result.data:
        project_names = []

        for row in result.data:
            if row["project_name"] not in project_names:
                project_names.append(row["project_name"])

        return project_names
    return []


def save_state_to_supabase(project_name):
    conn = st.connection("supabase", type=SupabaseConnection)

    update_dynamic_lists_before_saving()

    import base64

    def encode_files(files):
        encoded_files = []
        for file in files:
            # ⚡ IMPORTANT: remettre le curseur au début
            file.seek(0)
            # Encode each file to base64
            encoded_files.append(base64.b64encode(file.read()).decode("utf-8"))

        return encoded_files

    def encode_files_dict(etats_dict):
        result = {}
        if not etats_dict:
            return {}
        for niveau, files in etats_dict.items():
            encoded_files = []
            for file in files:
                # ⚡ IMPORTANT: remettre le curseur au début
                file.seek(0)
                encoded_files.append(base64.b64encode(file.read()).decode("utf-8"))
            result[niveau] = encoded_files
        return result

    data = (
        {
            "project_name": project_name,
            # Infos Générales
            "adresse_site": st.session_state.adresse_site,
            "num_affaire": st.session_state.num_affaire,
            "date_saisie": str(st.session_state.date_saisie),
            "date_construction_immeuble": str(
                st.session_state.date_construction_immeuble
            ),
            "avec_sans_prefinancement": st.session_state.avec_sans_prefinancement,
            "parking_interieur": st.session_state.parking_interieur,
            "parking_exterieur": st.session_state.parking_exterieur,
            "nombre_parkings": st.session_state.nombre_parkings,
            "nombre_de_niveaux": st.session_state.nombre_de_niveaux,
            "nombre_places_stationnement": st.session_state.nombre_places_stationnement,
            # Infos Fonctionnelles
            "date_visite_technique": str(st.session_state.date_visite_technique),
            "date_ag": str(st.session_state.date_ag),
            "date_debut_chantier": str(st.session_state.date_debut_chantier),
            "date_fin_chantier": str(st.session_state.date_fin_chantier),
            # Contacts
            "reference_pole_enedis": st.session_state.reference_pole_enedis,
            "adresse_pole_enedis": st.session_state.adresse_pole_enedis,
            "nom_charge_projet": st.session_state.nom_charge_projet,
            "tel_charge_projet": st.session_state.tel_charge_projet,
            "email_charge_projet": st.session_state.email_charge_projet,
            "nom_prestataire": st.session_state.nom_prestataire,
            "tel_prestataire": st.session_state.tel_prestataire,
            "email_prestataire": st.session_state.email_prestataire,
            "nom_syndic": st.session_state.nom_syndic,
            "adresse_syndic": st.session_state.adresse_syndic,
            "nom_interlocuteur_syndic": st.session_state.nom_interlocuteur_syndic,
            "tel_syndic": st.session_state.tel_syndic,
            "email_syndic": st.session_state.email_syndic,
            # Champs dynamiques regroupés explicitement !
            "description_technique_0": st.session_state.get(
                "description_technique_0", ""
            ),
            "description_technique_1": st.session_state.get(
                "description_technique_1", ""
            ),
            "description_technique_2": st.session_state.get(
                "description_technique_2", ""
            ),
            "description_technique_3": st.session_state.get(
                "description_technique_3", ""
            ),
            "description_technique_4": st.session_state.get(
                "description_technique_4", ""
            ),
            "description_technique_5": st.session_state.get(
                "description_technique_5", ""
            ),
            "nb_places_0": st.session_state.get("nb_places_0", 0),
            "nb_places_1": st.session_state.get("nb_places_1", 0),
            "nb_places_2": st.session_state.get("nb_places_2", 0),
            "nb_places_3": st.session_state.get("nb_places_3", 0),
            "nb_places_4": st.session_state.get("nb_places_4", 0),
            "nb_places_5": st.session_state.get("nb_places_5", 0),
            "puissance_irve_0": st.session_state.get("puissance_irve_0", 0),
            "puissance_irve_1": st.session_state.get("puissance_irve_1", 0),
            "puissance_irve_2": st.session_state.get("puissance_irve_2", 0),
            "puissance_irve_3": st.session_state.get("puissance_irve_3", 0),
            "puissance_irve_4": st.session_state.get("puissance_irve_4", 0),
            "puissance_irve_5": st.session_state.get("puissance_irve_5", 0),
            # Infos Techniques
            "type_chauffage": st.session_state.type_chauffage,
            "coffret": st.session_state.coffret,
            "plan_reseau": encode_files(st.session_state.plan_reseau),
            "documents": base64.b64encode(st.session_state.documents.read()).decode(
                "utf-8"
            )
            if st.session_state.documents
            else None,
            # Accès
            "moyen_acces_copro": st.session_state.moyen_acces_copro,
            "moyen_acces_parking": st.session_state.moyen_acces_parking,
            "facade_acces_copro": encode_files(st.session_state.facade_acces_copro),
            "facade_acces_parking": encode_files(st.session_state.facade_acces_parking),
            # Préfinancement
            "prefinancement_enedis": st.session_state.prefinancement_enedis,
            "prefinancement_demandeur": st.session_state.prefinancement_demandeur,
            # Images
            "etats_avant_travaux": encode_files_dict(
                st.session_state.etats_avant_travaux
            ),
            "plan_reseau2": encode_files(st.session_state.plan_reseau2),
            "img_parametres_generaux": encode_files_dict(
                st.session_state.sections_dict["Paramètres généraux"]
            ),
            "img_arrivee_reseau": encode_files_dict(
                st.session_state.sections_dict["Arrivée réseau et pied de colonne"]
            ),
            "img_distribution_parking": encode_files_dict(
                st.session_state.sections_dict["Distribution du parking"]
            ),
            "img_plans_apres_travaux": encode_files_dict(
                st.session_state.sections_dict["Plans après travaux"]
            ),
            "img_synoptique": encode_files_dict(
                st.session_state.sections_dict["Synoptique"]
            ),
            "img_calcul_colonne_electrique": encode_files_dict(
                st.session_state.sections_dict["Calcul de colonne électrique"]
            ),
            # Matériel
            "materiel_interieur_raccordement_au_reseau": json.dumps(
                st.session_state.materiel_interieur_raccordement_au_reseau
            ),
            "materiel_interieur_adaptation_pied_de_colonne": json.dumps(
                st.session_state.materiel_interieur_adaptation_pied_de_colonne
            ),
            "materiel_interieur_construction_ouvrages": json.dumps(
                st.session_state.materiel_interieur_construction_ouvrages
            ),
            "materiel_construction_travee": json.dumps(
                st.session_state.materiel_construction_travee
            ),
            "materiel_creation_di": json.dumps(st.session_state.materiel_creation_di),
            "materiel_cables_et_accessoires": json.dumps(
                st.session_state.materiel_cables_et_accessoires
            ),
            "materiel_travaux_annexes": json.dumps(
                st.session_state.materiel_travaux_annexes
            ),
            "extension_reseau": json.dumps(st.session_state.extension_reseau),
            "materiel_raccordement": json.dumps(st.session_state.materiel_raccordement),
            "materiel_derivation_collective": json.dumps(
                st.session_state.materiel_derivation_collective
            ),
            "materiel_derivation_parking_exterieur": json.dumps(
                st.session_state.materiel_derivation_parking_exterieur
            ),
            "materiel_di_coffret_exploitation": json.dumps(
                st.session_state.materiel_di_coffret_exploitation
            ),
            "materiel_travaux_annexes_ext": json.dumps(
                st.session_state.materiel_travaux_annexes_ext
            ),
            "materiel_di_box_ferme": json.dumps(st.session_state.materiel_di_box_ferme),
            "materiel_di_mur_exterieur": json.dumps(
                st.session_state.materiel_di_mur_exterieur
            ),
            "materiel_di_parking_sol": json.dumps(
                st.session_state.materiel_di_parking_sol
            ),
        },
    )

    conn.client.table("projects_state2").upsert(
        data, on_conflict="project_name"
    ).execute()

    st.toast(f"✅ Projet **{project_name}** sauvegardé avec succès.")
    st.rerun()


def load_state_from_supabase(project_name):
    conn = st.connection("supabase", type=SupabaseConnection)

    try:
        result = (
            conn.client.table("projects_state2")
            .select("*")
            .eq("project_name", project_name)
            .execute()
        )

        if not result.data:
            st.error("Projet non trouvé !")
            return False

        loaded_state = result.data[0]

        import base64
        from io import BytesIO

        def decode_files(encoded_files):
            if not encoded_files:
                return []
            result = []
            for img in encoded_files:
                file = BytesIO(base64.b64decode(img))
                file.seek(0)  # 🔥 remet le curseur au début
                result.append(file)
            return result

        def decode_files_dict(encoded_dict):
            if not encoded_dict:
                return {}
            decoded = {}
            for key, encoded_list in encoded_dict.items():
                decoded_list = []
                for file_encoded in encoded_list:
                    file = BytesIO(base64.b64decode(file_encoded))
                    file.seek(0)  # 🔥 remet le curseur au début
                    decoded_list.append(file)
                decoded[key] = decoded_list
            return decoded

        loaded_state["plan_reseau"] = decode_files(loaded_state.get("plan_reseau"))
        loaded_state["facade_acces_copro"] = decode_files(
            loaded_state.get("facade_acces_copro")
        )
        loaded_state["facade_acces_parking"] = decode_files(
            loaded_state.get("facade_acces_parking")
        )

        # NEW
        loaded_state["etats_avant_travaux"] = decode_files_dict(
            loaded_state.get("etats_avant_travaux")
        )
        loaded_state["plan_reseau2"] = decode_files(loaded_state.get("plan_reseau2"))

        loaded_state["sections_dict"] = {
            "Paramètres généraux": decode_files_dict(
                loaded_state.get("img_parametres_generaux", {})
            ),
            "Arrivée réseau et pied de colonne": decode_files_dict(
                loaded_state.get("img_arrivee_reseau", {})
            ),
            "Distribution du parking": decode_files_dict(
                loaded_state.get("img_distribution_parking", {})
            ),
            "Plans après travaux": decode_files_dict(
                loaded_state.get("img_plans_apres_travaux", {})
            ),
            "Synoptique": decode_files_dict(loaded_state.get("img_synoptique", {})),
            "Calcul de colonne électrique": decode_files_dict(
                loaded_state.get("img_calcul_colonne_electrique", {})
            ),
        }

        # Documents Excel
        if loaded_state.get("documents"):
            loaded_state["documents"] = BytesIO(
                base64.b64decode(loaded_state["documents"])
            )

        # Après avoir décodé ton loaded_state, pour corriger toutes les dates :
        for date_field in [
            "date_saisie",
            "date_construction_immeuble",
            "date_visite_technique",
            "date_ag",
            "date_debut_chantier",
            "date_fin_chantier",
        ]:
            if date_field in loaded_state and isinstance(loaded_state[date_field], str):
                try:
                    loaded_state[date_field] = datetime.datetime.strptime(
                        loaded_state[date_field], "%Y-%m-%d"
                    ).date()
                except Exception as e:
                    st.warning(f"Erreur en convertissant {date_field}: {e}")

        # Restaurer les valeurs simples
        for key, value in loaded_state.items():
            if key not in [
                "id",
                "created_at",
                "updated_at",
                "project_name",
                "nb_places",
                "puissance_irve",
                "description_technique",
            ]:
                st.session_state[key] = value

        # Restaurer explicitement les champs dynamiques en variables individuelles
        for i, val in enumerate(loaded_state.get("description_technique", [])):
            st.session_state[f"description_technique_{i}"] = val

        for i, val in enumerate(loaded_state.get("nb_places", [])):
            st.session_state[f"nb_places_{i}"] = val

        for i, val in enumerate(loaded_state.get("puissance_irve", [])):
            st.session_state[f"puissance_irve_{i}"] = val

        material_fields = [
            "materiel_interieur_raccordement_au_reseau",
            "materiel_interieur_adaptation_pied_de_colonne",
            "materiel_interieur_construction_ouvrages",
            "materiel_construction_travee",
            "materiel_creation_di",
            "materiel_cables_et_accessoires",
            "materiel_travaux_annexes",
            "extension_reseau",
            "materiel_raccordement",
            "materiel_derivation_collective",
            "materiel_derivation_parking_exterieur",
            "materiel_di_coffret_exploitation",
            "materiel_travaux_annexes_ext",
            "materiel_di_box_ferme",
            "materiel_di_mur_exterieur",
            "materiel_di_parking_sol",
        ]

        for field in material_fields:
            if loaded_state.get(field):
                st.session_state[field] = json.loads(loaded_state[field])

        st.toast(f"✅ Projet **{project_name}** chargé avec succès.")
        st.rerun()

    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return False


def delete_state_from_supabase(project_name):
    conn = st.connection("supabase", type=SupabaseConnection)
    try:
        result = (
            conn.client.table("projects_state2")
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
        "nb_places_0": 0,
        "nb_places_1": 0,
        "nb_places_2": 0,
        "nb_places_3": 0,
        "nb_places_4": 0,
        "nb_places_5": 0,
        "puissance_irve_0": 0,
        "puissance_irve_1": 0,
        "puissance_irve_2": 0,
        "puissance_irve_3": 0,
        "puissance_irve_4": 0,
        "puissance_irve_5": 0,
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
        "sections_dict": {
            "Paramètres généraux": {},
            "Arrivée réseau et pied de colonne": {},
            "Distribution du parking": {},
            "Plans après travaux": {},
            "Synoptique": {},
            "Calcul de colonne électrique": {},
        },
        # Matériel
        "materiel_interieur_raccordement_au_reseau": {},
        "materiel_adaptation_pied_de_colonne": {},
        "materiel_construction_ouvrages_collectifs": {},
        "materiel_construction_travee": {},
        "materiel_creation_di": {},
        "materiel_cables_et_accessoires": {},
        "materiel_travaux_annexes": {},
        "materiel_travaux_annexes_ext": {},
        "materiel_raccordement": {},
        "materiel_derivation_collective": {},
        "materiel_derivation_collective_exterieur": {},
        "materiel_di_coffret_exploitation": {},
        "materiel_di_mur_exterieur": {},
        "materiel_di_parking_sol": {},
        "materiel_extension_reseau": {},
        "materiel_autres": {},
        "materiel_autres_ext": {},
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
        var_name = f"description_technique_{i}"

        x = st.text_input(
            f"Description de la solution technique - Parking {i + 1}",
        )
        if x != "":
            st.session_state[var_name] = x

        if st.session_state[var_name] != "":
            st.write(f"Valeur actuelle : **{st.session_state[var_name]}**")

    st.write("")
    st.markdown("#### 🚘 Nombre de places par parking")

    for i in range(int(st.session_state.nombre_parkings)):
        var_name_places = f"nb_places_{i}"

        x = st.number_input(
            f"Nombre de places - Parking {i + 1}",
            min_value=0,
            step=1,
        )

        if x != 0:
            st.session_state[var_name_places] = x

        if st.session_state[var_name_places] != 0:
            st.write(f"Valeur actuelle : **{st.session_state[var_name_places]}**")

    st.write("")
    st.markdown("#### ⚡️ Puissance IRVE")

    for i in range(int(st.session_state.nombre_parkings)):
        var_name_puissance = f"puissance_irve_{i}"

        x = st.number_input(
            f"Puissance IRVE - Parking {i + 1} (KVA)",
            min_value=0,
            step=1,
        )

        if x != 0:
            st.session_state[var_name_puissance] = x

        if st.session_state[var_name_puissance] != 0:
            st.write(f"Valeur actuelle : **{st.session_state[var_name_puissance]}**")

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
            img.seek(0)
            if img.read():  # ✅ si le fichier n'est pas vide
                img.seek(0)  # 🔥 remets le curseur au début pour afficher
                st.image(img, width=200)
            else:
                st.warning("⚠️ Image vide détectée, elle sera ignorée.")

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
            "Fichier Excel chargé ✅",
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
            img.seek(0)
            if img.read():  # ✅ si le fichier n'est pas vide
                img.seek(0)  # 🔥 remets le curseur au début pour afficher
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
            img.seek(0)
            if img.read():  # ✅ si le fichier n'est pas vide
                img.seek(0)  # 🔥 remets le curseur au début pour afficher
                st.image(img, width=200)
            st.write("")
            st.write("")


def section_images():
    st.header("Images à fournir")

    st.markdown("#### Etat avant Travaux")

    # 1. Arrivée réseau
    uploaded_file_arrivee_reseau = st.file_uploader(
        "Arrivée réseau",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="arrivee_reseau_key",
    )

    if "etats_avant_travaux" not in st.session_state:
        st.session_state.etats_avant_travaux = {}

    if (
        "etats_avant_travaux" not in st.session_state
        or st.session_state.etats_avant_travaux is None
    ):
        st.session_state.etats_avant_travaux = {}

    if uploaded_file_arrivee_reseau:
        st.session_state.etats_avant_travaux["Arrivée réseau"] = (
            uploaded_file_arrivee_reseau
        )

    if len(st.session_state.etats_avant_travaux.get("Arrivée réseau", [])) > 0:
        if st.button(f"Supprimer les photos", key=f"delete_arrivee_reseau"):
            st.session_state.etats_avant_travaux["Arrivée réseau"] = []

    if len(st.session_state.etats_avant_travaux.get("Arrivée réseau", [])) > 0:
        for img in st.session_state.etats_avant_travaux["Arrivée réseau"]:
            img.seek(0)
            if img.read():  # ✅ si le fichier n'est pas vide
                img.seek(0)  # 🔥 remets le curseur au début pour afficher
                st.image(img, width=200)
            st.write("")
            st.write("")

    # 2. Niveau 0
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
                img.seek(0)
                if img.read():  # ✅ si le fichier n'est pas vide
                    img.seek(0)  # 🔥 remets le curseur au début pour afficher
                    st.image(img, width=200)
                    st.write("")
                    st.write("")

    st.write("")
    st.write("")
    st.markdown("#### Etat après Travaux")

    # 3. Plan réseau
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
            img.seek(0)
            if img.read():  # ✅ si le fichier n'est pas vide
                img.seek(0)  # 🔥 remets le curseur au début pour afficher
                st.image(img, width=200)
                st.write("")
                st.write("")

    render_image_section("Paramètres généraux")
    render_image_section("Arrivée réseau et pied de colonne")
    render_image_section("Distribution du parking")
    render_image_section("Plans après travaux")
    render_image_section("Synoptique")
    render_image_section("Calcul de colonne électrique")


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
        checked = st.checkbox(
            texte,
            key=f"pref_check_{i}",
            value=texte in st.session_state.prefinancement_enedis,  # 👈 rajoute ça
        )

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
            st.session_state.materiel_interieur_raccordement_au_reseau = {}
        for row in MATERIEL_RACCORDEMENT_AU_RESEAU:
            st.session_state.materiel_interieur_raccordement_au_reseau[row["code"]] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_interieur_raccordement_au_reseau.get(
                        row["code"], 0
                    ),
                    key=f"qte_{row['code']}",
                )
            )

    with st.expander("Construction adaptation du pied de colonne", expanded=False):
        if "materiel_interieur_adaptation_pied_de_colonne" not in st.session_state:
            st.session_state.materiel_interieur_adaptation_pied_de_colonne = {}
        for row in MATERIEL_ADAPTATION_PIED_DE_COLONNE:
            st.session_state.materiel_interieur_adaptation_pied_de_colonne[
                row["code"]
            ] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_interieur_adaptation_pied_de_colonne.get(
                    row["code"], 0
                ),
                key=f"qte_{row['code']}",
            )

    with st.expander(
        "Construction des ouvrages collectifs (hors câble)", expanded=False
    ):
        if "materiel_interieur_construction_ouvrages" not in st.session_state:
            st.session_state.materiel_interieur_construction_ouvrages = {}
        for row in MATERIEL_CONSTRUCTION_OUVRAGES_COLLECTIFS:
            st.session_state.materiel_interieur_construction_ouvrages[row["code"]] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_interieur_construction_ouvrages.get(
                        row["code"], 0
                    ),
                    key=f"qte_{row['code']}",
                )
            )

    with st.expander("Construction d’une travée (hors câble)", expanded=False):
        if "materiel_construction_travee" not in st.session_state:
            st.session_state.materiel_construction_travee = {}
        for row in MATERIEL_CONSTRUCTION_TRAVEE:
            st.session_state.materiel_construction_travee[row["code"]] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_construction_travee.get(
                        row["code"], 0
                    ),
                    key=f"qte_{row['code']}",
                )
            )

    with st.expander("Création des DI", expanded=False):
        if "materiel_creation_di" not in st.session_state:
            st.session_state.materiel_creation_di = {}
        for row in MATERIEL_CREATION_DI:
            st.session_state.materiel_creation_di[row["code"]] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_creation_di.get(row["code"], 0),
                key=f"qte_creation_di_{row['code']}",
            )

    with st.expander("Câbles et accessoires installés", expanded=False):
        if "materiel_cables_et_accessoires" not in st.session_state:
            st.session_state.materiel_cables_et_accessoires = {}
        for row in MATERIEL_CABLES_ET_ACCESSOIRES:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_cables_et_accessoires[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_cables_et_accessoires.get(key, 0),
                key=f"qte_cables_{key}",
            )

    with st.expander("Travaux Annexes", expanded=False):
        if "materiel_travaux_annexes" not in st.session_state:
            st.session_state.materiel_travaux_annexes = {}
        for row in MATERIEL_TRAVAUX_ANNEXES:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_travaux_annexes[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_travaux_annexes.get(key, 0),
                key=f"qte_travaux_annexes_{key}",
            )

    st.subheader("Matériel pour Parking Extérieur")

    with st.expander(
        "Extension réseau (départ monobloc, etc.), liaison réseau, etc.", expanded=False
    ):
        if "extension_reseau" not in st.session_state:
            st.session_state.extension_reseau = {}
        for row in EXTENSION_RESEAU:
            key = row["code"] or row["libelle"]
            st.session_state.extension_reseau[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.extension_reseau.get(key, 0),
                key=f"qte_extension_reseau_{key}",
            )

    with st.expander("Raccordement", expanded=False):
        if "materiel_raccordement" not in st.session_state:
            st.session_state.materiel_raccordement = {}
        for row in RACCORDEMENT:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_raccordement[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_raccordement.get(key, 0),
                key=f"qte_raccordement_{key}",
            )

    with st.expander("Câble dérivation collective (pleine terre)", expanded=False):
        if "materiel_derivation_collective" not in st.session_state:
            st.session_state.materiel_derivation_collective = {}
        for row in DERIVATION_COLLECTIVE:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_derivation_collective[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_derivation_collective.get(key, 0),
                key=f"qte_derivation_collective_{key}",
            )

    with st.expander("Dérivation collective en parking extérieur", expanded=False):
        if "materiel_derivation_parking_exterieur" not in st.session_state:
            st.session_state.materiel_derivation_parking_exterieur = {}
        for row in DERIVATION_COLLECTIVE_EXTERIEUR:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_derivation_parking_exterieur[key] = (
                st.number_input(
                    label=f"{row['libelle']} ({row['unite']})",
                    min_value=0,
                    step=1,
                    value=st.session_state.materiel_derivation_parking_exterieur.get(
                        key, 0
                    ),
                    key=f"qte_derivation_parking_exterieur_{key}",
                )
            )

    with st.expander("DI coffret exploitation", expanded=False):
        if "materiel_di_coffret_exploitation" not in st.session_state:
            st.session_state.materiel_di_coffret_exploitation = {}
        for row in DI_COFFRET_EXPLOITATION:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_coffret_exploitation[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_coffret_exploitation.get(key, 0),
                key=f"qte_di_coffret_exploitation_{key}",
            )

    with st.expander("Travaux Annexes (Parking extérieur)", expanded=False):
        if "materiel_travaux_annexes_ext" not in st.session_state:
            st.session_state.materiel_travaux_annexes_ext = {}
        for row in MATERIEL_TRAVAUX_ANNEXES_EXT:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_travaux_annexes_ext[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_travaux_annexes_ext.get(key, 0),
                key=f"qte_travaux_annexes_ext_{key}",
            )

    with st.expander("DI box fermé", expanded=False):
        if "materiel_di_box_ferme" not in st.session_state:
            st.session_state.materiel_di_box_ferme = {}
        for row in MATERIEL_DI_BOX_FERME:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_box_ferme[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_box_ferme.get(key, 0),
                key=f"qte_di_box_ferme_{key}",
            )

    with st.expander("DI mur extérieur", expanded=False):
        if "materiel_di_mur_exterieur" not in st.session_state:
            st.session_state.materiel_di_mur_exterieur = {}
        for row in MATERIEL_DI_MUR_EXTERIEUR:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_mur_exterieur[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_mur_exterieur.get(key, 0),
                key=f"qte_di_mur_exterieur_{key}",
            )

    with st.expander("DI sol (extérieur sans mur)", expanded=False):
        if "materiel_di_parking_sol" not in st.session_state:
            st.session_state.materiel_di_parking_sol = {}
        for row in MATERIEL_DI_PARKING_SOL:
            key = row["code"] or row["libelle"]
            st.session_state.materiel_di_parking_sol[key] = st.number_input(
                label=f"{row['libelle']} ({row['unite']})",
                min_value=0,
                step=1,
                value=st.session_state.materiel_di_parking_sol.get(key, 0),
                key=f"qte_di_parking_sol_{key}",
            )


def render_image_section(name_bigsection: str):
    # Initialize
    """if "sections_dict" not in st.session_state:
        st.session_state.sections_dict = {}
    if name_bigsection not in st.session_state.sections_dict:
        st.session_state.sections_dict[name_bigsection] = {}
    """

    st.write("")
    st.write("")
    st.markdown(f"##### 📍 {name_bigsection}")

    # Add a sub-section
    with st.form(f"form_{name_bigsection}"):
        new_section_name = st.text_input(
            "Nom de la nouvelle sous-section", key=f"input_{name_bigsection}"
        )
        submitted = st.form_submit_button("Ajouter")
        if submitted and new_section_name:
            if new_section_name not in st.session_state.sections_dict[name_bigsection]:
                st.session_state.sections_dict[name_bigsection][new_section_name] = []

    # Loop through sub-sections
    for sub in st.session_state.sections_dict[name_bigsection].keys():
        with st.expander(sub, expanded=False):
            if st.button(
                f"Supprimer la sous-section {sub}",
                key=f"delete_sec_{name_bigsection}_{sub}",
            ):
                del st.session_state.sections_dict[name_bigsection][sub]
                st.experimental_rerun()

            uploaded_files = st.file_uploader(
                label=f"Importer des images pour {sub}",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"upload_{name_bigsection}_{sub}",
            )

            if uploaded_files:
                st.session_state.sections_dict[name_bigsection][sub] = uploaded_files

            if (
                sub in st.session_state.sections_dict[name_bigsection]
                and st.session_state.sections_dict[name_bigsection][sub]
            ):
                if st.button(
                    f"Supprimer les images pour {sub}",
                    key=f"delete_imgs_{name_bigsection}_{sub}",
                ):
                    st.session_state.sections_dict[name_bigsection][sub] = []
                    st.experimental_rerun()

                for img in st.session_state.sections_dict[name_bigsection][sub]:
                    img.seek(0)
                    if img.read():  # ✅ si le fichier n'est pas vide
                        img.seek(0)  # 🔥 remets le curseur au début pour afficher
                        st.image(img, width=200)


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
            # "{MATERIEL_PARKING_INTERIEUR}": "",
            # "{MATERIEL_PARKING_EXTERIEUR}": "",
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

    if "load_done" not in st.session_state:
        st.session_state.load_done = False

    if not st.session_state.load_done:
        saved_projects = list_saved_states()

        selected_project = st.sidebar.selectbox("Projets disponibles :", saved_projects)

        if st.sidebar.button("Charger") and selected_project:
            load_success = load_state_from_supabase(selected_project)
            if load_success:
                st.session_state.load_done = True
                st.rerun()

        st.stop()  # ⛔️ STOP la page ici tant que pas chargé

    # Ici seulement on peut afficher le reste de l'app (widgets, etc)
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
