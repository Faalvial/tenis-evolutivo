# Plan del proyecto: Tenis evolutivo

> Documento de diseño para implementar con Claude Code, **fase por fase**.
> Este plan define qué se construye, en qué orden y cómo se sabe que cada parte funciona.
> Lo que se aprendió al construir cada fase está en el libro: `docs/libro/`.

---

## 0. Contexto

- **Evento:** Feria de Experimentos y Proyectos ABET 2026-II, Facultad de Ciencias, UNI.
- **Equipo:** de 3 a 6 integrantes; el autor está en 7.º ciclo (categoría 5.º–8.º ciclo). Asesor y curso: por definir. Roles en la sección 0.1.
- **Fechas clave:**
  - **6 nov 2026, 17:00:** ficha de inscripción firmada por el asesor (pide título, curso, docente, alumnos y categoría).
  - **30 nov 2026:** entrega del resumen (plantilla LaTeX) y del banner (plantilla PowerPoint).
  - **10–11 dic 2026:** feria.
- **Antecedente:** proyecto de *criaturas evolutivas* (carpeta `criaturas/`), ya terminado y con resultados de 10 semillas. Se reutilizan sus ideas y partes de su código: algoritmo genético, guardado atómico, evaluación en paralelo, script de experimentos y gráficos.
- **Plan B:** si al punto de control del **20 de noviembre** (sección 12) el tenis no tiene resultados, **se presentan las criaturas este año** y el tenis completo queda para la feria de 2027. Por eso el título de la ficha es general y cubre ambos proyectos (sección 1).

### 0.1 Equipo y roles

Cada rol es dueño de unos módulos (sección 10). Las interfaces comunes (el "controlador" y el formato de grabación) se acuerdan en F0, para que todos avancen en paralelo sin esperarse.

| Rol | Responsabilidad | Módulos |
|---|---|---|
| **R1 · Física y reglas** | Mundo, jugador, raqueta, árbitro, partidos, rivales programados, pruebas de reglas | `mundo`, `jugador`, `arbitro`, `partido`, `rivales`, `tests/` |
| **R2 · IA y entrenamiento** | Red, percepción, algoritmo genético, currículo, salón de la fama, experimentos | `red`, `percepcion`, `genetico`, `aptitud`, `entrenar`, `experimentos` |
| **R3 · Visualización y demo** | Grabaciones, visor 2D y 3D, humano contra IA, videos | `grabar`, `ver2d`, `ver3d`, `jugar` |
| **R4 · Análisis y documentos** | Métricas, gráficos, estadística, resumen LaTeX y banner | `metricas`, `graficos`, documentos |
| **R5 · Plan B (criaturas)** | Prepara en paralelo el resumen y el banner de las criaturas, por si se activa el plan B; luego apoya a R4 | `criaturas/` |
| **R6 · Coordinación e integración** | Repositorio, revisión de cambios, seguimiento del cronograma, guion y ensayo de la demo | todo (revisión) |

**Cómo repartir según el tamaño del equipo:**
- **3 personas:** R1 + R3 · R2 · R4 + R5 + R6.
- **4 personas:** R1 · R2 · R3 · R4 + R5 + R6.
- **5 personas:** R1 · R2 · R3 · R4 · R5 + R6.
- **6 personas:** un rol cada uno.

El rol R2 es el más difícil y el que tiene más riesgo. Conviene que lo tome quien tenga más interés en la IA, y que R6 lo apoye en las fases 2 a 4.

**Quién usa Claude Code.** Lo usarán 2 o 3 integrantes, entre ellos el autor:
- Esos integrantes toman los roles con más código nuevo: **R1, R2 y R3**. Si son solo 2, uno lleva R1 + R3 y el otro R2.
- El autor actúa además como **integrador (R6)**: revisa y une los cambios de todos a la rama principal.
- Los demás toman **R4 y R5**, que se apoyan en código ya existente (los gráficos de las criaturas) y en los documentos. Siguen las mismas reglas de trabajo de la sección 15, aunque programen sin Claude Code.

**Flujo de trabajo con git:**
- La rama `main` siempre funciona: nadie sube cambios directamente a ella.
- Cada integrante trabaja en una rama de su rol (`fisica`, `ia`, `visual`, `analisis`, `plan-b`) y la une a `main` con un *pull request* en GitHub.
- Antes de unir: las pruebas pasan (`pytest`) y el integrador revisa el cambio.
- Unir cambios pequeños y frecuentes (al menos una vez por semana) para evitar conflictos grandes.
- Los resultados pesados (`resultados/`, grabaciones, videos) no se suben al repositorio: se comparten por una carpeta en la nube.

---

## 1. Pregunta de investigación

**Título para la ficha de inscripción (general, sirve para el tenis y para el plan B):** *Influencia de la función de aptitud en los comportamientos emergentes de agentes virtuales evolutivos.*

