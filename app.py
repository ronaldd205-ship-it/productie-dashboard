import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Production Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { border: 1px solid #dce1e6; padding: 15px; border-radius: 8px; background: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 Factory Flow Intelligence")
st.markdown("_Grip op productie-efficiëntie en projectdoorloop_")

# --- DATA IMPORT ---
uploaded_file = st.sidebar.file_uploader("📂 Upload Production History (CSV)", type="csv")

if uploaded_file:
    try:
        # Laden en decimalen fixen
        df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
        
        for col in ['Length', 'Rate (Server)']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce')

        # Parser logica
        def parse_job(job):
            parts = str(job).split('_')
            return pd.Series({
                'Type': parts[0],
                'Project': parts[1] if len(parts) > 1 else "Overig",
                'ElementID': parts[-1] if len(parts) > 1 else "Onbekend"
            })

        df[['Type', 'Project', 'ElementID']] = df['Job'].apply(parse_job)
        df['Meters'] = df['Length'] / 1000

        # --- TABS VOOR GEBRUIKSVRIENDELIJKHEID ---
        tab_kpi, tab_speed, tab_routes = st.tabs(["🚀 Jaaroverzicht", "📈 Project Snelheid", "🛤️ Element Routes"])

        with tab_kpi:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Totaal Geproduceerd", f"{df['Meters'].sum()/1000:.2f} KM")
            c2.metric("Projecten", df['Project'].nunique())
            c3.metric("Gem. Snelheid", f"{df['Rate (Server)'].mean():.2f} m/u")
            c4.metric("Drukste Unit", df['Unit'].mode()[0])
            
            st.divider()
            st.write("### Productie per Maand")
            df['Start (Server)'] = pd.to_datetime(df['Start (Server)'], errors='coerce')
            df['Maand'] = df['Start (Server)'].dt.strftime('%m - %B')
            monthly = df.groupby('Maand')['Meters'].sum().reset_index()
            st.plotly_chart(px.line(monthly, x='Maand', y='Meters', markers=True, template="plotly_white"), use_container_width=True)

        with tab_speed:
            st.subheader("Welke projecten presteren het best?")
            proj_perf = df.groupby('Project').agg({
                'Rate (Server)': 'mean',
                'Meters': 'sum'
            }).reset_index().sort_values('Rate (Server)', ascending=False)

            # Kleurcode: Snel (Groen) vs Langzaam (Rood)
            avg_all = proj_perf['Rate (Server)'].mean()
            proj_perf['Status'] = proj_perf['Rate (Server)'].apply(lambda x: 'Boven Gemiddeld' if x > avg_all else 'Onder Gemiddeld')
            
            fig_speed = px.bar(proj_perf.head(20), x='Project', y='Rate (Server)', color='Status',
                               color_discrete_map={'Boven Gemiddeld': '#2ecc71', 'Onder Gemiddeld': '#e74c3c'},
                               title="Snelheid per Project (Top 20)")
            st.plotly_chart(fig_speed, use_container_width=True)

        with tab_routes:
            st.subheader("🛤️ De weg van een element")
            selected_project = st.selectbox("Kies een project om de route te zien:", df['Project'].unique())
            
            route_data = df[df['Project'] == selected_project].sort_values(['ElementID', 'Start (Server)'])
            
            # Visualiseer de volgorde van units
            fig_route = px.scatter(route_data, x='Unit', y='ElementID', color='Unit',
                                   title=f"Route-overzicht voor Project {selected_project}",
                                   labels={'ElementID': 'Uniek Element', 'Unit': 'Werkstation'})
            st.plotly_chart(fig_route, use_container_width=True)
            
            st.info("Deze grafiek laat zien welke elementen langs welke units zijn gegaan. Gaten in de lijn betekenen dat een element stations heeft overgeslagen.")

    except Exception as e:
        st.error(f"Er ging iets mis: {e}")
else:
    st.info("👋 Welkom! Upload je CSV-bestand in de zijbalk om de fabriek te analyseren.")
