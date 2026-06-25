# 06 - View: analiticaVentas

## Description
Schema completo, campos, medidas, dimensiones, casos de uso, conceptos relacionados y errores específicos de analiticaVentas. Keywords: analiticaVentas, ventas, ingresos, utilidad, tickets, productos vendidos, clasificación productos, SKU, marca, linea.

---

## Propósito

Analizar ventas con detalle de productos, clientes, rentabilidad y comportamiento.

## Schema

### Medidas

- MEASURE(ingresoTotal) - Ingresos totales
- MEASURE(costoTotal) - Costo total de productos vendidos
- MEASURE(utilidadBruta) - Utilidad bruta (ingreso - costo)
- MEASURE(cantidadVendida) - Unidades vendidas
- MEASURE(conteoTickets) - Número de tickets/transacciones
- MEASURE(valorTicketPromedio) - Valor promedio por ticket

### Dimensiones

- fecha (timestamp) - Fecha de la transacción (desde partidasVenta)
- anio (number) - Año de la transacción (calculado directamente en partidasVenta)
- numMes (number) - Número del mes (1-12) (calculado directamente en partidasVenta)
- nombreMes (string) - Nombre del mes (ej: "November") (calculado directamente en partidasVenta)
- diaSemana (string) - Día de la semana (ej: "Monday", "Tuesday") (calculado directamente en partidasVenta)
- sucursal - Nombre de la sucursal
- marca - Categoría principal del producto (ej: A, SYS, N, CE)
- linea - Subcategoría del producto (ej: L08, L23, L07)
- nombreProducto - Nombre del producto
- sku - Código único de producto (con ceros: 00058, 01234)
- nombreCliente - Nombre del cliente
- codigoCliente - Código del cliente
- numeroTicket - Folio del ticket/transacción

## Notas Importantes

- marca y linea pueden ser NULL o 'DESCONOCIDA' (~1% casos) - Es normal
- nombreCliente puede ser NULL (~15% casos) - Normal para ventas sin registro de cliente
- SKUs en ventas usan formato con ceros: 00058, 01234
- Para análisis cross-view con inventario, considerar que inventario usa SKUs sin ceros (58, 1234)

## Casos de Uso

- Análisis de ventas por periodo (anio, mes, día)
- Análisis de ventas por sucursal
- Análisis de rentabilidad por producto, marca o línea
- Identificación de productos más vendidos
- Análisis de comportamiento de clientes
- Validación de completitud de clasificación de productos

## Conceptos Relacionados

### Clasificación de Productos

**SKUs Numéricos (ej: 00058, 01234)**
- Se clasifican mediante join a catálogo de inventario
- Completitud: >99%

**SKUs Alfanuméricos (ej: L00125, G0337)**
- Se clasifican mediante parsing de descripción del producto
- Completitud: ~95% (depende de calidad de descripciones)
- Ejemplo: "CIRUELA PASA A GRANEL L08" → marca: A, linea: L08

**Casos Sin Clasificar (~1-2%)**
- SKUs temporales (productos nuevos ingresados manualmente)
- Productos sin descripción suficiente
- Aparecen como marca = NULL o marca = 'DESCONOCIDA'
- Es NORMAL tener este pequeño porcentaje

### Métricas de Calidad

| Indicador | Valor Actual | Estado |
|-----------|--------------|--------|
| Completitud marca/línea Oct-Nov 2025 | 98.86% | Excelente |
| Completitud 2024-2025 | 98.46% | Excelente |
| Ventas Clasificadas (por monto) | 99.76% | Sobresaliente |
| NULLs en nombreCliente | ~15% | Normal (clientes sin registrar) |

**Interpretación:**
- 98.86% de tickets tienen marca/línea correcta → Solo 1.14% sin clasificar
- 99.76% del monto de ventas está clasificado → Los productos sin clasificar son de bajo valor
- 15% de NULLs en cliente es esperado (ventas sin registro de cliente)

## Filtros Comunes

### Filtrar productos clasificados solamente:
WHERE marca IS NOT NULL AND marca != 'DESCONOCIDA'

### Ver solo productos sin clasificar:
WHERE marca IS NULL OR marca = 'DESCONOCIDA'

### Excluir sucursal de prueba:
WHERE sucursal != 'DPBodega-Test'

## Errores Comunes Específicos

**Error:** Alto % marca NULL (>5%)
- **Causa:** Problema en join o parsing
- **Solución:** Revisar modelo de cubes, verificar primary keys

**Error:** SKU numérico sin clasificar
- **Causa:** No existe en catálogo de inventario
- **Solución:** Normal si producto nuevo, revisar si persiste >1 semana

**Error:** SKU alfanumérico sin clasificar
- **Causa:** Descripción mal formateada o sin patrón
- **Solución:** Normal ~5%, revisar si >10%

**Error:** Cliente NULL ~50%
- **Causa:** Sucursal no captura clientes
- **Solución:** Normal para algunas sucursales, revisar proceso

## Tips de Análisis

1. Priorizar por monto: Los productos sin clasificar suelen ser de bajo valor (0.24% del monto total)
2. Revisar tendencias: Monitorear si % sin clasificar aumenta mes a mes
3. Filtrar en análisis críticos: Para reportes de rentabilidad por marca/línea, excluir productos sin clasificar
4. No confundir con error: 1-2% sin clasificar es operacionalmente normal

