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
        # We laden het bestand in en negeren foutieve rijen
        df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
        
        if 'Job' not in df.columns:
            st.error("❌ De kolom 'Job' is niet gevonden. Controleer of het bestand een CSV is.")
        else:
            # --- SCHOONMAAK: Komma's naar punten voor getallen ---
            # We doen dit voor Length en Rate kolommen
            for col in ['Length', 'Rate (Server)', 'Rate (Machine)']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # --- DE PARSER ---
            def parse_job(job):
                parts = str(job).split('_')
                return pd.Series({
                    'Type': parts[0],
                    'Project': parts[1] if len(parts) > 1 else "Overig",
                    'Element': parts[-1] if len(parts) > 1 else "Onbekend"
                })

            df[['Type', 'Project', 'Element']] = df['Job'].apply(parse_job)
            df['Meters'] = df['Length'] / 1000

            # --- KPI DASHBOARD ---
            tot_km = df['Meters'].sum() / 1000
            avg_speed = df['Rate (Server)'].mean()

            m1, m2, m3 = st.columns(3)
            m1.metric("Totaal Volume", f"{tot_km:.2f} KM")
            m2.metric("Projecten", df['Project'].nunique())
            m3.metric("Gem. Snelheid", f"{avg_speed:.2f} m/u")

            st.divider()

            # --- GRAFIEKEN ---
            c1, c2 = st.columns(2)
            
            with c1:
                st.write("### 📊 Meters per Project")
                proj_vol = df.groupby('Project')['Meters'].sum().nlargest(10).reset_index()
                fig_proj = px.bar(proj_vol, x='Project', y='Meters', color='Meters', color_continuous_scale='Blues')
                st.plotly_chart(fig_proj, use_container_width=True)

            with c2:
                st.write("### ⚙️ Unit Performance")
                unit_perf = df.groupby('Unit')['Rate (Server)'].mean().reset_index()
                fig_unit = px.bar(unit_perf, x='Unit', y='Rate (Server)', color='Rate (Server)', color_continuous_scale='Reds')
                st.plotly_chart(fig_unit, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Er ging iets mis: {e}")
        st.info("Tip: Controleer of het bestand niet geopend is in Excel tijdens het uploaden.")
else:
    st.info("👈 Upload het bestand in de zijbalk.")
