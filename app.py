import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# --- CONFIG & MODERN STYLING ---
st.set_page_config(page_title="FactoryOS | Production Intelligence", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f1f3f6; }
    .stMetric { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    .stRadio > div { flex-direction: row; gap: 20px; }
    .stPlotlyChart { border-radius: 15px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIES ---
def clean_val(v):
    try:
        if pd.isna(v): return 0
        s = str(v).replace('.', '').replace(',', '.')
        return float(s)
    except: return 0

# --- DATA CARRIER ---
if 'view' not in st.session_state: st.session_state.view = 'Dashboard'

st.title("🚀 FactoryOS Intelligence")
uploaded_file = st.sidebar.file_uploader("📂 Drop Production History CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
    
    # Data Schoonmaak & Parsing
    for c in ['Rate (Server)', 'Length']:
        if c in df.columns: df[c] = df[c].apply(clean_val)
    
    parts = df['Job'].str.split('_', expand=True)
    df['Type'] = parts[0]
    df['Project'] = parts[1].fillna("Overig")
    df['ElementID'] = parts.apply(lambda x: x.dropna().iloc[-1], axis=1)
    df['Meters'] = df['Length'] / 1000
    df['Start'] = pd.to_datetime(df['Start (Server)'], errors='coerce')
    df['End'] = pd.to_datetime(df['Finish (Server)'], errors='coerce')
    df['Dagen'] = df['Start'].dt.day_name()
    
    # BREADCRUMBS / NAVIGATIE
    st.session_state.view = st.radio("Navigatie", ["🏠 Dashboard", "📈 Project Diepte", "🧬 Element Journey", "🔥 Heatmaps"], label_visibility="collapsed")
    st.divider()

    if st.session_state.view == "🏠 Dashboard":
        st.subheader("Global Factory Performance")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Volume 2025", f"{df['Meters'].sum()/1000:.2f} KM")
        c2.metric("Flow Rate", f"{df[df['Rate (Server)']<150]['Rate (Server)'].mean():.1f} m/u")
        c3.metric("Projecten", df['Project'].nunique())
        c4.metric("Drukste Dag", df['Dagen'].mode()[0])

        st.plotly_chart(px.bar(df.groupby('Project')['Meters'].sum().nlargest(15).reset_index(), 
                               x='Project', y='Meters', color='Meters', title="Top 15 Projecten op Volume (Meters)"), use_container_width=True)

    elif st.session_state.view == "📈 Project Diepte":
        selected_proj = st.selectbox("Selecteer Project:", sorted(df['Project'].unique()))
        pdf = df[df['Project'] == selected_proj]
        
        st.write(f"### Analyse Project: {selected_proj}")
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            unit_eff = pdf.groupby('Unit')['Rate (Server)'].mean().reset_index()
            st.write("**Snelheid per Unit**")
            st.dataframe(unit_eff.style.background_gradient(cmap='RdYlGn'))
            
        with col_b:
            fig_p = px.scatter(pdf, x='Start', y='Rate (Server)', color='Unit', size='Meters', 
                               hover_data=['ElementID'], title="Performance over tijdperk")
            st.plotly_chart(fig_p, use_container_width=True)

    elif st.session_state.view == "🧬 Element Journey":
        st.subheader("Track & Trace Element-paden")
        sel_proj_2 = st.selectbox("Kies Project:", sorted(df['Project'].unique()), key="2")
        pdf2 = df[df['Project'] == sel_proj_2]
        
        sel_elem = st.selectbox("Kies ElementID:", sorted(pdf2['ElementID'].unique()))
        journey = pdf2[pdf2['ElementID'] == sel_elem].sort_values('Start')
        
        st.write(f"#### Reis van element: **{sel_elem}**")
        
        # Journey Path UI
        path = " ➔ ".join(journey['Unit'].tolist())
        st.success(f"**Route:** {path}")
        
        fig_j = px.timeline(journey, x_start="Start", x_end="End", y="Unit", color="Unit", text="Unit")
        fig_j.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_j, use_container_width=True)

    elif st.session_state.view == "🔥 Heatmaps":
        st.subheader("Capaciteit & Bottlenecks")
        heatmap_data = df.groupby(['Dagen', 'Unit'])['Meters'].sum().unstack().fillna(0)
        # Sorteer dagen
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(days)
        
        fig_h = px.imshow(heatmap_data, labels=dict(x="Werkstation", y="Dag", color="Meters"),
                          x=heatmap_data.columns, y=heatmap_data.index, aspect="auto",
                          color_continuous_scale='YlOrRd', title="Productie-druk Matrix")
        st.plotly_chart(fig_h, use_container_width=True)
        st.info("Donkerrode vlakken geven aan waar de meeste meters worden geproduceerd. Ideaal voor personeelsplanning.")

else:
    st.info("👋 Welkom bij FactoryOS. Upload uw data om de intelligentie te activeren.")
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop", caption="Data Driven Production")
