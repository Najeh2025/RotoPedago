# =============================================================================
# utils/helpers.py — Fonctions utilitaires pour RotoPédago v5.0
# =============================================================================
import streamlit as st
import numpy as np
from typing import Optional, Dict, List, Tuple
import hashlib


# =============================================================================
# CACHE DÉCORATEURS (fonctions globales — compatibles Streamlit)
# =============================================================================

@st.cache_data(show_spinner=False)
def compute_modal_cached(rotor_data_hash: str, speed_rad: float) -> Dict:
    """
    Cache wrapper pour run_modal — appelé depuis SimulationEngine.
    Retourne un dictionnaire sérialisable avec les résultats modaux.
    """
    return {"cached": True, "speed_rad": speed_rad, "hash": rotor_data_hash}


@st.cache_data(show_spinner=False)
def compute_campbell_cached(rotor_data_hash: str, speeds_rad: Tuple) -> Dict:
    """Cache wrapper pour run_campbell."""
    return {"cached": True, "speeds_count": len(speeds_rad), "hash": rotor_data_hash}


def hash_rotor_config(shaft_cfg: List, disk_cfg: List, bearing_cfg: List) -> str:
    """Génère un hash unique pour une configuration de rotor (pour le cache)."""
    config_str = f"{shaft_cfg}|{disk_cfg}|{bearing_cfg}"
    return hashlib.md5(config_str.encode()).hexdigest()


# =============================================================================
# VALIDATION ET FEEDBACK
# =============================================================================

def validate_numeric_param(value: float, min_val: float, max_val: float, 
                          param_name: str) -> Tuple[bool, Optional[str]]:
    """Valide un paramètre numérique et retourne (ok, message_erreur)."""
    if not isinstance(value, (int, float)):
        return False, f"{param_name} doit être un nombre"
    if value < min_val or value > max_val:
        return False, f"{param_name} doit être entre {min_val} et {max_val}"
    return True, None


def format_frequency(fn_rad_s: float, unit: str = "Hz") -> str:
    """Formate une fréquence avec unité."""
    if unit == "Hz":
        return f"{fn_rad_s / (2 * np.pi):.2f} Hz"
    elif unit == "rad/s":
        return f"{fn_rad_s:.2f} rad/s"
    elif unit == "RPM":
        return f"{fn_rad_s * 60 / (2 * np.pi):.0f} RPM"
    return f"{fn_rad_s:.2f}"


# =============================================================================
# VISUALISATION HELPERS
# =============================================================================

def get_log_dec_color(log_dec: float) -> str:
    """Retourne une couleur hex pour le Log Decrément."""
    if log_dec > 0.3:
        return "#22863A"  # Vert
    elif log_dec > 0.1:
        return "#F9A825"  # Orange
    elif log_dec > 0:
        return "#E65100"  # Orange foncé
    else:
        return "#C00000"  # Rouge (instable)


def create_badge_html(badge_type: str, tp_id: str) -> str:
    """Génère le HTML pour un badge de réussite."""
    badges = {
        "gold": ('<span class="badge badge-gold">🥇', "Or</span>"),
        "silver": ('<span class="badge badge-silver">🥈', "Argent</span>'),
        "bronze": ('<span class="badge badge-bronze">🥉', "Bronze</span>")
    }
    prefix, suffix = badges.get(badge_type, ('<span class="badge">', "</span>"))
    return f"{prefix} {tp_id} — {suffix}"
