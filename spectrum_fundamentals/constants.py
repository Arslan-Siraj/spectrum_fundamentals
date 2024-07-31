from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

#####################
# GENERAL CONSTANTS #
#####################

SEQ_LEN = 30  # Sequence length for prosit
NUM_CHARGES_ONEHOT = 6
MIN_CHARGE = 1
MAX_CHARGE = 6
BATCH_SIZE = 6000
VEC_LENGTH = (
    (SEQ_LEN - 1) * 2 * 3
)  # peptide of length 30 has 29 b and y-ions, each with charge 1+, 2+ and 3+, for a total of 174 fragments
VEC_LENGTH_CMS2 = (SEQ_LEN - 1) * 2 * 3 * 2
# peptide of length 30 can have 29 b, y, b_short, y_short, b_long and y_long ions, each with charge 1+, 2+ and 3+
# we do not annotate fragments wth charge 3+. All fragmets with charge 3+ convert to -1
#############
# ALPHABETS #
#############

AA_ALPHABET = {
    "A": 1,
    "C": 24,
    "D": 3,
    "E": 4,
    "F": 5,
    "G": 6,
    "H": 7,
    "I": 8,
    "K": 9,
    "L": 10,
    "M": 11,
    "N": 12,
    "P": 13,
    "Q": 14,
    "R": 15,
    "S": 16,
    "T": 17,
    "V": 18,
    "W": 19,
    "Y": 20,
}

TERMINAL_ALPHABET = {"[]-": 30, "-[]": 31}  # unmodified n terminus  # unmodified c terminus

ALPHABET_MODS = {
    "M[UNIMOD:35]": 21,
    "C[UNIMOD:4]": 2,
    "K[UNIMOD:737]": 22,
    "K[UNIMOD:2016]": 22,
    "K[UNIMOD:214]": 22,
    "K[UNIMOD:730]": 22,
    "K[UNIMOD:1896]": 22,
    "K[UNIMOD:1898]": 22,
    "K[UNIMOD:1884]": 23,
    "K[UNIMOD:1881]": 24,
    "K[UNIMOD:1882]": 25,
    "K[UNIMOD:1885]": 26,
    "K[UNIMOD:1886]": 27,
    "S[UNIMOD:21]": 25,
    "T[UNIMOD:21]": 26,
    "Y[UNIMOD:21]": 27,
    "S[UNIMOD:23]": 16,
    "T[UNIMOD:23]": 17,
    "Y[UNIMOD:23]": 20,
    "[UNIMOD:1]-": 32,
    "K[UNIMOD:259]": 9,
    "R[UNIMOD:267]": 15,
}

ALPHABET = {**AA_ALPHABET, **ALPHABET_MODS, **TERMINAL_ALPHABET}

######################
# MaxQuant constants #
######################

MAXQUANT_VAR_MODS = {
    "(ox)": "[UNIMOD:35]",
    "(Oxidation (M))": "[UNIMOD:35]",
    "(tm)": "[UNIMOD:737]",
    "_(tm)": "_[UNIMOD:737]-",
    "K(tm)": "K[UNIMOD:737]",
    "(i4)": "[UNIMOD:214]",
    "_(i4)": "_[UNIMOD:214]-",
    "K(i4)": "K[UNIMOD:214]",
    "(i8)": "[UNIMOD:730]",
    "_(i8)": "_[UNIMOD:730]-",
    "K(i8)": "K[UNIMOD:730]",
    "(tmp)": "[UNIMOD:2016]",
    "_(tmp)": "_[UNIMOD:2016]-",
    "K(tmp)": "K[UNIMOD:2016]",
    "(ph)": "[UNIMOD:21]",
    "(Phospho (STY))": "[UNIMOD:21]",
    "(de)": "[UNIMOD:23]",
    "(Dehydrated (ST))": "[UNIMOD:23]",
    "K(Lys8)": "K[UNIMOD:259]",
    "R(Arg10)": "R[UNIMOD:267]",
    "C(Carbamidomethyl (C))": "C[UNIMOD:4]",
}

MAXQUANT_NC_TERM = {"^_": "", "_$": ""}

