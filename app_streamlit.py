"""Explorador BI de artículos CLV.

Ejecutar con:
    streamlit run app_streamlit.py
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import clv_fase2 as f2

st.set_page_config(
    page_title="CLV | Explorador de artículos",
    page_icon=":material/dentistry:",
    layout="wide",
    initial_sidebar_state="expanded",
)

AZUL = "#1f4e79"
AZUL_CLARO = "#2a6f97"
VERDE = "#2e7d5b"
AMBAR = "#b7791f"
ROJO = "#a4343a"
GRIS = "#5b6670"
SECUENCIA = [AZUL_CLARO, VERDE, AMBAR, ROJO, GRIS, "#7b5ea7", "#0f7b8a", "#c56c3c"]

ESTILO = f"""
<style>
.block-container {{padding-top: 2rem; padding-bottom: 2rem;}}
.encabezado {{
    background: linear-gradient(90deg, {AZUL} 0%, {AZUL_CLARO} 100%);
    color: #ffffff; padding: 18px 24px; border-radius: 10px; margin-bottom: 18px;
}}
.encabezado h1 {{margin: 0; font-size: 1.6rem;}}
.encabezado p {{margin: 4px 0 0 0; opacity: 0.9; font-size: 0.9rem;}}
.tarjeta {{
    background: #ffffff; border: 1px solid #e3e7eb; border-left: 5px solid {AZUL_CLARO};
    border-radius: 8px; padding: 14px 16px; height: 100%;
}}
.tarjeta .titulo {{font-size: 0.75rem; text-transform: uppercase; color: {GRIS}; letter-spacing: .04em;}}
.tarjeta .valor {{font-size: 1.55rem; font-weight: 700; color: {AZUL}; line-height: 1.2;}}
.tarjeta .detalle {{font-size: 0.78rem; color: {GRIS};}}
.nota {{font-size: 0.8rem; color: {GRIS};}}
</style>
"""

VARIABLES_NUMERICAS = [
    "ventas_importe", "ventas_unidades", "ventas_eventos", "ticket_promedio",
    "unidades_por_venta", "precio_efectivo", "participacion_ingresos",
    "ventas_mensuales_unidades", "cv_ventas_mensual", "meses_con_venta",
    "recencia_dias", "antiguedad_dias", "compras_importe", "compras_unidades",
    "costo_promedio_compra", "lote_promedio_compra", "ratio_compras_ventas",
    "margen_unitario_estimado", "margen_pct_estimado", "inventario_unidades",
    "inventario_valor", "rotacion_inventario", "rotacion_salidas", "dias_cobertura",
    "valor_unitario_inventario", "gmroi", "salidas_unidades", "salidas_por_movimiento",
    "razon_salidas_ventas", "meses_con_salida", "cv_salidas_mensual",
    "participacion_en_marca", "indice_vs_mediana_categoria", "articulos_marca",
    "tiempo_entrega_dias_prom", "riesgo_abasto",
]

VARIABLES_FACTOR = [
    "categoria_tipo", "categoria_tecnologia", "marca_grupo", "segmento_demanda",
    "segmento_valor", "clase_abc", "clase_rotacion", "clase_entrega",
    "flete_predominante", "marca",
]

DEPENDIENTES_ANOVA = [
    "ticket_promedio_log1p", "ventas_mensuales_unidades_log1p",
    "rotacion_inventario_log1p", "margen_pct_estimado", "precio_efectivo_log1p",
    "dias_cobertura_log1p", "gmroi_log1p",
]


@st.cache_data(show_spinner=False)
def cargar(etiqueta: str) -> pd.DataFrame:
    ruta = f2.DIR_BASES / f"base_{etiqueta}_caracteristicas.parquet"
    if not ruta.exists():
        return pd.DataFrame()
    return pd.read_parquet(ruta)


@st.cache_data(show_spinner=False)
def cargar_reporte(nombre: str) -> pd.DataFrame:
    ruta = f2.DIR_REPORTES / nombre
    return pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()


def formato_moneda(valor: float) -> str:
    if pd.isna(valor):
        return "-"
    if abs(valor) >= 1_000_000:
        return f"$ {valor / 1_000_000:,.1f} M"
    if abs(valor) >= 1_000:
        return f"$ {valor / 1_000:,.1f} k"
    return f"$ {valor:,.0f}"


def tarjeta(columna, titulo: str, valor: str, detalle: str = "", color: str = AZUL_CLARO) -> None:
    columna.markdown(
        f"""<div class="tarjeta" style="border-left-color:{color}">
            <div class="titulo">{titulo}</div>
            <div class="valor">{valor}</div>
            <div class="detalle">{detalle}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def a_excel(hojas: dict[str, pd.DataFrame]) -> bytes:
    memoria = io.BytesIO()
    with pd.ExcelWriter(memoria, engine="xlsxwriter") as escritor:
        for nombre, df in hojas.items():
            df.to_excel(escritor, sheet_name=nombre[:31], index=False)
    return memoria.getvalue()


