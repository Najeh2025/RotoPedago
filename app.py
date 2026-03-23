import streamlit as st
import ross as rs
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="RotoPédago - Expert Vibration", layout="wide")

st.title("🎓 RotoPédago : Laboratoire Virtuel de Rotodynamique")
st.markdown("""
Cette application est un outil pédagogique basé sur la bibliothèque open-source **ROSS**. 
Elle permet d'étudier la dynamique des machines tournantes : vitesses critiques, modes de vibration et diagramme de Campbell.
""")

# --- BARRE LATÉRALE : PARAMÈTRES DU SYSTÈME ---
st.sidebar.header("🛠️ Configuration du Rotor")

# Matériau
st.sidebar.subheader("1. Matériau (Acier par défaut)")
E = 211e9  # Pa
rho = 7850 # kg/m3
G = 81.2e9 # Pa

# Géométrie de l'arbre
st.sidebar.subheader("2. Géométrie de l'Arbre")
L_total = st.sidebar.slider("Longueur totale (m)", 0.2, 2.0, 1.0, step=0.1)
D_arbre = st.sidebar.slider("Diamètre de l'arbre (m)", 0.01, 0.1, 0.05)

# Disque
st.sidebar.subheader("3. Propriétés du Disque")
m_disque = st.sidebar.number_input("Masse du disque (kg)", 1.0, 50.0, 10.0)
pos_disque = st.sidebar.slider("Position du disque (m)", 0.0, L_total, L_total/2)

# Paliers
st.sidebar.subheader("4. Rigidité des Paliers (N/m)")
k_palier = st.sidebar.select_slider(
    "Rigidité (k)",
    options=[1e5, 1e6, 1e7, 1e8, 1e9],
    value=1e7
)
c_palier = 1e3 # Amortissement fixe pour simplification

# --- MOTEUR DE CALCUL ROSS ---
def create_rotor(L, D, m, pos, k, c):
    # Création de l'arbre (divisé en 10 éléments)
    n_elem = 10
    le = L / n_elem
    shaft_elements = [
        rs.ShaftElement(L=le, idl=0, odl=D, material=rs.Material(name="Steel", rho=rho, E=E, G_s=G))
        for _ in range(n_elem)
    ]
    
    # Ajout du disque (on trouve le noeud le plus proche de la position choisie)
    node_disque = int((pos / L) * n_elem)
    disks = [rs.DiskElement.from_geometry(n=node_disque, material=rs.Material(name="Steel", rho=rho, E=E, G_s=G), 
                                         width=0.05, i_d=0, o_d=D*4)] # Masse simplifiée par géométrie
    
    # Ajout des paliers aux extrémités
    bearings = [
        rs.BearingElement(n=0, kxx=k, cxx=c),
        rs.BearingElement(n=n_elem, kxx=k, cxx=c)
    ]
    
    return rs.Rotor(shaft_elements, disks, bearings)

rotor = create_rotor(L_total, D_arbre, m_disque, pos_disque, k_palier, c_palier)

# --- AFFICHAGE PRINCIPAL (ONGLETS) ---
tab1, tab2, tab3 = st.tabs(["🏗️ Modèle 3D", "📊 Diagramme de Campbell", "💡 Guide Pédagogique"])

with tab1:
    st.subheader("Visualisation du modèle par Éléments Finis")
    fig_static = rotor.plot_rotor()
    st.plotly_chart(fig_static, use_container_width=True)
    st.info(f"Le rotor est composé de {len(rotor.elements)} éléments. Le disque est placé au noeud correspondant à {pos_disque}m.")

with tab2:
    st.subheader("Analyse des Fréquences Propres")
    
    vitesse_max_rpm = st.number_input("Vitesse max pour l'analyse (RPM)", 5000, 50000, 20000)
    samples = np.linspace(0, vitesse_max_rpm * np.pi/30, 50)
    
    campbell = rotor.run_campbell(samples)
    fig_campbell = campbell.plot()
    
    st.plotly_chart(fig_campbell, use_container_width=True)
    
    st.success("""
    **Interprétation :**
    - Les lignes diagonales représentent les excitations (1x, 2x...).
    - Les intersections avec les courbes de fréquences propres indiquent les **Vitesses Critiques**.
    - Remarquez comment les modes se séparent (Forward/Backward) à cause de l'effet gyroscopique.
    """)

with tab3:
    st.header("Étude de cas : L'influence de la rigidité")
    st.write("""
    En tant qu'élève ingénieur, essayez de manipuler le curseur **'Rigidité (k)'** dans la barre latérale.
    
    **Questions de réflexion :**
    1. Si vous augmentez la rigidité des paliers, vers où se déplacent les vitesses critiques ?
    2. Pourquoi la première fréquence propre augmente-t-elle alors que la masse reste identique ?
    3. Quel est l'impact du diamètre de l'arbre sur la flèche statique (voir onglet Modèle) ?
    """)
    
    if k_palier < 1e6:
        st.warning("⚠️ Attention : Avec une rigidité faible, le rotor se comporte comme un corps rigide sur ses supports.")
    else:
        st.info("ℹ️ Note : Avec une rigidité élevée, les modes de flexion de l'arbre deviennent prédominants.")

# --- PIED DE PAGE ---
st.markdown("---")
st.caption(f"Développé pour le concours de promotion au grade de Professeur - Expert : Dynamique des Machines Tournantes.")
