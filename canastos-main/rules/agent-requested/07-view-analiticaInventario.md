# 07 - View: analiticaInventario

## Description
Schema completo, campos, medidas, dimensiones, casos de uso, conceptos críticos y errores específicos de analiticaInventario. Keywords: analiticaInventario, estadoInventario, inventario, stock, inventario CEDIS, stock tiendas, días de inventario, inventario negativo, capturas inventario, unidades de medida, KG PZ LT, tipoUbicacion.

---

## Propósito

Analizar niveles de stock y valor de inventario por producto y sucursal.

**IMPORTANTE:** CEDIS concentra 70-80% del inventario total (bodega central). Tiendas tienen 5-50 kg promedio.

## Schema

### Medidas

- MEASURE(unidadesActuales) - Unidades en stock
- MEASURE(valorCostoActual) - Valor del inventario a costo
- MEASURE(stockPromedio) - Stock promedio por ubicación
- MEASURE(numUbicaciones) - Número de sucursales/ubicaciones con el producto
- MEASURE(stockMinimo) - Stock mínimo encontrado
- MEASURE(stockMaximo) - Stock máximo encontrado

### Dimensiones

- fechaCaptura (timestamp) - Fecha de captura del inventario
- anio (number) - Año de la captura (calculado directamente en historicoInventario)
- numMes (number) - Número del mes (1-12) (calculado directamente en historicoInventario)
- nombreMes (string) - Nombre del mes (ej: "November") (calculado directamente en historicoInventario)
- diaSemana (string) - Día de la semana (ej: "Monday", "Tuesday") (calculado directamente en historicoInventario)
- sucursal - Nombre de la sucursal
- marca - Categoría principal del producto
- linea - Subcategoría del producto
- producto - Nombre del producto
- sku - Código único de producto (sin ceros: 58, 1234)
- unidadMedida (KG, PZ, LT, etc.) - Unidad de medida del producto
- tipoUbicacion (CEDIS, MAYOREO, MENUDEO, TIENDA) - Tipo de ubicación

### Segmentos Disponibles

- soloTiendas - Excluye CEDIS, MAYOREO, MENUDEO
- soloCEDIS - Solo bodega central
- inventarioPositivo - Solo inventarios > 0
- inventarioNegativo - Solo inventarios < 0 (faltantes/errores)

## Notas Importantes

- Capturas irregulares: 1-3 veces/mes (NO diarias) - Datos NO son real-time
- Inventarios negativos indican ventas sin reabastecimiento o errores
- SKUs en inventario usan formato sin ceros: 58, 1234
- Para análisis cross-view con ventas, considerar que ventas usa SKUs con ceros (00058, 01234)

## Casos de Uso

- Análisis de disponibilidad total de inventario
- Análisis de distribución de inventario (CEDIS vs Tiendas)
- Detección de faltantes (inventarios negativos)
- Cálculo de días de inventario disponible
- Análisis de rotación de inventario
- Análisis comparativo inventario vs ventas

## Conceptos Críticos

### CEDIS vs Tiendas

**CEDIS (Centro de Distribución)**
- Es la bodega central de la compañía
- Concentra 70-80% del inventario total
- Reabastece a las tiendas diariamente (movimientos NO registrados)
- Aparece como sucursal = 'CEDIS' o tipoUbicacion = 'CEDIS'
- Stock típico por producto: Cientos o miles de kg

**Tiendas**
- Stock de exhibición y piso de venta
- Promedio: 5-50 kg por producto
- Se reabastecen desde CEDIS continuamente
- Movimientos internos CEDIS → Tiendas NO están capturados
- 30+ sucursales de tienda física
- Aparecen como tipoUbicacion = 'TIENDA'

**MAYOREO y MENUDEO**
- Formatos especiales de venta
- ABASTOS MAYOREO y ABASTOS MENUDEO son sucursales separadas
- También tienen stock de exhibición
- Aparecen como tipoUbicacion = 'MAYOREO' o 'MENUDEO'

### ERROR COMÚN: Analizar inventario sin CEDIS

**Incorrecto:**
"LIBERTAD tiene 14 kg de Ciruela Pasa → Inventario bajo"

Esto ignora que CEDIS tiene 5,676 kg. La tienda se reabastece continuamente desde CEDIS.

**Correcto:**
"Inventario total: 6,729 kg (CEDIS: 5,676 kg + Tiendas: 1,053 kg)"
"Días de inventario: 6,729 kg / 114 kg/día = 59 días"

### Capturas Irregulares

NO hay capturas diarias. Frecuencia: 1-3 veces/mes por producto.