**Subtítulo para el resumen y el banner, según lo que se presente:**
- Tenis: *Competir o colaborar: estrategias emergentes de agentes neuroevolutivos en un juego de tenis.*
- Plan B: *Caminar o arrastrarse: locomoción emergente de criaturas virtuales evolutivas.*

Conviene confirmar con el asesor o la organización que se puede agregar un subtítulo después de la inscripción.

**Problema.** Un algoritmo genético optimiza exactamente la métrica que se le da, no la intención de quien la diseña. En un juego entre dos agentes, la forma de premiar puede convertir a los rivales en colaboradores o producir estrategias inesperadas ("trampas").

**Pregunta.** ¿Cómo cambian las estrategias que emergen entre dos agentes que aprenden a jugar tenis según la función de aptitud con que se los evoluciona?

**Variable independiente: la función de aptitud de la etapa 3.** El detalle está en la sección 7.

| | Aptitud | Qué premia |
|---|---|---|
| A | **Ganar** | Puntos ganados menos puntos perdidos |
| B | **Pelotear** | Duración del peloteo (golpes válidos por punto) |
| C | **Precisión** | Tiros válidos que caen profundo en el campo rival |

**Variables controladas.** Física, reglas, cuerpo del jugador, arquitectura de la red, parámetros del algoritmo genético, etapas 1 y 2 de entrenamiento y semillas. Todo es idéntico entre tratamientos.

**Variables dependientes.** Las métricas de la sección 8: % de victorias contra un rival de referencia, duración del peloteo, % de golpes válidos, profundidad de los tiros y tipo de punto (ganador o error).

**Hipótesis:**
- **H1:** A produce jugadores agresivos, con peloteos cortos y más victorias contra el rival de referencia.
- **H2:** B produce colaboración: peloteos largos, golpes suaves al centro y pocas victorias contra el rival de referencia, aunque nadie les pidió "no ganar".
- **H3:** C produce tiros profundos con más errores propios: arriesga más que A.
- **H4 (exploratoria):** en los tres tratamientos aparecen estrategias no previstas, que se documentarán como hallazgos.

**Objetivo general.** Implementar un simulador de tenis 2D con visualización 3D donde dos agentes neuroevolutivos aprenden a jugar, y medir cómo distintas funciones de aptitud producen distintas estrategias.

**Objetivos específicos:**
1. Implementar la física y las reglas de un tenis simplificado en vista lateral.
2. Implementar agentes controlados por redes neuronales cuyos pesos evoluciona un algoritmo genético.
3. Diseñar un entrenamiento por etapas (currículo) que resuelva el problema de que al inicio nadie toca la pelota.
4. Comparar tres funciones de aptitud con 10 réplicas cada una (mínimo 5) y analizar los resultados estadísticamente.
5. Visualizar los partidos en 3D con cámara giratoria y permitir que un humano juegue contra la IA.

---

## 2. Alcance

**Incluido:**
- Simulación física **2D en vista lateral** (plano X–Y) con gravedad.
- **Visualización 3D** de los partidos grabados, con cámara giratoria.
- Neuroevolución: pesos de una red de tamaño fijo evolucionados por un algoritmo genético.
- Currículo de 3 etapas, con "salón de la fama" en la etapa 3.
- Experimento principal A/B/C, gráficos, tabla y pruebas estadísticas.
- Modo humano contra IA.

**Excluido (trabajo futuro):**
- 3D real: moverse en profundidad y pelota en tres ejes (PyBullet o MuJoCo).
- Que también evolucione la estructura de la red (NEAT).
- Efecto de la pelota (spin), sets y ventajas.

**Experimento secundario opcional** (solo si sobra tiempo): matriz de campeones de distintas generaciones jugando todos contra todos, con y sin salón de la fama. Sirve para estudiar ciclos y olvido.

---

## 3. Diseño del juego

Los valores numéricos son **iniciales y ajustables**. Van en `config.py` y se calibran en la fase 1.

> **Cambios tras F1** (el porqué de cada uno está en `docs/libro/cap01_fisica_y_reglas.md`, sección 1.4):
> - **Modelo de golpe:** si la pelota toca la raqueta durante un golpe, sale perpendicular a la raqueta (ángulo al empezar el golpe) con una rapidez que depende solo de la fuerza. El choque 100 % físico era caótico (el mejor rival devolvía el 65 %).
> - **Sin paredes invisibles:** los jugadores se mantienen en su mitad con un límite explícito de posición (las paredes se atravesaban).
> - **Espacio detrás del fondo** (400) donde los jugadores pueden pararse; **zona prohibida junto a la red** de 62 para que la raqueta no la cruce.
> - **Tiempo máximo por punto: 30 s** (no 20). **Subpasos: 2.** Rango de la raqueta: −1,4 a −0,4 rad.
> - **Realismo progresivo del golpe** (sección 1.6 del capítulo 1): encendidas la capa 1 (la pelota que llega aporta el 30 % de su rapidez) y la capa 2 (punto dulce: hasta −30 % en los extremos); la capa 3 (ángulo al tocar) queda apagada porque vuelve el golpe caótico. Si en la etapa 1 nadie aprende, plan B: currículo de física (capas apagadas al inicio); en la etapa 3 la física es siempre la final.
> - **F2b:** la red tiene 14 entradas (las 12 de la percepción + la posición de la pelota respecto de la raqueta) y 156 pesos; el golpe necesita superar un umbral de 0,3. El lanzapelotas apunta con el tiro parabólico. Se corrigió una regla del árbitro (segundo bote del saque fuera de la cancha). Detalle: capítulo 4.