def aplicar_filtros(datos: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("### Filtros")

    marcas = sorted(datos["marca"].dropna().unique())
    seleccion_marcas = st.sidebar.multiselect("Marca", marcas, default=[])

    tipos = sorted(datos["categoria_tipo"].dropna().unique())
    seleccion_tipos = st.sidebar.multiselect("Tipo de producto", tipos, default=[])

    tecnologias = sorted(datos["categoria_tecnologia"].dropna().unique())
    seleccion_tec = st.sidebar.multiselect("Tecnología", tecnologias, default=[])

    segmentos = ["ALTA", "MEDIA", "BAJA", "SIN_DEMANDA"]
    seleccion_seg = st.sidebar.multiselect(
        "Nivel de demanda", [s for s in segmentos if s in set(datos["segmento_demanda"])], default=[]
    )

    clases = sorted(datos["clase_abc"].dropna().unique())
    seleccion_abc = st.sidebar.multiselect("Clase ABC", clases, default=[])

    solo_con_venta = st.sidebar.toggle("Solo artículos con venta", value=False)
    solo_inventario = st.sidebar.toggle("Solo artículos con existencias", value=False)

    maximo = float(datos["ventas_importe"].max())
    rango = st.sidebar.slider(
        "Ingresos del artículo (pesos)",
        min_value=0.0,
        max_value=float(np.ceil(maximo)),
        value=(0.0, float(np.ceil(maximo))),
        step=max(maximo / 200, 1.0),
        format="%.0f",
    )

    texto = st.sidebar.text_input("Buscar artículo por nombre o clave", "")

    filtrado = datos.copy()
    if seleccion_marcas:
        filtrado = filtrado[filtrado["marca"].isin(seleccion_marcas)]
    if seleccion_tipos:
        filtrado = filtrado[filtrado["categoria_tipo"].isin(seleccion_tipos)]
    if seleccion_tec:
        filtrado = filtrado[filtrado["categoria_tecnologia"].isin(seleccion_tec)]
    if seleccion_seg:
        filtrado = filtrado[filtrado["segmento_demanda"].isin(seleccion_seg)]
    if seleccion_abc:
        filtrado = filtrado[filtrado["clase_abc"].isin(seleccion_abc)]
    if solo_con_venta:
        filtrado = filtrado[filtrado["ventas_importe"] > 0]
    if solo_inventario:
        filtrado = filtrado[filtrado["inventario_unidades"] > 0]
    filtrado = filtrado[filtrado["ventas_importe"].between(rango[0], rango[1])]
    if texto:
        patron = texto.strip().upper()
        filtrado = filtrado[
            filtrado["nombre_articulo"].str.contains(patron, na=False)
            | filtrado["clave_articulo"].astype(str).str.upper().str.contains(patron, na=False)
        ]

    st.sidebar.markdown(
        f"<p class='nota'>{len(filtrado):,} de {len(datos):,} artículos seleccionados</p>",
        unsafe_allow_html=True,
    )
    return filtrado


def panel_resumen(datos: pd.DataFrame, etiqueta: str) -> None:
    columnas = st.columns(6)
    ingresos = datos["ventas_importe"].sum()
    inventario = datos["inventario_valor"].sum()
    tarjeta(columnas[0], "Artículos", f"{len(datos):,}", f"base {etiqueta}")
    tarjeta(columnas[1], "Ingresos", formato_moneda(ingresos), "periodo completo", VERDE)
    tarjeta(columnas[2], "Ticket promedio", formato_moneda(datos["ticket_promedio"].median(skipna=True)), "mediana por artículo")
    tarjeta(columnas[3], "Valor de inventario", formato_moneda(inventario), "al corte", AMBAR)
    tarjeta(
        columnas[4],
        "Rotación mediana",
        f"{datos['rotacion_inventario'].median(skipna=True):,.2f}",
        "unidades vendidas / existencias",
    )
    inmovil = int(datos["inventario_inmovil"].sum())
    tarjeta(
        columnas[5],
        "Inventario inmóvil",
        f"{inmovil:,}",
        f"{100 * inmovil / max(len(datos), 1):.1f}% de la selección",
        ROJO,
    )

    st.markdown("")
    izquierda, derecha = st.columns([3, 2])

    top = (
        datos.groupby("marca", as_index=False)["ventas_importe"].sum()
        .sort_values("ventas_importe", ascending=False)
        .head(12)
    )
    figura = px.bar(
        top.sort_values("ventas_importe"),
        x="ventas_importe",
        y="marca",
        orientation="h",
        title="Ingresos por marca",
        color_discrete_sequence=[AZUL_CLARO],
        labels={"ventas_importe": "Ingresos", "marca": ""},
    )
    figura.update_layout(height=430, margin=dict(l=10, r=10, t=50, b=10))
    izquierda.plotly_chart(figura, use_container_width=True)

    composicion = (
        datos.groupby("categoria_tipo", as_index=False)["ventas_importe"].sum()
        .sort_values("ventas_importe", ascending=False)
    )
    composicion = composicion[composicion["ventas_importe"] > 0]
    figura = px.pie(
        composicion,
        names="categoria_tipo",
        values="ventas_importe",
        title="Composición de ingresos por tipo de producto",
        hole=0.45,
        color_discrete_sequence=SECUENCIA,
    )
    figura.update_layout(height=430, margin=dict(l=10, r=10, t=50, b=10))
    derecha.plotly_chart(figura, use_container_width=True)

    izquierda, derecha = st.columns(2)
    demanda = datos["segmento_demanda"].value_counts().reset_index()
    demanda.columns = ["segmento", "articulos"]
    figura = px.bar(
        demanda,
        x="segmento",
        y="articulos",
        title="Artículos por nivel de demanda",
        color="segmento",
        color_discrete_sequence=SECUENCIA,
    )
    figura.update_layout(height=360, showlegend=False, margin=dict(l=10, r=10, t=50, b=10))
    izquierda.plotly_chart(figura, use_container_width=True)

    abc = datos.groupby("clase_abc", as_index=False).agg(
        articulos=("articulo_id", "size"), ingresos=("ventas_importe", "sum")
    )
    figura = px.bar(
        abc,
        x="clase_abc",
        y="ingresos",
        title="Ingresos por clase ABC",
        color="clase_abc",
        text="articulos",
        color_discrete_sequence=SECUENCIA,
        labels={"ingresos": "Ingresos", "clase_abc": ""},
    )
    figura.update_traces(texttemplate="%{text:,} artículos", textposition="outside")
    figura.update_layout(height=360, showlegend=False, margin=dict(l=10, r=10, t=50, b=10))
    derecha.plotly_chart(figura, use_container_width=True)


def panel_exploracion(datos: pd.DataFrame) -> None:
    disponibles = [v for v in VARIABLES_NUMERICAS if v in datos.columns]
    columnas = st.columns(4)
    variable_x = columnas[0].selectbox("Variable X", disponibles, index=disponibles.index("ventas_importe"))
    variable_y = columnas[1].selectbox("Variable Y", disponibles, index=disponibles.index("rotacion_inventario"))
    factor = columnas[2].selectbox("Agrupar por", [f for f in VARIABLES_FACTOR if f in datos.columns])
    escala = columnas[3].selectbox("Escala", ["lineal", "logarítmica"], index=1)

    log = escala == "logarítmica"
    # La selección puede repetir columnas (por ejemplo variable X igual a la de
    # tamaño), y plotly rechaza nombres duplicados.
    columnas_muestra = list(
        dict.fromkeys([variable_x, variable_y, factor, "nombre_articulo", "marca", "ventas_importe"])
    )
    muestra = datos[columnas_muestra].copy()
    muestra = muestra.replace([np.inf, -np.inf], np.nan).dropna(subset=[variable_x, variable_y])
    muestra["tamano"] = muestra["ventas_importe"].fillna(0).clip(lower=0)

    # En escala logarítmica el cero no tiene representación; se excluye para que
    # el gráfico no intente ubicar puntos en menos infinito.
    histograma = datos.replace([np.inf, -np.inf], np.nan)
    if log:
        muestra = muestra[(muestra[variable_x] > 0) & (muestra[variable_y] > 0)]
        histograma = histograma[histograma[variable_x] > 0]

    izquierda, derecha = st.columns(2)
    figura = px.histogram(
        histograma,
        x=variable_x,
        color=factor,
        nbins=50,
        marginal="box",
        log_x=log,
        title=f"Distribución de {variable_x}",
        color_discrete_sequence=SECUENCIA,
    )
    figura.update_layout(height=470, margin=dict(l=10, r=10, t=50, b=10))
    izquierda.plotly_chart(figura, use_container_width=True)

    figura = px.scatter(
        muestra,
        x=variable_x,
        y=variable_y,
        color=factor,
        size="tamano",
        size_max=28,
        hover_data=["nombre_articulo", "marca"],
        log_x=log,
        log_y=log,
        title=f"{variable_y} frente a {variable_x}",
        color_discrete_sequence=SECUENCIA,
        opacity=0.75,
    )
    figura.update_layout(height=470, margin=dict(l=10, r=10, t=50, b=10))
    derecha.plotly_chart(figura, use_container_width=True)

    resumen = (
        datos.replace([np.inf, -np.inf], np.nan)
        .groupby(factor)
        .agg(
            articulos=("articulo_id", "size"),
            media=(variable_x, "mean"),
            mediana=(variable_x, "median"),
            desviacion=(variable_x, "std"),
            minimo=(variable_x, "min"),
            maximo=(variable_x, "max"),
        )
        .reset_index()
        .sort_values("media", ascending=False)
    )
    st.markdown(f"**Resumen de `{variable_x}` por `{factor}`**")
    st.dataframe(
        resumen.style.format(
            {"media": "{:,.2f}", "mediana": "{:,.2f}", "desviacion": "{:,.2f}", "minimo": "{:,.2f}", "maximo": "{:,.2f}"}
        ).background_gradient(subset=["media"], cmap="Blues"),
        use_container_width=True,
        height=320,
    )


def panel_estadistica(datos: pd.DataFrame, etiqueta: str) -> None:
    st.markdown("#### ANOVA de un factor")
    columnas = st.columns(3)
    disponibles = [v for v in DEPENDIENTES_ANOVA if v in datos.columns]
    variable = columnas[0].selectbox("Variable dependiente", disponibles, key="anova_var")
    factor = columnas[1].selectbox(
        "Factor", [f for f in VARIABLES_FACTOR if f in datos.columns], key="anova_factor"
    )
    minimo = columnas[2].number_input("Mínimo de artículos por nivel", 5, 200, 10, step=5)

    resultado, muestra = f2.anova_un_factor(datos, variable, factor, min_n=int(minimo))
    if resultado is None:
        st.warning("La selección no deja al menos dos grupos con suficientes artículos.")
        return

    tarjetas = st.columns(5)
    tarjeta(tarjetas[0], "Estadístico F", f"{resultado['F']:,.2f}", f"gl {resultado['gl_entre']} / {resultado['gl_dentro']}")
    color_p = VERDE if resultado["p_valor"] < 0.05 else ROJO
    tarjeta(tarjetas[1], "Valor p", f"{resultado['p_valor']:.2e}", "significativo" if resultado["p_valor"] < 0.05 else "no significativo", color_p)
    tarjeta(tarjetas[2], "Tamaño del efecto", f"{resultado['eta2']:.4f}", f"eta cuadrada, efecto {resultado['magnitud_efecto']}", AMBAR)
    tarjeta(tarjetas[3], "Welch", f"{resultado['welch_p']:.2e}", "no supone varianzas iguales")
    tarjeta(tarjetas[4], "Kruskal-Wallis", f"{resultado['kruskal_p']:.2e}", "alternativa no paramétrica", GRIS)

    st.markdown(
        f"<p class='nota'>Homogeneidad de varianzas (Levene): {resultado['homogeneidad']} (p = {resultado['levene_p']:.2e}). "
        f"Normalidad de residuales (Shapiro): {resultado['normalidad_residuales']} (p = {resultado['shapiro_p']:.2e}). "
        f"Conclusión: {resultado['conclusion']}.</p>",
        unsafe_allow_html=True,
    )

    izquierda, derecha = st.columns([3, 2])
    figura = px.box(
        muestra,
        x=factor,
        y=variable,
        color=factor,
        points=False,
        title=f"{variable} por {factor}",
        color_discrete_sequence=SECUENCIA,
    )
    figura.update_layout(height=430, showlegend=False, margin=dict(l=10, r=10, t=50, b=10))
    izquierda.plotly_chart(figura, use_container_width=True)

    grupos = f2.resumen_grupos(muestra, variable, factor)
    derecha.markdown("**Medias por nivel con intervalo de confianza al 95%**")
    derecha.dataframe(grupos, use_container_width=True, height=380)

    with st.expander("Comparaciones por pares (Tukey HSD)"):
        if muestra[factor].nunique() <= 15:
            tukey = f2.tukey_posthoc(muestra, variable, factor)
            st.dataframe(tukey, use_container_width=True, height=320)
        else:
            st.info("El factor tiene demasiados niveles para mostrar todas las comparaciones.")

    st.divider()
    st.markdown("#### ANOVA factorial y efecto de interacción")
    columnas = st.columns(3)
    variable_f = columnas[0].selectbox("Variable dependiente", disponibles, key="factorial_var")
    factor_a = columnas[1].selectbox(
        "Factor A", [f for f in VARIABLES_FACTOR if f in datos.columns], index=0, key="factorial_a"
    )
    factor_b = columnas[2].selectbox(
        "Factor B", [f for f in VARIABLES_FACTOR if f in datos.columns], index=1, key="factorial_b"
    )

    if factor_a == factor_b:
        st.warning("Selecciona dos factores distintos.")
        return

    resumen, modelo, muestra = f2.anova_factorial(datos, variable_f, [factor_a, factor_b])
    if resumen is None:
        st.warning("No hay suficientes observaciones por celda para estimar el modelo factorial.")
        return

    tabla = resumen[(resumen["tipo_suma_cuadrados"] == "II") & (resumen["termino"] != "Residual")]
    st.dataframe(
        tabla[["termino", "df", "sum_sq", "F", "p_valor", "eta2_parcial", "magnitud_efecto", "significativo"]]
        .style.format({"sum_sq": "{:,.2f}", "F": "{:,.2f}", "p_valor": "{:.2e}", "eta2_parcial": "{:.4f}"}),
        use_container_width=True,
    )

    interaccion = tabla[tabla["termino"].str.contains(":")]
    if len(interaccion):
        fila = interaccion.iloc[0]
        if fila["p_valor"] < 0.05:
            st.success(
                f"La interacción {factor_a} x {factor_b} es significativa (p = {fila['p_valor']:.2e}, "
                f"eta² parcial = {fila['eta2_parcial']:.4f}): el efecto de un factor depende del nivel del otro."
            )
        else:
            st.info(
                f"La interacción {factor_a} x {factor_b} no es significativa (p = {fila['p_valor']:.3f}): "
                "los efectos principales se pueden interpretar por separado."
            )

    medias = f2.medias_de_celda(muestra, variable_f, [factor_a, factor_b])
    figura = px.line(
        medias,
        x=factor_a,
        y="media",
        color=factor_b,
        markers=True,
        title=f"Gráfico de interacción: {variable_f}",
        color_discrete_sequence=SECUENCIA,
    )
    figura.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(figura, use_container_width=True)

    with st.expander("Medias por celda"):
        st.dataframe(medias, use_container_width=True)

    with st.expander("Resultados precalculados de la corrida completa"):
        st.markdown("**ANOVA de un factor**")
        st.dataframe(cargar_reporte(f"anova_un_factor_{etiqueta}.csv"), use_container_width=True)
        st.markdown("**ANOVA factorial**")
        st.dataframe(cargar_reporte(f"anova_factorial_{etiqueta}.csv"), use_container_width=True)


def panel_comparacion(inicial: pd.DataFrame, complementaria: pd.DataFrame) -> None:
    st.markdown("#### Versión inicial frente a versión complementaria")
    st.markdown(
        "<p class='nota'>La versión inicial parte de la hoja de existencias y cubre más artículos. "
        "La complementaria se construye sobre el catálogo de claves y suma el segundo corte de inventario, "
        "el histórico de entradas y salidas y las ventas del periodo posterior.</p>",
        unsafe_allow_html=True,
    )

    indicadores = pd.DataFrame(
        {
            "Indicador": [
                "Artículos", "Artículos con venta", "Artículos con existencias",
                "Ingresos totales", "Ticket promedio mediano", "Rotación mediana",
                "Margen porcentual mediano", "Inventario inmóvil", "Artículos clase A",
            ],
            "Inicial": [
                len(inicial),
                int((inicial["ventas_importe"] > 0).sum()),
                int((inicial["inventario_unidades"] > 0).sum()),
                inicial["ventas_importe"].sum(),
                inicial["ticket_promedio"].median(skipna=True),
                inicial["rotacion_inventario"].median(skipna=True),
                inicial["margen_pct_estimado"].median(skipna=True),
                int(inicial["inventario_inmovil"].sum()),
                int((inicial["clase_abc"] == "A").sum()),
            ],
            "Complementaria": [
                len(complementaria),
                int((complementaria["ventas_importe"] > 0).sum()),
                int((complementaria["inventario_unidades"] > 0).sum()),
                complementaria["ventas_importe"].sum(),
                complementaria["ticket_promedio"].median(skipna=True),
                complementaria["rotacion_inventario"].median(skipna=True),
                complementaria["margen_pct_estimado"].median(skipna=True),
                int(complementaria["inventario_inmovil"].sum()),
                int((complementaria["clase_abc"] == "A").sum()),
            ],
        }
    )
    indicadores["Diferencia"] = indicadores["Complementaria"] - indicadores["Inicial"]

    izquierda, derecha = st.columns([2, 3])
    izquierda.dataframe(
        indicadores.style.format({"Inicial": "{:,.2f}", "Complementaria": "{:,.2f}", "Diferencia": "{:,.2f}"}),
        use_container_width=True,
        height=380,
    )

    columnas_comunes = ["articulo_id", "nombre_articulo", "marca", "ventas_importe", "rotacion_inventario", "ticket_promedio"]
    cruce = inicial[columnas_comunes].merge(
        complementaria[columnas_comunes],
        on=["articulo_id", "nombre_articulo", "marca"],
        suffixes=("_inicial", "_complementaria"),
    )
    figura = px.scatter(
        cruce,
        x="ventas_importe_inicial",
        y="ventas_importe_complementaria",
        hover_data=["nombre_articulo", "marca"],
        log_x=True,
        log_y=True,
        title="Consistencia de ingresos por artículo entre versiones",
        color_discrete_sequence=[AZUL_CLARO],
        opacity=0.6,
    )
    maximo = float(max(cruce["ventas_importe_inicial"].max(), cruce["ventas_importe_complementaria"].max()))
    figura.add_shape(type="line", x0=1, y0=1, x1=maximo, y1=maximo, line=dict(color=ROJO, dash="dash"))
    figura.update_layout(height=430, margin=dict(l=10, r=10, t=50, b=10))
    derecha.plotly_chart(figura, use_container_width=True)

    solo_inicial = len(set(inicial["articulo_id"]) - set(complementaria["articulo_id"]))
    solo_complementaria = len(set(complementaria["articulo_id"]) - set(inicial["articulo_id"]))
    ambas = len(set(inicial["articulo_id"]) & set(complementaria["articulo_id"]))
    tarjetas = st.columns(3)
    tarjeta(tarjetas[0], "Solo en la inicial", f"{solo_inicial:,}", "sin equivalencia de clave", AMBAR)
    tarjeta(tarjetas[1], "En ambas versiones", f"{ambas:,}", "comparables artículo por artículo", VERDE)
    tarjeta(tarjetas[2], "Solo en la complementaria", f"{solo_complementaria:,}", "aportados por el catálogo de claves")
    st.markdown(
        "<p class='nota'>Los ingresos coinciden artículo por artículo porque ambas versiones agregan la misma hoja "
        "de ventas; la diferencia entre bases está en la cobertura del catálogo y en las variables adicionales "
        "del segundo corte de inventario.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("**Cobertura por tipo de producto**")
    cobertura = pd.concat(
        [
            inicial.groupby("categoria_tipo").size().rename("inicial"),
            complementaria.groupby("categoria_tipo").size().rename("complementaria"),
        ],
        axis=1,
    ).fillna(0).reset_index()
    figura = px.bar(
        cobertura.melt(id_vars="categoria_tipo", var_name="base", value_name="articulos"),
        x="categoria_tipo",
        y="articulos",
        color="base",
        barmode="group",
        color_discrete_sequence=[AZUL_CLARO, VERDE],
    )
    figura.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(figura, use_container_width=True)

    st.dataframe(cargar_reporte("comparacion_bases.csv"), use_container_width=True)


def panel_datos(datos: pd.DataFrame, etiqueta: str) -> None:
    columnas_sugeridas = [
        "articulo_id", "clave_articulo", "nombre_articulo", "marca", "categoria_tipo",
        "categoria_tecnologia", "segmento_demanda", "clase_abc", "ventas_importe",
        "ventas_unidades", "ticket_promedio", "precio_efectivo", "margen_pct_estimado",
        "inventario_unidades", "inventario_valor", "rotacion_inventario", "dias_cobertura",
        "tiempo_entrega_dias_prom",
    ]
    disponibles = [c for c in datos.columns]
    seleccion = st.multiselect(
        "Columnas a mostrar",
        disponibles,
        default=[c for c in columnas_sugeridas if c in disponibles],
    )
    orden = st.selectbox(
        "Ordenar por",
        [c for c in seleccion if pd.api.types.is_numeric_dtype(datos[c])] or ["articulo_id"],
    )
    tabla = datos[seleccion].sort_values(orden, ascending=False)

    st.dataframe(tabla, use_container_width=True, height=520)

    st.markdown("**Descargas**")
    columnas = st.columns(3)
    columnas[0].download_button(
        "Descargar selección en CSV",
        tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"clv_{etiqueta}_seleccion.csv",
        mime="text/csv",
        use_container_width=True,
    )
    columnas[1].download_button(
        "Descargar selección en Excel",
        a_excel({"Articulos": tabla}),
        file_name=f"clv_{etiqueta}_seleccion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    columnas[2].download_button(
        "Descargar resultados estadísticos",
        a_excel(
            {
                "ANOVA_un_factor": cargar_reporte(f"anova_un_factor_{etiqueta}.csv"),
                "ANOVA_factorial": cargar_reporte(f"anova_factorial_{etiqueta}.csv"),
                "Descriptivas": cargar_reporte(f"descriptivas_caracteristicas_{etiqueta}.csv"),
                "Diccionario": cargar_reporte("diccionario_caracteristicas.csv"),
            }
        ),
        file_name=f"clv_{etiqueta}_resultados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    with st.expander("Diccionario de características"):
        st.dataframe(cargar_reporte("diccionario_caracteristicas.csv"), use_container_width=True)


def main() -> None:
    st.markdown(ESTILO, unsafe_allow_html=True)
    st.markdown(
        """<div class="encabezado">
            <h1>CLV | Explorador de artículos</h1>
            <p>Material dental, de lo básico a lo especializado. Características, indicadores y análisis de varianza
            sobre las bases consolidadas de la Fase 1.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("### Base de datos")
    etiqueta = st.sidebar.radio(
        "Versión", ["inicial", "complementaria"], format_func=lambda x: f"Versión {x}", horizontal=True
    )

    datos = cargar(etiqueta)
    if datos.empty:
        st.error(
            "No se encontraron las bases con características en `salidas/bases/`. "
            "Vuelve a generarlas con `python ejecutar_fase2.py` desde la carpeta fase2 del proyecto."
        )
        return

    filtrado = aplicar_filtros(datos)
    if filtrado.empty:
        st.warning("Los filtros no dejan ningún artículo. Ajusta la selección en la barra lateral.")
        return

    pestanas = st.tabs(["Resumen", "Exploración", "Estadística", "Comparación de versiones", "Datos"])
    with pestanas[0]:
        panel_resumen(filtrado, etiqueta)
    with pestanas[1]:
        panel_exploracion(filtrado)
    with pestanas[2]:
        panel_estadistica(filtrado, etiqueta)
    with pestanas[3]:
        otra = cargar("complementaria" if etiqueta == "inicial" else "inicial")
        if otra.empty:
            st.warning("Falta la otra versión de la base.")
        else:
            inicial = datos if etiqueta == "inicial" else otra
            complementaria = otra if etiqueta == "inicial" else datos
            panel_comparacion(inicial, complementaria)
    with pestanas[4]:
        panel_datos(filtrado, etiqueta)


if __name__ == "__main__":
    main()
