# 01 - Contexto de Negocio

## Nombre de la Compañía

La compañía se llama "Los Canastos". 

Los usuarios pueden referirse a ella como:
- "Canastos"
- "Los Canastos"
- Con nombre de sucursal: "Canastos Lomas", "Los Canastos Independencia", etc.

## Sucursales Disponibles

### Sucursales en Producción (38 totales)

**Durango (sin prefijo):**
1. 20 DE NOVIEMBRE
2. ABASTOS MAYOREO
3. ABASTOS MENUDEO
4. ANALCO
5. ARRIETA
6. BACA ORTIZ
7. CAMINO REAL
8. CARRIL 2000
9. CEDIS
10. FIDEL VELAZQUEZ
11. FORESTAL
12. GUADALUPE VICTORIA
13. INDEPENDENCIA
14. JARDINES
15. LASALLE
16. LIBERTAD
17. LOMAS
18. PASTEUR
19. REX
20. SANTA MARIA
21. VICENTE GUERREO
22. VICTORIA
23. VILLA DE GUADALUPE
24. VILLAS CAMPESTRE

**Jalisco:**
25. GUADALAJARA SANTA TERE

**Sinaloa:**
26. MAZATLAN JUAREZ
27. MAZATLAN LEY DEL MAR
28. MAZATLAN MEDITERRANEO
29. MAZATLAN AQUILES
30. MAZATLAN CABO CARENA

**San Luis Potosí:**
31. SLP AMADO NERVO
32. SLP HIMALAYA
33. SLP HIMNO NACIONAL
34. SLP HIDALGO

**Coahuila:**
35. TORREON ARCOIRIS
36. TORREON FRESNO
37. TORREON LA ROSITA
38. TORREON MERCADO JUAREZ

### Sucursal de Prueba (EXCLUIR de análisis)

**DPBodega-Test** - Sucursal de pruebas, NO incluir en análisis de producción.

Siempre usar: WHERE sucursal != 'DPBodega-Test'

## Concepto Importante: CEDIS

**CEDIS (Centro de Distribución):**
- Es la bodega central de la compañía
- Concentra 70-80% del inventario total
- Reabastece a las tiendas propias y a las franquicias diariamente
- Los movimientos internos CEDIS → Tiendas NO están registrados en el sistema
- Aparece como sucursal "CEDIS" en los datos

**Tiendas:**
- Stock de exhibición/piso de venta
- Promedio: 5-50 kg por producto
- Se reabastecen desde CEDIS continuamente
- 30+ sucursales de tienda física

## Términos Críticos

**CEDIS**
Centro de Distribución (bodega central). Concentra 70-80% del inventario total y reabastece a las tiendas.

**Ventas Brutas**
Ventas SIN restar devoluciones (REM + FAC). Usar para comparar con Corte Z.

**Ventas Netas**
Ventas brutas MENOS devoluciones (Ventas Brutas - DEV - DV).

**Corte Z**
Cierre de caja diario del POS (reporte de ventas del día). Muestra ventas totales SIN restar devoluciones.

**Diferencia Sistema vs Z**
(Ventas Brutas) - (Ventas Z) - Indicador principal de sincronización entre ERP y POS.
- Positiva (+) = Sistema > Z → Posibles ventas a crédito o retrasos de sincronización
- Negativa (-) = Z > Sistema → Posibles ventas no registradas en ERP
- Cerca de 0% = Buena sincronización

**Retiros de efectivo**
Dinero retirado de caja por seguridad (típico: $2K-$10K). NO son faltantes.

**Estación COBRANZA**
Terminal para depósitos/transferencias. NO es caja de ventas, por lo que se excluye de análisis.

