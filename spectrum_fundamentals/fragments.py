import logging
from operator import itemgetter
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from . import constants as constants

logger = logging.getLogger(__name__)


def _get_modifications(peptide_sequence: str) -> Optional[Tuple[Dict[int, float], int, str]]:
    """
    Get modification masses and position in a peptide sequence.

    :param peptide_sequence: Modified peptide sequence
    :return: tuple with - dictionary of modification_position => mod_mass
                        - 2 if there is an isobaric tag on the n-terminal, else 1
                        - sequence without modifications
    """
    modification_deltas = {}
    tmt_n_term = 1
    modifications = constants.MOD_MASSES.keys()
    modification_mass = constants.MOD_MASSES
    # Handle terminal modifications here
    for possible_tmt_mod in constants.TMT_MODS.values():
        n_term_tmt = possible_tmt_mod + "-"
        if peptide_sequence.startswith(n_term_tmt):
            tmt_n_term = 2
            modification_deltas.update({0: constants.MOD_MASSES[possible_tmt_mod]})
            peptide_sequence = peptide_sequence[len(n_term_tmt) :]
            break

    if "(" in peptide_sequence:
        logger.info(
            "Error Modification "
            + peptide_sequence[peptide_sequence.find("(") + 1 : peptide_sequence.find(")")]
            + " not "
            "found"
        )
        return None

    while "[" in peptide_sequence:
        found_modification = False
        modification_index = peptide_sequence.index("[")
        for mod in modifications:
            if peptide_sequence[modification_index : modification_index + len(mod)] == mod:
                if modification_index - 1 in modification_deltas:
                    modification_deltas.update(
                        {modification_index - 1: modification_deltas[modification_index - 1] + modification_mass[mod]}
                    )
                else:
                    modification_deltas.update({modification_index - 1: modification_mass[mod]})
                peptide_sequence = (
                    peptide_sequence[0:modification_index] + peptide_sequence[modification_index + len(mod) :]
                )
                found_modification = True
        if not found_modification:
            logger.info(
                "Error Modification "
                + peptide_sequence[modification_index : peptide_sequence.find("]") + 1]
                + " not found"
            )
            return None

    return modification_deltas, tmt_n_term, peptide_sequence


def compute_peptide_mass(sequence: str) -> float:
    """
    Compute the theoretical mass of the peptide sequence.

    :param sequence: Modified peptide sequence
    :raises AssertionError: if an unknown modification has been found in the peptide sequence
    :return: Theoretical mass of the sequence
    """
    peptide_sequence = sequence
    modifications = _get_modifications(peptide_sequence)
    if modifications is None:
        raise AssertionError("Modification not found.")
    else:
        modification_deltas, tmt_n_term, peptide_sequence = modifications

    peptide_length = len(peptide_sequence)
    if peptide_length > 30:
        # return [], -1, ""
        return -1.0

    n_term_delta = 0.0

    # get mass delta for the c-terminus
    c_term_delta = 0.0

    n_term = constants.ATOM_MASSES["H"] + n_term_delta  # n-terminal delta [N]
    c_term = constants.ATOM_MASSES["O"] + constants.ATOM_MASSES["H"] + c_term_delta  # c-terminal delta [C]
    h = constants.ATOM_MASSES["H"]

    ion_type_offsets = [n_term - h, c_term + h]

    # calculation:
    forward_sum = 0.0  # sum over all amino acids from left to right (neutral charge)

    for i in range(0, peptide_length):  # generate substrings
        forward_sum += constants.AA_MASSES[peptide_sequence[i]]  # sum left to right
        if i in modification_deltas:  # add mass of modification if present
            forward_sum += modification_deltas[i]
    return forward_sum + ion_type_offsets[0] + ion_type_offsets[1]


