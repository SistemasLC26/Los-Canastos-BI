# Documentación del Modelo de Datos — Canastos TFX

> **Última actualización:** 2026-04
> **Motor de datos:** Trino / Parquet sobre `canastos_tfx`
> **Framework:** Cube.js

---

## Índice

- [Resumen del Modelo](#resumen-del-modelo)
- [Diagrama de Relaciones](#diagrama-de-relaciones)
- [Cubos](#cubos)
  - [cortesDiarios](#cubo-cortesdiarios)
  - [ventas](#cubo-ventas)
  - [reconciliacionCortesZ](#cubo-reconciliacioncortesz)
  - [reconciliacionVentasDiarias](#cubo-reconciliacionventasdiarias)
  - [ventasPorDocumento](#cubo-ventaspordocumento)
  - [historicoInventario](#cubo-historicoinventario)
  - [productosAlfaClasificados](#cubo-productosalfaclasificados)
  - [clientes](#cubo-clientes)
  - [catalogoProductos](#cubo-catalogoproductos)
  - [calendario](#cubo-calendario)
- [Vistas](#vistas)
  - [ventasTipoPago](#vista-ventastipopago)
  - [auditoriaEfectivo](#vista-auditoriaefectivo)
  - [reconciliacionDiaria](#vista-reconciliaciondiaria)
  - [analiticaDevoluciones](#vista-analiticadevoluciones)
  - [estadoInventario](#vista-estadoinventario)
- [Tipos de Documento](#tipos-de-documento)
- [Glosario de Sucursales Excluidas](#glosario-de-sucursales-excluidas)
- [Historial de Cambios](#historial-de-cambios)

---

## Resumen del Modelo

El modelo está organizado en dos grandes dominios:

| Dominio | Cubos involucrados | Propósito |
|---|---|---|
| **Ventas / POS** | `cortesDiarios`, `ventas`, `reconciliacionCortesZ`, `reconciliacionVentasDiarias`, `ventasPorDocumento` | Registro y análisis de transacciones de venta, cortes de caja y reconciliación ERP vs POS |
| **Inventario / Catálogo** | `historicoInventario`, `catalogoProductos`, `productosAlfaClasificados` | Stock histórico por ubicación y clasificación de productos |
| **Auxiliares** | `clientes`, `calendario` | Dimensiones de apoyo para joins y filtros |

---

## Diagrama de Relaciones

```
ventas ──────────────── many_to_one ──► clientes
  │                                    (cliente + sucursal)
  │
  └── (vistas consumen)
        ↓
  ventasPorDocumento          (análisis por folio)
  reconciliacionVentasDiarias (agregado día + sucursal)

reconciliacionVentasDiarias ── one_to_one ── reconciliacionCortesZ
                                              (fecha + sucursal)

cortesDiarios  ──────────────── (autónomo, sin joins)
historicoInventario ──────────── (autónomo, enriquecido con partvta)
catalogoProductos ───────────── (lookup de SKUs numéricos)
productosAlfaClasificados ────── (lookup de SKUs alfanuméricos)
calendario ──────────────────── (dimensión de tiempo auxiliar)
```

---

## Cubos

---

### Cubo: `cortesDiarios`

**Título:** Cortes de Caja
**Tabla fuente:** `canastos_tfx.tfx_table_cortes`
**Público:** No
**Joins:** Ninguno

#### Descripción

Registra los **cortes de caja tipo X** (parcial) y **Z** (cierre de día) a nivel de registro individual por estación. Incluye ventas reportadas, efectivo físico contado, ingresos totales, impuestos desglosados y clientes atendidos por caja.

> ⚠️ **FIX 2026-04:** Se eliminó el workaround de fecha (`< 2025-11-20`). Se usa `TRY_CAST` en todos los campos numéricos para tolerar schema drift en Parquet. Se excluye `DPBodega-Test` en el `WHERE`.

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Corte | string | **PK.** Campo `cort_id` |
| `numeroCorte` | Número de Corte | string | Consecutivo del corte dentro de la estación |
| `fechaCorte` | Fecha de Corte | string | `partition_date` casteado a `VARCHAR` |
| `anio` | Año | number | Año extraído de `partition_date` |
| `numMes` | Mes (Num) | number | Mes numérico (1–12) |
| `nombreMes` | Mes | string | Nombre del mes en español |
| `diaSemana` | Día Semana | string | Nombre del día; `DOW 0 = Domingo` (Trino/PostgreSQL) |
| `sucursal` | Sucursal | string | Nombre de la sucursal |
| `estacion` | Estación/Caja | string | Caja individual dentro de la sucursal |
| `tipoCorte` | Tipo de Corte | string | `z` = cierre de día / `x` = corte parcial |
| `horaCorte` | Hora del Corte | string | Hora en que el cajero ejecutó el corte |
| `fechaRegistro` | Fecha de Registro | string | Fecha del sistema; puede diferir de `partition_date` |

#### Medidas

| Nombre | Título | Tipo | Formato | Descripción |
|---|---|---|---|---|
| `ventasReportadasZ` | Ventas Reportadas (Z) | sum | currency | Total vendido según el sistema en el corte |
| `efectivoCaja` | Efectivo en Caja | sum | currency | Dinero físico contado por el cajero |
| `totalIngresos` | Total Ingresos | sum | currency | Suma de todas las formas de pago |
| `ventasConImpuesto10` | Ventas Base 16% | sum | currency | Base gravable al 16% de IVA |
| `impuesto10` | IVA 16% | sum | currency | Monto de IVA al 16% |
| `ventasConImpuesto15` | Ventas Exentas (0%) | sum | currency | Ventas exentas de IVA |
| `impuesto15` | IVA 0% | sum | currency | Siempre cero; conservado por consistencia de esquema |
| `ventas8` | Ventas Base 8% (IEPS) | number | currency | `(totalventas - impuesto15 - impuesto10 - ventasimpuesto10 - ventasimpuesto15) / 1.08` |
| `impuesto8` | IEPS 8% | number | currency | `ventas8 × 0.08` |
| `ventasNoEfectivo` | Ventas No Efectivo | sum | currency | `totalventas - totalcaja` (tarjeta/crédito) |
| `clientesAtendidos` | # Clientes Atendidos | sum | — | Suma de `clientes_int` |
| `ticketPromedioZ` | Ticket Promedio (Z) | avg | currency | `totalventas / NULLIF(clientes_int, 0)` |
| `conteoCortes` | # Cortes Realizados | count | — | Número de registros; útil para auditoría |

#### Segmentos

| Nombre | Título | Condición | Notas |
|---|---|---|---|
| `cortesZ` | Solo Cortes Z | `corte = 'z'` | Cierres de día; usar en reportes diarios consolidados |
| `cortesX` | Solo Cortes X | `corte = 'x'` | Cortes parciales intradía |
| `sinCobranza` | Sin Estación Cobranza | `estacion != 'COBRANZA'` | COBRANZA registra pagos de crédito, no ventas de mostrador |

---

### Cubo: `ventas`

**Título:** Ventas (Cabecero)
**Tabla fuente:** `canastos_tfx.tfx_table_ventas`
**Público:** Sí
**Joins:** `clientes`

#### Descripción

Representa el **cabecero de cada transacción de venta**: folio, cliente, tipo de documento, monto total y estado. No incluye el detalle artículo por artículo (eso corresponde a `partidasVenta`).

> ⚠️ **Deduplicación activa:** La tabla origen puede contener el mismo `folio+sucursal` con múltiples tipos de documento (ej: un pedido que se convirtió en factura aparece como `PE` y como `FAC`). Se aplica `ROW_NUMBER()` por `folio+sucursal` conservando solo el documento de mayor prioridad.

**Prioridad de deduplicación:**

| Prioridad | Tipo | Significado |
|---|---|---|
| 1 | `FAC` | Factura (documento final) |
| 2 | `TIC` | Ticket |
| 3 | `PE` | Pedido |
| 4 | `REM` | Remisión |
| 5 | otros | Cualquier otro tipo |

#### Joins

| Cube relacionado | Tipo | Condición |
|---|---|---|
| `clientes` | many_to_one | `ventas.cliente = clientes.codigoCliente AND ventas.sucursal = clientes.sucursal` |

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Venta Único | string | **PK.** Concatenación `folio + sucursal + tipo_doc` |
| `numeroVenta` | Folio | string | Número de folio del documento |
| `cliente` | Código Cliente | string | Puede ser `sys`/`SYS` en ventas de mostrador sin cliente |
| `sucursal` | Sucursal | string | Clave de la sucursal donde se generó el documento |
| `tipoDocumento` | Tipo de Documento | string | Ver [Tipos de Documento](#tipos-de-documento) |
| `fechaTransaccion` | Fecha Venta | time | `partition_date` |
| `anio` | Año | number | Año de la transacción |
| `numMes` | Mes (Num) | number | Mes numérico (1–12) |
| `nombreMes` | Mes | string | Nombre del mes en español |
| `observacion` | Observación | string | Texto libre; detecta agrupaciones como `TICKETS ANEXOS` |
| `estado` | Estado de Venta | string | `PE` = pendiente (no confirmado) |

#### Medidas

| Nombre | Título | Tipo | Formato | Descripción |
|---|---|---|---|---|
| `montoTotal` | Monto Bruto Cabecero | sum | currency | ⚠️ Incluye todos los tipos; puede duplicar montos. Solo para diagnóstico |
| `montoSinDuplicar` | Monto Sin Duplicar | sum | currency | Solo `FAC`, `REM`, `DV`, `DEV`. Alineado con reporte contable *(FIX 2025-04)* |
| `impuestoSinDuplicar` | Impuesto Total Sin Duplicar | sum | currency | Impuesto filtrado igual que `montoSinDuplicar` *(FIX 2025-04)* |
| `totalImpuesto` | Impuesto Total (Bruto) | sum | currency | ⚠️ Misma advertencia que `montoTotal`. Preferir `impuestoSinDuplicar` |
| `clientesUnicos` | Clientes Únicos (Registrados) | count_distinct | — | Excluye `sys`/`SYS`. Solo con `is_viable = true` |

#### Segmentos

| Nombre | Título | Condición | Notas |
|---|---|---|---|
| `ventasValidas` | Solo Ventas Viables | `is_viable = true` | Excluye cancelados y registros de prueba |
| `sinDuplicacionPedidos` | Sin Duplicar Pedidos | `tipo_doc IN ('FAC','REM','TIC','NC','DV','PE','DEV')` | Excluye documentos intermedios |
| `ventasReales` | Ventas Reales (Filtros Aplicados) | `is_viable = true` + sin `TICKETS ANEXOS` + sin cliente `sys` con `FAC` + `estado <> 'PE'` | Segmento más estricto para análisis al mayoreo |

---

### Cubo: `reconciliacionCortesZ`

**Título:** Cortes Z Diarios (Reconciliación)
**Tabla fuente:** `canastos_tfx.tfx_table_cortes`
**Público:** No
**Joins:** `reconciliacionVentasDiarias`

#### Descripción

Cortes Z **pre-agregados por día y sucursal** para reconciliación contra el ERP. A diferencia de `cortesDiarios` (un registro por corte individual), este cubo produce **una sola fila por fecha+sucursal**, facilitando el join directo con `reconciliacionVentasDiarias`.

> ⚠️ **FIX 2026-04:** Se reemplazó el workaround de fecha por `TRY_CAST` + exclusión explícita de `TORREON ARCOIRIS`. Ahora incluye datos desde 2025-11-20 en adelante.

**Filtros aplicados en la fuente:**

- `corte = 'z'` — solo cierres de día
- `sucursal != 'DPBodega-Test'` — excluir pruebas
- `sucursal != 'TORREON ARCOIRIS'` — excluir schema drift
- `estacion != 'COBRANZA'` — excluir pagos de crédito

#### Joins

| Cube relacionado | Tipo | Condición |
|---|---|---|
| `reconciliacionVentasDiarias` | one_to_one | `fecha + sucursal` |

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Agregado | string | **PK.** `CAST(fecha AS VARCHAR) \|\| '-' \|\| sucursal` |
| `fecha` | Fecha | time | `partition_date` del archivo Parquet |
| `sucursal` | Sucursal | string | Nombre de la sucursal |

#### Medidas

| Nombre | Título | Tipo | Formato | Descripción |
|---|---|---|---|---|
| `ventasZ` | Ventas Reportadas (Z) | sum | currency | Total vendido según cortes Z del día |
| `efectivoCaja` | Efectivo en Caja | sum | currency | Efectivo físico contado en todas las cajas |
| `diferenciaZ` | Diferencia Z (Efectivo - Ventas) | sum | currency | Faltante (-) o sobrante (+) del día |
| `totalIngresos` | Total Ingresos | sum | currency | Suma de todas las formas de pago |
| `retirosEfectivo` | Retiros de Efectivo | sum | currency | `totalIngresos - efectivoCaja` |
| `ventasImpuesto10` | Ventas Base 16% | sum | currency | Base gravable al 16% |
| `impuesto10` | IVA 16% | sum | currency | Monto IVA 16% |
| `ventasImpuesto15` | Ventas Exentas (0%) | sum | currency | Ventas exentas de IVA |
| `impuesto15` | IVA 0% | sum | currency | Siempre cero |
| `ventas8` | Ventas Base 8% (IEPS) | sum | currency | Base IEPS calculada por diferencia |
| `impuesto8` | IEPS 8% | sum | currency | `ventas8 × 0.08` |
| `totalImpuestosDesglosados` | Total Impuestos (0%+8%+16%) | sum | currency | Suma de los tres impuestos para validación |
| `clientesAtendidos` | # Clientes Atendidos | sum | — | Total de clientes del día |
| `numCortesZ` | # Cortes Z | sum | — | Cajas que cerraron ese día; detecta cajas sin corte |
| `ticketPromedioZ` | Ticket Promedio (Z) | avg | currency | `ventas_z / NULLIF(clientes_atendidos, 0)` |

---

### Cubo: `reconciliacionVentasDiarias`

**Título:** Ventas Diarias Sistema (Reconciliación)
**Tabla fuente:** `canastos_tfx.tfx_table_ventas`
**Público:** No
**Joins:** Ninguno

#### Descripción

Ventas del ERP **pre-agregadas por día y sucursal**. Es el "lado sistema" de la reconciliación contra los cortes Z del POS.

> ⚠️ **Uso restringido:** Este cubo NO debe usarse para análisis general de ventas. Usar `analiticaVentas` o `analiticaDevoluciones` para ese propósito.

**Filtros aplicados en la fuente:**

- `is_viable = true` — solo documentos válidos
- `estado = 'CO'` — solo completados
- `sucursal != 'DPBodega-Test'` — excluir pruebas

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Agregado | string | **PK.** `CAST(fecha AS VARCHAR) \|\| '-' \|\| sucursal` |
| `fecha` | Fecha | time | `partition_date` de la tabla origen |
| `anio` | Año | number | Año de la fecha |
| `numMes` | Mes (Num) | number | Mes numérico (1–12) |
| `nombreMes` | Mes | string | Nombre del mes |
| `diaSemana` | Día Semana | string | Nombre del día de la semana |
| `sucursal` | Sucursal | string | Sucursal de la venta |

#### Medidas

| Nombre | Título | Tipo | Formato | Descripción |
|---|---|---|---|---|
| `ventasBrutas` | Ventas Brutas Sistema | sum | currency | Suma `REM + FAC` completados y viables |
| `devoluciones` | Devoluciones Sistema | sum | currency | Suma `DEV + DV` completados y viables |
| `ventasNetas` | Ventas Netas Sistema | sum | currency | `ventasBrutas - devoluciones` |
| `numVentas` | # Ventas | sum | — | Número de documentos de venta |
| `numDevoluciones` | # Devoluciones | sum | — | Número de documentos de devolución |
| `descuentos` | Descuentos | sum | currency | Descuentos aplicados en ventas |
| `impuestos` | Impuestos | sum | currency | Impuestos registrados |
| `costos` | Costos | sum | currency | Costo de los artículos vendidos |

---

### Cubo: `ventasPorDocumento`

**Título:** Ventas por Tipo de Documento
**Tabla fuente:** `canastos_tfx.tfx_table_ventas`
**Público:** No
**Joins:** Ninguno

#### Descripción

Detalle de ventas a **nivel de documento individual** (folio). A diferencia de `reconciliacionVentasDiarias`, no pre-agrega: expone cada folio por separado para análisis de devoluciones, facturación y comportamiento por cliente o vendedor.

> ⚠️ Todas las medidas aplican `is_viable = true` internamente. Los registros no viables contribuyen con `0` (no se omiten).

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Venta | string | **PK.** `venta \|\| '-' \|\| sucursal` |
| `numeroVenta` | Número de Venta | string | Folio del documento |
| `fechaVenta` | Fecha de Venta | time | `partition_date` |
| `anio` | Año | number | — |
| `numMes` | Mes (Num) | number | — |
| `nombreMes` | Mes | string | — |
| `diaSemana` | Día Semana | string | — |
| `sucursal` | Sucursal | string | — |
| `tipoDocumento` | Tipo de Documento | string | Ver [Tipos de Documento](#tipos-de-documento) |
| `estado` | Estado | string | `CO` = Completado, `CA` = Cancelado |
| `cliente` | Cliente | string | Puede ser `sys`/`SYS` en mostrador |
| `serieDocumento` | Serie del Documento | string | Serie del comprobante fiscal |
| `observaciones` | Observaciones | string | Texto libre; puede contener motivo de devolución |
| `vendedor` | Vendedor | string | Vendedor asociado al documento |
| `esViable` | Es Viable | boolean | `true` si el documento es válido para análisis |

#### Medidas

| Nombre | Título | Tipo | Formato | Descripción |
|---|---|---|---|---|
| `importeTotal` | Importe Total | sum | currency | Todos los documentos viables (ventas + devoluciones) |
| `importeVentas` | Importe Ventas | sum | currency | Solo `REM` y `FAC` viables |
| `importeDevoluciones` | Importe Devoluciones | sum | currency | Solo `DEV` y `DV` viables |
| `importeNeto` | Importe Neto | sum | currency | `REM/FAC` suman, `DEV/DV` restan |
| `descuentoTotal` | Descuentos | sum | currency | Descuentos sobre viables |
| `impuestoTotal` | Impuestos | sum | currency | Impuestos sobre viables |
| `precioTotal` | Precio Total | sum | currency | Precio antes de descuentos |
| `costoTotal` | Costo Total | sum | currency | Costo de los artículos |
| `conteoDocumentos` | # Documentos | sum | — | Total documentos viables |
| `conteoVentas` | # Ventas | sum | — | Solo `REM` y `FAC` viables |
| `conteoDevoluciones` | # Devoluciones | sum | — | Solo `DEV` y `DV` viables |
| `porcentajeDevoluciones` | % Devoluciones | number | percent | `importeDevoluciones / NULLIF(importeVentas, 0) * 100` |

#### Segmentos

| Nombre | Título | Condición |
|---|---|---|
| `soloVentas` | Solo Ventas (REM y FAC) | `tipo_doc IN ('REM', 'FAC')` |
| `soloDevoluciones` | Solo Devoluciones (DEV y DV) | `tipo_doc IN ('DEV', 'DV')` |
| `documentosViables` | Solo Documentos Viables | `is_viable = true` |
| `documentosCompletados` | Solo Completados | `estado = 'CO'` |

---

### Cubo: `historicoInventario`

**Título:** Historico de Inventario
**Tabla fuente:** `canastos_tfx.tfx_table_inv` + `tfx_table_partvta` (LEFT JOIN)
**Público:** No especificado
**Joins:** Ninguno

#### Descripción

Snapshots históricos de inventario por artículo, sucursal y fecha de partición. Cada registro es la existencia de un SKU en una ubicación en un día específico.

**Enriquecimiento con precio y costo:**
La tabla de inventario no tiene precio ni costo propios. Se hace un `LEFT JOIN` con `tfx_table_partvta` para traer `precio_lista` y `costo_ajustado`. El costo se sanea: si es ≤0 o mayor al precio, se estima como el **80% del precio de lista**.

> ⚠️ **Advertencia CEDIS:** El CEDIS concentra el 70-80% del stock total. Sin filtrar, los totales están dominados por la bodega. Usar el segmento `soloTiendas` para análisis por punto de venta.

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Historico | string | **PK.** `articulo \|\| '-' \|\| sucursal \|\| '-' \|\| partition_date` |
| `sku` | SKU | string | `CAST(articulo AS VARCHAR)` |
| `sucursal` | Sucursal | string | Sucursal o bodega del snapshot |
| `marca` | Marca | string | Marca del producto |
| `linea` | Línea | string | Línea/categoría del producto |
| `producto` | Producto | string | Nombre descriptivo del artículo |
| `fechaCaptura` | Fecha Corte Inventario | time | `partition_date` |
| `anio` | Año | number | — |
| `numMes` | Mes (Num) | number | — |
| `nombreMes` | Mes | string | — |
| `diaSemana` | Día Semana | string | DOW 0 = Sunday (Trino/PostgreSQL) |
| `unidadMedida` | Unidad de Medida | string | KG, PZ, LT, etc. |
| `tipoUbicacion` | Tipo de Ubicación | string | `CEDIS`, `MAYOREO`, `MENUDEO`, o `TIENDA` |

#### Medidas

| Nombre | Título | Tipo | Formato | Descripción |
|---|---|---|---|---|
| `cantidadStock` | Unidades en Stock | sum | — | ⚠️ Incluye CEDIS por defecto; aplicar `soloTiendas` para canal |
| `stockPromedio` | Stock Promedio por Ubicación | avg | — | Promedio en el período seleccionado |
| `numUbicaciones` | # Ubicaciones | count_distinct | — | Sucursales distintas donde hay registro del SKU |
| `stockMinimo` | Stock Mínimo | min | — | Mínimo del período; detecta quiebres |
| `stockMaximo` | Stock Máximo | max | — | Máximo del período; detecta sobrestock |
| `precioConImpuesto` | Precio (con Impuesto) | max | currency | `precio_lista × 1.16` (IVA 16%) |
| `costoUnitario` | Costo Unitario | max | currency | Costo saneado; fallback al 80% del precio si inválido |

#### Segmentos

| Nombre | Título | Condición | Notas |
|---|---|---|---|
| `soloTiendas` | Solo Tiendas | `sucursal != 'CEDIS' AND NOT LIKE '%MAYOREO%' AND NOT LIKE '%MENUDEO%'` | Excluye bodega central y canales de distribución |
| `soloCEDIS` | Solo CEDIS | `sucursal = 'CEDIS'` | Solo bodega central |
| `inventarioPositivo` | Solo Inventario Positivo | `existencia > 0` | Disponibilidad real de producto |
| `inventarioNegativo` | Solo Inventario Negativo | `existencia < 0` | Faltantes o errores de captura |

---

### Cubo: `productosAlfaClasificados`

**Título:** Clasificación Híbrida de Productos Alfanuméricos
**Tabla fuente:** `canastos_tfx.tfx_table_partvta`
**Público:** No

#### Descripción

Clasifica los **~106 productos con SKU alfanumérico** que no pueden unirse al catálogo numérico. Usa una estrategia híbrida de dos capas:

| Capa | Productos | Método |
|---|---|---|
| **Mapeo directo** | 23 productos | Marca y línea asignadas manualmente (match conocido en inventario) |
| **Parsing automático** | 83 productos | Marca y línea extraídas del campo `observ` con `UPPER(observ) LIKE '%keyword%'` |
| **Fallback** | Resto | `PRODUCTOS LOCALES` / `SIN CLASIFICAR` |

**Filtros de la fuente:**
- `TRY_CAST(articulo AS BIGINT) IS NULL` — solo alfanuméricos
- `articulo NOT LIKE 'SYS%'` — excluir artículos internos
- `observ IS NOT NULL AND observ != ''` — requiere descripción para el parsing

#### Dimensiones

| Nombre | Título | Tipo | Público |
|---|---|---|---|
| `sku` | SKU Alfanumérico | string (**PK**) | Sí |
| `descripcion` | Descripción | string | Sí |
| `marca` | Marca | string | Sí |
| `linea` | Línea | string | Sí |

#### Líneas inferidas por parsing automático

| Línea | Keywords detectados |
|---|---|
| `GALLETAS` | GALLETA, ALFAJOR |
| `CHOCOLATES` | CHOCOLATE |
| `BOTANAS` | PRETZEL, CHURRO, CHICHARRON, MAIZ INFLADO, KONCHITA, FRITURA, CHIPS (sin CAMOTE/JICAMA) |
| `VEGETALES PROCESADOS` | JICAMA, CAMOTE, BETABEL, ZANAHORIA, PLATANO+SAN LUIS |
| `DULCES` | GOMA, GOMITA, PALETA, PALANQUETA, DULCE, COCADA, GLORIAS, MAZAPAN, CHAMOY, CHICLE, ATE |
| `AMARANTO` | ALEGRIA |
| `CEREALES` | GRANOLA |
| `SEMILLAS Y FRUTOS SECOS` | CACAHUATE, NUEZ, PEPITA, PISTACHE, SOYA (sin CHICHARRON) |
| `BEBIDAS` | CONCENTRADO, PONCHE, TISANA, TE, AGUA, COCA, BOLSITA+MI CASITA |
| `MIELES Y ENDULZANTES` | MIEL |
| `CONDIMENTOS` | CHILE (sin CHICLE) |
| `SUPLEMENTOS` | MICRODOSIS |
| `CAFES Y TES` | CAFE |
| `ENVASES Y EMPAQUES` | BOLSA, FRASCO, TARRO, BOLSA BIODEGRADABLE |
| `SERVICIOS` | COSTO ENVIO, FLETE |

---

### Cubo: `clientes`

**Título:** Clientes
**Tabla fuente:** `canastos_tfx.tfx_table_clients`
**Público:** Sí

#### Descripción

Catálogo de clientes registrados en el sistema. La **PK es compuesta** (`cliente + sucursal`) porque un mismo cliente puede estar registrado en más de una sucursal con datos distintos.

> Es el cubo hijo del join en `ventas` (many_to_one).

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Sistema | string | **PK.** `cliente \|\| '-' \|\| sucursal` |
| `codigoCliente` | Código Cliente | string | Campo usado para el join con `ventas` |
| `nombreCliente` | Nombre | string | Nombre o razón social (público) |
| `sucursal` | Sucursal | string | Sucursal donde está registrado el cliente |

#### Medidas

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `conteo` | Total Clientes | count | Conteo de registros; tamaño de cartera por sucursal |

---

### Cubo: `catalogoProductos`

**Título:** Catálogo de Productos
**Tabla fuente:** `canastos_tfx.tfx_table_inv`
**Público:** Sí

#### Descripción

Catálogo de productos con **SKU numérico únicamente**. Los SKUs alfanuméricos están cubiertos por `productosAlfaClasificados`. El SKU se expone en dos formatos para facilitar joins con tablas que lo almacenen como texto o como entero.

**Filtro:** `TRY_CAST(articulo AS BIGINT) IS NOT NULL`
**Granularidad:** Un registro por SKU a nivel empresa (GROUP BY artículo; colapsa múltiples filas por sucursal).

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `id` | ID Producto | string | **PK.** `sku_str` |
| `sku` | SKU (String) | string | VARCHAR; para joins con tablas de texto |
| `skuInt` | SKU (Numérico) | number | BIGINT; para joins con tablas numéricas |
| `descripcion` | Descripción | string | Nombre del producto |
| `linea` | Línea | string | Línea/categoría |
| `marca` | Marca | string | Marca del producto |

---

### Cubo: `calendario`

**Título:** Calendario
**Tabla fuente:** `canastos_tfx.calendar_table`
**Público:** Sí

#### Descripción

Tabla de calendario auxiliar precalculada. Sirve como dimensión de tiempo confiable para joins y filtros, evitando recalcular `EXTRACT` y `CASE` en cada cubo.

**Ventajas sobre calcular fechas en cada cubo:**
- Consistencia garantizada entre todos los cubos
- Mejor rendimiento (valores precalculados, no funciones en tiempo de consulta)
- Facilita filtros de rango en el playground

#### Dimensiones

| Nombre | Título | Tipo | Descripción |
|---|---|---|---|
| `fecha` | Fecha | time (**PK**) | `cal_date`; habilita filtros de rango nativos |
| `anio` | Año | number | Precalculado |
| `numMes` | Mes (Num) | number | Precalculado (1–12) |
| `nombreMes` | Mes | string | Precalculado en idioma del sistema |
| `diaSemana` | Día Semana | string | Precalculado; verificar convención DOW vs otros cubos |

---

## Vistas

---

### Vista: `ventasTipoPago`

**Título:** 4. Ventas por Tipo de Pago
**Público:** Sí
**Cubo base:** `cortesDiarios`

#### Descripción

Desglose de ventas por tipo de pago usando cortes Z. La lógica de separación es:

```
Efectivo    = efectivoCaja          (totalcaja)
Tarjeta/Otros = ventasNoEfectivo   (totalventas - totalcaja)
```

> ⚠️ Recomendado usar junto con el segmento `cortesZ` para evitar mezclar cortes parciales.

#### Campos incluidos

| Campo | Tipo |
|---|---|
| `fechaCorte`, `anio`, `numMes`, `nombreMes`, `diaSemana` | Dimensiones de tiempo |
| `sucursal`, `estacion`, `tipoCorte` | Dimensiones operativas |
| `ventasReportadasZ`, `efectivoCaja`, `ventasNoEfectivo` | Medidas de tipo de pago |
| `conteoCortes` | Medida operativa |

---

### Vista: `auditoriaEfectivo`

**Título:** 3. Auditoría de Efectivo
**Público:** Sí
**Cubo base:** `cortesDiarios`

#### Descripción

Control de efectivo a nivel de **corte individual**. Permite identificar exactamente qué caja, en qué hora y en qué día presentó un faltante o sobrante.

> ⚠️ **FIX 2026-04:** Datos completos con `TRY_CAST`. Se agregaron medidas de tasa 8% (IEPS).

#### Medidas propias

| Nombre | Fórmula | Descripción |
|---|---|---|
| `diferencia` | `efectivoCaja - ventasReportadasZ` | **Positivo** = sobrante / **Negativo** = faltante / **Cero** = cuadre perfecto |
| `porcentajeDiferencia` | `diferencia / NULLIF(ventasReportadasZ, 0) * 100` | Magnitud relativa del desfase |

#### Segmentos propios

| Nombre | Título | Condición |
|---|---|---|
| `conFaltantes` | Con Faltantes de Caja | `efectivoCaja < ventasReportadasZ` |
| `conSobrantes` | Con Sobrantes de Caja | `efectivoCaja > ventasReportadasZ` |
| `cuadrados` | Cuadrados (Sin Diferencia) | `efectivoCaja = ventasReportadasZ` |
| `soloZ` | Solo Cortes Z | `tipoCorte = 'z'` |
| `sinCobranza` | Sin Estación Cobranza | `estacion != 'COBRANZA'` |
| `diferenciaSignificativa` | Diferencia > $1,000 | `ABS(efectivoCaja - ventasReportadasZ) > 1000` |

---

### Vista: `reconciliacionDiaria`

**Título:** 4. Reconciliación Diaria (Ventas vs Cortes Z)
**Público:** Sí
**Cubos base:** `reconciliacionVentasDiarias` + `reconciliacionCortesZ`

#### Descripción

Cruza el ERP contra el POS por día y sucursal para identificar brechas entre los dos sistemas.

**Claves para interpretar:**

1. El reporte Z **NO resta devoluciones** → comparar siempre contra ventas **brutas**
2. Ventas Z incluye **todos los métodos de pago** (efectivo + tarjeta + crédito)
3. La diferencia "normal" en efectivo es 40-80% por pagos con tarjeta
4. Una sucursal puede tener múltiples cajas → la vista suma todos los cortes Z del día

> ⚠️ **FIX 2026-04:** Se agregaron medidas de tasa 8% (IEPS) y se eliminó el workaround de fecha.

#### Medidas propias

| Nombre | Fórmula | Descripción |
|---|---|---|
| `diferenciaSistemaVsZ` | `ventasBrutas - ventasZ` | Positivo = ERP > POS / Negativo = POS > ERP |
| `diferenciaEfectivoVsZ` | `efectivoCaja - ventasZ` | Normalmente negativo (hay ventas con tarjeta) |
| `impactoDevoluciones` | `devoluciones` | Monto devuelto que no aparece en cortes Z |
| `ventasNoEfectivo` | `ventasZ - totalIngresos` | Estimación de ventas con tarjeta u otros medios |
| `porcentajeVentasNoEfectivo` | `ventasNoEfectivo / NULLIF(ventasZ, 0) * 100` | Proporción sin efectivo |
| `tasaDevoluciones` | `devoluciones / NULLIF(ventasBrutas, 0) * 100` | Tasa de devoluciones sobre ventas brutas |
| `porcentajeDiferenciaSistemaVsZ` | `(ventasBrutas - ventasZ) / NULLIF(ventasZ, 0) * 100` | Brecha relativa ERP vs POS |

#### Segmentos propios

| Nombre | Título | Condición |
|---|---|---|
| `conDevoluciones` | Con Devoluciones | `devoluciones > 0` |
| `sistemaMayorQueZ` | Sistema > Z | `ventasBrutas > ventasZ` |
| `zMayorQueSistema` | Z > Sistema | `ventasBrutas < ventasZ` |
| `diferenciaSignificativa` | Diferencia > $1,000 | `ABS(ventasBrutas - ventasZ) > 1000` |

---

### Vista: `analiticaDevoluciones`

**Título:** 5. Analítica de Devoluciones
**Público:** Sí
**Cubo base:** `ventasPorDocumento`

#### Descripción

Análisis de devoluciones a nivel de **documento individual**. Permite identificar patrones por cliente, vendedor, sucursal y período.

> ⚠️ Para comparar con cortes Z, consultar `auditoriaEfectivo` por separado y combinar manualmente por `fecha + sucursal`.

**Casos de uso:**
- Identificar clientes con alta tasa de devolución
- Detectar devoluciones anómalas por monto o frecuencia
- Comparar ventas brutas vs netas por período
- Analizar motivos de devolución vía campo `observaciones`

#### Medidas propias

| Nombre | Fórmula | Descripción |
|---|---|---|
| `tasaDevoluciones` | `importeDevoluciones / NULLIF(importeVentas, 0) * 100` | % devoluciones sobre ventas brutas |
| `ventasNetas` | `importeVentas - importeDevoluciones` | Ingreso real del período |
| `promedioDevolucion` | `importeDevoluciones / NULLIF(conteoDevoluciones, 0)` | Monto típico de cada devolución |
| `promedioVenta` | `importeVentas / NULLIF(conteoVentas, 0)` | Monto típico de cada venta |

#### Segmentos propios

| Nombre | Título | Condición |
|---|---|---|
| `soloDevoluciones` | Solo Devoluciones | `tipo_doc IN ('DEV', 'DV')` |
| `soloVentas` | Solo Ventas | `tipo_doc IN ('REM', 'FAC')` |
| `devolucionesAltas` | Devoluciones Altas (> $500) | `importeDevoluciones > 500` |
| `conDevoluciones` | Períodos con Devoluciones | `importeDevoluciones > 0` |
| `documentosViables` | Solo Documentos Viables | `esViable = true` |
| `documentosCompletados` | Solo Completados | `estado = 'CO'` |

---

### Vista: `estadoInventario`

**Título:** 2. Estado de Inventario
**Cubo base:** `historicoInventario`

#### Descripción

Análisis de inventario histórico por producto, sucursal y fecha. Permite monitorear niveles de stock, detectar faltantes y comparar inventario entre tiendas y CEDIS.

> ⚠️ El CEDIS concentra el 70-80% del stock total. Para análisis por tienda usar el segmento `soloTiendas`.

#### Campos incluidos

| Campo | Tipo |
|---|---|
| `fechaCaptura`, `anio`, `numMes`, `nombreMes`, `diaSemana` | Dimensiones de tiempo |
| `sucursal`, `tipoUbicacion` | Dimensiones de ubicación |
| `sku`, `producto`, `marca`, `linea`, `unidadMedida` | Dimensiones de producto |
| `soloTiendas`, `soloCEDIS`, `inventarioPositivo`, `inventarioNegativo` | Segmentos heredados |
| `precioConImpuesto`, `costoUnitario` | Precio y costo |
| `cantidadStock` (alias `unidadesActuales`), `stockPromedio`, `numUbicaciones`, `stockMinimo`, `stockMaximo` | Medidas de stock |

---

## Tipos de Documento

| Código | Nombre | Categoría | Descripción |
|---|---|---|---|
| `FAC` | Factura | Venta | Venta con comprobante fiscal; mayor prioridad en deduplicación |
| `TIC` | Ticket | Venta | Venta de mostrador sin factura |
| `REM` | Remisión | Venta | Entrega de mercancía sin pago inmediato |
| `PE` | Pedido | Intermedio | Orden pendiente de confirmar; no es venta definitiva |
| `DEV` | Devolución | Devolución | Devolución completa de mercancía |
| `DV` | Devolución Parcial | Devolución | Devolución parcial de mercancía |
| `NC` | Nota de Crédito | Ajuste | Ajuste a favor del cliente |

---

## Glosario de Sucursales Excluidas

| Sucursal | Motivo de exclusión | Cubos afectados |
|---|---|---|
| `DPBodega-Test` | Entorno de pruebas; no es producción | `cortesDiarios`, `ventas`, `reconciliacionVentasDiarias` |
| `TORREON ARCOIRIS` | Schema drift en archivos Parquet | `cortesDiarios`, `reconciliacionCortesZ` |
| `CEDIS` | Ventas mayoristas B2B sin POS (excluida de reconciliación) | `reconciliacionVentasDiarias` (implícito) |
| Estación `COBRANZA` | Registra pagos de crédito, no ventas de mostrador | `cortesDiarios`, `reconciliacionCortesZ` |

---

## Historial de Cambios

| Fecha | Cubo/Vista | Cambio |
|---|---|---|
| **2026-04** | `cortesDiarios` | Reemplazado workaround de fecha por `TRY_CAST` + exclusión de `TORREON ARCOIRIS`. Datos históricos completos disponibles |
| **2026-04** | `reconciliacionCortesZ` | Mismo fix que `cortesDiarios`. Datos desde 2025-11-20 en adelante |
| **2026-04** | `reconciliacionDiaria` | Agregadas medidas de tasa 8% (IEPS) y eliminado workaround de fecha |
| **2026-04** | `auditoriaEfectivo` | Datos completos con `TRY_CAST`. Agregadas medidas IEPS 8% |
| **2025-04** | `ventas` | Alineación de `montoSinDuplicar` e `impuestoSinDuplicar` con reporte "Ventas por artículo por impuesto" del sistema contable |
| **Pendiente** | `catalogoProductos` | Cobertura de SKUs alfanuméricos (actualmente solo numéricos) |
