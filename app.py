# =============================================================================
# RotoPédago v5.1 — Application Streamlit pédagogique pour la rotordynamique
# Version corrigée et fiabilisée
# =============================================================================

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

try:
    import ross as rs
    ROSS_AVAILABLE = True
except Exception:
    rs = None
    ROSS_AVAILABLE = False


# =============================================================================
# CONFIGURATION GLOBALE
# =============================================================================
st.set_page_config(
    page_title="RotoPédago v5.1",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_TITLE = "RotoPédago v5.1"

SESSION_DEFAULTS = {
    "user_name": "Étudiant",
    "badges": {},
    "tp11_rotor": None,
    "tp12_modal": None,
    "tp21_rotor": None,
    "tp21_camp": None,
    "tp22_modal": None,
    "tp22_unbal": None,
    "tp31_rotor": None,
    "tp32_rotor": None,
    "tp32_modal": None,
    "tp32_camp": None,
    "free_rotor": None,
    "free_modal": None,
    "free_camp": None,
}


# =============================================================================
# CATALOGUE DES TP
# =============================================================================
TP_CATALOGUE: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "Niveau 1 — Découverte",
        "duration": "~30 min",
        "color": "#22863A",
        "tps": {
            "TP1.1": {
                "title": "Mon premier rotor",
                "icon": "🔧",
                "objectives": [
                    "Créer un arbre simple (5 éléments)",
                    "Ajouter un disque au nœud central",
                    "Définir deux paliers aux extrémités",
                ],
                "theory": (
                    "Un rotor se compose d'un arbre, de disques et de paliers. "
                    "L'assemblage par éléments finis mène aux matrices de masse, rigidité et amortissement."
                ),
                "default_params": {
                    "n_elements": 5,
                    "L_elem": 0.2,
                    "od": 0.05,
                    "disk_node": 2,
                    "disk_od": 0.25,
                    "disk_width": 0.07,
                    "kxx": 1e7,
                    "kyy": 1e7,
                    "cxx": 500.0,
                    "cyy": 500.0,
                },
                "validation": {
                    "expected_nodes_min": 4,
                    "expected_mass_min": 5.0,
                    "expected_mass_max": 200.0,
                },
                "hints": [
                    "Utilisez 5 éléments pour commencer.",
                    "Les nœuds sont numérotés de 0 à n_elements.",
                    "La masse totale attendue doit rester réaliste.",
                ],
            },
            "TP1.2": {
                "title": "Modes propres et déformées",
                "icon": "📊",
                "objectives": [
                    "Calculer les fréquences naturelles",
                    "Afficher le tableau wn / wd / Log Dec",
                    "Visualiser la déformée du premier mode",
                ],
                "theory": (
                    "L'analyse modale résout un problème aux valeurs propres. "
                    "Les valeurs propres complexes renseignent la fréquence amortie et la stabilité des modes."
                ),
                "default_params": {"n_modes": 6, "speed_rpm": 0.0},
                "validation": {
                    "fn1_min": 5.0,
                    "fn1_max": 500.0,
                    "log_dec_positive": True,
                },
                "hints": [
                    "run_modal(speed=0) donne les modes à l'arrêt.",
                    "Une fréquence propre > 0 indique un modèle correctement contraint.",
                    "Un Log Dec > 0 indique un mode stable.",
                ],
            },
        },
    },
    2: {
        "title": "Niveau 2 — Maîtrise",
        "duration": "~60 min",
        "color": "#C55A11",
        "tps": {
            "TP2.1": {
                "title": "Paliers anisotropes et Campbell",
                "icon": "📈",
                "objectives": [
                    "Définir Kxx ≠ Kyy",
                    "Tracer le diagramme de Campbell",
                    "Identifier les vitesses critiques (intersections 1X)",
                ],
                "theory": (
                    "Un palier anisotrope lève la dégénérescence des modes. "
                    "Le diagramme de Campbell représente les fréquences en fonction de la vitesse de rotation."
                ),
                "default_params": {
                    "kxx": 1e7,
                    "kyy": 5e6,
                    "kxy": 0.0,
                    "cxx": 500.0,
                    "cyy": 500.0,
                    "speed_max_rpm": 8000,
                },
                "validation": {
                    "anisotropy_ratio_min": 1.5,
                    "stability_margin": 0.15,
                },
                "hints": [
                    "Kxx / Kyy > 1.5 facilite la séparation des modes.",
                    "Les intersections avec la droite 1X correspondent aux vitesses critiques synchrones.",
                    "Augmentez la résolution du Campbell pour un tracé plus lisse.",
                ],
            },
            "TP2.2": {
                "title": "Réponse au balourd",
                "icon": "🌀",
                "objectives": [
                    "Définir un balourd (kg·m)",
                    "Calculer la réponse fréquentielle",
                    "Identifier le pic de résonance et le DAF",
                ],
                "theory": (
                    "Un balourd produit une force tournante proportionnelle à m·e·ω². "
                    "La réponse au balourd met en évidence la résonance et l'influence de l'amortissement."
                ),
                "default_params": {
                    "unbalance_node": 2,
                    "unbalance_magnitude": 0.001,
                    "unbalance_phase_deg": 0,
                    "probe_node": 2,
                    "freq_max_hz": 80.0,
                },
                "validation": {"daf_reasonable_min": 1.0},
                "hints": [
                    "Un pic net apparaît près de la première fréquence propre.",
                    "Le balourd est saisi en kg·m.",
                    "Le DAF compare l'amplitude dynamique à une amplitude de référence.",
                ],
            },
        },
    },
    3: {
        "title": "Niveau 3 — Expertise",
        "duration": "~90 min",
        "color": "#1F5C8B",
        "tps": {
            "TP3.1": {
                "title": "Instabilité par raideur croisée",
                "icon": "⚠️",
                "objectives": [
                    "Comprendre le rôle de Kxy",
                    "Observer la transition stable → instable",
                    "Identifier un seuil critique de Kxy",
                ],
                "theory": (
                    "La raideur croisée peut déstabiliser le mode de précession avant. "
                    "L'instabilité apparaît quand le décrément logarithmique devient négatif."
                ),
                "default_params": {"kxy_max": 1e7, "speed_max_rpm": 5000},
                "validation": {"log_dec_sign_change": True},
                "hints": [
                    "Augmentez Kxy progressivement.",
                    "Un Log Dec < 0 indique une instabilité.",
                    "Le seuil dépend de la vitesse de rotation.",
                ],
            },
            "TP3.2": {
                "title": "Cas industriel complet",
                "icon": "🏭",
                "objectives": [
                    "Modéliser un rotor industriel simplifié",
                    "Vérifier des critères inspirés de l'API 684",
                    "Générer un rapport complet",
                ],
                "theory": (
                    "Les études rotordynamiques industrielles vérifient les vitesses critiques, "
                    "la stabilité et la réponse dynamique dans la plage d'exploitation."
                ),
                "default_params": {
                    "operating_rpm": 3000,
                    "n_elements": 8,
                    "od": 0.08,
                    "kxx": 5e7,
                    "kyy": 5e7,
                    "cxx": 1000.0,
                    "cyy": 1000.0,
                },
                "validation": {
                    "api684_margin": 0.15,
                    "min_log_dec": 0.1,
                    "performance_score": 0.85,
                },
                "hints": [
                    "La zone interdite peut être prise comme [0.85×Nop, 1.15×Nop].",
                    "Log Dec ≥ 0.1 est un bon critère pédagogique de stabilité.",
                    "Documentez systématiquement vos hypothèses.",
                ],
            },
        },
    },
}


# =============================================================================
# OUTILS GÉNÉRAUX
# =============================================================================
def init_session_state() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


def ross_required() -> bool:
    if not ROSS_AVAILABLE:
        st.error(
            "La bibliothèque ROSS n'est pas installée. "
            "Installez les dépendances puis redémarrez l'application."
        )
        return False
    return True