def initialize_peaks(
    sequence: str,
    mass_analyzer: str,
    charge: int,
    mass_tolerance: Optional[float] = None,
    unit_mass_tolerance: Optional[str] = None,
    noncl_xl: int = 0,
    peptide_beta_mass: Optional[int] = None,
    xl_pos: Optional[int] = None,
) -> Tuple[List[dict], int, str, float]:
    """
    Generate theoretical peaks for a modified peptide sequence.

    :param sequence: Modified peptide sequence
    :param mass_analyzer: Type of mass analyzer used eg. FTMS, ITMS
    :param charge: Precursor charge
    :param mass_tolerance: mass tolerance to calculate min and max mass
    :param unit_mass_tolerance: unit for the mass tolerance (da or ppm)
    :param noncl_xl: whether the function is called with a non-cleavable xl modification
    :param peptide_beta_mass: the mass of the second peptide to be considered for non-cleavable XL
    :param xl_pos: the position of the crosslinker for non-cleavable XL
    :raises AssertionError:  if peptide sequence contained an unknown modification. TODO do this within the get_mod func.
    :return: List of theoretical peaks, Flag to indicate if there is a tmt on n-terminus, Un modified peptide sequence
    """
    peptide_sequence = sequence
    modifications = _get_modifications(peptide_sequence)
    if modifications is None:
        raise AssertionError("Modification not found.")
    else:
        modification_deltas, tmt_n_term, peptide_sequence = modifications

    peptide_length = len(peptide_sequence)
    if peptide_length > 30:
        return [{}], -1, "", 0.0

    # initialize constants
    if int(round(charge)) <= 3:
        max_charge = int(round(charge))
    else:
        max_charge = 3

    n_term_delta = 0.0

    # get mass delta for the c-terminus
    c_term_delta = 0.0

    n_term = constants.ATOM_MASSES["H"] + n_term_delta  # n-terminal delta [N]
    c_term = constants.ATOM_MASSES["O"] + constants.ATOM_MASSES["H"] + c_term_delta  # c-terminal delta [C]

    # cho = constants.ATOM_MASSES["H"] + constants.ATOM_MASSES["C"] + constants.ATOM_MASSES["O"]
    h = constants.ATOM_MASSES["H"]
    # co = constants.ATOM_MASSES["C"] + constants.ATOM_MASSES["O"]
    # nh2 = constants.ATOM_MASSES["N"] + constants.ATOM_MASSES["H"] * 2.0

    ion_type_offsets = [n_term - h, c_term + h]

    # tmp place holder
    ion_type_masses = [0.0, 0.0]
    ion_types = ["b", "y"]

    number_of_ion_types = len(ion_type_offsets)
    fragments_meta_data = []
    # calculation:
    forward_sum = 0.0  # sum over all amino acids from left to right (neutral charge)
    backward_sum = 0.0  # sum over all amino acids from right to left (neutral charge)
    for i in range(0, peptide_length):  # generate substrings
        forward_sum += constants.AA_MASSES[peptide_sequence[i]]  # sum left to right
        if i in modification_deltas:  # add mass of modification if present
            forward_sum += modification_deltas[i]
        backward_sum += constants.AA_MASSES[peptide_sequence[peptide_length - i - 1]]  # sum right to left
        if peptide_length - i - 1 in modification_deltas:  # add mass of modification if present
            backward_sum += modification_deltas[peptide_length - i - 1]

        ion_type_masses[0] = forward_sum + ion_type_offsets[0]  # b ion - ...

        ion_type_masses[1] = backward_sum + ion_type_offsets[1]  # y ion

        for charge in range(constants.MIN_CHARGE, max_charge + 1):  # generate ion in different charge states
            # positive charge is introduced by protons (or H - ELECTRON_MASS)
            charge_delta = charge * constants.PARTICLE_MASSES["PROTON"]
            for ion_type in range(0, number_of_ion_types):  # generate all ion types
                # Check for neutral loss here
                if noncl_xl == 1 and ion_type == 0 and i + 1 >= xl_pos:  # for the b ions
                    ion_mass_with_peptide_beta = ion_type_masses[ion_type] + peptide_beta_mass
                    mass = (ion_mass_with_peptide_beta + charge_delta) / charge
                elif noncl_xl == 1 and ion_type == 1 and i >= peptide_length - xl_pos:  # for the y-ions
                    ion_mass_with_peptide_beta = ion_type_masses[ion_type] + peptide_beta_mass
                    mass = (ion_mass_with_peptide_beta + charge_delta) / charge
                else:
                    mass = (ion_type_masses[ion_type] + charge_delta) / charge
                min_mass, max_mass = get_min_max_mass(mass_analyzer, mass, mass_tolerance, unit_mass_tolerance)
                fragments_meta_data.append(
                    {
                        "ion_type": ion_types[ion_type],  # ion type
                        "no": i + 1,  # no
                        "charge": charge,  # charge
                        "mass": mass,  # mass
                        "min_mass": min_mass,  # min mass
                        "max_mass": max_mass,  # max mass
                    }
                )
    fragments_meta_data = sorted(fragments_meta_data, key=itemgetter("mass"))
    return fragments_meta_data, tmt_n_term, peptide_sequence, (forward_sum + ion_type_offsets[0] + ion_type_offsets[1])