#######################
# MsFragger constants #
#######################

MSFRAGGER_VAR_MODS = {
    "C[160]": "C[UNIMOD:4]",
    "M[147]": "M[UNIMOD:35]",
    "K[230]": "K[UNIMOD:737]",
    "K[305]": "K[UNIMOD:2016]",
    "K[214]": "K[UNIMOD:214]",
    "n[230]": "[UNIMOD:737]-",
    "n[305]": "[UNIMOD:2016]-",
    "n[214]": "[UNIMOD:214]-",
}

#######################
# Xisearch constants #
#######################

XISEARCH_VAR_MODS = {
    "ox": "[UNIMOD:35]",
    "cm": "[UNIMOD:4]",
    "dsso": "[UNIMOD:1896]",
    "dsbu": "[UNIMOD:1884]",
}

####################
# MASS CALCULATION #
####################

# initialize other masses
PARTICLE_MASSES = {"PROTON": 1.007276467, "ELECTRON": 0.00054858}

# masses of different atoms
ATOM_MASSES = {
    "H": 1.007825035,
    "C": 12.0,
    "O": 15.9949146,
    "N": 14.003074,
}

MASSES = {**PARTICLE_MASSES, **ATOM_MASSES}
MASSES["N_TERMINUS"] = MASSES["H"]
MASSES["C_TERMINUS"] = MASSES["O"] + MASSES["H"]


AA_MASSES = {
    "A": 71.037114,
    "R": 156.101111,
    "N": 114.042927,
    "D": 115.026943,
    "C": 103.009185,
    "E": 129.042593,
    "Q": 128.058578,
    "G": 57.021464,
    "H": 137.058912,
    "I": 113.084064,
    "L": 113.084064,
    "K": 128.094963,
    "M": 131.040485,
    "F": 147.068414,
    "P": 97.052764,
    "S": 87.032028,
    "T": 101.047679,
    "U": 150.95363,
    "W": 186.079313,
    "Y": 163.063329,
    "V": 99.068414,
    "[]-": MASSES["N_TERMINUS"],
    "-[]": MASSES["C_TERMINUS"],
}

