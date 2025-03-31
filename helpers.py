import base64
import os
import tempfile
from io import BytesIO
from xhtml2pdf import pisa
import datetime
import streamlit as st
import pandas as pd


MATERIEL_RACCORDEMENT_AU_RESEAU = [
    {"code": "S6902019", "libelle": "Coffret ECP 3D", "unite": "U"},
    {"code": "S6902033", "libelle": "Borne ECP 3D", "unite": "U"},
    {"code": "S6902054", "libelle": "Coffret ECP 2D", "unite": "U"},
    {"code": "S6902053", "libelle": "B ECP 2D", "unite": "U"},
    {"code": "S6902035", "libelle": "Kit passage de 2D en 3D", "unite": "U"},
    {"code": "S6798304", "libelle": "Extrémité rétractable BT E4R 240", "unite": "U"},
    {"code": "S6798303", "libelle": "Extrémité rétractable BT E4R50-150", "unite": "U"},
    {"code": "S6982200", "libelle": "Départ monobloc TIPI", "unite": "U"},
    {"code": "S6982777", "libelle": "Départ monobloc TUR", "unite": "U"},
    {"code": "S6943009", "libelle": "Fusible 200A-115MM", "unite": "U"},
    {"code": "S6943013", "libelle": "Fusible 250A-115MM", "unite": "U"},
    {"code": "S6943016", "libelle": "Fusible 400A-115MM", "unite": "U"},
    {"code": "S6943424", "libelle": "Fusible 400A-160MM", "unite": "U"},
    {"code": "S6943413", "libelle": "Fusible 200A-160MM", "unite": "U"},
]

