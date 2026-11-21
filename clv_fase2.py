"""Fase 2: extracción de características y análisis de varianza para CLV.

Parte de las bases preprocesadas en la Fase 1 y construye indicadores de ventas,
abastecimiento, inventario, salidas de almacén, marca y tiempos de entrega.
Sobre esas características ejecuta ANOVA de un factor y ANOVA factorial con
evaluación del efecto de interacción.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

DIR_FASE2 = Path(__file__).resolve().parent
RAIZ = DIR_FASE2.parent
DIR_FASE1 = RAIZ / "fase1"

if str(DIR_FASE1) not in sys.path:
    sys.path.insert(0, str(DIR_FASE1))

try:
    import clv_fase1 as fase1  # noqa: E402
except ModuleNotFoundError:
    # La carpeta del dashboard se distribuye sin el módulo de la Fase 1: la app
    # solo lee las bases ya construidas y nunca vuelve a las fuentes en Excel.
    fase1 = None

SALIDAS = DIR_FASE2 / "salidas"
DIR_BASES = SALIDAS / "bases"
DIR_REPORTES = SALIDAS / "reportes"
DIR_FIGURAS = SALIDAS / "figuras"

SIN_DATO = fase1.SIN_DATO if fase1 else "SIN_DATO"
SIN_CLASIFICAR = fase1.SIN_CLASIFICAR if fase1 else "SIN_CLASIFICAR"

# Fecha del corte de inventario más reciente; sirve de referencia temporal.
FECHA_CORTE = pd.Timestamp("2026-10-15")

# Las dos bases nombran distinto los mismos conceptos. Se traducen a un juego
# único de columnas para que todas las características se calculen igual.
CANONICO = {
    "inicial": {
        "ingresos_totales": "ventas_importe",
        "unidades_vendidas": "ventas_unidades",
        "numero_ventas": "ventas_eventos",
        "importe_compras": "compras_importe",
        "unidades_compradas": "compras_unidades",
        "numero_compras": "compras_eventos",
        "total_salidas": "salidas_unidades",
        "movimientos_almacen": "salidas_eventos",
        "existencias": "inventario_unidades",
        "valor_total_inventario": "inventario_valor",
    },
    "complementaria": {
        "importe_ventas": "ventas_importe",
        "unidades_vendidas": "ventas_unidades",
        "numero_registros_venta": "ventas_eventos",
        "importe_compras": "compras_importe",
        "unidades_compradas": "compras_unidades",
        "numero_registros_compra": "compras_eventos",
        "salidas_almacen": "salidas_unidades",
        "numero_registros_salidas": "salidas_eventos",
        "existencias": "inventario_unidades",
        "valor_total_inventario": "inventario_valor",
    },
}

CARACTERISTICAS_NUMERICAS = [
    "ticket_promedio",
    "unidades_por_venta",
    "precio_efectivo",
    "participacion_ingresos",
    "ventas_mensuales_unidades",
    "cv_ventas_mensual",
    "meses_con_venta",
    "recencia_dias",
    "antiguedad_dias",
    "costo_promedio_compra",
    "lote_promedio_compra",
    "ratio_compras_ventas",
    "margen_unitario_estimado",
    "margen_pct_estimado",
    "rotacion_inventario",
    "rotacion_salidas",
    "dias_cobertura",
    "valor_unitario_inventario",
    "gmroi",
    "salidas_por_movimiento",
    "razon_salidas_ventas",
    "meses_con_salida",
    "cv_salidas_mensual",
    "participacion_en_marca",
    "indice_vs_mediana_categoria",
    "articulos_marca",
    "tiempo_entrega_dias_prom",
    "riesgo_abasto",
]

FACTORES = [
    "categoria_tipo",
    "categoria_tecnologia",
    "marca_grupo",
    "segmento_demanda",
    "clase_abc",
    "clase_entrega",
    "flete_predominante",
]


def _division(numerador, denominador):
    """División que devuelve nulo en lugar de infinito cuando no está definida."""
    num = pd.to_numeric(numerador, errors="coerce")
    den = pd.to_numeric(denominador, errors="coerce")
    return (num / den.where(den > 0)).replace([np.inf, -np.inf], np.nan)


def cargar_base(etiqueta: str) -> pd.DataFrame:
    ruta = DIR_FASE1 / "salidas" / "bases" / f"base_{etiqueta}_preprocesada.parquet"
    if not ruta.exists():
        raise FileNotFoundError(
            f"Falta {ruta}. Ejecuta primero fase1/ejecutar_fase1.py"
        )
    return pd.read_parquet(ruta)


def normalizar_nombres(base: pd.DataFrame, etiqueta: str) -> pd.DataFrame:
    """Crea las columnas canónicas sin perder las originales."""
    datos = base.copy()
    for origen, destino in CANONICO[etiqueta].items():
        datos[destino] = pd.to_numeric(datos[origen], errors="coerce").fillna(0)
    return datos


def caracteristicas_temporales(fuentes, libro_ventas) -> pd.DataFrame:
    """Regularidad y vigencia a partir de las series mensuales por artículo.

    El libro de ventas unificado y la hoja de salidas de almacén dan el ritmo de
    movimiento de cada artículo: en cuántos meses hubo actividad, qué tan
    estable fue y hace cuánto ocurrió la última operación.
    """
    ventas = libro_ventas.dropna(subset=["fecha"]).copy()
    ventas["periodo"] = ventas["fecha"].dt.to_period("M")
    mensual_ventas = (
        ventas.groupby(["articulo_id", "periodo"])["total_unidades"].sum().reset_index()
    )
    resumen_ventas = (
        mensual_ventas.groupby("articulo_id")["total_unidades"]
        .agg(
            meses_con_venta="size",
            ventas_mensuales_unidades="mean",
            desviacion_mensual_ventas="std",
        )
        .reset_index()
    )
    resumen_ventas["cv_ventas_mensual"] = (
        resumen_ventas["desviacion_mensual_ventas"] / resumen_ventas["ventas_mensuales_unidades"]
    ).replace([np.inf, -np.inf], np.nan)

    fechas = (
        ventas.groupby("articulo_id")["fecha"]
        .agg(primera_venta_libro="min", ultima_venta_libro="max")
        .reset_index()
    )

    salidas = fuentes["salidas"].copy()
    resumen_salidas = (
        salidas.groupby(["articulo_id", "anio", "mes"])["salidas"]
        .sum()
        .reset_index()
        .groupby("articulo_id")["salidas"]
        .agg(meses_con_salida="size", salidas_mensuales="mean", desviacion_mensual_salidas="std")
        .reset_index()
    )
    resumen_salidas["cv_salidas_mensual"] = (
        resumen_salidas["desviacion_mensual_salidas"] / resumen_salidas["salidas_mensuales"]
    ).replace([np.inf, -np.inf], np.nan)

    movimientos = fuentes["movimientos"].copy()
    movimientos["SKU"] = movimientos["SKU"].map(fase1.normalizar_clave)
    resumen_movimientos = (
        movimientos.groupby(["SKU", "ANO", "MES"])["SALIDAS"]
        .sum()
        .reset_index()
        .groupby("SKU")["SALIDAS"]
        .agg(meses_con_movimiento="size", movimientos_mensuales="mean")
        .reset_index()
        .rename(columns={"SKU": "clave_articulo"})
    )

    temporales = resumen_ventas.merge(fechas, on="articulo_id", how="outer").merge(
        resumen_salidas, on="articulo_id", how="outer"
    )
    temporales["recencia_dias"] = (FECHA_CORTE - temporales["ultima_venta_libro"]).dt.days
    temporales["antiguedad_dias"] = (FECHA_CORTE - temporales["primera_venta_libro"]).dt.days
    temporales.attrs["por_clave"] = resumen_movimientos
    return temporales


def agregar_caracteristicas(base: pd.DataFrame, etiqueta: str, temporales: pd.DataFrame) -> pd.DataFrame:
    """Construye el conjunto de características derivadas de cada base."""
    datos = normalizar_nombres(base, etiqueta)

    columnas_temporales = [
        "articulo_id", "meses_con_venta", "ventas_mensuales_unidades", "cv_ventas_mensual",
        "meses_con_salida", "salidas_mensuales", "cv_salidas_mensual",
        "recencia_dias", "antiguedad_dias",
    ]
    datos = datos.merge(temporales[columnas_temporales], on="articulo_id", how="left")
    por_clave = temporales.attrs.get("por_clave")
    if por_clave is not None:
        datos = datos.merge(por_clave, on="clave_articulo", how="left")
    for col in ("meses_con_venta", "meses_con_salida", "meses_con_movimiento"):
        datos[col] = pd.to_numeric(datos.get(col), errors="coerce").fillna(0)

    # Comportamiento de ventas
    datos["ticket_promedio"] = _division(datos["ventas_importe"], datos["ventas_eventos"])
    datos["unidades_por_venta"] = _division(datos["ventas_unidades"], datos["ventas_eventos"])
    datos["precio_efectivo"] = _division(datos["ventas_importe"], datos["ventas_unidades"])
    datos["participacion_ingresos"] = 100 * datos["ventas_importe"] / datos["ventas_importe"].sum()

    # Compras y abastecimiento
    datos["costo_promedio_compra"] = _division(datos["compras_importe"], datos["compras_unidades"])
    datos["lote_promedio_compra"] = _division(datos["compras_unidades"], datos["compras_eventos"])
    datos["ratio_compras_ventas"] = _division(datos["compras_unidades"], datos["ventas_unidades"])
    datos["margen_unitario_estimado"] = datos["precio_efectivo"] - datos["costo_promedio_compra"]
    datos["margen_pct_estimado"] = 100 * _division(
        datos["margen_unitario_estimado"], datos["precio_efectivo"]
    )

    # Existencias e inventario
    datos["rotacion_inventario"] = _division(datos["ventas_unidades"], datos["inventario_unidades"])
    datos["rotacion_salidas"] = _division(datos["salidas_unidades"], datos["inventario_unidades"])
    datos["dias_cobertura"] = _division(
        datos["inventario_unidades"] * 365, datos["ventas_unidades"]
    )
    datos["valor_unitario_inventario"] = _division(
        datos["inventario_valor"], datos["inventario_unidades"]
    )
    costo_vendido = datos["costo_promedio_compra"] * datos["ventas_unidades"]
    datos["gmroi"] = _division(datos["ventas_importe"] - costo_vendido, datos["inventario_valor"])
    datos["inventario_inmovil"] = (datos["inventario_unidades"] > 0) & (datos["salidas_unidades"] == 0)

    # Salidas de almacén
    datos["salidas_por_movimiento"] = _division(datos["salidas_unidades"], datos["salidas_eventos"])
    datos["razon_salidas_ventas"] = _division(datos["salidas_unidades"], datos["ventas_unidades"])

    # Marca y categoría
    ingresos_marca = datos.groupby("marca")["ventas_importe"].transform("sum")
    datos["ingresos_marca"] = ingresos_marca
    datos["articulos_marca"] = datos.groupby("marca")["articulo_id"].transform("size")
    datos["participacion_en_marca"] = 100 * _division(datos["ventas_importe"], ingresos_marca)
    datos["ranking_en_marca"] = (
        datos.groupby("marca")["ventas_importe"].rank(ascending=False, method="min").astype(int)
    )
    mediana_categoria = datos.groupby("categoria_tipo")["ventas_importe"].transform("median")
    datos["indice_vs_mediana_categoria"] = _division(datos["ventas_importe"], mediana_categoria)

    top_marcas = (
        datos.loc[datos["marca_comercial"], :]
        .groupby("marca")["ventas_importe"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .index
    )
    datos["marca_grupo"] = np.where(datos["marca"].isin(top_marcas), datos["marca"], "OTRAS")
    datos.loc[~datos["marca_comercial"], "marca_grupo"] = "NO COMERCIAL"

    # Tiempos de entrega
    datos["clase_entrega"] = pd.cut(
        datos["tiempo_entrega_dias_prom"],
        bins=[-np.inf, 30, 60, np.inf],
        labels=["RAPIDA", "MEDIA", "LENTA"],
    ).astype("object").fillna(SIN_DATO)
    datos["riesgo_abasto"] = _division(datos["tiempo_entrega_dias_prom"], datos["dias_cobertura"])

    # Segmentación de demanda y de valor
    datos["segmento_demanda"] = clasificar_por_terciles(
        datos["ventas_unidades"], etiquetas=("BAJA", "MEDIA", "ALTA"), sin_actividad="SIN_DEMANDA"
    )
    datos["segmento_valor"] = clasificar_por_terciles(
        datos["ventas_importe"], etiquetas=("BAJO", "MEDIO", "ALTO"), sin_actividad="SIN_VENTA"
    )
    datos["clase_abc"] = clasificar_abc(datos["ventas_importe"])
    datos["clase_rotacion"] = pd.cut(
        datos["rotacion_inventario"],
        bins=[-np.inf, 1, 4, np.inf],
        labels=["LENTA", "NORMAL", "RAPIDA"],
    ).astype("object").fillna(SIN_DATO)

    for col in CARACTERISTICAS_NUMERICAS:
        if col in datos.columns:
            datos[f"{col}_log1p"] = np.log1p(pd.to_numeric(datos[col], errors="coerce").clip(lower=0))
    return datos


def clasificar_por_terciles(serie, etiquetas, sin_actividad):
    """Clasifica en tres niveles usando solo los artículos con actividad."""
    valores = pd.to_numeric(serie, errors="coerce")
    activos = valores[valores > 0]
    resultado = pd.Series(sin_actividad, index=valores.index, dtype="object")
    if activos.empty:
        return resultado
    cortes = activos.quantile([1 / 3, 2 / 3]).tolist()
    bins = [-np.inf] + sorted(set(cortes)) + [np.inf]
    if len(bins) - 1 < 3:
        # Con una distribución muy concentrada los terciles colapsan; se usa la
        # mediana para separar al menos dos niveles.
        bins = [-np.inf, activos.median(), np.inf]
        usadas = [etiquetas[0], etiquetas[-1]]
    else:
        usadas = list(etiquetas)
    resultado.loc[activos.index] = pd.cut(activos, bins=bins, labels=usadas).astype("object")
    return resultado


def clasificar_abc(serie):
    """Clasificación ABC por Pareto acumulado del importe de ventas."""
    valores = pd.to_numeric(serie, errors="coerce").fillna(0)
    orden = valores.sort_values(ascending=False)
    acumulado = orden.cumsum() / orden.sum() if orden.sum() else orden
    clase = pd.Series("C", index=orden.index, dtype="object")
    clase[acumulado <= 0.80] = "A"
    clase[(acumulado > 0.80) & (acumulado <= 0.95)] = "B"
    clase[valores.loc[orden.index] == 0] = "SIN_VENTA"
    return clase.reindex(serie.index)


def diccionario_caracteristicas() -> pd.DataFrame:
    filas = [
        ("ticket_promedio", "Ventas", "ventas_importe / ventas_eventos", "Importe promedio por operación de venta"),
        ("unidades_por_venta", "Ventas", "ventas_unidades / ventas_eventos", "Unidades promedio vendidas por operación"),
        ("precio_efectivo", "Ventas", "ventas_importe / ventas_unidades", "Precio unitario realmente cobrado"),
        ("participacion_ingresos", "Ventas", "100 * ventas_importe / total", "Peso del artículo en los ingresos"),
        ("meses_con_venta", "Ventas", "meses distintos con venta", "Regularidad de la demanda"),
        ("ventas_mensuales_unidades", "Ventas", "promedio mensual de unidades", "Velocidad de venta"),
        ("cv_ventas_mensual", "Ventas", "desv/media mensual", "Estabilidad de la demanda"),
        ("recencia_dias", "Ventas", "corte - última venta", "Días desde la última venta"),
        ("antiguedad_dias", "Ventas", "corte - primera venta", "Antigüedad comercial del artículo"),
        ("costo_promedio_compra", "Compras", "compras_importe / compras_unidades", "Costo unitario de abastecimiento"),
        ("lote_promedio_compra", "Compras", "compras_unidades / compras_eventos", "Tamaño típico de pedido"),
        ("ratio_compras_ventas", "Compras", "compras_unidades / ventas_unidades", "Relación entre lo comprado y lo vendido"),
        ("margen_unitario_estimado", "Compras", "precio_efectivo - costo_promedio_compra", "Margen unitario estimado"),
        ("margen_pct_estimado", "Compras", "margen / precio_efectivo", "Margen porcentual estimado"),
        ("rotacion_inventario", "Inventario", "ventas_unidades / existencias", "Veces que el inventario se vende"),
        ("rotacion_salidas", "Inventario", "salidas_unidades / existencias", "Rotación medida por salidas de almacén"),
        ("dias_cobertura", "Inventario", "existencias * 365 / ventas_unidades", "Días que alcanza el inventario"),
        ("valor_unitario_inventario", "Inventario", "inventario_valor / existencias", "Costo unitario del inventario"),
        ("gmroi", "Inventario", "(ventas - costo vendido) / inventario_valor", "Retorno del margen sobre la inversión en inventario"),
        ("inventario_inmovil", "Inventario", "existencias > 0 y salidas = 0", "Inventario sin movimiento"),
        ("salidas_por_movimiento", "Salidas", "salidas_unidades / salidas_eventos", "Tamaño promedio de la salida"),
        ("razon_salidas_ventas", "Salidas", "salidas_unidades / ventas_unidades", "Salidas de almacén por unidad vendida"),
        ("meses_con_salida", "Salidas", "meses distintos con salida", "Regularidad del movimiento de almacén"),
        ("cv_salidas_mensual", "Salidas", "desv/media mensual de salidas", "Estabilidad del movimiento"),
        ("ingresos_marca", "Marca", "suma de ventas por marca", "Tamaño comercial de la marca"),
        ("articulos_marca", "Marca", "conteo de artículos por marca", "Amplitud del catálogo de la marca"),
        ("participacion_en_marca", "Marca", "100 * ventas / ventas de la marca", "Peso del artículo dentro de su marca"),
        ("ranking_en_marca", "Marca", "rango por ventas dentro de la marca", "Posición del artículo en su marca"),
        ("indice_vs_mediana_categoria", "Categoría", "ventas / mediana de la categoría", "Desempeño relativo a su categoría"),
        ("tiempo_entrega_dias_prom", "Entrega", "promedio de días por folio ligado", "Tiempo de entrega de importación"),
        ("clase_entrega", "Entrega", "<=30 rápida, <=60 media, >60 lenta", "Clasificación del tiempo de entrega"),
        ("riesgo_abasto", "Entrega", "tiempo_entrega / dias_cobertura", "Riesgo de quedarse sin inventario antes de reponer"),
        ("segmento_demanda", "Segmentación", "terciles de unidades vendidas", "Nivel de demanda alta, media o baja"),
        ("segmento_valor", "Segmentación", "terciles de importe vendido", "Nivel de valor comercial"),
        ("clase_abc", "Segmentación", "Pareto 80/15/5 de ingresos", "Clasificación ABC"),
        ("clase_rotacion", "Segmentación", "cortes en 1 y 4 vueltas", "Velocidad de rotación"),
        ("marca_grupo", "Segmentación", "8 marcas mayores + OTRAS", "Factor de marca con niveles suficientes"),
    ]
    return pd.DataFrame(filas, columns=["variable", "grupo", "formula", "interpretacion"])


def preparar_muestra(datos, variable, factores, min_n=10, excluir=(SIN_DATO, SIN_CLASIFICAR, "SIN_VENTA", "SIN_DEMANDA")):
    """Deja la muestra lista para comparar grupos.

    Quita los registros sin valor en la variable dependiente, descarta los
    niveles que solo señalan ausencia de información y elimina los grupos con
    menos de `min_n` observaciones, que vuelven inestable la prueba.
    """
    factores = [factores] if isinstance(factores, str) else list(factores)
    muestra = datos[[variable] + factores].copy()
    muestra[variable] = pd.to_numeric(muestra[variable], errors="coerce")
    muestra = muestra.replace([np.inf, -np.inf], np.nan).dropna()
    for factor in factores:
        muestra[factor] = muestra[factor].astype(str)
        muestra = muestra[~muestra[factor].isin(excluir)]
    for factor in factores:
        conteo = muestra[factor].value_counts()
        muestra = muestra[muestra[factor].isin(conteo[conteo >= min_n].index)]
    return muestra


def resumen_grupos(muestra, variable, factor):
    """Estadísticos por nivel del factor, con intervalo de confianza al 95%."""
    from scipy import stats

    filas = []
    for nivel, grupo in muestra.groupby(factor):
        x = grupo[variable]
        error = x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan
        margen = error * stats.t.ppf(0.975, len(x) - 1) if len(x) > 1 else np.nan
        filas.append(
            {
                "nivel": nivel,
                "n": len(x),
                "media": round(x.mean(), 4),
                "mediana": round(x.median(), 4),
                "desv_est": round(x.std(ddof=1), 4) if len(x) > 1 else np.nan,
                "ic95_inferior": round(x.mean() - margen, 4) if len(x) > 1 else np.nan,
                "ic95_superior": round(x.mean() + margen, 4) if len(x) > 1 else np.nan,
            }
        )
    return pd.DataFrame(filas).sort_values("media", ascending=False).reset_index(drop=True)


def anova_welch(grupos):
    """ANOVA de Welch: no supone varianzas iguales entre grupos."""
    from scipy import stats

    k = len(grupos)
    n = np.array([len(g) for g in grupos], dtype=float)
    medias = np.array([g.mean() for g in grupos])
    varianzas = np.array([g.var(ddof=1) for g in grupos])
    pesos = n / varianzas
    media_ponderada = (pesos * medias).sum() / pesos.sum()
    numerador = ((pesos * (medias - media_ponderada) ** 2).sum()) / (k - 1)
    lambda_ = (((1 - pesos / pesos.sum()) ** 2) / (n - 1)).sum()
    denominador = 1 + (2 * (k - 2) / (k**2 - 1)) * lambda_
    f = numerador / denominador
    gl2 = (k**2 - 1) / (3 * lambda_)
    p = stats.f.sf(f, k - 1, gl2)
    return f, k - 1, gl2, p


def anova_un_factor(datos, variable, factor, min_n=10):
    """ANOVA de un factor con verificación de supuestos y alternativas robustas.

    Devuelve la prueba clásica, el tamaño del efecto, la prueba de Levene sobre
    homogeneidad de varianzas, la normalidad de los residuales y dos contrastes
    que no dependen de esos supuestos: Welch y Kruskal-Wallis.
    """
    from scipy import stats

    muestra = preparar_muestra(datos, variable, factor, min_n=min_n)
    grupos = [g[variable].values for _, g in muestra.groupby(factor) if len(g) >= min_n]
    if len(grupos) < 2:
        return None, muestra

    f, p = stats.f_oneway(*grupos)
    k = len(grupos)
    n = len(muestra)
    medias = muestra.groupby(factor)[variable].mean()
    media_global = muestra[variable].mean()
    tamanos = muestra.groupby(factor)[variable].size()
    ss_entre = float((tamanos * (medias - media_global) ** 2).sum())
    ss_total = float(((muestra[variable] - media_global) ** 2).sum())
    ss_dentro = ss_total - ss_entre
    ms_dentro = ss_dentro / (n - k)
    eta2 = ss_entre / ss_total if ss_total else np.nan
    omega2 = (ss_entre - (k - 1) * ms_dentro) / (ss_total + ms_dentro) if ss_total else np.nan

    residuales = muestra[variable] - muestra.groupby(factor)[variable].transform("mean")
    muestra_normalidad = residuales.sample(min(5000, len(residuales)), random_state=7)
    shapiro_p = stats.shapiro(muestra_normalidad).pvalue if len(muestra_normalidad) >= 3 else np.nan
    levene_p = stats.levene(*grupos, center="median").pvalue
    kruskal_p = stats.kruskal(*grupos).pvalue
    welch_f, _, welch_gl2, welch_p = anova_welch(grupos)

    resultado = {
        "variable": variable,
        "factor": factor,
        "n": n,
        "niveles": k,
        "gl_entre": k - 1,
        "gl_dentro": n - k,
        "F": round(f, 4),
        "p_valor": p,
        "eta2": round(eta2, 4),
        "omega2": round(omega2, 4),
        "magnitud_efecto": magnitud_efecto(eta2),
        "levene_p": levene_p,
        "homogeneidad": "se cumple" if levene_p > 0.05 else "no se cumple",
        "shapiro_p": shapiro_p,
        "normalidad_residuales": "se cumple" if shapiro_p > 0.05 else "no se cumple",
        "welch_F": round(welch_f, 4),
        "welch_p": welch_p,
        "kruskal_p": kruskal_p,
        "conclusion": conclusion_anova(p, welch_p, kruskal_p),
    }
    return resultado, muestra


def magnitud_efecto(eta2):
    if pd.isna(eta2):
        return SIN_DATO
    if eta2 < 0.01:
        return "insignificante"
    if eta2 < 0.06:
        return "pequeño"
    if eta2 < 0.14:
        return "mediano"
    return "grande"


def conclusion_anova(p, welch_p, kruskal_p):
    pruebas = [p, welch_p, kruskal_p]
    significativas = sum(1 for valor in pruebas if pd.notna(valor) and valor < 0.05)
    if significativas == 3:
        return "diferencias significativas confirmadas por las tres pruebas"
    if significativas == 0:
        return "sin diferencias significativas"
    return "evidencia mixta, revisar supuestos"


def tukey_posthoc(muestra, variable, factor):
    """Comparaciones por pares con corrección de Tukey."""
    from statsmodels.stats.multicomp import pairwise_tukeyhsd

    resultado = pairwise_tukeyhsd(muestra[variable], muestra[factor], alpha=0.05)
    tabla = pd.DataFrame(resultado.summary().data[1:], columns=resultado.summary().data[0])
    tabla = tabla.rename(
        columns={
            "group1": "nivel_a",
            "group2": "nivel_b",
            "meandiff": "diferencia_medias",
            "p-adj": "p_ajustado",
            "lower": "ic_inferior",
            "upper": "ic_superior",
            "reject": "significativo",
        }
    )
    tabla.insert(0, "variable", variable)
    tabla.insert(1, "factor", factor)
    return tabla


def equilibrar_celdas(muestra, factores, min_celda=5, max_iteraciones=60):
    """Elimina niveles que dejan celdas vacías en el diseño factorial.

    Con celdas vacías el modelo con interacción queda sin rango completo y la
    suma de cuadrados tipo III deja de ser interpretable. Se van quitando los
    niveles que más celdas deficientes generan, sin bajar de dos niveles por
    factor; si aun así quedan huecos, se informa para no reportar tipo III.
    """
    deficientes = 0
    for _ in range(max_iteraciones):
        niveles = [sorted(muestra[f].unique()) for f in factores]
        if any(len(n) < 2 for n in niveles):
            return muestra, -1
        esperadas = pd.MultiIndex.from_product(niveles, names=factores)
        conteos = muestra.groupby(factores).size().reindex(esperadas, fill_value=0)
        huecos = conteos[conteos < min_celda]
        deficientes = len(huecos)
        if deficientes == 0:
            return muestra, 0
        candidato = None
        peor = -1
        for i, factor in enumerate(factores):
            if muestra[factor].nunique() <= 2:
                continue
            cuenta = huecos.index.get_level_values(i).value_counts()
            if len(cuenta) and cuenta.iloc[0] > peor:
                peor = cuenta.iloc[0]
                candidato = (factor, cuenta.index[0])
        if candidato is None:
            return muestra, deficientes
        muestra = muestra[muestra[candidato[0]] != candidato[1]]
    return muestra, deficientes


def anova_factorial(datos, variable, factores, min_n=10):
    """ANOVA factorial con término de interacción.

    Se reportan la suma de cuadrados tipo II y tipo III. Con diseños
    desbalanceados, que es el caso aquí, la tipo III es la que respeta el orden
    de entrada de los factores al evaluar la interacción.
    """
    import statsmodels.api as sm
    from statsmodels.formula.api import ols

    muestra = preparar_muestra(datos, variable, factores, min_n=min_n)
    if muestra.empty or any(muestra[f].nunique() < 2 for f in factores):
        return None, None, muestra

    muestra, celdas_deficientes = equilibrar_celdas(muestra, factores, min_celda=3)
    if muestra.empty or celdas_deficientes < 0 or any(muestra[f].nunique() < 2 for f in factores):
        return None, None, muestra

    terminos_ii = " * ".join(f"C({f})" for f in factores)
    modelo_ii = ols(f"{variable} ~ {terminos_ii}", data=muestra).fit()
    tabla_ii = sm.stats.anova_lm(modelo_ii, typ=2)

    tabla_iii = None
    if celdas_deficientes == 0:
        terminos_iii = " * ".join(f"C({f}, Sum)" for f in factores)
        modelo_iii = ols(f"{variable} ~ {terminos_iii}", data=muestra).fit()
        tabla_iii = sm.stats.anova_lm(modelo_iii, typ=3)

    tabla = tabla_ii.reset_index().rename(columns={"index": "termino", "PR(>F)": "p_valor"})
    ss_residual = float(tabla.loc[tabla["termino"] == "Residual", "sum_sq"].iloc[0])
    gl_residual = float(tabla.loc[tabla["termino"] == "Residual", "df"].iloc[0])
    ms_residual = ss_residual / gl_residual
    ss_total = float(tabla["sum_sq"].sum())

    tabla["eta2"] = tabla["sum_sq"] / ss_total
    tabla["eta2_parcial"] = tabla["sum_sq"] / (tabla["sum_sq"] + ss_residual)
    tabla["omega2"] = (tabla["sum_sq"] - tabla["df"] * ms_residual) / (ss_total + ms_residual)
    tabla["magnitud_efecto"] = tabla["eta2_parcial"].map(magnitud_efecto)
    tabla.loc[tabla["termino"] == "Residual", ["eta2", "eta2_parcial", "omega2", "magnitud_efecto"]] = np.nan
    tabla["significativo"] = tabla["p_valor"] < 0.05
    tabla["variable"] = variable
    tabla["tipo_suma_cuadrados"] = "II"

    partes = [tabla]
    if tabla_iii is not None:
        tabla3 = tabla_iii.reset_index().rename(columns={"index": "termino", "PR(>F)": "p_valor"})
        tabla3["variable"] = variable
        tabla3["tipo_suma_cuadrados"] = "III"
        tabla3["significativo"] = tabla3["p_valor"] < 0.05
        partes.append(tabla3)

    resumen = pd.concat(partes, ignore_index=True)
    resumen["r2_modelo"] = modelo_ii.rsquared
    resumen["n"] = len(muestra)
    resumen["celdas_deficientes"] = celdas_deficientes
    resumen["niveles_usados"] = " | ".join(
        f"{f}={muestra[f].nunique()}" for f in factores
    )
    return resumen, modelo_ii, muestra


def medias_de_celda(muestra, variable, factores):
    """Medias por combinación de factores: la base del gráfico de interacción."""
    tabla = (
        muestra.groupby(list(factores))[variable]
        .agg(n="size", media="mean", desv_est="std")
        .reset_index()
    )
    tabla["media"] = tabla["media"].round(4)
    tabla["desv_est"] = tabla["desv_est"].round(4)
    return tabla


def grafico_interaccion(muestra, variable, factores, archivo, titulo=None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    factor_x, factor_linea = factores[0], factores[1]
    tabla = muestra.groupby([factor_x, factor_linea])[variable].mean().unstack()

    fig, eje = plt.subplots(figsize=(10, 5.5))
    for columna in tabla.columns:
        eje.plot(tabla.index, tabla[columna], marker="o", label=str(columna))
    eje.set_xlabel(factor_x)
    eje.set_ylabel(f"media de {variable}")
    eje.set_title(titulo or f"Interacción {factor_x} x {factor_linea}", fontsize=11)
    eje.legend(title=factor_linea, fontsize=8)
    eje.tick_params(axis="x", rotation=30, labelsize=8)
    eje.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(DIR_FIGURAS / archivo, dpi=110)
    plt.close(fig)


def grafico_cajas_por_factor(muestra, variable, factor, archivo, titulo=None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    niveles = muestra.groupby(factor)[variable].median().sort_values(ascending=False).index
    datos = [muestra.loc[muestra[factor] == nivel, variable].values for nivel in niveles]

    fig, eje = plt.subplots(figsize=(11, 5.5))
    eje.boxplot(datos, tick_labels=[str(n) for n in niveles], showfliers=False)
    medias = [np.mean(d) for d in datos]
    eje.plot(range(1, len(medias) + 1), medias, "o", color="#bc4749", label="media")
    eje.set_ylabel(variable)
    eje.set_title(titulo or f"{variable} por {factor}", fontsize=11)
    eje.tick_params(axis="x", rotation=30, labelsize=8)
    eje.legend(fontsize=8)
    eje.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(DIR_FIGURAS / archivo, dpi=110)
    plt.close(fig)