MOD_MASSES = {
    "[UNIMOD:737]": 229.162932,  # TMT_6
    "[UNIMOD:2016]": 304.207146,  # TMT_PRO
    "[UNIMOD:214]": 144.102063,  # iTRAQ4
    "[UNIMOD:730]": 304.205360,  # iTRAQ8
    "[UNIMOD:259]": 8.014199,  # SILAC Lysine
    "[UNIMOD:267]": 10.008269,  # SILAC Arginine
    "[]": 0.0,
    "[UNIMOD:1]": 42.010565,  # Acetylation
    "[UNIMOD:1896]": 158.003765,  # DSSO-crosslinker
    "[UNIMOD:1881]": 54.010565,  # Alkene short fragment of DSSO-crosslinker
    "[UNIMOD:1882]": 85.982635,  # Thiol long fragment of DSSO-crosslinker
    "[UNIMOD:1884]": 196.084792,  # BuUrBu (DSBU)-crosslinker
    "[UNIMOD:1885]": 111.032028,  # BuUr long fragment of BuUrBu (DSBU)-crosslinker
    "[UNIMOD:1886]": 85.052764,  # Bu short fragment of BuUrBu (DSBU)-crosslinker
    "[UNIMOD:1898]": 138.068080,  # DSS and BS3 non-cleavable crosslinker
    "[UNIMOD:122]": 27.994915,  # Formylation
    "[UNIMOD:1289]": 70.041865,  # Butyrylation
    "[UNIMOD:1363]": 68.026215,  # Crotonylation
    "[UNIMOD:1848]": 114.031694,  # Glutarylation
    "[UNIMOD:1914]": -32.008456,  # Oxidation and then loss of oxidized M side chain
    "[UNIMOD:2]": -0.984016,  # Amidation
    "[UNIMOD:21]": 79.966331,  # Phosphorylation
    "[UNIMOD:213]": 541.06111,  # ADP-ribosylation
    "[UNIMOD:23]": -18.010565,  # Water Loss
    "[UNIMOD:24]": 71.037114,  # Propionamidation
    "[UNIMOD:354]": 44.985078,  # Nitrosylation
    "[UNIMOD:28]": -17.026549,  # Glu to PyroGlu
    "[UNIMOD:280]": 28.0313,  # Ethylation
    "[UNIMOD:299]": 43.989829,  # Carboxylation
    "[UNIMOD:3]": 226.077598,  # Biotinylation
    "[UNIMOD:34]": 14.01565,  # Methylation
    "[UNIMOD:345]": 47.984744,  # Trioxidation
    "[UNIMOD:35]": 15.994915,  # Hydroxylation
    "[UNIMOD:351]": 3.994915,  # Oxidation to Kynurenine
    "[UNIMOD:36]": 28.0313,  # Dimethylation
    "[UNIMOD:360]": -30.010565,  # Pyrrolidinone
    "[UNIMOD:368]": -33.987721,  # Dehydroalanine
    "[UNIMOD:37]": 42.04695,  # Trimethylation
    "[UNIMOD:385]": -17.026549,  # Ammonia loss
    "[UNIMOD:392]": 29.974179,  # Quinone
    "[UNIMOD:4]": 57.021464,  # Carbamidomethyl
    "[UNIMOD:40]": 79.956815,  # Sulfonation
    "[UNIMOD:401]": -2.01565,  # Didehydro
    "[UNIMOD:425]": 31.989829,  # Dioxidation
    "[UNIMOD:43]": 203.079373,  # HexNAc
    "[UNIMOD:44]": 204.187801,  # Farnesylation
    "[UNIMOD:447]": -15.994915,  # Reduction
    "[UNIMOD:46]": 229.014009,  # Pyridoxal phosphate
    "[UNIMOD:47]": 238.229666,  # Palmitoylation
    "[UNIMOD:5]": 43.005814,  # Carbamyl
    "[UNIMOD:58]": 56.026215,  # Propionylation
    "[UNIMOD:6]": 58.005479,  # Carboxymethylation
    "[UNIMOD:64]": 100.016044,  # Succinylation
    "[UNIMOD:7]": 0.984016,  # Deamidation
    "[UNIMOD:747]": 86.000394,  # Malonylation
}


def update_mod_masses(mods: Optional[Dict[str, Dict[str, Tuple[str, float]]]] = None) -> Dict[str, float]:
    """
    Function to update MOD_MASSES with custom modifications.

    :param mods: Modifications with respective mass
    :raises AssertionError: if mass of modification was not provided as float.
    :return: updated MOD_MASSES
    """
    mod_masses = {}
    if mods:
        try:
            stat_mods: List[Tuple[str, float]] = [
                (value[0], float(value[1])) for key, value in (mods.get("stat_mods") or {}).items()
            ]
            var_mods: List[Tuple[str, float]] = [
                (value[0], float(value[1])) for key, value in (mods.get("var_mods") or {}).items()
            ]
        except ValueError as e:
            raise AssertionError("All custom modifications value entries must be of type Tuple[str, float]") from e

        for value in stat_mods + var_mods:
            mod_masses[value[0]] = float(value[1])

    return MOD_MASSES | mod_masses


