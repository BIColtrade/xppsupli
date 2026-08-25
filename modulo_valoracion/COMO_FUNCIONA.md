# SUPLI PERFORMANCE — Guía de uso

> **SUPLI PERFORMANCE** es el nombre del módulo de valoración de SUPLI OS.

Esta guía explica, paso a paso y sin tecnicismos, cómo se usa el módulo. Está pensada para que cualquier persona del equipo (People, Líderes, Colaboradores, CEO) entienda qué hacer y dónde hacerlo.

---

## 1. ¿Quién puede hacer qué?

El módulo tiene 5 tipos de usuarios. Cada uno ve cosas distintas:

| Rol | Qué puede hacer |
|---|---|
| **Admin People** | Acceso total: crea ciclos, asigna evaluadores, ve todos los resultados, gestiona jerarquía. |
| **BI / Tech** | Configura preguntas, competencias y plantillas técnicas. |
| **CEO** | Ve todos los resultados de la compañía (solo lectura). |
| **Líder** | Ve los resultados de las personas que tiene a su cargo. |
| **Colaborador** | Ve solamente su propio resultado y responde las evaluaciones asignadas. |

> Tu rol se define con dos cosas: **tipo de usuario** (colaborador/líder/admin) y **área** (People, BI, Tecnología, CEO, Trade, Comercial, etc.). Por ejemplo, si eres `admin` + área `people`, eres Admin People. Si tu área es `ceo`, eres CEO.

---

## 2. PASO A PASO — Cómo arrancar el módulo desde cero

### PASO 1 — Crear los usuarios

> 👤 Lo hace: **Admin People**
> 📍 Donde: pantalla **"Usuarios"** del menú principal

1. Entras a **Usuarios** y le das clic en **"+ Crear usuario"**.
2. Llenas los datos básicos: nombre, apellido, correo, contraseña inicial.
3. Eliges el **Tipo de usuario**:
   - `Colaborador` → quien va a ser evaluado pero no evalúa a nadie.
   - `Líder` → tiene personas a cargo.
   - `Admin` → permisos administrativos.
4. Eliges el **Área**: Trade, People & Cultura, Comercial, Logística, Tecnología, BI, CEO, Finanzas, etc.
5. Guardas. Listo, el usuario ya existe en el sistema.

**¿Tienes muchos usuarios?** Hay un botón para **importar desde Excel**: descargas la plantilla, la llenas con todos los usuarios y la subes. El sistema los crea de un solo golpe.

---

### PASO 2 — Definir las Competencias (categorías internas)

> 👤 Lo hace: **Admin People** o **BI/Tech**
> 📍 Donde: módulo Valoración → tarjeta **"Competencias"**

Las competencias son las **categorías internas** que agrupan las preguntas. Por ejemplo:
- A. CULTURA
- B. ESTRUCTURA OPERACIONAL
- C. LIDERAZGO
- D. EJECUCIÓN
- E. PRINCIPIOS SUPLI OS

**Importante:** estas categorías son solo para uso interno (para reportar y agrupar resultados). **El evaluador NUNCA las ve** al momento de calificar. Solo aparecen en los reportes finales.

Para crear una competencia, le das clic en **"+ Nueva competencia"**, pones el código (A, B, C…), el nombre y guardas.

---

### PASO 3 — Crear las Preguntas

> 👤 Lo hace: **Admin People** o **BI/Tech**
> 📍 Donde: módulo Valoración → tarjeta **"Preguntas"**

Esta es la parte más importante de la configuración. Aquí está el banco de preguntas que se van a usar en todas las evaluaciones.

Para cada pregunta defines:
- **Competencia**: a qué categoría interna pertenece (A, B, C…).
- **Enunciado**: la pregunta tal como la va a leer el evaluador. Ejemplo: *"El líder promueve los valores de SUPLI OS en su equipo."*
- **Tipo de evaluación**: ¿esta pregunta aplica para **Liderazgo** o para **Operativo/Táctico**?
- **Tipo de pregunta**:
  - `Escala 1-5` → el evaluador elige entre los 5 niveles (Es un referente, Está consolidado, En desarrollo, Requiere acompañamiento, Requiere intervención).
  - `Abierta` → el evaluador escribe texto libre (no califica).
