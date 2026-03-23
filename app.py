import streamlit as st
import ross as rs
import numpy as np
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RotoPédago v4.0 Expert", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; font-size: 14px; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BIBLIOTHÈQUE DE PALIERS (PRÉ-DÉFINIS) ---
bearing_presets = {
    "Roulement à billes (Standard)": {"kxx": 1e7, "kyy": 1e7, "kxy": 0, "cxx": 500, "cyy": 500},
    "Palier Lisse (Hydrodynamique)": {"kxx": 1e7, "kyy": 5e6, "kxy": 2e6, "cxx": 2000, "cyy": 2000},
    "Support Souple (Amortisseur)": {"kxx": 1e6, "kyy": 1e6, "kxy": 0, "cxx": 5000, "cyy": 5000}
}

# --- 3. BARRE LATÉRALE ---
st.sidebar.title("🚀 RotoPédago v4.0")
st.sidebar.subheader("💎 Version Expert")
mode = st.sidebar.radio("Navigation :", ["🏗️ Constructeur Libre", "🎓 Mode TP Guidé"])

# Matériau
mat_std = rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9)

st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    st.markdown("### 🛠️ Model Builder & Bearing Library")
    
    # Présélection de palier
    st.write("#### 📖 Sélectionner un type de palier dans la bibliothèque :")
    selected_preset = st.selectbox("Type de paliers pour l'initialisation :", list(bearing_presets.keys()))
    p = bearing_presets[selected_preset]

    col1, col2, col3 = st.columns([1, 1, 1.2])

    with col1:
        st.subheader("1. Arbre (Shaft)")
        df_s = pd.DataFrame([{"L": 0.2, "id": 0.0, "od": 0.05} for _ in range(5)])
        ed_s = st.data_editor(df_s, num_rows="dynamic", key="s_v4")

    with col2:
        st.subheader("2. Disques (Disks)")
        df_d = pd.DataFrame([{"node": 2, "id": 0.05, "od": 0.25, "width": 0.07}])
        ed_d = st.data_editor(df_d, num_rows="dynamic", key="d_v4")

    with col3:
        st.subheader("3. Paliers (Bearings)")
        # On ajoute kyy et kxy pour l'étude de stabilité
        df_b = pd.DataFrame([
            {"node": 0, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"]},
            {"node": 5, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"]}
        ])
        ed_b = st.data_editor(df_b, num_rows="dynamic", key="b_v4")

    # --- 4. ASSEMBLAGE ET CALCULS ---
    try:
        shaft = [rs.ShaftElement(L=r.L, idl=r.id, odl=r.od, material=mat_std) for r in ed_s.itertuples()]
        disks = [rs.DiskElement.from_geometry(n=int(r.node), material=mat_std, width=r.width, i_d=r.id, o_d=r.od) for r in ed_d.itertuples()]
        # Paliers avec coefficients croisés
        bears = [rs.BearingElement(n=int(r.node), kxx=r.kxx, kyy=r.kyy, kxy=r.kxy, kyx=-r.kxy, cxx=r.cxx) for r in ed_b.itertuples()]

        rotor = rs.Rotor(shaft, disks, bears)
        n_nodes = len(rotor.nodes)

        # --- 5. RÉSULTATS (TABS) ---
        t1, t2, t3, t4, t5 = st.tabs(["🏗️ Modèle", "📊 Campbell", "📉 Stabilité (Log Dec)", "📏 Flèche Statique", "🎬 Animation"])

        with t1:
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
            st.write(f"**Masse :** {rotor.m:.2f} kg | **Paliers :** {selected_preset}")

        with t2:
            st.subheader("Diagramme de Campbell")
            v_max = st.slider("Vitesse Max (RPM)", 1000, 20000, 8000)
            speeds = np.linspace(0, v_max * np.pi/30, 40)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)

        with t3:
            st.subheader("Étude de Stabilité")
            st.info("Un Log Dec positif (> 0) indique un système stable. S'il devient négatif, il y a risque d'instabilité.")
            # On extrait le Log Dec du Campbell
            fig_stab = camp.plot_damping() # Affiche le Log Dec en fonction de la vitesse
            st.plotly_chart(fig_stab, use_container_width=True)

        with t4:
            st.subheader("Déformée Statique (Propre Poids)")
            # Calcul statique (G=9.81 m/s²)
            static = rotor.run_static()
            # Affichage de la flèche (déplacement vertical au repos)
            fig_static = static.plot_deformation()
            st.plotly_chart(fig_static, use_container_width=True)
            st.caption("Visualisation de la flèche de l'arbre entre les paliers due à la gravité.")

        with t5:
            st.subheader("Animation des Modes 3D")
            modal = rotor.run_modal(speed=0)
            m_idx = st.selectbox("Mode :", range(min(len(modal.evalues)//2, 8)), format_func=lambda x: f"Mode n°{x+1}")
            try:
                st.plotly_chart(modal.plot_mode_3d(mode=m_idx), use_container_width=True)
            except:
                st.plotly_chart(modal.plot_mode_shape(mode=m_idx), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        st.info("Vérifiez que les nœuds des paliers/disques sont valides.")

else:
    # --- MODE TP v4.0 ---
    st.subheader("TP n°2 : Instabilité des Paliers Lisses")
    st.write("Analysez comment les coefficients croisés (Kxy) des paliers influencent la stabilité du rotor.")
    
    k_excit = st.slider("Coéfficient croisé Kxy (Instabilité)", 0.0, 1e7, 1e6, step=1e6)
    
    tp_s = [rs.ShaftElement(L=0.2, idl=0, odl=0.05, material=mat_std) for _ in range(5)]
    tp_d = [rs.DiskElement.from_geometry(n=2, material=mat_std, width=0.07, i_d=0.05, o_d=0.25)]
    # Palier avec Kxy variable
    tp_b = [rs.BearingElement(n=0, kxx=1e7, kyy=1e7, kxy=k_excit, kyx=-k_excit, cxx=1000),
            rs.BearingElement(n=5, kxx=1e7, kyy=1e7, kxy=k_excit, kyx=-k_excit, cxx=1000)]
    
    rotor_tp = rs.Rotor(tp_s, tp_d, tp_b)
    camp_tp = rotor_tp.run_campbell(np.linspace(0, 1000, 30))
    
    st.plotly_chart(camp_tp.plot_damping(), use_container_width=True)
    
    if k_excit > 5e6:
        st.error("🚨 INSTABILITÉ DÉTECTÉE : Le Log Dec est passé sous zéro. Le rotor va entrer en 'Oil Whip'.")
    else:
        st.success("✅ Système stable.")

st.sidebar.markdown("---")
st.sidebar.caption("Outil de Simulation Académique v4.0")
