# 09 - View: reconciliacionDiaria

## Description
Schema completo, campos, medidas, dimensiones, casos de uso, conceptos críticos, interpretación de métricas y errores específicos de reconciliacionDiaria. Keywords: reconciliacionDiaria, reconciliación, corte Z, diferencias sistema, ventas brutas, devoluciones, múltiples cajas, retiros efectivo, ventas crédito, sincronización, faltantes sobrantes.

---

## Propósito

Reconciliar ventas del sistema ERP con cortes Z del POS para detectar diferencias.

**CRÍTICO:** Ventas Z NO restan devoluciones → Comparar con Ventas BRUTAS del sistema (no netas)

## Schema

### Medidas del Sistema ERP

- MEASURE(ventasBrutas) - Ventas brutas sistema (REM + FAC)
- MEASURE(devoluciones) - Devoluciones sistema (DEV + DV)
- MEASURE(ventasNetas) - Ventas netas = Brutas - Devoluciones
- MEASURE(numVentas) - Número de ventas
- MEASURE(numDevoluciones) - Número de devoluciones
- MEASURE(descuentos) - Descuentos aplicados
- MEASURE(impuestos) - Impuestos
- MEASURE(costos) - Costos

### Medidas del Corte Z (POS)

- MEASURE(ventasZ) - Ventas reportadas en corte Z (suma de todas las cajas del día)
- MEASURE(efectivoCaja) - Efectivo físico en caja al cierre
- MEASURE(diferenciaZ) - Diferencia Z = Efectivo - Ventas Z
- MEASURE(totalIngresos) - Total ingresos en efectivo ANTES de retiros
- MEASURE(retirosEfectivo) - Retiros programados
- MEASURE(clientesAtendidos) - Clientes atendidos
- MEASURE(ticketPromedioZ) - Ticket promedio según Z
- MEASURE(numCortesZ) - Número de cortes Z realizados (múltiples cajas)
- MEASURE(ventasImpuesto10) - Ventas con impuesto 10%
- MEASURE(impuesto10) - Impuesto 10%
- MEASURE(ventasImpuesto15) - Ventas con impuesto 15%
- MEASURE(impuesto15) - Impuesto 15%

### Medidas Calculadas (Análisis)

- MEASURE(diferenciaSistemaVsZ) - (PRINCIPAL) (Ventas Brutas) - (Ventas Z)
- MEASURE(diferenciaEfectivoVsZ) - (Efectivo) - (Ventas Z) [Normal: -40% a -80%]
- MEASURE(impactoDevoluciones) - Para análisis separado
- MEASURE(ventasNoEfectivo) - Estimado ventas tarjeta/crédito
- MEASURE(porcentajeVentasNoEfectivo) - % ventas no efectivo (típico 40-80%)
- MEASURE(tasaDevoluciones) - % devoluciones sobre ventas brutas
- MEASURE(porcentajeDiferenciaSistemaVsZ) - % diferencia (cerca de 0% = buena sync)

### Dimensiones

- fecha (timestamp) - Fecha del día (desde reconciliacionVentasDiarias)
- anio (number) - Año de la transacción (expuesto desde reconciliacionVentasDiarias)
- numMes (number) - Número del mes (1-12) (expuesto desde reconciliacionVentasDiarias)
- nombreMes (string) - Nombre del mes (ej: "November") (expuesto desde reconciliacionVentasDiarias)
- diaSemana (string) - Día de la semana (ej: "Monday", "Tuesday") (expuesto desde reconciliacionVentasDiarias)
- sucursal - Nombre de la sucursal

### Segmentos Disponibles

- conDevoluciones - Días con devoluciones > 0
- sistemaMayorQueZ - Sistema > Z (ventas a crédito o retrasos)
- zMayorQueSistema - Z > Sistema (ventas no registradas en ERP)
- diferenciaSignificativa - Diferencia > $1,000 (requiere revisión)