MATERIEL_ADAPTATION_PIED_DE_COLONNE = [
    {
        "code": "S6902433",
        "libelle": "Kit 4 liaisons simples 200 A DIST. 400 A MICHAUD",
        "unite": "U",
    },
    {
        "code": "S6902443",
        "libelle": "Kit 4 liaisons simples 200 A DIST. 400 A DEPAGNE",
        "unite": "U",
    },
    {
        "code": "S6902473",
        "libelle": "Kit 4 liaisons simples 200 A DIST. 400 A MAEC",
        "unite": "U",
    },
    {
        "code": "S6902483",
        "libelle": "Kit 4 liaisons simples 200 A DIST. 400 A SEIFEL",
        "unite": "U",
    },
    {
        "code": "S6902434",
        "libelle": "Kit 4 liaisons doubles 200 A DIST. 400 A MICHAUD",
        "unite": "U",
    },
    {
        "code": "S6902444",
        "libelle": "Kit 4 liaisons doubles 200 A DIST. 400 A DEPAGNE",
        "unite": "U",
    },
    {
        "code": "S6902474",
        "libelle": "Kit 4 liaisons doubles 200 A DIST. 400 A MAEC",
        "unite": "U",
    },
    {
        "code": "S6902484",
        "libelle": "Kit 4 liaisons doubles 200 A DIST. 400 A SEIFEL",
        "unite": "U",
    },
    {"code": "S6902429", "libelle": "Distributeur d'arrivée 200A", "unite": "U"},
    {"code": "S6902428", "libelle": "Distributeur de niveau 200A", "unite": "U"},
    {
        "code": "S6902432",
        "libelle": "Distributeur d'arrivée 400A MICHAUD",
        "unite": "U",
    },
    {"code": "S6902472", "libelle": "Distributeur d'arrivée 400A MAEC", "unite": "U"},
    {"code": "S6902482", "libelle": "Distributeur d'arrivée 400A SEIFEL", "unite": "U"},
    {
        "code": "S6902442",
        "libelle": "Distributeur d'arrivée 400A DEPAGNE",
        "unite": "U",
    },
    {
        "code": "S6902431",
        "libelle": "Distributeur de niveau 400A MICHAUD",
        "unite": "U",
    },
    {"code": "S6902471", "libelle": "Distributeur de niveau 400A MAEC", "unite": "U"},
    {"code": "S6902481", "libelle": "Distributeur de niveau 400A SEIFEL", "unite": "U"},
    {"code": "S6902441", "libelle": "Distributeur 400A NIVEAU DEPAGNE", "unite": "U"},
]
MATERIEL_CONSTRUCTION_OUVRAGES_COLLECTIFS = [
    {"code": "S6902650", "libelle": "SPCM protection maximales 200A", "unite": "U"},
    {
        "code": "S6902651",
        "libelle": "SPCM protection 200A avec 2 dérivations 95MM²",
        "unite": "U",
    },
    {
        "code": "S6902653",
        "libelle": "SPCM 400A - 2 dérivations. 95MM² 200A",
        "unite": "U",
    },
    {"code": "S6943405", "libelle": "Fusible 100A T0", "unite": "U"},
    {"code": "S6941272", "libelle": "Adaptateur T2 115MM T00", "unite": "U"},
    {"code": "S6943007", "libelle": "Fusible 125A T2 115MM", "unite": "U"},
    {"code": "S6943009b", "libelle": "Fusible 200A T2 115 MM", "unite": "U"},
    {"code": "S6943013b", "libelle": "Fusible 250A T2 115 MM", "unite": "U"},
    {"code": "S6943450", "libelle": "Barrette SECT T2 115 MM CU Argent", "unite": "U"},
    {"code": "S_kit dériv", "libelle": "Kit dérivation", "unite": "U"},
]
MATERIEL_CONSTRUCTION_TRAVEE = [
    {"code": "S6902664", "libelle": "Kit d’extrémité câble 4x35-70 mm²", "unite": "U"},
    {
        "code": "S6902665",
        "libelle": "Kit d’extrémité câble E 4x50-150 mm²",
        "unite": "U",
    },
    {
        "code": "S6902661",
        "libelle": "Ensemble triphasé connecteurs 35-70P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6902663",
        "libelle": "Ensemble triphasé connecteurs 50-150 P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6902662",
        "libelle": "Ensemble monophasé connecteurs 50-150 P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6902660",
        "libelle": "Ensemble monophasé connecteurs 35-70 P/16-35D",
        "unite": "U",
    },
    {"code": "S6902666", "libelle": "Coffret d’exploitation câbles IRVE", "unite": "U"},
    {
        "code": "S6918371",
        "libelle": "Fourreau DI coffret exploit ICTA 110, couronne de 25m",
        "unite": "M",
    },
    {
        "code": "S6918372",
        "libelle": "Fourreau DI coffret exploit ICTA 110, couronne de 50m",
        "unite": "M",
    },
]
MATERIEL_CREATION_DI = [
    {
        "code": "S6902662",
        "libelle": "Ensemble monophasé connecteurs 50-150P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6902660",
        "libelle": "Ensemble monophasé connecteurs 35-70P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6902663",
        "libelle": "Ensemble triphasé connecteurs 50-150P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6902661",
        "libelle": "Ensemble triphasé connecteurs 35-70P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6125736",
        "libelle": "Cable BT IRVE 4*25 CCA(C50m) → livré 200m",
        "unite": "U",
    },
    {
        "code": "S6125724",
        "libelle": "Cable N AR BT 2*25 IRVE CCA NF 32-323 cable (MONO) (C100m) → livré 400m",
        "unite": "M",
    },
    {
        "code": "S6981222",
        "libelle": "Panneau TRI 25x80 avec CC60A (panneau TRI)",
        "unite": "U",
    },
    {
        "code": "S6981210",
        "libelle": "Panneau MONO 25x50 avec CC60A (panneau MONO)",
        "unite": "U",
    },
    {"code": "S6981155", "libelle": "Panneau de contrôle mono sans CC", "unite": "U"},
    {"code": "S6981220", "libelle": "Panneau de contrôle tri sans CC", "unite": "U"},
    {"code": "S6981221", "libelle": "Panneau de contrôle tri sans CC", "unite": "U"},
    {
        "code": "S6943514",
        "libelle": "Cartouche à fusible à couteaux tailles 00 CALIBRE AD 45A",
        "unite": "U",
    },
    {
        "code": "S6943513",
        "libelle": "Cartouche à fusible à couteaux-00-TYP60A AD (cartouche)",
        "unite": "U",
    },
    {"code": "S6943512", "libelle": "Couteau de neutre taille 00", "unite": "U"},
    {
        "code": "S6930067",
        "libelle": "Disjoncteur Différentiel sélectif 440V T 30A60A (disjoncteur TRI)",
        "unite": "U",
    },
    {
        "code": "S6930061",
        "libelle": "Disjoncteur Différentiel sélectif 250 V B 15A45A (disjoncteur MONO)",
        "unite": "U",
    },
    {"code": "S6940036", "libelle": "C/C mono", "unite": "U"},
    {"code": "S6940038", "libelle": "C/C tri", "unite": "U"},
    {"code": "S4074058", "libelle": "Compteur LINKY TRI CPL G3-P1-60A", "unite": "U"},
    {
        "code": "S4074060",
        "libelle": "Compteur LINKY MONO CPL G3-P2-60A- AB",
        "unite": "U",
    },
    {"code": "S4074061", "libelle": "Compteur LINKY MONO G1-90A", "unite": "U"},
    {"code": "S4074054", "libelle": "Compteur LINKY MONO G3-P1-90A", "unite": "U"},
    {"code": "S4074062", "libelle": "Compteur LINKY TRI G1", "unite": "U"},
]

