# ============================================================
# saneamiento_story.py
# Brecha en acceso a fuente de agua mejorada — Colombia
# Storytelling y Narrativa de los Datos
# Universidad Tecnológica de Bolívar
# ============================================================

# ── Dependencias ────────────────────────────────────────────
# pip install dash dash-bootstrap-components plotly openpyxl numpy

import numpy as np
import openpyxl
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# ── Configuración ────────────────────────────────────────────
EXCEL_PATH = "anex-PMultidimensional-Departamental-2025.xlsx"
YEARS      = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
C_URB      = "#2166ac"
C_RUR      = "#d6604d"
C_BG       = "#f9f9f9"

# ════════════════════════════════════════════════════════════
# 1. CARGA Y PREPARACIÓN DE DATOS
# ════════════════════════════════════════════════════════════
wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True)
ws = wb['IPM_Indicadores_Departamento ']   # ← espacio al final

current_dept = None
records      = []

for row in ws.iter_rows(values_only=True):
    if row[0] and str(row[0]).strip() not in ('', 'Departamento'):
        current_dept = str(row[0]).strip()
    if row[1] and 'agua mejorada' in str(row[1]):
        vals = list(row[2:])
        cab  = [float(vals[1 + i*3]) if vals[1 + i*3] is not None else np.nan for i in range(8)]
        rur  = [float(vals[2 + i*3]) if vals[2 + i*3] is not None else np.nan for i in range(8)]
        records.append({"Departamento": current_dept, "Cabeceras": cab, "Rural": rur})

# Promedio nacional
nac_cab = [round(np.nanmean([r["Cabeceras"][i] for r in records]), 1) for i in range(8)]
nac_rur = [round(np.nanmean([r["Rural"][i] for r in records
                              if not np.isnan(r["Rural"][i])]), 1) for i in range(8)]

records.insert(0, {
    "Departamento": "🇨🇴 Nacional (promedio)",
    "Cabeceras": nac_cab,
    "Rural":     nac_rur
})

data        = {r["Departamento"]: r for r in records}
dept_options = [{"label": r["Departamento"], "value": r["Departamento"]} for r in records]

print(f"✅ {len(records)-1} departamentos + promedio nacional cargados")

# ════════════════════════════════════════════════════════════
# 2. APLICACIÓN DASH
# ════════════════════════════════════════════════════════════
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([

    # ── Encabezado ─────────────────────────────────────────
    dbc.Row(dbc.Col([
        html.H3(
            "El campo sigue sin agua: la brecha urbano-rural en acceso "
            "a fuente de agua mejorada persiste en Colombia",
            className="fw-bold mt-3 mb-1",
            style={"color": "#1a1a1a", "lineHeight": "1.35"}
        ),
        html.P(
            "Proporción de hogares sin acceso a fuente de agua mejorada (%) · "
            "2018–2025 · Fuente: DANE — ECV",
            className="text-muted mb-2",
            style={"fontSize": "13px"}
        ),
    ], width=12)),

    # ── Selector + tarjeta narrativa ────────────────────────
    dbc.Row([
        dbc.Col([
            html.Label("Selecciona un departamento:",
                       className="fw-semibold mb-1",
                       style={"fontSize": "13px"}),
            dcc.Dropdown(
                id="dept-dropdown",
                options=dept_options,
                value="🇨🇴 Nacional (promedio)",
                clearable=False,
                style={"fontSize": "13px"}
            ),
        ], width=4),
        dbc.Col(
            html.Div(id="tarjeta-brecha"),
            width=8, className="d-flex align-items-end"
        ),
    ], className="mb-2"),

    # ── Gráfico principal ───────────────────────────────────
    dbc.Row(dbc.Col(
        dcc.Graph(
            id="grafico-agua",
            style={"height": "520px"},
            config={"displayModeBar": False}
        ),
        width=12
    )),

    # ── Pie de página ───────────────────────────────────────
    dbc.Row(dbc.Col(
        html.Small(
            "Nota: Los valores nacionales corresponden al promedio simple entre "
            "departamentos. San Andrés no tiene dato rural (isla sin ruralidad "
            "dispersa). La variación 2019–2020 en zona rural refleja el cambio "
            "de marco geoestadístico del CNPV 2018.",
            className="text-muted"
        ), width=12, className="mt-1 mb-3"
    )),

], fluid=True, style={"backgroundColor": C_BG, "minHeight": "100vh", "padding": "0 24px"})


