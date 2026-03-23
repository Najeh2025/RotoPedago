# --- ASSEMBLAGE DU ROTOR (Correctif n_nodes) ---
        rotor = rs.Rotor(shaft_elements, disk_elements, bearing_elements)
        
        # Calcul du nombre de noeuds réel
        num_nodes = len(rotor.nodes)

        # --- AFFICHAGE DES RÉSULTATS ---
        t1, t2, t3, t4 = st.tabs(["🏗️ Visualisation 3D", "📊 Campbell", "📈 Réponse au Balourd", "🎬 Modes Propres"])

        with t1:
            st.plotly_chart(rotor.plot_rotor(), use_container_width=True)
            st.info(f"💡 **Note pédagogique :** Un arbre de {len(shaft_elements)} éléments possède {num_nodes} nœuds (numérotés de 0 à {num_nodes-1}).")
            st.write(f"**Masse totale :** {rotor.m:.2f} kg")

        with t2:
            st.subheader("Diagramme de Campbell")
            v_max = st.slider("Vitesse Max (RPM)", 1000, 20000, 5000, key="vmax_camp")
            speeds = np.linspace(0, v_max * np.pi/30, 40)
            camp = rotor.run_campbell(speeds)
            st.plotly_chart(camp.plot(), use_container_width=True)

        with t3:
            st.subheader("Réponse en fréquence (Bode)")
            # Utilisation de num_nodes au lieu de n_nodes
            node_probe = st.selectbox("Position du capteur (noeud) :", range(num_nodes), index=int(num_nodes/2))
            freqs = np.linspace(0, v_max * np.pi/30, 100)
            
            if len(disk_elements) > 0:
                # On prend le noeud du premier disque pour le balourd
                target_node = int(ed_disks.iloc[0]["node"])
                try:
                    resp = rotor.run_unbalance_response(target_node, 0.001, 0, freqs)
                    st.plotly_chart(resp.plot(probe=[(node_probe, 0)]), use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur de calcul du balourd : {e}")
            else:
                st.warning("Ajoutez au moins un disque dans le tableau pour simuler un balourd.")

        with t4:
            st.subheader("Animation des Modes")
            modal = rotor.run_modal(speed=0)
            # On limite l'affichage aux 6 premiers modes pour éviter les erreurs
            num_modes_avail = len(modal.evalues) // 2 
            m_idx = st.selectbox("Mode :", range(min(num_modes_avail, 6)), format_func=lambda x: f"Mode {x+1}")
            st.plotly_chart(modal.plot_mode_3d(mode=m_idx), use_container_width=True)