## Notas Importantes

- Múltiples cajas por día SE SUMAN automáticamente (GROUP BY fecha, sucursal)
- Filtros aplicados: Excluye estación COBRANZA y DPBodega-Test
- Retiros de efectivo ($2K-$10K) son normales por seguridad (NO son faltantes)
- CEDIS puede tener diferencias grandes (ventas B2B sin POS)

## Casos de Uso

- Reconciliación diaria entre sistema ERP y POS
- Detección de diferencias significativas que requieren revisión
- Análisis de sincronización entre sistemas
- Análisis de efectivo vs tarjetas
- Validación de múltiples cajas por día
- Análisis de devoluciones

## Conceptos Críticos

### CONCEPTO CRÍTICO: Ventas Brutas vs Netas

**El Problema**
Ventas Z NO restan devoluciones → El reporte Z muestra ventas totales del día SIN restar productos devueltos.

**La Solución**
Siempre comparar Ventas BRUTAS (no netas) con Ventas Z

```
Ventas Brutas (Sistema) = REM + FAC (documentos de venta)
Devoluciones (Sistema) = DEV + DV (documentos de devolución)
Ventas Netas (Sistema) = Ventas Brutas - Devoluciones

Ventas Z (POS) = Total ventas del día SIN restar devoluciones

Comparación correcta: Ventas BRUTAS vs Ventas Z
Comparación incorrecta: Ventas NETAS vs Ventas Z
```

### Múltiples Cajas por Día

**Cómo Funciona**
- Una sucursal puede tener 2-3 cortes Z por día (diferentes cajas o turnos)
- El modelo SUMA automáticamente todos los cortes del día
- Agregación: GROUP BY fecha, sucursal
- Campo numCortesZ indica cuántos cortes hubo

**Ejemplo Real: LOMAS - 12 Nov 2025**
- 3 cortes Z (3 cajas operando)
- Ventas Z sumadas: $24,629
- Esto es NORMAL y esperado

### Retiros de Efectivo (NO son faltantes)

**Qué Son**
Dinero retirado de caja por seguridad durante el día.

**Montos Típicos**
- $2,000 a $10,000 por día
- Montos redondos: $2K, $5K, $8K, $10K
- Ejemplo: REX promedio $6,000/día de retiros

**IMPORTANTE**
Retiros ALTOS son normales → NO son faltantes → Es política de seguridad

### Interpretación de Diferencias

**1. Diferencia Sistema vs Z (PRINCIPAL)**

**Fórmula:** (Ventas Brutas Sistema) - (Ventas Z)

**Interpretación:**
- Positiva (+): Sistema > Z
  - Posibles ventas a crédito no capturadas en POS
  - Retrasos en sincronización
  - Normal: 0% a +10%

- Negativa (-): Z > Sistema
  - Posibles ventas no registradas en ERP
  - Timing de captura (ventas tarde en la noche)
  - Normal: 0% a -10%

- Cerca de 0%: Buena sincronización

**Ejemplo LOMAS típico:** -4% a -6% (normal)

**2. Diferencia Efectivo vs Z**

**Fórmula:** (Efectivo Caja) - (Ventas Z)

**Interpretación:**
- Negativa (-40% a -80%): NORMAL
  - Indica ventas con tarjeta/crédito
  - Ejemplo: Si Ventas Z = $10,000 y Efectivo = $3,000 → -70% normal

- Cerca de 0%: Solo efectivo
  - Revisar si tienda tiene terminal de tarjeta
  - Puede ser sospechoso si terminal está funcionando

- Positiva (+): Sobrante en caja
  - REVISAR - Error de captura o ingreso no registrado

### Filtros Automáticos Aplicados

**Estación COBRANZA (Excluida)**
- Qué es: Terminal para depósitos/transferencias
- NO es caja de ventas: No genera cortes Z
- Filtro aplicado: Automáticamente excluida del view