def safe_plot(obj: Any, preferred_methods: Optional[List[str]] = None, **kwargs: Any):
    methods = preferred_methods or [
        "plot_mode_3d",
        "plot_mode_shape",
        "plot_deflected_shape",
        "plot_deformation",
        "plot",
    ]
    for method_name in methods:
        if hasattr(obj, method_name):
            method = getattr(obj, method_name)
            try:
                fig = method(**kwargs)
                if fig is not None:
                    return fig
            except Exception:
                continue
    return None


def to_rad_per_sec_from_rpm(speed_rpm: float) -> float:
    return float(speed_rpm) * np.pi / 30.0


def to_hz_from_rad_per_sec(omega: np.ndarray) -> np.ndarray:
    return np.asarray(omega, dtype=float) / (2.0 * np.pi)


def state_get(key: str, default: Any = None) -> Any:
    return st.session_state.get(key, default)


def state_set(key: str, value: Any) -> None:
    st.session_state[key] = value


def metric_card(label: str, value: Any, help_text: str = "") -> None:
    st.metric(label, value, help=help_text if help_text else None)


def get_material():
    if not ROSS_AVAILABLE:
        return None
    return rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9)


# =============================================================================
# CLASSES MÉTIER
# =============================================================================
class RotorBuilder:
    """Constructeur de rotors ROSS avec validations robustes."""

    def __init__(self):
        self.material = get_material()
        self.shaft_elements: List[Any] = []
        self.disk_elements: List[Any] = []
        self.bearing_elements: List[Any] = []
        self._errors: List[str] = []

    @property
    def errors(self) -> List[str]:
        return self._errors

    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0

    def add_shaft(self, n_elements: int, L: float, od: float, id_: float = 0.0) -> "RotorBuilder":
        if not ROSS_AVAILABLE:
            self._errors.append("ROSS non disponible.")
            return self
        if n_elements < 2:
            self._errors.append("Au moins 2 éléments d'arbre sont requis.")
            return self
        if L <= 0 or od <= 0 or id_ < 0:
            self._errors.append("Les dimensions d'arbre doivent être strictement positives.")
            return self
        if id_ >= od:
            self._errors.append("Le diamètre intérieur doit être inférieur au diamètre extérieur.")
            return self
        try:
            self.shaft_elements = [
                rs.ShaftElement(L=float(L), idl=float(id_), odl=float(od), material=self.material)
                for _ in range(int(n_elements))
            ]
        except Exception as exc:
            self._errors.append(f"Erreur de création des éléments d'arbre : {exc}")
        return self

    def add_disk(self, node: int, od: float, width: float, id_: float = 0.05) -> "RotorBuilder":
        if not ROSS_AVAILABLE:
            self._errors.append("ROSS non disponible.")
            return self
        if not self.shaft_elements:
            self._errors.append("Définissez d'abord l'arbre avant d'ajouter un disque.")
            return self
        n_nodes = len(self.shaft_elements) + 1
        if node < 0 or node >= n_nodes:
            self._errors.append(f"Nœud disque invalide : {node}. Nœuds disponibles : 0 à {n_nodes - 1}.")
            return self
        if od <= 0 or width <= 0 or id_ < 0:
            self._errors.append("Les dimensions du disque doivent être positives.")
            return self
        if id_ >= od:
            self._errors.append("Le diamètre intérieur du disque doit être inférieur au diamètre extérieur.")
            return self
        try:
            self.disk_elements.append(
                rs.DiskElement.from_geometry(
                    n=int(node),
                    material=self.material,
                    width=float(width),
                    i_d=float(id_),
                    o_d=float(od),
                )
            )
        except Exception as exc:
            self._errors.append(f"Erreur de création du disque : {exc}")
        return self

    def add_bearing(
        self,
        node: int,
        kxx: float,
        kyy: float,
        kxy: float = 0.0,
        cxx: float = 500.0,
        cyy: float = 500.0,
    ) -> "RotorBuilder":
        if not ROSS_AVAILABLE:
            self._errors.append("ROSS non disponible.")
            return self
        if not self.shaft_elements:
            self._errors.append("Définissez d'abord l'arbre avant d'ajouter un palier.")
            return self
        n_nodes = len(self.shaft_elements) + 1
        if node < 0 or node >= n_nodes:
            self._errors.append(f"Nœud palier invalide : {node}. Nœuds disponibles : 0 à {n_nodes - 1}.")
            return self
        for name, value in {"kxx": kxx, "kyy": kyy}.items():
            if value <= 0:
                self._errors.append(f"{name} doit être > 0.")
                return self
        for name, value in {"cxx": cxx, "cyy": cyy}.items():
            if value < 0:
                self._errors.append(f"{name} doit être ≥ 0.")
                return self
        try:
            self.bearing_elements.append(
                rs.BearingElement(
                    n=int(node),
                    kxx=float(kxx),
                    kyy=float(kyy),
                    kxy=float(kxy),
                    kyx=float(-kxy),
                    cxx=float(cxx),
                    cyy=float(cyy),
                )
            )
        except Exception as exc:
            self._errors.append(f"Erreur de création du palier : {exc}")
        return self

    def build(self):
        if self.errors:
            return None
        if not self.shaft_elements:
            self._errors.append("Aucun élément d'arbre défini.")
            return None
        if len(self.bearing_elements) < 2:
            self._errors.append("Au moins deux paliers sont recommandés pour ce modèle pédagogique.")
            return None
        try:
            return rs.Rotor(self.shaft_elements, self.disk_elements, self.bearing_elements)
        except Exception as exc:
            self._errors.append(f"Assemblage impossible : {exc}")
            return None


class SimulationEngine:
    """Exécution robuste des simulations ROSS."""

    def __init__(self, rotor: Any):
        self.rotor = rotor
        self._last_error = ""

    @property
    def last_error(self) -> str:
        return self._last_error

    def _guard(self) -> bool:
        if self.rotor is None:
            self._last_error = "Aucun rotor disponible."
            return False
        return True

    def run_modal(self, speed_rpm: float = 0.0):
        if not self._guard():
            return None
        try:
            return self.rotor.run_modal(speed=to_rad_per_sec_from_rpm(speed_rpm))
        except Exception as exc:
            self._last_error = str(exc)
            return None

    def run_campbell(self, speed_max_rpm: float = 8000.0, n_points: int = 100):
        if not self._guard():
            return None
        try:
            speeds = np.linspace(0.0, to_rad_per_sec_from_rpm(speed_max_rpm), int(n_points))
            return self.rotor.run_campbell(speeds)
        except Exception as exc:
            self._last_error = str(exc)
            return None

    def run_static(self):
        if not self._guard():
            return None
        try:
            return self.rotor.run_static()
        except Exception as exc:
            self._last_error = str(exc)
            return None

    def run_unbalance_response(
        self,
        node: int,
        magnitude: float,
        phase_rad: float,
        freq_max_hz: float,
        n_points: int = 500,
    ):
        if not self._guard():
            return None
        if magnitude <= 0:
            self._last_error = "La magnitude du balourd doit être > 0."
            return None
        if freq_max_hz <= 0:
            self._last_error = "La fréquence maximale doit être > 0."
            return None
        try:
            frequency_range = np.linspace(0.0, 2.0 * np.pi * float(freq_max_hz), int(n_points))
            return self.rotor.run_unbalance_response(
                node=[int(node)],
                magnitude=[float(magnitude)],
                phase=[float(phase_rad)],
                frequency_range=frequency_range,
            )
        except Exception as exc:
            self._last_error = str(exc)
            return None


