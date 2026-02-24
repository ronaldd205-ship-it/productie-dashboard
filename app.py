import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import io

# --- CONFIG & STRENGERE STYLING ---
st.set_page_config(page_title="FactoryOS | Production Intelligence", layout="wide")

st.markdown("""
    <style>
    /* Achtergrond van de hele app */
    .main { background-color: #f8f9fa; }
    
    /* Zijbalk styling: Donkere achtergrond en witte tekst */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p {
        color: #ffffff !important;
    }
    
    /* Kaarten voor cijfers */
    .stMetric { 
        background: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        border: 1px solid #eee; 
    }
    
    /* Navigatie menu */
    .stRadio > div { 
        flex-direction: row; 
        gap: 15px; 
        background: white; 
        padding: 10px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA HELPERS ---
def clean_val(v):
    try:
        if pd.isna(v): return 0
        s = str(v).replace('.', '').replace(',', '.')
        return float(s)
    except: return 0

# --- APP START ---
st.title("🚀 FactoryOS Intelligence")

# Linker Menu
with st.sidebar:
    st.header("📥 Data Control")
    uploaded_file = st.file_uploader("Drop Production History CSV", type="csv")
    st.markdown("---")
    st.info("💡 **Tip:** Gebruik de 'Project Diepte' tab om bottlenecks per project te isoleren.")

if uploaded_file:
    # Laden
    df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
    
    # Cleaning
    for c in ['Rate (Server)', 'Length']:
        if c in df.columns: df[c] = df[c].apply(clean_val)
    
    # Parser
    parts = df['Job'].str.split('_', expand=True)
    df['Type'] = parts[0]
    df['Project'] = parts[1].fillna("Overig")
    df['ElementID'] = parts.apply(lambda x: x.dropna().iloc[-1], axis=1)
    df['Meters'] = df['Length'] / 1000
    df['Start'] = pd.to_datetime(df['Start (Server)'], errors='coerce')
    df['End'] = pd.to_datetime(df['Finish (Server)'], errors='coerce')
    df['Dagen'] = df['Start'].dt.day_name()
    
    # Navigatie
    view = st.radio("Navigatie", ["🏠 Dashboard", "📈 Project Diepte", "🧬 Element Journey", "🔥 Heatmaps"])
    st.divider()

    if view == "🏠 Dashboard":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Volume 2025", f"{df['Meters'].sum()/1000:.2f} KM")
        c2.metric("Gem. Rate", f"{df[df['Rate (Server)'] < 150]['Rate (Server)'].mean():.1f} m/u")
        c3.metric("Projecten", df['Project'].nunique())
        c4.metric("Drukste Dag", df['Dagen'].mode()[0])

        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.plotly_chart(px.bar(df.groupby('Project')['Meters'].sum().nlargest(12).reset_index(), 
                                   x='Project', y='Meters', color='Meters', title="Top 12 Projecten"), use_container_width=True)
        with col_r:
            st.plotly_chart(px.pie(df, names='Type', values='Meters', hole=0.4, title="Mix per Type"), use_container_width=True)

    elif view == "📈 Project Diepte":
        sel_proj = st.selectbox("Selecteer Project:", sorted(df['Project'].unique()))
        pdf = df[df['Project'] == sel_proj].copy()
        
        st.write(f"### 🔍 Analyse: {sel_proj}")
        
        # Download knop voor de klant
        output = io.BytesIO()
        pdf.to_excel(output, index=False)
        st.download_button(label="📥 Download Project Data (Excel)", data=output.getvalue(), file_name=f"Project_{sel_proj}.xlsx")

        col_a, col_b = st.columns([1, 2])
        with col_a:
            unit_eff = pdf.groupby('Unit')['Rate (Server)'].mean().reset_index()
            unit_eff.columns = ['Unit', 'Snelheid (m/u)']
            st.dataframe(unit_eff.style.background_gradient(cmap='RdYlGn', subset=['Snelheid (m/u)']).format(precision=2), use_container_width=True)
            
        with col_b:
            st.plotly_chart(px.scatter(pdf, x='Start', y='Rate (Server)', color='Unit', size='Meters', title="Snelheidsverloop"), use_container_width=True)

    elif view == "🧬 Element Journey":
        sel_proj_2 = st.selectbox("Kies Project:", sorted(df['Project'].unique()), key="2")
        pdf2 = df[df['Project'] == sel_proj_2]
        sel_elem = st.selectbox("Kies ElementID:", sorted(pdf2['ElementID'].unique()))
        journey = pdf2[pdf2['ElementID'] == sel_elem].sort_values('Start')
        
        st.write("### 🛤️ Gevolgde Route")
        path_html = " ➔ ".join([f"<span style='background:#1e293b; color:white; padding:5px 15px; border-radius:20px;'>{u}</span>" for u in journey['Unit']])
        st.markdown(path_html, unsafe_allow_html=True)
        st.plotly_chart(px.timeline(journey, x_start="Start", x_end="End", y="Unit", color="Unit", text="Unit"), use_container_width=True)

    elif view == "🔥 Heatmaps":
        st.subheader("🔥 Productie-druk Matrix")
        heatmap_data = df.groupby(['Dagen', 'Unit'])['Meters'].sum().unstack().fillna(0)
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex([d for d in days_order if d in heatmap_data.index])
        st.plotly_chart(px.imshow(heatmap_data, color_continuous_scale='YlOrRd', aspect="auto"), use_container_width=True)

else:
    st.info("👋 Upload de CSV in het linker menu (nu wel leesbaar!) om te starten.")
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop")
