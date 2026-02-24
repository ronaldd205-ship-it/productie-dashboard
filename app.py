import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Factory Flow Intelligence", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { border: 1px solid #dce1e6; padding: 20px; border-radius: 12px; background: white; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 Factory Flow: Eindejaarsrapportage 2025")

# --- SIDEBAR ---
st.sidebar.header("📥 Data Input")
uploaded_file = st.sidebar.file_uploader("Upload 'Production History' CSV", type="csv")

if uploaded_file:
    try:
        # Laden: we proberen de delimiter te herkennen
        df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')

        # --- DE GROTE SCHOONMAAK (De 'Anti-298000' filter) ---
        def clean_numeric(value):
            if pd.isna(value): return 0
            s = str(value).strip()
            # Als er zowel een punt als een komma is (bijv. 1.234,56), verwijder de punt
            if '.' in s and ',' in s:
                s = s.replace('.', '')
            # Vervang de komma door een punt voor de computer
            s = s.replace(',', '.')
            try:
                return float(s)
            except:
                return 0

        for col in ['Rate (Server)', 'Length']:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)

        # Filter onmogelijke uitschieters (bijv. alles boven de 150 m/u is vaak meetfout)
        df = df[df['Rate (Server)'] < 150]
        # Filter elementen zonder lengte
        df = df[df['Length'] > 0]

        # --- PARSING ---
        def parse_job(job):
            parts = str(job).split('_')
            return pd.Series({
                'Type': parts[0],
                'Project': parts[1] if len(parts) > 1 else "Overig",
                'ElementID': parts[-1] if len(parts) > 1 else "Onbekend"
            })

        df[['Type', 'Project', 'ElementID']] = df['Job'].apply(parse_job)
        df['Meters'] = df['Length'] / 1000

        # --- DASHBOARD TABS ---
        tab1, tab2, tab3 = st.tabs(["📊 Management Summary", "🚀 Project Efficiency", "🛤️ Productie Routes"])

        with tab1:
            st.subheader("Kerncijfers over 2025")
            c1, c2, c3, c4 = st.columns(4)
            
            # KPI Berekeningen
            total_km = df['Meters'].sum() / 1000
            avg_speed = df['Rate (Server)'].replace(0, np.nan).mean() # Negeer 0-metingen
            total_elements = len(df)
            active_projects = df['Project'].nunique()

            c1.metric("Totaal Volume", f"{total_km:.2f} KM", "geproduceerd")
            c2.metric("Projecten", active_projects, "unieke nummers")
            c3.metric("Gem. Snelheid", f"{avg_speed:.2f} m/u", "netto server rate")
            c4.metric("Elementen", total_elements, "stuks")

            st.divider()
            
            # Maandelijkse trend
            df['Start (Server)'] = pd.to_datetime(df['Start (Server)'], errors='coerce')
            monthly_trend = df.resample('M', on='Start (Server)')['Meters'].sum().reset_index()
            monthly_trend['Maand'] = monthly_trend['Start (Server)'].dt.strftime('%B')
            
            st.write("### Productievolume per Maand (Meters)")
            fig_trend = px.area(monthly_trend, x='Maand', y='Meters', color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig_trend, use_container_width=True)

        with tab2:
            st.subheader("Project Ranking: Snelheid vs. Volume")
            
            proj_data = df.groupby('Project').agg({
                'Rate (Server)': 'mean',
                'Meters': 'sum',
                'ElementID': 'count'
            }).reset_index()

            # Filter kleine projecten voor de grafiek
            proj_data = proj_data[proj_data['Meters'] > 10].sort_values('Rate (Server)', ascending=False)

            fig_speed = px.scatter(proj_data, x='Meters', y='Rate (Server)', size='ElementID', 
                                   color='Rate (Server)', hover_name='Project',
                                   title="Snelheid per Project (Groter bolletje = meer elementen)",
                                   color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_speed, use_container_width=True)
            
            st.write("### Top 10 Snelste Projecten")
            st.table(proj_data[['Project', 'Rate (Server)', 'Meters']].head(10))

        with tab3:
            st.subheader("Spoor een element op (Track & Trace)")
            sel_project = st.selectbox("Selecteer een Project om de routes te zien:", sorted(df['Project'].unique()))
            
            subset = df[df['Project'] == sel_project].sort_values('Start (Server)')
            
            fig_route = px.timeline(subset, x_start="Start (Server)", x_end="Finish (Server)", 
                                    y="ElementID", color="Unit", title=f"Route van elementen binnen {sel_project}")
            fig_route.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_route, use_container_width=True)

    except Exception as e:
        st.error(f"Er ging iets mis in de machinekamer: {e}")
else:
    st.info("👋 Welkom! Sleep je CSV-bestand in de zijbalk om de jaarcijfers te genereren.")