class TPValidator:
    """Validation pédagogique des exercices."""

    def __init__(self, tp_id: str):
        self.tp_id = tp_id

    def check_parameters(self, user_params: Dict[str, Any]) -> Dict[str, List[str]]:
        results = {"passed": [], "warnings": [], "errors": []}

        if "n_elements" in user_params:
            n = int(user_params["n_elements"])
            if n < 2:
                results["errors"].append("Au moins 2 éléments d'arbre sont requis.")
            elif n > 20:
                results["warnings"].append("Beaucoup d'éléments : le calcul sera plus lent.")
            else:
                results["passed"].append(f"Nombre d'éléments valide ({n}).")

        positive_fields = {
            "od": "Le diamètre de l'arbre doit être positif.",
            "disk_od": "Le diamètre du disque doit être positif.",
            "disk_width": "La largeur du disque doit être positive.",
            "kxx": "Kxx doit être positif.",
            "kyy": "Kyy doit être positif.",
        }
        for field, message in positive_fields.items():
            if field in user_params and float(user_params[field]) <= 0:
                results["errors"].append(message)

        non_negative_fields = {
            "cxx": "Cxx doit être ≥ 0.",
            "cyy": "Cyy doit être ≥ 0.",
        }
        for field, message in non_negative_fields.items():
            if field in user_params and float(user_params[field]) < 0:
                results["errors"].append(message)

        if "kxx" in user_params and float(user_params["kxx"]) < 1e5:
            results["warnings"].append("Kxx très faible : palier très souple.")

        return results

    def verify_results(self, rotor: Any, modal: Any = None, tp_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        results = {"score": 0, "total": 0, "details": [], "passed": False, "percentage": 0.0}
        if rotor is None:
            results["details"].append(("❌", "Rotor non assemblé."))
            return results

        results["total"] += 1
        results["score"] += 1
        results["details"].append(("✅", f"Rotor assemblé — {len(rotor.nodes)} nœuds, masse {rotor.m:.2f} kg."))

        if tp_config and "validation" in tp_config:
            val = tp_config["validation"]
            if "expected_mass_min" in val and "expected_mass_max" in val:
                results["total"] += 1
                if val["expected_mass_min"] <= rotor.m <= val["expected_mass_max"]:
                    results["score"] += 1
                    results["details"].append(("✅", f"Masse dans la plage attendue : {rotor.m:.2f} kg."))
                else:
                    results["details"].append(
                        ("⚠️", f"Masse {rotor.m:.2f} kg hors plage [{val['expected_mass_min']}, {val['expected_mass_max']}].")
                    )

        if modal is not None and hasattr(modal, "wn") and len(modal.wn) > 0:
            fn = to_hz_from_rad_per_sec(np.asarray(modal.wn))
            results["total"] += 1
            if fn[0] > 0:
                results["score"] += 1
                results["details"].append(("✅", f"1ère fréquence propre : {fn[0]:.2f} Hz."))
            else:
                results["details"].append(("❌", "Fréquence propre nulle : vérifiez les paliers."))

            if hasattr(modal, "log_dec") and len(modal.log_dec) > 0:
                ld = np.asarray(modal.log_dec[:6], dtype=float)
                results["total"] += 1
                if np.all(ld >= 0.0):
                    results["score"] += 1
                    results["details"].append(("✅", f"Modes stables — Log Dec min = {ld.min():.4f}."))
                else:
                    unstable = [str(i + 1) for i, value in enumerate(ld) if value < 0]
                    results["details"].append(("❌", f"Modes instables détectés : {', '.join(unstable)}."))

        if results["total"] > 0:
            results["percentage"] = 100.0 * results["score"] / results["total"]
            results["passed"] = results["percentage"] >= 75.0
        return results

    @staticmethod
    def generate_feedback(validation_result: Dict[str, Any]) -> Tuple[str, str]:
        pct = float(validation_result.get("percentage", 0.0))
        if pct >= 90.0:
            return "✅", f"Excellent ! Score {pct:.0f}% — tous les critères sont validés."
        if pct >= 60.0:
            return "⚠️", f"Bon travail ! Score {pct:.0f}% — quelques points restent à améliorer."
        return "❌", f"Score {pct:.0f}% — revoyez les paramètres et les indices proposés."

    @staticmethod
    def award_badge(score: float) -> Optional[str]:
        if score >= 95.0:
            return "gold"
        if score >= 75.0:
            return "silver"
        if score >= 50.0:
            return "bronze"
        return None


class ReportGenerator:
    """Génération de rapports HTML et PDF réels."""

    def __init__(self, user_id: str = "Étudiant"):
        self.user_id = user_id
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    def generate_html(
        self,
        tp_id: str,
        params: Dict[str, Any],
        validation: Dict[str, Any],
        rotor: Any = None,
        modal: Any = None,
    ) -> str:
        rows = ""
        if modal is not None and hasattr(modal, "wn"):
            fn = to_hz_from_rad_per_sec(np.asarray(modal.wn))
            log_dec = np.asarray(getattr(modal, "log_dec", np.zeros_like(fn)), dtype=float)
            for idx, (freq, ld) in enumerate(zip(fn[:6], log_dec[:6]), start=1):
                color = "#22863A" if ld >= 0.1 else ("#F9A825" if ld > 0 else "#C00000")
                rows += (
                    f"<tr><td>{idx}</td><td>{freq:.3f}</td><td style='color:{color}'>{ld:.4f}</td></tr>"
                )

        params_rows = "".join(
            f"<tr><td>{key}</td><td>{value}</td></tr>" for key, value in params.items()
        )
        details_html = "".join(
            f"<li><b>{icon}</b> {message}</li>" for icon, message in validation.get("details", [])
        )
        score = float(validation.get("percentage", 0.0))
        score_color = "#22863A" if score >= 75.0 else ("#F9A825" if score >= 50.0 else "#C00000")

        return f"""
<!DOCTYPE html>
<html lang='fr'>
<head>
<meta charset='utf-8'>
<title>Rapport {tp_id}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; color: #222; }}
h1, h2, h3 {{ color: #1F5C8B; }}
.score {{ font-size: 1.6rem; color: {score_color}; font-weight: bold; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
th {{ background: #f0f4f8; }}
.badge {{ background: #eef6ff; padding: .4rem .6rem; border-radius: 6px; display:inline-block; }}
</style>
</head>
<body>
<h1>Rapport TP — {tp_id}</h1>
<p class='badge'>Généré par {APP_TITLE}</p>
<p><b>Étudiant :</b> {self.user_id}<br><b>Date :</b> {self.timestamp}</p>
<h2>Score de validation</h2>
<p class='score'>{score:.0f}%</p>
<h2>Critères détaillés</h2>
<ul>{details_html}</ul>
<h2>Paramètres utilisés</h2>
<table>
<tr><th>Paramètre</th><th>Valeur</th></tr>
{params_rows}
</table>
<h2>Fréquences propres</h2>
<table>
<tr><th>Mode</th><th>fn (Hz)</th><th>Log Dec</th></tr>
{rows if rows else '<tr><td colspan="3">Aucun résultat modal disponible.</td></tr>'}
</table>
<p><i>RotoPédago v5.1 — rapport pédagogique généré automatiquement.</i></p>
</body>
</html>
"""

    def generate_pdf_bytes(self, tp_id: str, params: Dict[str, Any], validation: Dict[str, Any], modal: Any = None) -> bytes:
        from io import BytesIO

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))

        story = [
            Paragraph(f"<b>Rapport TP — {tp_id}</b>", styles["Title"]),
            Spacer(1, 0.3 * cm),
            Paragraph(f"Étudiant : {self.user_id}", styles["Normal"]),
            Paragraph(f"Date : {self.timestamp}", styles["Normal"]),
            Spacer(1, 0.3 * cm),
            Paragraph("<b>Critères détaillés</b>", styles["Heading2"]),
        ]

        icon_map = {"✅": "OK", "⚠️": "ATTENTION", "❌": "ERREUR", "🥇": "OR", "🥈": "ARGENT", "🥉": "BRONZE"}
        for icon, message in validation.get("details", []):
            safe_icon = icon_map.get(str(icon), str(icon).encode("ascii", errors="ignore").decode("ascii"))
            safe_message = str(message).replace("✅", "OK").replace("⚠️", "ATTENTION").replace("❌", "ERREUR")
            story.append(Paragraph(f"{safe_icon} {safe_message}", styles["Small"]))

        story.extend([Spacer(1, 0.3 * cm), Paragraph("<b>Paramètres</b>", styles["Heading2"])])
        param_table = Table([["Paramètre", "Valeur"]] + [[str(k), str(v)] for k, v in params.items()], colWidths=[7 * cm, 8 * cm])
        param_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe9f4")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(param_table)

        if modal is not None and hasattr(modal, "wn"):
            fn = to_hz_from_rad_per_sec(np.asarray(modal.wn))
            ld = np.asarray(getattr(modal, "log_dec", np.zeros_like(fn)), dtype=float)
            story.extend([Spacer(1, 0.3 * cm), Paragraph("<b>Fréquences propres</b>", styles["Heading2"])])
            mode_rows = [["Mode", "fn (Hz)", "Log Dec"]]
            for idx, (f_val, ld_val) in enumerate(zip(fn[:6], ld[:6]), start=1):
                mode_rows.append([str(idx), f"{f_val:.3f}", f"{ld_val:.4f}"])
            mode_table = Table(mode_rows, colWidths=[2 * cm, 5 * cm, 5 * cm])
            mode_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe9f4")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(mode_table)

        doc.build(story)
        return buffer.getvalue()


