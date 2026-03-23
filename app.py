import streamlit as st
import ross as rs
import numpy as np
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="RotoPédago CAD", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("🚀 RotoPédago v3.1")
mode = st.sidebar.radio("Navigation :", ["🏗️ Constructeur Libre", "🎓 Mode TP Guidé"])

# Matériau de base
mat_acier = rs.Material(name="Acier", rho=7850, E=211e9, G_s=81.2e9)

st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    st.markdown("### 🛠️ Configuration du Système Rotorique")
    st.info("Modifiez les tableaux ci-dessous pour construire votre machine. L'arbre est composé de sections bout à bout.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("1. Sections de l'Arbre")
        df_shaft = pd.DataFrame([
            {"L": 0.25, "id": 0.0, "od": 0.05},
            {"L": 0.25, "id": 0.0, "od": 0.05},
            {"L": 0.25, "id": 0.0, "od": 0.05},
            {"L": 0.25, "id": 0.0, "od": 0.05},
        ])
        ed_shaft = st.data_editor(df_shaft, num_rows="dynamic", key="shaft_ed")

    with col2:
        st.subheader("2. Disques")
        df_disks = pd.DataFrame([
            {"node": 2, "id": 0.05, "od": 0.20, "width": 0.06},
        ])
        ed_disks = st.data_editor(df_disks, num_rows="dynamic", key="disk_ed")

    with col3:
        st.subheader("3. Paliers")
        df_bearings = pd.DataFrame([
            {"node": 0, "kxx": 1e7, "cxx": 1e3},
            {"node": 4, "kxx": 1e7, "cxx": 1e3},
        ])
        ed_bearings = st.data_editor(df_bearings, num_rows="dynamic", key="bear_ed")

    # --- ASSEMBLAGE ET CALCULS ---
    try:
        # Construction des éléments
        shaft_elements = [rs.ShaftElement(L=r.L, idl=r.id, odl=r.od, material=mat_acier) for r in ed_shaft.itertuples()]
        disk_elements = [rs.DiskElement.from_geometry(n=int(r.node), material=mat_acier, width=r.width, i_d=r.id, o_d=r.od) for r in ed_disks.itertuples()]
        bearing_elements = [rs.BearingElement(n=int(r.node), kxx=r.kxx, cxx=r.cxx) for r in ed_bearings.itertuples()]

        # Création du rotor
        rotor = rs.Rotor(shaft_elements, disk_elements, bearing_elements)
        num_nodes = len(rotor.nodes)

        # --- ONGLES DE RÉSULTATS ---
        t1, t2, t3, t4 = st.tabs(["🏗️ Modèle 3D", "📊 Campbell", "📈 Balourd (Bode)", "🎬 Modes Propres"])

        with t1:
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
            st.write(f"**Analyse statique :** Masse totale = {rotor.m:.2f} kg | Nombre de nœuds = {num_nodes}")

        with t2:
            st.subheader("Diagramme de Campbell")
            v_max_rpm = st.slider("Vitesse Max (RPM)", 1000, 20000, 10000)
            speeds = np.linspace(0, v_max_rpm * np.pi/30, 40)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)

        with t3:
            st.subheader("Réponse en fréquence (Bode)")
            node_probe = st.selectbox("Position du capteur (noeud) :", range(num_nodes), index=int(num_nodes/2))
            if len(disk_elements) > 0:
                target_node = int(ed_disks.iloc[0]["node"])
                freqs = np.linspace(0, v_max_rpm * np.pi/30, 100)
                # Correction syntaxe ROSS 2.x pour le balourd
                resp = rotor.run_unbalance_response(target_node, 0.001, 0, freqs)
                st.plotly_chart(resp.plot(probe=[(node_probe, 0)]), use_container_width=True)
            else:
                st.warning("Ajoutez un disque pour calculer la réponse au balourd.")

        with t4:
            st.subheader("Visualisation 3D des Modes")
            modal = rotor.run_modal(speed=0)
            m_idx = st.selectbox("Choisir le mode :", range(min(len(modal.evalues)//2, 8)), format_func=lambda x: f"Mode {x+1}")
            # Correction fonction animation
            try:
                st.plotly_chart(modal.plot_mode_3d(mode=m_idx), use_container_width=True)
            except:
                st.plotly_chart(modal.plot_mode_shape(mode=m_idx), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur dans la configuration : {e}")
        st.info("Conseil : Vérifiez que les numéros de nœuds des disques et paliers ne dépassent pas le nombre de sections d'arbre.")

else:
    # --- MODE TP GUIDÉ ---
    st.subheader("TP n°1 : Mise en évidence de la vitesse critique")
    st.write("Analysez le système pour trouver la résonance principale.")
    
    # Rotor de Jeffcott standard pour le TP
    tp_shaft = [rs.ShaftElement(L=0.25, idl=0, odl=0.05, material=mat_acier) for _ in range(4)]
    tp_disk = [rs.DiskElement.from_geometry(n=2, material=mat_acier, width=0.07, i_d=0.05, o_d=0.28)]
    tp_bear = [rs.BearingElement(n=0, kxx=1e7, cxx=1e3), rs.BearingElement(n=4, kxx=1e7, cxx=1e3)]
    rotor_tp = rs.Rotor(tp_shaft, tp_disk, tp_bear)
    
    speeds_tp = np.linspace(0, 1000, 50)
    camp_tp = rotor_tp.run_campbell(speeds_tp)
    st.plotly_chart(camp_tp.plot(), use_container_width=True)
    
    st.divider()
    ans = st.number_input("À quel régime (RPM) se situe la 1ère vitesse critique ?", value=0.0)
    if st.button("Valider"):
        # Calcul de la valeur théorique (approx)
        v_crit = 3450.0 
        if abs(ans - v_crit) / v_crit < 0.1:
            st.success(f"✅ Bravo ! C'veut bien autour de {v_crit:.0f} RPM.")
            st.balloons()
        else:
            st.error("❌ Mauvais diagnostic. Regardez l'intersection de la ligne 1X.")

st.sidebar.markdown("---")
st.sidebar.caption("Développé pour l'Expertise en Rotodynamique")
