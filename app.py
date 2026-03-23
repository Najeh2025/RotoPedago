import streamlit as st
import ross as rs
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="RotoPédago - Expert", layout="wide")

# --- CSS PERSONNALISÉ POUR LE STYLE "PROFESSEUR" ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("🚀 Navigation")
mode = st.sidebar.radio("Choisir le mode :", ["🏗️ Constructeur Libre", "🎓 Mode TP Guidé"])

# --- BASE DE DONNÉES MATÉRIAUX (Section 4.1 du CDCF) ---
materials_db = {
    "Acier": {"E": 211e9, "rho": 7850, "G": 81.2e9},
    "Aluminium": {"E": 70e9, "rho": 2700, "G": 26e9},
    "Titane": {"E": 114e9, "rho": 4500, "G": 44e9}
}

# --- BARRE LATÉRALE : CONFIGURATION ---
st.sidebar.header("🛠️ Configuration")

if mode == "🎓 Mode TP Guidé":
    st.sidebar.info("**TP n°1 : Le Rotor de Jeffcott**\nObjectif : Identifier la première vitesse critique.")
    # On verrouille certains paramètres pour le TP
    mat_choice = "Acier"
    L_total = 1.0
    D_arbre = 0.05
    st.sidebar.text(f"Matériau : {mat_choice}")
    st.sidebar.text(f"Longueur : {L_total} m")
    st.sidebar.text(f"Diamètre : {D_arbre} m")
else:
    mat_choice = st.sidebar.selectbox("Matériau de l'arbre", list(materials_db.keys()))
    L_total = st.sidebar.slider("Longueur de l'arbre (m)", 0.5, 2.0, 1.0)
    D_arbre = st.sidebar.slider("Diamètre de l'arbre (m)", 0.02, 0.1, 0.05)

m_disque = st.sidebar.number_input("Masse du disque (kg)", 1.0, 50.0, 10.0)
pos_disque = st.sidebar.slider("Position du disque (m)", 0.0, L_total, L_total/2)
k_palier = st.sidebar.select_slider("Rigidité Paliers (N/m)", options=[1e6, 1e7, 1e8], value=1e7)

# --- MOTEUR DE CALCUL ROSS ---
def build_rotor():
    mat = rs.Material(name=mat_choice, rho=materials_db[mat_choice]['rho'], 
                      E=materials_db[mat_choice]['E'], G_s=materials_db[mat_choice]['G'])
    n_elem = 20
    shaft = [rs.ShaftElement(L=L_total/n_elem, idl=0, odl=D_arbre, material=mat) for _ in range(n_elem)]
    
    # Disque
    node_d = int((pos_disque / L_total) * n_elem)
    disks = [rs.DiskElement.from_geometry(n=node_d, material=mat, width=0.07, i_d=0, o_d=D_arbre*4)]
    
    # Paliers
    bearings = [rs.BearingElement(n=0, kxx=k_palier, cxx=1e3), 
                rs.BearingElement(n=n_elem, kxx=k_palier, cxx=1e3)]
    
    return rs.Rotor(shaft, disks, bearings)

rotor = build_rotor()

# --- AFFICHAGE PRINCIPAL ---
st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    t1, t2, t3 = st.tabs(["📊 Analyses", "🎬 Animation des Modes", "📝 Rapport"])
    
    with t1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Modèle Géométrique")
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
        with col2:
            st.subheader("Diagramme de Campbell")
            campbell = rotor.run_campbell(np.linspace(0, 2000, 50))
            st.plotly_chart(campbell.plot(), use_container_width=True)
            
    with t2:
        st.subheader("Animation 3D des Modes Propres")
        mode_idx = st.selectbox("Choisir le mode à visualiser", [0, 1, 2], format_func=lambda x: f"Mode n°{x+1}")
        # Calcul modal
        modal = rotor.run_modal(speed=0)
        fig_mode = modal.plot_mode_shape(mode=mode_idx)
        st.plotly_chart(fig_mode, use_container_width=True)
        st.info("Utilisez la souris pour faire pivoter le rotor et observer la déformée.")

    with t3:
        st.subheader("Résumé Technique")
        st.write(rotor.summary())

else:
    # --- INTERFACE TP GUIDÉ ---
    st.subheader("Exercice : Analyse d'un rotor suspendu")
    st.write("Analysez le diagramme de Campbell ci-dessous pour trouver la première vitesse critique (intersection 1X).")
    
    campbell = rotor.run_campbell(np.linspace(0, 1000, 50))
    st.plotly_chart(campbell.plot(), use_container_width=True)
    
    # Calcul de la valeur réelle pour vérification
    v_critique_reelle = campbell.critical_speeds()[0] # Rad/s
    v_critique_rpm = v_critique_reelle * 30 / np.pi
    
    st.divider()
    st.subheader("📝 Votre réponse")
    user_answer = st.number_input("Quelle est la 1ère vitesse critique en RPM ?", value=0.0)
    
    if st.button("Valider la réponse"):
        erreur = abs(user_answer - v_critique_rpm) / v_critique_rpm
        if erreur < 0.05: # 5% de marge d'erreur
            st.success(f"✅ Bravo ! La valeur exacte est {v_critique_rpm:.1f} RPM. Vous avez bien identifié l'intersection.")
            st.balloons()
        else:
            st.error(f"❌ Ce n'est pas tout à fait ça. Regardez bien l'intersection entre la droite 1X et la première courbe bleue.")

# --- FOOTER ---
st.markdown("---")
st.caption("Application développée pour le concours de Professeur Universitaire - Basée sur ROSS Library.")