**DPBodega-Test (Excluida)**
- Sucursal de pruebas
- Excluida de análisis de producción

**Solo Cortes Tipo 'Z'**
- Cortes X NO existen en base de datos (validado)
- Solo se capturan cortes Z (cierre de día)

### Caso Especial: CEDIS

CEDIS puede tener diferencias grandes (normales):
- Ventas B2B sin POS
- Ventas mayoristas registradas en sistema pero no en terminal
- Operación diferente a tiendas retail

**Acción:** Analizar CEDIS por separado, no aplicar mismos criterios que tiendas.

## Estrategias de Query

**Resumen por Sucursal (Mes Completo)**
Usar reconciliacionDiaria con GROUP BY sucursal, filtrar por rango de fechas del mes.

**Solo Diferencias Significativas (>$1,000)**
Usar HAVING MEASURE(diferenciaSistemaVsZ) > 1000 OR MEASURE(diferenciaSistemaVsZ) < -1000

**Análisis de Efectivo vs Tarjetas**
Usar medidas: ventasZ, totalIngresos, ventasNoEfectivo, porcentajeVentasNoEfectivo

**Validación de Múltiples Cajas**
Usar HAVING MEASURE(numCortesZ) > 1 para ver días con múltiples cajas

## Métricas de Calidad

| Indicador | Valor Actual | Estado |
|-----------|--------------|--------|
| Cortes Z existentes | Solo tipo 'Z' | Sin cortes X (validado) |
| Filtro COBRANZA | Aplicado | Estación excluida correctamente |
| Múltiples cajas manejadas | Suma automática | GROUP BY fecha + sucursal |
| Devoluciones capturadas | 3 docs DEV Nov 2025 | Se registran por separado |
| Comparación correcta | Ventas BRUTAS vs Z | Z no resta devoluciones |
| Retiros identificados | $2K-$10K típico | No confundidos con faltantes |
| Diferencia típica LOMAS | -4% a -6% | Normal (sincronización, crédito) |
| % Ventas tarjeta promedio | 40-80% | Normal en tiendas con terminal |

## Errores Comunes Específicos

**Error:** Diferencia grande Sistema vs Z
- **Causa:** Ventas a crédito, retrasos sincronización, ventas B2B (CEDIS)
- **Solución:** Normal en CEDIS; revisar sucursales con >10% diferencia

**Error:** Efectivo muy cercano a ventas Z
- **Causa:** No hay ventas con tarjeta (sospechoso si tienda tiene terminal)
- **Solución:** Verificar que terminal esté funcionando

**Error:** Múltiples cortes Z mismo día
- **Causa:** Varias cajas/turnos en la sucursal
- **Solución:** Normal si numCortesZ = 2-3; revisar si >5

**Error:** Devoluciones no aparecen
- **Causa:** No hay devoluciones ese día/periodo
- **Solución:** Validar con HAVING MEASURE(numDevoluciones) > 0

**Error:** Retiros muy altos
- **Causa:** Retiros de seguridad programados
- **Solución:** Normal $2K-$10K; no es faltante

**Error:** Sistema > Z constantemente
- **Causa:** Ventas a crédito no registradas en POS
- **Solución:** Revisar procesos de captura crédito

**Error:** Z > Sistema constantemente
- **Causa:** Ventas no registradas en ERP o timing
- **Solución:** Revisar sincronización y proceso de cierre

## Tips de Análisis

1. Siempre revisar numCortesZ - Contexto de múltiples cajas
2. Retiros NO son faltantes - Montos $2K-$10K normales
3. Diferencias <10% normales - Considerar timing y crédito
4. CEDIS es caso especial - Analizar por separado
5. Efectivo -40% a -80% normal - Indica ventas con tarjeta
6. Usar segmentos predefinidos - diferenciaSignificativa para casos que requieren revisión
7. Comparar Ventas BRUTAS vs Z (no ventas netas)