MATERIEL_CABLES_ET_ACCESSOIRES = [
    {"code": "S6148440", "libelle": "Câble BTS 3X240+115M (ou 120 M) -T", "unite": "M"},
    {"code": "S6148435", "libelle": "Câble BTS 3X150+95M", "unite": "M"},
    {"code": "S6148430", "libelle": "Câble BTS 3X95+70M -T", "unite": "M"},
    {"code": "S6148430b", "libelle": "Câble BTS 3X70+50 M -T", "unite": "M"},
    {"code": "S6148167", "libelle": "Câble BTS 4X50 -T", "unite": "M"},
    {"code": "S6125735", "libelle": "Câble BT IRVE 3x240+95 Cca (T250m)", "unite": "M"},
    {"code": "S6125733", "libelle": "Câble BT IRVE 3x150+70 Cca", "unite": "M"},
    {"code": "S6125731", "libelle": "Câble BT IRVE 3x95+50 Cca (T250m)", "unite": "M"},
    {"code": "S6125730", "libelle": "Câble BT IRVE 3x70+50 Cca (T250m)", "unite": "M"},
    {"code": "S6125729", "libelle": "Câble BT IRVE 4x50+50 Cca (T250m)", "unite": "M"},
    {"code": "S6125728", "libelle": "Câble BT IRVE 4x50 Cca (C225m)", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x240+95 R2V (T250m)", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x150+70 R2V", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x95+50 R2V", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x70+50 R2V", "unite": "M"},
    {"code": "S6023909", "libelle": "Câble BT U1000 4x50 R2V", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x240+95 AR2V (T250m)", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x150+70 AR2V", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x95+50 AR2V", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x70+50 AR2V", "unite": "M"},
    {"code": "", "libelle": "Câble BT 3x50+50 AR2V", "unite": "M"},
    {"code": "", "libelle": "Longueur sous collier créé", "unite": "M"},
    {"code": "", "libelle": "Longueur sous goulotte créé", "unite": "M"},
    {"code": "", "libelle": "Longueur sous fourreau (enterré) créé", "unite": "M"},
    {"code": "", "libelle": "Longueur chemin de câble perforé créé", "unite": "M"},
    {"code": "", "libelle": "Longueur chemin de câble non perforé créé", "unite": "M"},
    {
        "code": "S6910187",
        "libelle": "Chemin de Câbles synthétiques pour parking intérieurs : 150mm",
        "unite": "M",
    },
    {
        "code": "S6910188",
        "libelle": "Chemin de Câbles synthétiques pour parking intérieurs : 200mm",
        "unite": "M",
    },
    {
        "code": "S6910189",
        "libelle": "Chemin de Câbles synthétiques pour parking intérieurs : 300mm",
        "unite": "M",
    },
    {"code": "S6910190", "libelle": "Pendants", "unite": "U"},
    {"code": "S6910191", "libelle": "Equerres ou supports", "unite": "U"},
    {"code": "S6827764", "libelle": "Colliers BIP 180 CV", "unite": "U"},
    {"code": "S6827794", "libelle": "Colliers BIP 260 CV", "unite": "U"},
]

MATERIEL_TRAVAUX_ANNEXES = [
    {
        "code": "",
        "libelle": "Câble de terre isolé C15-100 (longueur totale)",
        "unite": "M",
    },
    {
        "code": "S6902675",
        "libelle": "Placard technique 1 module (armoire SPCM/IS)",
        "unite": "U",
    },
    {
        "code": "S6902676",
        "libelle": "Placard technique 3 modules (armoire SPCM/IS)",
        "unite": "U",
    },
    {
        "code": "S6902677",
        "libelle": "Placard technique 5 modules (armoire SPCM/IS)",
        "unite": "U",
    },
]