- **Peso**: qué tan importante es esta pregunta respecto a las otras (default 1.0).
- **Obligatoria**: si es sí, el evaluador no puede enviar sin responderla.
- **Activa**: si está activa, se usa en las evaluaciones; si no, queda guardada pero no aparece.

> 💡 Normalmente tendrás dos bloques separados: 30 preguntas para Liderazgo y 30 para Operativo. Una sola pregunta puede ser para ambos si la duplicas.

---

### PASO 4 — Definir la Jerarquía (quién manda a quién)

> 👤 Lo hace: **Admin People**
> 📍 Donde: módulo Valoración → tarjeta **"Jerarquía / Cargos"**

Aquí le dices al sistema:
- ¿Cuál es el **cargo** real de cada persona? (Coordinador, Jefe, Director, CEO, Asesor, Analista, etc.)
- ¿Quién es el **jefe directo** de cada persona?

La jerarquía es **dinámica**: una persona puede ser jefe de 100 personas, y otra persona puede ser su jefe a ella. No depende del rol, lo defines tú manualmente.

**Ejemplo:**
- Pedro (Asesor) → su jefe directo es **Julian**
- María (Asesor) → su jefe directo es **Julian**
- Julian (Coordinador de Trade) → su jefe directo es **Fabio**
- Fabio (Director de Operaciones) → su jefe directo es el **CEO**

Para editar, buscas a la persona en la lista, escribes su cargo y eliges su jefe directo del desplegable. Guardas.

> 💡 Esta jerarquía es la base para saber **quién evalúa a quién** en los ciclos.

---

### PASO 5 — Crear un Ciclo de Evaluación

> 👤 Lo hace: **Admin People**
> 📍 Donde: módulo Valoración → tarjeta **"Ciclos de Evaluación"**

Un ciclo es un periodo específico donde se hacen evaluaciones. Por ejemplo: *"Evaluación Q2 2026"*.

Para crear un ciclo, le das clic en **"+ Nuevo ciclo"** y llenas:
- **Nombre**: ej. "Evaluación Q2 2026".
- **Descripción** (opcional).
- **Tipo**:
  - `Liderazgo` → solo se evalúan líderes.
  - `Operativo/Táctico` → solo se evalúan colaboradores operativos.
  - `Mixta` → ambos.
- **Fecha inicio** y **Fecha cierre** del periodo de respuestas.
- **Estado**: arranca en `Programado`. Cuando esté listo, lo pasas a `Activo` para que la gente pueda responder.
- **Peso jefe (líder)** y **Peso equipo (líder)**: define cuánto pesa la opinión del jefe vs el equipo en evaluaciones de liderazgo. Default 60/40 (deben sumar 100).
- **Anonimato**: si lo activas, el evaluado no verá quién lo calificó.
- **Comentarios obligatorios**: si lo activas, los evaluadores deben dejar observaciones al final.

Guardas y el ciclo aparece en la lista.

---

### PASO 6 — Asignar quién evalúa a quién

> 👤 Lo hace: **Admin People**
> 📍 Donde: dentro del ciclo creado, le das al botón **"Asignaciones"**

Aquí defines uno por uno los pares **Evaluador → Evaluado**. Para cada asignación necesitas:
- **Evaluador**: quién va a calificar.
- **Evaluado**: a quién van a calificar.
- **Rol del evaluador**:
  - `Jefe Inmediato` → el jefe directo del evaluado.
  - `Miembro del Equipo` → alguien del equipo a cargo (para evaluaciones 180° de líderes).
  - `Autoevaluación` → el mismo se evalúa.
- **Tipo de evaluación**: Liderazgo u Operativo (debe coincidir con el tipo del ciclo si no es mixto).

**Ejemplo práctico** — Para evaluar a Julian (Coordinador) en un ciclo de Liderazgo:

