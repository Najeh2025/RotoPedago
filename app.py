import streamlit as st
import ross as rs
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="RotoPédago v4.1 Expert", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BIBLIOTHÈQUE DE PALIERS ---
bearing_presets = {
    "Roulement à billes (Standard)": {"kxx": 1e7, "kyy": 1e7, "kxy": 0, "cxx": 500, "cyy": 500},
    "Palier Lisse (Hydrodynamique)": {"kxx": 1e7, "kyy": 5e6, "kxy": 2e6, "cxx": 2000, "cyy": 2000},
    "Support Souple (Amortisseur)": {"kxx": 1e6, "kyy": 1e6, "kxy": 0, "cxx": 5000, "cyy": 5000}
}

# --- 3. NAVIGATION ---
st.sidebar.title("🚀 RotoPédago v4.1")
mode = st.sidebar.radio("Navigation :", ["🏗️ Constructeur Libre", "🎓 Mode TP Guidé"])
mat_std = rs.Material(name="Steel", rho=7850, E=211e9, G_s=81.2e9)

st.title(f"🎓 RotoPédago - {mode}")

if mode == "🏗️ Constructeur Libre":
    st.markdown("### 🛠️ Model Builder & Bearing Library")
    selected_preset = st.selectbox("Type de paliers pour l'initialisation :", list(bearing_presets.keys()))
    p = bearing_presets[selected_preset]

    col1, col2, col3 = st.columns([1, 1, 1.2])

    with col1:
        st.subheader("1. Arbre (Shaft)")
        df_s = pd.DataFrame([{"L": 0.2, "id": 0.0, "od": 0.05} for _ in range(5)])
        ed_s = st.data_editor(df_s, num_rows="dynamic", key="s_v41")

    with col2:
        st.subheader("2. Disques (Disks)")
        df_d = pd.DataFrame([{"node": 2, "id": 0.05, "od": 0.25, "width": 0.07}])
        ed_d = st.data_editor(df_d, num_rows="dynamic", key="d_v41")

    with col3:
        st.subheader("3. Paliers (Bearings)")
        df_b = pd.DataFrame([
            {"node": 0, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"]},
            {"node": 5, "kxx": p["kxx"], "kyy": p["kyy"], "kxy": p["kxy"], "cxx": p["cxx"]}
        ])
        ed_b = st.data_editor(df_b, num_rows="dynamic", key="b_v41")

    # --- 4. ASSEMBLAGE ET CALCULS ---
    try:
        shaft = [rs.ShaftElement(L=r.L, idl=r.id, odl=r.od, material=mat_std) for r in ed_s.itertuples()]
        disks = [rs.DiskElement.from_geometry(n=int(r.node), material=mat_std, width=r.width, i_d=r.id, o_d=r.od) for r in ed_d.itertuples()]
        bears = [rs.BearingElement(n=int(r.node), kxx=r.kxx, kyy=r.kyy, kxy=r.kxy, kyx=-r.kxy, cxx=r.cxx) for r in ed_b.itertuples()]

        rotor = rs.Rotor(shaft, disks, bears)
        num_nodes = len(rotor.nodes)

        t1, t2, t3, t4, t5 = st.tabs(["🏗️ Modèle", "📊 Campbell", "📉 Stabilité", "📏 Statique", "🎬 Animation"])

        with t1:
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
            st.write(f"**Masse :** {rotor.m:.2f} kg | **Paliers :** {selected_preset}")

        with t2:
            v_max = st.slider("Vitesse Max (RPM)", 1000, 20000, 8000)
            speeds = np.linspace(0, v_max * np.pi/30, 40)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)

        with t3:
            st.subheader("Étude du Décrément Logarithmique")
            st.info("Le Log Dec indique la stabilité. Si Log Dec < 0, le rotor est instable.")
            # Correction : Utilisation d'un graphique manuel si plot_damping n'existe pas
            try:
                # On trace le log_dec vs speed pour les premiers modes
                fig_stab = go.Figure()
                for i in range(min(6, camp.log_dec.shape[1])):
                    fig_stab.add_trace(go.Scatter(x=speeds*30/np.pi, y=camp.log_dec[:, i], name=f"Mode {i+1}"))
                fig_stab.update_layout(xaxis_title="Vitesse (RPM)", yaxis_title="Log Decrement", title="Stabilité des modes")
                st.plotly_chart(fig_stab, use_container_width=True)
            except:
                st.warning("Données de stabilité non disponibles pour ce modèle.")

        with t4:
            st.subheader("Flèche Statique (Gravité)")
            try:
                static = rotor.run_static()
                # On utilise la méthode de tracé 2D plus stable
                st.plotly_chart(static.plot_deflected_shape(), use_container_width=True)
            except Exception as e:
                st.error(f"Erreur d'analyse statique : {e}")

        with t5:
            st.subheader("Animation des Modes 3D")
            modal = rotor.run_modal(speed=0)
            m_idx = st.selectbox("Mode :", range(min(len(modal.evalues)//2, 6)), format_func=lambda x: f"Mode n°{x+1}")
            try:
                st.plotly_chart(modal.plot_mode_3d(mode=m_idx), use_container_width=True)
            except:
                st.plotly_chart(modal.plot_mode_shape(mode=m_idx), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur de Modélisation : {e}")

else:
    # --- MODE TP v4.1 ---
    st.subheader("TP : Analyse de Stabilité")
    st.write("Faites varier le coefficient croisé Kxy pour observer l'instabilité.")
    k_excit = st.slider("Kxy (N/m)", 0.0, 1e7, 1e6, step=1e6)
    
    tp_s = [rs.ShaftElement(L=0.2, idl=0, odl=0.05, material=mat_std) for _ in range(5)]
    tp_d = [rs.DiskElement.from_geometry(n=2, material=mat_std, width=0.07, i_d=0.05, o_d=0.25)]
    tp_b = [rs.BearingElement(n=0, kxx=1e7, kyy=1e7, kxy=k_excit, kyx=-k_excit, cxx=1000),
            rs.BearingElement(n=5, kxx=1e7, kyy=1e7, kxy=k_excit, kyx=-k_excit, cxx=1000)]
    
    rotor_tp = rs.Rotor(tp_s, tp_d, tp_b)
    camp_tp = rotor_tp.run_campbell(np.linspace(0, 1000, 30))
    
    fig_tp = go.Figure()
    for i in range(2):
        fig_tp.add_trace(go.Scatter(x=np.linspace(0, 1000, 30)*30/np.pi, y=camp_tp.log_dec[:, i], name=f"Mode {i+1}"))
    fig_tp.add_hline(y=0, line_dash="dash", line_color="red")
    fig_tp.update_layout(xaxis_title="Vitesse (RPM)", yaxis_title="Log Dec")
    st.plotly_chart(fig_tp, use_container_width=True)

st.sidebar.caption("Stable Version 4.1")