RACCORDEMENT = [
    {"code": "S6902033", "libelle": "Borne ECP 3D", "unite": "U"},
    {"code": "S6902019", "libelle": "Coffret ECP 3D", "unite": "U"},
    {"code": "S6902053", "libelle": "Borne ECP 2D", "unite": "U"},
    {"code": "S6902054", "libelle": "Coffret ECP 2D", "unite": "U"},
    {"code": "S6902035", "libelle": "Kit passage de 2D en 3D", "unite": "U"},
]

DERIVATION_COLLECTIVE = [
    {"code": "S6148430", "libelle": "Câble BTS 3X95+70M (50E) touret", "unite": "M"},
    {"code": "S6148435", "libelle": "Câble BTS 3X150+95M (70E)", "unite": "M"},
    {"code": "S6148440", "libelle": "Câble BTS 3X240+115M (95E)", "unite": "M"},
    {
        "code": "S6126112",
        "libelle": "Câble non armé BT alu TORS 3X70+54,6",
        "unite": "M",
    },
    {
        "code": "S6126260",
        "libelle": "Câble non armé BT alu TORS 3X150+70",
        "unite": "M",
    },
]

DERIVATION_COLLECTIVE_EXTERIEUR = [
    {"code": "S6772101", "libelle": "Borne REMBT Harmoniée 300 + JDB", "unite": "U"},
    {
        "code": "S6772130",
        "libelle": "Borne REMBT Harmoniée 450 + JDB + RRCP",
        "unite": "U",
    },
    {
        "code": "S6772138",
        "libelle": "Borne REMBT Harmoniée 600 + JDB + RRCP",
        "unite": "U",
    },
    {
        "code": "S6148162",
        "libelle": "CA C33210 BT AL 4X35 CIR MA - S6148162",
        "unite": "M",
    },
    {
        "code": "S6126112",
        "libelle": "Câble non armé BT alu torsadé 3X70+54,6",
        "unite": "M",
    },
    {"code": "S6792059", "libelle": "Ensemble BT NJAS 150-70/240S-95", "unite": "U"},
    {
        "code": "S6729408",
        "libelle": "Capuchon rétractable réseau CRR 16-70 pour du 70²",
        "unite": "U",
    },
    {
        "code": "S6729410",
        "libelle": "Capuchon rétractable réseau CRR 150 pourdu 150²",
        "unite": "U",
    },
]

DI_COFFRET_EXPLOITATION = [
    {"code": "S6902666", "libelle": "Coffret d’exploitation câbles IRVE", "unite": "U"},
    {
        "code": "S6902663",
        "libelle": "Ensemble triphasé connecteurs 50-150 P/16-35D",
        "unite": "U",
    },
    {
        "code": "S6125117",
        "libelle": "Câble alu torsadé R SPO 4X25 Couronne 80 m",
        "unite": "M",
    },
]

MATERIEL_TRAVAUX_ANNEXES_EXT = [
    {"code": "S_cable_terre1", "libelle": "Câble alu isolé vert/jaune", "unite": "M"},
    {"code": "S_barette_terre", "libelle": "Barrette coupure de terre", "unite": "U"},
]

