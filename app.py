import streamlit as st
import ross as rs
import numpy as np
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="RotoPédago CAD", layout="wide")

st.sidebar.title("🚀 RotoPédago v3.0")
mode = st.sidebar.radio("Navigation :", ["🏗️ Constructeur Libre", "🎓 Mode TP Guidé"])

# --- MATÉRIAUX ---
mat_acier = rs.Material(name="Acier", rho=7850, E=211e9, G_s=81.2e9)

# --- INTERFACE PRINCIPALE ---
st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    st.markdown("### 🛠️ Configuration du Système Rotorique")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("1. Arbre (Shaft Elements)")
        st.caption("Définissez les sections de l'arbre [Longueur, Diam Int, Diam Ext]")
        # Tableau éditable pour l'arbre
        df_shaft = pd.DataFrame(
            [
                {"L": 0.25, "id": 0.0, "od": 0.05},
                {"L": 0.25, "id": 0.0, "od": 0.05},
                {"L": 0.25, "id": 0.0, "od": 0.05},
                {"L": 0.25, "id": 0.0, "od": 0.05},
            ]
        )
        ed_shaft = st.data_editor(df_shaft, num_rows="dynamic", key="shaft_table")

    with col2:
        st.subheader("2. Disques (Disks)")
        st.caption("Positionnez les disques [Noeud, Diam Int, Diam Ext, Largeur]")
        df_disks = pd.DataFrame(
            [
                {"node": 2, "id": 0.05, "od": 0.20, "width": 0.06},
            ]
        )
        ed_disks = st.data_editor(df_disks, num_rows="dynamic", key="disk_table")

    with col3:
        st.subheader("3. Paliers (Bearings)")
        st.caption("Ajoutez les paliers [Noeud, Raideur Kxx, Amortissement Cxx]")
        df_bearings = pd.DataFrame(
            [
                {"node": 0, "kxx": 1e7, "cxx": 1e3},
                {"node": 4, "kxx": 1e7, "cxx": 1e3},
            ]
        )
        ed_bearings = st.data_editor(df_bearings, num_rows="dynamic", key="bearing_table")

    # --- ASSEMBLAGE DU ROTOR ---
    try:
        # Construction des éléments d'arbre
        shaft_elements = [
            rs.ShaftElement(L=row["L"], idl=row["id"], odl=row["od"], material=mat_acier)
            for _, row in ed_shaft.iterrows()
        ]

        # Construction des disques
        disk_elements = [
            rs.DiskElement.from_geometry(
                n=int(row["node"]), material=mat_acier, 
                width=row["width"], i_d=row["id"], o_d=row["od"]
            )
            for _, row in ed_disks.iterrows()
        ]

        # Construction des paliers
        bearing_elements = [
            rs.BearingElement(n=int(row["node"]), kxx=row["kxx"], cxx=row["cxx"])
            for _, row in ed_bearings.iterrows()
        ]

        # Création de l'objet Rotor
        rotor = rs.Rotor(shaft_elements, disk_elements, bearing_elements)

        # --- AFFICHAGE DES RÉSULTATS ---
        t1, t2, t3, t4 = st.tabs(["🏗️ Visualisation 3D", "📊 Campbell", "📈 Réponse au Balourd", "🎬 Modes Propres"])

        with t1:
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
            st.write(f"**Nombre de noeuds :** {rotor.n_nodes} | **Masse totale :** {rotor.m:.2f} kg")

        with t2:
            st.subheader("Diagramme de Campbell")
            v_max = st.slider("Vitesse Max (RPM)", 1000, 20000, 5000)
            speeds = np.linspace(0, v_max * np.pi/30, 40)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)

        with t3:
            st.subheader("Réponse en fréquence (Bode)")
            node_probe = st.selectbox("Sonde sur le noeud :", range(rotor.n_nodes), index=int(rotor.n_nodes/2))
            freqs = np.linspace(0, v_max * np.pi/30, 100)
            # Balourd de 0.01 kg.m sur le premier disque trouvé
            if len(disk_elements) > 0:
                target_node = int(ed_disks.iloc[0]["node"])
                resp = rotor.run_unbalance_response(target_node, 0.001, 0, freqs)
                st.plotly_chart(resp.plot(probe=[(node_probe, 0)]), use_container_width=True)
            else:
                st.warning("Ajoutez au moins un disque pour simuler un balourd.")

        with t4:
            st.subheader("Animation des Modes")
            modal = rotor.run_modal(speed=0)
            m_idx = st.selectbox("Mode :", range(len(modal.evalues[:8])), format_func=lambda x: f"Mode {x+1}")
            st.plotly_chart(modal.plot_mode_3d(mode=m_idx), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur de modélisation : {e}")
        st.info("Vérifiez que les numéros de noeuds correspondent à la structure de l'arbre.")

else:
    # --- MODE TP GUIDÉ (Inchangé pour la stabilité) ---
    st.subheader("TP n°1 : Vitesse Critique")
    # ... (Le code du TP précédent peut être inséré ici)