| Evaluador | Evaluado | Rol | Tipo |
|---|---|---|---|
| Fabio (su jefe) | Julian | Jefe Inmediato | Liderazgo |
| Pedro (su equipo) | Julian | Miembro del Equipo | Liderazgo |
| María (su equipo) | Julian | Miembro del Equipo | Liderazgo |

Y para evaluar a Pedro (Asesor) en Operativo:

| Evaluador | Evaluado | Rol | Tipo |
|---|---|---|---|
| Julian (su jefe) | Pedro | Jefe Inmediato | Operativo |

> ⚠️ El sistema no permite que alguien se evalúe a sí mismo desde acá (solo si el rol es "Autoevaluación") y no deja registrar dos veces el mismo par evaluador→evaluado en el mismo ciclo.

---

### PASO 7 — Activar el ciclo

Vuelves a la tarjeta **"Ciclos de Evaluación"**, le das **Editar** al ciclo y cambias el estado de `Programado` a `Activo`. Desde ese momento, todos los evaluadores van a ver sus tareas pendientes.

---

## 3. La hora de evaluar (lo que hace cada evaluador)

> 👤 Lo hace: **cualquier persona que tenga asignaciones**
> 📍 Donde: módulo Valoración → tarjeta **"Mis Evaluaciones"**

Cuando entras a Mis Evaluaciones ves la lista de personas que te toca calificar.

**Ejemplo de lo que verá Julian:**

| Ciclo | Evaluado | Tipo | Rol | Estado | Cierre |
|---|---|---|---|---|---|
| Evaluación Q2 2026 | Pedro (Asesor) | Operativo | Jefe Inmediato | Pendiente | 27/05/2026 |
| Evaluación Q2 2026 | María (Asesor) | Operativo | Jefe Inmediato | Pendiente | 27/05/2026 |

Le da clic a **"Responder"** y entra al formulario.

### En el formulario verá:
- Una a una, las preguntas con su escala 1 a 5:
  - 5 → Es un referente
  - 4 → Está consolidado
  - 3 → En desarrollo
  - 2 → Requiere acompañamiento
  - 1 → Requiere intervención inmediata
- **No verá** a qué competencia pertenece cada pregunta (eso es interno).
- Una barra arriba que muestra el progreso (ej: 12/30 respondidas, 40%).
- Al final, un campo libre de **"Observaciones y acuerdos"** para escribir compromisos cualitativos.

### Dos botones al final:
- **Guardar borrador** → guarda lo que llevas y puedes volver más tarde a continuar. El estado pasa a "En progreso".
- **Enviar evaluación** → cierra y envía. **Ya no se puede modificar.** Si dejaste preguntas obligatorias sin responder, te avisa.

> 💡 El evaluador puede entrar, llenar 5 preguntas, irse, y volver al otro día a continuar. El sistema recuerda lo que ya respondió.

---

## 4. Consolidar los resultados

> 👤 Lo hace: **Admin People** o **BI/Tech**
> 📍 Donde: módulo Valoración → tarjeta **"Ciclos de Evaluación"** → botón **"Consolidar resultados"** en la fila del ciclo

Cuando ya hay evaluaciones completadas, alguien tiene que pedirle al sistema que calcule los resultados. Esto se hace con el botón **Consolidar resultados**.

### ¿Qué hace el motor de cálculo?

Para cada persona evaluada en ese ciclo:

1. **Recoge todas las respuestas** que le dieron los distintos evaluadores.
2. **Calcula el score de cada evaluador** sobre esa persona (0 a 100%).
3. **Promedia por rol del evaluador**: un promedio para el jefe, otro para el equipo y otro para la autoevaluación (esta última queda como referencia, no suma al puntaje).
4. **Combina los promedios según el tipo de evaluación:**
   - Si es **Liderazgo** y hay jefe y equipo: promedio del jefe × 60% + promedio del equipo × 40% (los pesos se configuran en cada ciclo).
   - Si es **Operativo** y hay jefe y equipo: promedio simple de las dos miradas.
   - Si solo hay una fuente: se usa esa.
   - Si solo hay autoevaluación: se usa como referencia.