MATERIEL_DI_BOX_FERME = [
    {
        "code": "S6737640",
        "libelle": "Connecteur CBS/CT 70 - 35/70 - 16/35",
        "unite": "U",
    },
    {
        "code": "S6737650",
        "libelle": "Connecteur CBS/CT 70 - 54/150 - 16/35",
        "unite": "U",
    },
    {
        "code": "S6125074",
        "libelle": "Câble alu torsadé SS PORT 2X25 couronne 100 M",
        "unite": "M",
    },
    {"code": "S_CTA3522", "libelle": "Fourreau classique ICTA 3522", "unite": "M"},
    {"code": "S6910193", "libelle": "Socle Mobilier Urbain IRVE", "unite": "U"},
    {"code": "Scli_protect", "libelle": "Dispositif protection socles", "unite": "U"},
    {"code": "S6981155", "libelle": "Panneau TB 25X22 GP SH BL 2EBCP-AU", "unite": "U"},
    {
        "code": "S6981210",
        "libelle": "Panneau synthétique blanc CBEM+DB CC25X50",
        "unite": "U",
    },
    {"code": "S6981220", "libelle": "Panneau synthétique 25X55 BL TB+DB", "unite": "U"},
    {
        "code": "S6981221",
        "libelle": "Panneau de contrôle TRI 330x330 Type I",
        "unite": "U",
    },
    {
        "code": "S6981222",
        "libelle": "Panneau synthétique 25X80 BL TB+DB 1CC60A",
        "unite": "U",
    },
    {
        "code": "S6940036",
        "libelle": "C/C Bipolaire 90A PR cartouche TX AD00",
        "unite": "U",
    },
    {
        "code": "S6940038",
        "libelle": "C/C Tétrapolaire 60A PR cartouche CTX AD00",
        "unite": "U",
    },
    {
        "code": "S6930061",
        "libelle": "Disjoncteur Différentiel sélectif BIP (15A45A)",
        "unite": "U",
    },
    {
        "code": "S6930067",
        "libelle": "Disjoncteur Différentiel sélectif 4440V T 30A60A",
        "unite": "U",
    },
    {
        "code": "S6771034",
        "libelle": "Lot 50 dispositif blocage disjoncteur",
        "unite": "U",
    },
    {
        "code": "S6771033",
        "libelle": "Lot 50 scellé dispositif blocage disjoncteur",
        "unite": "U",
    },
    {"code": "S6771035", "libelle": "Lot 50 étiquettes blocage disj", "unite": "U"},
    {
        "code": "S4074060",
        "libelle": "Compteur LINKY MONO CPL G3-P2-60A- AB",
        "unite": "U",
    },
    {
        "code": "S69435142",
        "libelle": "Cartouche fusible à couteau -00-TYP45A-AD",
        "unite": "U",
    },
    {"code": "S6943512", "libelle": "Couteau de Neutre taille 00", "unite": "U"},
]

MATERIEL_DI_MUR_EXTERIEUR = [
    {
        "code": "S6737640",
        "libelle": "Connecteur CBS/CT 70 - 35/70 - 16/35",
        "unite": "U",
    },
    {
        "code": "S6737650",
        "libelle": "Connecteur CBS/CT 70 - 54/150 - 16/35",
        "unite": "U",
    },
    {
        "code": "S6125074",
        "libelle": "Câble alu torsadé SS PORT 2X25 COUR 100 M",
        "unite": "M",
    },
    {"code": "S_CTA3522", "libelle": "Fourreau classique ICTA 3522", "unite": "M"},
    {"code": "S6910193", "libelle": "Socle Mobilier Urbain IRVE", "unite": "U"},
    {"code": "Scli_protect", "libelle": "Dispositif protection socles", "unite": "U"},
    {"code": "S6981155", "libelle": "Panneau TB 25X22 GP SH BL 2EBCP-AU", "unite": "U"},
    {"code": "C6981210", "libelle": "Panneau SYNT BLANC CBEM+DB CC25X50", "unite": "U"},
    {"code": "C6981220", "libelle": "Panneau SYNT 25X55 BL TB+DB", "unite": "U"},
    {
        "code": "C6981221",
        "libelle": "Panneau de contrôle TRI 330x330 Type I",
        "unite": "U",
    },
    {"code": "C6981222", "libelle": "Panneau SYNT 25X80 BL TB+DB 1CC60A", "unite": "U"},
    {
        "code": "C6940036",
        "libelle": "Coupe Circuit bipolaire 90A PR CARTOUCHE CTX AD00",
        "unite": "U",
    },
    {
        "code": "C6940038",
        "libelle": "Coupe Circuit tétrapolaire 60A pour cartouche CTX AD00",
        "unite": "U",
    },
    {
        "code": "S6940038",
        "libelle": "Coupe Circuit tétrapolaire 60A pour cartouche CTX AD00",
        "unite": "U",
    },
    {
        "code": "S6930061",
        "libelle": "Disjoncteur Différentiel sélectif BIP (15A45A)",
        "unite": "U",
    },
    {
        "code": "S6930067",
        "libelle": "Disjoncteur Différentiel sélectif 440V T 30A60A",
        "unite": "U",
    },
    {"code": "S6771034", "libelle": "Lot 50 dispositif blocage disj", "unite": "U"},
    {
        "code": "S6771033",
        "libelle": "Lot 50 scellé dispositif blocage Disj",
        "unite": "U",
    },
    {"code": "S6771035", "libelle": "Lot 50 étiquettes blocage disj", "unite": "U"},
    {"code": "S4074061", "libelle": "Compteur LINKY MONO-CPL G1-P1-90A", "unite": "U"},
    {
        "code": "S4074060",
        "libelle": "Compteur LINKY MONO CPL G3-P2-60A- AB",
        "unite": "U",
    },
    {"code": "S4074054", "libelle": "Compteur LINKY MONO CPL G3-P1-90A", "unite": "U"},
    {"code": "S4074062", "libelle": "Compteur LINKY TRI-CPL G1-P1-60A", "unite": "U"},
    {"code": "S4074058", "libelle": "Compteur LINKY TRI CPL G3-P1-60A", "unite": "U"},
    {
        "code": "S69435143",
        "libelle": "Cartouche fusible à couteaux T-00-TYP45A-AD",
        "unite": "U",
    },
    {
        "code": "S69435144",
        "libelle": "Cartouche fusible à couteaux-00-TYP45A-AD",
        "unite": "U",
    },
    {"code": "S6943512", "libelle": "Couteau de Neutre taille 00", "unite": "U"},
]