# =============================================================================
# FONCTIONS D'AFFICHAGE ET D'ANALYSE
# =============================================================================
def badge_html(badge: Optional[str], tp_id: str) -> str:
    icons = {"gold": "🥇", "silver": "🥈", "bronze": "🥉"}
    labels = {"gold": "Or", "silver": "Argent", "bronze": "Bronze"}
    if badge in icons:
        return f"{icons[badge]} {tp_id} — {labels[badge]}"
    return ""


def modal_dataframe(modal: Any) -> pd.DataFrame:
    fn = to_hz_from_rad_per_sec(np.asarray(modal.wn))
    wd = to_hz_from_rad_per_sec(np.asarray(getattr(modal, "wd", modal.wn)))
    log_dec = np.asarray(getattr(modal, "log_dec", np.zeros_like(fn)), dtype=float)
    n = min(8, len(fn))
    return pd.DataFrame(
        {
            "Mode": np.arange(1, n + 1),
            "fn (Hz)": [f"{v:.3f}" for v in fn[:n]],
            "fd (Hz)": [f"{v:.3f}" for v in wd[:n]],
            "ωn (rad/s)": [f"{v:.3f}" for v in np.asarray(modal.wn)[:n]],
            "Log Dec": [f"{v:.4f}" for v in log_dec[:n]],
            "Stabilité": ["✅ Stable" if v >= 0 else "❌ Instable" for v in log_dec[:n]],
        }
    )


def build_standard_rotor(
    n_el: int,
    L: float,
    od: float,
    disk_node: int,
    disk_od: float,
    disk_w: float,
    kxx: float,
    cxx: float,
    kyy: Optional[float] = None,
    cyy: Optional[float] = None,
    kxy: float = 0.0,
    disk_id: float = 0.05,
):
    kyy = float(kxx if kyy is None else kyy)
    cyy = float(cxx if cyy is None else cyy)
    builder = RotorBuilder()
    builder.add_shaft(n_el, L, od)
    builder.add_disk(disk_node, disk_od, disk_w, id_=disk_id)
    builder.add_bearing(0, kxx, kyy, kxy=kxy, cxx=cxx, cyy=cyy)
    builder.add_bearing(n_el, kxx, kyy, kxy=kxy, cxx=cxx, cyy=cyy)
    return builder.build(), builder.errors


def show_builder_errors(errors: List[str]) -> None:
    for err in errors:
        st.error(err)


