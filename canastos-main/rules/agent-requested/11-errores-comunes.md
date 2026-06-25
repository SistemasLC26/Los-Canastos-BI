# 11 - Errores Comunes de Sintaxis

## Description
Tabla de troubleshooting para errores comunes de sintaxis en CubeSQL: errores de sintaxis (Dimension with aggregate, Can't detect Cube, Expression not resolved, TYPE_MISMATCH), y errores básicos de uso. Keywords: error cube, dimension aggregate, can't detect cube, type mismatch, expression not resolved, fecha error, GROUP BY error.

---

## Errores de Sintaxis CubeSQL

**Error:** Dimension 'fecha' was used with aggregate function
- **Causa:** Usar MAX(fecha) o MIN(fecha)
- **Solución:** Usar fecha directamente con GROUP BY

**Error:** Can't detect Cube query
- **Causa:** CASE WHEN en GROUP BY o CTEs complejas
- **Solución:** Simplificar query, usar WHERE en lugar de CASE

**Error:** Expression could not be resolved
- **Causa:** Usar aliases en GROUP BY
- **Solución:** Usar índices numéricos: GROUP BY 1, 2, 3

**Error:** Column cannot be resolved
- **Causa:** Referencia incorrecta a columna o dimensión no expuesta en el cubo fuente
- **Solución:** Verificar que la dimensión existe en el view y está incluida desde el cubo fuente correspondiente. Las dimensiones temporales (anio, numMes, nombreMes, diaSemana) están calculadas directamente en los cubos fuente (partidasVenta, ventasPorDocumento, cortesDiarios, historicoInventario, reconciliacionVentasDiarias) usando EXTRACT() y están disponibles directamente en las views.

**Error:** TYPE_MISMATCH con fecha
- **Causa:** Usar DATE_TRUNC con tipo date
- **Solución:** Usar dimensiones anio, numMes, nombreMes y diaSemana en su lugar. Estas dimensiones están calculadas directamente en los cubos fuente usando EXTRACT() y están disponibles directamente en todas las views.

**Error:** EXPRESSION_NOT_SCALAR en WHERE
- **Causa:** Usar MEASURE() en cláusula WHERE
- **Solución:** Mover condición a HAVING: HAVING MEASURE(...) < 0

## Ejemplo de Fix Común

**ERROR:**
Usar DATE_TRUNC('month', fecha) con MEASURE(ingresoTotal)

**CORRECTO:**
Usar anio, nombreMes, MEASURE(ingresoTotal) con GROUP BY 1, 2

## Checklist de Troubleshooting

Cuando algo no se ve correcto, revisar en orden:

1. Sintaxis: ¿Estoy usando anio, numMes, nombreMes y diaSemana en lugar de DATE_TRUNC?
2. GROUP BY: ¿Estoy usando índices numéricos (1, 2, 3)?
3. MEASURE() en WHERE: ¿Debería usar HAVING en su lugar?
4. Filtros: ¿Incluí WHERE sucursal != 'DPBodega-Test'?
5. LIMIT: ¿Incluí LIMIT en la query?