MOD_MASSES_SAGE = {
    "229.1629": "[UNIMOD:737]",
    "304.2071": "[UNIMOD:2016]",
    "144.1020": "[UNIMOD:214]",
    "304.2053": "[UNIMOD:730]",
    "8.0141": "[UNIMOD:259]",
    "10.0082": "[UNIMOD:267]",
    "79.9663": "[UNIMOD:21]",
    "-18.0105": "[UNIMOD:23]",
    "57.0215": "[UNIMOD:4]",
    "15.9949": "[UNIMOD:35]",
    "15.994": "[UNIMOD:35]",
    "42.0105": "[UNIMOD:1]",
}
# these are only used for prosit_grpc, oktoberfest uses the masses from MOD_MASSES
AA_MOD_MASSES = {
    "K[UNIMOD:737]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:737]"],
    "M[UNIMOD:35]": AA_MASSES["M"] + MOD_MASSES["[UNIMOD:35]"],
    "C[UNIMOD:4]": AA_MASSES["C"] + MOD_MASSES["[UNIMOD:4]"],
    "K[UNIMOD:2016]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:2016]"],
    "K[UNIMOD:214]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:214]"],
    "K[UNIMOD:730]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:730]"],
    "S[UNIMOD:21]": AA_MASSES["S"] + MOD_MASSES["[UNIMOD:21]"],
    "T[UNIMOD:21]": AA_MASSES["T"] + MOD_MASSES["[UNIMOD:21]"],
    "Y[UNIMOD:21]": AA_MASSES["Y"] + MOD_MASSES["[UNIMOD:21]"],
    "S[UNIMOD:23]": AA_MASSES["S"],  # + MOD_MASSES['[UNIMOD:23]'],
    "T[UNIMOD:23]": AA_MASSES["T"],  # + MOD_MASSES['[UNIMOD:23]'],
    "Y[UNIMOD:23]": AA_MASSES["Y"],  # + MOD_MASSES['[UNIMOD:23]'],
    "K[UNIMOD:1896]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:1896]"],
    "K[UNIMOD:1881]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:1881]"],
    "K[UNIMOD:1882]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:1882]"],
    "K[UNIMOD:1884]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:1884]"],
    "K[UNIMOD:1885]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:1885]"],
    "K[UNIMOD:1886]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:1886]"],
    "K[UNIMOD:1898]": AA_MASSES["K"] + MOD_MASSES["[UNIMOD:1898]"],
    "[UNIMOD:1]-": MASSES["N_TERMINUS"] + MOD_MASSES["[UNIMOD:1]"],
    "K[UNIMOD:259]": AA_MASSES[
        "K"
    ],  # + MOD_MASSES['[UNIMOD:259]'],#we need a different way of encoding mods on AA so it wouldn't have same encoding
    # to make vecMZ work
    "R[UNIMOD:267]": AA_MASSES["R"],  # + MOD_MASSES['[UNIMOD:267]']
}

AA_MOD = {**AA_MASSES, **AA_MOD_MASSES}

#######################################
# HELPERS FOR FRAGMENT MZ CALCULATION #
#######################################

# Array containing masses --- at index one is mass for A, etc.
# these are only used for prosit_grpc, oktoberfest uses the masses from MOD_MASSES
VEC_MZ = np.zeros(max(ALPHABET.values()) + 1)
for a, i in ALPHABET.items():
    VEC_MZ[i] = AA_MOD[a]

# small positive intensity to distinguish invalid ion (=0) from missing peak (=EPSILON)
EPSILON = 1e-7

B_ION_MASK = np.tile([0, 0, 0, 1, 1, 1], SEQ_LEN - 1)
Y_ION_MASK = np.tile([1, 1, 1, 0, 0, 0], SEQ_LEN - 1)
SINGLE_CHARGED_MASK = np.tile([1, 0, 0, 1, 0, 0], SEQ_LEN - 1)
DOUBLE_CHARGED_MASK = np.tile([0, 1, 0, 0, 1, 0], SEQ_LEN - 1)
TRIPLE_CHARGED_MASK = np.tile([0, 0, 1, 0, 0, 1], SEQ_LEN - 1)

B_ION_MASK_XL = np.tile([0, 0, 0, 1, 1, 1], (SEQ_LEN - 1) * 2)
Y_ION_MASK_XL = np.tile([1, 1, 1, 0, 0, 0], (SEQ_LEN - 1) * 2)
SINGLE_CHARGED_MASK_XL = np.tile([1, 0, 0, 1, 0, 0], (SEQ_LEN - 1) * 2)
DOUBLE_CHARGED_MASK_XL = np.tile([0, 1, 0, 0, 1, 0], (SEQ_LEN - 1) * 2)
TRIPLE_CHARGED_MASK_XL = np.tile([0, 0, 1, 0, 0, 1], (SEQ_LEN - 1) * 2)


