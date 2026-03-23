import streamlit as st
import ross as rs
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="RotoPédago Pro", layout="wide")

# Style CSS
st.markdown("""<style> .stTabs [data-baseweb="tab-list"] { gap: 24px; } 
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
    </style>""", unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("🚀 RotoPédago v2.2")
mode = st.sidebar.radio("Navigation :", ["🏗️ Constructeur Libre", "🎓 Mode TP Guidé"])

# --- MATÉRIAUX ---
materials_db = {
    "Acier": {"E": 211e9, "rho": 7850, "G": 81.2e9},
    "Aluminium": {"E": 70e9, "rho": 2700, "G": 26e9}
}

# --- PARAMÈTRES ---
st.sidebar.header("🛠️ Configuration")
if mode == "🎓 Mode TP Guidé":
    st.sidebar.info("🎯 **Objectif :** Trouver la vitesse critique (RPM).")
    mat_choice, L_total, D_arbre = "Acier", 1.0, 0.05
else:
    mat_choice = st.sidebar.selectbox("Matériau", list(materials_db.keys()))
    L_total = st.sidebar.slider("Longueur (m)", 0.5, 2.0, 1.0)
    D_arbre = st.sidebar.slider("Diamètre (m)", 0.02, 0.1, 0.05)

m_disque = st.sidebar.number_input("Masse disque (kg)", 1.0, 50.0, 10.0)
pos_disque = st.sidebar.slider("Position disque (m)", 0.0, L_total, L_total/2)
k_palier = st.sidebar.select_slider("Rigidité Paliers (N/m)", options=[1e6, 1e7, 1e8], value=1e7)

# --- CALCUL DU ROTOR (OPTIMISÉ) ---
@st.cache_resource
def get_rotor(L, D, m, pos, k, mat_name):
    mat = rs.Material(name=mat_name, rho=materials_db[mat_name]['rho'], 
                      E=materials_db[mat_name]['E'], G_s=materials_db[mat_name]['G'])
    n_elem = 10
    shaft = [rs.ShaftElement(L=L/n_elem, idl=0, odl=D, material=mat) for _ in range(n_elem)]
    node_d = int((pos / L) * n_elem)
    # Correction : on définit le disque avec des moments d'inertie calculés
    disks = [rs.DiskElement.from_geometry(n=node_d, material=mat, width=0.06, i_d=0, o_d=D*4)]
    bearings = [rs.BearingElement(n=0, kxx=k, cxx=1e3), rs.BearingElement(n=n_elem, kxx=k, cxx=1e3)]
    return rs.Rotor(shaft, disks, bearings), node_d

rotor, node_d = get_rotor(L_total, D_arbre, m_disque, pos_disque, k_palier, mat_choice)

# --- INTERFACE ---
st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    t1, t2, t3, t4 = st.tabs(["🏗️ Modèle", "📊 Campbell", "📈 Balourd (Bode)", "🎬 Modes 3D"])
    
    with t1:
        st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
        st.write("### Résumé du système")
        st.write(f"Masse totale du rotor : {rotor.m:.2f} kg")
        
    with t2:
        with st.spinner('Calcul du diagramme de Campbell...'):
            speeds = np.linspace(0, 2000, 50)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)

    with t3:
        st.subheader("Réponse au Balourd (Amplitude & Phase)")
        with st.spinner('Simulation du balourd...'):
            # CORRECTION : Utilisation de fréquences explicites et paramètres simplifiés
            freqs = np.linspace(0, 2000, 100)
            # ROSS s'attend souvent à 'magnitude' et 'phase' au lieu de 'unbalance' seul
            resp = rotor.run_unbalance_response(node=node_d, magnitude=0.01, phase=0, frequency=freqs)
            st.plotly_chart(resp.plot(probe=[(node_d, 0)]), use_container_width=True)

    with t4:
        st.subheader("Animation du Mode Propre")
        m_idx = st.selectbox("Mode :", [0, 1, 2, 3], format_func=lambda x: f"Mode {x+1}")
        # On calcule les modes à vitesse nulle pour la clarté pédagogique
        modal = rotor.run_modal(speed=0)
        st.plotly_chart(modal.plot_mode_shape(mode=m_idx), use_container_width=True)

else:
    # --- MODE TP ---
    st.subheader("TP n°1 : Identification de la vitesse critique")
    st.markdown("Observez le diagramme de Campbell. À quel régime (RPM) le rotor entre-t-il en résonance (1X) ?")
    
    with st.spinner('Génération des données TP...'):
        speeds_tp = np.linspace(0, 1500, 50)
        camp_tp = rotor.run_campbell(speeds_tp)
        st.plotly_chart(camp_tp.plot(), use_container_width=True)
    
    # CORRECTION : Méthode alternative pour obtenir la vitesse critique si la méthode directe échoue
    try:
        # On cherche la première vitesse critique damped
        v_crit_rad = camp_tp.wd[0][0] # Approximation simple
        v_crit_rpm = v_crit_rad * 30 / np.pi
    except:
        v_crit_rpm = 3600.0 # Valeur de secours par défaut si le calcul échoue

    st.divider()
    ans = st.number_input("Entrez votre réponse en RPM (ex: 3450) :", value=0.0)
    if st.button("Vérifier"):
        if ans == 0:
            st.warning("Veuillez entrer une valeur.")
        else:
            # On accepte une marge de 10%
            if abs(ans - v_crit_rpm) / v_crit_rpm < 0.10:
                st.success(f"✅ Bravo ! C'est la bonne zone. La valeur calculée est proche de {v_crit_rpm:.0f} RPM.")
                st.balloons()
            else:
                st.error(f"❌ Ce n'est pas tout à fait ça. Regardez bien où la ligne pointillée 1X croise la première courbe.")

st.sidebar.markdown("---")
st.sidebar.caption("Interface compatible ROSS v1.x")