### 3.1 Mundo (unidades de pymunk)
- **Cancha:** ancho 1200; red en x = 600, de 60 de alto; suelo en y = 0; gravedad −900.
- **Paredes invisibles** en la red y en los extremos que **solo chocan con los jugadores**: cada uno queda confinado en su mitad. La pelota no choca con ellas (se usan filtros de colisión de pymunk).
- **Techo de juego:** si la pelota supera una altura máxima (por ejemplo 600), es "fuera" para quien la golpeó.
- **Paso de tiempo fijo:** dt = 1/60 s. Los jugadores deciden cada 2 pasos (30 Hz) para ahorrar cómputo.

### 3.2 Pelota
- Círculo de radio 8, elasticidad alrededor de 0,75 y algo de fricción.
- Velocidad máxima limitada, para evitar que atraviese la raqueta (ver 3.4).

### 3.3 Jugador (cubo)
- Cuerpo dinámico de 40 × 40 con **rotación bloqueada**: el cubo nunca se voltea.
- **Movimiento horizontal:** velocidad = salida "mover" × velocidad máxima.
- **Salto:** impulso vertical, solo si está tocando el suelo.

### 3.4 Raqueta
- Cuerpo separado (rectángulo largo de 50 × 8) unido al cubo con un pivote y movido por un motor con control proporcional, igual que las articulaciones de las criaturas.
- **Ángulo objetivo:** lo decide la red en todo momento, dentro de un rango limitado.
- **Golpe (swing):** si la salida "golpe" supera un umbral, la raqueta hace un giro rápido cuya fuerza depende del valor de esa salida. Después hay un tiempo de recarga de unos 0,4 s.
- **Anti-atravesamiento:** raqueta gruesa, velocidad máxima de la pelota y, si hace falta, subpasos de física durante el golpe. Hay que verificarlo con una prueba automática.

### 3.5 Reglas (árbitro)
- **Saque neutro automático:** cada punto empieza con un lanzamiento desde lo alto de la red hacia el campo de uno de los jugadores, alternando, con velocidad aleatoria dentro de un rango. Así se evita tener que aprender a sacar y se elimina la trampa de "nunca sacar".
- **Pierde el punto el jugador que:**
  - deja botar la pelota dos veces en su campo;
  - golpea la pelota y esta bota primero en su propio campo, lo que incluye pegarle a la red;
  - golpea la pelota y esta cae fuera de la cancha o supera el techo.
- **Golpe válido:** cruza la red y bota dentro del campo rival.
- **Tiempo máximo por punto** de 20 s: el punto se anula y se registra como "punto anulado" (posible indicio de una trampa).
- **Partido de evaluación:** un número fijo de puntos (por ejemplo 6), con los saques alternados.

### 3.6 Simetría
- El jugador derecho percibe el mundo **reflejado en espejo**, y sus acciones horizontales se invierten. Así una misma red puede jugar en cualquier lado y los dos lados son comparables.

---

## 4. Agente: la red neuronal

- **Red de propagación hacia adelante:** entradas → 8 neuronas ocultas (tanh) → salidas (tanh). El tamaño oculto va en `config.py`.
- **Entradas** (unas 12), normalizadas a [−1, 1] y en el marco espejado:
  - pelota: x, y, vx, vy;
  - propio: x, y, vy, si está en el suelo, ángulo de la raqueta, recarga del golpe;
  - rival: x, y.
- **Salidas** (4): mover (−1 a 1), saltar (si > 0), ángulo objetivo de la raqueta y golpe (si > umbral, la fuerza depende de su valor).
- **Genoma:** todos los pesos y sesgos en una lista, unos 140 números reales.
- **Implementación:** medir si NumPy o Python puro es más rápido para una red tan pequeña, y elegir el más rápido.

---

## 5. Algoritmo genético

Se adapta `genetico.py` de las criaturas:
- **Genes reales sin límite fijo:** mutación gaussiana sobre cada peso (σ entre 0,1 y 0,2, por calibrar), con recorte suave a ±5.
- **Selección por torneo** y **elitismo**, como antes.
- **Cruce por neurona:** el hijo hereda **completas** las conexiones de entrada de cada neurona oculta de uno de los dos padres. Así se respeta la estructura de la red; se compara con el cruce uniforme, y queda la opción de desactivar el cruce si perjudica.
- **Población y generaciones:** por calibrar según el presupuesto de cómputo (sección 11). Referencia inicial: población de 60.
- **Reproducibilidad:** toda la aleatoriedad (algoritmo genético, saques, lanzapelotas) depende de la semilla de cada corrida.

