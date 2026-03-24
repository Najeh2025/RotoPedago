import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
import traceback

# --- 1. TENTATIVE D'IMPORT ROSS ---
try:
    import ross as rs
    ROSS_AVAILABLE = True
except ImportError:
    ROSS_AVAILABLE = False

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="RotoPédago v5.2 Expert",
    page_icon="⚙️",
    layout="wide"
)

# --- 3. STYLE CSS PROFESSIONNEL ---
st.markdown("""
<style>
.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700; margin:2px; }
.badge-gold { background:#FFD700; color:#7A5700; }
.badge-silver { background:#C0C0C0; color:#3A3A3A; }
.tp-card { background:#F0F4FF; border-left:5px solid #1F5C8B; border-radius:8px; padding:16px; margin:10px 0; }
.status-ok { background:#E6FFE6; border:1px solid #22863A; border-radius:6px; padding:10px; }
.status-err { background:#FFE6E6; border:1px solid #C00000; border-radius:6px; padding:10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. FONCTION DE TRACÉ UNIVERSELLE (SÉCURITÉ) ---
def safe_plot(obj, methods=['plot_mode_3d', 'plot_mode_shape', 'plot_deflected_shape', 'plot'], **kwargs):
    """Détecte dynamiquement la méthode de tracé disponible selon la version de ROSS"""
    for method in methods:
        if hasattr(obj, method):
            try:
                fig = getattr(obj, method)(**kwargs)
                # S'assurer que c'est un objet Plotly
                if fig: return fig
            except: continue
    return None

# =============================================================================
# CLASSES MOTEUR (ARCHITECTURE v5.2)
# =============================================================================

class RotorBuilder:
    def __init__(self):
        self.mat = rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9) if ROSS_AVAILABLE else None

    def build_custom(self, df_s, df_d, df_b):
        try:
            shaft = [rs.ShaftElement(L=r.L, idl=r.id, odl=r.od, material=self.mat) for r in df_s.itertuples()]
            disks = [rs.DiskElement.from_geometry(n=int(r.node), material=self.mat, width=r.width, i_d=r.id, o_d=r.od) for r in df_d.itertuples()]
            # Support des coefficients croisés Kxy pour l'expertise
            bears = [rs.BearingElement(n=int(r.node), kxx=r.kxx, kyy=getattr(r, 'kyy', r.kxx), 
                                        kxy=getattr(r, 'kxy', 0), kyx=-getattr(r, 'kxy', 0), 
                                        cxx=r.cxx) for r in ed_b.itertuples()]
            return rs.Rotor(shaft, disks, bears)
        except Exception as e:
            st.error(f"Erreur d'assemblage : {e}")
            return None

# =============================================================================
# PAGES DE L'APPLICATION
# =============================================================================

def render_home():
    st.markdown("<h1 style='text-align:center; color:#1F5C8B;'>⚙️ RotoPédago v5.2</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:1.2em;'>Laboratoire Virtuel de Rotodynamique pour l'Enseignement Supérieur</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='tp-card'><h3>🎓 Mode TP</h3><p>3 niveaux progressifs avec validation API 684 et badges.</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='tp-card'><h3>🏗️ Mode Libre</h3><p>Conception avancée par éléments finis (Timoshenko).</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='tp-card'><h3>📚 Documentation</h3><p>Théorie vibratoire et guide de l'utilisateur ROSS.</p></div>", unsafe_allow_html=True)

def render_free_mode():
    st.header("🏗️ Mode Constructeur Libre (Expert)")
    
    # Tableaux de conception
    col_s, col_d, col_b = st.columns(3)
    with col_s:
        st.subheader("1. Sections Arbre")
        df_s = st.data_editor(pd.DataFrame([{"L": 0.2, "id": 0.0, "od": 0.05} for _ in range(5)]), num_rows="dynamic", key="free_s")
    with col_d:
        st.subheader("2. Disques")
        df_d = st.data_editor(pd.DataFrame([{"node": 2, "id": 0.05, "od": 0.25, "width": 0.07}]), num_rows="dynamic", key="free_d")
    with col_b:
        st.subheader("3. Paliers")
        df_b = st.data_editor(pd.DataFrame([{"node": 0, "kxx": 1e7, "kyy": 1e7, "kxy": 0, "cxx": 1000},
                                            {"node": 5, "kxx": 1e7, "kyy": 1e7, "kxy": 0, "cxx": 1000}]), num_rows="dynamic", key="free_b")

    if st.button("🚀 Lancer l'Analyse Complète", type="primary"):
        with st.spinner("Calculs EF en cours..."):
            builder = RotorBuilder()
            # Reconstruction sécurisée
            try:
                shaft = [rs.ShaftElement(L=r.L, idl=r.id, odl=r.od, material=builder.mat) for r in df_s.itertuples()]
                disks = [rs.DiskElement.from_geometry(n=int(r.node), material=builder.mat, width=r.width, i_d=r.id, o_d=r.od) for r in df_d.itertuples()]
                bears = [rs.BearingElement(n=int(r.node), kxx=r.kxx, kyy=r.kyy, kxy=r.kxy, kyx=-r.kxy, cxx=r.cxx) for r in df_b.itertuples()]
                st.session_state.rotor = rs.Rotor(shaft, disks, bears)
            except Exception as e:
                st.error(f"Erreur : {e}")

    if "rotor" in st.session_state:
        rotor = st.session_state.rotor
        tabs = st.tabs(["🏗️ Modèle", "📊 Campbell", "📉 Stabilité", "📏 Statique", "🎬 Animation"])
        
        with tabs[0]:
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
            st.metric("Masse totale", f"{rotor.m:.2f} kg")
        
        with tabs[1]:
            v_max = st.slider("Vitesse (RPM)", 1000, 20000, 10000)
            camp = rotor.run_campbell(np.linspace(0, v_max * np.pi/30, 50))
            st.plotly_chart(camp.plot(), use_container_width=True)
            
        with tabs[2]:
            st.subheader("Analyse du Décrément Logarithmique (Stability)")
            fig_stab = go.Figure()
            for i in range(min(4, camp.log_dec.shape[1])):
                fig_stab.add_trace(go.Scatter(x=np.linspace(0, v_max, 50), y=camp.log_dec[:, i], name=f"Mode {i+1}"))
            fig_stab.add_hline(y=0, line_dash="dash", line_color="red")
            fig_stab.update_layout(xaxis_title="Vitesse (RPM)", yaxis_title="Log Dec")
            st.plotly_chart(fig_stab, use_container_width=True)
            
        with tabs[3]:
            st.subheader("Flèche Statique sous Propre Poids")
            static = rotor.run_static()
            fig_stat = safe_plot(static)
            if fig_stat: st.plotly_chart(fig_stat, use_container_width=True)
            
        with tabs[4]:
            modal = rotor.run_modal(speed=0)
            m_idx = st.selectbox("Sélection du Mode :", range(min(len(modal.evalues)//2, 6)))
            fig_anim = safe_plot(modal, mode=m_idx)
            if fig_anim: st.plotly_chart(fig_anim, use_container_width=True)

def render_tp_mode():
    st.title("🎓 Mode TP - Guide Interactif")
    level = st.sidebar.selectbox("Niveau", ["1. Découverte", "2. Maîtrise", "3. Expertise (API 684)"])
    
    if "1" in level:
        st.markdown("<div class='tp-card'><h3>TP 1.1 : Le Rotor de Jeffcott</h3><p>Objectif : Modéliser un rotor simple et identifier sa 1ère vitesse critique.</p></div>", unsafe_allow_html=True)
        # Logique de validation
        ans = st.number_input("Entrez la vitesse critique trouvée (RPM) :", value=0.0)
        if st.button("Valider"):
            if 3400 < ans < 3600:
                st.success("Correct ! Vous avez obtenu le badge Bronze 🥉")
                st.session_state.badges["TP1.1"] = "bronze"
            else:
                st.error("Incorrect. Vérifiez l'intersection sur le Campbell.")

    elif "3" in level:
        st.markdown("<div class='tp-card'><h3>TP 3.1 : Conformité API 684</h3><p>Objectif : Vérifier si le rotor respecte la marge de séparation de 15%.</p></div>", unsafe_allow_html=True)
        st.info("Utilisez le Mode Libre pour tester vos designs industriels.")

# =============================================================================
# MAIN
# =============================================================================

def main():
    if not ROSS_AVAILABLE:
        st.error("ROSS introuvable. Veuillez vérifier votre requirements.txt.")
        return

    if "badges" not in st.session_state: st.session_state.badges = {}
    
    st.sidebar.title("⚙️ RotoPédago Pro")
    menu = st.sidebar.radio("Navigation", ["🏠 Accueil", "🎓 Mode TP", "🏗️ Mode Libre"])
    
    if st.session_state.badges:
        st.sidebar.write("🏅 Mes Badges :")
        for k, v in st.session_state.badges.items():
            st.sidebar.markdown(f"- {k} : {v}")

    if menu == "🏠 Accueil": render_home()
    elif menu == "🎓 Mode TP": render_tp_mode()
    elif menu == "🏗️ Mode Libre": render_free_mode()

if __name__ == "__main__":
    main()