**Implicaciones:**
1. Datos NO son real-time - Pueden tener días/semanas de antigüedad
2. Fechas varían por producto - Un producto puede tener captura del día 5, otro del día 12
3. Para análisis temporal: Verificar primero qué fechas tienen datos disponibles

### Unidades de Medida

**Productos a Granel (mayoría)**
- Unidad: KG (kilogramos)
- Inventario: existencia = kg en stock (ej: 14 kg, 5676 kg)
- Ejemplo: "CIRUELA PASA A GRANEL" → unidadMedida: KG

**Productos Empaquetados (minoría)**
- Unidad: PZ (piezas), LT (litros), etc.
- Ver campo unidadMedida en analiticaInventario
- Ejemplo: "CAJA DE GALLETAS" → unidadMedida: PZ

**IMPORTANTE**
NO confundir "unidades" con "cajas" o "bultos". El campo existencia en la BD YA está en la unidad de medida especificada.

Si dice "14 KG" → son 14 kilogramos, NO 14 cajas.

### Inventarios Negativos

Indican problemas operativos:
- Ventas sin reabastecimiento capturado
- Errores en captura de inventario
- Faltantes físicos

**Detectar inventarios negativos:**
Usar HAVING MEASURE(unidadesActuales) < 0

**Acción:** Estos casos requieren revisión manual y ajuste de inventario.

### Días de Inventario Disponible

**Fórmula:**  
Días de Inventario = Inventario Total / Ventas Promedio Diarias

**Rangos Saludables:**
- CEDIS + Tiendas: 30-60 días (inventario completo)
- Solo Tiendas: 3-7 días (se reabastecen desde CEDIS)

**Cálculo en 2 pasos:**
1. Ver inventario total desde analiticaInventario
2. Ver ventas diarias promedio desde analiticaVentas (query separado)

### Conversión de SKUs (Cross-View Analysis)

**Ventas (analiticaVentas):** SKU con ceros → 00058, 01234  
**Inventario (analiticaInventario):** SKU sin ceros → 58, 1234

**Al hacer análisis cross-view:**
1. Top productos vendidos desde analiticaVentas (sku = '00058', '00404', '00955')
2. Consultar inventario quitando ceros (sku IN ('58', '404', '955'))

## Estrategias de Análisis

**Para disponibilidad total:**
Usar inventario total (suma de todas las ubicaciones) - GROUP BY producto

**Para análisis operativo:**
Usar por sucursal individual - GROUP BY sucursal, producto

**Para análisis de distribución:**
Usar tipoUbicacion - GROUP BY tipoUbicacion, producto

**Usar Segmentos Predefinidos:**
- analiticaInventario.soloTiendas - Solo tiendas (excluye CEDIS)
- analiticaInventario.soloCEDIS - Solo CEDIS
- analiticaInventario.inventarioPositivo - Solo inventarios positivos
- analiticaInventario.inventarioNegativo - Solo inventarios negativos

## Métricas de Calidad

| Indicador | Valor Actual | Estado |
|-----------|--------------|--------|
| Concentración en CEDIS | 70-80% | Normal (bodega central) |
| Stock promedio tiendas | 5-50 kg | Normal (exhibición) |
| Frecuencia capturas | 1-3 veces/mes | Periódico (no diario) |
| Inventarios negativos | <1% sucursales | Errores operativos detectados |
| Productos sin datos inventario | Variable | Ej: PISTACHE (1062) sin datos |

## Errores Comunes Específicos

**Error:** Inventario parece bajo vs ventas
- **Causa:** Solo viendo sucursal individual sin CEDIS
- **Solución:** Usar tipoUbicacion o sumar todas las ubicaciones

**Error:** Inventario negativo en sucursal
- **Causa:** Ventas sin reabastecimiento o error captura
- **Solución:** Usar HAVING MEASURE(unidadesActuales) < 0 para detectar

**Error:** Producto no aparece en inventario
- **Causa:** SKU no capturado o desincronización sistemas
- **Solución:** Verificar en tabla fuente directa o reportar

**Error:** Días de inventario muy bajos
- **Causa:** Alta rotación o capturas desactualizadas
- **Solución:** Normal para productos de alta demanda (ej: CIRUELA)

## Tips de Análisis

1. Siempre considerar CEDIS en análisis de disponibilidad
2. Validar fechas de captura antes de análisis temporal
3. No esperar datos diarios - Usar últimas capturas disponibles
4. Inventarios negativos = problema operativo - Reportar para ajuste
5. Conversión de SKUs - Recordar quitar ceros al cruzar con ventas
6. Días de inventario: Calcular con inventario total, no por sucursal individual