MATERIEL_DI_PARKING_SOL = [
    {
        "code": "S6125074",
        "libelle": "Câble alu torsadé SS PORT 2X25 COUR 100 M",
        "unite": "M",
    },
    {"code": "S_CTA3522", "libelle": "Fourreau classique ICTA3522", "unite": "M"},
    {"code": "S6910193", "libelle": "Socle Mobilier Urbain IRVE", "unite": "U"},
    {"code": "Scli_protect", "libelle": "Dispositif protection socles", "unite": "U"},
    {"code": "S_mobilier", "libelle": "Mobilier extérieur", "unite": "U"},
    {"code": "S6980866", "libelle": "Coffret Haut CIBE NU COMPLET", "unite": "U"},
    {"code": "S6980818", "libelle": "Grille de repiquage CIBE 3x35²", "unite": "U"},
    {"code": "C6981155", "libelle": "Panneau TB 25X22 GP SH BL 2EBCP-AU", "unite": "U"},
    {
        "code": "C6981210",
        "libelle": "Panneau synthétique blanc CBEM+DB CC25X50",
        "unite": "U",
    },
    {
        "code": "S6930067",
        "libelle": "Disjoncteur Différentiel sélectif 440V T 30A60A",
        "unite": "U",
    },
    {"code": "S6771034", "libelle": "Lot 50 dispositif blocage disj", "unite": "U"},
    {
        "code": "S6771033",
        "libelle": "Lot 50 scellé dispositif blocage Disj",
        "unite": "U",
    },
    {"code": "S6771035", "libelle": "Lot 50 étiquettes blocage disj", "unite": "U"},
    {"code": "S4074061", "libelle": "Compteur LINKY MONO-CPL G1-P1-90A", "unite": "U"},
    {
        "code": "S4074060",
        "libelle": "Compteur LINKY MONO CPL G3-P2-60A- AB",
        "unite": "U",
    },
    {"code": "S4074054", "libelle": "Compteur LINKY MONO CPL G3-P1-80A", "unite": "U"},
    {
        "code": "S69435145",
        "libelle": "Cartouche à fusible à couteaux -00-TYP45A-AD",
        "unite": "U",
    },
    {"code": "S6943512", "libelle": "Couteau de Neutre taille 00", "unite": "U"},
]
EXTENSION_RESEAU = [
    {
        "code": "",
        "libelle": "BTS - 95 mm²",
        "unite": "M",
    },
]
DEMANDEUR_ROWS = [
    {
        "type": "Accueil par le Génie-Civil de l'immeuble de canalisation collective ou de travée",
        "desc": "Pose de caniveaux permettant le passage de canalisations électriques, création de dos d’âne sur toit terrasse, etc.",
        "realisation": "Demandeur",
    },
    {
        "type": "Accueil par le Génie-Civil de l'immeuble de canalisation collective ou de travée",
        "desc": "Terrassement sur revêtement particulier",
        "realisation": "Demandeur",
    },
    {
        "type": "Travaux de Génie-Civil ci-dessus présentant un seuil d’amiante supérieur aux normes",
        "desc": "Réalisation DTA (Dossier Technique d'Amiante), placé sous la responsabilité du Demandeur",
        "realisation": "Demandeur",
    },
    {
        "type": "Création et/ou adaptation de la mise à la terre de l'immeuble",
        "desc": "Travaux imposés par la norme C15-100",
        "realisation": "Demandeur",
    },
]