---

## 6. Entrenamiento por etapas (currículo)

Resuelve dos problemas: que al principio nadie toca la pelota y que la coevolución es inestable.

| Etapa | Rival | Aptitud (común a todos los tratamientos) | Pasa a la siguiente cuando |
|---|---|---|---|
| 1. Lanzapelotas | Máquina que lanza pelotas a su campo | +1 por toque, +3 si cruza la red, +5 si bota dentro; pequeño premio por acercarse a la pelota cuando no la toca | El campeón devuelve bien ≥ 60 % de las pelotas, o se alcanza el máximo de generaciones |
| 2. Rival programado | Jugador escrito a mano que sigue la pelota con error y potencia aleatorios | Puntos ganados + 0,2 × devoluciones válidas | Gana ≥ 40 % de los puntos, o se alcanza el máximo de generaciones |
| 3. IA contra IA | 2 rivales al azar de la población actual + 2 del salón de la fama, jugando en ambos lados | **A, B o C** según el tratamiento | Número fijo de generaciones |

- **Equidad:** en cada generación, todos los individuos enfrentan los mismos lanzamientos y saques. Estos cambian entre generaciones para no memorizar.
- **Salón de la fama:** se guarda el campeón de cada generación de la etapa 3, y los rivales del salón se eligen al azar entre ellos.
- **Bifurcación:** para cada semilla, las etapas 1 y 2 se entrenan **una sola vez**. La población resultante (**población base**) se copia y desde ahí se evoluciona por separado con A, B y C. Así los tres tratamientos parten de jugadores idénticos y solo difieren en la aptitud. Es el control experimental clave, y además ahorra tiempo de cómputo.

---

## 7. Funciones de aptitud del experimento (etapa 3)

Se definen **antes** de ver resultados y no se cambian después. Si se ajustan, se documenta.

- **A · Ganar:** (puntos ganados − puntos perdidos) / puntos jugados.
- **B · Pelotear:** promedio de golpes válidos por punto en los partidos del jugador. Los dos jugadores reciben el mismo valor (aptitud compartida).
- **C · Precisión:** fracción de los golpes propios que son válidos y caen en el tercio profundo del campo rival, menos la fracción de golpes propios que terminan en error.
- **Puntos anulados** (tiempo máximo agotado): no suman ni restan en A y C. En B se registran aparte, para detectar si "congelar" la pelota se vuelve una trampa.

> **Ajustes documentados (decididos por el equipo tras la corrida corta de F4, capítulo 6 del libro):**
> - **C:** una pelota que el jugador no devuelve (le bota dos veces) cuenta también como intento fallido. Con la definición original, no golpear nunca daba C = 0 y la evolución aprendió a no jugar (trampa documentada como hallazgo, H4).
> - **B:** los puntos anulados cuentan en el promedio (un peloteo largo que llega al tiempo máximo es lo que B premia) y su fracción se informa aparte.
> - **Etapa 3:** 4 rivales de la población + 4 del salón (en vez de 2 + 2) y mutación σ = 0,05 (en vez de 0,15), para evitar la deriva por ruido. Igual en los tres tratamientos.
> - **Métricas (sección 8):** la batería de referencia es de 300 puntos (en vez de 100), para bajar el ruido de ±5 a ±3 puntos porcentuales.

---

## 8. Métricas y evaluación

Las métricas se calculan **igual para todos los tratamientos**, siempre contra la misma **batería de referencia**, y no dependen de la aptitud usada:
- **Batería:** el campeón juega 100 puntos con saques fijos (siempre los mismos) contra el rival programado de la etapa 2.
- **Métricas:**
  1. % de puntos ganados contra el rival de referencia;
  2. duración media del peloteo (golpes válidos por punto);
  3. % de golpes válidos;
  4. profundidad media de los tiros (distancia a la red de los botes válidos);
  5. % de puntos terminados por golpe ganador o por error propio;
  6. % de puntos anulados.
- **Frecuencia:** cada 10 generaciones y al final, para ahorrar cómputo.
- **Estilo de juego:** mapa de calor de dónde botan los tiros de cada tratamiento, que es una buena imagen para el banner.

---

## 9. Diseño experimental y análisis

- **Tratamientos:** A, B y C. **Réplicas:** 10 semillas (mínimo 5 si el cómputo no alcanza).
- Para cada semilla: etapas 1 y 2 una vez, y luego tres ramas de etapa 3.
- **Estadística:**
  - promedio ± desviación estándar por tratamiento;
  - prueba **U de Mann–Whitney** entre pares de tratamientos con `scipy`, reportando el valor p. No asume datos normales y funciona con pocas réplicas.
