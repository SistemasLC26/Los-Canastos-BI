# 08 - View: analiticaCortes

## Description
Schema completo, campos, medidas, dimensiones, casos de uso, conceptos relacionados y errores específicos de analiticaCortes. Keywords: analiticaCortes, auditoriaEfectivo, cortes, cortes Z, auditoría efectivo, efectivo recaudado, diferencias efectivo, ventas sistema vs efectivo.

---

## Propósito

Analizar diferencias entre ventas registradas y efectivo recaudado.

## Schema

### Medidas

- MEASURE(ventasSistema) - Ventas registradas en el sistema
- MEASURE(ventasReporteZ) - Ventas según reporte Z
- MEASURE(efectivoRecaudado) - Efectivo realmente recaudado
- MEASURE(diferencia) - Diferencia entre sistema y efectivo

### Dimensiones

- fechaCorte (timestamp) - Fecha del corte
- anio (number) - Año de la transacción (calculado directamente en cortesDiarios)
- numMes (number) - Número del mes (1-12) (calculado directamente en cortesDiarios)
- nombreMes (string) - Nombre del mes (ej: "November") (calculado directamente en cortesDiarios)
- diaSemana (string) - Día de la semana (ej: "Monday", "Tuesday") (calculado directamente en cortesDiarios)
- sucursal - Nombre de la sucursal
- numeroCorte - Número de corte

## Casos de Uso

- Detectar diferencias entre ventas registradas y efectivo recaudado
- Analizar faltantes/sobrantes de caja por sucursal/estación
- Monitorear cortes de caja y cajeros
- Identificar patrones de diferencias por día/hora/cajero

## Conceptos Relacionados

Esta view se enfoca en diferencias entre sistema y efectivo. Para análisis más completo de reconciliación entre sistema ERP y cortes Z, consultar view-reconciliacionDiaria.

## Errores Comunes Específicos

**Error:** Diferencias grandes
- **Causa:** Ventas a crédito, retrasos sincronización
- **Solución:** Normal en algunas sucursales, revisar si >10%

**Error:** Efectivo muy cercano a ventas Z
- **Causa:** No hay ventas con tarjeta (sospechoso si tienda tiene terminal)
- **Solución:** Verificar que terminal esté funcionando

## Tips de Análisis

1. Para análisis completo de reconciliación, usar view-reconciliacionDiaria
2. Esta view es útil para auditoría específica de efectivo
3. Considerar que diferencias pueden ser normales por ventas con tarjeta/crédito