def render_homepage() -> None:
    st.markdown(
        f"""
## ⚙️ {APP_TITLE}

Application pédagogique de rotordynamique propulsée par **ROSS**.
"""
    )
    if not ROSS_AVAILABLE:
        st.warning("ROSS n'est pas disponible dans cet environnement. Les pages de simulation resteront accessibles mais les calculs seront désactivés.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
### 🎓 Mode TP
Parcours guidé en 3 niveaux progressifs.
- Feedback immédiat
- Validation pédagogique
- Badges de progression
"""
        )
    with col2:
        st.markdown(
            """
### 🏗️ Mode Libre
Construisez vos rotors personnalisés.
- Géométrie
- Modal / Campbell
- Statique et stabilité
"""
        )
    with col3:
        st.markdown(
            """
### 📚 Documentation
Références théoriques et bonnes pratiques.
- Théorie MEF
- API ROSS
- Critères pédagogiques API 684
"""
        )

    st.markdown("---")
    n_badges = len(state_get("badges", {}))
    total_tp = sum(len(level_data["tps"]) for level_data in TP_CATALOGUE.values())
    st.markdown(f"### 📊 Votre progression : {n_badges}/{total_tp} TP complétés")
    st.progress(n_badges / total_tp if total_tp > 0 else 0)
    if n_badges:
        for tp_id, badge in state_get("badges", {}).items():
            st.markdown(f"- {badge_html(badge, tp_id)}")
    else:
        st.info("Commencez par le Mode TP pour débloquer vos badges.")


def render_validation_block(tp_id: str, tp_cfg: Dict[str, Any], rotor: Any, modal: Any = None) -> Dict[str, Any]:
    validator = TPValidator(tp_id)
    validation = validator.verify_results(rotor, modal=modal, tp_config=tp_cfg)
    icon, message = validator.generate_feedback(validation)
    score = validation.get("percentage", 0.0)

    col_s, col_d = st.columns([1, 2])
    with col_s:
        st.metric("Score", f"{score:.0f}%")
        st.write(f"{icon} {message}")
    with col_d:
        st.markdown("**Détail des critères**")
        for det_icon, det_msg in validation.get("details", []):
            st.markdown(f"- {det_icon} {det_msg}")

    badge = validator.award_badge(score)
    if badge:
        badges = deepcopy(state_get("badges", {}))
        badges[tp_id] = badge
        state_set("badges", badges)
        st.success(f"Badge obtenu : {badge_html(badge, tp_id)}")

    return validation


def render_report_block(tp_id: str, tp_cfg: Dict[str, Any], rotor: Any = None, modal: Any = None) -> None:
    reporter = ReportGenerator(state_get("user_name", "Étudiant"))
    params_used = dict(tp_cfg.get("default_params", {}))
    if rotor is not None:
        params_used["Masse calculée (kg)"] = f"{rotor.m:.3f}"
        params_used["Nombre de nœuds"] = len(rotor.nodes)

    validator = TPValidator(tp_id)
    validation = validator.verify_results(rotor, modal=modal, tp_config=tp_cfg) if rotor is not None else {"details": [], "percentage": 0.0}

    col1, col2 = st.columns(2)
    with col1:
        html = reporter.generate_html(tp_id, params_used, validation, rotor=rotor, modal=modal)
        st.download_button(
            label="📥 Télécharger le rapport HTML",
            data=html.encode("utf-8"),
            file_name=f"Rapport_{tp_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            use_container_width=True,
        )
    with col2:
        pdf_bytes = reporter.generate_pdf_bytes(tp_id, params_used, validation, modal=modal)
        st.download_button(
            label="📄 Télécharger le rapport PDF",
            data=pdf_bytes,
            file_name=f"Rapport_{tp_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def plot_campbell_manual(camp: Any, speed_max_rpm: float, n_points: int) -> None:
    speeds_rpm = np.linspace(0.0, float(speed_max_rpm), int(n_points))
    fig = go.Figure()
    if hasattr(camp, "wd"):
        data = np.asarray(camp.wd)
    elif hasattr(camp, "wn"):
        data = np.asarray(camp.wn)
    else:
        st.warning("Données Campbell indisponibles.")
        return

    n_modes = min(6, data.shape[1] if data.ndim > 1 else 1)
    if data.ndim == 1:
        data = data[:, None]

    for i in range(n_modes):
        fig.add_trace(
            go.Scatter(
                x=speeds_rpm,
                y=to_hz_from_rad_per_sec(data[:, i]),
                mode="lines",
                name=f"Mode {i + 1}",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=speeds_rpm,
            y=speeds_rpm / 60.0,
            mode="lines",
            name="1X",
            line=dict(color="red", dash="dash"),
        )
    )
    fig.update_layout(title="Diagramme de Campbell", xaxis_title="Vitesse (RPM)", yaxis_title="Fréquence (Hz)")
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# INTERFACES TP
# =============================================================================
def tp11_interface(tp_cfg: Dict[str, Any]):
    d = tp_cfg["default_params"]
    validator = TPValidator("TP1.1")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Arbre**")
        n_el = st.slider("Nombre d'éléments", 2, 12, int(d["n_elements"]))
        L_el = st.number_input("Longueur d'un élément (m)", 0.05, 1.0, float(d["L_elem"]), 0.05)
        od = st.number_input("Diamètre extérieur (m)", 0.01, 0.30, float(d["od"]), 0.005)
    with col2:
        st.markdown("**Disque**")
        disk_n = st.slider("Nœud du disque", 0, n_el, min(int(d["disk_node"]), n_el))
        disk_od = st.number_input("Diamètre disque (m)", 0.05, 0.8, float(d["disk_od"]), 0.01)
        disk_w = st.number_input("Largeur disque (m)", 0.01, 0.30, float(d["disk_width"]), 0.01)
    with col3:
        st.markdown("**Paliers**")
        kxx = st.number_input("Kxx (N/m)", 1e4, 1e9, float(d["kxx"]), format="%.2e")
        cxx = st.number_input("Cxx (N·s/m)", 0.0, 10000.0, float(d["cxx"]))

    p_check = validator.check_parameters(
        {"n_elements": n_el, "od": od, "disk_od": disk_od, "disk_width": disk_w, "kxx": kxx, "cxx": cxx}
    )
    for item in p_check["errors"]:
        st.error(item)
    for item in p_check["warnings"]:
        st.warning(item)
    for item in p_check["passed"]:
        st.success(item)

    if st.button("🚀 Assembler et visualiser", key="btn_tp11"):
        if ross_required():
            with st.spinner("Assemblage du rotor..."):
                rotor, errors = build_standard_rotor(n_el, L_el, od, disk_n, disk_od, disk_w, kxx, cxx)
            show_builder_errors(errors)
            if rotor is not None:
                state_set("tp11_rotor", rotor)
                state_set("tp12_modal", None)
                st.success(f"Rotor assemblé avec succès — masse : {rotor.m:.2f} kg.")

    rotor = state_get("tp11_rotor")
    if rotor is not None:
        col_plot, col_info = st.columns([2, 1])
        with col_plot:
            fig = safe_plot(rotor, preferred_methods=["plot_rotor"]) if rotor is not None else None
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Visualisation géométrique indisponible pour cette version de ROSS.")
        with col_info:
            metric_card("Masse totale", f"{rotor.m:.2f} kg")
            metric_card("Nombre de nœuds", len(rotor.nodes))
            metric_card("Nombre d'éléments", len(rotor.shaft_elements) if hasattr(rotor, "shaft_elements") else n_el)
    return rotor, None


def tp12_interface(tp_cfg: Dict[str, Any]):
    rotor = state_get("tp11_rotor")
    if rotor is None:
        st.warning("Créez d'abord un rotor dans le TP1.1.")
        return None, None

    d = tp_cfg["default_params"]
    n_modes = st.slider("Nombre de modes à afficher", 2, 10, int(d["n_modes"]))
    speed_rpm = st.number_input("Vitesse de rotation (RPM)", 0.0, 20000.0, float(d["speed_rpm"]), 100.0)

    if st.button("🔬 Calculer les modes propres", key="btn_tp12"):
        if ross_required():
            with st.spinner("Calcul modal..."):
                engine = SimulationEngine(rotor)
                modal = engine.run_modal(speed_rpm=speed_rpm)
            if modal is not None:
                state_set("tp12_modal", modal)
                st.success("Analyse modale calculée avec succès.")
            else:
                st.error(f"Échec du calcul modal : {engine.last_error}")

    modal = state_get("tp12_modal")
    if modal is not None:
        st.dataframe(modal_dataframe(modal), use_container_width=True, hide_index=True)
        max_modes = min(n_modes, len(getattr(modal, "evalues", [])) // 2 if hasattr(modal, "evalues") else len(modal.wn))
        mode_idx = st.selectbox("Mode à visualiser", options=list(range(max(1, max_modes))), format_func=lambda x: f"Mode {x + 1}")
        fig = safe_plot(modal, mode=mode_idx)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Visualisation modale indisponible avec cette version de ROSS.")
    return rotor, modal


def tp21_interface(tp_cfg: Dict[str, Any]):
    d = tp_cfg["default_params"]
    col1, col2 = st.columns(2)
    with col1:
        kxx = st.number_input("Kxx (N/m)", 1e5, 1e9, float(d["kxx"]), format="%.2e")
        kyy = st.number_input("Kyy (N/m)", 1e5, 1e9, float(d["kyy"]), format="%.2e")
        metric_card("Ratio Kxx/Kyy", f"{kxx / kyy:.2f}")
    with col2:
        v_max = st.slider("Vitesse max (RPM)", 2000, 20000, int(d["speed_max_rpm"]))
        n_pts = st.slider("Résolution (points)", 50, 200, 100)

    if st.button("📊 Calculer le diagramme de Campbell", key="btn_tp21"):
        if ross_required():
            with st.spinner("Calcul Campbell..."):
                rotor, errors = build_standard_rotor(5, 0.2, 0.05, 2, 0.25, 0.07, kxx, d["cxx"], kyy=kyy, cyy=d["cyy"], kxy=d["kxy"])
                show_builder_errors(errors)
                if rotor is not None:
                    engine = SimulationEngine(rotor)
                    camp = engine.run_campbell(speed_max_rpm=v_max, n_points=n_pts)
                    if camp is not None:
                        state_set("tp21_rotor", rotor)
                        state_set("tp21_camp", camp)
                        st.success("Diagramme de Campbell calculé.")
                    else:
                        st.error(f"Échec du calcul Campbell : {engine.last_error}")

    rotor = state_get("tp21_rotor")
    camp = state_get("tp21_camp")
    if camp is not None:
        fig = safe_plot(camp, preferred_methods=["plot"])
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            plot_campbell_manual(camp, v_max, n_pts)

        st.markdown("#### ⚡ Estimation des vitesses critiques (approximation 1X)")
        try:
            modal0 = SimulationEngine(rotor).run_modal(0.0)
            if modal0 is not None:
                fn = to_hz_from_rad_per_sec(np.asarray(modal0.wn))
                crit_df = pd.DataFrame(
                    {
                        "Mode": np.arange(1, min(5, len(fn) + 1)),
                        "Fréquence (Hz)": [f"{value:.2f}" for value in fn[:4]],
                        "Vitesse critique approx. (RPM)": [f"{value * 60.0:.0f}" for value in fn[:4]],
                    }
                )
                st.dataframe(crit_df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.info(f"Vitesses critiques non disponibles : {exc}")
    return rotor, camp


def tp22_interface(tp_cfg: Dict[str, Any]):
    rotor = state_get("tp11_rotor")
    if rotor is None:
        st.warning("Créez d'abord un rotor dans le TP1.1.")
        return None, None, None

    d = tp_cfg["default_params"]
    col1, col2 = st.columns(2)
    with col1:
        max_node = max(0, len(rotor.nodes) - 1)
        unbal_node = st.slider("Nœud du balourd", 0, max_node, min(int(d["unbalance_node"]), max_node))
        magnitude = st.number_input("Magnitude balourd (kg·m)", 1e-6, 0.1, float(d["unbalance_magnitude"]), format="%.6f")
        phase_deg = st.slider("Phase (°)", 0, 360, int(d["unbalance_phase_deg"]))
    with col2:
        probe_node = st.slider("Nœud de mesure", 0, max_node, min(int(d["probe_node"]), max_node))
        freq_max_hz = st.slider("Fréquence maximale (Hz)", 10.0, 500.0, float(d["freq_max_hz"]), 5.0)

    if st.button("🌀 Calculer la réponse au balourd", key="btn_tp22"):
        if ross_required():
            with st.spinner("Calcul de la réponse au balourd..."):
                engine = SimulationEngine(rotor)
                modal = engine.run_modal(0.0)
                unbal = engine.run_unbalance_response(unbal_node, magnitude, np.deg2rad(phase_deg), freq_max_hz)
            if unbal is not None:
                state_set("tp22_modal", modal)
                state_set("tp22_unbal", unbal)
                st.success("Réponse au balourd calculée.")
            else:
                st.error(f"Échec du calcul : {engine.last_error}")

    modal = state_get("tp22_modal")
    unbal = state_get("tp22_unbal")
    if unbal is not None:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Magnitude (Bode)**")
            try:
                fig_mag = unbal.plot_magnitude(probe=[probe_node, 0])
                st.plotly_chart(fig_mag, use_container_width=True)
            except Exception as exc:
                st.warning(f"Magnitude indisponible : {exc}")
        with col_b:
            st.markdown("**Phase (Bode)**")
            try:
                fig_ph = unbal.plot_phase(probe=[probe_node, 0])
                st.plotly_chart(fig_ph, use_container_width=True)
            except Exception as exc:
                st.warning(f"Phase indisponible : {exc}")

        if modal is not None and hasattr(modal, "wn"):
            fn = to_hz_from_rad_per_sec(np.asarray(modal.wn))
            st.info(f"Première fréquence propre estimée : {fn[0]:.2f} Hz.")
    return rotor, modal, unbal


def tp31_interface(tp_cfg: Dict[str, Any]):
    d = tp_cfg["default_params"]
    kxy_max = st.slider("Kxy max (N/m)", int(1e5), int(1e7), int(d["kxy_max"]), step=int(1e5))
    v_max = st.slider("Vitesse max (RPM)", 1000, 10000, int(d["speed_max_rpm"]))
    kxy_val = st.slider("Kxy actuel (N/m)", 0, kxy_max, 0, step=max(1, int(kxy_max / 20)))

    if st.button("⚠️ Analyser la stabilité", key="btn_tp31"):
        if ross_required():
            with st.spinner("Analyse de stabilité..."):
                rotor, errors = build_standard_rotor(5, 0.2, 0.05, 2, 0.25, 0.07, 1e7, 1000.0, kyy=1e7, cyy=1000.0, kxy=kxy_val)
                show_builder_errors(errors)
                if rotor is not None:
                    state_set("tp31_rotor", rotor)
                    engine = SimulationEngine(rotor)
                    camp = engine.run_campbell(speed_max_rpm=v_max, n_points=50)
                    if camp is None:
                        st.error(f"Échec du calcul de stabilité : {engine.last_error}")
                    else:
                        fig = go.Figure()
                        if hasattr(camp, "log_dec"):
                            log_dec = np.asarray(camp.log_dec)
                            if log_dec.ndim == 1:
                                log_dec = log_dec[:, None]
                            for i in range(min(4, log_dec.shape[1])):
                                fig.add_trace(
                                    go.Scatter(
                                        x=np.linspace(0.0, float(v_max), log_dec.shape[0]),
                                        y=log_dec[:, i],
                                        mode="lines",
                                        name=f"Mode {i + 1}",
                                    )
                                )
                            fig.add_hline(y=0.0, line_dash="dash", line_color="red", annotation_text="Seuil d'instabilité")
                            fig.update_layout(title=f"Stabilité — Kxy = {kxy_val:.2e} N/m", xaxis_title="Vitesse (RPM)", yaxis_title="Log Décrément")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Le résultat Campbell ne fournit pas le Log Décrément.")

                        if kxy_val == 0:
                            st.success("Kxy = 0 : système stable dans ce cadre pédagogique.")
                        elif kxy_val < 0.5 * kxy_max:
                            st.warning("Kxy modéré : surveillez le Log Décrément.")
                        else:
                            st.error("Kxy élevé : risque d'instabilité accru.")

    return state_get("tp31_rotor")


def tp32_interface(tp_cfg: Dict[str, Any]):
    d = tp_cfg["default_params"]
    op_rpm = st.number_input("Vitesse opérationnelle (RPM)", 500.0, 10000.0, float(d["operating_rpm"]), 100.0)
    col1, col2 = st.columns(2)
    with col1:
        n_el = st.slider("Éléments d'arbre", 4, 12, int(d["n_elements"]))
        od = st.number_input("Diamètre arbre (m)", 0.02, 0.20, float(d["od"]), 0.005)
    with col2:
        kxx = st.number_input("Kxx paliers (N/m)", 1e5, 1e9, float(d["kxx"]), format="%.2e")
        cxx = st.number_input("Cxx paliers (N·s/m)", 0.0, 5000.0, float(d["cxx"]))

    if st.button("🏭 Lancer l'analyse complète API 684", key="btn_tp32"):
        if ross_required():
            with st.spinner("Analyse industrielle..."):
                rotor, errors = build_standard_rotor(
                    n_el, 0.3, od, n_el // 2, 0.40, 0.10, kxx, cxx, kyy=d["kyy"], cyy=d["cyy"]
                )
                show_builder_errors(errors)
                if rotor is not None:
                    engine = SimulationEngine(rotor)
                    modal = engine.run_modal(0.0)
                    camp = engine.run_campbell(speed_max_rpm=2.0 * op_rpm, n_points=100)
                    state_set("tp32_rotor", rotor)
                    state_set("tp32_modal", modal)
                    state_set("tp32_camp", camp)
                    st.success("Analyse complète terminée.")

    rotor = state_get("tp32_rotor")
    modal = state_get("tp32_modal")
    camp = state_get("tp32_camp")
    if rotor is not None and modal is not None:
        fn_rpm = to_hz_from_rad_per_sec(np.asarray(modal.wn)) * 60.0
        ld = np.asarray(getattr(modal, "log_dec", np.zeros_like(fn_rpm)), dtype=float)
        zone_low = 0.85 * op_rpm
        zone_high = 1.15 * op_rpm
        rows = []
        for idx, (speed_crit, ld_val) in enumerate(zip(fn_rpm[:4], ld[:4]), start=1):
            in_zone = zone_low <= speed_crit <= zone_high
            log_ok = ld_val >= 0.1
            rows.append(
                {
                    "Mode": idx,
                    "Fréq. critique (RPM)": f"{speed_crit:.0f}",
                    "Dans zone interdite": "❌ OUI" if in_zone else "✅ NON",
                    "Log Dec ≥ 0.1": "✅ OUI" if log_ok else "❌ NON",
                    "Conforme": "✅" if (not in_zone and log_ok) else "❌",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.info(f"Zone interdite pédagogique : [{zone_low:.0f} – {zone_high:.0f}] RPM")
        n_ok = sum(1 for row in rows if row["Conforme"] == "✅")
        score = 100.0 * n_ok / max(1, len(rows))
        metric_card("Score API 684 (pédagogique)", f"{score:.0f}%")
        if camp is not None:
            fig = safe_plot(camp, preferred_methods=["plot"])
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                plot_campbell_manual(camp, 2.0 * op_rpm, 100)
    return rotor, modal, camp


# =============================================================================
# MODE TP
# =============================================================================
def render_tp_mode() -> None:
    st.title("🎓 Mode TP — Parcours pédagogique")
    if not ross_required():
        st.info("Vous pouvez consulter la théorie et la documentation, mais les calculs resteront indisponibles tant que ROSS n'est pas installé.")

    level = st.sidebar.selectbox(
        "Niveau",
        options=list(TP_CATALOGUE.keys()),
        format_func=lambda x: f"Niveau {x} — {TP_CATALOGUE[x]['title'].split('—')[-1].strip()}",
    )
    lvl_data = TP_CATALOGUE[level]
    tp_ids = list(lvl_data["tps"].keys())
    tp_id = st.sidebar.radio(
        "Exercice",
        options=tp_ids,
        format_func=lambda x: f"{lvl_data['tps'][x]['icon']} {x} — {lvl_data['tps'][x]['title']}",
    )
    tp_cfg = lvl_data["tps"][tp_id]

    st.markdown(
        f"""
### {tp_cfg['icon']} {tp_id} — {tp_cfg['title']}
**Niveau {level}** · Durée estimée : {lvl_data['duration']}
"""
    )

    tab_th, tab_sim, tab_valid, tab_report = st.tabs(["📖 Théorie", "🔬 Simulation", "✅ Validation", "📄 Rapport"])

    with tab_th:
        st.markdown("### 🎯 Objectifs")
        for obj in tp_cfg["objectives"]:
            st.markdown(f"- {obj}")
        st.markdown("### 📐 Concepts théoriques")
        st.info(tp_cfg["theory"])
        st.markdown("### 💡 Indices")
        for hint in tp_cfg["hints"]:
            st.markdown(f"- {hint}")

    rotor = None
    modal = None
    with tab_sim:
        if tp_id == "TP1.1":
            rotor, modal = tp11_interface(tp_cfg)
        elif tp_id == "TP1.2":
            rotor, modal = tp12_interface(tp_cfg)
        elif tp_id == "TP2.1":
            rotor, _ = tp21_interface(tp_cfg)
        elif tp_id == "TP2.2":
            rotor, modal, _ = tp22_interface(tp_cfg)
        elif tp_id == "TP3.1":
            rotor = tp31_interface(tp_cfg)
        elif tp_id == "TP3.2":
            rotor, modal, _ = tp32_interface(tp_cfg)

    with tab_valid:
        st.subheader("Résultats de validation")
        if tp_id == "TP1.1":
            rotor = state_get("tp11_rotor")
            modal = None
        elif tp_id == "TP1.2":
            rotor = state_get("tp11_rotor")
            modal = state_get("tp12_modal")
        elif tp_id == "TP2.1":
            rotor = state_get("tp21_rotor")
            modal = SimulationEngine(rotor).run_modal(0.0) if rotor is not None and ROSS_AVAILABLE else None
        elif tp_id == "TP2.2":
            rotor = state_get("tp11_rotor")
            modal = state_get("tp22_modal")
        elif tp_id == "TP3.1":
            rotor = state_get("tp31_rotor")
            modal = SimulationEngine(rotor).run_modal(0.0) if rotor is not None and ROSS_AVAILABLE else None
        elif tp_id == "TP3.2":
            rotor = state_get("tp32_rotor")
            modal = state_get("tp32_modal")

        if rotor is None:
            st.warning("Lancez d'abord une simulation dans l'onglet correspondant.")
        else:
            render_validation_block(tp_id, tp_cfg, rotor, modal=modal)

    with tab_report:
        st.subheader("Exporter le travail")
        if tp_id == "TP1.1":
            rotor = state_get("tp11_rotor")
            modal = None
        elif tp_id == "TP1.2":
            rotor = state_get("tp11_rotor")
            modal = state_get("tp12_modal")
        elif tp_id == "TP2.1":
            rotor = state_get("tp21_rotor")
            modal = SimulationEngine(rotor).run_modal(0.0) if rotor is not None and ROSS_AVAILABLE else None
        elif tp_id == "TP2.2":
            rotor = state_get("tp11_rotor")
            modal = state_get("tp22_modal")
        elif tp_id == "TP3.1":
            rotor = state_get("tp31_rotor")
            modal = SimulationEngine(rotor).run_modal(0.0) if rotor is not None and ROSS_AVAILABLE else None
        else:
            rotor = state_get("tp32_rotor")
            modal = state_get("tp32_modal")

        render_report_block(tp_id, tp_cfg, rotor=rotor, modal=modal)


# =============================================================================
# MODE LIBRE
# =============================================================================
def render_free_mode() -> None:
    st.title("🏗️ Mode Libre — Simulation personnalisée")
    if not ross_required():
        st.info("La construction et les calculs nécessitent ROSS.")
        return

    presets = {
        "Roulement à billes": {"kxx": 1e7, "kyy": 1e7, "kxy": 0.0, "cxx": 500.0, "cyy": 500.0},
        "Palier lisse (hydrodynamique)": {"kxx": 1e7, "kyy": 5e6, "kxy": 2e6, "cxx": 2000.0, "cyy": 2000.0},
        "Support souple": {"kxx": 1e6, "kyy": 1e6, "kxy": 0.0, "cxx": 5000.0, "cyy": 5000.0},
    }
    preset_name = st.selectbox("Preset de paliers", list(presets.keys()))
    p = presets[preset_name]

    col1, col2, col3 = st.columns([1.1, 1.0, 1.25])
    with col1:
        st.subheader("🔩 Arbre")
        shaft_df = pd.DataFrame([{"L (m)": 0.2, "id (m)": 0.0, "od (m)": 0.05} for _ in range(5)])
        shaft_edit = st.data_editor(shaft_df, num_rows="dynamic", key="free_shaft")
    with col2:
        st.subheader("💿 Disques")
        disk_df = pd.DataFrame([{"nœud": 2, "id (m)": 0.05, "od (m)": 0.25, "largeur (m)": 0.07}])
        disk_edit = st.data_editor(disk_df, num_rows="dynamic", key="free_disk")
    with col3:
        st.subheader("🔗 Paliers")
        last_node = max(0, len(shaft_edit))
        bear_df = pd.DataFrame(
            [
                {"nœud": 0, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"], "cyy": p["cyy"]},
                {"nœud": last_node, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"], "cyy": p["cyy"]},
            ]
        )
        bear_edit = st.data_editor(bear_df, num_rows="dynamic", key="free_bear")

    if st.button("🚀 Construire et analyser", type="primary"):
        try:
            material = get_material()
            shaft = [
                rs.ShaftElement(L=float(row["L (m)"]), idl=float(row["id (m)"]), odl=float(row["od (m)"]), material=material)
                for _, row in shaft_edit.iterrows()
            ]
            n_nodes = len(shaft)
            disks = [
                rs.DiskElement.from_geometry(
                    n=int(row["nœud"]),
                    material=material,
                    width=float(row["largeur (m)"]),
                    i_d=float(row["id (m)"]),
                    o_d=float(row["od (m)"]),
                )
                for _, row in disk_edit.iterrows()
            ]
            bearings = []
            for _, row in bear_edit.iterrows():
                node = int(row["nœud"])
                if node < 0 or node > n_nodes:
                    raise ValueError(f"Nœud de palier invalide : {node}.")
                bearings.append(
                    rs.BearingElement(
                        n=node,
                        kxx=float(row["kxx"]),
                        kyy=float(row["kyy"]),
                        kxy=float(row["kxy"]),
                        kyx=float(-row["kxy"]),
                        cxx=float(row["cxx"]),
                        cyy=float(row["cyy"]),
                    )
                )
            rotor = rs.Rotor(shaft, disks, bearings)
            state_set("free_rotor", rotor)
            state_set("free_modal", None)
            state_set("free_camp", None)
            st.success(f"Rotor construit — {len(rotor.nodes)} nœuds, masse {rotor.m:.2f} kg.")
        except Exception as exc:
            state_set("free_rotor", None)
            st.error(f"Erreur d'assemblage : {exc}")

    rotor = state_get("free_rotor")
    tabs = st.tabs(["🏗️ Géométrie", "📊 Modal", "📈 Campbell", "📉 Stabilité", "📏 Statique"])

    with tabs[0]:
        if rotor is None:
            st.info("Construisez d'abord un rotor.")
        else:
            fig = safe_plot(rotor, preferred_methods=["plot_rotor"])
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Visualisation géométrique indisponible.")

    with tabs[1]:
        if rotor is None:
            st.warning("Veuillez d'abord construire le rotor.")
        else:
            speed_rpm = st.number_input("Vitesse de rotation pour l'analyse modale (RPM)", 0.0, 20000.0, 0.0, 100.0, key="free_modal_speed")
            if st.button("Calculer les modes", key="free_modal_btn"):
                engine = SimulationEngine(rotor)
                modal = engine.run_modal(speed_rpm)
                if modal is not None:
                    state_set("free_modal", modal)
                else:
                    st.error(f"Échec du calcul modal : {engine.last_error}")
            modal = state_get("free_modal")
            if modal is not None:
                st.dataframe(modal_dataframe(modal), use_container_width=True, hide_index=True)
                max_modes = min(6, len(getattr(modal, "evalues", [])) // 2 if hasattr(modal, "evalues") else len(modal.wn))
                mode_i = st.selectbox("Sélection du mode", list(range(max(1, max_modes))), format_func=lambda x: f"Mode {x + 1}")
                fig_modal = safe_plot(modal, mode=mode_i)
                if fig_modal is not None:
                    st.plotly_chart(fig_modal, use_container_width=True)
                else:
                    st.info("Déformée modale indisponible.")

    with tabs[2]:
        if rotor is None:
            st.warning("Veuillez d'abord construire le rotor.")
        else:
            v_max = st.slider("Vitesse max (RPM)", 1000, 20000, 8000, key="free_camp_vmax")
            if st.button("Calculer Campbell", key="free_camp_btn"):
                engine = SimulationEngine(rotor)
                camp = engine.run_campbell(v_max, 100)
                if camp is not None:
                    state_set("free_camp", camp)
                else:
                    st.error(f"Échec du Campbell : {engine.last_error}")
            camp = state_get("free_camp")
            if camp is not None:
                fig = safe_plot(camp, preferred_methods=["plot"])
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    plot_campbell_manual(camp, v_max, 100)

    with tabs[3]:
        camp = state_get("free_camp")
        if camp is None:
            st.info("Calculez d'abord le Campbell pour accéder à la stabilité.")
        else:
            st.info("Log Dec < 0 = instabilité. Log Dec ≥ 0.1 = bonne stabilité pédagogique.")
            if hasattr(camp, "log_dec"):
                fig_s = go.Figure()
                log_dec = np.asarray(camp.log_dec)
                if log_dec.ndim == 1:
                    log_dec = log_dec[:, None]
                v_max = st.session_state.get("free_camp_vmax", 8000)
                for i in range(min(6, log_dec.shape[1])):
                    fig_s.add_trace(go.Scatter(x=np.linspace(0.0, float(v_max), log_dec.shape[0]), y=log_dec[:, i], mode="lines", name=f"Mode {i + 1}"))
                fig_s.add_hline(y=0.0, line_dash="dash", line_color="red")
                fig_s.add_hline(y=0.1, line_dash="dot", line_color="orange", annotation_text="Seuil pédagogique (0.1)")
                fig_s.update_layout(xaxis_title="Vitesse (RPM)", yaxis_title="Log Décrément")
                st.plotly_chart(fig_s, use_container_width=True)
            else:
                st.warning("Données de stabilité indisponibles.")

    with tabs[4]:
        if rotor is None:
            st.warning("Veuillez d'abord construire le rotor.")
        else:
            if st.button("Analyse statique", key="free_static_btn"):
                engine = SimulationEngine(rotor)
                static = engine.run_static()
                if static is not None:
                    fig_static = safe_plot(static)
                    if fig_static is not None:
                        st.plotly_chart(fig_static, use_container_width=True)
                    else:
                        st.info("Visualisation statique indisponible.")
                else:
                    st.error(f"Analyse statique impossible : {engine.last_error}")


# =============================================================================
# DOCUMENTATION
# =============================================================================
def render_documentation() -> None:
    st.title("📚 Documentation & Références pédagogiques")
    tab1, tab2, tab3, tab4 = st.tabs(["🔬 Théorie", "🛠️ API ROSS", "📏 Critères", "💻 Exemple"])

    with tab1:
        st.markdown(
            """
## Fondements théoriques

### Modèle de poutre de Timoshenko
L'arbre est discrétisé en éléments de poutre intégrant les effets de cisaillement transverse
et d'inertie rotatoire.

### Équation du mouvement
"""
        )
        st.latex(r"M\ddot{q} + (C + G)\dot{q} + Kq = F(t)")
        st.markdown(
            """
- **M** : matrice de masse
- **C** : matrice d'amortissement
- **G** : matrice gyroscopique
- **K** : matrice de rigidité

### Décrément logarithmique
"""
        )
        st.latex(r"\delta = \frac{2\pi\xi}{\sqrt{1-\xi^2}}")

    with tab2:
        st.markdown(
            """
## Méthodes principales de ROSS
- `run_static()` : déflexion statique
- `run_modal(speed)` : fréquences propres, amortissement, stabilité
- `run_campbell(speeds)` : évolution des fréquences avec la vitesse
- `run_unbalance_response(...)` : réponse au balourd
"""
        )

    with tab3:
        st.markdown(
            """
## Critères pédagogiques inspirés de l'API 684
1. Éviter les vitesses critiques dans la zone d'exploitation ±15 %.
2. Viser un **Log Dec ≥ 0.1** dans la plage utile.
3. Documenter les hypothèses et les marges de sécurité.
"""
        )

    with tab4:
        st.code(
            """import ross as rs
import numpy as np

steel = rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9)
shaft = [rs.ShaftElement(L=0.2, idl=0.0, odl=0.05, material=steel) for _ in range(5)]
disk = rs.DiskElement.from_geometry(n=2, material=steel, width=0.07, i_d=0.05, o_d=0.25)
b0 = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, kxy=0.0, kyx=0.0, cxx=500.0, cyy=500.0)
b1 = rs.BearingElement(n=5, kxx=1e7, kyy=1e7, kxy=0.0, kyx=0.0, cxx=500.0, cyy=500.0)
rotor = rs.Rotor(shaft, [disk], [b0, b1])
modal = rotor.run_modal(speed=0.0)
print(modal.wn[:4] / (2 * np.pi))""",
            language="python",
        )


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    init_session_state()

    st.sidebar.title("⚙️ RotoPédago v5.1")
    st.sidebar.markdown("---")
    state_set("user_name", st.sidebar.text_input("👤 Votre nom", value=state_get("user_name", "Étudiant")))
    page = st.sidebar.radio("Navigation", ["🏠 Accueil", "🎓 Mode TP", "🏗️ Mode Libre", "📚 Documentation"])

    if state_get("badges"):
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🏅 Mes badges**")
        for tp_id, badge in state_get("badges", {}).items():
            st.sidebar.markdown(f"- {badge_html(badge, tp_id)}")

    st.sidebar.markdown("---")
    if ROSS_AVAILABLE:
        st.sidebar.success("✅ ROSS opérationnel")
    else:
        st.sidebar.error("❌ ROSS non installé")
    st.sidebar.caption("RotoPédago v5.1 — version fiabilisée")

    if page == "🏠 Accueil":
        render_homepage()
    elif page == "🎓 Mode TP":
        render_tp_mode()
    elif page == "🏗️ Mode Libre":
        render_free_mode()
    elif page == "📚 Documentation":
        render_documentation()


if __name__ == "__main__":
    main()
