# 10 - View: analiticaDevoluciones

## Description
Schema completo, campos, medidas, dimensiones, casos de uso, conceptos relacionados y errores específicos de analiticaDevoluciones. Keywords: analiticaDevoluciones, devoluciones, tasa devoluciones, ventas netas, DEV, DV, tipo documento, devoluciones por sucursal, devoluciones por cliente.

---

## Propósito

Análisis detallado de devoluciones por tipo de documento. Permite analizar comportamiento de devoluciones por sucursal, fecha y cliente.

## Schema

### Medidas del Cubo Base

- MEASURE(importeTotal) - Importe total del documento
- MEASURE(importeVentas) - Importe de ventas (REM + FAC)
- MEASURE(importeDevoluciones) - Importe de devoluciones (DEV + DV)
- MEASURE(importeNeto) - Importe neto
- MEASURE(descuentoTotal) - Descuentos totales
- MEASURE(impuestoTotal) - Impuestos totales
- MEASURE(precioTotal) - Precio total
- MEASURE(costoTotal) - Costo total

### Medidas Calculadas

- MEASURE(tasaDevoluciones) - Porcentaje de devoluciones sobre ventas brutas
- MEASURE(ventasNetas) - Ventas brutas menos devoluciones
- MEASURE(promedioDevolucion) - Importe promedio de cada devolución
- MEASURE(promedioVenta) - Importe promedio de cada venta

### Conteos

- MEASURE(conteoDocumentos) - Número total de documentos
- MEASURE(conteoVentas) - Número de ventas (REM + FAC)
- MEASURE(conteoDevoluciones) - Número de devoluciones (DEV + DV)
- MEASURE(porcentajeDevoluciones) - Porcentaje de documentos que son devoluciones

### Dimensiones

- fechaVenta (timestamp) - Fecha de la venta/devolución
- anio (number) - Año de la transacción (calculado directamente en ventasPorDocumento)
- numMes (number) - Número del mes (1-12) (calculado directamente en ventasPorDocumento)
- nombreMes (string) - Nombre del mes (ej: "November") (calculado directamente en ventasPorDocumento)
- diaSemana (string) - Día de la semana (ej: "Monday", "Tuesday") (calculado directamente en ventasPorDocumento)
- sucursal - Nombre de la sucursal
- tipoDocumento - Tipo de documento (REM, FAC, DEV, DV)
- estado - Estado del documento
- numeroVenta - Número de venta/documento
- cliente - Código del cliente
- vendedor - Código del vendedor
- serieDocumento - Serie del documento
- observaciones - Observaciones del documento

### Segmentos Disponibles

- soloDevoluciones - Filtra solo documentos de devolución (DEV, DV)
- soloVentas - Filtra solo documentos de venta (REM, FAC)
- devolucionesAltas - Devoluciones individuales mayores a $500
- conDevoluciones - Períodos con devoluciones (importeDevoluciones > 0)
- documentosViables - Solo documentos viables (excluye cancelados o no válidos)
- documentosCompletados - Solo documentos con estado completado (estado = 'CO')

## Notas Importantes

- Tipos de documento: REM (Remisión/venta normal), FAC (Factura), DEV (Devolución completa), DV (Devolución parcial)
- Para comparar con cortes Z, consultar analiticaCortes de forma separada y combinar manualmente por fecha/sucursal
- Ventas Netas = Ventas Brutas - Devoluciones
- Tasa de Devoluciones = (Devoluciones / Ventas Brutas) * 100

## Casos de Uso

- Identificar patrones de devoluciones por sucursal/cliente
- Calcular tasa de devoluciones
- Analizar motivos de devolución
- Detectar devoluciones anormales
- Comparar ventas brutas vs netas
- Análisis de comportamiento de devoluciones por periodo
- Identificar clientes con alta tasa de devoluciones
- Analizar impacto de devoluciones en rentabilidad

## Conceptos Relacionados

### Tipos de Documento

**REM (Remisión)**
- Venta normal sin factura
- Documento de venta estándar

**FAC (Factura)**
- Venta con factura
- Documento de venta facturado

**DEV (Devolución completa)**
- Devolución total de una venta
- El cliente devuelve todo el producto

**DV (Devolución parcial)**
- Devolución parcial de una venta
- El cliente devuelve parte del producto

### Ventas Brutas vs Netas

**Ventas Brutas**
- Suma de todas las ventas (REM + FAC)
- NO resta devoluciones
- Usar para comparar con Cortes Z

**Ventas Netas**
- Ventas brutas menos devoluciones
- Ventas Brutas - (DEV + DV)
- Representa ingresos reales después de devoluciones

### Tasa de Devoluciones

**Fórmula:**
Tasa de Devoluciones = (Importe Devoluciones / Importe Ventas) * 100

**Interpretación:**
- Tasa baja (<1%): Normal, operación saludable
- Tasa media (1-3%): Revisar casos específicos
- Tasa alta (>3%): Investigar causas (calidad, procesos, clientes)

## Estrategias de Análisis

**Análisis de Devoluciones por Sucursal**
Usar GROUP BY sucursal con MEASURE(importeDevoluciones) y MEASURE(tasaDevoluciones)

**Análisis de Devoluciones por Cliente**
Usar GROUP BY cliente con MEASURE(importeDevoluciones) y MEASURE(conteoDevoluciones)

**Análisis Temporal de Devoluciones**
Usar GROUP BY fechaVenta o usar dimensiones temporales si están disponibles

**Identificar Devoluciones Anormales**
Usar segmento devolucionesAltas o filtrar con HAVING MEASURE(importeDevoluciones) > umbral

**Comparar Ventas Brutas vs Netas**
Usar MEASURE(importeVentas) vs MEASURE(ventasNetas)

## Errores Comunes Específicos

**Error:** Tasa de devoluciones >100%
- **Causa:** Más devoluciones que ventas en el periodo
- **Solución:** Revisar filtros de fecha, puede ser normal si hay devoluciones de periodos anteriores

**Error:** Devoluciones sin ventas asociadas
- **Causa:** Devoluciones de periodos anteriores
- **Solución:** Normal, usar filtros de fecha apropiados

**Error:** Importe neto negativo
- **Causa:** Devoluciones mayores que ventas
- **Solución:** Revisar periodo, puede ser válido si hay devoluciones grandes

## Tips de Análisis

1. Usar segmento soloDevoluciones para análisis enfocados en devoluciones
2. Usar segmento conDevoluciones para identificar períodos con devoluciones
3. Comparar tasa de devoluciones entre sucursales para identificar problemas
4. Analizar promedioDevolucion vs promedioVenta para entender patrones
5. Usar documentosViables para excluir documentos cancelados o no válidos
6. Para reconciliación con cortes Z, recordar que Z NO resta devoluciones