- **Gráficos** (paleta fija por tratamiento, igual que en las criaturas):
  1. curvas de cada métrica por generación (promedio ± desviación estándar);
  2. diagramas de cajas de las métricas finales;
  3. mapas de calor de los botes por tratamiento;
  4. "cronofotografía" o secuencia de un punto típico de cada tratamiento.
- **Tabla final** en Markdown y CSV, lista para el banner.
- **Experimento secundario (opcional):** campeones cada 25 generaciones jugando todos contra todos, mostrado en un mapa de calor, con y sin salón de la fama.

---

## 10. Arquitectura del código

Proyecto nuevo `tenis_evolutivo/`, separado de `criaturas/`.

```
tenis_evolutivo/
├── config.py            # TODOS los parámetros (física, reglas, red, AG, currículo)
├── mundo.py             # espacio pymunk: cancha, red, paredes, pelota
├── jugador.py           # cubo + raqueta + motor; aplica acciones
├── red.py               # red neuronal: genoma <-> pesos, propagación
├── percepcion.py        # construye entradas normalizadas y espejadas
├── arbitro.py           # reglas: botes, golpes válidos, puntos, fin del punto
├── partido.py           # simula un partido entre dos "controladores"; registra eventos
├── rivales.py           # lanzapelotas y rival programado (sin IA)
├── aptitud.py           # aptitudes de etapas 1-2 y de A/B/C
├── metricas.py          # batería de referencia y métricas de la sección 8
├── genetico.py          # selección, cruce por neurona, mutación, elitismo
├── entrenar.py          # currículo de 3 etapas, salón de la fama, paralelo, guardado
├── experimentos.py      # semillas × tratamientos, bifurcación, reanudable
├── graficos.py          # gráficos, tabla y pruebas estadísticas
├── grabar.py            # guarda la repetición de un partido (posiciones por fotograma)
├── ver2d.py             # visor pygame (depuración rápida)
├── ver3d.py             # visor Ursina con cámara giratoria (reproduce grabaciones)
├── jugar.py             # humano contra IA (teclado)
├── tests/               # pruebas automáticas (pytest)
├── README.md            # uso + guía de estudio con fuentes
└── CLAUDE.md            # instrucciones para Claude Code (ver sección 15)
```

**Principios de diseño:**
- **"Controlador" común:** un objeto que recibe percepciones y devuelve acciones. La IA, el rival programado y el humano lo implementan igual, así que `partido.py` no sabe quién juega.
- **Separar simulación y dibujo:** el entrenamiento nunca dibuja. Los visores reproducen **grabaciones** (`grabar.py`), de modo que el 3D no depende de la física ni la frena.
- **Formatos:** JSON para estados, corridas y grabaciones, con guardado atómico. CSV para el historial.
- **Reanudable:** entrenamientos y experimentos continúan donde quedaron, como en las criaturas.

---

## 11. Rendimiento y presupuesto de cómputo

- **Paralelismo:** `multiprocessing.Pool` evaluando individuos (o partidos) en paralelo.
- **Máquina de desarrollo:** Intel Core i7-1255U, 10 núcleos (12 procesadores lógicos), 16 GB de RAM.
- **Referencia medida:** el experimento de las criaturas (30 corridas × 150 generaciones × 100 individuos = 450 000 simulaciones de 10 s) tardó unos **20 minutos** en esa máquina, es decir, unas **375 simulaciones por segundo** usando todos los núcleos.
- **Estimación para el tenis** (a confirmar midiendo en F1): un partido de 6 puntos simula unas 3 a 4 veces más tiempo que una prueba de criatura, más el costo de la red.
  - población 60 × 4 rivales = 240 partidos por generación: unos **2–3 s por generación**;
  - 200 generaciones: unos 7–10 min por rama, y lo mismo para las etapas 1–2 de cada semilla;
  - **10 semillas × (etapas 1–2 + 3 ramas): unas 4 a 6 horas.** Cabe en una noche, o en dos tandas.
- **Precauciones:**
  - la memoria estaba al 80 % en la captura: cerrar programas pesados (navegador, juegos) antes de correr experimentos largos;
  - una laptop delgada reduce su velocidad al calentarse: conectarla al cargador y en modo "máximo rendimiento";
  - la laptop gamer del integrante puede usarse para correr parte de las semillas en paralelo (cada máquina corre semillas distintas y luego se juntan las carpetas `resultados/`).
- **Medición de F1** (nube, Xeon 2,1 GHz, un núcleo): un partido de 6 puntos entre dos rivales programados tarda **≈ 0,25 s** (75 s de juego simulado); es el peor caso, con peloteos largos. Jugadores que fallan rápido: ≈ 0,05 s.
  - Peor caso: 240 partidos × 0,25 s = 60 s de CPU por generación → ≈ 7,5 s con 8 núcleos → 25 min por rama de 200 generaciones → **≈ 17 h** para 10 semillas × 4 ramas.
  - Caso típico temprano: ≈ 2 s por generación → **≈ 4 h**.
  - Falta sumar el costo de la red (se mide en F2b). Probablemente haga falta aplicar recortes: decidir al terminar F2b, con números reales. Detalle en el capítulo 1 del libro, sección 1.9.