# ════════════════════════════════════════════════════════════
# 3. CALLBACK
# ════════════════════════════════════════════════════════════
@app.callback(
    Output("grafico-agua",   "figure"),
    Output("tarjeta-brecha", "children"),
    Input("dept-dropdown",   "value"),
)
def actualizar(dept):
    d      = data[dept]
    cab    = d["Cabeceras"]
    rur    = d["Rural"]

    br_2025 = round(rur[-1] - cab[-1], 1) if not np.isnan(rur[-1]) else None
    factor  = round(rur[-1] / cab[-1],  1) if cab[-1] and cab[-1] > 0 else None
    nombre  = dept.replace("🇨🇴 ", "")

    # ── Tarjeta narrativa ───────────────────────────────────
    if br_2025 and factor:
        tarjeta = dbc.Alert([
            html.Span("Brecha en 2025: ", className="fw-bold"),
            html.Span(f"{br_2025} pp",
                      style={"color": C_RUR, "fontWeight": "700", "fontSize": "16px"}),
            html.Span("  ·  ", className="text-muted"),
            html.Span(f"En {nombre}, el campo tiene "),
            html.Span(f"{factor}×",
                      style={"color": C_RUR, "fontWeight": "700", "fontSize": "16px"}),
            html.Span(" más privación de agua que la ciudad"),
        ], color="warning", className="py-2 px-3 mb-0",
           style={"fontSize": "13px", "borderLeft": f"4px solid {C_RUR}"})
    else:
        tarjeta = html.Div()

    # ── Figura ──────────────────────────────────────────────
    rur_clean = [r if not np.isnan(r) else None for r in rur]
    cab_clean = [c if not np.isnan(c) else None for c in cab]

    fig = go.Figure()

    # Área de brecha
    fig.add_trace(go.Scatter(
        x=YEARS + YEARS[::-1],
        y=rur_clean + cab_clean[::-1],
        fill="toself",
        fillcolor="rgba(244,165,130,0.35)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip", showlegend=False, name="Brecha"
    ))

    # Línea rural
    fig.add_trace(go.Scatter(
        x=YEARS, y=rur,
        mode="lines+markers+text",
        name="Rural disperso",
        line=dict(color=C_RUR, width=3),
        marker=dict(size=8, color=C_RUR),
        text=[f"{v:.1f}%" if not np.isnan(v) else "" for v in rur],
        textposition="top center",
        textfont=dict(size=10, color=C_RUR, family="Arial Black"),
        hovertemplate="<b>%{x} · Rural</b><br>Sin agua: <b>%{y:.1f}%</b><extra></extra>"
    ))

    # Línea cabeceras
    fig.add_trace(go.Scatter(
        x=YEARS, y=cab,
        mode="lines+markers+text",
        name="Cabeceras (urbano)",
        line=dict(color=C_URB, width=3),
        marker=dict(size=8, color=C_URB),
        text=[f"{v:.1f}%" if not np.isnan(v) else "" for v in cab],
        textposition="bottom center",
        textfont=dict(size=10, color=C_URB, family="Arial Black"),
        hovertemplate="<b>%{x} · Cabeceras</b><br>Sin agua: <b>%{y:.1f}%</b><extra></extra>"
    ))

    # Anotaciones de brecha en 2018 y 2025
    for yr_idx, yr in [(0, 2018), (7, 2025)]:
        if np.isnan(rur[yr_idx]) or np.isnan(cab[yr_idx]):
            continue
        brecha = round(rur[yr_idx] - cab[yr_idx], 1)
        mid_y  = (rur[yr_idx] + cab[yr_idx]) / 2
        fig.add_annotation(
            x=yr, y=mid_y,
            text=f"<b>Brecha<br>{brecha} pp</b>",
            showarrow=False,
            font=dict(size=10, color="#7f3b08"),
            bgcolor="white", bordercolor=C_RUR,
            borderwidth=1.5, borderpad=4, opacity=0.92
        )

    ymax = max((v for v in rur if not np.isnan(v)), default=80)
    fig.update_layout(
        paper_bgcolor=C_BG, plot_bgcolor=C_BG,
        margin=dict(l=40, r=30, t=20, b=40),
        xaxis=dict(
            tickvals=YEARS, ticktext=[str(y) for y in YEARS],
            tickfont=dict(size=11), showgrid=False, zeroline=False,
        ),
        yaxis=dict(
            ticksuffix="%", tickfont=dict(size=11),
            gridcolor="#e8e8e8", zeroline=False,
            range=[-3, ymax * 1.22],
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0, font=dict(size=11),
            bgcolor="rgba(0,0,0,0)"
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#cccccc"),
        transition=dict(duration=400, easing="cubic-in-out"),
    )

    return fig, tarjeta


# ════════════════════════════════════════════════════════════
# 4. PUNTO DE ENTRADA
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=False, port=8050)