import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- UI CONFIGURATIE ---
st.set_page_config(page_title="Factory Flow | Inzicht 2025", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 Factory Flow: Production Intelligence")
st.subheader("Strategisch jaaroverzicht op basis van real-time data")

# --- DATA IMPORT ---
uploaded_file = st.sidebar.file_uploader("📂 Sleep hier het jaarbestand (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # --- DE MAGISCHE PARSER ---
    def parse_job(job):
        parts = str(job).split('_')
        return pd.Series({
            'Type': parts[0],
            'Project': parts[1] if len(parts) > 1 else "Overig",
            'Element': parts[-1] if len(parts) > 1 else "Onbekend"
        })

    df[['Type', 'Project', 'Element']] = df['Job'].apply(parse_job)
    df['Meters'] = df['Length'] / 1000
    df['Start (Server)'] = pd.to_datetime(df['Start (Server)'])

    # --- KPI SECTIE ---
    tot_km = df['Meters'].sum() / 1000
    avg_speed = df['Rate (Server)'].mean()
    top_proj = df.groupby('Project')['Meters'].sum().idxmax()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Totaal Volume", f"{tot_km:.2f} KM", "Jaartotaal")
    m2.metric("Projecten", df['Project'].nunique(), "Actieve dossiers")
    m3.metric("Gem. Snelheid", f"{avg_rate:.1f} m/u", "Efficiency")
    m4.metric("Grootste Project", top_proj)

    st.divider()

    # --- VISUELE ANALYSE ---
    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.write("### 📈 Maandelijkse Productie Trend")
        df['Maand'] = df['Start (Server)'].dt.strftime('%B')
        trend = df.groupby('Maand')['Meters'].sum().reset_index()
        fig_trend = px.line(trend, x='Maand', y='Meters', markers=True, 
                            line_shape="spline", title="Productie Volume per Maand")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_r:
        st.write("### 🏗️ Verdeling per Type")
        type_dist = df.groupby('Type')['Element'].count().reset_index()
        fig_pie = px.pie(type_dist, values='Element', names='Type', hole=.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # --- DE BOTTLENECK FINDER ---
    st.write("### 🚨 Werkstation Performance (Unit Analyse)")
    unit_perf = df.groupby('Unit')['Rate (Server)'].mean().reset_index().sort_values('Rate (Server)')
    
    fig_unit = px.bar(unit_perf, x='Rate (Server)', y='Unit', orientation='h',
                      color='Rate (Server)', color_continuous_scale='RdYlGn',
                      title="Snelheid per Unit (Lager = Bottleneck)")
    st.plotly_chart(fig_unit, use_container_width=True)

    # --- DE "STRONG" CONCLUSIE ---
    st.info(f"**Management Samenvatting:** In 2025 was Project **{top_proj}** de grootste drijver van volume. Let op: Unit **{unit_perf.iloc[0]['Unit']}** presteert structureel onder het gemiddelde. Een verbetering van 10% op deze unit levert direct extra capaciteit op.")

else:
    st.warning("👈 Upload het CSV-bestand in de zijbalk om de analyse te genereren.")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=1000", caption="Wachten op data...")