- **Medición de F2b:** la red es el 6 % del tiempo de un partido (Python puro: 8 µs por decisión; NumPy: 4,6 µs; se queda Python puro). La etapa 1 cuesta 1–2 s por generación con 4 procesos y terminó en 36 generaciones (semilla 1). Detalle: capítulo 4 del libro.
- **Medición del experimento de ejemplo (F5):** con 4 núcleos, el currículo tarda 4,5–8 min por semilla y cada rama de la etapa 3 ≈ 10 min cada 60 generaciones (con 4 + 4 rivales). Una semilla completa (200 generaciones) ≈ 1 h 50 min con 4 núcleos; en la laptop de 10 núcleos ≈ 50 min. **10 semillas ≈ 8–9 h en una laptop o 4–5 h en dos; 5 semillas ≈ 4 h.** Detalle: capítulo 7 del libro.
- **Si no alcanza, en este orden:** bajar a 5 semillas, reducir los puntos por partido, reducir la población y luego las generaciones.
- **Optimizaciones:** decidir cada 2 pasos de física, evaluar las métricas cada 10 generaciones y elegir la red más rápida (NumPy o Python puro).

---

## 12. Fases de implementación

Cada fase termina con **criterios de aceptación** verificables. No se pasa a la siguiente sin cumplirlos.

Con equipo, el trabajo avanza en **tres líneas paralelas**. La línea de IA es la ruta crítica: si se atrasa, se atrasa todo. Las fechas incluyen holgura por las prácticas calificadas; cuando el equipo conozca sus fechas de evaluación, conviene marcarlas aquí y mover las tareas pesadas fuera de esas semanas.

**Línea 1 · Física e IA (R1, R2) — ruta crítica**

| Fase | Fechas | Contenido | Criterios de aceptación |
|---|---|---|---|
| **F0** Preparación (todos) | 26–28 oct | Repositorio en GitHub, entorno virtual, `requirements.txt`, pytest, CLAUDE.md; **acordar las interfaces** del controlador y de la grabación | Todos clonan el repositorio y `pytest` corre en sus máquinas |
| **F1** Física y reglas (R1) | 28 oct–3 nov | mundo, jugador, raqueta, árbitro, partido, rival programado | Dos rivales programados pelotean; las pruebas de reglas pasan (doble bote, red, fuera, golpe válido); la pelota no atraviesa la raqueta en 1000 golpes de prueba; tiempo de un partido medido |
| **F2a** Aprender redes (R2) | 28 oct–3 nov, en paralelo con F1 | Ejercicio guiado de neuroevolución sin física: una red pequeña que aprende a "seguir un punto" en pantalla. Lecturas de la sección 17 | El integrante explica con sus palabras qué es un peso, una neurona y la propagación hacia adelante; el ejercicio aprende |
| — | **6 nov** | **Inscripción** con el título general y el asesor | Ficha enviada |
| **F2b** Red + AG + etapa 1 (R2) | 3–9 nov | red, percepción con espejo, `genetico.py`, lanzapelotas, guardado y reanudación | La aptitud de la etapa 1 sube; el campeón devuelve ≥ 60 % de las pelotas |
| **F3** Etapa 2 (R2) | 9–13 nov | Entrenamiento contra el rival programado | El campeón gana ≥ 40 % de los puntos contra el rival programado |
| **F4** Etapa 3 (R2) | 13–18 nov | Coevolución, salón de la fama, aptitudes A/B/C, bifurcación | Una corrida corta de cada tratamiento termina sin errores; se ven diferencias de estilo en `ver2d.py` |
| **F5** Experimento (R2) | 18–22 nov | `experimentos.py` completo, corridas largas (de noche, repartidas en dos laptops si hace falta) | Todas las corridas guardadas |
| **Punto de control** (todos) | **20 nov** | ¿F4 terminada y F5 en curso? | **Sí:** se sigue con el tenis. **No:** se activa el **plan B** (criaturas este año, tenis en 2027) |

**Línea 2 · Visualización y demo (R3)**

| Fase | Fechas | Contenido | Criterios de aceptación |
|---|---|---|---|
| **V1** Grabaciones + 2D | 28 oct–5 nov | `grabar.py` y `ver2d.py`, probados con partidos entre rivales programados | Se graba y se reproduce un partido |
| **V2** 3D básico | 5–15 nov | `ver3d.py`: cancha, cubos, pelota, sombra y cámara giratoria | Una grabación se ve en 3D en las dos laptops (incluida la gamer) |
| **V3** Humano contra IA | 15–25 nov | `jugar.py` en 2D (luego en 3D) | Una persona juega contra el rival programado y luego contra un campeón |
| **V4** Pulido + videos | 1–7 dic | Marcador, rotación automática, guion de la demo, videos y código QR | Demo estable de 10 min sin fallos; videos de respaldo |

