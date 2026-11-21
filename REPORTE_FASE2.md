# Fase 2. Características, ANOVA y aplicación de exploración

Documento generado por `ejecutar_fase2.py` a partir de las bases preprocesadas en la Fase 1.

## 1. Extracción de características

Se construyeron 37 características agrupadas en 8 bloques:

- **Ventas** (9): ticket_promedio, unidades_por_venta, precio_efectivo, participacion_ingresos, meses_con_venta, ventas_mensuales_unidades, cv_ventas_mensual, recencia_dias, antiguedad_dias
- **Compras** (5): costo_promedio_compra, lote_promedio_compra, ratio_compras_ventas, margen_unitario_estimado, margen_pct_estimado
- **Inventario** (6): rotacion_inventario, rotacion_salidas, dias_cobertura, valor_unitario_inventario, gmroi, inventario_inmovil
- **Salidas** (4): salidas_por_movimiento, razon_salidas_ventas, meses_con_salida, cv_salidas_mensual
- **Marca** (4): ingresos_marca, articulos_marca, participacion_en_marca, ranking_en_marca
- **Categoría** (1): indice_vs_mediana_categoria
- **Entrega** (3): tiempo_entrega_dias_prom, clase_entrega, riesgo_abasto
- **Segmentación** (5): segmento_demanda, segmento_valor, clase_abc, clase_rotacion, marca_grupo

Las dos bases nombran distinto los mismos conceptos, así que primero se traducen a un juego
único de columnas (`ventas_importe`, `ventas_unidades`, `compras_importe`, `inventario_unidades`...)
y sobre esas se calcula todo. Las razones que no están definidas, como la rotación de un artículo
sin existencias, quedan como nulo en vez de infinito.

| Característica | Mediana base inicial | Mediana base complementaria |
|---|---|---|
| ticket_promedio | 753.22 | 748.85 |
| unidades_por_venta | 1.14 | 1.12 |
| precio_efectivo | 609.82 | 609.82 |
| rotacion_inventario | 0.44 | 0.67 |
| dias_cobertura | 34.88 | 34.88 |
| margen_pct_estimado | 43.18 | 43.18 |
| ratio_compras_ventas | 1.31 | 1.31 |
| gmroi | 0.52 | 0.52 |

### Clasificación de artículos por nivel de demanda

| Segmento | Base inicial | Base complementaria |
|---|---|---|
| ALTA | 1,293 | 1,293 |
| MEDIA | 1,254 | 1,254 |
| BAJA | 1,348 | 1,348 |
| SIN_DEMANDA | 2,160 | 1,084 |

Clasificación ABC de la base inicial: 168 artículos clase A concentran el 80% de los ingresos,
449 clase B, 3,239 clase C y 2,199 sin venta registrada.

## 2. ANOVA de un factor

Cada prueba compara la variable dependiente entre los niveles de un factor. Se excluyen los niveles
que solo indican ausencia de información y los grupos con menos de 10 artículos. Junto al ANOVA clásico
se reportan la prueba de Levene, la normalidad de residuales, el ANOVA de Welch y Kruskal-Wallis,
porque las variables de negocio rara vez cumplen los supuestos clásicos.

| Variable | Factor | n | Niveles | F | p | eta² | Efecto | Welch p | Kruskal p |
|---|---|---|---|---|---|---|---|---|---|
| ticket_promedio_log1p | categoria_tipo | 3,738 | 4 | 394.56 | <0.0001 | 0.2407 | grande | <0.0001 | <0.0001 |
| ticket_promedio_log1p | categoria_tecnologia | 3,725 | 2 | 1,098.96 | <0.0001 | 0.2279 | grande | <0.0001 | <0.0001 |
| ticket_promedio_log1p | marca_grupo | 3,889 | 9 | 160.58 | <0.0001 | 0.2487 | grande | <0.0001 | <0.0001 |
| ticket_promedio_log1p | segmento_demanda | 3,895 | 3 | 3.05 | 0.0476 | 0.0016 | insignificante | 0.0544 | 0.1877 |
| ventas_mensuales_unidades_log1p | categoria_tipo | 3,748 | 4 | 20.28 | <0.0001 | 0.016 | pequeño | <0.0001 | <0.0001 |
| ventas_mensuales_unidades_log1p | categoria_tecnologia | 3,736 | 2 | 28.19 | <0.0001 | 0.0075 | insignificante | <0.0001 | <0.0001 |
| ventas_mensuales_unidades_log1p | marca_grupo | 3,924 | 9 | 44.65 | <0.0001 | 0.0836 | mediano | <0.0001 | <0.0001 |
| ventas_mensuales_unidades_log1p | segmento_demanda | 3,895 | 3 | 1,462.17 | <0.0001 | 0.429 | grande | <0.0001 | <0.0001 |
| rotacion_inventario_log1p | categoria_tipo | 2,571 | 4 | 16.24 | <0.0001 | 0.0186 | pequeño | <0.0001 | <0.0001 |
| rotacion_inventario_log1p | categoria_tecnologia | 2,728 | 2 | 24.41 | <0.0001 | 0.0089 | insignificante | <0.0001 | <0.0001 |
| rotacion_inventario_log1p | marca_grupo | 2,925 | 6 | 26.39 | <0.0001 | 0.0433 | pequeño | <0.0001 | <0.0001 |
| rotacion_inventario_log1p | segmento_demanda | 2,165 | 3 | 658.79 | <0.0001 | 0.3787 | grande | <0.0001 | <0.0001 |
| margen_pct_estimado | categoria_tipo | 2,735 | 4 | 99.31 | <0.0001 | 0.0984 | mediano | <0.0001 | <0.0001 |
| margen_pct_estimado | categoria_tecnologia | 2,719 | 2 | 45.55 | <0.0001 | 0.0165 | pequeño | <0.0001 | <0.0001 |
| margen_pct_estimado | marca_grupo | 2,868 | 9 | 13.41 | <0.0001 | 0.0362 | pequeño | <0.0001 | <0.0001 |
| margen_pct_estimado | segmento_demanda | 2,869 | 3 | 7.77 | 0.0004 | 0.0054 | insignificante | <0.0001 | 0.0005 |

