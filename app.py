import streamlit as st
import ross as rs
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="RotoPédago Pro", layout="wide")

# Style pour améliorer le contraste
st.markdown("""<style> .stTabs [data-baseweb="tab-list"] { gap: 24px; } 
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
    </style>""", unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("🚀 RotoPédago v2.1")
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

# --- CALCUL DU ROTOR ---
@st.cache_resource # Pour éviter de recalculer si les paramètres ne changent pas
def get_rotor(L, D, m, pos, k, mat_name):
    mat = rs.Material(name=mat_name, rho=materials_db[mat_name]['rho'], 
                      E=materials_db[mat_name]['E'], G_s=materials_db[mat_name]['G'])
    n_elem = 10
    shaft = [rs.ShaftElement(L=L/n_elem, idl=0, odl=D, material=mat) for _ in range(n_elem)]
    node_d = int((pos / L) * n_elem)
    disks = [rs.DiskElement.from_geometry(n=node_d, material=mat, width=0.06, i_d=0, o_d=D*4)]
    bearings = [rs.BearingElement(n=0, kxx=k, cxx=1e3), rs.BearingElement(n=n_elem, kxx=k, cxx=1e3)]
    return rs.Rotor(shaft, disks, bearings)

rotor = get_rotor(L_total, D_arbre, m_disque, pos_disque, k_palier, mat_choice)

# --- INTERFACE ---
st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    t1, t2, t3, t4 = st.tabs(["🏗️ Modèle", "📊 Campbell", "📈 Balourd (Bode)", "🎬 Modes 3D"])
    
    with t1:
        st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
        st.write(rotor.summary())
        
    with t2:
        with st.spinner('Calcul du diagramme de Campbell...'):
            speeds = np.linspace(0, 1500, 40)
            fig_camp = rotor.run_campbell(speeds).plot()
            st.plotly_chart(fig_camp, use_container_width=True)

    with t3:
        st.subheader("Réponse au Balourd (Amplitude & Phase)")
        with st.spinner('Simulation du balourd...'):
            # On place un balourd sur le disque (0.01 kg.m)
            node_d = int((pos_disque / L_total) * 10)
            resp = rotor.run_unbalance_response(node=node_d, unbalance=0.01, frequency=np.linspace(0, 1500, 100))
            fig_bode = resp.plot(probe=[(node_d, 0)]) # Sonde sur le disque
            st.plotly_chart(fig_bode, use_container_width=True)

    with t4:
        st.subheader("Animation du Mode Propre")
        m_idx = st.selectbox("Mode :", [0, 1, 2], format_func=lambda x: f"Mode {x+1}")
        fig_modal = rotor.run_modal(speed=0).plot_mode_shape(mode=m_idx)
        st.plotly_chart(fig_modal, use_container_width=True)

else:
    # --- MODE TP ---
    st.subheader("TP n°1 : Identification de la vitesse critique")
    st.markdown("Observez le diagramme de Campbell ci-dessous. À quel régime (RPM) la droite **1X** croise-t-elle le **premier mode** ?")
    
    with st.spinner('Génération des données TP...'):
        speeds_tp = np.linspace(0, 1200, 40)
        camp_tp = rotor.run_campbell(speeds_tp)
        st.plotly_chart(camp_tp.plot(), use_container_width=True)
    
    # Calcul de la vérité terrain
    v_crit_rad = camp_tp.critical_speeds()[0]
    v_crit_rpm = v_crit_rad * 30 / np.pi
    
    st.divider()
    ans = st.number_input("Entrez votre réponse en RPM :", value=0.0)
    if st.button("Vérifier"):
        error = abs(ans - v_crit_rpm) / v_crit_rpm
        if error < 0.05:
            st.success(f"✅ Correct ! La vitesse critique est de {v_crit_rpm:.0f} RPM.")
            st.balloons()
        else:
            st.error(f"❌ Erreur. Indice : regardez l'intersection vers {v_crit_rpm:.0f} RPM.")

st.sidebar.markdown("---")
st.sidebar.caption("Développé pour l'Expertise en Vibrations Mécaniques.")