**Línea 3 · Análisis, documentos y plan B (R4, R5, R6)**

| Fase | Fechas | Contenido | Criterios de aceptación |
|---|---|---|---|
| **D1** Plan B listo | 28 oct–15 nov | Borrador del resumen y del banner de las **criaturas**, con sus resultados reales | Borrador revisado por el asesor |
| **D2** Métricas y gráficos | 5–18 nov | `metricas.py` (batería de referencia) y `graficos.py`, probados con datos de corridas cortas | Gráficos y tabla se generan automáticamente |
| **D3** Marco teórico | 5–20 nov | Secciones del resumen y del banner que no dependen de resultados: introducción, conceptos previos, metodología | Textos listos para insertar resultados |
| **F6** Análisis final | 22–25 nov | Gráficos, estadística y tabla con los resultados del experimento | Resultados listos para los documentos |
| **F8** Documentos | 25–30 nov | Resumen (LaTeX) y banner (PowerPoint) del proyecto que se presente | **Entregados el 30 nov** |

**Cierre (todos):** ensayo de la explicación de 2 minutos y de las preguntas del jurado el 8–9 de diciembre; feria el 10–11 de diciembre.

---

## 13. Visualización y demo

- **`ver2d.py` (pygame):** rápido y simple, para depurar durante todo el desarrollo.
- **`ver3d.py` (Ursina):**
  - el plano X–Y de la simulación se dibuja en 3D (z = 0 para jugadores y pelota) sobre una cancha con profundidad, red y líneas;
  - cámara orbital con el mouse (`EditorCamera`) y modo de rotación automática para la feria;
  - **sombra bajo la pelota** para percibir la profundidad;
  - marcador, tratamiento (A/B/C) y generación en pantalla;
  - reproduce grabaciones a velocidad normal o lenta.
- **`jugar.py`:** humano contra el campeón (flechas para moverse, espacio para saltar, una tecla para golpear). Se empieza en 2D y se lleva a 3D si hay tiempo.
- **Guion de la demo:**
  1. generación 0 contra generación final (se ve el aprendizaje);
  2. A contra B lado a lado (competir o colaborar);
  3. reto al público: humano contra IA.
- **Respaldo:** videos grabados de cada momento, enlazados con un código QR en el banner.

---

## 14. Riesgos y mitigaciones

| Riesgo | Señal | Mitigación |
|---|---|---|
| Nadie aprende a tocar la pelota | La aptitud de la etapa 1 no sube | Más premio por acercarse a la pelota, raqueta más grande, lanzamientos más fáciles al inicio |
| La pelota atraviesa la raqueta | Toques que no se registran | Raqueta gruesa, velocidad máxima de la pelota, subpasos de física, prueba automática |
| Coevolución inestable o con ciclos | Las métricas contra el rival de referencia oscilan | Salón de la fama, más rivales por evaluación |
| Trampas que rompen el experimento | Muchos puntos anulados, pelotas "congeladas" | Revisar las reglas; documentar la trampa como hallazgo |
| Cómputo insuficiente | Fase 5 lenta | Orden de recortes de la sección 11 |
| Ursina falla en la laptop de la feria | Errores de gráficos | Probarlo en la laptop gamer en V2 (antes del 15 nov); respaldo con `ver2d.py` y videos |
| Falta de tiempo | Punto de control del 20 nov no cumplido | Plan B: presentar las criaturas, tenis en 2027 |
| Poca experiencia con redes neuronales | F2b se atrasa | Fase F2a de aprendizaje; R6 apoya a R2 |
| Conflictos al trabajar en equipo | Cambios que rompen el código de otro | Repositorio con ramas por rol, revisión antes de unir, pruebas que deben pasar, interfaces acordadas en F0 |
| Prácticas calificadas | Semanas sin avance | Marcar las fechas en el cronograma y adelantar trabajo; la holgura del plan B cubre una semana perdida |

---

## 15. Instrucciones para Claude Code

Este texto puede copiarse a `CLAUDE.md`:

