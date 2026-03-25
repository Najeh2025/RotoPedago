# =============================================================================
# RotoPédago v5.0 — Application Streamlit complète (ROSS)
# Version améliorée avec Frequency Response et Unbalance Response complets
# =============================================================================

# =============================================================================
# IMPORTS
# =============================================================================
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import io
import json
import traceback

try:
    import ross as rs
    ROSS_AVAILABLE = True
    ROSS_VERSION = rs.__version__
except ImportError:
    ROSS_AVAILABLE = False
    ROSS_VERSION = "Non installé"

def safe_plot(obj, preferred_methods=['plot_mode_3d', 'plot_deflected_shape', 
                                      'plot_deformation', 'plot'], **kwargs):
    """Fonction bouclier pour empêcher les erreurs AttributeError"""
    for method in preferred_methods:
        if hasattr(obj, method):
            try:
                fig = getattr(obj, method)(**kwargs)
                if fig is not None:
                    return fig
            except:
                continue
    return None

# =============================================================================
# CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="RotoPédago v5.0",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* --- Global --- */
.stTabs [data-baseweb="tab-list"] { gap: 12px; }
.stTabs [data-baseweb="tab"] { height: 46px; font-weight: 600; font-size: 13px; border-radius: 8px 8px 0 0; }
/* --- Badges --- */
.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700; margin:2px; }
.badge-gold   { background:#FFD700; color:#7A5700; }
.badge-silver { background:#C0C0C0; color:#3A3A3A; }
.badge-bronze { background:#CD7F32; color:#fff; }
/* --- TP Cards --- */
.tp-card { background:#F0F4FF; border-left:5px solid #1F5C8B; border-radius:8px;
padding:16px 20px; margin:10px 0; }
.tp-card-done { background:#F0FFF4; border-left:5px solid #22863A; }
/* --- Status boxes --- */
.status-ok   { background:#E6FFE6; border:1px solid #22863A; border-radius:6px; padding:8px 14px; }
.status-warn { background:#FFF8E1; border:1px solid #F9A825; border-radius:6px; padding:8px 14px; }
.status-err  { background:#FFE6E6; border:1px solid #C00000; border-radius:6px; padding:8px 14px; }
/* --- Progress bar custom --- */
div[data-testid="stProgress"] > div > div { background:#1F5C8B; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DONNÉES TP — Catalogue complet
# =============================================================================
TP_CATALOGUE = {
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
                    "Définir deux paliers aux extrémités"
                ],
                "theory": (
                    "Un rotor se compose d'un **arbre** (modélisé par des éléments de poutre de Timoshenko), "
                    "de **disques** rigides (masses et inerties concentrées) et de **paliers** (ressorts et amortisseurs). "
                    "L'assemblage de ces trois composants via la MEF produit les matrices globales de masse, rigidité et amortissement."
                ),
                "default_params": {
                    "n_elements": 5, "L_elem": 0.2, "od": 0.05,
                    "disk_node": 2, "disk_od": 0.25, "disk_width": 0.07,
                    "kxx": 1e7, "cxx": 500
                },
                "validation": {
                    "check_assembly": True,
                    "expected_nodes_min": 4,
                    "expected_mass_min": 5.0,
                    "expected_mass_max": 200.0
                },
                "hints": [
                    "Utilisez n_elements=5 pour commencer",
                    "La masse totale doit être entre 5 et 200 kg",
                    "Les nœuds sont numérotés de 0 à n_elements"
                ]
            },
            "TP1.2": {
                "title": "Modes propres et déformées",
                "icon": "📊",
                "objectives": [
                    "Calculer les fréquences naturelles (run_modal)",
                    "Afficher le tableau wn / wd / Log Dec",
                    "Visualiser la déformée du 1er mode"
                ],
                "theory": (
                    "L'analyse modale résout le problème aux valeurs propres **det(K - ω²M) = 0**. "
                    "Pour un rotor, les valeurs propres sont complexes : la partie réelle donne l'amortissement, "
                    "la partie imaginaire la fréquence amortie ω_d. Le **décrément logarithmique** "
                    "δ = 2π·ξ/√(1-ξ²) quantifie l'amortissement de chaque mode."
                ),
                "default_params": {"n_modes": 6, "speed_rpm": 0},
                "validation": {
                    "check_natural_frequencies": True,
                    "fn1_min": 5.0, "fn1_max": 500.0,
                    "log_dec_positive": True,
                    "tolerance": 0.01
                },
                "hints": [
                    "run_modal(speed=0) calcule les modes à l'arrêt",
                    "modal.wn donne les fréquences en rad/s",
                    "Un Log Dec > 0 indique un mode stable"
                ]
            }
        }
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
                    "Définir des raideurs directionnelles Kxx ≠ Kyy",
                    "Tracer le diagramme de Campbell",
                    "Identifier les vitesses critiques (intersections 1X)"
                ],
                "theory": (
                    "Un palier **anisotrope** (Kxx ≠ Kyy) lève la dégénérescence des modes : les fréquences "
                    "de précession avant et arrière se séparent. Le **diagramme de Campbell** trace ces fréquences "
                    "vs la vitesse de rotation. Les **vitesses critiques** sont les intersections avec les droites "
                    "nX (synchrones). La norme API 684 impose une marge de séparation ≥ 15%."
                ),
                "default_params": {
                    "kxx": 1e7, "kyy": 5e6, "kxy": 0, "speed_max_rpm": 8000
                },
                "validation": {
                    "check_critical_speeds": True,
                    "anisotropy_ratio_min": 1.5,
                    "stability_margin": 0.15
                },
                "hints": [
                    "Kxx / Kyy > 1.5 pour observer la séparation des modes",
                    "Les intersections avec la droite 1X sont les vitesses critiques",
                    "La marge API = (Nc_suivante - Nc) / Nc × 100%"
                ]
            },
            "TP2.2": {
                "title": "Réponse au balourd",
                "icon": "🌀",
                "objectives": [
                    "Définir un balourd (masse × rayon = kg·m)",
                    "Calculer la réponse fréquentielle (run_unbalance_response)",
                    "Identifier le DAF (Dynamic Amplification Factor)"
                ],
                "theory": (
                    "Un **balourd** est un déséquilibre de masse qui génère une force tournante F = m·e·ω². "
                    "La réponse au balourd est calculée dans le domaine fréquentiel via la résolution de "
                    "(K + jωC - ω²M)·q = F_unbalance. Le **DAF** mesure l'amplification à la résonance "
                    "par rapport au déplacement statique. Pour un système amorti : DAF = 1/(2·ξ)."
                ),
                "default_params": {
                    "unbalance_node": 2, "unbalance_magnitude": 0.001,
                    "unbalance_phase": 0.0, "probe_node": 2,
                    "freq_min": 0, "freq_max": 5000
                },
                "validation": {
                    "check_peak_amplitude": True,
                    "frequency_range": (0, 5000),
                    "daf_reasonable_min": 1.0
                },
                "hints": [
                    "Balourd = masse résiduelle × rayon d'excentricité (ex: 1g × 1m = 0.001 kg·m)",
                    "Le pic d'amplitude coïncide avec la 1ère vitesse critique du Campbell",
                    "DAF = Amplitude_max / Déplacement_statique"
                ]
            },
            "TP2.3": {
                "title": "Réponse Fréquentielle (FRF)",
                "icon": "📉",
                "objectives": [
                    "Appliquer une force harmonique externe",
                    "Calculer la FRF avec run_freq_response",
                    "Analyser les diagrammes de Bode"
                ],
                "theory": (
                    "La **réponse fréquentielle** (FRF) caractérise la réponse du rotor à une excitation "
                    "harmonique externe F(ω) = F₀·e^(jωt). Contrairement au balourd (force tournante), "
                    "la FRF permet d'étudier la réponse à des forces dans des directions fixes. "
                    "Les diagrammes de **Bode** montrent le gain et la phase en fonction de la fréquence."
                ),
                "default_params": {
                    "force_node": 2, "force_magnitude": 100.0,
                    "force_direction": "x", "freq_min": 0, "freq_max": 5000
                },
                "validation": {
                    "check_frf_peaks": True,
                    "frequency_range": (0, 5000),
                    "phase_continuity": True
                },
                "hints": [
                    "La FRF révèle les mêmes résonances que le balourd",
                    "La phase tourne de 180° à chaque résonance",
                    "Comparez FRF et réponse au balourd pour valider"
                ]
            }
        }
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
                    "Comprendre le rôle de Kxy dans les paliers hydrodynamiques",
                    "Observer la transition stable → instable (Log Dec < 0)",
                    "Identifier le seuil critique de Kxy"
                ],
                "theory": (
                    "La **raideur croisée** Kxy (et kyx = -kxy) est générée par le film d'huile dans les paliers "
                    "hydrodynamiques. Elle crée un couplage entre les directions X et Y qui peut déstabiliser "
                    "le mode de précession avant. L'instabilité apparaît quand le **décrément logarithmique** "
                    "d'un mode devient négatif : l'amplitude croît exponentiellement → défaillance catastrophique."
                ),
                "default_params": {
                    "kxy_max": 1e7, "speed_max_rpm": 5000
                },
                "validation": {
                    "check_instability_threshold": True,
                    "log_dec_sign_change": True
                },
                "hints": [
                    "Augmentez Kxy progressivement : regardez le Log Dec du Mode 1",
                    "L'instabilité apparaît quand Log Dec < 0",
                    "Le seuil Kxy_critique dépend de la vitesse de rotation"
                ]
            },
            "TP3.2": {
                "title": "Cas industriel complet",
                "icon": "🏭",
                "objectives": [
                    "Modéliser un compresseur centrifuge industriel",
                    "Vérifier la conformité API 684 (marges vitesses critiques)",
                    "Générer un rapport d'analyse complet"
                ],
                "theory": (
                    "La norme **API 684** définit les exigences rotordynamiques pour les turbomachines industrielles. "
                    "Elle impose : (1) aucune vitesse critique dans la plage opérationnelle ±10%, "
                    "(2) marge de séparation ≥ 15% entre vitesses critiques adjacentes, "
                    "(3) Log Dec ≥ 0.1 pour tous les modes dans la plage de fonctionnement, "
                    "(4) réponse au balourd < limites ISO 7919."
                ),
                "default_params": {
                    "operating_rpm": 3000,
                    "n_elements": 8,
                    "n_disks": 2
                },
                "validation": {
                    "check_all_constraints": True,
                    "api684_margin": 0.15,
                    "min_log_dec": 0.1,
                    "performance_score": 0.85
                },
                "hints": [
                    "La plage interdite API = [0.85×N_op, 1.15×N_op]",
                    "Log Dec ≥ 0.1 requis pour tous les modes",
                    "Score = (critères validés) / (total critères) × 100%"
                ]
            }
        }
    }
}

