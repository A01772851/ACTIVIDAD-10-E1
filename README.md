# Dashboard CLV | Explorador de artículos

Aplicación para explorar el catálogo de artículos de CLV: indicadores comerciales, de inventario y de
abastecimiento, más los análisis de varianza sobre las dos versiones de la base consolidada.

La carpeta es autocontenida: trae los datos ya procesados, no necesita los archivos de Excel
originales ni conexión a ninguna base de datos.

## Cómo abrirlo (Windows)

1. Instalar Python 3.11 o superior desde python.org, marcando la casilla **Add Python to PATH**.
2. Doble clic en `iniciar_dashboard.bat`.

La primera vez tarda un par de minutos instalando librerías. Después abre el navegador en
`http://localhost:8501`. Para cerrarlo, cerrar la ventana negra de la consola.

## Cómo abrirlo (manual, cualquier sistema)

```
pip install -r requirements.txt
streamlit run app_streamlit.py
```

## Qué contiene

| Pestaña | Contenido |
|---|---|
| Resumen | Indicadores de artículos, ingresos, ticket promedio, valor de inventario, rotación e inventario inmóvil; ingresos por marca, composición por tipo de producto, nivel de demanda y clase ABC |
| Exploración | Selectores de variable para histograma, dispersión y resumen por factor |
| Estadística | ANOVA de un factor con supuestos y pruebas robustas, comparaciones de Tukey, ANOVA factorial y gráfico de interacción, todo sobre la selección vigente |
| Comparación de versiones | Versión inicial frente a complementaria: cobertura, indicadores y consistencia |
| Datos | Tabla con selección de columnas y descarga en CSV y Excel |

En la barra lateral se elige la versión de la base y se filtra por marca, tipo de producto,
tecnología, nivel de demanda, clase ABC, rango de ingresos o búsqueda por nombre o clave.

## Estructura

```
dashboard_clv/
  iniciar_dashboard.bat        lanzador para Windows
  app_streamlit.py             la aplicación
  clv_fase2.py                 características y funciones estadísticas
  requirements.txt             librerías necesarias
  REPORTE_FASE2.md             metodología, resultados y limitaciones
  .streamlit/config.toml       tema visual
  salidas/bases/               las dos bases con características (Parquet)
  salidas/reportes/            resultados estadísticos precalculados (CSV)
```

## Nota sobre los datos

Los datos corresponden al corte de inventario del 15 de octubre de 2026 y al histórico de ventas
2023-2026. Para regenerarlos hay que correr las fases 1 y 2 del proyecto completo; esta carpeta solo
los consume.