- Trabajar **una fase a la vez** (sección 12) y detenerse al cumplir sus criterios de aceptación para que el equipo revise.
- **Trabajo en equipo:** cada integrante trabaja en una rama de git de su rol y solo modifica sus módulos (sección 0.1). Si hace falta cambiar una interfaz común (el controlador o el formato de grabación), avisar y no hacerlo sin acuerdo del equipo. Antes de unir una rama, todas las pruebas deben pasar.
- **No todos usan Claude Code:** el código debe poder entenderlo y modificarlo a mano cualquier integrante. Nada de "magia": funciones cortas, nombres claros en español y comentarios que expliquen el porqué.
- Agregar a `.gitignore` las carpetas de resultados, grabaciones, videos y los archivos de estado.
- **Objetivo de aprendizaje:** el equipo quiere entender cada concepto, y tiene poca experiencia con redes neuronales: explicarlas desde cero cuando aparezcan. El código debe ir **comentado en español**, explicando el porqué y no solo el qué. Cada concepto nuevo se agrega al README con una fuente de estudio.
- Todos los parámetros van en `config.py`; nunca números mágicos en el código.
- No cambiar las aptitudes A/B/C ni las métricas de la sección 8 sin preguntar: son el diseño experimental.
- Escribir pruebas (`pytest`) para las reglas del árbitro y para la reproducibilidad: la misma semilla debe dar el mismo resultado.
- El entrenamiento nunca dibuja; los visores solo reproducen grabaciones.
- Mantener todo reanudable y con guardado atómico.
- Medir tiempos al terminar F1 y actualizar el presupuesto de la sección 11.
- Si un criterio de aceptación no se cumple tras ajustes razonables, explicar el problema y proponer opciones en lugar de seguir adelante.

---

## 16. Entregables de la feria

**Ficha de inscripción (6 nov):** título general (sección 1), curso, docente asesor, alumnos (de 3 a 6, con código, correo y celular) y categoría. Si el equipo mezcla ciclos, confirmar qué categoría corresponde.

**Resumen (plantilla LaTeX, 30 nov):**
- Resumen en español y en inglés, con palabras clave: *algoritmos genéticos, neuroevolución, coevolución, función de aptitud, comportamiento emergente*.
- **1. Introducción:** problema, motivación y objetivos (sección 1).
- **2. Conceptos previos:** algoritmo genético, neuroevolución, coevolución competitiva y salón de la fama, función de aptitud y trampas (specification gaming).
- **3. Análisis:** diseño del juego, currículo, tratamientos, métricas y resultados con estadística.
- **4. Observaciones:** estrategias y trampas observadas, y limitaciones.
- **5. Conclusiones** y referencias.

**Banner (plantilla PowerPoint, 30 nov):** resumen, introducción (problema, estado del arte y objetivos), marco teórico, metodología (diagrama del currículo y de la bifurcación), resultados y discusiones (curvas, diagramas de cajas, mapas de calor y capturas 3D), de 3 a 6 conclusiones, bibliografía, agradecimientos y código QR a los videos.

**Demo (10–11 dic):** laptop con `ver3d.py` y `jugar.py`, videos de respaldo y, de ser posible, un proyector o una pantalla grande.

---

## 17. Fuentes de estudio por concepto

- **Algoritmos genéticos:** *The Nature of Code*, cap. 9 — https://natureofcode.com/genetic-algorithms/
- **Redes neuronales desde cero (para F2a):** serie de videos *Neural Networks* de 3Blue1Brown (YouTube; muy visual, empezar por los dos primeros capítulos) y *The Nature of Code*, cap. 10 — https://natureofcode.com/neural-networks/
- **Neuroevolución:** *The Nature of Code*, cap. 11 — https://natureofcode.com/neuroevolution/
- **Criaturas que compiten (antecedente directo):** K. Sims, "Evolving 3D Morphology and Behavior by Competition", *Artificial Life IV*, 1994 — https://gpbib.pmacs.upenn.edu/gp-html/alife94_sims.html
- **Coevolución competitiva y salón de la fama:** C. Rosin y R. Belew, "New Methods for Competitive Coevolution", *Evolutionary Computation*, 1997. Resumen: https://research.cs.wisc.edu/areas/ai/aisem/abstracts/1995.2.summer/rosin.html. Revisión del área: https://arxiv.org/pdf/1506.05082
- **Trampas de la evolución:** Lehman et al., "The Surprising Creativity of Digital Evolution", 2018 — https://arxiv.org/abs/1803.03453
- **Estrategias emergentes entre agentes que compiten (ejemplo moderno):** OpenAI, "Emergent Tool Use From Multi-Agent Autocurricula", 2019 — https://openai.com/index/emergent-tool-use y https://arxiv.org/pdf/1909.07528
- **Física:** documentación de Pymunk — https://www.pymunk.org/en/latest/overview.html
- **Visualización 3D:** Ursina — https://pypi.org/project/ursina/
- **Evaluación en paralelo:** `multiprocessing` — https://docs.python.org/3/library/multiprocessing.html

---

## 18. Decisiones pendientes

- [ ] Asesor, curso, integrantes (de 3 a 6) y asignación de roles.
- [ ] Confirmar el título general antes del 6 de noviembre, y si se puede agregar un subtítulo después.
- [ ] Fechas de las prácticas calificadas de cada integrante, para marcarlas en el cronograma.
- [ ] Probar el visor 3D en la laptop gamer (V2).
- [x] Valores numéricos de física y reglas: calibrados en F1 (ver capítulo 1 del libro).
- [ ] Número final de semillas (10 o 5) según el tiempo medido en F1.
- [ ] Si se hace el experimento secundario (matriz de campeones).
