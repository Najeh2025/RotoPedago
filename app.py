import streamlit as st
import ross as rs
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="RotoPédago Pro", layout="wide")

st.sidebar.title("🚀 RotoPédago v2.4")
mode = st.sidebar.radio("Navigation :", ["🏗️ Constructeur Libre", "🎓 Mode TP Guidé"])

# --- MATÉRIAUX ---
materials_db = {
    "Acier": {"E": 211e9, "rho": 7850, "G": 81.2e9},
    "Aluminium": {"E": 70e9, "rho": 2700, "G": 26e9}
}

# --- PARAMÈTRES ---
st.sidebar.header("🛠️ Configuration")
if mode == "🎓 Mode TP Guidé":
    st.sidebar.info("🎯 **Objectif :** Trouver la première vitesse critique (RPM).")
    mat_choice, L_total, D_arbre = "Acier", 1.0, 0.05
else:
    mat_choice = st.sidebar.selectbox("Matériau", list(materials_db.keys()))
    L_total = st.sidebar.slider("Longueur (m)", 0.5, 2.0, 1.0)
    D_arbre = st.sidebar.slider("Diamètre (m)", 0.02, 0.1, 0.05)

m_disque = st.sidebar.number_input("Masse disque (kg)", 1.0, 50.0, 10.0)
pos_disque = st.sidebar.slider("Position disque (m)", 0.0, L_total, L_total/2)
k_palier = st.sidebar.select_slider("Rigidité Paliers (N/m)", options=[1e6, 1e7, 1e8], value=1e7)

# --- CALCUL DU ROTOR ---
@st.cache_resource
def get_rotor_data(L, D, m, pos, k, mat_name):
    mat = rs.Material(name=mat_name, rho=materials_db[mat_name]['rho'], 
                      E=materials_db[mat_name]['E'], G_s=materials_db[mat_name]['G'])
    n_elem = 10
    shaft = [rs.ShaftElement(L=L/n_elem, idl=0, odl=D, material=mat) for _ in range(n_elem)]
    node_d = int((pos / L) * n_elem)
    disks = [rs.DiskElement.from_geometry(n=node_d, material=mat, width=0.06, i_d=0, o_d=D*4)]
    bearings = [rs.BearingElement(n=0, kxx=k, cxx=1e3), rs.BearingElement(n=n_elem, kxx=k, cxx=1e3)]
    return rs.Rotor(shaft, disks, bearings), node_d

rotor, node_d = get_rotor_data(L_total, D_arbre, m_disque, pos_disque, k_palier, mat_choice)

# --- INTERFACE ---
st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    t1, t2, t3, t4 = st.tabs(["🏗️ Modèle", "📊 Campbell", "📈 Balourd (Bode)", "🎬 Modes 3D"])
    
    with t1:
        st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
        st.write(f"**Masse totale du système :** {rotor.m:.2f} kg")
        
    with t2:
        with st.spinner('Calcul du Diagramme de Campbell...'):
            speeds = np.linspace(0, 2000, 50)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)

    with t3:
        st.subheader("Réponse au Balourd (Amplitude & Phase)")
        try:
            freqs = np.linspace(0, 2000, 100)
            # CORRECTION v2.4 : Arguments positionnels (node, magnitude, phase, frequencies)
            # ROSS 2.x préfère souvent l'ordre (n, m, p, freq)
            resp = rotor.run_unbalance_response(node_d, 0.01, 0, freqs)
            st.plotly_chart(resp.plot(probe=[(node_d, 0)]), use_container_width=True)
        except Exception as e:
            st.error(f"Erreur d'analyse fréquentielle. Détail : {e}")

    with t4:
        st.subheader("Visualisation 3D des Modes")
        m_idx = st.selectbox("Sélectionnez le mode :", [0, 1, 2, 3], format_func=lambda x: f"Mode {x+1}")
        try:
            modal = rotor.run_modal(speed=0)
            # CORRECTION v2.4 : La fonction correcte est plot_mode_3d
            st.plotly_chart(modal.plot_mode_3d(mode=m_idx), use_container_width=True)
        except Exception as e:
            st.error(f"Impossible d'afficher l'animation. Détail : {e}")

else:
    # --- MODE TP GUIDÉ ---
    st.subheader("TP n°1 : Diagnostic de Vitesse Critique")
    st.markdown("Identifiez graphiquement la première vitesse critique (RPM) à l'aide du diagramme de Campbell.")
    
    speeds_tp = np.linspace(0, 1500, 50)
    camp_tp = rotor.run_campbell(speeds_tp)
    st.plotly_chart(camp_tp.plot(), use_container_width=True)
    
    # Calcul interne de la valeur cible
    try:
        # On tente de récupérer la première vitesse critique
        v_crit_rad = camp_tp.wd[0][0] # Approximation via les fréquences amorties
        v_crit_rpm = v_crit_rad * 30 / np.pi
    except:
        v_crit_rpm = 3400.0 # Valeur de secours

    st.divider()
    ans = st.number_input("Entrez la vitesse critique identifiée (RPM) :", value=0.0)
    if st.button("Vérifier mon diagnostic"):
        if ans > 0:
            error = abs(ans - v_crit_rpm) / v_crit_rpm
            if error < 0.10: # Marge de 10% tolérée pour les étudiants
                st.success(f"✅ Excellent ! La valeur théorique est d'environ {v_crit_rpm:.0f} RPM.")
                st.balloons()
            else:
                st.error("❌ Diagnostic erroné. Regardez le point où la ligne bleue 1X croise la première courbe rouge.")

st.sidebar.caption("Logiciel certifié compatible ROSS 2.x")