5. **Guarda cuántas calificaciones se consolidaron** (total y por rol), para que el resultado nunca se muestre como calificaciones sueltas.
6. **Calcula el promedio por competencia** (A. Cultura, B. Estructura Operacional, etc.).
7. **Asigna un semáforo** según el porcentaje final:
   - 🟢 ≥90% → Es un referente
   - 🟡 75-89% → Está consolidado
   - 🟠 60-74% → En desarrollo
   - 🔴 40-59% → Requiere acompañamiento
   - ⚫ <40% → Requiere intervención inmediata
8. **Identifica fortalezas** (los ítems donde sacó promedio ≥4).
9. **Identifica brechas** (los ítems donde sacó promedio ≤2.5).

> ⚠️ El motor se ejecuta cuando le das clic al botón. Puedes correrlo varias veces a medida que más evaluadores van completando sus respuestas.

> 🔁 **Ciclos consolidados antes de esta versión:** vuelve a darle "Consolidar resultados" (o ejecuta `python manage.py recalcular_valoracion`) para que se llenen el número de evaluadores, la autoevaluación y el detalle por competencia.

### El consolidado entre ciclos

Cuando una persona tiene resultados en varios ciclos, SUPLI PERFORMANCE **no los muestra como filas independientes**: los pondera por la cantidad de calificaciones que aportó cada ciclo y entrega un único **% consolidado** por persona. Ejemplo: 1 calificación al 60% en el ciclo 1 y 4 calificaciones al 90% en el ciclo 2 → consolidado **84%** con 5 calificaciones.

---

## 5. Ver los resultados (tres perspectivas)

### 5.0 Candado de publicación (importante)

Las tarjetas **"Mis Resultados"** y **"Planes de Acción"** nacen **bloqueadas** para todo el equipo.
Aparecen en gris con un candado y no se pueden abrir; si alguien entra por el enlace directo ve la
pantalla "aún no está disponible" con el avance de evaluaciones.

Quién lo destraba: **cualquier persona de las áreas People, Business Intelligence (Data) o Tech**,
más los usuarios admin/staff. En el home de SUPLI PERFORMANCE esas personas ven un panel con el estado
actual, el porcentaje de evaluaciones respondidas y el botón **"Habilitar resultados al equipo"**
(y luego **"Bloquear resultados"** para volver a cerrarlo). La recomendación es habilitar cuando el
avance llegue al 100%.

El interruptor es global (una sola fila en `valoracion_configuracion`) y queda registrado con la
fecha y la persona que lo cambió.


### 5.1 Como **Colaborador o Líder evaluado**

> 📍 Tarjeta **"Mis Resultados"**

Aquí ves SOLO tus propios resultados. Por cada ciclo en el que te evaluaron, verás una fila con:
- Nombre del ciclo
- Tipo de evaluación
- Puntaje (sobre 5)
- Porcentaje
- Tu semáforo (referente / consolidado / desarrollo / acompañamiento / intervención)
- Fortalezas y brechas detectadas
- Botón **"Ver detalle"**

Arriba de la tabla ves tu **consolidado**: un solo porcentaje que pondera todas las calificaciones que recibiste, con el desglose de jefe / equipo / autoevaluación y tu resultado por competencia.

Al darle a **Ver ítems** entras a una pantalla con:
- KPIs grandes: % consolidado, puntaje, score del jefe, del equipo y de la autoevaluación (con el número de calificaciones de cada uno).
- El semáforo con su descripción.
- **Resultado por competencia** en barras.
- **Cada ítem evaluado y su resultado**: promedio 1-5, nivel de la escala, promedio del jefe, del equipo, de la autoevaluación, la brecha de autopercepción y la distribución de las calificaciones recibidas.
- Filtro para ver el detalle solo de un rol de evaluador (jefe / equipo / autoevaluación) o buscar un ítem.
- **Calificaciones recibidas**: qué puntaje dio cada evaluador (anónimo si el ciclo lo es).
- **Respuestas abiertas** y **observaciones y acuerdos**.

### 5.2 Como **Líder de un equipo**