# Module-level cache for non-serializable ROSS objects
_CACHE: dict = {}

# Matériau standard
MAT_STEEL = None
if ROSS_AVAILABLE:
    MAT_STEEL = rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9)

# =============================================================================
# CLASSE 1 : RotorBuilder
# =============================================================================
class RotorBuilder:
    """Constructeur de rotors ROSS avec validation intégrée."""
    
    def __init__(self):
        self.shaft_elements: List = []
        self.disk_elements: List = []
        self.bearing_elements: List = []
        self.material = MAT_STEEL
        self._errors: List[str] = []
    
    def add_shaft(self, n_elements: int, L: float, od: float, id_: float = 0.0) -> "RotorBuilder":
        """Ajoute des éléments d'arbre uniformes."""
        self._errors.clear()
        if not ROSS_AVAILABLE:
            self._errors.append("ROSS non disponible.")
            return self
        try:
            self.shaft_elements = [
                rs.ShaftElement(L=L, idl=id_, odl=od, material=self.material)
                for _ in range(n_elements)
            ]
        except Exception as e:
            self._errors.append(f"Erreur arbre : {e}")
        return self
    
    def add_disk(self, node: int, od: float, width: float, id_: float = 0.05) -> "RotorBuilder":
        """Ajoute un disque à un nœud."""
        if not ROSS_AVAILABLE:
            return self
        n_nodes = len(self.shaft_elements) + 1
        if node < 0 or node >= n_nodes:
            self._errors.append(
                f"❌ Nœud disque {node} invalide — l'arbre a {n_nodes} nœuds (0 → {n_nodes-1})."
            )
            return self
        try:
            self.disk_elements.append(
                rs.DiskElement.from_geometry(
                    n=node, material=self.material,
                    width=width, i_d=id_, o_d=od
                )
            )
        except Exception as e:
            self._errors.append(f"Erreur disque : {e}")
        return self
    
    def add_bearing(self, node: int, kxx: float, kyy: float,
                    kxy: float = 0.0, cxx: float = 500.0, cyy: float = 500.0) -> "RotorBuilder":
        """Ajoute un palier à un nœud."""
        if not ROSS_AVAILABLE:
            return self
        n_nodes = len(self.shaft_elements) + 1
        if node < 0 or node >= n_nodes:
            self._errors.append(
                f"❌ Nœud palier {node} invalide — l'arbre a {n_nodes} nœuds (0 → {n_nodes-1})."
            )
            return self
        try:
            self.bearing_elements.append(
                rs.BearingElement(
                    n=node, kxx=kxx, kyy=kyy,
                    kxy=kxy, kyx=-kxy,
                    cxx=cxx, cyy=cyy
                )
            )
        except Exception as e:
            self._errors.append(f"Erreur palier : {e}")
        return self
    
    def build(self) -> Optional[object]:
        """Assemble le rotor ROSS. Retourne None si erreurs."""
        if self._errors:
            return None
        if not self.shaft_elements:
            self._errors.append("❌ Aucun élément d'arbre défini.")
            return None
        if not self.bearing_elements:
            self._errors.append("❌ Aucun palier défini.")
            return None
        try:
            rotor = rs.Rotor(self.shaft_elements, self.disk_elements, self.bearing_elements)
            return rotor
        except Exception as e:
            self._errors.append(f"❌ Assemblage impossible : {e}")
            return None
    
    @property
    def errors(self) -> List[str]:
        return self._errors
    
    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0

# =============================================================================
# CLASSE 2 : SimulationEngine (ENHANCED)
# =============================================================================
class SimulationEngine:
    """Moteur de simulation ROSS avec cache et gestion d'erreurs améliorée."""
    
    def __init__(self, rotor):
        self.rotor = rotor
        self._last_error: str = ""
    
    @st.cache_data(show_spinner=False)
    def _run_modal_cached(_self, rotor_hash: str, speed: float):
        return _self.rotor.run_modal(speed=speed)
    
    def run_modal(self, speed_rpm: float = 0.0) -> Optional[object]:
        """Calcule l'analyse modale."""
        speed_rad = speed_rpm * np.pi / 30
        try:
            return self.rotor.run_modal(speed=speed_rad)
        except Exception as e:
            self._last_error = f"Erreur modale : {str(e)}"
            return None
    
    def run_campbell(self, speed_max_rpm: float = 8000, n_points: int = 100) -> Optional[object]:
        """Calcule le diagramme de Campbell."""
        try:
            speeds = np.linspace(0, speed_max_rpm * np.pi / 30, n_points)
            return self.rotor.run_campbell(speeds)
        except Exception as e:
            self._last_error = f"Erreur Campbell : {str(e)}"
            return None
    
    def run_static(self) -> Optional[object]:
        """Calcule la déflexion statique."""
        try:
            return self.rotor.run_static()
        except Exception as e:
            self._last_error = f"Erreur statique : {str(e)}"
            return None
    
    def run_unbalance_response(self, node: int, magnitude: float,
                                phase: float, freq_max: float) -> Optional[object]:
        """
        Calcule la réponse au balourd.
        Compatible avec ROSS >= 0.3.0
        """
        try:
            # Création du vecteur de fréquences
            frequency = np.linspace(0, freq_max, 500)
            
            # Méthode 1: Essayer avec les paramètres directs (ROSS récent)
            try:
                return self.rotor.run_unbalance_response(
                    node=[node],
                    magnitude=[magnitude],
                    phase=[phase],
                    frequency=frequency
                )
            except TypeError:
                # Méthode 2: Ancienne API ROSS
                return self.rotor.run_unbalance_response(
                    node=node,
                    unbalance_magnitude=magnitude,
                    unbalance_phase=phase,
                    frequency=frequency
                )
        except Exception as e:
            self._last_error = f"Erreur réponse balourd : {str(e)}"
            return None
    
    def run_freq_response(self, node: int, force_magnitude: float,
                          force_direction: str = 'x', freq_min: float = 0,
                          freq_max: float = 5000) -> Optional[object]:
        """
        Calcule la réponse fréquentielle (FRF) à une force harmonique.
        ROSS utilise run_forced_response pour cela.
        """
        try:
            frequency_range = np.linspace(freq_min, freq_max, 500)
            
            # Création du vecteur de force
            # Dans ROSS, on utilise un tableau de forces complexes
            if force_direction.lower() == 'x':
                dof = 0  # DDL translation X
            else:
                dof = 1  # DDL translation Y
            
            # Force harmonique F = F0 * e^(j*omega*t)
            forces = np.zeros((self.rotor.model_size, len(frequency_range)), dtype=complex)
            forces[dof, :] = force_magnitude
            
            return self.rotor.run_freq_response(
                frequency=frequency_range,
                forces=forces
            )
        except Exception as e:
            self._last_error = f"Erreur réponse fréquentielle : {str(e)}"
            return None
    
    def run_critical_speed(self) -> Optional[object]:
        """Calcule les vitesses critiques du rotor."""
        try:
            return self.rotor.run_critical_speed()
        except Exception as e:
            self._last_error = f"Erreur vitesses critiques : {str(e)}"
            return None
    
    @property
    def last_error(self) -> str:
        return self._last_error

