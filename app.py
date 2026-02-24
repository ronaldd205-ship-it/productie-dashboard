import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Factory Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { border-radius: 15px; background: white; border: 1px solid #e0e0e0; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 Factory Flow: Intelligence Dashboard")

# --- DATA IMPORT ---
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV Bestand", type="csv")

if uploaded_file:
    try:
        # Laden & Schoonmaken
        df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
        
        def clean_num(v):
            if pd.isna(v): return 0
            s = str(v).replace('.', '').replace(',', '.')
            try: return float(s)
            except: return 0

        for col in ['Rate (Server)', 'Length']:
            if col in df.columns:
                df[col] = df[col].apply(clean_num)

        # Parser
        def parse_job(job):
            p = str(job).split('_')
            return pd.Series({'Type': p[0], 'Project': p[1] if len(p)>1 else "Overig", 'ElementID': p[-1]})

        df[['Type', 'Project', 'ElementID']] = df['Job'].apply(parse_job)
        df['Meters'] = df['Length'] / 1000
        df['Start (Server)'] = pd.to_datetime(df['Start (Server)'], errors='coerce')
        df['Finish (Server)'] = pd.to_datetime(df['Finish (Server)'], errors='coerce')
        
        # --- TABS ---
        tab1, tab2 = st.tabs(["📊 Jaar Analyse", "🛤️ Route & Proces Inzicht"])

        with tab1:
            st.subheader("Jaarresultaten 2025")
            c1, c2, c3 = st.columns(3)
            c1.metric("Totaal Volume", f"{df['Meters'].sum()/1000:.2f} KM")
            c2.metric("Projecten", df['Project'].nunique())
            c3.metric("Gem. Snelheid", f"{df[df['Rate (Server)'] < 150]['Rate (Server)'].mean():.2f} m/u")
            
            st.plotly_chart(px.histogram(df, x='Project', y='Meters', color='Type', title="Volume per Project per Type"), use_container_width=True)

        with tab2:
            st.subheader("Route-analyse per Project")
            
            # UX: Filter bovenaan
            sel_proj = st.selectbox("🔍 Kies een Project voor diepte-analyse:", sorted(df['Project'].unique()))
            p_df = df[df['Project'] == sel_proj].sort_values('Start (Server)')

            # Project-specifieke metrics
            k1, k2, k3 = st.columns(3)
            k1.info(f"**Aantal Elementen:** {p_df['ElementID'].nunique()}")
            k2.success(f"**Totaal Meters:** {p_df['Meters'].sum():.1f} m")
            k3.warning(f"**Langzaamste Unit:** {p_df.groupby('Unit')['Rate (Server)'].mean().idxmin()}")

            st.divider()

            # VISUALISATIE 1: De Flow (Sankey-achtig)
            st.write("### Flow over de Werkstations")
            flow = p_df.groupby('Unit').agg({'ElementID': 'count', 'Meters': 'sum'}).reset_index()
            fig_flow = px.funnel(flow.sort_values('Meters', ascending=False), y='Unit', x='Meters', 
                                 title="Volume per Unit (Waar gaat de meeste massa heen?)",
                                 color_discrete_sequence=['#636EFA'])
            st.plotly_chart(fig_flow, use_container_width=True)

            # VISUALISATIE 2: Route per Element (Tijdlijn)
            st.write("### De 'Reis' van de Elementen")
            # UX: Mogelijkheid om op specifiek element te filteren
            all_elements = ["Alles"] + sorted(p_df['ElementID'].unique().tolist())
            sel_elem = st.selectbox("Focus op specifiek element (optioneel):", all_elements)
            
            plot_df = p_df if sel_elem == "Alles" else p_df[p_df['ElementID'] == sel_elem]
            
            fig_route = px.timeline(plot_df, x_start="Start (Server)", x_end="Finish (Server)", 
                                    y="Unit", color="Unit", text="ElementID",
                                    title=f"Tijdslijn per Unit voor {sel_proj}")
            fig_route.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig_route, use_container_width=True)

            # UX: De Bottleneck tabel
            st.write("### Efficiency per Unit voor dit project")
            unit_table = p_df.groupby('Unit').agg({
                'Rate (Server)': 'mean',
                'Meters': 'sum'
            }).rename(columns={'Rate (Server)': 'Gem. Snelheid (m/u)', 'Meters': 'Totaal Meters'}).reset_index()
            st.dataframe(unit_table.style.highlight_min(subset=['Gem. Snelheid (m/u)'], color='#ffcccc'))

    except Exception as e:
        st.error(f"Fout bij verwerken: {e}")
else:
    st.info("👋 Upload de CSV om de routes te visualiseren.")