> 📍 Tarjeta **"Resultados del Equipo"**

Aquí ves los resultados de TODAS las personas que tienes como subordinados directos (las que tienen tu nombre en el campo "Jefe directo").

La pantalla tiene dos tablas:

1. **Consolidado por persona** — una sola fila por persona: cuántas calificaciones recibió, el promedio del jefe, del equipo y de la autoevaluación, el **% consolidado** y su semáforo.
2. **Detalle por ciclo** — el resultado de cada ciclo, por si necesitas ver la evolución.

Además puedes **segmentar** por fecha, ciclo, área/dirección, equipo, rol, cargo, persona, tipo de evaluación y semáforo.

Así puedes identificar quiénes están en verde y a quiénes les debes prestar atención.

### 5.3 Como **CEO o Admin People**

> 📍 Tarjeta **"Resultados del Equipo"** (misma tarjeta, pero con visibilidad ampliada)

Cuando tu rol es CEO o Admin People, la misma tarjeta te muestra los resultados de **TODA la compañía**, no solo de un equipo. Puedes ver el detalle de cualquier persona.

### 5.4 Dashboard Organizacional y Consolidado Individual

> 📍 Tarjetas **"Dashboard Organizacional"** y **"Consolidado Individual"** (Admin People / CEO / BI / Tech)

- **Dashboard Organizacional**: promedio compañía calculado sobre el consolidado de cada persona, semáforo organizacional, evolución histórica, resultado por competencia y promedios por **área/dirección, rol, equipo (jefe directo) y cargo**, además de top performers y mayores brechas — todos sobre el consolidado, nunca sobre calificaciones sueltas.
- **Consolidado Individual**: la tabla completa, una fila por persona con sus competencias, ordenable por consolidado, nombre, área, cargo, equipo o número de calificaciones; y el **detalle de ítems** (una fila por persona e ítem evaluado).
- **Exportación a CSV** del consolidado y del detalle de ítems, respetando la segmentación aplicada, para analizar en Excel o Power BI.

### 5.5 Segmentación disponible

En el dashboard, el consolidado y los resultados del equipo se puede filtrar por: **fechas, ciclo, área/dirección, equipo (jefe directo), rol organizacional, cargo, persona, tipo de evaluación y semáforo consolidado**. Los filtros se conservan al exportar a CSV.

---

## 6. Planes de Acción

> 📍 Tarjeta **"Planes de Acción"**

Cuando se identifican **brechas** en un resultado, lo siguiente es crear acciones de mejora. Cada plan tiene:
- **Descripción** de la acción (ej: "Capacitación en gestión de tiempo").
- **Responsable** (quién va a ejecutar la acción).
- **Fecha de compromiso**.
- **Estado**: Pendiente → En proceso → Cumplido (o Vencido si pasa la fecha).
- **Evidencia** (link a un certificado, foto, documento, etc.).

Cada persona ve los planes que tiene asignados o que son de su equipo. El Admin People y el CEO ven todos.

---

## 7. Resumen visual del flujo completo

```
┌────────────────────────────────────────────────────────────────────┐
│                       PREPARACIÓN (1 vez)                          │
│                                                                    │
│  [Admin People crea usuarios]                                      │
│            ↓                                                       │
│  [Admin/BI define Competencias internas]                          │
│            ↓                                                       │
│  [Admin/BI crea Banco de Preguntas]                                │
│            ↓                                                       │
│  [Admin People define Jerarquía: cargos + jefes directos]         │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                    CADA CICLO DE EVALUACIÓN                        │
│                                                                    │
│  [Admin People crea Ciclo]                                         │
│            ↓                                                       │
│  [Admin People registra Asignaciones evaluador→evaluado]          │
│            ↓                                                       │
│  [Admin People activa el ciclo]                                    │
│            ↓                                                       │
│  [Evaluadores responden desde "Mis Evaluaciones"]                 │
│   - Pueden guardar borrador y continuar después                   │
│   - Al enviar, queda bloqueada                                    │
│            ↓                                                       │
│  [Admin/BI le da "Consolidar resultados"]                         │
│   - El motor calcula puntajes, semáforos, fortalezas, brechas    │
│            ↓                                                       │
│  [Cada quien ve sus resultados según su rol]                      │
│   - Colaboradores → Mis Resultados                                │
│   - Líderes → Resultados del Equipo (su equipo)                  │
│   - CEO / Admin People → Resultados del Equipo (todos)            │
│            ↓                                                       │
│  [Se crean Planes de Acción sobre las brechas]                    │
│            ↓                                                       │
│  [Admin People cierra el ciclo cuando termine el periodo]         │
└────────────────────────────────────────────────────────────────────┘
```

