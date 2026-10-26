# El libro del tenis evolutivo

Este libro cuenta **cómo se construyó el proyecto, fase por fase**: qué
problema resuelve cada parte, la teoría que hace falta para entenderla, qué
decisiones se tomaron (y cuáles fallaron) y cómo comprobarlo con tus propias
manos. Se lee junto al código: cada capítulo dice qué archivos mirar y qué
comandos correr.

No hace falta saber de redes neuronales ni de motores de física: cada
concepto se explica desde cero la primera vez que aparece.

## Cómo leerlo

Cada fase quedó guardada en git con una **etiqueta** (`fase-0`, `fase-1`, ...).
Si una fase se corrigió después de terminarla, la corrección lleva otra
etiqueta (`fase-1.1`) y la original se conserva: así se puede comparar.
Con ella puedes volver al proyecto tal como estaba al terminar esa fase:

```bash
git checkout fase-1        # el proyecto al terminar la fase 1
pytest                     # las pruebas de esa fase
git checkout -             # volver a donde estabas
```

Así puedes leer un capítulo con el código de *ese* momento, sin las piezas
que se agregaron después. Para ver qué cambió entre dos fases:

```bash
git diff fase-0 fase-1 --stat      # qué archivos cambiaron
git diff fase-0 fase-1 -- arbitro.py
```

Cada capítulo tiene la misma estructura:

1. **Dónde estamos**: qué problema resuelve la fase y por qué va en ese orden.
2. **Teoría**: los conceptos nuevos, desde cero.
3. **Cómo está construido**: los archivos y cómo se conectan.
4. **Diario de decisiones**: qué se probó, qué falló y por qué se cambió.
5. **Pruébalo tú**: comandos y experimentos para tocar el código.
6. **Criterios de aceptación**: cómo sabemos que la fase está terminada.
7. **Puente**: qué queda sin resolver y por qué eso lleva a la fase siguiente.

## Índice

| Capítulo | Fase del plan | Etiqueta | Estado |
|---|---|---|---|
| [0. Preparación e interfaces](cap00_preparacion.md) | F0 | `fase-0` | listo |
| [1. Física y reglas](cap01_fisica_y_reglas.md) | F1 | `fase-1`, `fase-1.1` | listo |
| [2. Grabaciones y visor 2D](cap02_grabaciones_y_visor.md) | V1 | `fase-1`, `fase-1.2` | listo |
| [3. Qué es una red neuronal](cap03_red_neuronal.md) | F2a | `fase-2a` | listo |
| [4. Neuroevolución y etapa 1](cap04_neuroevolucion_etapa1.md) | F2b | `fase-2b` | listo |
| 5. Etapa 2: contra el rival programado | F3 | — | pendiente |
| 6. Etapa 3: coevolución y aptitudes A/B/C | F4 | — | pendiente |
| 7. El experimento | F5 | — | pendiente |
| 8. Métricas, gráficos y estadística | D2 + F6 | — | pendiente |
| 9. Visor 3D y humano contra IA | V2 + V3 | — | pendiente |

Las figuras se regeneran con los scripts de `docs/libro/figuras/` (por ejemplo,
`python docs/libro/figuras/figuras_cap01.py`).