def initialize_peaks_xl(
    sequence: str,
    mass_analyzer: str,
    crosslinker_position: int,
    crosslinker_type: str,
    mass_tolerance: Optional[float] = None,
    unit_mass_tolerance: Optional[str] = None,
    sequence_beta: Optional[str] = None,
) -> Tuple[List[dict], int, str, float]:
    """
    Generate theoretical peaks for a modified (potentially cleavable cross-linked) peptide sequence.

    This function get only one modified peptide (peptide a or b))

    :param sequence: Modified peptide sequence (peptide a or b)
    :param mass_analyzer: Type of mass analyzer used eg. FTMS, ITMS
    :param crosslinker_position: The position of crosslinker
    :param crosslinker_type: Can be either DSSO, DSBU or BuUrBU
    :param mass_tolerance: mass tolerance to calculate min and max mass
    :param unit_mass_tolerance: unit for the mass tolerance (da or ppm)
    :param sequence_beta: optional second peptide to be considered for non-cleavable XL
    :raises ValueError: if crosslinker_type is unkown
    :raises AssertionError: if the short and long XL sequence (the one with the short / long crosslinker mod)
        has a tmt n term while the other one does not
    :return: List of theoretical peaks, flag to indicate if there is a tmt on n-terminus, unmodified peptide
        sequence, therotical mass of modified peptide (without considering mass of crosslinker)
    """
    crosslinker_type = crosslinker_type.upper()

    if crosslinker_type in ["DSSO", "DSBU", "BUURBU"]:  # cleavable XL
        charge = 2  # generate only peaks with charge 1 and 2
        if crosslinker_type == "DSSO":
            dsso = "[UNIMOD:1896]"
            dsso_s = "[UNIMOD:1881]"
            dsso_l = "[UNIMOD:1882]"
            sequence_s = sequence.replace(dsso, dsso_s)
            sequence_l = sequence.replace(dsso, dsso_l)
            sequence_without_crosslinker = sequence.replace(dsso, "")

        elif crosslinker_type in ["DSBU", "BUURBU"]:
            dsbu = "[UNIMOD:1884]"
            dsbu_s = "[UNIMOD:1886]"
            dsbu_l = "[UNIMOD:1885]"
            sequence_s = sequence.replace(dsbu, dsbu_s)
            sequence_l = sequence.replace(dsbu, dsbu_l)
            sequence_without_crosslinker = sequence.replace(dsbu, "")

        # TODO: this needs to be done more efficiently:
        # currently calculating the non-cleaved part until the xl_pos of the ions two times!
        # also the peptide sequence, mass and modifications are called twice
        # need to separate all of these functions better!
        # for XL, we actually don't need mass_s / mass_l at the moment because only one mass, without
        # the crosslinker is returned! This needs to be fixed, because mass is used as CALCULATED_MASS in
        # percolator!

        list_out_s, tmt_n_term_s, peptide_sequence, mass_s = initialize_peaks(
            sequence_s, mass_analyzer, charge, mass_tolerance, unit_mass_tolerance
        )
        list_out_l, tmt_n_term_l, peptide_sequence, mass_l = initialize_peaks(
            sequence_l, mass_analyzer, charge, mass_tolerance, unit_mass_tolerance
        )

        tmt_n_term = tmt_n_term_s
        if tmt_n_term_s ^ tmt_n_term_l:
            raise AssertionError("tmt_mod is {tmt_n_term_s} for short sequence but {tmt_n_term_l} for long sequence!")

        df_out_s = pd.DataFrame(list_out_s)
        df_out_l = pd.DataFrame(list_out_l)

        threshold_b = crosslinker_position
        threshold_y = len(peptide_sequence) - crosslinker_position + 1

        df_out_s.loc[(df_out_s["no"] >= threshold_b) & (df_out_s["ion_type"] == "b"), "ion_type"] = "b-short"
        df_out_s.loc[(df_out_s["no"] >= threshold_y) & (df_out_s["ion_type"] == "y"), "ion_type"] = "y-short"
        df_out_l.loc[(df_out_l["no"] >= threshold_b) & (df_out_l["ion_type"] == "b"), "ion_type"] = "b-long"
        df_out_l.loc[(df_out_l["no"] >= threshold_y) & (df_out_l["ion_type"] == "y"), "ion_type"] = "y-long"

        concatenated_df = pd.concat([df_out_s, df_out_l])
        unique_df = concatenated_df.drop_duplicates()  # TODO: this is where the duplicate calculations are removed
        df_out = unique_df.sort_values("mass")
        mass = compute_peptide_mass(sequence_without_crosslinker)

    elif crosslinker_type in ["BS3", "DSS"]:  # non-cleavable XL
        charge=3    # generate only peaks with charge 1, 2 and 3

        sequence_without_crosslinker = sequence.replace("[UNIMOD:1898]", "")
        sequence_beta_without_crosslinker = sequence_beta.replace("[UNIMOD:1898]", "")
        sequence_mass = compute_peptide_mass(sequence_without_crosslinker)
        sequence_beta_mass = compute_peptide_mass(sequence_beta_without_crosslinker)

        list_out, tmt_n_term, peptide_sequence, calc_mass_s = initialize_peaks(
            sequence,
            mass_analyzer,
            charge,
            mass_tolerance,
            unit_mass_tolerance,
            1,
            sequence_beta_mass,
            crosslinker_position,
        )
        df_out = pd.DataFrame(list_out)

        threshold_b_alpha = crosslinker_position
        threshold_y_alpha = len(peptide_sequence) - crosslinker_position + 1

        df_out.loc[(df_out["no"] >= threshold_b_alpha) & (df_out["ion_type"] == "b"), "ion_type"] = "b-xl"
        df_out.loc[(df_out["no"] >= threshold_y_alpha) & (df_out["ion_type"] == "y"), "ion_type"] = "y-xl"

        df_out = df_out.sort_index()
        unique_df = df_out.drop_duplicates()
        df_out = unique_df.sort_values("mass")
        mass = sequence_mass

    else:
        raise ValueError(f"Unkown crosslinker type: {crosslinker_type}")

    return df_out.to_dict(orient="records"), tmt_n_term, peptide_sequence, mass


