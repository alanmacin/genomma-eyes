"""
Genomma Eyes — Executive Intelligence Dashboard
"""

import os, random
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
from collections import Counter

# ── Config ──────────────────────────────────────────────────
st.set_page_config(page_title="Genomma Eyes", page_icon="👁️", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY", ""))
DEMO_MODE = not SUPABASE_URL or not SUPABASE_KEY

# ── Brand palette ───────────────────────────────────────────
GENOMMA_BLUE = "#003366"
GENOMMA_LIGHT = "#0072CE"
ACCENT_GREEN = "#00A86B"
ACCENT_RED = "#D0342C"
ACCENT_AMBER = "#F5A623"
ACCENT_GRAY = "#8C8C8C"

BRAND_COLORS = {
    "Suerox": "#00B4D8", "Cicatricure": "#9B2335", "Nikzon": "#6A0DAD",
    "Tío Nacho": "#DAA520", "Asepxia": "#2ECC71", "Lomecan V": "#E91E63",
    "Silka Medic": "#FF6B35", "Sistema GB": "#3498DB",
}

STOCK_COLORS = {"alto": ACCENT_GREEN, "medio": ACCENT_AMBER, "bajo": "#E67E22", "quiebre": ACCENT_RED}
SHELF_COLORS = {"superior": GENOMMA_LIGHT, "medio": ACCENT_AMBER, "inferior": ACCENT_GRAY}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0), font=dict(size=12),
)

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global */
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    h1, h2, h3 {color: #003366 !important;}

    /* KPI cards */
    .kpi-row {display: flex; gap: 12px; margin-bottom: 20px;}
    .kpi-card {
        flex: 1; padding: 18px 16px; border-radius: 12px;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e9ecef; box-shadow: 0 2px 8px rgba(0,0,0,.04);
        text-align: center;
    }
    .kpi-card .kpi-value {font-size: 2rem; font-weight: 700; color: #003366; line-height: 1.1;}
    .kpi-card .kpi-label {font-size: .78rem; color: #6c757d; text-transform: uppercase; letter-spacing: .5px; margin-top:4px;}
    .kpi-card .kpi-delta {font-size: .8rem; margin-top: 2px;}
    .kpi-card .kpi-delta.positive {color: #00A86B;}
    .kpi-card .kpi-delta.negative {color: #D0342C;}

    /* Section cards */
    .dash-card {
        padding: 20px; border-radius: 12px;
        background: #ffffff; border: 1px solid #e9ecef;
        box-shadow: 0 2px 8px rgba(0,0,0,.04); margin-bottom: 16px;
    }
    .dash-card h4 {margin: 0 0 12px 0; font-size: 1rem; color: #003366;}

    /* Alert cards */
    .alert-card {
        padding: 14px 18px; border-radius: 10px; margin-bottom: 10px;
        border-left: 4px solid; background: #fff;
        box-shadow: 0 1px 4px rgba(0,0,0,.06);
    }
    .alert-card.critical {border-color: #D0342C; background: #FFF5F5;}
    .alert-card.warning  {border-color: #F5A623; background: #FFFBF0;}
    .alert-card .alert-type {font-weight: 700; font-size: .85rem; text-transform: uppercase; letter-spacing: .3px;}
    .alert-card.critical .alert-type {color: #D0342C;}
    .alert-card.warning  .alert-type {color: #C68A00;}
    .alert-card .alert-desc {color: #333; margin-top: 4px;}
    .alert-card .alert-meta {font-size: .75rem; color: #888; margin-top: 6px;}

    /* Insight cards */
    .insight-card {
        padding: 14px 18px; border-radius: 10px; margin-bottom: 10px;
        border-left: 4px solid #0072CE; background: #F0F7FF;
        box-shadow: 0 1px 4px rgba(0,0,0,.06);
    }
    .insight-card .insight-tag {
        display: inline-block; font-size: .7rem; font-weight: 600; padding: 2px 8px;
        border-radius: 4px; background: #003366; color: white; margin-right: 6px;
    }
    .insight-card .insight-text {color: #1a1a1a; margin-top: 6px; font-size: .9rem; line-height: 1.4;}
    .insight-card .insight-meta {font-size: .75rem; color: #888; margin-top: 6px;}

    /* Brand pill */
    .brand-pill {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: .75rem; font-weight: 600; color: white; margin: 2px;
    }

    /* Quiebre gauge section */
    .gauge-container {display: flex; align-items: center; justify-content: center;}

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {gap: 4px;}
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px; border-radius: 8px 8px 0 0;
        font-weight: 600; font-size: .85rem;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}

    /* Scoreboard */
    .score-row {
        display: flex; align-items: center; padding: 10px 16px;
        border-radius: 8px; margin-bottom: 6px;
        background: linear-gradient(90deg, #f8f9fa 0%, #fff 100%);
        border: 1px solid #eee;
    }
    .score-row .rank {font-size: 1.2rem; font-weight: 800; color: #003366; width: 40px;}
    .score-row .name {flex: 1; font-weight: 600; color: #333;}
    .score-row .meta {font-size: .8rem; color: #888; flex: 1;}
    .score-row .pts {font-size: 1.1rem; font-weight: 700; color: #0072CE;}
</style>
""", unsafe_allow_html=True)


# ── Demo data generator ─────────────────────────────────────
@st.cache_data
def generate_demo_data():
    random.seed(42)
    now = datetime.now(timezone.utc)
    store_types = ["super", "farmacia", "conveniencia", "tradicional"]

    marcas_genomma = {
        "Suerox": "Hidratación", "Cicatricure": "Cuidado de piel",
        "Nikzon": "Salud digestiva", "Tío Nacho": "Cuidado capilar",
        "Asepxia": "Cuidado facial", "Lomecan V": "Salud femenina",
        "Silka Medic": "Cuidado de pies", "Sistema GB": "Cuidado capilar",
    }
    competencia_por_categoria = {
        "Hidratación": ["Electrolit", "Gatorade", "Powerade"],
        "Cuidado de piel": ["Pond's", "Nivea", "Eucerin", "La Roche-Posay"],
        "Salud digestiva": ["Pepto-Bismol", "Tums", "Sal de Uvas"],
        "Cuidado capilar": ["Head & Shoulders", "Pantene", "Dove", "TRESemmé"],
        "Cuidado facial": ["Neutrogena", "Clean & Clear", "Garnier"],
        "Salud femenina": ["Canesten", "Gynodaktarin"],
        "Cuidado de pies": ["Lotrimin", "Lamisil"],
    }
    stocks = ["alto", "medio", "bajo", "quiebre"]
    niveles = ["superior", "medio", "inferior"]

    alert_descs = {
        "quiebre_stock": ["{m} sin stock en anaquel principal", "{m} solo 1-2 unidades, reposición urgente", "Espacio de {m} vacío, competencia expandió facing"],
        "precio_incorrecto": ["{m} etiquetado $20 arriba de precio sugerido", "Promoción de {m} no aplicada en sistema"],
        "innovacion_competencia": ["{c} lanzó nueva línea en categoría {cat}", "{c} con display especial de piso en entrada", "{c} sampling activo en PDV"],
        "mal_exhibido": ["{m} en anaquel inferior, debería estar a nivel de ojos", "{m} detrás de competencia, visibilidad nula"],
        "producto_pirata": ["Empaque sospechoso de {m}, tipografía diferente", "Posible imitación de {m} junto a original"],
    }
    insight_tpls = [
        "Fuerte presencia de {m1} ({s1}) pero {m2} en quiebre. {c} aprovechando espacio vacante.",
        "Anaquel dominado por competencia en {cat}. {m1} relegada a posición inferior.",
        "{m1} bien posicionada con material POP activo. {c} sin presencia en tienda.",
        "Promoción 2x1 de {c} presionando a {m1} en {cat}. Precio de {m1} 15% más alto.",
        "Excelente ejecución: {m1} y {m2} en nivel de ojos con facing completo.",
        "Tienda nueva en zona, {c} ya presente. Oportunidad de entrada para {m1}.",
        "{m1} como líder de categoría con ~40% de facing estimado. {c} intentando ganar espacio.",
        "Temporada alta: {m1} con stock bajo en refrigerador. Riesgo de quiebre si no se repone.",
    ]

    nombres = [
        ("Carlos López", "México"), ("María García", "México"), ("Ana Torres", "Colombia"),
        ("Pedro Oliveira", "Brasil"), ("Lucía Fernández", "Argentina"), ("Roberto Díaz", "Chile"),
        ("Patricia Morales", "Perú"), ("Jorge Ramírez", "México"), ("Claudia Vargas", "Colombia"),
        ("Fernando Herrera", "USA"), ("Sofía Mendoza", "México"), ("Miguel Cruz", "Brasil"),
        ("Valentina Ríos", "Argentina"), ("Diego Castillo", "Chile"), ("Camila Paredes", "Perú"),
        ("Andrés Gutiérrez", "Colombia"), ("Laura Jiménez", "México"), ("Ricardo Salazar", "USA"),
        ("Isabella Rojas", "México"), ("Tomás Acosta", "Argentina"),
        ("Daniela Soto", "Ecuador"), ("Luis Mejía", "Guatemala"), ("Karen Flores", "México"),
        ("Javier Reyes", "Colombia"), ("Paula Navarro", "Chile"),
    ]
    employees = [{"id": f"emp-{i+1:03d}", "name": n, "area": random.choice(["Ventas","Trade Marketing","Operaciones","Marketing","Comercial"]), "country": c, "total_points": random.randint(30,580), "active": True} for i,(n,c) in enumerate(nombres)]

    visits, all_alerts = [], []
    for i in range(300):
        emp = random.choice(employees)
        store = random.choice(store_types)
        created = now - timedelta(days=random.randint(0,45), hours=random.randint(6,22))
        sel_brands = random.sample(list(marcas_genomma.keys()), random.randint(1,5))
        brand_det, comp_det, cats = [], [], set()
        for m in sel_brands:
            cat = marcas_genomma[m]; cats.add(cat)
            s = random.choices(stocks, weights=[30,40,20,10])[0]
            brand_det.append({"marca":m,"producto":f"Producto {m}","nivel_anaquel":random.choice(niveles),"stock_visible":s})
            if cat in competencia_por_categoria and random.random()>0.3:
                cc = random.choice(competencia_por_categoria[cat])
                comp_det.append({"marca":cc,"producto":f"Producto {cc}","categoria":cat,"observacion":random.choice(["Precio más bajo","Promoción activa","Display especial","Nuevo empaque","Sin novedad","Mayor facing","Sampling"])})
        v_alerts = []
        if random.random()<0.25:
            at = random.choices(["quiebre_stock","precio_incorrecto","innovacion_competencia","mal_exhibido","producto_pirata"],weights=[35,20,25,15,5])[0]
            mm = random.choice(sel_brands); ccat = marcas_genomma[mm]
            cc2 = random.choice(competencia_por_categoria.get(ccat,["Competidor"]))
            desc = random.choice(alert_descs[at]).format(m=mm,c=cc2,cat=ccat)
            v_alerts.append({"tipo":at,"descripcion":desc})
        pop_p = random.random()>0.45
        m1,m2 = sel_brands[0], sel_brands[1] if len(sel_brands)>1 else sel_brands[0]
        cat1 = marcas_genomma.get(m1,"Cuidado personal")
        cc3 = random.choice(competencia_por_categoria.get(cat1,["Competidor"]))
        insight = random.choice(insight_tpls).format(m1=m1,m2=m2,s1=brand_det[0]["stock_visible"],c=cc3,cat=cat1)
        analysis = {"tipo_tienda":store,"marcas_genomma":brand_det,"competencia":comp_det,"alertas":v_alerts,"material_pop":{"presente":pop_p,"marca":random.choice(sel_brands) if pop_p else None},"insight_principal":insight}
        vid = f"visit-{i+1:03d}"
        visits.append({"id":vid,"employee_id":emp["id"],"employee_name":emp["name"],"country":emp["country"],"store_type":store,"points_earned":35 if random.random()<0.15 else 10,"ai_analysis":analysis,"created_at":created.isoformat(),"lat":round(random.uniform(14,33),4),"lng":round(random.uniform(-117,-43),4)})
        for a in v_alerts:
            all_alerts.append({"id":f"alert-{len(all_alerts)+1:03d}","visit_id":vid,"employee_id":emp["id"],"employee_name":emp["name"],"alert_type":a["tipo"],"description":a["descripcion"],"country":emp["country"],"store_type":store,"resolved":random.random()<0.2,"created_at":created.isoformat()})
    quests = [
        {"id":"q-001","title":"Operación Suerox Verano","description":"Documenta presencia de Suerox en refrigeradores de conveniencias.","prize_amount":5000,"countries":["México","Colombia","Chile"],"start_date":"2026-03-01","end_date":"2026-03-31","target_brand":"Suerox","active":True},
        {"id":"q-002","title":"Caza de Piratas Cicatricure","description":"Reporta cualquier producto sospechoso de ser imitación de Cicatricure.","prize_amount":10000,"countries":["México","Brasil","Argentina","Colombia","Perú","Chile"],"start_date":"2026-03-15","end_date":"2026-04-15","target_brand":"Cicatricure","active":True},
    ]
    return {"employees":pd.DataFrame(employees),"visits":pd.DataFrame(visits),"alerts":pd.DataFrame([a for a in all_alerts if not a["resolved"]]),"quests":pd.DataFrame(quests)}


# ── Extractors ──────────────────────────────────────────────
def extract_brands(vdf):
    rows = []
    for _,v in vdf.iterrows():
        a = v.get("ai_analysis")
        if not isinstance(a,dict): continue
        for b in a.get("marcas_genomma",[]):
            if isinstance(b,dict):
                rows.append({**b, "country":v.get("country",""), "store_type":v.get("store_type",""), "created_at":v.get("created_at")})
    df = pd.DataFrame(rows)
    if "stock_visible" in df.columns:
        df.rename(columns={"stock_visible":"stock"}, inplace=True)
    return df

def extract_comp(vdf):
    rows = []
    for _,v in vdf.iterrows():
        a = v.get("ai_analysis")
        if not isinstance(a,dict): continue
        for c in a.get("competencia",[]):
            if isinstance(c,dict):
                rows.append({**c, "country":v.get("country",""), "store_type":v.get("store_type",""), "created_at":v.get("created_at")})
    return pd.DataFrame(rows)

def extract_pop(vdf):
    total = present = 0
    by_brand = Counter()
    for _,v in vdf.iterrows():
        a = v.get("ai_analysis")
        if not isinstance(a,dict): continue
        pop = a.get("material_pop",{})
        if isinstance(pop,dict):
            total += 1
            if pop.get("presente"):
                present += 1
                if pop.get("marca"): by_brand[pop["marca"]] += 1
    return total, present, by_brand


# ── HTML helpers ────────────────────────────────────────────
def kpi_card(value, label, delta=None, delta_dir="positive"):
    delta_html = f'<div class="kpi-delta {delta_dir}">{delta}</div>' if delta else ""
    return f'<div class="kpi-card"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div>{delta_html}</div>'

def alert_card_html(atype, desc, country, store, date_str, reporter):
    is_crit = atype in ("quiebre_stock","producto_pirata","precio_incorrecto")
    cls = "critical" if is_crit else "warning"
    icon = "🔴" if is_crit else "🟡"
    return f'''<div class="alert-card {cls}">
        <div class="alert-type">{icon} {atype.replace("_"," ")}</div>
        <div class="alert-desc">{desc}</div>
        <div class="alert-meta">📍 {country} · {store} · 📅 {date_str} · 👤 {reporter}</div>
    </div>'''

def insight_card_html(store_type, insight, date_str, brands_n, employee, has_alert):
    alert_badge = ' <span style="color:#D0342C;font-weight:700">⚠ ALERTA</span>' if has_alert else ""
    return f'''<div class="insight-card">
        <span class="insight-tag">{store_type.upper()}</span>{alert_badge}
        <div class="insight-text">{insight}</div>
        <div class="insight-meta">📅 {date_str} · 🏷️ {brands_n} marcas · 👤 {employee}</div>
    </div>'''

def score_row_html(rank, name, country, area, pts):
    medal = {1:"🥇",2:"🥈",3:"🥉"}.get(rank, str(rank))
    return f'''<div class="score-row">
        <div class="rank">{medal}</div>
        <div class="name">{name}</div>
        <div class="meta">{country} · {area}</div>
        <div class="pts">{pts} pts</div>
    </div>'''


# ── Header ──────────────────────────────────────────────────
hdr1, hdr2 = st.columns([1, 6])
with hdr1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Genomma_Lab_Internacional_logo.svg/200px-Genomma_Lab_Internacional_logo.svg.png", width=100)
with hdr2:
    st.markdown(f"<h1 style='margin:0;padding:0;font-size:2rem'>Genomma Eyes</h1><span style='color:#6c757d;font-size:.9rem'>Inteligencia de punto de venta en tiempo real — 18 países</span>", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────
st.sidebar.markdown(f"<h3 style='color:{GENOMMA_BLUE}'>Filtros</h3>", unsafe_allow_html=True)
countries = ["Todos","México","USA","Brasil","Argentina","Colombia","Chile","Perú","Ecuador","Guatemala","Honduras","El Salvador","Costa Rica","Nicaragua","Panamá","Bolivia","Paraguay","Rep. Dominicana"]
selected_country = st.sidebar.selectbox("País", countries)
selected_store = st.sidebar.selectbox("Canal", ["Todos","super","farmacia","conveniencia","tradicional"])
selected_marca = st.sidebar.selectbox("Marca", ["Todas","Suerox","Cicatricure","Nikzon","Tío Nacho","Asepxia","Lomecan V","Silka Medic","Sistema GB"])
period_map = {"7 días":7,"14 días":14,"30 días":30,"Todo":999}
selected_days = period_map[st.sidebar.selectbox("Período", list(period_map.keys()), index=2)]
if DEMO_MODE:
    st.sidebar.markdown("---")
    st.sidebar.caption("⚡ Modo demo — datos simulados")

# ── Load & filter ───────────────────────────────────────────
data = generate_demo_data()
vdf = data["visits"].copy(); edf = data["employees"].copy(); adf = data["alerts"].copy(); qdf = data["quests"].copy()
vdf["created_at"] = pd.to_datetime(vdf["created_at"]); adf["created_at"] = pd.to_datetime(adf["created_at"])
cutoff = datetime.now(timezone.utc) - timedelta(days=selected_days)
vdf = vdf[vdf["created_at"]>=cutoff]; adf = adf[adf["created_at"]>=cutoff]
if selected_country!="Todos":
    vdf=vdf[vdf["country"]==selected_country]; edf=edf[edf["country"]==selected_country]; adf=adf[adf["country"]==selected_country]
if selected_store!="Todos":
    vdf=vdf[vdf["store_type"]==selected_store]
if selected_marca!="Todas":
    vdf=vdf[vdf["ai_analysis"].apply(lambda a: isinstance(a,dict) and any(b.get("marca")==selected_marca for b in a.get("marcas_genomma",[]) if isinstance(b,dict)))]

bdf = extract_brands(vdf); cdf = extract_comp(vdf); pop_total, pop_present, pop_by_brand = extract_pop(vdf)
pop_rate = round(pop_present/max(pop_total,1)*100)
quiebre_n = len(bdf[bdf["stock"]=="quiebre"]) if not bdf.empty else 0
quiebre_rate = round(quiebre_n/max(len(bdf),1)*100,1)

# ── KPI Row ─────────────────────────────────────────────────
st.markdown('<div class="kpi-row">' +
    kpi_card(f"{len(vdf):,}", "Visitas registradas") +
    kpi_card(f"{vdf['country'].nunique() if not vdf.empty else 0}", "Países activos") +
    kpi_card(f"{len(bdf):,}", "Detecciones de marca") +
    kpi_card(f"{pop_rate}%", "Presencia POP") +
    kpi_card(f"{quiebre_rate}%", "Tasa de quiebre", delta=f"▼ {quiebre_n} detecciones", delta_dir="negative" if quiebre_rate>8 else "positive") +
    kpi_card(f"{len(adf)}", "Alertas activas", delta_dir="negative" if len(adf)>20 else "positive") +
'</div>', unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────
tab_exec, tab_brands, tab_comp, tab_alerts, tab_cov, tab_insights, tab_game = st.tabs([
    "📈 Resumen", "🏷️ Marcas", "🔍 Competencia", "🚨 Alertas", "🗺️ Cobertura", "🧠 Insights", "🏆 Ranking"
])

# ================================================================
# TAB: RESUMEN EJECUTIVO
# ================================================================
with tab_exec:
    if vdf.empty:
        st.info("No hay datos para los filtros seleccionados.")
    else:
        r1a, r1b = st.columns(2)

        with r1a:
            st.markdown('<div class="dash-card"><h4>Presencia de marca (detecciones)</h4>', unsafe_allow_html=True)
            if not bdf.empty:
                bc = bdf["marca"].value_counts().reset_index(); bc.columns=["Marca","Detecciones"]
                fig = px.bar(bc, y="Marca", x="Detecciones", orientation="h", color="Marca",
                    color_discrete_map=BRAND_COLORS, text="Detecciones")
                fig.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with r1b:
            st.markdown('<div class="dash-card"><h4>Volumen de visitas (tendencia diaria)</h4>', unsafe_allow_html=True)
            vdf["date"] = vdf["created_at"].dt.date
            daily = vdf.groupby("date").size().reset_index(name="Visitas").sort_values("date")
            fig = px.area(daily, x="date", y="Visitas", color_discrete_sequence=[GENOMMA_LIGHT])
            fig.update_layout(**PLOTLY_LAYOUT, height=350, xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        r2a, r2b = st.columns(2)

        with r2a:
            st.markdown('<div class="dash-card"><h4>Nivel de stock por marca</h4>', unsafe_allow_html=True)
            if not bdf.empty:
                sp = bdf.groupby(["marca","stock"]).size().reset_index(name="n")
                fig = px.bar(sp, x="marca", y="n", color="stock", color_discrete_map=STOCK_COLORS,
                    barmode="stack", text="n")
                fig.update_layout(**PLOTLY_LAYOUT, height=320, xaxis_title="", yaxis_title="", legend_title="")
                fig.update_traces(textposition="inside")
                st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with r2b:
            st.markdown('<div class="dash-card"><h4>Distribución por canal</h4>', unsafe_allow_html=True)
            ch = vdf["store_type"].value_counts().reset_index(); ch.columns=["Canal","Visitas"]
            channel_colors = {"super":"#3498DB","farmacia":"#2ECC71","conveniencia":"#F39C12","tradicional":"#9B59B6"}
            fig = px.pie(ch, names="Canal", values="Visitas", color="Canal", color_discrete_map=channel_colors, hole=0.45)
            fig.update_layout(**PLOTLY_LAYOUT, height=320, legend=dict(orientation="h",y=-0.1))
            fig.update_traces(textinfo="percent+label", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Tabla resumen
        st.markdown('<div class="dash-card"><h4>Resumen por marca</h4>', unsafe_allow_html=True)
        if not bdf.empty:
            summary = bdf.groupby("marca").agg(
                Detecciones=("marca","size"),
                Alto=("stock", lambda x:(x=="alto").sum()),
                Medio=("stock", lambda x:(x=="medio").sum()),
                Bajo=("stock", lambda x:(x=="bajo").sum()),
                Quiebres=("stock", lambda x:(x=="quiebre").sum()),
            ).sort_values("Detecciones", ascending=False)
            summary["% Quiebre"] = (summary["Quiebres"]/summary["Detecciones"]*100).round(1)

            # Tabla con color condicional via Plotly (sin matplotlib)
            s = summary.reset_index()
            colors = []
            for pct in s["% Quiebre"]:
                if pct >= 15: colors.append("#FFCCCC")
                elif pct >= 8: colors.append("#FFF3CD")
                else: colors.append("#D4EDDA")
            fig_table = go.Figure(data=[go.Table(
                header=dict(values=list(s.columns), fill_color=GENOMMA_BLUE, font=dict(color="white", size=13), align="center"),
                cells=dict(values=[s[c] for c in s.columns],
                    fill_color=[["white"]*len(s), ["white"]*len(s), ["white"]*len(s), ["white"]*len(s), ["white"]*len(s), colors],
                    font=dict(size=12), align="center", format=[None, None, None, None, None, ".1f"]),
            )])
            fig_table.update_layout(**PLOTLY_LAYOUT, height=max(200, 40*len(s)+60))
            st.plotly_chart(fig_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# TAB: MARCAS
# ================================================================
with tab_brands:
    if bdf.empty:
        st.info("Sin detecciones de marca.")
    else:
        ba, bb = st.columns(2)
        with ba:
            st.markdown('<div class="dash-card"><h4>Marca × Canal</h4>', unsafe_allow_html=True)
            ct = pd.crosstab(bdf["marca"], bdf["store_type"])
            fig = px.imshow(ct, text_auto=True, color_continuous_scale=["#f0f7ff",GENOMMA_LIGHT,GENOMMA_BLUE], aspect="auto")
            fig.update_layout(**PLOTLY_LAYOUT, height=380, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with bb:
            st.markdown('<div class="dash-card"><h4>Posición en anaquel</h4>', unsafe_allow_html=True)
            sp2 = bdf.groupby(["marca","nivel_anaquel"]).size().reset_index(name="n")
            fig = px.bar(sp2, x="marca", y="n", color="nivel_anaquel", color_discrete_map=SHELF_COLORS, barmode="group")
            fig.update_layout(**PLOTLY_LAYOUT, height=380, xaxis_title="", yaxis_title="", legend_title="")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if selected_country == "Todos" and not bdf.empty:
            st.markdown('<div class="dash-card"><h4>Presencia de marca × País (heatmap)</h4>', unsafe_allow_html=True)
            ct2 = pd.crosstab(bdf["marca"], bdf["country"])
            fig = px.imshow(ct2, text_auto=True, color_continuous_scale=["#f0f7ff",GENOMMA_LIGHT,GENOMMA_BLUE], aspect="auto")
            fig.update_layout(**PLOTLY_LAYOUT, height=400, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # POP
        pa, pb = st.columns(2)
        with pa:
            st.markdown('<div class="dash-card"><h4>Material POP — Presencia</h4>', unsafe_allow_html=True)
            fig = go.Figure(go.Indicator(mode="gauge+number", value=pop_rate, number={"suffix":"%"},
                gauge={"axis":{"range":[0,100]},"bar":{"color":ACCENT_GREEN if pop_rate>60 else ACCENT_AMBER},
                    "steps":[{"range":[0,40],"color":"#FFF0F0"},{"range":[40,70],"color":"#FFFBE6"},{"range":[70,100],"color":"#F0FFF0"}]}))
            fig.update_layout(**PLOTLY_LAYOUT, height=250)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with pb:
            st.markdown('<div class="dash-card"><h4>POP por marca</h4>', unsafe_allow_html=True)
            if pop_by_brand:
                pbs = pd.DataFrame(pop_by_brand.most_common(8), columns=["Marca","Visitas con POP"])
                fig = px.bar(pbs, x="Visitas con POP", y="Marca", orientation="h", color="Marca", color_discrete_map=BRAND_COLORS)
                fig.update_layout(**PLOTLY_LAYOUT, height=250, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# TAB: COMPETENCIA
# ================================================================
with tab_comp:
    if cdf.empty:
        st.info("Sin detecciones de competencia.")
    else:
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="dash-card"><h4>Top competidores</h4>', unsafe_allow_html=True)
            cc = cdf["marca"].value_counts().head(12).reset_index(); cc.columns=["Competidor","Detecciones"]
            fig = px.bar(cc, y="Competidor", x="Detecciones", orientation="h", color_discrete_sequence=["#E74C3C"], text="Detecciones")
            fig.update_layout(**PLOTLY_LAYOUT, height=400)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="dash-card"><h4>Tipo de actividad detectada</h4>', unsafe_allow_html=True)
            if "observacion" in cdf.columns:
                obs = cdf["observacion"].value_counts().reset_index(); obs.columns=["Actividad","Conteo"]
                act_colors = {"Promoción activa":"#E74C3C","Display especial":"#E67E22","Sampling":"#F1C40F","Mayor facing":"#9B59B6","Precio más bajo":"#3498DB","Nuevo empaque":"#1ABC9C","Sin novedad":"#BDC3C7"}
                fig = px.pie(obs, names="Actividad", values="Conteo", color="Actividad", color_discrete_map=act_colors, hole=0.4)
                fig.update_layout(**PLOTLY_LAYOUT, height=400, legend=dict(orientation="h",y=-0.15))
                st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="dash-card"><h4>Competencia × Categoría (heatmap)</h4>', unsafe_allow_html=True)
        if "categoria" in cdf.columns:
            ct3 = pd.crosstab(cdf["marca"], cdf["categoria"])
            fig = px.imshow(ct3, text_auto=True, color_continuous_scale=["#fff5f5","#E74C3C","#7B241C"], aspect="auto")
            fig.update_layout(**PLOTLY_LAYOUT, height=380, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# TAB: ALERTAS
# ================================================================
with tab_alerts:
    if adf.empty:
        st.markdown('<div class="dash-card" style="text-align:center;padding:40px"><h4 style="color:#00A86B">✅ Sin alertas activas</h4></div>', unsafe_allow_html=True)
    else:
        aa, ab, ac = st.columns(3)
        with aa:
            st.markdown('<div class="dash-card"><h4>Por tipo</h4>', unsafe_allow_html=True)
            at_c = adf["alert_type"].value_counts().reset_index(); at_c.columns=["Tipo","Conteo"]
            type_colors = {"quiebre_stock":ACCENT_RED,"producto_pirata":"#7B241C","precio_incorrecto":"#E67E22","mal_exhibido":ACCENT_AMBER,"innovacion_competencia":"#3498DB"}
            fig = px.bar(at_c, x="Tipo", y="Conteo", color="Tipo", color_discrete_map=type_colors)
            fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with ab:
            st.markdown('<div class="dash-card"><h4>Por país</h4>', unsafe_allow_html=True)
            ac2 = adf["country"].value_counts().reset_index(); ac2.columns=["País","Alertas"]
            fig = px.bar(ac2, y="País", x="Alertas", orientation="h", color_discrete_sequence=[ACCENT_RED])
            fig.update_layout(**PLOTLY_LAYOUT, height=280)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with ac:
            st.markdown('<div class="dash-card"><h4>Por canal</h4>', unsafe_allow_html=True)
            ac3 = adf["store_type"].value_counts().reset_index(); ac3.columns=["Canal","Alertas"]
            fig = px.pie(ac3, names="Canal", values="Alertas", hole=0.5, color_discrete_sequence=px.colors.sequential.OrRd)
            fig.update_layout(**PLOTLY_LAYOUT, height=280)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Alert cards
        st.markdown('<div class="dash-card"><h4>Alertas recientes</h4>', unsafe_allow_html=True)
        sev = {"producto_pirata":0,"quiebre_stock":1,"precio_incorrecto":2,"mal_exhibido":3,"innovacion_competencia":4}
        sa = adf.copy(); sa["sev"]=sa["alert_type"].map(sev).fillna(5); sa=sa.sort_values(["sev","created_at"],ascending=[True,False])
        html = ""
        for _,al in sa.head(20).iterrows():
            ds = al["created_at"].strftime("%d %b") if hasattr(al["created_at"],"strftime") else ""
            html += alert_card_html(al["alert_type"],al["description"],al["country"],al.get("store_type",""),ds,al.get("employee_name",""))
        st.markdown(html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# TAB: COBERTURA
# ================================================================
with tab_cov:
    if vdf.empty:
        st.info("Sin datos de cobertura.")
    else:
        ca2, cb2 = st.columns(2)
        with ca2:
            st.markdown('<div class="dash-card"><h4>Cobertura: País × Canal</h4>', unsafe_allow_html=True)
            cov = pd.crosstab(vdf["country"], vdf["store_type"])
            fig = px.imshow(cov, text_auto=True, color_continuous_scale=["#f8f9fa",GENOMMA_LIGHT,GENOMMA_BLUE], aspect="auto")
            fig.update_layout(**PLOTLY_LAYOUT, height=400, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cb2:
            st.markdown('<div class="dash-card"><h4>Visitas por empleado (Top 15)</h4>', unsafe_allow_html=True)
            vpe = vdf.groupby("employee_name").size().reset_index(name="Visitas").sort_values("Visitas",ascending=False).head(15)
            fig = px.bar(vpe, y="employee_name", x="Visitas", orientation="h", color_discrete_sequence=[GENOMMA_LIGHT], text="Visitas")
            fig.update_layout(**PLOTLY_LAYOUT, height=400, yaxis_title="")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if "lat" in vdf.columns:
            st.markdown('<div class="dash-card"><h4>Mapa de visitas</h4>', unsafe_allow_html=True)
            mdf = vdf[["lat","lng","country","store_type"]].dropna()
            fig = px.scatter_map(mdf, lat="lat", lon="lng", color="store_type", hover_data=["country"],
                color_discrete_map={"super":"#3498DB","farmacia":"#2ECC71","conveniencia":"#F39C12","tradicional":"#9B59B6"},
                map_style="carto-positron", zoom=2, height=500)
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), legend_title="Canal")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# TAB: INSIGHTS
# ================================================================
with tab_insights:
    if vdf.empty:
        st.info("Sin insights.")
    else:
        # Accionables arriba
        st.markdown('<div class="dash-card"><h4>Hallazgos accionables</h4>', unsafe_allow_html=True)
        cols_act = st.columns(2)
        with cols_act[0]:
            if not bdf.empty:
                qb = bdf[bdf["stock"]=="quiebre"].groupby("marca").size()
                tb = bdf.groupby("marca").size()
                qp = (qb/tb*100).dropna().sort_values(ascending=False)
                if not qp.empty:
                    st.markdown("**Marcas con mayor riesgo de quiebre**")
                    for m,p in qp.head(5).items():
                        color = ACCENT_RED if p>15 else ACCENT_AMBER
                        st.markdown(f'<div style="display:flex;align-items:center;margin-bottom:4px"><div style="width:10px;height:10px;border-radius:50%;background:{color};margin-right:8px"></div><strong>{m}</strong>: {p:.0f}% quiebre</div>', unsafe_allow_html=True)
        with cols_act[1]:
            if not cdf.empty and "observacion" in cdf.columns:
                promos = cdf[cdf["observacion"].isin(["Promoción activa","Display especial","Sampling"])]
                if not promos.empty:
                    st.markdown("**Competencia con actividad agresiva**")
                    for m,n in promos.groupby("marca").size().sort_values(ascending=False).head(5).items():
                        st.markdown(f'<div style="display:flex;align-items:center;margin-bottom:4px"><div style="width:10px;height:10px;border-radius:50%;background:#E74C3C;margin-right:8px"></div><strong>{m}</strong>: {n} acciones en PDV</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Insight cards por país
        for country in sorted(vdf["country"].unique()):
            cv = vdf[vdf["country"]==country].sort_values("created_at", ascending=False)
            st.markdown(f'<div class="dash-card"><h4>📍 {country} — {len(cv)} visitas</h4>', unsafe_allow_html=True)
            html = ""
            for _,v in cv.head(8).iterrows():
                a = v.get("ai_analysis")
                if isinstance(a,dict) and a.get("insight_principal"):
                    ds = v["created_at"].strftime("%d %b %H:%M") if hasattr(v["created_at"],"strftime") else ""
                    html += insight_card_html(v.get("store_type",""), a["insight_principal"], ds, len(a.get("marcas_genomma",[])), v.get("employee_name",""), len(a.get("alertas",[]))>0)
            st.markdown(html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# TAB: GAMIFICACIÓN
# ================================================================
with tab_game:
    es = edf.sort_values("total_points", ascending=False)
    if not es.empty:
        st.markdown('<div class="dash-card"><h4>Top empleados</h4>', unsafe_allow_html=True)
        html = ""
        for i,(_, r) in enumerate(es.head(15).iterrows()):
            html += score_row_html(i+1, r["name"], r["country"], r["area"], r["total_points"])
        st.markdown(html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if not qdf.empty:
        st.markdown('<div class="dash-card"><h4>Misiones activas</h4>', unsafe_allow_html=True)
        for _,q in qdf.iterrows():
            cc = q.get("countries",[]); cc = [cc] if isinstance(cc,str) else cc
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border-radius:8px;background:#f8f9fa;margin-bottom:8px;border-left:4px solid {GENOMMA_LIGHT}">
                <div><strong>{q['title']}</strong><br><span style="color:#666;font-size:.85rem">{q['description']}</span><br><span style="font-size:.75rem;color:#888">🎯 {q.get('target_brand','Todas')} · 🌎 {', '.join(cc)}</span></div>
                <div style="text-align:right"><div style="font-size:1.4rem;font-weight:700;color:{GENOMMA_BLUE}">${q['prize_amount']:,.0f}</div><div style="font-size:.75rem;color:#888">MXN</div></div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────
st.markdown(f"""<div style="text-align:center;padding:20px 0;color:#aaa;font-size:.75rem">
    Genomma Eyes v1.0 · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · Powered by Claude Vision
</div>""", unsafe_allow_html=True)