ENEDIS_ROWS = [
    {
        "type": "Accueil par le Génie-Civil de l'immeuble de coffrets, armoires, mobilier…",
        "desc": "Confection de niche sur façade, encastrement du coffret sur façade, pose de coffret sur mur, etc.",
        "realisation": "Enedis",
    },
    {
        "type": "Accueil par le Génie civil de l'immeuble de canalisation collective ou de travée",
        "desc": "Création d'un placard technique",
        "realisation": "Enedis",
    },
    {
        "type": "Accueil par le Génie civil de l'immeuble de canalisation collective ou de travée",
        "desc": "Création de tranchée, pose de fourreaux",
        "realisation": "Enedis",
    },
    {
        "type": "Accueil par le Génie civil de l'immeuble de canalisation collective ou de travée",
        "desc": "Percements supérieurs à 50 mm, etc.",
        "realisation": "Enedis",
    },
    {
        "type": "Accueil de la dérivation individuelle dans les parties communes",
        "desc": "Fourniture et pose de socles pour accueillir les bornes, etc.",
        "realisation": "Enedis",
    },
    {
        "type": "Réalisation de travaux dans le Génie-Civil du bâtiment pouvant avoir un impact sur sa structure lors de percements, etc.",
        "desc": "Études et travaux spécialisés commandées à des prestataires habilités",
        "realisation": "Enedis",
    },
    {
        "type": "Fourniture et pose de matériels",
        "desc": "Fourniture et pose d'armoire, coffret pour l'infrastructure collective, etc.",
        "realisation": "Enedis",
    },
    {
        "type": "Reprise du circuit de terre : norme C15-100",
        "desc": "Déroulage de la terre C15-100 en partie collective (hors Dérivation Individuelle)",
        "realisation": "Enedis",
    },
    {
        "type": "Travaux de Génie-Civil présentant un seuil d’amiante supérieur aux normes",
        "desc": "En fonction du DTA (Dossier Technique d'Amiante) ou si absence de DTA, réalisation d’un RAT (Repérage Avant Travaux).",
        "realisation": "Enedis",
    },
    {
        "type": "Travaux de Génie-Civil présentant un seuil d’amiante supérieur aux normes",
        "desc": "Réalisation de travaux en sous-section IV si présence d'amiante",
        "realisation": "Enedis",
    },
]


def process_pdf(pdf_file):
    if pdf_file is not None:
        pdf_base64 = base64.b64encode(pdf_file.read()).decode("utf-8")
        return f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600px"></iframe>'
    return ""


def process_excel(excel_file):
    xlsx_data = pd.read_excel(excel_file, sheet_name=None)
    xlsx_html = (
        """<hr style="border: none; height: 1px; background-color: #995b9f; ">"""
    )
    for sheet_name, df in xlsx_data.items():
        xlsx_html += f"<h4>{sheet_name}</h4>"

        xlsx_html += f"""<table class="tg">
        <thead>
            <tr>
            <th class="th-title" style="font-size: 11px; width:40%">{df.columns[0]}</th>
            <th class="th-title" style="font-size: 11px; width:15%">{df.columns[1]}</th>
            <th class="th-title" style="font-size: 11px; width:15%">{df.columns[2]}</th>
            <th class="th-title" style="font-size: 11px; width:15%">{df.columns[3]}</th>
            <th class="th-title" style="font-size: 11px; width:15%">{df.columns[4]}</th>
            </tr>
        </thead>
        <tbody>"""
        for _, row in df.iterrows():
            xlsx_html += f"""
            <tr>
                <td class="tg-merge" style="width:40%">{row[0]}</td>
                <td class="tg-merge" style="width:15%">{row[1]}</td>
                <td class="tg-merge" style="width:15%">{row[2]}</td>
                <td class="tg-merge" style="width:15%">{row[3]}</td>
                <td class="tg-merge" style="width:15%">{row[4]}</td>
            </tr>
            """
        xlsx_html += """
        </tbody>
        </table>
        """
    return xlsx_html


def render_prefinancement_table_html(dict_name, selected_descs):
    if len(selected_descs) == 0:
        return ""
    html = """
    <table class="tg">
      <thead>
        <tr>
          <th class="th-title" style="font-size: 11px; width:40%">Type de travaux</th>
          <th class="th-title" style="font-size: 11px; width:40%">Descriptif Technique</th>
          <th class="th-title" style="font-size: 11px; width:20%">Réalisation</th>
        </tr>
      </thead>
      <tbody>
    """

    if dict_name == "enedis":
        rows = ENEDIS_ROWS
    elif dict_name == "demandeur":
        rows = DEMANDEUR_ROWS

    for row in rows:
        if row["desc"] in selected_descs:
            html += f"""
            <tr>
              <td class="tg-merge" style="width:40%">{row["type"]}</td>
              <td class="tg-merge" style="width:40%">{row["desc"]}</td>
              <td class="tg-merge" style="width:20%">{row["realisation"]}</td>
            </tr>
            """

    html += """
      </tbody>
    </table>
    """
    return html


