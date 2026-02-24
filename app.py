import streamlit as st
import pandas as pd
import plotly.express as px

# --- UI CONFIGURATIE ---
st.set_page_config(page_title="Factory Flow | Inzicht 2025", layout="wide")

st.title("🏭 Factory Flow: Production Intelligence")
st.subheader("Strategisch jaaroverzicht op basis van real-time data")

# --- DATA IMPORT ---
uploaded_file = st.sidebar.file_uploader("📂 Sleep hier het jaarbestand (CSV)", type="csv")

if uploaded_file:
    try:
        # We proberen het bestand in te laden. 
        # sep=None met engine='python' zorgt dat hij zelf zoekt naar , of ;
        df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
        
        # Controleer of de cruciale kolom 'Job' wel bestaat
        if 'Job' not in df.columns:
            st.error("❌ Fout: De kolom 'Job' is niet gevonden in dit bestand. Controleer de kolomnamen.")
        else:
            # --- DE MAGISCHE PARSER ---
            def parse_job(job):
                job_str = str(job)
                parts = job_str.split('_')
                # Logica: Prefix is 1e deel, Project is 2e deel, Element is laatste deel
                prefix = parts[0] if len(parts) > 0 else "Overig"
                project = parts[1] if len(parts) > 1 else "Onbekend"
                element = parts[-1] if len(parts) > 1 else "Onbekend"
                return pd.Series([prefix, project, element])

            df[['Type', 'Project', 'Element']] = df['Job'].apply(parse_job)
            
            # Zet Length om naar meters
            if 'Length' in df.columns:
                df['Meters'] = pd.to_numeric(df['Length'], errors='coerce') / 1000
            else:
                df['Meters'] = 0

            # --- KPI SECTIE ---
            tot_km = df['Meters'].sum() / 1000
            avg_speed = df['Rate (Server)'].mean() if 'Rate (Server)' in df.columns else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Totaal Volume", f"{tot_km:.2f} KM")
            m2.metric("Projecten", df['Project'].nunique())
            m3.metric("Gem. Snelheid", f"{avg_speed:.1f} m/u")

            st.divider()

            # --- VISUELE ANALYSE ---
            col_l, col_r = st.columns([2, 1])

            with col_l:
                st.write("### 🏗️ Volume per Project")
                proj_vol = df.groupby('Project')['Meters'].sum().reset_index().sort_values('Meters', ascending=False).head(15)
                fig_proj = px.bar(proj_vol, x='Project', y='Meters', color='Meters', template="plotly_white")
                st.plotly_chart(fig_proj, use_container_width=True)

            with col_r:
                st.write("### 📋 Verdeling per Type")
                type_dist = df.groupby('Type').size().reset_index(name='Aantal')
                fig_pie = px.pie(type_dist, values='Aantal', names='Type', hole=.4)
                st.plotly_chart(fig_pie, use_container_width=True)

    except Exception as e:
        st.error(f"Er ging iets mis bij het verwerken van het bestand: {e}")
else:
    st.info("👈 Upload het CSV-bestand in de zijbalk om de analyse te starten.")