# =============================================================================
# CLASSE 3 : TPValidator
# =============================================================================
class TPValidator:
    """Système de validation des exercices TP avec feedback contextuel."""
    
    def __init__(self, tp_id: str):
        self.tp_id = tp_id
        self.criteria = TP_CATALOGUE
    
    def check_parameters(self, user_params: dict) -> dict:
        """Vérifie les paramètres d'entrée."""
        results = {"passed": [], "warnings": [], "errors": []}
        
        if "kxx" in user_params and user_params["kxx"] <= 0:
            results["errors"].append("Kxx doit être positif (raideur de palier)")
        if "kxx" in user_params and user_params["kxx"] < 1e5:
            results["warnings"].append("Kxx très faible — palier très souple")
        
        if "n_elements" in user_params:
            n = user_params["n_elements"]
            if n < 2:
                results["errors"].append("Au moins 2 éléments d'arbre sont requis")
            elif n > 20:
                results["warnings"].append("Beaucoup d'éléments — calcul plus lent")
            else:
                results["passed"].append(f"Nombre d'éléments valide ({n})")
        
        if "od" in user_params and user_params["od"] <= 0:
            results["errors"].append("Le diamètre de l'arbre doit être positif")
        
        if "force_magnitude" in user_params:
            f = user_params["force_magnitude"]
            if f <= 0:
                results["errors"].append("La force doit être positive")
            elif f > 10000:
                results["warnings"].append("Force très élevée — vérifiez la cohérence")
        
        if "unbalance_magnitude" in user_params:
            u = user_params["unbalance_magnitude"]
            if u <= 0:
                results["errors"].append("Le balourd doit être positif")
            elif u > 0.1:
                results["warnings"].append("Balourd très élevé — peu réaliste")
        
        return results
    
    def verify_results(self, rotor, modal=None, camp=None, unbal=None, frf=None, 
                       tp_config=None) -> dict:
        """Compare les résultats avec les critères de validation."""
        results = {"score": 0, "total": 0, "details": [], "passed": False}
        
        if rotor is None:
            results["details"].append(("❌", "Rotor non assemblé"))
            return results
        
        # Critère 1 : assemblage réussi
        results["total"] += 1
        results["score"] += 1
        results["details"].append(("✅", f"Rotor assemblé — {len(rotor.nodes)} nœuds, masse {rotor.m:.2f} kg"))
        
        # Critère 2 : masse cohérente
        if tp_config and "validation" in tp_config:
            val = tp_config["validation"]
            if "expected_mass_min" in val:
                results["total"] += 1
                m_ok = val["expected_mass_min"] <= rotor.m <= val["expected_mass_max"]
                if m_ok:
                    results["score"] += 1
                    results["details"].append(("✅", f"Masse {rotor.m:.2f} kg dans la plage attendue"))
                else:
                    results["details"].append(("⚠️", f"Masse {rotor.m:.2f} kg hors plage"))
        
        # Critère 3 : modes propres positifs
        if modal is not None:
            results["total"] += 1
            fn = modal.wn / (2 * np.pi)
            if fn[0] > 0:
                results["score"] += 1
                results["details"].append(("✅", f"1ère fréquence propre : {fn[0]:.1f} Hz"))
            else:
                results["details"].append(("❌", "Fréquence propre nulle — vérifiez les paliers"))
        
        # Critère 4 : stabilité (log_dec > 0)
        if hasattr(modal, 'log_dec') and len(modal.log_dec) > 0:
            results["total"] += 1
            ld = modal.log_dec[:6]
            if all(ld > -0.01):
                results["score"] += 1
                results["details"].append(("✅", f"Tous les modes stables (Log Dec min = {min(ld):.3f})"))
            else:
                unstable = [i+1 for i, v in enumerate(ld) if v < 0]
                results["details"].append(("❌", f"Modes instables détectés : {unstable}"))
        
        # Critère 5 : réponse au balourd calculée
        if unbal is not None:
            results["total"] += 1
            results["score"] += 1
            results["details"].append(("✅", "Réponse au balourd calculée avec succès"))
        
        # Critère 6 : réponse fréquentielle calculée
        if frf is not None:
            results["total"] += 1
            results["score"] += 1
            results["details"].append(("✅", "Réponse fréquentielle (FRF) calculée avec succès"))
        
        # Score final
        if results["total"] > 0:
            pct = results["score"] / results["total"]
            results["passed"] = pct >= 0.75
            results["percentage"] = pct * 100
        
        return results
    
    def generate_feedback(self, validation_result: dict) -> Tuple[str, str]:
        """Génère un feedback HTML et une icône."""
        pct = validation_result.get("percentage", 0)
        if pct >= 90:
            return "✅", f"Excellent ! Score {pct:.0f}% — Tous les critères validés."
        elif pct >= 60:
            return "⚠️", f"Bon travail ! Score {pct:.0f}% — Quelques points à revoir."
        else:
            return "❌", f"Score {pct:.0f}% — Revoyez les paramètres (consultez les hints)."
    
    def award_badge(self, tp_id: str, score: float) -> Optional[str]:
        """Attribue un badge selon le score."""
        if score >= 95:
            return "gold"
        elif score >= 75:
            return "silver"
        elif score >= 50:
            return "bronze"
        return None

# =============================================================================
# CLASSE 4 : ReportGenerator
# =============================================================================
class ReportGenerator:
    """Génération de rapports PDF et HTML."""
    
    def __init__(self, user_id: str = "Étudiant"):
        self.user_id = user_id
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def generate_html(self, tp_id: str, params: dict, validation: dict,
                      rotor=None, modal=None, unbal=None, frf=None) -> str:
        """Génère un rapport HTML complet."""
        fn_table = ""
        if modal is not None:
            fn = modal.wn / (2 * np.pi)
            ld = modal.log_dec if hasattr(modal, 'log_dec') else ["-"] * 6
            rows = ""
            for i, (f, d) in enumerate(zip(fn[:6], ld[:6])):
                color = "#22863A" if d > 0.1 else ("#F9A825" if d > 0 else "#C00000")
                rows += f"<tr><td>{i+1}</td><td>{f:.2f}</td><td style='color:{color};font-weight:bold'>{d:.4f}</td></tr>"
            fn_table = f"""
            <h3>Fréquences Propres</h3>
            <table border='1' cellpadding='6' style='border-collapse:collapse;width:100%'>
            <tr style='background:#1F5C8B;color:white'><th>Mode</th><th>fn (Hz)</th><th>Log Dec</th></tr>
            {rows}
            </table>"""
        
        analyses_html = ""
        if unbal is not None:
            analyses_html += "<h3>Réponse au Balourd</h3><p>✅ Calculée avec succès</p>"
        if frf is not None:
            analyses_html += "<h3>Réponse Fréquentielle (FRF)</h3><p>✅ Calculée avec succès</p>"
        
        details_html = "".join(
            f"<li><b>{icon}</b> {msg}</li>"
            for icon, msg in validation.get("details", [])
        )
        
        score = validation.get("percentage", 0)
        score_color = "#22863A" if score >= 75 else ("#F9A825" if score >= 50 else "#C00000")
        
        return f"""<!DOCTYPE html>
<html><head><meta charset='UTF-8'>
<title>Rapport TP — {tp_id}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; color: #333; }}
h1 {{ color: #1F5C8B; border-bottom: 3px solid #1F5C8B; padding-bottom: 8px; }}
h2 {{ color: #C55A11; }}
.score {{ font-size: 2em; font-weight: bold; color: {score_color}; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
th {{ background: #1F5C8B; color: white; padding: 8px; }}
td {{ padding: 6px; border: 1px solid #DDD; }}
.footer {{ margin-top: 40px; color: #999; font-size: 0.85em; border-top: 1px solid #EEE; padding-top: 10px; }}
</style>
</head><body>
<h1>⚙️ RotoPédago v5.0 — Rapport de TP</h1>
<p><b>Exercice :</b> {tp_id} &nbsp;|&nbsp; <b>Étudiant :</b> {self.user_id} &nbsp;|&nbsp; <b>Date :</b> {self.timestamp}</p>
<h2>Score de Validation</h2>
<p class='score'>{score:.0f}% {'✅' if score >= 75 else '⚠️'}</p>
<h2>Critères Détaillés</h2>
<ul>{details_html}</ul>
<h2>Paramètres Utilisés</h2>
<table><tr style='background:#1F5C8B;color:white'><th>Paramètre</th><th>Valeur</th></tr>
{''.join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in params.items())}
</table>
{fn_table}
{analyses_html}
<div class='footer'>Généré par RotoPédago v5.0 — ROSS Rotordynamic Open-Source Software (v{ROSS_VERSION})</div>
</body></html>"""
    
    def generate_pdf_bytes(self, html_content: str) -> bytes:
        """Retourne le HTML encodé (simulé car reportlab non requis ici)."""
        return html_content.encode("utf-8")