def get_min_max_mass(
    mass_analyzer: str, mass: float, mass_tolerance: Optional[float] = None, unit_mass_tolerance: Optional[str] = None
) -> Tuple[float, float]:
    """Helper function to get min and max mass based on mass analyzer.

    If both mass_tolerance and unit_mass_tolerance are provided, the function uses the provided tolerance
    to calculate the min and max mass. If either `mass_tolerance` or `unit_mass_tolerance` is missing
    (or both are None), the function falls back to the default tolerances based on the `mass_analyzer`.

    Default mass tolerances for different mass analyzers:
    - FTMS: +/- 20 ppm
    - TOF: +/- 40 ppm
    - ITMS: +/- 0.35 daltons

    :param mass_tolerance: mass tolerance to calculate min and max mass
    :param unit_mass_tolerance: unit for the mass tolerance (da or ppm)
    :param mass_analyzer: the type of mass analyzer used to determine the tolerance.
    :param mass: the theoretical fragment mass
    :raises ValueError: if mass_analyzer is other than one of FTMS, TOF, ITMS
    :raises ValueError: if unit_mass_tolerance is other than one of ppm, da

    :return: a tuple (min, max) denoting the mass tolerance range.
    """
    if mass_tolerance is not None and unit_mass_tolerance is not None:
        if unit_mass_tolerance == "ppm":
            min_mass = (mass * -mass_tolerance / 1000000) + mass
            max_mass = (mass * mass_tolerance / 1000000) + mass
        elif unit_mass_tolerance == "da":
            min_mass = mass - mass_tolerance
            max_mass = mass + mass_tolerance
        else:
            raise ValueError(f"Unsupported unit for the mass tolerance: {unit_mass_tolerance}")
    elif mass_analyzer == "FTMS":
        min_mass = (mass * -20 / 1000000) + mass
        max_mass = (mass * 20 / 1000000) + mass
    elif mass_analyzer == "TOF":
        min_mass = (mass * -40 / 1000000) + mass
        max_mass = (mass * 40 / 1000000) + mass
    elif mass_analyzer == "ITMS":
        min_mass = mass - 0.35
        max_mass = mass + 0.35
    else:
        raise ValueError(f"Unsupported mass_analyzer: {mass_analyzer}")
    return (min_mass, max_mass)