De 16 pruebas en la base inicial, 16 resultan significativas al 5%.
El efecto más grande es el de `segmento_demanda` sobre `ventas_mensuales_unidades_log1p` (eta² = 0.429, efecto grande).

Supuestos: en 14 de 16 pruebas se rechaza la homogeneidad de varianzas y en
16 se rechaza la normalidad de los residuales. Por eso la conclusión se toma de las tres
pruebas en conjunto y no solo del estadístico F.

## 3. ANOVA factorial y efecto de interacción

Se estimaron modelos de dos y tres factores con término de interacción. Al ser un diseño desbalanceado
se reportan las sumas de cuadrados tipo II y tipo III. Antes de estimar se eliminan los niveles que dejan
celdas con menos de tres artículos, porque una celda vacía deja el modelo con interacción sin rango completo
y vuelve ininterpretable la suma de cuadrados tipo III. La columna `niveles_usados` del CSV indica cuántos
niveles sobrevivieron en cada modelo.

| Modelo | Término | gl | F | p | eta² parcial | Efecto |
|---|---|---|---|---|---|---|
| categoria_tipo x categoria_tecnologia | C(categoria_tipo) | 3 | 331.09 | <0.0001 | 0.2120 | grande |
| categoria_tipo x categoria_tecnologia | C(categoria_tecnologia) | 1 | 723.64 | <0.0001 | 0.1639 | grande |
| categoria_tipo x categoria_tecnologia | C(categoria_tipo):C(categoria_tecnologia) | 3 | 35.69 | <0.0001 | 0.0282 | pequeño |
| marca_grupo x categoria_tipo | C(marca_grupo) | 5 | 185.69 | <0.0001 | 0.2146 | grande |
| marca_grupo x categoria_tipo | C(categoria_tipo) | 1 | 646.23 | <0.0001 | 0.1598 | grande |
| marca_grupo x categoria_tipo | C(marca_grupo):C(categoria_tipo) | 5 | 11.96 | <0.0001 | 0.0173 | pequeño |
| categoria_tipo x segmento_demanda | C(categoria_tipo) | 3 | 6.25 | 0.0003 | 0.0089 | insignificante |
| categoria_tipo x segmento_demanda | C(segmento_demanda) | 2 | 630.10 | <0.0001 | 0.3759 | grande |
| categoria_tipo x segmento_demanda | C(categoria_tipo):C(segmento_demanda) | 6 | 1.12 | 0.3468 | 0.0032 | insignificante |
| categoria_tecnologia x clase_abc | C(categoria_tecnologia) | 1 | 31.94 | <0.0001 | 0.0086 | insignificante |
| categoria_tecnologia x clase_abc | C(clase_abc) | 2 | 329.93 | <0.0001 | 0.1517 | grande |
| categoria_tecnologia x clase_abc | C(categoria_tecnologia):C(clase_abc) | 2 | 19.33 | <0.0001 | 0.0104 | pequeño |
| categoria_tipo x categoria_tecnologia x segmento_demanda | C(categoria_tipo) | 3 | 346.45 | <0.0001 | 0.2204 | grande |
| categoria_tipo x categoria_tecnologia x segmento_demanda | C(categoria_tecnologia) | 1 | 696.87 | <0.0001 | 0.1594 | grande |
| categoria_tipo x categoria_tecnologia x segmento_demanda | C(segmento_demanda) | 2 | 4.32 | 0.0134 | 0.0023 | insignificante |
| categoria_tipo x categoria_tecnologia x segmento_demanda | C(categoria_tipo):C(categoria_tecnologia) | 3 | 28.07 | <0.0001 | 0.0224 | pequeño |
| categoria_tipo x categoria_tecnologia x segmento_demanda | C(categoria_tipo):C(segmento_demanda) | 6 | 6.12 | <0.0001 | 0.0099 | insignificante |
| categoria_tipo x categoria_tecnologia x segmento_demanda | C(categoria_tecnologia):C(segmento_demanda) | 2 | 13.11 | <0.0001 | 0.0071 | insignificante |
| categoria_tipo x categoria_tecnologia x segmento_demanda | C(categoria_tipo):C(categoria_tecnologia):C(segmento_demanda) | 6 | 6.04 | <0.0001 | 0.0098 | insignificante |
| categoria_tipo x categoria_tecnologia x marca_grupo | C(categoria_tipo) | 1 | 404.09 | <0.0001 | 0.2159 | grande |
| categoria_tipo x categoria_tecnologia x marca_grupo | C(categoria_tecnologia) | 1 | 66.27 | <0.0001 | 0.0432 | pequeño |
| categoria_tipo x categoria_tecnologia x marca_grupo | C(marca_grupo) | 1 | 50.85 | <0.0001 | 0.0335 | pequeño |
| categoria_tipo x categoria_tecnologia x marca_grupo | C(categoria_tipo):C(categoria_tecnologia) | 1 | 3.30 | 0.0696 | 0.0022 | insignificante |
| categoria_tipo x categoria_tecnologia x marca_grupo | C(categoria_tipo):C(marca_grupo) | 1 | 0.00 | 0.9953 | 0.0000 | insignificante |
| categoria_tipo x categoria_tecnologia x marca_grupo | C(categoria_tecnologia):C(marca_grupo) | 1 | 0.42 | 0.5195 | 0.0003 | insignificante |
| categoria_tipo x categoria_tecnologia x marca_grupo | C(categoria_tipo):C(categoria_tecnologia):C(marca_grupo) | 1 | 11.29 | 0.0008 | 0.0076 | insignificante |

