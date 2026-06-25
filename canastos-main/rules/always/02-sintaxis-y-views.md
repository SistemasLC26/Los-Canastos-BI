# 02 - Sintaxis Básica y Views Disponibles

## Reglas Críticas de Sintaxis

Estas son las reglas esenciales para usar views en CubeSQL. Violar estas reglas causará errores.

### NO PERMITIDO - Causará Errores

- NO usar DATE_TRUNC con dimensión fecha (tipo date) - Causará error TYPE_MISMATCH
- NO usar COUNT(*) o COUNT(columna) - Usar MEASURE(conteoTickets) en su lugar
- NO usar GROUP BY con aliases - Usar índices numéricos (1, 2, 3, etc.)
- NO usar MEASURE() en WHERE - Usar HAVING en su lugar
- NO usar funciones agregadas en dimensiones (MAX, MIN, etc.)

### PERMITIDO - Funcionará Correctamente

- Usar anio, numMes, nombreMes y diaSemana para análisis temporal (NO usar DATE_TRUNC)
- Usar fecha directamente para ver fechas específicas
- Contar tickets con MEASURE(conteoTickets)
- Filtrar con WHERE en dimensiones
- Agrupar por índices numéricos: GROUP BY 1, 2, 3
- Verificar NULLs con IS NULL / IS NOT NULL
- Usar operaciones aritméticas con MEASURE()
- Usar HAVING para filtrar por MEASURE()

## Dimensiones del Calendario

Las dimensiones temporales están disponibles en todas las views:

- `fecha` - Fecha de la transacción
- `anio` - Año (number)
- `numMes` - Número del mes 1-12 (number)
- `nombreMes` - Nombre del mes (string, ej: "November")
- `diaSemana` - Día de la semana (string, ej: "Monday")

Usar estas dimensiones en lugar de DATE_TRUNC para análisis temporal.

## Reglas Resumidas

1. Temporal: Usar anio, numMes, nombreMes y diaSemana, NO usar DATE_TRUNC
2. Conteos: Usar MEASURE(conteoTickets), NO usar COUNT(*)
3. GROUP BY: Usar índices numéricos (1, 2, 3), NO usar aliases
4. Filtrar medidas: Usar HAVING, NO usar WHERE MEASURE(...)
5. Siempre incluir: LIMIT (5000 por defecto para análisis completos, 100 para exploración)

## Reglas de Modelado de Cubos

### Regla 19: Dimensiones Temporales - Usar SQL Nativo en lugar de Joins a Calendario

**✅ CORRECTO:** Usar EXTRACT() y CASE para dimensiones temporales desde la columna de fecha

**❌ INCORRECTO:** Crear joins a una tabla `calendario` separada solo para dimensiones básicas

**Ejemplo CORRECTO:**
```yaml
- name: anio
  sql: "EXTRACT(YEAR FROM {CUBE}.partition_date)"
  type: number

- name: nombreMes
  sql: |
    CASE EXTRACT(MONTH FROM {CUBE}.partition_date)
      WHEN 1 THEN 'January'
      WHEN 2 THEN 'February'
      ...
    END
  type: string
```

**Ejemplo INCORRECTO:**
```yaml
- name: fecha
  sql: "{calendario.fecha}"  # ❌ Causa COLUMN_NOT_FOUND en vistas
```

**Razón:** Evita resolver joins innecesarios durante compilación y ejecución. Los joins a tablas dimensionales de calendario rara vez agregan valor para dimensiones básicas (año, mes, día) y pueden causar cascadas de errores cuando se usan en vistas.

**NOTA:** El cubo `calendario` se mantiene para uso futuro cuando se necesiten datos de negocio (festivos, campañas, eventos, días asuetos, etc.) que no se pueden calcular con SQL nativo.

### Regla 20: Vistas - Solo Exponer Dimensiones y Medidas, Nunca Definir Medidas Propias

- Vistas NO pueden definir sus propias medidas (limitación arquitectónica de Cube)
- Vistas deben SOLO incluir miembros (dimensiones + medidas) del cubo subyacente
- Para cálculos complejos, definirlos en el cubo usando medidas calculadas

**Estructura Correcta de Vista:**
```yaml
views:
  - name: miVista
    cubes:
      - join_path: miCubo
        includes:
          - dimension1
          - dimension2
          - measure1
          - measure2
```

**Estructura Incorrecta:**
```yaml
views:
  - name: miVista
    cubes:
      - join_path: miCubo
    measures:  # ❌ NO PERMITIDO
      - name: medidaPersonalizada
```

### Regla 21: Joins en Cubes - Justificación Requerida

- Cada join debe tener una justificación clara: agregar datos que no existen en la tabla base
- Joins que solo proporcionan cálculos derivados deben ser reemplazados por SQL nativo
- Verificar siempre si la información se puede calcular con EXTRACT(), CASE, o funciones SQL

**Caso de Uso VÁLIDO para Join:**
- Tabla base: partidas_venta (con articulo)
- Join a: catalogo_productos (para obtener marca, línea, nombre)
- Razón: Datos complementarios no existentes en tabla base

**Caso de Uso NO VÁLIDO para Join:**
- Tabla base: partidas_venta (con partition_date)
- Join a: calendario (para obtener año, mes, día semana)
- Razón: Datos calculables con EXTRACT() desde partition_date

## Patrones Básicos

### Construcción Iterativa

1. Query inicial simple → Verificar que funciona
2. Agregar 1 dimensión → Verificar
3. Agregar 1 medida → Verificar
4. Agregar filtros WHERE → Verificar
5. Agregar ORDER BY → Verificar
6. Ajustar LIMIT → Listo

### Reglas Fundamentales

- Siempre empezar simple: Una medida, una dimensión, verificar que funciona antes de agregar complejidad
- Agregar complejidad gradualmente: Añadir más dimensiones/medidas una a una
- Validar NULLs: Si hay NULLs inesperados, filtrarlos explícitamente con IS NULL / IS NOT NULL
- Excluir sucursal de prueba: Siempre incluir WHERE sucursal != 'DPBodega-Test'
- Verificar completitud: Es normal tener ~1% de casos sin clasificar (marca/línea NULL o DESCONOCIDA)

## Views Disponibles

El modelo contiene 5 views principales. Para detalles completos de cada view (schema, campos, medidas, dimensiones, casos de uso, errores específicos), consulta los archivos correspondientes en agent-requested.

### analiticaVentas
Análisis detallado de ventas con detalle de productos, clientes, rentabilidad y comportamiento. Incluye medidas de ingresos, costos, utilidad, cantidad vendida y tickets. Para más detalles: agent-requested - 06-view-analiticaVentas

### analiticaInventario
Análisis de niveles de stock y valor de inventario por producto y sucursal. IMPORTANTE: CEDIS concentra 70-80% del inventario total. Para más detalles: agent-requested - 07-view-analiticaInventario

### analiticaCortes
Análisis de diferencias entre ventas registradas y efectivo recaudado. Para más detalles: agent-requested - 08-view-analiticaCortes

### reconciliacionDiaria
Reconciliación entre ventas del sistema ERP y cortes Z del POS para detectar diferencias. CRÍTICO: Ventas Z NO restan devoluciones → Comparar con Ventas BRUTAS del sistema (no netas). Para más detalles: agent-requested - 09-view-reconciliacionDiaria

### analiticaDevoluciones
Análisis detallado de devoluciones por tipo de documento. Permite analizar comportamiento de devoluciones por sucursal, fecha y cliente. Incluye medidas de tasa de devoluciones, ventas netas y promedios. Para más detalles: agent-requested - 10-view-analiticaDevoluciones