def compute_ion_masses(seq_int: List[int], charge_onehot: List[int], tmt: str = "") -> Optional[np.ndarray]:
    """
    Collects an integer sequence e.g. [1,2,3] with charge 2 and returns array with 174 positions for ion masses.

    Invalid masses are set to -1.

    :param seq_int: TODO
    :param charge_onehot: is a onehot representation of charge with 6 elems for charges 1 to 6
    :param tmt: TODO
    :return: list of masses as floats
    """
    charge = list(charge_onehot).index(1) + 1
    if not (charge in (1, 2, 3, 4, 5, 6) and len(charge_onehot) == 6):
        print("[ERROR] One-hot-enconded Charge is not in valid range 1 to 6")
        return None

    if not len(seq_int) == constants.SEQ_LEN:
        print(f"[ERROR] Sequence length {len(seq_int)} is not desired length of {constants.SEQ_LEN}")
        return None

    idx = list(seq_int).index(0) if 0 in seq_int else constants.SEQ_LEN
    masses = np.ones((constants.SEQ_LEN - 1) * 2 * 3, dtype=np.float32) * -1
    mass_b = 0
    mass_y = 0
    j = 0  # iterate over masses

    # Iterate over sequence, sequence should have length 30
    for i in range(idx - 1):  # only 29 possible ions
        j = i * 6  # index for masses array at position

        # MASS FOR Y IONS
        # print("Added", constants.VEC_MZ[seq_int[l-1-i]])
        mass_y += constants.VEC_MZ[seq_int[idx - 1 - i]]

        # Compute charge +1
        masses[j] = (
            mass_y
            + 1 * constants.PARTICLE_MASSES["PROTON"]
            + constants.MASSES["C_TERMINUS"]
            + constants.ATOM_MASSES["H"]
        ) / 1.0
        # Compute charge +2
        masses[j + 1] = (
            (
                mass_y
                + 2 * constants.PARTICLE_MASSES["PROTON"]
                + constants.MASSES["C_TERMINUS"]
                + constants.ATOM_MASSES["H"]
            )
            / 2.0
            if charge >= 2
            else -1.0
        )
        # Compute charge +3
        masses[j + 2] = (
            (
                mass_y
                + 3 * constants.PARTICLE_MASSES["PROTON"]
                + constants.MASSES["C_TERMINUS"]
                + constants.ATOM_MASSES["H"]
            )
            / 3.0
            if charge >= 3.0
            else -1.0
        )

        # MASS FOR B IONS
        if i == 0 and tmt != "":
            mass_b += constants.VEC_MZ[seq_int[i]] + constants.MOD_MASSES[constants.TMT_MODS[tmt]]
        else:
            mass_b += constants.VEC_MZ[seq_int[i]]

        # Compute charge +1
        masses[j + 3] = (
            mass_b
            + 1 * constants.PARTICLE_MASSES["PROTON"]
            + constants.MASSES["N_TERMINUS"]
            - constants.ATOM_MASSES["H"]
        ) / 1.0
        # Compute charge +2
        masses[j + 4] = (
            (
                mass_b
                + 2 * constants.PARTICLE_MASSES["PROTON"]
                + constants.MASSES["N_TERMINUS"]
                - constants.ATOM_MASSES["H"]
            )
            / 2.0
            if charge >= 2
            else -1.0
        )
        # Compute charge +3
        masses[j + 5] = (
            (
                mass_b
                + 3 * constants.PARTICLE_MASSES["PROTON"]
                + constants.MASSES["N_TERMINUS"]
                - constants.ATOM_MASSES["H"]
            )
            / 3.0
            if charge >= 3.0
            else -1.0
        )

    return masses