# =============================================================================
# HELPERS UI
# =============================================================================
def _badge_html(badge: Optional[str], tp_id: str) -> str:
    if badge == "gold":
        return f"<span class='badge badge-gold'>🥇 {tp_id} — Or</span>"
    elif badge == "silver":
        return f"<span class='badge badge-silver'>🥈 {tp_id} — Argent</span>"
    elif badge == "bronze":
        return f"<span class='badge badge-bronze'>🥉 {tp_id} — Bronze</span>"
    return ""

def _log_dec_color(ld: float) -> str:
    if ld > 0.3:  return "#22863A"
    if ld > 0.1:  return "#F9A825"
    if ld > 0.0:  return "#E65100"
    return "#C00000"

def _modal_table(modal) -> pd.DataFrame:
    fn  = modal.wn / (2 * np.pi)
    fd  = modal.wd / (2 * np.pi) if hasattr(modal, 'wd') else fn
    ld  = modal.log_dec if hasattr(modal, 'log_dec') else np.zeros(len(fn))
    xi  = ld / (2 * np.pi) if len(ld) > 0 else np.zeros(len(fn))
    n   = min(8, len(fn))
    return pd.DataFrame({
        "Mode":              range(1, n+1),
        "fn (Hz)":           [f"{v:.3f}" for v in fn[:n]],
        "ωn (rad/s)":        [f"{v:.2f}" for v in modal.wn[:n]],
        "Log Dec":           [f"{v:.4f}" for v in ld[:n]],
        "Stabilité":         ["✅ Stable" if v > 0 else "❌ INSTABLE" for v in ld[:n]],
    })

def _plot_frf_bode(frf, probe_node: int = 0):
    """
    Crée les diagrammes de Bode pour la réponse fréquentielle (FRF).
    Utilise les méthodes de plot de ROSS si disponibles.
    """
    try:
        # Tentative avec la méthode native ROSS
        fig = frf.plot_bode(probe=[probe_node])
        return fig
    except:
        # Fallback: création manuelle des diagrammes
        try:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               subplot_titles=('Magnitude (dB)', 'Phase (°)'))
            
            frequency = frf.frequency / (2 * np.pi)  # Conversion en Hz
            magnitude = 20 * np.log10(np.abs(frf.response[probe_node, :]) + 1e-10)
            phase = np.angle(frf.response[probe_node, :]) * 180 / np.pi
            
            fig.add_trace(go.Scatter(x=frequency, y=magnitude, name='Magnitude'), row=1, col=1)
            fig.add_trace(go.Scatter(x=frequency, y=phase, name='Phase'), row=2, col=1)
            
            fig.update_layout(xaxis_title="Fréquence (Hz)", height=600,
                             title=f"Diagrammes de Bode — Nœud {probe_node}")
            return fig
        except Exception as e:
            st.warning(f"Visualisation FRF indisponible : {e}")
            return None

# =============================================================================
# PAGE : ACCUEIL
# =============================================================================
def render_homepage():
    st.markdown("""
    <div style='text-align:center; padding: 30px 0 10px 0'>
    <h1 style='color:#1F5C8B; font-size:2.8em'>⚙️ RotoPédago v5.0</h1>
    <p style='font-size:1.2em; color:#555'>Application pédagogique de rotordynamique • Propulsée par ROSS v{ROSS_VERSION}</p>
    </div>
    """.format(ROSS_VERSION=ROSS_VERSION), unsafe_allow_html=True)
    
    if not ROSS_AVAILABLE:
        st.error("⚠️ La bibliothèque ROSS n'est pas installée. Installez-la avec : `pip install ross-rotordynamics`")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='tp-card'>
        <h3>🎓 Mode TP</h3>
        <p>Parcours guidé en 3 niveaux progressifs (Découverte → Maîtrise → Expertise)</p>
        <p>✅ Feedback immédiat<br>✅ Badges de réussite<br>✅ Export rapport HTML</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='tp-card'>
        <h3>🏗️ Mode Libre</h3>
        <p>Construisez et analysez vos propres rotors sans contraintes</p>
        <p>✅ 6 analyses disponibles<br>✅ FRF & Balourd<br>✅ Tableaux modaux</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='tp-card'>
        <h3>📚 Documentation</h3>
        <p>Références théoriques, API ROSS et normes industrielles (API 684)</p>
        <p>✅ Théorie MEF<br>✅ Glossaire<br>✅ Exemples de code</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Progression globale
    prog = st.session_state.get("badges", {})
    n_badges = len(prog)
    total_tp = sum(len(lvl["tps"]) for lvl in TP_CATALOGUE.values())
    st.markdown(f"### 📊 Votre progression : {n_badges}/{total_tp} TP complétés")
    st.progress(n_badges / total_tp if total_tp > 0 else 0)
    
    if prog:
        badges_html = "".join(_badge_html(v, k) for k, v in prog.items())
        st.markdown(badges_html, unsafe_allow_html=True)
    else:
        st.info("Commencez le Mode TP pour débloquer vos badges ! 🏅")