De 12 términos de interacción evaluados, 8 son significativos al 5%.
La interacción más fuerte es `C(categoria_tipo):C(categoria_tecnologia)` en el modelo categoria_tipo x categoria_tecnologia (eta² parcial = 0.0282, efecto pequeño):
el efecto de un factor sobre la variable depende del nivel del otro, de modo que los efectos principales
no se pueden leer de forma aislada. Conviene notar que, aun siendo significativas, las interacciones
explican mucho menos varianza que los efectos principales, así que el peso del negocio sigue estando en
el tipo de producto, la tecnología y la marca por separado.

Las figuras `interaccion_*.png` muestran las medias por celda: líneas paralelas indican ausencia de
interacción y líneas que se cruzan o cambian de pendiente indican que sí la hay.

## 4. Comparación entre la versión inicial y la complementaria

| Indicador | inicial | complementaria |
|---|---|---|
| articulos | 6,055 | 4,979 |
| variables | 154 | 181 |
| articulos_con_venta | 3,856 | 3,856 |
| articulos_con_inventario | 2,948 | 2,556 |
| inventario_inmovil | 772 | 380 |
| importe_total_ventas | 525,064,079.06 | 525,064,079.06 |
| ticket_promedio_mediano | 753.22 | 748.85 |
| rotacion_inventario_mediana | 0.44 | 0.67 |
| margen_pct_mediano | 43.18 | 43.18 |
| articulos_clase_A | 168 | 168 |
| anova_significativos | 16 | 15 |
| anova_ejecutados | 16 | 16 |

La versión complementaria cubre menos artículos porque parte del catálogo que sí tiene equivalencia de
clave, pero incorpora el segundo corte de inventario y el histórico de entradas y salidas, lo que permite
medir variación de existencias y regularidad de movimiento que la versión inicial no tiene.

## 5. Aplicación Streamlit

`app_streamlit.py` explora ambas bases con:

- Tarjetas de indicadores: artículos, ingresos, ticket promedio, rotación, inventario inmóvil y clase A.
- Filtros por base, marca, tipo de producto, tecnología, segmento de demanda, clase ABC y rango de ingresos.
- Selectores dinámicos de variable para histograma, dispersión y comparación por factor.
- Resultados de ANOVA de un factor y factorial con el término de interacción y su gráfica.
- Comparación lado a lado de la versión inicial y la complementaria.
- Tabla interactiva y descarga de resultados en CSV y Excel.

Para ejecutarla:

```
cd fase2
streamlit run app_streamlit.py
```

## 6. Limitaciones del análisis

- El margen es estimado: compara el precio efectivo de venta contra el costo promedio de compra del periodo,
  no contra el costo de la partida vendida. Artículos con compras en un periodo y ventas en otro arrojan márgenes extremos.
- El tiempo de entrega solo existe para artículos con folio de importación ligado, así que los análisis que lo
  usan se restringen a esa submuestra y no son generalizables al catálogo completo.
- Los factores están desbalanceados: hay marcas con cientos de artículos y otras con unidades. Se agrupan las
  marcas menores en OTRAS y se exigen al menos 10 artículos por nivel, pero el desbalance permanece.
- La rotación usa el inventario de un corte, no el inventario promedio del periodo, porque no hay una serie de
  existencias. Es una aproximación, no la rotación contable.