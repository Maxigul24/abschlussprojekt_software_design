import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from graph4 import Node, Spring, System, create_mbb_beam, plot_structure

# Seiten-Konfiguration
st.set_page_config(page_title="Topology Optimizer", layout="wide")

st.title("Topologieoptimierung")

# --- SIDEBAR: EINSTELLUNGEN ---
with st.sidebar:
    st.header("1. Gitter-Einstellungen")
    width = st.slider("Breite (Knoten)", min_value=5, max_value=50, value=20)
    height = st.slider("Höhe (Knoten)", min_value=3, max_value=20, value=5)
    
    st.header("2. Optimierung")
    remove_pct = st.slider("Masse entfernen (%)", 0, 90, 50)
    
    st.header("3. Visualisierung")
    show_labels = st.checkbox("Knoten-IDs anzeigen", value=False)
    # colormap ist fix auf "jet" gesetzt

    start_btn = st.button("Simulation Starten", type="primary")

if start_btn:
    progress_bar = st.progress(0, text="Initialisiere...")
    
    # 1. System aufbauen
    with st.spinner('Erstelle Gitterstruktur...'):
        nodes, springs = create_mbb_beam(width, height)
        system = System(nodes, springs)
        
        # 2. Randbedingungen (MBB)
        bottom_left = 0 # (0,0)
        # Rechts unten (x=width-1, z=0): ROLLENLAGER
        bottom_right_node_id = (width - 1) * height + 0
        bottom_left_node_id = 0

        u_fixed_idx = [
            2 * bottom_left_node_id,      # u_x links fest
            2 * bottom_left_node_id + 1,  # u_z links fest
            2 * bottom_right_node_id + 1  # u_z rechts fest (Rollenlager)
        ]
        
        # 3. Kraft oben mitte
        max_id = max(nodes.keys())
        dim = 2 * (max_id + 1)
        F = np.zeros(dim) 
        
        # Top center node
        top_center = (width // 2) * height + (height - 1)
        if top_center in nodes:
             F[2 * top_center + 1] = -10.0 # Kraft nach unten
        
        
        system.set_boundary_conditions(F, u_fixed_idx)

    # Zeige Initialzustand
    st.subheader("Ausgangszustand")
    system.assemble_global_stiffness()
    system.solve()
    st.pyplot(plot_structure(system, "Vollständige Struktur", show_labels, "jet"))

    # 4. Optimierung
    to_delete = int(len(nodes) * (remove_pct / 100))
    progress_bar.progress(10, text=f"Starte Optimierung: Lösche {to_delete} Knoten...")
    
    try:
        remaining = system.reduce_mass(to_delete)
        progress_bar.progress(100, text="Fertig!")
        
        st.subheader("Optimiertes Ergebnis")
        st.success(f"Optimierung abgeschlossen. Verbleibende Masse: {remaining} Knoten (-{remove_pct}%).")
        st.pyplot(plot_structure(system, "Optimierte Topologie", show_labels, "jet"))
        
    except Exception as e:
        st.error(f"Fehler während der Optimierung: {e}")
        st.error("Traceback: " + str(e))