MASK_DICT = {
    1: SINGLE_CHARGED_MASK,
    2: DOUBLE_CHARGED_MASK,
    3: TRIPLE_CHARGED_MASK,
    4: B_ION_MASK,
    5: Y_ION_MASK,
}


MASK_DICT_XL = {
    1: SINGLE_CHARGED_MASK_XL,
    2: DOUBLE_CHARGED_MASK_XL,
    3: TRIPLE_CHARGED_MASK_XL,
    4: B_ION_MASK_XL,
    5: Y_ION_MASK_XL,
}


SHARED_DATA_COLUMNS = ["RAW_FILE", "SCAN_NUMBER"]
META_DATA_ONLY_COLUMNS = [
    "MODIFIED_SEQUENCE",
    "PRECURSOR_CHARGE",
    "MASS",
    "SCAN_EVENT_NUMBER",
    "PRECURSOR_MASS_EXP",
    "SCORE",
    "REVERSE",
    "PROTEINS",
]
META_DATA_COLUMNS = SHARED_DATA_COLUMNS + META_DATA_ONLY_COLUMNS
MZML_ONLY_DATA_COLUMNS = [
    "INTENSITIES",
    "MZ",
    "MZ_RANGE",
    "RETENTION_TIME",
    "MASS_ANALYZER",
    "FRAGMENTATION",
    "COLLISION_ENERGY",
    "INSTRUMENT_TYPES",
]
MZML_DATA_COLUMNS = SHARED_DATA_COLUMNS + MZML_ONLY_DATA_COLUMNS

TMT_MODS = {
    "tmt": "[UNIMOD:737]",
    "tmtpro": "[UNIMOD:2016]",
    "itraq4": "[UNIMOD:214]",
    "itraq8": "[UNIMOD:730]",
    "tmt_msa": "[UNIMOD:737]",
    "tmtpro_msa": "[UNIMOD:2016]",
    "itraq4_msa": "[UNIMOD:214]",
    "itraq8_msa": "[UNIMOD:730]",
}

# Used for MSP spectral library format
MOD_NAMES = {
    "[UNIMOD:737]": "TMT_6",
    "[UNIMOD:2016]": "TMT_Pro",
    "[UNIMOD:21]": "Phospho",
    "[UNIMOD:4]": "Carbamidomethyl",
    "[UNIMOD:35]": "Oxidation",
    "[UNIMOD:214]": "iTRAQ4",
    "[UNIMOD:730]": "iTRAQ8",
}

# Used for MSP spectral library format
SPECTRONAUT_MODS = {
    "[UNIMOD:737]": "[TMT_6]",
    "[UNIMOD:2016]": "[TMT_Pro]",
    "[UNIMOD:21]": "[Phospho]",
    "[UNIMOD:4]": "[Carbamidomethyl (C)]",
    "[UNIMOD:35]": "[Oxidation (O)]",
}

FRAGMENTATION_ENCODING = {"HCD": 2, "CID": 1}

############################
# GENERATION OF ANNOTATION #
############################

IONS = ["y", "b"]  # limited to single character unicode string when array is created
CHARGES = [1, 2, 3]  # limited to uint8 (0-255) when array is created
POSITIONS = [x for x in range(1, 30)]  # fragment numbers 1-29 -- limited to uint8 (0-255) when array is created

ANNOTATION_FRAGMENT_TYPE = []
ANNOTATION_FRAGMENT_CHARGE = []
ANNOTATION_FRAGMENT_NUMBER = []
for pos in POSITIONS:
    for ion in IONS:
        for charge in CHARGES:
            ANNOTATION_FRAGMENT_TYPE.append(ion)
            ANNOTATION_FRAGMENT_CHARGE.append(charge)
            ANNOTATION_FRAGMENT_NUMBER.append(pos)

ANNOTATION = [ANNOTATION_FRAGMENT_TYPE, ANNOTATION_FRAGMENT_CHARGE, ANNOTATION_FRAGMENT_NUMBER]


########################
# RESCORING PARAMETERS #
########################


class RescoreType(Enum):
    """Class for rescoring types."""

    PROSIT = "prosit"
    ANDROMEDA = "andromeda"
