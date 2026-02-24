import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# --- CONFIG & MODERN STYLING ---
st.set_page_config(page_title="FactoryOS | Production Intelligence", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f3f6; }
    .stMetric { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    [data-testid="stSidebar"] { background-color: #1e293b; color: white; }
    .stRadio > div { flex-direction: row; gap: 15px; background: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- DATA HELPERS ---
def clean_val(v):
    try:
        if pd.isna(v): return 0
        s = str(v).replace('.', '').replace(',', '.')
        return float(s)
    except: return 0

# --- APP HEADER ---
st.title("🚀 FactoryOS Intelligence")
st.markdown("### *Van ruwe data naar fabriekscontrole*")

uploaded_file = st.sidebar.file_uploader("📂 Drop Production History CSV", type="csv")

if uploaded_file:
    # Automatische detectie van scheidingstekens (, of ;)
    df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
    
    # 1. Grondige Data Opschoning
    for c in ['Rate (Server)', 'Length']:
        if c in df.columns: df[c] = df[c].apply(clean_val)
    
    # 2. Slimme Parser voor Job-strings
    parts = df['Job'].str.split('_', expand=True)
    df['Type'] = parts[0]
    df['Project'] = parts[1].fillna("Overig")
    df['ElementID'] = parts.apply(lambda x: x.dropna().iloc[-1], axis=1)
    df['Meters'] = df['Length'] / 1000
    df['Start'] = pd.to_datetime(df['Start (Server)'], errors='coerce')
    df['End'] = pd.to_datetime(df['Finish (Server)'], errors='coerce')
    df['Dagen'] = df['Start'].dt.day_name()
    
    # 3. NAVIGATIE BREADCRUMBS
    view = st.radio("Navigatie", ["🏠 Dashboard", "📈 Project Diepte", "🧬 Element Journey", "🔥 Heatmaps"])
    st.divider()

    # --- VIEW: DASHBOARD ---
    if view == "🏠 Dashboard":
        c1, c2, c3, c4 = st.columns(4)
        km_total = df['Meters'].sum()/1000
        avg_rate = df[df['Rate (Server)'] < 150]['Rate (Server)'].mean()
        
        c1.metric("Volume 2025", f"{km_total:.2f} KM")
        c2.metric("Flow Rate", f"{avg_rate:.1f} m/u")
        c3.metric("Projecten", df['Project'].nunique())
        c4.metric("Drukste Dag", df['Dagen'].mode()[0])

        col_left, col_right = st.columns([2, 1])
        with col_left:
            top_proj = df.groupby('Project')['Meters'].sum().nlargest(12).reset_index()
            fig_top = px.bar(top_proj, x='Project', y='Meters', color='Meters', 
                             title="Top 12 Projecten (Meters)", color_continuous_scale='Viridis')
            st.plotly_chart(fig_top, use_container_width=True)
        with col_right:
            st.write("### 🏗️ Type Verdeling")
            fig_pie = px.pie(df, names='Type', values='Meters', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- VIEW: PROJECT DIEPTE ---
    elif view == "📈 Project Diepte":
        sel_proj = st.selectbox("Selecteer Project:", sorted(df['Project'].unique()))
        pdf = df[df['Project'] == sel_proj].copy()
        
        st.write(f"## 🔍 Project Analyse: {sel_proj}")
        
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.write("#### Performance per Unit")
            unit_eff = pdf.groupby('Unit')['Rate (Server)'].mean().reset_index()
            unit_eff.columns = ['Unit', 'Snelheid (m/u)']
            
            # De tabel met de kleur-gradiënt (Requires matplotlib)
            st.dataframe(
                unit_eff.style.background_gradient(cmap='RdYlGn', subset=['Snelheid (m/u)'])
                .format(precision=2),
                use_container_width=True
            )
            st.info("💡 Groen is sneller, rood is de bottleneck.")
            
        with col_b:
            fig_p = px.scatter(pdf, x='Start', y='Rate (Server)', color='Unit', size='Meters', 
                               hover_data=['ElementID'], title="Productiesnelheid over tijdstippen")
            st.plotly_chart(fig_p, use_container_width=True)

    # --- VIEW: ELEMENT JOURNEY ---
    elif view == "🧬 Element Journey":
        st.subheader("🧬 Track & Trace Elementpad")
        col1, col2 = st.columns(2)
        with col1:
            sel_proj_2 = st.selectbox("Kies Project:", sorted(df['Project'].unique()), key="2")
        with col2:
            pdf2 = df[df['Project'] == sel_proj_2]
            sel_elem = st.selectbox("Kies ElementID:", sorted(pdf2['ElementID'].unique()))
        
        journey = pdf2[pdf2['ElementID'] == sel_elem].sort_values('Start')
        
        # Route-breadcrumbs
        st.write("### 🛤️ Gevolgde Route")
        path_html = " ➔ ".join([f"<span style='background:#fff; padding:5px 10px; border-radius:5px; border:1px solid #ccc;'>{u}</span>" for u in journey['Unit']])
        st.markdown(path_html, unsafe_allow_html=True)
        
        st.write("#### Tijdsverloop")
        fig_j = px.timeline(journey, x_start="Start", x_end="End", y="Unit", color="Unit", text="Unit")
        fig_j.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_j, use_container_width=True)

    # --- VIEW: HEATMAPS ---
    elif view == "🔥 Heatmaps":
        st.subheader("🔥 Capaciteit & Druk Matrix")
        
        heatmap_data = df.groupby(['Dagen', 'Unit'])['Meters'].sum().unstack().fillna(0)
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex([d for d in days_order if d in heatmap_data.index])
        
        fig_h = px.imshow(heatmap_data, labels=dict(x="Werkstation", y="Dag", color="Meters"),
                          color_continuous_scale='YlOrRd', aspect="auto")
        st.plotly_chart(fig_h, use_container_width=True)
        st.success("Deze heatmap toont wanneer welke units de hoogste belasting hadden.")

else:
    st.info("👋 Welkom bij FactoryOS. Upload je data in de zijbalk om te starten.")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=1000", caption="Industrial Intelligence 2026")
