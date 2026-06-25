# Agent Rules para "Los Canastos"

Esta carpeta contiene las reglas organizadas para el Agente de Cube Cloud.

## Estructura

```
rules/
├── always/              → 2 reglas que SIEMPRE están cargadas
│   ├── 01-contexto-negocio.md
│   └── 02-sintaxis-y-views.md
│
└── agent-requested/     → 6 reglas que se cargan bajo demanda
    ├── 06-view-analiticaVentas.md
    ├── 07-view-analiticaInventario.md
    ├── 08-view-analiticaCortes.md
    ├── 09-view-reconciliacionDiaria.md
    ├── 10-view-analiticaDevoluciones.md
    └── 11-errores-comunes.md
```

## Cómo usar estas reglas

### 1. Always Rules (2 archivos)

Estas reglas deben configurarse como "Always" en Cube Cloud:
- Se cargan en CADA conversación con el agente
- Contienen contexto fundamental del negocio, sintaxis básica e índice de views
- Tamaño total: ~1.5K tokens (optimizado desde ~4K)

**Cómo agregar:**
1. En Cube Cloud, ir a Settings → Agent Rules
2. Click en "Add Rule"
3. Seleccionar Type: Always
4. Copiar el contenido del archivo .md correspondiente
5. Nombrar la regla según el archivo (ej: "01 - Contexto Negocio")

### 2. Agent Requested Rules (6 archivos)

Estas reglas deben configurarse como "Agent Requested" en Cube Cloud:
- Se cargan SOLO cuando el agente detecta que son relevantes
- Cada view tiene su propio archivo completo con schema, campos, casos de uso, conceptos y errores
- Cada una tiene keywords específicos para activación

**Cómo agregar:**
1. En Cube Cloud, ir a Settings → Agent Rules
2. Click en "Add Rule"
3. Seleccionar Type: Agent Requested
4. Copiar el contenido del archivo .md correspondiente
5. En Description: Usar el texto del encabezado "Description" del archivo
6. En Prompt keywords: Usar las palabras clave listadas en el archivo
7. Nombrar la regla según el archivo (ej: "06 - View analiticaVentas")

## Comparación: Antes vs Después

| Métrica | Antes (12 reglas) | Después (8 reglas optimizadas) |
|---------|-------------------|--------------------------------|
| Tokens en contexto base | ~4K | ~1.5K (62% ↓) |
| Archivos always | 5 archivos | 2 archivos (60% ↓) |
| Archivos agent-requested | 7 archivos | 6 archivos (5 views + errores) |
| Ejemplos SQL completos | Múltiples | Eliminados |
| Emojis y símbolos | Extensivos | Eliminados |
| Información técnica de desarrollo | Incluida | Eliminada |
| Enfoque | Cubes + Views | Solo Views (usuarios) |
| Organización | Mezclado | 1 archivo por view |

## Optimizaciones Realizadas

1. Consolidación de always rules: De 5 archivos a 2 archivos consolidados
2. Índice de views en always: Solo lista simple con referencias a agent-requested
3. Un archivo por view: Cada view tiene su propio archivo completo en agent-requested
4. Eliminación de ejemplos SQL completos: Los usuarios usan UI/interfaz, no SQL directo
5. Eliminación de información técnica: Detalles sobre construcción de cubes, joins internos, primary keys
6. Eliminación de emojis y símbolos: Reducción de tokens sin pérdida de funcionalidad
7. Enfoque en interpretación: Priorizar qué significan los datos, no cómo se construyen

## Mantenimiento

Cuando necesites actualizar las reglas:
1. Edita el archivo .md correspondiente en esta carpeta
2. Copia el nuevo contenido a Cube Cloud (Settings → Agent Rules)
3. Mantén el versionado en Git para control de cambios

## Notas Importantes

Estos archivos NO se cargan automáticamente. Son documentación que debes copiar manualmente a la UI de Cube Cloud.

Esta carpeta NO afecta el modelo de datos. Cube solo lee archivos en /model/.

Revisa periódicamente las métricas de calidad en las reglas para mantenerlas actualizadas.

**Última actualización:** Diciembre 2024  
**Versión:** 5.0 (Reorganización: 2 always + 1 archivo por view en agent-requested)
