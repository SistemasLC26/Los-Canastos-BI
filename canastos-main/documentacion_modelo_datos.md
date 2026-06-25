# Documentación del Modelo de Datos --- Canastos TFX

> **Última actualización:** 2026-06 **Motor de datos:** Trino / Parquet
> sobre `canastos_tfx` **Framework:** Cube.js

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
  - [auditoriaEtl](#cubo-auditoriaetl)
- [Vistas](#vistas)
  - [ventasTipoPago](#vista-ventastipopago)
  - [auditoriaEfectivo](#vista-auditoriaefectivo)
  - [reconciliacionDiaria](#vista-reconciliaciondiaria)
  - [analiticaDevoluciones](#vista-analiticadevoluciones)
  - [estadoInventario](#vista-estadoinventario)
  - [auditoriaEtlView](#vista-auditoriaetlview)
- [Tipos de Documento](#tipos-de-documento)
- [Glosario de Sucursales
  Excluidas](#glosario-de-sucursales-excluidas)
- [Historial de Cambios](#historial-de-cambios)

---

## Resumen del Modelo

El modelo está organizado en tres grandes dominios:

---

Dominio Cubos involucrados Propósito

---

**Ventas / POS** `cortesDiarios`, `ventas`, Registro y análisis de
`reconciliacionCortesZ`, transacciones de venta,
`reconciliacionVentasDiarias`, cortes de caja y
`ventasPorDocumento` reconciliación ERP vs POS

**Inventario / `historicoInventario`, Stock histórico por ubicación
Catálogo** `catalogoProductos`, y clasificación de productos
`productosAlfaClasificados`

**Auxiliares** `clientes`, `calendario` Dimensiones de apoyo para
joins y filtros

**Monitoreo de `auditoriaEtl` Salud y trazabilidad del ETL
Pipeline** que extrae datos desde
sucursales hacia Athena

---

---

## Diagrama de Relaciones

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
    auditoriaEtl ─────────────────── (autónomo; monitoreo de pipeline, no de negocio)

---

## Cubos

---

### Cubo: `cortesDiarios`

**Título:** Cortes de Caja **Tabla fuente:**
`canastos_tfx.tfx_table_cortes` **Público:** No **Joins:** Ninguno

#### Descripción

Registra los **cortes de caja tipo X** (parcial) y **Z** (cierre de día)
a nivel de registro individual por estación. Incluye ventas reportadas,
efectivo físico contado, ingresos totales, impuestos desglosados y
clientes atendidos por caja.

> ⚠️ **FIX 2026-04:** Se eliminó el workaround de fecha
> (`< 2025-11-20`). Se usa `TRY_CAST` en todos los campos numéricos para
> tolerar schema drift en Parquet. Se excluye `DPBodega-Test` en el
> `WHERE`.

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID Corte string **PK.** Campo `cort_id`

`numeroCorte` Número de Corte string Consecutivo del corte dentro de la
estación

`fechaCorte` Fecha de Corte string `partition_date` casteado a `VARCHAR`

`anio` Año number Año extraído de `partition_date`

`numMes` Mes (Núm) number Mes numérico (1--12)

`nombreMes` Mes string Nombre del mes en español

`diaSemana` Día de la string Nombre del día; `DOW 0 = Domingo`
Semana (Trino/PostgreSQL)

`sucursal` Sucursal string Nombre de la sucursal

`estacion` Estación/Caja string Caja individual dentro de la sucursal

`tipoCorte` Tipo de Corte string `z` = cierre de día / `x` = corte parcial

`horaCorte` Hora del Corte string Hora en que el cajero ejecutó el corte

`fechaRegistro` Fecha de string Fecha del sistema; puede diferir de
Registro `partition_date`

---

#### Medidas

---

Nombre Título Tipo Formato Descripción

---

`ventasReportadasZ` Ventas sum currency Total vendido según el sistema en el corte
Reportadas  
 (Z)

`efectivoCaja` Efectivo en sum currency Dinero físico contado por el cajero
Caja

`totalIngresos` Total sum currency Suma de todas las formas de pago
Ingresos

`ventasConImpuesto10` Ventas Base sum currency Base gravable al 16% de IVA
16%

`impuesto10` IVA 16% sum currency Monto de IVA al 16%

`ventasConImpuesto15` Ventas sum currency Ventas exentas de IVA
Exentas (0%)

`impuesto15` IVA 0% sum currency Siempre cero; conservado por consistencia de esquema

`ventas8` Ventas Base number currency `(totalventas - impuesto15 - impuesto10 - ventasimpuesto10 - ventasimpuesto15) / 1.08`
8% (IEPS)

`impuesto8` IEPS 8% number currency `ventas8 × 0.08`

`ventasNoEfectivo` Ventas No sum currency `totalventas - totalcaja` (tarjeta/crédito)
Efectivo

`clientesAtendidos` \# Clientes sum --- Suma de `clientes_int`
Atendidos

`ticketPromedioZ` Ticket avg currency `totalventas / NULLIF(clientes_int, 0)`
Promedio (Z)

`conteoCortes` \# Cortes count --- Número de registros; útil para auditoría
Realizados

---

#### Segmentos

---

Nombre Título Condición Notas

---

`cortesZ` Solo Cortes `corte = 'z'` Cierres de día; usar en reportes
Z diarios consolidados

`cortesX` Solo Cortes `corte = 'x'` Cortes parciales intradía
X

`sinCobranza` Sin Estación `estacion != 'COBRANZA'` COBRANZA registra pagos de crédito,
Cobranza no ventas de mostrador

---

---

### Cubo: `ventas`

**Título:** Ventas (Cabecero) **Tabla fuente:**
`canastos_tfx.tfx_table_ventas` **Público:** Sí **Joins:** `clientes`

#### Descripción

Representa el **cabecero de cada transacción de venta**: folio, cliente,
tipo de documento, monto total y estado. No incluye el detalle artículo
por artículo (eso corresponde a `partidasVenta`).

> ⚠️ **Deduplicación activa:** La tabla origen puede contener el mismo
> `folio+sucursal` con múltiples tipos de documento (ej: un pedido que
> se convirtió en factura aparece como `PE` y como `FAC`). Se aplica
> `ROW_NUMBER()` por `folio+sucursal` conservando solo el documento de
> mayor prioridad.

**Prioridad de deduplicación:**

Prioridad Tipo Significado

---

1 `FAC` Factura (documento final)
2 `TIC` Ticket
3 `PE` Pedido
4 `REM` Remisión
5 otros Cualquier otro tipo

#### Joins

---

Cube Tipo Condición
relacionado

---

`clientes` many_to_one `ventas.cliente = clientes.codigoCliente AND ventas.sucursal = clientes.sucursal`

---

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID Venta string **PK.** Concatenación
Único `folio + sucursal + tipo_doc`

`numeroVenta` Folio string Número de folio del documento

`cliente` Código string Puede ser `sys`/`SYS` en ventas de
Cliente mostrador sin cliente

`sucursal` Sucursal string Clave de la sucursal donde se generó el
documento

`tipoDocumento` Tipo de string Ver [Tipos de
Documento Documento](#tipos-de-documento)

`fechaTransaccion` Fecha Venta time `partition_date`

`anio` Año number Año de la transacción

`numMes` Mes (Núm) number Mes numérico (1--12)

`nombreMes` Mes string Nombre del mes en español

`observacion` Observación string Texto libre; detecta agrupaciones como
`TICKETS ANEXOS`

`estado` Estado de string `PE` = pendiente (no confirmado)
Venta

---

#### Medidas

---

Nombre Título Tipo Formato Descripción

---

`montoTotal` Monto Bruto sum currency ⚠️ Incluye todos los tipos; puede
Cabecero duplicar montos. Solo para
diagnóstico

`montoSinDuplicar` Monto Sin sum currency Solo `FAC`, `REM`, `DV`, `DEV`.
Duplicar Alineado con reporte contable _(FIX
2025-04)_

`impuestoSinDuplicar` Impuesto Total sum currency Impuesto filtrado igual que
Sin Duplicar `montoSinDuplicar` _(FIX 2025-04)_

`totalImpuesto` Impuesto Total sum currency ⚠️ Misma advertencia que
(Bruto) `montoTotal`. Preferir
`impuestoSinDuplicar`

`clientesUnicos` Clientes Únicos count_distinct --- Excluye `sys`/`SYS`. Solo con
(Registrados) `is_viable = true`

---

#### Segmentos

---

Nombre Título Condición Notas

---

`ventasValidas` Solo Ventas `is_viable = true` Excluye
Viables cancelados y
registros de
prueba

`sinDuplicacionPedidos` Sin Duplicar `tipo_doc IN ('FAC','REM','TIC','NC','DV','PE','DEV')` Excluye
Pedidos documentos
intermedios

`ventasReales` Ventas `is_viable = true` + sin `TICKETS ANEXOS` + sin cliente Segmento más
Reales `sys` con `FAC` + `estado <> 'PE'` estricto para
(Filtros análisis al
Aplicados) mayoreo

---

---

### Cubo: `reconciliacionCortesZ`

**Título:** Cortes Z Diarios (Reconciliación) **Tabla fuente:**
`canastos_tfx.tfx_table_cortes` **Público:** No **Joins:**
`reconciliacionVentasDiarias`

#### Descripción

Cortes Z **pre-agregados por día y sucursal** para reconciliación contra
el ERP. A diferencia de `cortesDiarios` (un registro por corte
individual), este cubo produce **una sola fila por fecha+sucursal**,
facilitando el join directo con `reconciliacionVentasDiarias`.

> ⚠️ **FIX 2026-04:** Se reemplazó el workaround de fecha por
> `TRY_CAST` + exclusión explícita de `TORREON ARCOIRIS`. Ahora incluye
> datos desde 2025-11-20 en adelante.

**Filtros aplicados en la fuente:**

- `corte = 'z'` --- solo cierres de día
- `sucursal != 'DPBodega-Test'` --- excluir pruebas
- `sucursal != 'TORREON ARCOIRIS'` --- excluir schema drift
- `estacion != 'COBRANZA'` --- excluir pagos de crédito

#### Joins

Cube relacionado Tipo Condición

---

`reconciliacionVentasDiarias` one_to_one `fecha + sucursal`

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID string **PK.**  
 Agregado `CAST(fecha AS VARCHAR)      \|     \| '-' \|     \| sucursal`

`fecha` Fecha time `partition_date` del archivo Parquet

`sucursal` Sucursal string Nombre de la sucursal

---

#### Medidas

---

Nombre Título Tipo Formato Descripción

---

`ventasZ` Ventas Reportadas sum currency Total vendido según cortes Z del día
(Z)

`efectivoCaja` Efectivo en Caja sum currency Efectivo físico contado en todas las cajas

`diferenciaZ` Diferencia Z sum currency Faltante (-) o sobrante (+) del día
(Efectivo -  
 Ventas)

`totalIngresos` Total Ingresos sum currency Suma de todas las formas de pago

`retirosEfectivo` Retiros de sum currency `totalIngresos - efectivoCaja`
Efectivo

`ventasImpuesto10` Ventas Base 16% sum currency Base gravable al 16%

`impuesto10` IVA 16% sum currency Monto IVA 16%

`ventasImpuesto15` Ventas Exentas sum currency Ventas exentas de IVA
(0%)

`impuesto15` IVA 0% sum currency Siempre cero

`ventas8` Ventas Base 8% sum currency Base IEPS calculada por diferencia
(IEPS)

`impuesto8` IEPS 8% sum currency `ventas8 × 0.08`

`totalImpuestosDesglosados` Total Impuestos sum currency Suma de los tres impuestos para validación
(0%+8%+16%)

`clientesAtendidos` \# Clientes sum --- Total de clientes del día
Atendidos

`numCortesZ` \# Cortes Z sum --- Cajas que cerraron ese día; detecta cajas
sin corte

`ticketPromedioZ` Ticket Promedio avg currency `ventas_z / NULLIF(clientes_atendidos, 0)`
(Z)

---

---

### Cubo: `reconciliacionVentasDiarias`

**Título:** Ventas Diarias Sistema (Reconciliación) **Tabla fuente:**
`canastos_tfx.tfx_table_ventas` **Público:** No **Joins:** Ninguno

#### Descripción

Ventas del ERP **pre-agregadas por día y sucursal**. Es el "lado
sistema" de la reconciliación contra los cortes Z del POS.

> ⚠️ **Uso restringido:** Este cubo NO debe usarse para análisis general
> de ventas. Usar `analiticaVentas` o `analiticaDevoluciones` para ese
> propósito.

**Filtros aplicados en la fuente:**

- `is_viable = true` --- solo documentos válidos
- `estado = 'CO'` --- solo completados
- `sucursal != 'DPBodega-Test'` --- excluir pruebas

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID string **PK.**  
 Agregado `CAST(fecha AS VARCHAR)     \|     \| '-' \|     \| sucursal`

`fecha` Fecha time `partition_date` de la tabla origen

`anio` Año number Año de la fecha

`numMes` Mes (Núm) number Mes numérico (1--12)

`nombreMes` Mes string Nombre del mes

`diaSemana` Día de la string Nombre del día de la semana  
 Semana

`sucursal` Sucursal string Sucursal de la venta

---

#### Medidas

---

Nombre Título Tipo Formato Descripción

---

`ventasBrutas` Ventas Brutas sum currency Suma `REM + FAC` completados y
Sistema viables

`devoluciones` Devoluciones sum currency Suma `DEV + DV` completados y
Sistema viables

`ventasNetas` Ventas Netas sum currency `ventasBrutas - devoluciones`
Sistema

`numVentas` \# Ventas sum --- Número de documentos de venta

`numDevoluciones` \# Devoluciones sum --- Número de documentos de
devolución

`descuentos` Descuentos sum currency Descuentos aplicados en ventas

`impuestos` Impuestos sum currency Impuestos registrados

`costos` Costos sum currency Costo de los artículos vendidos

---

---

### Cubo: `ventasPorDocumento`

**Título:** Ventas por Tipo de Documento **Tabla fuente:**
`canastos_tfx.tfx_table_ventas` **Público:** No **Joins:** Ninguno

#### Descripción

Detalle de ventas a **nivel de documento individual** (folio). A
diferencia de `reconciliacionVentasDiarias`, no pre-agrega: expone cada
folio por separado para análisis de devoluciones, facturación y
comportamiento por cliente o vendedor.

> ⚠️ Todas las medidas aplican `is_viable = true` internamente. Los
> registros no viables contribuyen con `0` (no se omiten).

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID Venta string **PK.**  
 `venta                                   \|     \| '-' \|     \| sucursal`

`numeroVenta` Número de Venta string Folio del documento

`fechaVenta` Fecha de Venta time `partition_date`

`anio` Año number ---

`numMes` Mes (Núm) number ---

`nombreMes` Mes string ---

`diaSemana` Día de la string ---  
 Semana

`sucursal` Sucursal string ---

`tipoDocumento` Tipo de string Ver [Tipos de Documento](#tipos-de-documento)  
 Documento

`estado` Estado string `CO` = Completado, `CA` = Cancelado

`cliente` Cliente string Puede ser `sys`/`SYS` en mostrador

`serieDocumento` Serie del string Serie del comprobante fiscal  
 Documento

`observaciones` Observaciones string Texto libre; puede contener motivo de devolución

`vendedor` Vendedor string Vendedor asociado al documento

`esViable` Es Viable boolean `true` si el documento es válido para análisis

---

#### Medidas

---

Nombre Título Tipo Formato Descripción

---

`importeTotal` Importe Total sum currency Todos los documentos viables (ventas + devoluciones)

`importeVentas` Importe Ventas sum currency Solo `REM` y `FAC` viables

`importeDevoluciones` Importe sum currency Solo `DEV` y `DV` viables
Devoluciones

`importeNeto` Importe Neto sum currency `REM/FAC` suman, `DEV/DV` restan

`descuentoTotal` Descuentos sum currency Descuentos sobre viables

`impuestoTotal` Impuestos sum currency Impuestos sobre viables

`precioTotal` Precio Total sum currency Precio antes de descuentos

`costoTotal` Costo Total sum currency Costo de los artículos

`conteoDocumentos` \# Documentos sum --- Total documentos viables

`conteoVentas` \# Ventas sum --- Solo `REM` y `FAC` viables

`conteoDevoluciones` \# sum --- Solo `DEV` y `DV` viables
Devoluciones

`porcentajeDevoluciones` \% number percent `importeDevoluciones / NULLIF(importeVentas, 0) * 100`
Devoluciones

---

#### Segmentos

---

Nombre Título Condición

---

`soloVentas` Solo Ventas (REM y FAC) `tipo_doc IN ('REM', 'FAC')`

`soloDevoluciones` Solo Devoluciones (DEV y `tipo_doc IN ('DEV', 'DV')`
DV)

`documentosViables` Solo Documentos Viables `is_viable = true`

`documentosCompletados` Solo Completados `estado = 'CO'`

---

---

### Cubo: `historicoInventario`

**Título:** Historico de Inventario **Tabla fuente:**
`canastos_tfx.tfx_table_inv` + `tfx_table_partvta` (LEFT JOIN)
**Público:** No especificado **Joins:** Ninguno

#### Descripción

Snapshots históricos de inventario por artículo, sucursal y fecha de
partición. Cada registro es la existencia de un SKU en una ubicación en
un día específico.

**Enriquecimiento con precio y costo:** La tabla de inventario no tiene
precio ni costo propios. Se hace un `LEFT JOIN` con `tfx_table_partvta`
para traer `precio_lista` y `costo_ajustado`. El costo se sanea: si es
≤0 o mayor al precio, se estima como el **80% del precio de lista**.

> ⚠️ **Advertencia CEDIS:** El CEDIS concentra el 70-80% del stock
> total. Sin filtrar, los totales están dominados por la bodega. Usar el
> segmento `soloTiendas` para análisis por punto de venta.

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID Historico string **PK.**  
 `articulo                         \|     \| '-' \|     \| sucursal \|     \| '-' \|     \| partition_date`

`sku` SKU string `CAST(articulo AS VARCHAR)`

`sucursal` Sucursal string Sucursal o bodega del snapshot

`marca` Marca string Marca del producto

`linea` Línea string Línea/categoría del producto

`producto` Producto string Nombre descriptivo del artículo

`fechaCaptura` Fecha Corte time `partition_date`  
 Inventario

`anio` Año number ---

`numMes` Mes (Núm) number ---

`nombreMes` Mes string ---

`diaSemana` Día de la string DOW 0 = Sunday (Trino/PostgreSQL)  
 Semana

`unidadMedida` Unidad de string KG, PZ, LT, etc.  
 Medida

`tipoUbicacion` Tipo de string `CEDIS`, `MAYOREO`, `MENUDEO`, o `TIENDA`  
 Ubicación

---

#### Medidas

---

Nombre Título Tipo Formato Descripción

---

`cantidadStock` Unidades en sum --- ⚠️ Incluye CEDIS por defecto;
Stock aplicar `soloTiendas` para canal

`stockPromedio` Stock Promedio avg --- Promedio en el período
por Ubicación seleccionado

`numUbicaciones` \# Ubicaciones count_distinct --- Sucursales distintas donde hay
registro del SKU

`stockMinimo` Stock Mínimo min --- Mínimo del período; detecta
quiebres

`stockMaximo` Stock Máximo max --- Máximo del período; detecta
sobrestock

`precioConImpuesto` Precio (con max currency `precio_lista × 1.16` (IVA 16%)
Impuesto)

`costoUnitario` Costo Unitario max currency Costo saneado; fallback al 80%
del precio si inválido

---

#### Segmentos

---

Nombre Título Condición Notas

---

`soloTiendas` Solo Tiendas `sucursal != 'CEDIS' AND NOT LIKE '%MAYOREO%' AND NOT LIKE '%MENUDEO%'` Excluye bodega
central y canales de
distribución

`soloCEDIS` Solo CEDIS `sucursal = 'CEDIS'` Solo bodega central

`inventarioPositivo` Solo `existencia > 0` Disponibilidad real
Inventario de producto
Positivo

`inventarioNegativo` Solo `existencia < 0` Faltantes o errores
Inventario de captura
Negativo

---

---

### Cubo: `productosAlfaClasificados`

**Título:** Clasificación Híbrida de Productos Alfanuméricos **Tabla
fuente:** `canastos_tfx.tfx_table_partvta` **Público:** No

#### Descripción

Clasifica los **\~106 productos con SKU alfanumérico** que no pueden
unirse al catálogo numérico. Usa una estrategia híbrida de dos capas:

---

Capa Productos Método

---

**Mapeo 23 Marca y línea asignadas manualmente (match
directo** productos conocido en inventario)

**Parsing 83 Marca y línea extraídas del campo `observ` con
automático** productos `UPPER(observ) LIKE '%keyword%'`

**Fallback** Resto `PRODUCTOS LOCALES` / `SIN CLASIFICAR`

---

**Filtros de la fuente:**

- `TRY_CAST(articulo AS BIGINT) IS NULL` --- solo alfanuméricos
- `articulo NOT LIKE 'SYS%'` --- excluir artículos internos
- `observ IS NOT NULL AND observ != ''` --- requiere descripción para
  el parsing

#### Dimensiones

Nombre Título Tipo Público

---

`sku` SKU Alfanumérico string (**PK**) Sí
`descripcion` Descripción string Sí
`marca` Marca string Sí
`linea` Línea string Sí

#### Líneas inferidas por parsing automático

---

Línea Keywords detectados

---

`GALLETAS` GALLETA, ALFAJOR

`CHOCOLATES` CHOCOLATE

`BOTANAS` PRETZEL, CHURRO, CHICHARRON, MAIZ INFLADO, KONCHITA,
FRITURA, CHIPS (sin CAMOTE/JICAMA)

`VEGETALES PROCESADOS` JICAMA, CAMOTE, BETABEL, ZANAHORIA, PLATANO+SAN LUIS

`DULCES` GOMA, GOMITA, PALETA, PALANQUETA, DULCE, COCADA,
GLORIAS, MAZAPAN, CHAMOY, CHICLE, ATE

`AMARANTO` ALEGRIA

`CEREALES` GRANOLA

`SEMILLAS Y FRUTOS SECOS` CACAHUATE, NUEZ, PEPITA, PISTACHE, SOYA (sin
CHICHARRON)

`BEBIDAS` CONCENTRADO, PONCHE, TISANA, TE, AGUA, COCA, BOLSITA+MI
CASITA

`MIELES Y ENDULZANTES` MIEL

`CONDIMENTOS` CHILE (sin CHICLE)

`SUPLEMENTOS` MICRODOSIS

`CAFES Y TES` CAFE

`ENVASES Y EMPAQUES` BOLSA, FRASCO, TARRO, BOLSA BIODEGRADABLE

`SERVICIOS` COSTO ENVIO, FLETE

---

---

### Cubo: `clientes`

**Título:** Clientes **Tabla fuente:** `canastos_tfx.tfx_table_clients`
**Público:** Sí

#### Descripción

Catálogo de clientes registrados en el sistema. La **PK es compuesta**
(`cliente + sucursal`) porque un mismo cliente puede estar registrado en
más de una sucursal con datos distintos.

> Es el cubo hijo del join en `ventas` (many_to_one).

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID Sistema string **PK.**  
 `cliente                          \|     \| '-' \|     \| sucursal`

`codigoCliente` Código string Campo usado para el join con `ventas`  
 Cliente

`nombreCliente` Nombre string Nombre o razón social (público)

`sucursal` Sucursal string Sucursal donde está registrado el cliente

---

#### Medidas

---

Nombre Título Tipo Descripción

---

`conteo` Total count Conteo de registros; tamaño de cartera por
Clientes sucursal

---

---

### Cubo: `catalogoProductos`

**Título:** Catálogo de Productos **Tabla fuente:**
`canastos_tfx.tfx_table_inv` **Público:** Sí

#### Descripción

Catálogo de productos con **SKU numérico únicamente**. Los SKUs
alfanuméricos están cubiertos por `productosAlfaClasificados`. El SKU se
expone en dos formatos para facilitar joins con tablas que lo almacenen
como texto o como entero.

**Filtro:** `TRY_CAST(articulo AS BIGINT) IS NOT NULL` **Granularidad:**
Un registro por SKU a nivel empresa (GROUP BY artículo; colapsa
múltiples filas por sucursal).

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID Producto string **PK.** `sku_str`

`sku` SKU (String) string VARCHAR; para joins con tablas de
texto

`skuInt` SKU number BIGINT; para joins con tablas
(Numérico) numéricas

`descripcion` Descripción string Nombre del producto

`linea` Línea string Línea/categoría

`marca` Marca string Marca del producto

---

---

### Cubo: `calendario`

**Título:** Calendario **Tabla fuente:** `canastos_tfx.calendar_table`
**Público:** Sí

#### Descripción

Tabla de calendario auxiliar precalculada. Sirve como dimensión de
tiempo confiable para joins y filtros, evitando recalcular `EXTRACT` y
`CASE` en cada cubo.

**Ventajas sobre calcular fechas en cada cubo:**

- Consistencia garantizada entre todos los cubos
- Mejor rendimiento (valores precalculados, no funciones en tiempo de
  consulta)
- Facilita filtros de rango en el playground

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`fecha` Fecha time `cal_date`; habilita filtros de rango
(**PK**) nativos

`anio` Año number Precalculado

`numMes` Mes number Precalculado (1--12)
(Núm)

`nombreMes` Mes string Precalculado en idioma del sistema

`diaSemana` Día de string Precalculado; verificar convención DOW vs
la otros cubos
Semana

---

---

### Cubo: `auditoriaEtl`

**Título:** Auditoría ETL **Tabla fuente:**
`canastos_tfx.audit_etl_status` **Público:** Sí **Joins:** Ninguno

#### Descripción

Log de ejecución del **ETL que extrae datos desde las sucursales
(Compaq/POS) hacia Athena**. Cada fila es una corrida de extracción para
un proceso/tabla/sucursal en una fecha específica, con su resultado
(`SUCCESS`/`FAILED`) y métricas básicas de volumen.

Es un cubo de **monitoreo de pipeline**, no de datos de negocio ---
sirve para detectar sucursales que fallan en su extracción diaria,
identificar pipelines atrasados vía `watermark`, y diagnosticar errores
reportados por el ETL (típicamente errores de SQL Server por nombres de
tabla origen inválidos).

> ⚠️ **Columnas casteadas:** `execution_date` y `watermark` llegan como
> `VARCHAR` desde Athena (no como timestamp nativo), por lo que ambas se
> castean explícitamente a `TIMESTAMP`/`DATE` en el SQL del cubo para
> poder usarlas como dimensiones de tiempo y aplicar `EXTRACT()`.
>
> ⚠️ **Palabra reservada:** la columna `table` es palabra reservada en
> Athena/Presto; se referencia siempre entre comillas dobles
> (`{CUBE}."table"`) para evitar errores de sintaxis.

#### Dimensiones

---

Nombre Título Tipo Descripción

---

`id` ID Sistema string **PK.** Concatenación
`execution_date + process + sucursal + table`

`fechaEjecucion` Fecha time `execution_date` casteado a `TIMESTAMP`; día en que
Ejecución corrió el proceso ETL (no la fecha de los datos
extraídos)

`anio` Año number `EXTRACT(YEAR FROM CAST(execution_date AS DATE))`

`mes` Mes number `EXTRACT(MONTH FROM CAST(execution_date AS DATE))`

`dia` Día number `EXTRACT(DAY FROM CAST(execution_date AS DATE))`

`nombreMes` Nombre Mes string Nombre del mes en español, calculado con `CASE` sobre
`execution_date` casteado

`diaSemana` Día de la string Nombre del día en español, vía `day_of_week()` sobre
Semana `execution_date` casteado

`proceso` Proceso string Nombre del proceso ETL que generó la corrida (ej.
`EXTRACTION`)

`tipoCorrida` Tipo string Tipo de corrida del ETL (ej. `Completa` vs
Corrida incremental/parcial)

`sucursal` Sucursal string Sucursal de origen de los datos extraídos en la corrida
(público)

`tabla` Tabla string Nombre de la tabla destino que se está cargando (ej.
`ventas`, `inv`, `cortesxx`)

`estadoConsulta` Estado string Resultado de la etapa de consulta/extracción desde el
Consulta origen (`query_status`)

`estadoCarga` Estado string Resultado de la etapa de carga hacia el destino
Carga Athena/S3 (`upload_status`)

`watermark` Watermark time Última fecha de datos que el ETL alcanzó a procesar;
casteado a `TIMESTAMP`. Si se estanca para una
sucursal, indica pipeline atrasado

`error` Error string Mensaje de error reportado por el ETL, si lo hubo
(vacío/`N/A` en corridas exitosas)

`tieneError` Tiene Error string `'Sí'`/`'No'`; marca la corrida como fallida si
`estadoConsulta` **o** `estadoCarga` no fue `SUCCESS`

---

#### Medidas

---

Nombre Título Tipo Descripción

---

`conteo` Total count Conteo simple de corridas registradas
Corridas

`filasCargadas` Filas sum Suma de `rows`; detecta caídas anormales de volumen por sucursal
Cargadas

`corridasConError` Corridas sum `CASE WHEN estadoConsulta != SUCCESS OR estadoCarga != SUCCESS THEN 1 ELSE 0 END`
Con Error

`corridasExitosas` Corridas sum `CASE WHEN estadoConsulta = SUCCESS AND estadoCarga = SUCCESS THEN 1 ELSE 0 END`
Exitosas

---

#### Notas de interpretación

- `filasCargadas = 0` con `estadoCarga = SUCCESS` puede ser normal
  (sin movimientos ese día) o señal de un problema silencioso ---
  comparar contra el histórico de la misma sucursal/tabla.
- El campo `error` distingue dos tipos de falla observados en
  producción: errores de SQL Server con mensaje explícito (típicamente
  `Invalid object name '<tabla>'`, indicando un nombre de tabla origen
  incorrecto) y fallas silenciosas tipo `No data returned`, que pueden
  ser simples ausencias de movimiento más que errores del pipeline.
- Sucursales con `corridasConError` consistentemente altas en relación
  a `conteo` indican un problema estructural (ej. configuración de
  nombre de tabla incorrecta), distinto a una falla aislada de un solo
  día.

---

## Vistas

---

### Vista: `ventasTipoPago`

**Título:** 4. Ventas por Tipo de Pago **Público:** Sí **Cubo base:**
`cortesDiarios`

#### Descripción

Desglose de ventas por tipo de pago usando cortes Z. La lógica de
separación es:

    Efectivo    = efectivoCaja          (totalcaja)
    Tarjeta/Otros = ventasNoEfectivo   (totalventas - totalcaja)

> ⚠️ Recomendado usar junto con el segmento `cortesZ` para evitar
> mezclar cortes parciales.

#### Campos incluidos

---

Campo Tipo

---

`fechaCorte`, `anio`, `numMes`, `nombreMes`, Dimensiones de
`diaSemana` tiempo

`sucursal`, `estacion`, `tipoCorte` Dimensiones
operativas

`ventasReportadasZ`, `efectivoCaja`, Medidas de tipo de
`ventasNoEfectivo` pago

`conteoCortes` Medida operativa

---

---

### Vista: `auditoriaEfectivo`

**Título:** 3. Auditoría de Efectivo **Público:** Sí **Cubo base:**
`cortesDiarios`

#### Descripción

Control de efectivo a nivel de **corte individual**. Permite identificar
exactamente qué caja, en qué hora y en qué día presentó un faltante o
sobrante.

> ⚠️ **FIX 2026-04:** Datos completos con `TRY_CAST`. Se agregaron
> medidas de tasa 8% (IEPS).

#### Medidas propias

---

Nombre Fórmula Descripción

---

`diferencia` `efectivoCaja - ventasReportadasZ` **Positivo** = sobrante /
**Negativo** = faltante / **Cero** =
cuadre perfecto

`porcentajeDiferencia` `diferencia / NULLIF(ventasReportadasZ, 0) * 100` Magnitud relativa del desfase

---

#### Segmentos propios

---

Nombre Título Condición

---

`conFaltantes` Con Faltantes de `efectivoCaja < ventasReportadasZ`
Caja

`conSobrantes` Con Sobrantes de `efectivoCaja > ventasReportadasZ`
Caja

`cuadrados` Cuadrados (Sin `efectivoCaja = ventasReportadasZ`
Diferencia)

`soloZ` Solo Cortes Z `tipoCorte = 'z'`

`sinCobranza` Sin Estación `estacion != 'COBRANZA'`
Cobranza

`diferenciaSignificativa` Diferencia \> `ABS(efectivoCaja - ventasReportadasZ) > 1000`
\$1,000

---

---

### Vista: `reconciliacionDiaria`

**Título:** 4. Reconciliación Diaria (Ventas vs Cortes Z) **Público:**
Sí **Cubos base:** `reconciliacionVentasDiarias` +
`reconciliacionCortesZ`

#### Descripción

Cruza el ERP contra el POS por día y sucursal para identificar brechas
entre los dos sistemas.

**Claves para interpretar:**

1.  El reporte Z **NO resta devoluciones** → comparar siempre contra
    ventas **brutas**
2.  Ventas Z incluye **todos los métodos de pago** (efectivo + tarjeta +
    crédito)
3.  La diferencia "normal" en efectivo es 40-80% por pagos con tarjeta
4.  Una sucursal puede tener múltiples cajas → la vista suma todos los
    cortes Z del día

> ⚠️ **FIX 2026-04:** Se agregaron medidas de tasa 8% (IEPS) y se
> eliminó el workaround de fecha.

#### Medidas propias

---

Nombre Fórmula Descripción

---

`diferenciaSistemaVsZ` `ventasBrutas - ventasZ` Positivo = ERP \> POS /
Negativo = POS \> ERP

`diferenciaEfectivoVsZ` `efectivoCaja - ventasZ` Normalmente negativo (hay
ventas con tarjeta)

`impactoDevoluciones` `devoluciones` Monto devuelto que no
aparece en cortes Z

`ventasNoEfectivo` `ventasZ - totalIngresos` Estimación de ventas con
tarjeta u otros medios

`porcentajeVentasNoEfectivo` `ventasNoEfectivo / NULLIF(ventasZ, 0) * 100` Proporción sin efectivo

`tasaDevoluciones` `devoluciones / NULLIF(ventasBrutas, 0) * 100` Tasa de devoluciones
sobre ventas brutas

`porcentajeDiferenciaSistemaVsZ` `(ventasBrutas - ventasZ) / NULLIF(ventasZ, 0) * 100` Brecha relativa ERP vs
POS

---

#### Segmentos propios

---

Nombre Título Condición

---

`conDevoluciones` Con Devoluciones `devoluciones > 0`

`sistemaMayorQueZ` Sistema \> Z `ventasBrutas > ventasZ`

`zMayorQueSistema` Z \> Sistema `ventasBrutas < ventasZ`

`diferenciaSignificativa` Diferencia \> `ABS(ventasBrutas - ventasZ) > 1000`
\$1,000

---

---

### Vista: `analiticaDevoluciones`

**Título:** 5. Analítica de Devoluciones **Público:** Sí **Cubo base:**
`ventasPorDocumento`

#### Descripción

Análisis de devoluciones a nivel de **documento individual**. Permite
identificar patrones por cliente, vendedor, sucursal y período.

> ⚠️ Para comparar con cortes Z, consultar `auditoriaEfectivo` por
> separado y combinar manualmente por `fecha + sucursal`.

**Casos de uso:**

- Identificar clientes con alta tasa de devolución
- Detectar devoluciones anómalas por monto o frecuencia
- Comparar ventas brutas vs netas por período
- Analizar motivos de devolución vía campo `observaciones`

#### Medidas propias

---

Nombre Fórmula Descripción

---

`tasaDevoluciones` `importeDevoluciones / NULLIF(importeVentas, 0) * 100` \% devoluciones sobre
ventas brutas

`ventasNetas` `importeVentas - importeDevoluciones` Ingreso real del
período

`promedioDevolucion` `importeDevoluciones / NULLIF(conteoDevoluciones, 0)` Monto típico de cada
devolución

`promedioVenta` `importeVentas / NULLIF(conteoVentas, 0)` Monto típico de cada
venta

---

#### Segmentos propios

---

Nombre Título Condición

---

`soloDevoluciones` Solo Devoluciones `tipo_doc IN ('DEV', 'DV')`

`soloVentas` Solo Ventas `tipo_doc IN ('REM', 'FAC')`

`devolucionesAltas` Devoluciones Altas (\> `importeDevoluciones > 500`
\$500)

`conDevoluciones` Períodos con `importeDevoluciones > 0`
Devoluciones

`documentosViables` Solo Documentos Viables `esViable = true`

`documentosCompletados` Solo Completados `estado = 'CO'`

---

---

### Vista: `estadoInventario`

**Título:** 2. Estado de Inventario **Cubo base:** `historicoInventario`

#### Descripción

Análisis de inventario histórico por producto, sucursal y fecha. Permite
monitorear niveles de stock, detectar faltantes y comparar inventario
entre tiendas y CEDIS.

> ⚠️ El CEDIS concentra el 70-80% del stock total. Para análisis por
> tienda usar el segmento `soloTiendas`.

#### Campos incluidos

---

Campo Tipo

---

`fechaCaptura`, `anio`, `numMes`, `nombreMes`, Dimensiones
`diaSemana` de tiempo

`sucursal`, `tipoUbicacion` Dimensiones
de ubicación

`sku`, `producto`, `marca`, `linea`, `unidadMedida` Dimensiones
de producto

`soloTiendas`, `soloCEDIS`, `inventarioPositivo`, Segmentos
`inventarioNegativo` heredados

`precioConImpuesto`, `costoUnitario` Precio y
costo

`cantidadStock` (alias `unidadesActuales`), Medidas de
`stockPromedio`, `numUbicaciones`, `stockMinimo`, stock
`stockMaximo`

---

---

### Vista: `auditoriaEtlView`

**Título:** Auditoría ETL **Público:** Sí **Cubo base:** `auditoriaEtl`

#### Descripción

Monitoreo de corridas del ETL que extrae datos de sucursales hacia
Athena. Agregación a nivel **fecha de ejecución + proceso + sucursal +
tabla**. Vista de un solo cubo, sin joins, ya que la tabla origen es un
log compacto de auditoría que no requiere enriquecimiento adicional.

**Claves para interpretar:**

1.  `tieneError = 'Sí'` si `estadoConsulta` o `estadoCarga` no fue
    `SUCCESS`
2.  `watermark` estancado en una sucursal indica pipeline atrasado en
    ese punto
3.  `filasCargadas = 0` no siempre es error; comparar contra histórico
    antes de concluir falla
4.  `error` solo tiene contenido en corridas fallidas; en corridas
    exitosas viene vacío/`N/A`

#### Campos incluidos

---

Campo Tipo

---

`fechaEjecucion`, `anio`, `mes`, `dia`, Dimensiones de tiempo
`nombreMes`, `diaSemana`

`proceso`, `tipoCorrida`, `sucursal`, Identificación de la
`tabla` corrida

`estadoConsulta`, `estadoCarga`, Resultado de la corrida
`tieneError`, `watermark`, `error`

`conteo`, `filasCargadas`, Métricas de volumen y
`corridasConError`, `corridasExitosas` salud del pipeline

---

#### Caso de uso de referencia

Detección de sucursales con extracción fallando de forma recurrente (no
aislada): agrupar por `sucursal` y ordenar por `SUM(corridasConError)`
descendente. Sucursales con una proporción alta de `corridasConError`
sobre `conteo` suelen indicar un problema de configuración estructural
(ej. nombre de tabla origen incorrecto en SQL Server) en lugar de una
falla puntual de un día.

---

## Tipos de Documento

---

Código Nombre Categoría Descripción

---

`FAC` Factura Venta Venta con comprobante fiscal; mayor prioridad
en deduplicación

`TIC` Ticket Venta Venta de mostrador sin factura

`REM` Remisión Venta Entrega de mercancía sin pago inmediato

`PE` Pedido Intermedio Orden pendiente de confirmar; no es venta
definitiva

`DEV` Devolución Devolución Devolución completa de mercancía

`DV` Devolución Devolución Devolución parcial de mercancía
Parcial

`NC` Nota de Ajuste Ajuste a favor del cliente
Crédito

---

---

## Glosario de Sucursales Excluidas

---

Sucursal Motivo de exclusión Cubos afectados

---

`DPBodega-Test` Entorno de pruebas; no es `cortesDiarios`, `ventas`,
producción `reconciliacionVentasDiarias`

`TORREON ARCOIRIS` Schema drift en archivos `cortesDiarios`,
Parquet `reconciliacionCortesZ`

`CEDIS` Ventas mayoristas B2B sin POS `reconciliacionVentasDiarias`
(excluida de reconciliación) (implícito)

Estación `COBRANZA` Registra pagos de crédito, no `cortesDiarios`,
ventas de mostrador `reconciliacionCortesZ`

---

> ⚠️ **Nota sobre `auditoriaEtl`:** este cubo NO excluye `DPBodega-Test`
> (sí es relevante monitorear si esa sucursal de prueba también está
> corriendo el ETL). Al analizar el ranking de errores recurrentes,
> filtrar manualmente esta sucursal si se busca aislar problemas de
> sucursales productivas reales.

---

## Historial de Cambios

---

Fecha Cubo/Vista Cambio

---

**2026-06** `auditoriaEtl` / Cubo y vista nuevos. Monitoreo de corridas del ETL de
`auditoriaEtlView` extracción Compaq/POS → Athena. `execution_date` y
`watermark` casteados de `VARCHAR` a `TIMESTAMP`/`DATE`;
columna `table` escapada por ser palabra reservada en
Athena/Presto

**2026-04** `cortesDiarios` Reemplazado workaround de fecha por `TRY_CAST` + exclusión
de `TORREON ARCOIRIS`. Datos históricos completos
disponibles

**2026-04** `reconciliacionCortesZ` Mismo fix que `cortesDiarios`. Datos desde 2025-11-20 en
adelante

**2026-04** `reconciliacionDiaria` Agregadas medidas de tasa 8% (IEPS) y eliminado workaround
de fecha

**2026-04** `auditoriaEfectivo` Datos completos con `TRY_CAST`. Agregadas medidas IEPS 8%

**2025-04** `ventas` Alineación de `montoSinDuplicar` e `impuestoSinDuplicar`
con reporte "Ventas por artículo por impuesto" del sistema
contable

**Pendiente** `catalogoProductos` Cobertura de SKUs alfanuméricos (actualmente solo
numéricos)

---
