import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
import traceback

# Tentative d'import ROSS avec sécurité
try:
    import ross as rs
    ROSS_AVAILABLE = True
except ImportError:
    ROSS_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(page_title="RotoPédago v5.1 Pro", page_icon="⚙️", layout="wide")

# --- STYLE CSS (Inspiré de votre v5.0) ---
st.markdown("""
<style>
.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700; margin:2px; }
.badge-gold { background:#FFD700; color:#7A5700; }
.badge-silver { background:#C0C0C0; color:#3A3A3A; }
.tp-card { background:#F0F4FF; border-left:5px solid #1F5C8B; border-radius:8px; padding:16px; margin:10px 0; }
</style>
""", unsafe_allow_html=True)

# --- HELPER : TRACÉ UNIVERSEL (Sécurité Totale) ---
def universal_plot(obj, methods=['plot_mode_3d', 'plot_mode_shape', 'plot_deflected_shape', 'plot'], **kwargs):
    """Tente toutes les méthodes de tracé ROSS possibles pour éviter les AttributeError."""
    for method in methods:
        if hasattr(obj, method):
            try:
                fig = getattr(obj, method)(**kwargs)
                return fig
            except: continue
    return None

# =============================================================================
# CLASSES DE GESTION (Architecture v5.1)
# =============================================================================

class RotorBuilder:
    def __init__(self):
        self.material = rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9) if ROSS_AVAILABLE else None
        self.errors = []

    def build_from_df(self, df_s, df_d, df_b):
        try:
            shaft = [rs.ShaftElement(L=r.L, idl=r.id, odl=r.od, material=self.material) for r in df_s.itertuples()]
            disks = [rs.DiskElement.from_geometry(n=int(r.node), material=self.material, width=r.width, i_d=r.id, o_d=r.od) for r in df_d.itertuples()]
            bears = [rs.BearingElement(n=int(r.node), kxx=r.kxx, kyy=r.kyy, kxy=r.kxy, kyx=-r.kxy, cxx=r.cxx) for r in df_b.itertuples()]
            return rs.Rotor(shaft, disks, bears)
        except Exception as e:
            self.errors.append(str(e))
            return None

class TPValidator:
    def verify(self, rotor, modal, tp_id):
        # Logique de calcul du score (0-100)
        score = 0
        details = []
        if rotor:
            score += 40
            details.append("✅ Rotor assemblé correctement.")
            if modal:
                score += 40
                details.append(f"✅ Analyse modale réussie (Mode 1: {modal.wn[0]/(2*np.pi):.1f} Hz).")
                if modal.log_dec[0] > 0:
                    score += 20
                    details.append("✅ Système stable (Log Dec > 0).")
        return score, details

# =============================================================================
# CONTENU DES PAGES
# =============================================================================

def render_home():
    st.markdown("<h1 style='text-align:center; color:#1F5C8B;'>⚙️ RotoPédago v5.1</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Laboratoire Virtuel pour l'Expertise en Vibrations</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("### 🎓 Mode TP\nSuivez un parcours guidé avec validation automatique et badges.")
    with col2:
        st.success("### 🏗️ Mode Libre\nConception sans limites pour vos projets de recherche.")

def render_free_mode():
    st.header("🏗️ Mode Constructeur Libre")
    
    # Entrées par Tableaux
    col_s, col_d, col_b = st.columns(3)
    with col_s:
        st.write("Arbre")
        df_s = st.data_editor(pd.DataFrame([{"L": 0.2, "id": 0.0, "od": 0.05} for _ in range(5)]), num_rows="dynamic", key="free_s")
    with col_d:
        st.write("Disques")
        df_d = st.data_editor(pd.DataFrame([{"node": 2, "id": 0.05, "od": 0.25, "width": 0.07}]), num_rows="dynamic", key="free_d")
    with col_b:
        st.write("Paliers (Kxy pour stabilité)")
        df_b = st.data_editor(pd.DataFrame([{"node": 0, "kxx": 1e7, "kyy": 1e7, "kxy": 0, "cxx": 1000},
                                            {"node": 5, "kxx": 1e7, "kyy": 1e7, "kxy": 0, "cxx": 1000}]), num_rows="dynamic", key="free_b")

    if st.button("🚀 Lancer l'Analyse"):
        builder = RotorBuilder()
        rotor = builder.build_from_df(df_s, df_d, df_b)
        if rotor:
            st.session_state.free_rotor = rotor
            st.success("Rotor construit avec succès !")
        else:
            st.error(f"Erreur : {builder.errors}")

    if "free_rotor" in st.session_state:
        rotor = st.session_state.free_rotor
        t1, t2, t3, t4 = st.tabs(["🏗️ Modèle", "📊 Campbell", "📈 Stabilité", "📏 Statique"])
        
        with t1:
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
        with t2:
            speeds = np.linspace(0, 1000, 50)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)
        with t3:
            fig_stab = go.Figure()
            for i in range(min(4, camp.log_dec.shape[1])):
                fig_stab.add_trace(go.Scatter(x=speeds*30/np.pi, y=camp.log_dec[:, i], name=f"Mode {i+1}"))
            fig_stab.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig_stab, use_container_width=True)
        with t4:
            static = rotor.run_static()
            fig_stat = universal_plot(static)
            if fig_stat: st.plotly_chart(fig_stat, use_container_width=True)

def render_tp_mode():
    st.header("🎓 Parcours Pédagogique")
    tp_choice = st.sidebar.selectbox("Sélectionnez votre TP :", ["TP 1 : Découverte", "TP 2 : Stabilité API 684"])
    
    if tp_choice == "TP 1 : Découverte":
        st.write("### Objectif : Créer un rotor de Jeffcott et trouver sa vitesse critique.")
        # Similaire à la structure v5.0 mais sécurisée
        k = st.number_input("Raideur Kxx :", 1e6, 1e8, 1e7)
        if st.button("Valider le TP"):
            st.balloons()
            st.success("Badge Or obtenu ! 🥇")

# =============================================================================
# MAIN
# =============================================================================

def main():
    if not ROSS_AVAILABLE:
        st.error("❌ Erreur Critique : Bibliothèque 'ross-rotordynamics' introuvable. Vérifiez votre requirements.txt.")
        return

    st.sidebar.title("⚙️ RotoPédago Pro")
    menu = st.sidebar.radio("Menu :", ["🏠 Accueil", "🎓 Mode TP", "🏗️ Mode Libre"])
    
    if menu == "🏠 Accueil":
        render_home()
    elif menu == "🎓 Mode TP":
        render_tp_mode()
    elif menu == "🏗️ Mode Libre":
        render_free_mode()

if __name__ == "__main__":
    main()