---

## 8. Preguntas frecuentes

### ¿Tengo que crear nuevas preguntas para cada ciclo?
No. Las preguntas se crean **una sola vez** y se reutilizan en todos los ciclos. Solo creas nuevas cuando quieras cambiar el modelo de evaluación o agregar dimensiones.

### Si me cambian de jefe a mitad del ciclo, ¿qué pasa?
Las asignaciones que ya existen en el ciclo se mantienen. Para el próximo ciclo, actualiza el jefe directo en la pantalla de Jerarquía y las nuevas asignaciones reflejarán ese cambio.

### ¿Una persona puede evaluarse a sí misma?
Solo si el Admin People le crea una asignación con rol "Autoevaluación". Por defecto, el sistema bloquea que evaluador y evaluado sean la misma persona.

### ¿Qué pasa si un evaluador no responde a tiempo?
El sistema no envía recordatorios automáticos todavía (esa función está pendiente). El Admin People puede ver en la pantalla de Asignaciones qué evaluadores están en estado "Pendiente" o "En progreso" y hacerles seguimiento manual.

### Si el ciclo es anónimo, ¿el evaluado puede saber quién dijo qué?
No. En la pantalla de detalle, las observaciones aparecen como "Anónimo". Solo el CEO y el Admin People pueden ver los nombres aunque el ciclo sea anónimo.

### ¿Puedo modificar una evaluación después de enviarla?
No. Una vez enviada queda bloqueada. Si necesitas corregirla, el Admin People tendría que eliminarla manualmente y volver a crear la asignación.

### ¿Puedo correr el motor de cálculo varias veces?
Sí. Cada vez que entran nuevas respuestas, puedes darle "Consolidar resultados" y los resultados se recalculan con la información más reciente.

### ¿Las competencias internas las puede ver el evaluador?
**No.** El evaluador solo ve el enunciado de la pregunta y las opciones de respuesta. La competencia (A. CULTURA, B. ESTRUCTURA…) es solo para que el Admin People y BI puedan reportar y agrupar resultados internamente.

---

## 9. Glosario rápido

| Término | Qué significa |
|---|---|
| **Competencia** | Categoría interna para agrupar preguntas (Cultura, Liderazgo, Ejecución…). |
| **Ciclo** | Periodo de evaluación con fecha de inicio y cierre (ej: Q2 2026). |
| **Asignación** | Par de "evaluador → evaluado" dentro de un ciclo. |
| **Rol del evaluador** | Si quien evalúa es el Jefe, un Miembro del Equipo, o la propia persona. |
| **Tipo de evaluación** | Liderazgo (para líderes/coordinadores) u Operativo (para roles ejecutivos). |
| **Escala Likert** | La escala 1-5 (Referente → Intervención). |
| **Semáforo** | Color que resume el resultado: verde, amarillo, naranja, rojo, negro. |
| **Fortalezas** | Preguntas donde la persona sacó promedio alto (≥4). |
| **Brechas** | Preguntas donde la persona sacó promedio bajo (≤2.5). |
| **Plan de acción** | Compromiso concreto para mejorar una brecha. |
| **Jefe directo** | La persona que tienes asignada en la jerarquía como tu superior inmediato. |
| **Cargo** | El nombre real de tu posición (Coordinador, Director, Asesor…). |

---

*Documento vivo — se irá actualizando a medida que se agreguen nuevas funciones (notificaciones automáticas, dashboards, reportes exportables, etc.).*
