"""
DashBoard - Cash Flow Forecasting System
========================================
Dashboard web interactivo con Streamlit + Plotly
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cash Flow Forecasting - Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────
# CSS PERSONALIZADO
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fondo principal */
    .main { background-color: #0e1117; }
    
    /* Cards KPIs */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        margin: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-2px); }
    
    .kpi-label {
        font-size: 14px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
    }
    .kpi-sub {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
    }
    
    /* Badge de riesgo */
    .risk-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
    }
    .risk-alto { background: #7f1d1d; color: #fca5a5; }
    .risk-medio { background: #78350f; color: #fdba74; }
    .risk-bajo { background: #14532d; color: #86efac; }
    
    /* Título del dashboard */
    .dashboard-title {
        color: #f1f5f9;
        font-size: 32px;
        font-weight: 700;
        text-align: center;
        padding: 20px 0;
        border-bottom: 1px solid #334155;
        margin-bottom: 24px;
    }
    
    /* Secciones */
    .section-title {
        color: #e2e8f0;
        font-size: 22px;
        font-weight: 600;
        padding: 12px 0;
        border-left: 4px solid #3b82f6;
        padding-left: 16px;
        margin: 20px 0 16px 0;
    }
    
    /* Tooltip info */
    .info-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        color: #cbd5e1;
        font-size: 13px;
    }
    
    /* Sombreado de tarjetas métricas */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    
    /* Métrica título */
    .metric-title {
        color: #64748b;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
# FUNCIONES DE CARGA DE DATOS
# ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent

@st.cache_data
def load_cashflow():
    path = PROJECT_ROOT / "powerbi" / "cash_flow_daily.csv"
    if not path.exists():
        path = PROJECT_ROOT / "data" / "processed" / "cash_flow_daily.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    return df

@st.cache_data
def load_forecast():
    path = PROJECT_ROOT / "powerbi" / "forecast_results.csv"
    if not path.exists():
        path = PROJECT_ROOT / "models" / "forecast_results.csv"
    df = pd.read_csv(path, parse_dates=["ds"])
    return df

@st.cache_data
def load_kpis():
    path = PROJECT_ROOT / "powerbi" / "kpis.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["report_date"])
    return df

@st.cache_data
def load_crm():
    path = PROJECT_ROOT / "data" / "processed" / "crm_deals_clean.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["created_date", "expected_close", "actual_close"])
    return df

@st.cache_data
def load_invoices():
    path = PROJECT_ROOT / "data" / "processed" / "invoices_clean.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["invoice_date", "paid_date"])
    return df

@st.cache_data
def load_metrics():
    path = PROJECT_ROOT / "models" / "model_metrics.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)

@st.cache_data
def load_forecast_summary():
    path = PROJECT_ROOT / "models" / "forecast_summary.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ──────────────────────────────────────────────────────────────────
with st.spinner("Cargando datos..."):
    cashflow = load_cashflow()
    forecast = load_forecast()
    kpis = load_kpis()
    crm = load_crm()
    invoices = load_invoices()
    metrics = load_metrics()
    forecast_summary = load_forecast_summary()

# Verificar si hay datos
if cashflow.empty or forecast.empty:
    st.error("❌ No se encontraron datos. Ejecuta `python main.py` primero para generar los datos.")
    st.stop()


# ──────────────────────────────────────────────────────────────────
# TÍTULO Y NAVEGACIÓN
# ──────────────────────────────────────────────────────────────────
st.markdown('<div class="dashboard-title">💰 Cash Flow Forecasting — Industrial Metálica Portillo S.L.</div>', unsafe_allow_html=True)

# Sidebar - Filtros globales
with st.sidebar:
    st.markdown("## 📅 Filtros")
    min_date = cashflow["date"].min()
    max_date = cashflow["date"].max()
    
    date_range = st.date_input(
        "Rango de fechas",
        value=(max_date - timedelta(days=365), max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = min_date
        end_date = max_date
    
    st.markdown("---")
    st.markdown("## 📊 Métricas del modelo")
    
    model_metrics = metrics.get("model_metrics", {})
    if model_metrics:
        col1, col2 = st.columns(2)
        col1.metric("MAPE", f"{model_metrics.get('mape', 'N/A')}%")
        col2.metric("MAE", f"${model_metrics.get('mae', 'N/A'):,}")
        col1.metric("RMSE", f"${model_metrics.get('rmse', 'N/A'):,}")
        col2.metric("Coverage 95%", f"{model_metrics.get('coverage_95', 'N/A')}%")
    
    st.markdown("---")
    st.markdown("## ℹ️ Información")
    st.markdown(f"**Cash flow:** {len(cashflow):,} días")
    st.markdown(f"**Forecast:** {len(forecast):,} días")
    st.markdown(f"**Facturas:** {len(invoices):,}" if not invoices.empty else "")
    st.markdown(f"**CRM Deals:** {len(crm):,}" if not crm.empty else "")
    st.markdown(f"**Última actualización:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ──────────────────────────────────────────────────────────────────
# FILTRAR DATOS POR FECHA
# ──────────────────────────────────────────────────────────────────
start_ts = pd.Timestamp(start_date)
end_ts = pd.Timestamp(end_date)

cashflow_filtered = cashflow[(cashflow["date"] >= start_ts) & (cashflow["date"] <= end_ts)].copy()
forecast_filtered = forecast[(forecast["ds"] >= start_ts) & (forecast["ds"] <= end_ts)].copy()


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 1: KPI CARDS
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📊 KPIs Principales</div>', unsafe_allow_html=True)

# KPI data
if not kpis.empty:
    latest_kpi = kpis.iloc[-1]
    current_balance = latest_kpi.get("current_cash_balance", 0)
    inflow_30d = latest_kpi.get("cash_inflow_30d", 0)
    outflow_30d = latest_kpi.get("cash_outflow_30d", 0)
    forecast_90d = latest_kpi.get("forecast_90d", 0)
    risk = latest_kpi.get("liquidity_risk", "BAJO")
else:
    today = cashflow["date"].max()
    current_balance = cashflow[cashflow["date"] == today]["cash_balance"].values[0] if today in cashflow["date"].values else 0
    inflow_30d = cashflow[cashflow["date"] >= today - timedelta(days=30)]["cash_inflow"].sum()
    outflow_30d = cashflow[cashflow["date"] >= today - timedelta(days=30)]["cash_outflow"].sum()
    
    target_date = today + timedelta(days=90)
    forecast_90d = forecast.iloc[(forecast["ds"] - target_date).abs().idxmin()]["yhat"] if not forecast.empty else 0
    risk = "ALTO" if forecast_90d < 25000 else "MEDIO" if forecast_90d < 50000 else "BAJO"

net_30d = inflow_30d - outflow_30d
risk_class = f"risk-{risk.lower()}" if risk else "risk-bajo"
risk_color = "#ef4444" if risk == "ALTO" else "#f59e0b" if risk == "MEDIO" else "#22c55e"

# 4 columnas KPI
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💵 Saldo Actual</div>
        <div class="kpi-value">${current_balance:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📈 Ingresos 30d</div>
        <div class="kpi-value" style="color: #22c55e;">+${inflow_30d:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📉 Gastos 30d</div>
        <div class="kpi-value" style="color: #ef4444;">-${outflow_30d:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🎯 Neto 30d</div>
        <div class="kpi-value" style="color: {"#22c55e" if net_30d >= 0 else "#ef4444"};">
            {"+" if net_30d >= 0 else "-"}${abs(net_30d):,.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Segunda fila de KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📊 Forecast 90d</div>
        <div class="kpi-value" style="color: #60a5fa;">${forecast_90d:,.0f}</div>
        <div class="kpi-sub">Proyección a 90 días</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">⚠️ Riesgo Liquidez</div>
        <div><span class="risk-badge {risk_class}">{risk}</span></div>
        <div class="kpi-sub">{"Por debajo del umbral" if risk == "ALTO" else "Monitoreo normal" if risk == "MEDIO" else "Saludable"}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Saldo mínimo del forecast
    min_forecast = forecast_filtered["yhat"].min() if not forecast_filtered.empty else 0
    days_below = (forecast_filtered["yhat"] < 50000).sum() if not forecast_filtered.empty else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">⬇️ Saldo Mínimo</div>
        <div class="kpi-value" style="color: {"#ef4444" if min_forecast < 25000 else "#f59e0b"};">
            ${min_forecast:,.0f}
        </div>
        <div class="kpi-sub">{days_below} días por debajo de umbral</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    # MAPE del modelo
    mape_val = model_metrics.get("mape", 0)
    mape_color = "#22c55e" if mape_val < 5 else "#f59e0b" if mape_val < 10 else "#ef4444"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🎯 Precisión Modelo</div>
        <div class="kpi-value" style="color: {mape_color};">{mape_val:.2f}%</div>
        <div class="kpi-sub">MAPE — {"Excelente" if mape_val < 5 else "Aceptable" if mape_val < 10 else "Revisar"}</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 2: FORECAST vs REAL
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📈 Forecast vs Real — Comparación</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    # Merge forecast con cashflow real
    merged = forecast_filtered.merge(
        cashflow_filtered[["date", "cash_balance"]],
        left_on="ds",
        right_on="date",
        how="left"
    )
    merged_filtered = merged.dropna(subset=["cash_balance"]).head(500)
    
    fig = go.Figure()
    
    # Intervalo de confianza
    fig.add_trace(go.Scatter(
        x=forecast_filtered["ds"],
        y=forecast_filtered["yhat_upper"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=forecast_filtered["ds"],
        y=forecast_filtered["yhat_lower"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(59, 130, 246, 0.15)",
        name="Intervalo 95%",
        hovertemplate="%{y:$,.0f}<extra>Intervalo</extra>"
    ))
    
    # Forecast line
    fig.add_trace(go.Scatter(
        x=forecast_filtered["ds"],
        y=forecast_filtered["yhat"],
        mode="lines",
        line=dict(color="#3b82f6", width=2.5, dash="dash"),
        name="Predicción",
        hovertemplate="%{x|%d/%m/%Y}<br>Predicción: $%{y:,.0f}<extra></extra>"
    ))
    
    # Real values
    fig.add_trace(go.Scatter(
        x=merged_filtered["ds"],
        y=merged_filtered["cash_balance"],
        mode="lines+markers",
        line=dict(color="#22c55e", width=2.5),
        marker=dict(size=3, color="#22c55e"),
        name="Real",
        hovertemplate="%{x|%d/%m/%Y}<br>Real: $%{y:,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        height=450,
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title=None,
            gridcolor="#1e293b",
            showgrid=True
        ),
        yaxis=dict(
            title="Saldo ($)",
            gridcolor="#1e293b",
            showgrid=True,
            tickformat="$,.0f"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Resumen de errores
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("**📊 Resumen de Errores**")
    
    if not merged_filtered.empty:
        y_true = merged_filtered["cash_balance"].values
        y_pred = merged_filtered["yhat"].values
        errors = y_true - y_pred
        abs_errors = np.abs(errors)
        pct_errors = np.abs(errors / y_true) * 100
        
        mae = np.mean(abs_errors)
        rmse = np.sqrt(np.mean(errors**2))
        mape = np.mean(pct_errors)
        bias = np.mean(errors)
        
        col_a, col_b = st.columns(2)
        col_a.metric("MAE", f"${mae:,.0f}")
        col_b.metric("RMSE", f"${rmse:,.0f}")
        col_a.metric("MAPE", f"{mape:.2f}%")
        col_b.metric("Bias", f"${bias:,.0f}", 
                     delta_color="inverse")
    
    st.markdown("---")
    
    # Estadísticas resumen
    st.markdown("**📈 Resumen Forecast**")
    fs = forecast_summary.get("statistics", {})
    if fs:
        st.metric("Media", f"${fs.get('mean_balance', 0):,.0f}")
        st.metric("Máximo", f"${fs.get('max_balance', 0):,.0f}")
        st.metric("Mínimo", f"${fs.get('min_balance', 0):,.0f}")
    
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 3: ANÁLISIS TEMPORAL
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📊 Análisis Temporal</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Evolución del saldo
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cashflow_filtered["date"],
        y=cashflow_filtered["cash_balance"],
        mode="lines",
        line=dict(color="#3b82f6", width=2),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.1)",
        name="Cash Balance",
        hovertemplate="%{x|%d/%m/%Y}<br>Balance: $%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        template="plotly_dark",
        title="Evolución del Saldo",
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(title=None, gridcolor="#1e293b"),
        yaxis=dict(title="Saldo ($)", gridcolor="#1e293b", tickformat="$,.0f"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Cash Inflow vs Outflow
    monthly = cashflow_filtered.copy()
    monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
    monthly_agg = monthly.groupby("month").agg(
        cash_inflow=("cash_inflow", "sum"),
        cash_outflow=("cash_outflow", "sum")
    ).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_agg["month"],
        y=monthly_agg["cash_inflow"],
        name="Ingresos",
        marker_color="#22c55e",
        hovertemplate="%{x}<br>Ingresos: $%{y:,.0f}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=monthly_agg["month"],
        y=-monthly_agg["cash_outflow"],
        name="Gastos",
        marker_color="#ef4444",
        hovertemplate="%{x}<br>Gastos: $%{abs(y):,.0f}<extra></extra>"
    ))
    fig.update_layout(
        template="plotly_dark",
        title="Ingresos vs Gastos Mensuales",
        barmode="relative",
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(title=None, gridcolor="#1e293b"),
        yaxis=dict(title="Monto ($)", gridcolor="#1e293b", tickformat="$,.0f"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    # Patrón semanal
    cashflow_filtered["day_of_week"] = cashflow_filtered["date"].dt.dayofweek
    cashflow_filtered["day_name"] = cashflow_filtered["date"].dt.strftime("%A")
    
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_labels_es = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    
    weekly_pattern = cashflow_filtered.groupby("day_of_week")["net_cash"].mean().reset_index()
    weekly_pattern["day_name"] = weekly_pattern["day_of_week"].map(lambda x: day_labels_es[x])
    
    fig = go.Figure()
    colors = ["#3b82f6"] * 5 + ["#f59e0b"] * 2  # Weekdays blue, weekend orange
    fig.add_trace(go.Bar(
        x=weekly_pattern["day_name"],
        y=weekly_pattern["net_cash"],
        marker_color=colors,
        hovertemplate="%{x}<br>Neto medio: $%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        template="plotly_dark",
        title="Patrón Semanal — Neto Promedio",
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(title=None, gridcolor="#1e293b"),
        yaxis=dict(title="Neto ($)", gridcolor="#1e293b", tickformat="$,.0f"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Heatmap mensual
    cashflow_filtered["year"] = cashflow_filtered["date"].dt.year
    cashflow_filtered["month"] = cashflow_filtered["date"].dt.month
    
    heatmap_data = cashflow_filtered.groupby(["year", "month"])["net_cash"].sum().reset_index()
    heatmap_pivot = heatmap_data.pivot(index="month", columns="year", values="net_cash")
    
    month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=[str(c) for c in heatmap_pivot.columns],
        y=month_names[:len(heatmap_pivot)],
        colorscale="RdBu_r",
        zmid=0,
        text=np.round(heatmap_pivot.values / 1000, 0).astype(int),
        texttemplate="%{text}K",
        hovertemplate="%{y} %{x}<br>Neto: $%{z:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        template="plotly_dark",
        title="Neto Mensual por Año (en miles $)",
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(title=None, gridcolor="#1e293b"),
        yaxis=dict(title=None, gridcolor="#1e293b"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 4: COMPONENTES DEL FORECAST
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🧩 Componentes del Forecast (Prophet)</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if "trend" in forecast_filtered.columns and "weekly" in forecast_filtered.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=forecast_filtered["ds"],
            y=forecast_filtered["trend"],
            mode="lines",
            line=dict(color="#8b5cf6", width=2),
            name="Trend",
            hovertemplate="%{x|%d/%m/%Y}<br>Trend: $%{y:,.0f}<extra></extra>"
        ))
        
        fig.update_layout(
            template="plotly_dark",
            title="Componente de Tendencia (Trend)",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title=None, gridcolor="#1e293b"),
            yaxis=dict(title="Trend ($)", gridcolor="#1e293b", tickformat="$,.0f"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "yearly" in forecast_filtered.columns and "weekly" in forecast_filtered.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=forecast_filtered["ds"],
            y=forecast_filtered["yearly"],
            mode="lines",
            line=dict(color="#f59e0b", width=2),
            name="Estacionalidad Anual",
            hovertemplate="%{x|%d/%m/%Y}<br>Yearly: %{y:.4f}%<extra></extra>"
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_filtered["ds"],
            y=forecast_filtered["weekly"],
            mode="lines",
            line=dict(color="#06b6d4", width=2),
            name="Estacionalidad Semanal",
            hovertemplate="%{x|%d/%m/%Y}<br>Weekly: %{y:.4f}%<extra></extra>"
        ))
        
        fig.update_layout(
            template="plotly_dark",
            title="Estacionalidad (Yearly + Weekly)",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title=None, gridcolor="#1e293b"),
            yaxis=dict(title="Factor estacional (%)", gridcolor="#1e293b"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 5: CRM PIPELINE
# ══════════════════════════════════════════════════════════════════
if not crm.empty:
    st.markdown('<div class="section-title">📋 CRM — Pipeline de Oportunidades</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Pipeline por etapa
        stage_counts = crm["stage"].value_counts().reset_index()
        stage_counts.columns = ["stage", "count"]
        
        colors_stage = {
            "prospecting": "#94a3b8",
            "proposal": "#3b82f6",
            "negotiation": "#f59e0b",
            "won": "#22c55e",
            "lost": "#ef4444"
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=stage_counts["stage"],
            values=stage_counts["count"],
            marker_colors=[colors_stage.get(s, "#64748b") for s in stage_counts["stage"]],
            textinfo="label+percent",
            hovertemplate="%{label}<br>%{value} deals (%{percent})<extra></extra>"
        )])
        fig.update_layout(
            template="plotly_dark",
            title="Distribución por Etapa",
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Expected amount by stage
        stage_amount = crm.groupby("stage")["expected_amount"].sum().reset_index()
        
        fig = go.Figure(data=[go.Bar(
            x=stage_amount["stage"],
            y=stage_amount["expected_amount"],
            marker_color=[colors_stage.get(s, "#64748b") for s in stage_amount["stage"]],
            text=stage_amount["expected_amount"].apply(lambda x: f"${x:,.0f}"),
            textposition="outside",
            hovertemplate="%{x}<br>Monto: $%{y:,.0f}<extra></extra>"
        )])
        fig.update_layout(
            template="plotly_dark",
            title="Monto Esperado por Etapa",
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title=None, gridcolor="#1e293b"),
            yaxis=dict(title="Monto ($)", gridcolor="#1e293b", tickformat="$,.0f"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Timeline de cierres esperados
        crm_with_close = crm.dropna(subset=["expected_close"])
        if not crm_with_close.empty:
            close_timeline = crm_with_close.groupby(
                crm_with_close["expected_close"].dt.to_period("M").astype(str)
            )["expected_amount"].sum().reset_index()
            close_timeline.columns = ["month", "amount"]
            
            fig = go.Figure(data=[go.Scatter(
                x=close_timeline["month"],
                y=close_timeline["amount"],
                mode="lines+markers",
                line=dict(color="#8b5cf6", width=2.5),
                marker=dict(size=8, color="#8b5cf6", symbol="diamond"),
                fill="tozeroy",
                fillcolor="rgba(139, 92, 246, 0.1)",
                hovertemplate="%{x}<br>Cierre esperado: $%{y:,.0f}<extra></extra>"
            )])
            fig.update_layout(
                template="plotly_dark",
                title="Timeline de Cierres Esperados",
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(title=None, gridcolor="#1e293b"),
                yaxis=dict(title="Monto ($)", gridcolor="#1e293b", tickformat="$,.0f"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Cards resumen CRM
    total_pipeline = crm["expected_amount"].sum() if "expected_amount" in crm.columns else 0
    weighted_pipeline = crm["weighted_value"].sum() if "weighted_value" in crm.columns else 0
    won_deals = crm[crm["stage"] == "won"]["expected_amount"].sum() if "won" in crm["stage"].values else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pipeline", f"${total_pipeline:,.0f}")
    c2.metric("Valor Ponderado", f"${weighted_pipeline:,.0f}")
    c3.metric("Deals Ganados", f"${won_deals:,.0f}")
    c4.metric("Total Deals", f"{len(crm)}")


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 6: DISTRIBUCIÓN DE ERRORES
# ══════════════════════════════════════════════════════════════════
if not merged_filtered.empty:
    st.markdown('<div class="section-title">📉 Distribución de Errores del Modelo</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histograma de errores
        error_values = merged_filtered["cash_balance"].values - merged_filtered["yhat"].values
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=error_values,
            nbinsx=30,
            marker_color="#3b82f6",
            marker_line=dict(color="#1e293b", width=1),
            hovertemplate="Error: $%{x:,.0f}<br>Frecuencia: %{y}<extra></extra>"
        ))
        fig.add_vline(x=0, line_dash="dash", line_color="#ef4444", line_width=2)
        fig.update_layout(
            template="plotly_dark",
            title="Distribución del Error (Real - Predicción)",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title="Error ($)", gridcolor="#1e293b", tickformat="$,.0f"),
            yaxis=dict(title="Frecuencia", gridcolor="#1e293b"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Scatter plot: Real vs Predicho
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=merged_filtered["cash_balance"],
            y=merged_filtered["yhat"],
            mode="markers",
            marker=dict(
                color="#3b82f6",
                size=5,
                opacity=0.6,
                line=dict(color="#1e293b", width=0.5)
            ),
            hovertemplate="Real: $%{x:,.0f}<br>Predicho: $%{y:,.0f}<extra></extra>"
        ))
        
        # Línea ideal (y=x)
        min_val = min(merged_filtered["cash_balance"].min(), merged_filtered["yhat"].min())
        max_val = max(merged_filtered["cash_balance"].max(), merged_filtered["yhat"].max())
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode="lines",
            line=dict(color="#22c55e", width=2, dash="dash"),
            name="Ideal (y=x)"
        ))
        
        fig.update_layout(
            template="plotly_dark",
            title="Real vs Predicho (Scatter)",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title="Real ($)", gridcolor="#1e293b", tickformat="$,.0f"),
            yaxis=dict(title="Predicho ($)", gridcolor="#1e293b", tickformat="$,.0f"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 7: INDICADORES DE RIESGO
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">⚠️ Indicadores de Riesgo</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Gauge de cobertura
    coverage = model_metrics.get("coverage_95", 0)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=coverage,
        number=dict(suffix="%", font=dict(size=36, color="#f1f5f9")),
        title=dict(text="Cobertura Intervalo 95%", font=dict(size=16, color="#94a3b8")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#64748b", tickfont=dict(color="#94a3b8")),
            bar=dict(color="#3b82f6"),
            steps=[
                dict(range=[0, 50], color="rgba(239, 68, 68, 0.3)"),
                dict(range=[50, 80], color="rgba(245, 158, 11, 0.3)"),
                dict(range=[80, 100], color="rgba(34, 197, 94, 0.3)")
            ],
            threshold=dict(
                line=dict(color="#f59e0b", width=4),
                thickness=0.75,
                value=95
            )
        )
    ))
    fig.update_layout(
        template="plotly_dark",
        height=280,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Gauge de riesgo de liquidez
    risk_score = 0 if risk == "BAJO" else 50 if risk == "MEDIO" else 100
    risk_text = {"BAJO": "Saludable", "MEDIO": "Monitoreo", "ALTO": "Crítico"}
    risk_color_gauge = "#22c55e" if risk == "BAJO" else "#f59e0b" if risk == "MEDIO" else "#ef4444"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        number=dict(suffix="%", font=dict(size=36)),
        title=dict(
            text=f"Riesgo de Liquidez — {risk_text.get(risk, risk)}",
            font=dict(size=16, color="#94a3b8")
        ),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#64748b", tickfont=dict(color="#94a3b8")),
            bar=dict(color=risk_color_gauge),
            steps=[
                dict(range=[0, 33], color="rgba(34, 197, 94, 0.3)"),
                dict(range=[33, 66], color="rgba(245, 158, 11, 0.3)"),
                dict(range=[66, 100], color="rgba(239, 68, 68, 0.3)")
            ],
            threshold=dict(
                line=dict(color="#f1f5f9", width=4),
                thickness=0.75,
                value=risk_score
            )
        )
    ))
    fig.update_layout(
        template="plotly_dark",
        height=280,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# SECCIÓN 8: FACTURAS
# ══════════════════════════════════════════════════════════════════
if not invoices.empty:
    st.markdown('<div class="section-title">🧾 Facturación</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_invoiced = invoices["total"].sum() if "total" in invoices.columns else 0
    avg_invoice = invoices["total"].mean() if "total" in invoices.columns else 0
    paid_invoices = len(invoices[invoices["status"] == "paid"]) if "status" in invoices.columns else 0
    overdue = invoices["is_overdue"].sum() if "is_overdue" in invoices.columns else 0
    
    col1.metric("Total Facturado", f"${total_invoiced:,.0f}")
    col2.metric("Promedio Factura", f"${avg_invoice:,.0f}")
    col3.metric("Pagadas", f"{paid_invoices:,}")
    col4.metric("Vencidas", f"{int(overdue)}", delta_color="inverse")
    
    # Timeline de facturación
    if "invoice_date" in invoices.columns and "total" in invoices.columns:
        invoice_monthly = invoices.copy()
        invoice_monthly["month"] = invoice_monthly["invoice_date"].dt.to_period("M").astype(str)
        inv_monthly_agg = invoice_monthly.groupby("month")["total"].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=inv_monthly_agg["month"],
            y=inv_monthly_agg["total"],
            marker_color="#3b82f6",
            marker_line=dict(color="#1e293b", width=0.5),
            hovertemplate="%{x}<br>Facturado: $%{y:,.0f}<extra></extra>"
        ))
        fig.update_layout(
            template="plotly_dark",
            title="Facturación Mensual",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title=None, gridcolor="#1e293b"),
            yaxis=dict(title="Facturado ($)", gridcolor="#1e293b", tickformat="$,.0f"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748b; padding: 20px; font-size: 13px;">
        <b>Cash Flow Forecasting System</b> — Industrial Metálica Portillo S.L.<br>
        Datos actualizados: {} | Datos sintéticos generados para demo
    </div>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M")),
    unsafe_allow_html=True
)