def generate_material_html_table(title, data_list, session_key):
    rows_html = ""
    for row in data_list:
        key = row["code"] or row["libelle"]
        quantity = st.session_state.get(session_key, {}).get(key, 0)
        if quantity > 0:
            rows_html += f"""
            <tr>
              <td class="tg-merge" style="width: 60%; text-align: left;">{row["libelle"]}</td>
              <td class="tg-merge" style="width: 40%; text-align: center;">{quantity} {row["unite"]}</td>
            </tr>
            """

    if rows_html:
        return f"""
        <div class="tableau">
          <table class="tg">
            <thead>
              <tr>
                <th class="th-title"; font-size: 11px;" colspan="2">{title}</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>
        </div>
        """
    return ""


def image_to_base64(image_file):
    if image_file is not None:
        return base64.b64encode(image_file.read()).decode("utf-8")
    return ""


def insert_image_to_fields(file_or_files, placeholder, alt_text, fields):
    if not file_or_files:
        return

    if not isinstance(file_or_files, list):
        file_or_files = [file_or_files]  # Assure que c’est une liste

    images_html = ""
    for file in file_or_files:
        image_base64 = base64.b64encode(file.read()).decode("utf-8")
        mime_type = file.type
        images_html += (
            f'<div style="width:100%; margin-bottom: 10px;">'
            f'<img src="data:{mime_type};base64,{image_base64}" '
            f'alt="{alt_text}" style="display: block; width:70%; max-width: 70%;" />'
            f"</div>"
        )

    fields[placeholder] = images_html


def insert_images_to_fields(etats_dict, placeholder, alt_text, fields):
    """
    Insère un dictionnaire {niveau_label: [list of files]} dans le champ HTML.
    """
    if not etats_dict or all(not files for files in etats_dict.values()):
        fields[placeholder] = f"<p>Pas d'image {alt_text.lower()}</p>"
        return

    html_output = ""
    for niveau_label, files in etats_dict.items():
        if files:
            html_output += f"<div><strong>{niveau_label}</strong></div>"
            for file in files:
                image_base64 = base64.b64encode(file.read()).decode("utf-8")
                mime_type = file.type
                html_output += f'''
                    <div style="width:100%; margin-bottom: 10px;">
                        <img src="data:{mime_type};base64,{image_base64}" 
                             alt="{alt_text}" 
                             style="display: block; width:70%; max-width: 70%;" />
                    </div>
                '''
    fields[placeholder] = html_output


def insert_images_to_fields_titles(etats_dict, placeholder, alt_text, fields):
    """
    Insère un dictionnaire {niveau_label: [list of files]} dans le champ HTML.
    """
    if not etats_dict or all(not files for files in etats_dict.values()):
        fields[placeholder] = f"<p>Pas d'image {alt_text.lower()}</p>"
        return

    html_output = ""
    for niveau_label, files in etats_dict.items():
        if files:
            html_output += f"<h4>{niveau_label}</h4>"
            for file in files:
                image_base64 = base64.b64encode(file.read()).decode("utf-8")
                mime_type = file.type
                html_output += f'''
                    <div style="width:100%; margin-bottom: 10px;">
                        <img src="data:{mime_type};base64,{image_base64}" 
                             alt="{alt_text}" 
                             style="display: block; width:70%; max-width: 70%;" />
                    </div>
                '''
    fields[placeholder] = html_output


def save_temp_image(image_file):
    """
    Sauvegarde l'image uploadée dans un fichier temporaire et renvoie
    le chemin complet vers ce fichier.
    """
    if image_file is not None:
        suffix = "." + image_file.name.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(image_file.read())
            return tmp_file.name  # Chemin absolu (ex. /var/folders/.../tmpabcd.jpg)
    return ""


def html_to_pdf(source_html):
    result = BytesIO()
    pisa_status = pisa.CreatePDF(src=source_html, dest=result)
    if pisa_status.err:
        return None
    return result.getvalue()