# =============================================================================
# PAGE : MODE TP
# =============================================================================
def render_tp_mode():
    st.title("🎓 Mode TP — Parcours Pédagogique")
    
    if not ROSS_AVAILABLE:
        st.error("ROSS non disponible. Impossible de lancer les simulations.")
        return
    
    # Sélection niveau
    level = st.sidebar.selectbox(
        "Niveau :",
        options=list(TP_CATALOGUE.keys()),
        format_func=lambda x: f"Niveau {x} — {TP_CATALOGUE[x]['title'].split('—')[1].strip()}"
    )
    
    lvl_data = TP_CATALOGUE[level]
    tp_ids = list(lvl_data["tps"].keys())
    tp_id = st.sidebar.radio("Exercice :", tp_ids,
                            format_func=lambda x: f"{lvl_data['tps'][x]['icon']} {x} — {lvl_data['tps'][x]['title']}")
    
    tp = lvl_data["tps"][tp_id]
    validator = TPValidator(tp_id)
    reporter = ReportGenerator(st.session_state.get("user_name", "Étudiant"))
    
    # En-tête TP
    st.markdown(f"""
    <div class='tp-card'>
    <h2>{tp['icon']} {tp_id} — {tp['title']}</h2>
    <p><b>Niveau {level}</b> &nbsp;|&nbsp; Durée estimée : {lvl_data['duration']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_th, tab_sim, tab_valid, tab_report = st.tabs(
        ["📖 Théorie", "🔬 Simulation", "✅ Validation", "📄 Rapport"]
    )
    
    # ── THÉORIE ──
    with tab_th:
        st.markdown(f"### 🎯 Objectifs")
        for obj in tp["objectives"]:
            st.markdown(f"- {obj}")
        st.markdown(f"### 📐 Concepts Théoriques")
        st.info(tp["theory"])
        st.markdown("### 💡 Hints")
        for h in tp["hints"]:
            st.markdown(f"- {h}")
    
    # ── SIMULATION ──
    with tab_sim:
        rotor, modal, camp, unbal, frf = None, None, None, None, None
        
        if tp_id == "TP1.1":
            rotor, modal = _tp11_interface(tp, validator)
        elif tp_id == "TP1.2":
            rotor, modal = _tp12_interface(tp)
        elif tp_id == "TP2.1":
            rotor, camp = _tp21_interface(tp)
        elif tp_id == "TP2.2":
            rotor, modal, unbal = _tp22_interface(tp)
        elif tp_id == "TP2.3":
            rotor, modal, frf = _tp23_interface(tp)  # NOUVEAU TP FRF
        elif tp_id == "TP3.1":
            rotor = _tp31_interface(tp)
        elif tp_id == "TP3.2":
            rotor, modal, camp = _tp32_interface(tp)
    
    # ── VALIDATION ──
    with tab_valid:
        st.subheader("📋 Résultats de Validation")
        if rotor is None:
            st.warning("⚠️ Lancez d'abord la simulation dans l'onglet 🔬")
        else:
            val_result = validator.verify_results(rotor, modal=modal, unbal=unbal, frf=frf, tp_config=tp)
            icon, msg = validator.generate_feedback(val_result)
            score = val_result.get("percentage", 0)
            
            # Score visuel
            col_s, col_d = st.columns([1, 2])
            with col_s:
                color = "#22863A" if score >= 75 else ("#F9A825" if score >= 50 else "#C00000")
                st.markdown(f"""
                <div style='text-align:center; background:{color}22; border:2px solid {color};
                border-radius:12px; padding:20px'>
                <div style='font-size:3em'>{icon}</div>
                <div style='font-size:2.5em; font-weight:bold; color:{color}'>{score:.0f}%</div>
                <div style='color:{color}'>{msg}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_d:
                st.markdown("**Détail des critères :**")
                for det_icon, det_msg in val_result["details"]:
                    st.markdown(f"{det_icon} {det_msg}")
            
            # Badge
            badge = validator.award_badge(tp_id, score)
            if badge:
                if "badges" not in st.session_state:
                    st.session_state.badges = {}
                st.session_state.badges[tp_id] = badge
                st.markdown(_badge_html(badge, tp_id), unsafe_allow_html=True)
    
    # ── RAPPORT ──
    with tab_report:
        st.subheader("📄 Exporter mon TP")
        params_used = tp.get("default_params", {})
        if rotor:
            params_used["Masse calculée (kg)"] = f"{rotor.m:.2f}"
            params_used["Nœuds"] = len(rotor.nodes)
        
        if st.button("📥 Générer le rapport HTML"):
            val_result_rep = validator.verify_results(rotor, modal=modal, unbal=unbal, frf=frf, tp_config=tp) if rotor else {"details": [], "percentage": 0}
            html = reporter.generate_html(tp_id, params_used, val_result_rep, rotor, modal, unbal, frf)
            st.download_button(
                label="⬇️ Télécharger le rapport (.html)",
                data=html.encode("utf-8"),
                file_name=f"Rapport_{tp_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html"
            )
            st.success("✅ Rapport généré ! Cliquez sur le bouton de téléchargement.")

# =============================================================================
# INTERFACES INDIVIDUELLES PAR TP
# =============================================================================
def _build_standard_rotor(n_el, L, od, disk_node, disk_od, disk_w, kxx, cxx, kxy=0.0, kyy=None):
    """Helper : construit le rotor standard et affiche les erreurs."""
    if kyy is None:
        kyy = kxx
    builder = RotorBuilder()
    (builder
     .add_shaft(n_el, L, od)
     .add_disk(disk_node, disk_od, disk_w)
     .add_bearing(0, kxx, kyy, kxy, cxx)
     .add_bearing(n_el, kxx, kyy, kxy, cxx))
    
    for err in builder.errors:
        st.error(err)
    
    return builder.build()

def _tp11_interface(tp, validator):
    st.subheader("🔧 TP1.1 — Construire son premier rotor")
    d = tp["default_params"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Arbre**")
        n_el = st.slider("Nombre d'éléments", 2, 10, d["n_elements"])
        L_el = st.number_input("Longueur d'un élément (m)", 0.05, 1.0, float(d["L_elem"]), 0.05)
        od   = st.number_input("Diamètre extérieur (m)", 0.01, 0.3, float(d["od"]), 0.005)
    
    with col2:
        st.markdown("**Disque**")
        disk_n  = st.slider("Nœud du disque", 0, n_el, min(d["disk_node"], n_el))
        disk_od = st.number_input("Diamètre disque (m)", 0.05, 0.8, float(d["disk_od"]), 0.01)
        disk_w  = st.number_input("Largeur disque (m)", 0.01, 0.3, float(d["disk_width"]), 0.01)
    
    with col3:
        st.markdown("**Paliers**")
        kxx = st.number_input("Kxx (N/m)", 1e4, 1e9, float(d["kxx"]), format="%.2e")
        cxx = st.number_input("Cxx (N·s/m)", 10.0, 10000.0, float(d["cxx"]))
    
    # Validation paramètres en temps réel
    p_check = validator.check_parameters({"n_elements": n_el, "kxx": kxx, "od": od})
    for e in p_check["errors"]:
        st.error(e)
    for w in p_check["warnings"]:
        st.warning(w)
    
    rotor, modal = None, None
    if st.button("🚀 Assembler et visualiser", key="btn_tp11"):
        with st.spinner("Assemblage en cours..."):
            rotor = _build_standard_rotor(n_el, L_el, od, disk_n, disk_od, disk_w, kxx, cxx)
            if rotor:
                st.success(f"✅ Rotor assemblé — {len(rotor.nodes)} nœuds | Masse : {rotor.m:.2f} kg")
                col_plot, col_info = st.columns([2, 1])
                with col_plot:
                    try:
                        st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
                    except Exception as e:
                        st.warning(f"Visualisation 3D indisponible : {e}")
                with col_info:
                    st.metric("Masse totale", f"{rotor.m:.2f} kg")
                    st.metric("Nombre de nœuds", len(rotor.nodes))
                    st.metric("Longueur totale", f"{n_el * L_el:.3f} m")
    
    _CACHE["tp11_rotor"] = rotor
    _CACHE["tp11_modal"] = modal
    rotor = _CACHE.get("tp11_rotor")
    modal = _CACHE.get("tp11_modal")
    return rotor, modal

def _tp12_interface(tp):
    st.subheader("📊 TP1.2 — Modes propres et déformées")
    st.info("Ce TP reprend le rotor du TP1.1. Lancez d'abord TP1.1 pour assembler votre rotor.")
    
    rotor = _CACHE.get("tp11_rotor")
    modal = None
    
    if rotor is None:
        st.warning("⚠️ Aucun rotor en mémoire — retournez à TP1.1.")
        return None, None
    
    n_modes = st.slider("Nombre de modes à calculer", 2, 10, 6)
    
    if st.button("🔬 Calculer les modes propres", key="btn_tp12"):
        engine = SimulationEngine(rotor)
        with st.spinner("Calcul modal..."):
            modal = engine.run_modal(speed_rpm=0)
            if modal:
                _CACHE["tp12_modal"] = modal
            else:
                st.error(f"Erreur de calcul : {engine.last_error}")
    
    modal = _CACHE.get("tp12_modal")
    
    if modal:
        st.markdown("#### Tableau des Fréquences Propres")
        df_modal = _modal_table(modal)
        st.dataframe(df_modal, use_container_width=True, hide_index=True)
        
        mode_idx = st.selectbox("Mode à visualiser :", 
                               range(min(n_modes, len(modal.evalues)//2)),
                               format_func=lambda x: f"Mode {x+1} — {modal.wn[x]/(2*np.pi):.2f} Hz")
        try:
            fig = modal.plot_mode_3d(mode=mode_idx)
            st.plotly_chart(fig, use_container_width=True)
        except:
            try:
                fig = modal.plot_mode_shape(mode=mode_idx)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Visualisation de mode indisponible : {e}")
    
    return rotor, modal

def _tp21_interface(tp):
    st.subheader("📈 TP2.1 — Paliers anisotropes et Campbell")
    d = tp["default_params"]
    
    col1, col2 = st.columns(2)
    with col1:
        kxx = st.number_input("Kxx (N/m)", 1e5, 1e9, float(d["kxx"]), format="%.2e")
        kyy = st.number_input("Kyy (N/m)", 1e5, 1e9, float(d["kyy"]), format="%.2e")
        st.metric("Ratio Kxx/Kyy", f"{kxx/kyy:.2f}")
    
    with col2:
        v_max = st.slider("Vitesse max (RPM)", 2000, 20000, int(d["speed_max_rpm"]))
        n_pts  = st.slider("Résolution (points)", 50, 200, 100)
    
    rotor, camp = None, None
    if st.button("📊 Calculer le diagramme de Campbell", key="btn_tp21"):
        with st.spinner("Calcul Campbell en cours..."):
            rotor = _build_standard_rotor(5, 0.2, 0.05, 2, 0.25, 0.07, kxx, 500, kyy=kyy)
            if rotor:
                engine = SimulationEngine(rotor)
                camp = engine.run_campbell(v_max, n_pts)
                if camp:
                    _CACHE["tp21_camp"] = camp
                    _CACHE["tp21_rotor"] = rotor
                else:
                    st.error(f"Erreur Campbell : {engine.last_error}")
    
    rotor = _CACHE.get("tp21_rotor")
    camp  = _CACHE.get("tp21_camp")
    
    if camp:
        try:
            fig = camp.plot()
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            _plot_campbell_manual(camp, v_max, n_pts)
        
        st.markdown("#### ⚡ Vitesses Critiques estimées (intersections 1X)")
        speeds_rpm = np.linspace(0, v_max, n_pts)
        try:
            modal_0 = rotor.run_modal(speed=0)
            fn = modal_0.wn / (2 * np.pi)
            crit_df = pd.DataFrame({
                "Mode": range(1, len(fn[:4])+1),
                "Fréquence (Hz)": [f"{v:.2f}" for v in fn[:4]],
                "Vitesse critique (RPM)": [f"{v*60:.0f}" for v in fn[:4]]
            })
            st.dataframe(crit_df, use_container_width=True, hide_index=True)
        except:
            st.info("Vitesses critiques non disponibles.")
    
    return rotor, camp

def _plot_campbell_manual(camp, v_max, n_pts):
    """Tracé Campbell manuel si camp.plot() échoue."""
    try:
        speeds_rpm = np.linspace(0, v_max, n_pts)
        fig = go.Figure()
        n_modes = min(6, camp.wd.shape[1] if hasattr(camp, 'wd') else 4)
        
        for i in range(n_modes):
            fn = camp.wd[:, i] / (2 * np.pi) if hasattr(camp, 'wd') else camp.wn[:, i]/(2*np.pi)
            fig.add_trace(go.Scatter(x=speeds_rpm, y=fn, name=f"Mode {i+1}"))
        
        fig.add_trace(go.Scatter(x=speeds_rpm, y=speeds_rpm/60,
                                name="1X", line=dict(dash="dash", color="red")))
        fig.update_layout(xaxis_title="Vitesse (RPM)", yaxis_title="Fréquence (Hz)",
                         title="Diagramme de Campbell")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Impossible de tracer le Campbell : {e}")

def _tp22_interface(tp):
    """TP2.2 — Réponse au balourd (Unbalance Response)"""
    st.subheader("🌀 TP2.2 — Réponse au balourd")
    d = tp["default_params"]
    
    rotor_prev = _CACHE.get("tp11_rotor")
    if rotor_prev is None:
        st.warning("⚠️ Retournez à TP1.1 pour créer un rotor.")
        return None, None, None
    
    col1, col2 = st.columns(2)
    with col1:
        unbal_node = st.slider("Nœud du balourd", 0, 5, d["unbalance_node"])
        magnitude  = st.number_input("Magnitude balourd (kg·m)", 1e-5, 0.1, 
                                     float(d["unbalance_magnitude"]), format="%.5f")
        phase      = st.slider("Phase (°)", 0, 360, int(d["unbalance_phase"]))
    
    with col2:
        probe_node = st.slider("Nœud de mesure (probe)", 0, 5, d["probe_node"])
        freq_max   = st.slider("Fréquence max analyse (Hz)", 100, 5000, d["freq_max"])
    
    modal, unbal = None, None
    if st.button("🌀 Calculer la réponse au balourd", key="btn_tp22"):
        engine = SimulationEngine(rotor_prev)
        with st.spinner("Calcul modal + réponse au balourd..."):
            modal = engine.run_modal()
            unbal = engine.run_unbalance_response(
                node=unbal_node, 
                magnitude=magnitude, 
                phase=np.deg2rad(phase), 
                freq_max=freq_max
            )
            if unbal:
                _CACHE["tp22_unbal"] = unbal
                _CACHE["tp22_modal"] = modal
            else:
                st.error(f"Erreur : {engine.last_error}")
    
    unbal = _CACHE.get("tp22_unbal")
    modal = _CACHE.get("tp22_modal")
    
    if unbal:
        try:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Magnitude (Bode)**")
                fig_mag = unbal.plot_magnitude(probe=[probe_node, 0])
                st.plotly_chart(fig_mag, use_container_width=True)
            with col_b:
                st.markdown("**Phase (Bode)**")
                fig_ph = unbal.plot_phase(probe=[probe_node, 0])
                st.plotly_chart(fig_ph, use_container_width=True)
        except Exception as e:
            st.warning(f"Visualisation avancée indisponible ({e}) — affichage simplifié.")
        
    return rotor_prev, modal, unbal

def _tp23_interface(tp):
    """
    TP2.3 — Réponse Fréquentielle (FRF)
    NOUVELLE FONCTIONNALITÉ : Utilise run_freq_response de ROSS
    """
    st.subheader("📉 TP2.3 — Réponse Fréquentielle (FRF)")
    d = tp["default_params"]
    
    rotor_prev = _CACHE.get("tp11_rotor")
    if rotor_prev is None:
        st.warning("⚠️ Retournez à TP1.1 pour créer un rotor.")
        return None, None, None
    
    st.info("💡 La FRF analyse la réponse à une force harmonique externe (contrairement au balourd qui est une force tournante)")
    
    col1, col2 = st.columns(2)
    with col1:
        force_node = st.slider("Nœud d'application de la force", 0, 5, d["force_node"])
        force_mag  = st.number_input("Magnitude de la force (N)", 1.0, 10000.0, 
                                     float(d["force_magnitude"]), format="%.1f")
        force_dir  = st.selectbox("Direction de la force", ["x", "y"], index=0)
    
    with col2:
        probe_node = st.slider("Nœud de mesure (probe)", 0, 5, d["force_node"])
        freq_min   = st.number_input("Fréquence min (Hz)", 0.0, 1000.0, 0.0)
        freq_max   = st.slider("Fréquence max (Hz)", 100, 5000, d["freq_max"])
    
    modal, frf = None, None
    
    # Validation des paramètres
    param_check = {"force_magnitude": force_mag}
    validator = TPValidator("TP2.3")
    p_check = validator.check_parameters(param_check)
    for e in p_check["errors"]:
        st.error(e)
    for w in p_check["warnings"]:
        st.warning(w)
    
    if st.button("📉 Calculer la réponse fréquentielle (FRF)", key="btn_tp23"):
        engine = SimulationEngine(rotor_prev)
        with st.spinner("Calcul modal + FRF..."):
            modal = engine.run_modal()
            frf = engine.run_freq_response(
                node=force_node,
                force_magnitude=force_mag,
                force_direction=force_dir,
                freq_min=freq_min,
                freq_max=freq_max
            )
            if frf:
                _CACHE["tp23_frf"] = frf
                _CACHE["tp23_modal"] = modal
                st.success("✅ FRF calculée avec succès !")
            else:
                st.error(f"Erreur FRF : {engine.last_error}")
    
    frf = _CACHE.get("tp23_frf")
    modal = _CACHE.get("tp23_modal")
    
    if frf:
        st.markdown("#### 📊 Diagrammes de Bode (FRF)")
        
        try:
            # Essai avec la méthode native ROSS
            fig_bode = _plot_frf_bode(frf, probe_node=probe_node)
            if fig_bode:
                st.plotly_chart(fig_bode, use_container_width=True)
            else:
                st.info("Utilisation du tracé alternatif...")
                # Tracé alternatif
                frequency = frf.frequency / (2 * np.pi)
                fig_alt = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                       subplot_titles=('Magnitude', 'Phase'))
                fig_alt.add_trace(go.Scatter(x=frequency, 
                                            y=np.abs(frf.response[probe_node, :]), 
                                            name='Magnitude'), row=1, col=1)
                fig_alt.add_trace(go.Scatter(x=frequency, 
                                            y=np.angle(frf.response[probe_node, :])*180/np.pi, 
                                            name='Phase'), row=2, col=1)
                st.plotly_chart(fig_alt, use_container_width=True)
        except Exception as e:
            st.warning(f"Visualisation FRF limitée : {e}")
        
        # Informations supplémentaires
        st.markdown("#### 📋 Informations FRF")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("Fréquence min", f"{freq_min:.1f} Hz")
            st.metric("Fréquence max", f"{freq_max:.1f} Hz")
        with col_info2:
            st.metric("Force appliquée", f"{force_mag:.1f} N")
            st.metric("Direction", force_dir.upper())
    
    return rotor_prev, modal, frf

def _tp31_interface(tp):
    st.subheader("⚠️ TP3.1 — Instabilité par raideur croisée")
    d = tp["default_params"]
    
    kxy_max = st.slider("Kxy max (N/m)", int(1e5), int(1e7), int(d["kxy_max"]), step=int(1e5))
    v_max   = st.slider("Vitesse max (RPM)", 1000, 10000, int(d["speed_max_rpm"]))
    
    st.markdown("**Faites varier Kxy et observez l'évolution du Log Décrément :**")
    kxy_val = st.slider("Kxy actuel (N/m)", 0, kxy_max, 0, step=int(kxy_max/20))
    
    rotor = None
    if st.button("⚠️ Analyser la stabilité", key="btn_tp31"):
        with st.spinner("Calcul..."):
            rotor = _build_standard_rotor(5, 0.2, 0.05, 2, 0.25, 0.07, 1e7, 1000, kxy=kxy_val)
            if rotor:
                engine = SimulationEngine(rotor)
                speeds = np.linspace(0, v_max * np.pi / 30, 50)
                camp = rotor.run_campbell(speeds)
                
                fig = go.Figure()
                try:
                    for i in range(min(4, camp.log_dec.shape[1])):
                        ld = camp.log_dec[:, i]
                        color = "green" if all(ld > 0) else "red"
                        fig.add_trace(go.Scatter(
                            x=np.linspace(0, v_max, 50),
                            y=ld, name=f"Mode {i+1}", 
                            line=dict(color=color if i == 0 else None)
                        ))
                except:
                    pass
                
                fig.add_hline(y=0, line_dash="dash", line_color="red", 
                             annotation_text="Seuil instabilité")
                fig.update_layout(xaxis_title="Vitesse (RPM)", yaxis_title="Log Décrément",
                                 title=f"Stabilité — Kxy = {kxy_val:.1e} N/m")
                st.plotly_chart(fig, use_container_width=True)
                
                if kxy_val == 0:
                    st.markdown("<div class='status-ok'>✅ Kxy = 0 — Système stable</div>", unsafe_allow_html=True)
                elif kxy_val < kxy_max * 0.5:
                    st.markdown("<div class='status-warn'>⚠️ Kxy modéré — Surveillez le Log Dec</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='status-err'>❌ Kxy élevé — Risque d'instabilité !</div>", unsafe_allow_html=True)
    
    _CACHE["tp31_rotor"] = rotor
    return _CACHE.get("tp31_rotor")

def _tp32_interface(tp):
    st.subheader("🏭 TP3.2 — Cas industriel complet (API 684)")
    d = tp["default_params"]
    
    op_rpm = st.number_input("Vitesse opérationnelle (RPM)", 500.0, 10000.0, float(d["operating_rpm"]))
    
    col1, col2 = st.columns(2)
    with col1:
        n_el  = st.slider("Éléments d'arbre", 4, 12, d["n_elements"])
        od    = st.number_input("Diamètre arbre (m)", 0.02, 0.2, 0.08, 0.01)
    
    with col2:
        kxx = st.number_input("Kxx paliers (N/m)", 1e5, 1e9, 5e7, format="%.2e")
        cxx = st.number_input("Cxx paliers (N·s/m)", 100.0, 5000.0, 1000.0)
    
    rotor, modal, camp = None, None, None
    
    if st.button("🏭 Lancer l'analyse complète API 684", key="btn_tp32"):
        with st.spinner("Analyse industrielle en cours..."):
            rotor = _build_standard_rotor(n_el, 0.3, od, n_el//2, 0.4, 0.1, kxx, cxx)
            if rotor:
                engine = SimulationEngine(rotor)
                modal = engine.run_modal()
                camp  = engine.run_campbell(op_rpm * 2, 100)
                _CACHE.update({"tp32_rotor": rotor, "tp32_modal": modal, "tp32_camp": camp})
    
    rotor = _CACHE.get("tp32_rotor")
    modal = _CACHE.get("tp32_modal")
    camp  = _CACHE.get("tp32_camp")
    
    if rotor and modal:
        # Vérification API 684
        fn = modal.wn / (2 * np.pi) * 60  # en RPM
        zone_low  = op_rpm * 0.85
        zone_high = op_rpm * 1.15
        ld = modal.log_dec if hasattr(modal, 'log_dec') else np.zeros(6)
        
        st.markdown("#### 📋 Vérification Conformité API 684")
        results_api = []
        for i, (fn_rpm, log_d) in enumerate(zip(fn[:4], ld[:4])):
            in_zone = zone_low <= fn_rpm <= zone_high
            log_ok  = log_d >= 0.1
            results_api.append({
                "Mode": i+1,
                "Fréq. critique (RPM)": f"{fn_rpm:.0f}",
                "Dans zone interdite": "❌ OUI" if in_zone else "✅ NON",
                "Log Dec ≥ 0.1": "✅ OUI" if log_ok else "❌ NON",
                "Conforme API 684": "✅" if (not in_zone and log_ok) else "❌"
            })
        
        st.dataframe(pd.DataFrame(results_api), use_container_width=True, hide_index=True)
        st.markdown(f"🔴 Zone interdite API : [{zone_low:.0f} – {zone_high:.0f}] RPM")
        
        n_ok = sum(1 for r in results_api if r["Conforme API 684"] == "✅")
        score = n_ok / max(len(results_api), 1) * 100
        col_s = "#22863A" if score >= 85 else "#C00000"
        st.markdown(f"<h3 style='color:{col_s}'>Score API 684 : {score:.0f}%</h3>", unsafe_allow_html=True)
    
    return rotor, modal, camp

# =============================================================================
# PAGE : MODE LIBRE (ENHANCED WITH FRF)
# =============================================================================
def render_free_mode():
   # st.title("🏗️ Mode Libre — Simulation Personnalisée")
    tabs = st.tabs(["🏗️ Géométrie", "📊 Modal", "📈 Campbell", "🌀 Balourd", "📉 FRF", "📏 Statique"])
    if not ROSS_AVAILABLE:
        st.error("ROSS non disponible.")
        return
    
    BEARING_PRESETS = {
        "Roulement à billes":     {"kxx": 1e7, "kyy": 1e7, "kxy": 0,   "cxx": 500,  "cyy": 500},
        "Palier lisse (hydro.)":  {"kxx": 1e7, "kyy": 5e6, "kxy": 2e6, "cxx": 2000, "cyy": 2000},
        "Support souple":         {"kxx": 1e6, "kyy": 1e6, "kxy": 0,   "cxx": 5000, "cyy": 5000},
    }
    
    preset = st.selectbox("Preset paliers :", list(BEARING_PRESETS.keys()))
    p = BEARING_PRESETS[preset]
    
    col1, col2, col3 = st.columns([1.1, 1, 1.2])
    with col1:
        st.subheader("🔩 Arbre")
        df_s = pd.DataFrame([{"L (m)": 0.2, "id (m)": 0.0, "od (m)": 0.05} for _ in range(5)])
        ed_s = st.data_editor(df_s, num_rows="dynamic", key="free_shaft")
    
    with col2:
        st.subheader("💿 Disques")
        df_d = pd.DataFrame([{"nœud": 2, "id (m)": 0.05, "od (m)": 0.25, "largeur (m)": 0.07}])
        ed_d = st.data_editor(df_d, num_rows="dynamic", key="free_disk")
    
    with col3:
        st.subheader("🔗 Paliers")
        df_b = pd.DataFrame([
            {"nœud": 0, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"], "cyy": p["cyy"]},
            {"nœud": len(ed_s)-1, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"], "cyy": p["cyy"]}
        ])
        ed_b = st.data_editor(df_b, num_rows="dynamic", key="free_bear")
    
    if st.button("🚀 Construire et analyser", type="primary"):
        try:
            shaft = [rs.ShaftElement(L=r[1], idl=r[2], odl=r[3], material=MAT_STEEL)
                    for r in ed_s.itertuples()]
            disks = [rs.DiskElement.from_geometry(n=int(r[1]), material=MAT_STEEL,
                                                  width=r[4], i_d=r[2], o_d=r[3])
                    for r in ed_d.itertuples()]
            bears = [rs.BearingElement(n=int(r[1]), kxx=r[2], kyy=r[3],
                                       kxy=r[4], kyx=-r[4], cxx=r[5], cyy=r[6])
                    for r in ed_b.itertuples()]
            
            rotor = rs.Rotor(shaft, disks, bears)
            st.session_state.free_rotor = rotor
            _CACHE["free_rotor"] = rotor
            st.success(f"✅ Rotor assemblé — {len(rotor.nodes)} nœuds | Masse : {rotor.m:.2f} kg")
        except Exception as e:
            st.error(f"❌ Erreur d'assemblage : {e}")
            _CACHE["free_rotor"] = None
    
    rotor = _CACHE.get("free_rotor")
    if "free_rotor" in st.session_state:
        rotor = st.session_state.free_rotor
    
    # ONGLETS AMÉLIORÉS AVEC FRF
    tabs = st.tabs(["🏗️ Géométrie", "📊 Modal", "📈 Campbell", "🌀 Balourd", "📉 FRF", "📏 Statique"])
    
    with tabs[0]:
        st.markdown("### 🏗️ Visualisation de la structure")
        if "free_rotor" in st.session_state:
            rotor = st.session_state.free_rotor
            try:
                fig_geom = rotor.plot_rotor()
                st.plotly_chart(fig_geom, use_container_width=True)
                st.success("Modèle 3D généré avec succès.")
            except Exception as e:
                st.error(f"Erreur d'affichage géométrique : {e}")
        else:
            st.info("Veuillez d'abord cliquer sur 'Construire et analyser'.")
    
    with tabs[1]:
        if st.button("Calculer les modes", key="free_modal_btn"):
            engine = SimulationEngine(rotor)
            modal = engine.run_modal()
            st.session_state.free_modal = modal
        
        if "free_modal" in st.session_state:
            modal = st.session_state.free_modal
            st.dataframe(_modal_table(modal), use_container_width=True, hide_index=True)
            mode_i = st.selectbox("Sélection du mode :", range(min(6, len(modal.evalues)//2)))
            try:
                fig_modal = safe_plot(modal, mode=mode_i)
                if fig_modal:
                    st.plotly_chart(fig_modal, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur d'affichage du mode : {e}")
    
    with tabs[2]:
        v_max = st.slider("Vitesse max (RPM)", 1000, 20000, 8000, key="free_camp_vmax")
        if st.button("Calculer Campbell", key="free_camp"):
            engine = SimulationEngine(rotor)
            camp = engine.run_campbell(v_max, 100)
            _CACHE["free_camp"] = camp
        
        camp = _CACHE.get("free_camp")
        if camp:
            try:
                st.plotly_chart(camp.plot(), use_container_width=True)
            except:
                _plot_campbell_manual(camp, v_max, 100)
    
    with tabs[3]:  # NOUVEL ONGLET BALOURD
        st.markdown("### 🌀 Réponse au Balourd")
        if "free_rotor" in st.session_state:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                unbal_node = st.slider("Nœud balourd", 0, len(ed_s), 2, key="free_unbal_node")
                unbal_mag = st.number_input("Magnitude (kg·m)", 1e-5, 0.1, 0.001, format="%.5f", key="free_unbal_mag")
                unbal_phase = st.slider("Phase (°)", 0, 360, 0, key="free_unbal_phase")
            with col_b2:
                probe_node = st.slider("Nœud probe", 0, len(ed_s), 2, key="free_probe_node")
                freq_max = st.slider("Fréquence max (Hz)", 100, 5000, 5000, key="free_unbal_freq")
            
            if st.button("Calculer réponse balourd", key="free_unbal_btn"):
                engine = SimulationEngine(st.session_state.free_rotor)
                unbal = engine.run_unbalance_response(
                    node=unbal_node,
                    magnitude=unbal_mag,
                    phase=np.deg2rad(unbal_phase),
                    freq_max=freq_max
                )
                if unbal:
                    _CACHE["free_unbal"] = unbal
                    st.success("✅ Réponse au balourd calculée !")
                else:
                    st.error(f"Erreur : {engine.last_error}")
            
            unbal = _CACHE.get("free_unbal")
            if unbal:
                try:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.plotly_chart(unbal.plot_magnitude(probe=[probe_node]), use_container_width=True)
                    with col_b:
                        st.plotly_chart(unbal.plot_phase(probe=[probe_node]), use_container_width=True)
                except Exception as e:
                    st.warning(f"Visualisation limitée : {e}")
        else:
            st.info("Construisez d'abord un rotor.")
    
    with tabs[4]:  # NOUVEL ONGLET FRF
        st.markdown("### 📉 Réponse Fréquentielle (FRF)")
        st.info("La FRF analyse la réponse à une force harmonique externe (différent du balourd)")
        
        if "free_rotor" in st.session_state:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                force_node = st.slider("Nœud force", 0, len(ed_s), 2, key="free_force_node")
                force_mag = st.number_input("Force (N)", 1.0, 10000.0, 100.0, key="free_force_mag")
                force_dir = st.selectbox("Direction", ["x", "y"], key="free_force_dir")
            with col_f2:
                probe_node = st.slider("Nœud probe", 0, len(ed_s), 2, key="free_frf_probe")
                frf_freq_max = st.slider("Fréquence max (Hz)", 100, 5000, 5000, key="free_frf_freq")
            
            if st.button("Calculer FRF", key="free_frf_btn"):
                engine = SimulationEngine(st.session_state.free_rotor)
                frf = engine.run_freq_response(
                    node=force_node,
                    force_magnitude=force_mag,
                    force_direction=force_dir,
                    freq_max=frf_freq_max
                )
                if frf:
                    _CACHE["free_frf"] = frf
                    st.success("✅ FRF calculée !")
                else:
                    st.error(f"Erreur : {engine.last_error}")
            
            frf = _CACHE.get("free_frf")
            if frf:
                try:
                    fig_bode = _plot_frf_bode(frf, probe_node=probe_node)
                    if fig_bode:
                        st.plotly_chart(fig_bode, use_container_width=True)
                    else:
                        st.info("Tracé Bode alternatif non disponible")
                except Exception as e:
                    st.warning(f"Visualisation FRF limitée : {e}")
        else:
            st.info("Construisez d'abord un rotor.")
    
    with tabs[5]:
        if st.button("Analyse statique", key="free_static"):
            try:
                static = rotor.run_static()
                fig_static = safe_plot(static)
                if fig_static:
                    st.plotly_chart(fig_static, use_container_width=True)
                else:
                    st.info("Visualisation statique non disponible.")
            except Exception as e:
                st.error(f"Analyse statique impossible : {e}")

# =============================================================================
# PAGE : DOCUMENTATION (MISE À JOUR)
# =============================================================================
def render_documentation():
    st.title("📚 Documentation & Références")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔬 Théorie", "🛠️ API ROSS", "📏 Normes", "💻 Code"])
    
    with tab1:
        st.markdown("""
        ## Fondements Théoriques
        ### Modèle de Timoshenko
        L'arbre est discrétisé en éléments de poutre de **Timoshenko** à 4 DDL par nœud :
        translations (u, v) et rotations (β, γ) dans les plans XZ et YZ.
        
        ### Équation du mouvement
        """)
        st.latex(r"M\ddot{q} + (C + G)\dot{q} + Kq = F(t)")
        st.markdown("""
        ### Réponse au Balourd vs FRF
        | Caractéristique | Balourd | FRF |
        |----------------|---------|-----|
        | Type de force | Tournante (synchrone) | Harmonique fixe |
        | Méthode ROSS | `run_unbalance_response` | `run_freq_response` |
        | Application | Déséquilibre masse | Excitation externe |
        """)
    
    with tab2:
        st.markdown("""
        ## API ROSS — Méthodes Principales
        | Méthode | Description | Sorties clés |
        |---------|-------------|--------------|
        | `run_static()` | Déflexion statique | `plot_deflected_shape()` |
        | `run_modal(speed)` | Fréquences propres | `.wn`, `.wd`, `.log_dec` |
        | `run_campbell(speeds)` | Diagramme de Campbell | `.plot()` |
        | `run_critical_speed()` | Vitesses critiques | Tableau numérique |
        | `run_unbalance_response()` | Réponse balourd | `plot_magnitude()`, `plot_phase()` |
        | `run_freq_response()` | Réponse fréquentielle | `plot_bode()` |
        | `run_time_response()` | Transitoires | Orbites, DFFT |
        
        **Référence :** Timbó et al. (2020), JOSS, 5(48), 2120
        """)
    
    with tab3:
        st.markdown("""
        ## Normes Industrielles
        ### API 684 — 2nd Edition
        1. **Marge de vitesse critique ≥ 15%**
        2. **Log Dec ≥ 0.1** pour tous les modes
        3. **Réponse au balourd** < limites ISO 7919
        
        ### ISO 1925 — Terminologie
        Définitions officielles : balourd, centre de gravité, axe principal d'inertie
        """)
    
    with tab4:
        st.markdown("## Exemples de Code ROSS")
        st.code("""
import ross as rs
import numpy as np

# Matériau
steel = rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9)

# Arbre
shaft = [rs.ShaftElement(L=0.2, idl=0, odl=0.05, material=steel) for _ in range(5)]

# Disque
disk = rs.DiskElement.from_geometry(n=2, material=steel, width=0.07, i_d=0.05, o_d=0.25)

# Paliers
bear0 = rs.BearingElement(n=0, kxx=1e7, kyy=1e7, cxx=500, cyy=500)
bear5 = rs.BearingElement(n=5, kxx=1e7, kyy=1e7, cxx=500, cyy=500)

# Assemblage
rotor = rs.Rotor(shaft, [disk], [bear0, bear5])

# Réponse au balourd
unbalance = [rs.Unbalance(node=2, magnitude=0.001, phase=0)]
unbal_response = rotor.run_unbalance_response(unbalance=unbalance, frequency=np.linspace(0, 5000, 500))

# Réponse fréquentielle (FRF)
force = [rs.Force(node=2, magnitude=100, phase=0)]
frf = rotor.run_freq_response(force=force, frequency=np.linspace(0, 5000, 500))
        """, language="python")

# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================
def main():
    # --- Session State Initialization ---
    if "badges" not in st.session_state:
        st.session_state.badges = {}
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Étudiant"
    
    # --- Sidebar ---
    st.sidebar.title("⚙️ RotoPédago v5.0")
    st.sidebar.markdown("---")
    st.session_state.user_name = st.sidebar.text_input("👤 Votre nom :", st.session_state.user_name)
    
    page = st.sidebar.radio(
        "Navigation :",
        ["🏠 Accueil", "🎓 Mode TP", "🏗️ Mode Libre", "📚 Documentation"]
    )
    
    # --- Progression sidebar ---
    if st.session_state.badges:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🏅 Mes badges :**")
        for tp_id, badge in st.session_state.badges.items():
            icons = {"gold": "🥇", "silver": "🥈", "bronze": "🥉"}
            st.sidebar.markdown(f"{icons.get(badge, '🏅')} {tp_id}")
    
    # ROSS status
    st.sidebar.markdown("---")
    if ROSS_AVAILABLE:
        st.sidebar.success(f"✅ ROSS v{ROSS_VERSION} opérationnel")
    else:
        st.sidebar.error("❌ ROSS non installé")
    
    st.sidebar.caption("RotoPédago v5.0 — ROSS-based")
    
    # --- Routing ---
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
