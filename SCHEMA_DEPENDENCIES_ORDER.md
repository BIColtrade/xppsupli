# Orden de Dependencias de Tablas - Base de Datos xppcoltrade

## Apps / Módulos Django

| App | Módulo | Descripción |
|-----|--------|-------------|
| `user` | Usuarios | Custom user model, jerarquía (jefe directo) + reset de contraseña |
| `abastecimientos` | Abastecimiento | Canales, productos, puntos de venta, inventarios |
| `malla_operaciones_trade` | Malla Operaciones | Coordinadores, asesores, puntos de venta y registro laboral |
| `listado_compras` | Listado Compras | Catálogos de productos Supli, nacionales e internacionales |
| `bienestar_coltrade` | Bienestar (PPS) | Sistema de puntos, acciones, beneficios y progreso |
| `modulo_valoracion` | Valoración | Evaluaciones de desempeño (ciclos, preguntas, asignaciones, resultados, planes de acción) |
| `portafolio_mayoristas` | Portafolio Mayoristas | (Sin modelos actualmente) |
| `core` | Core | (Sin modelos actualmente) |

---

## NIVEL 1: Tablas Base (Sin Dependencias)

### 1. auth_permission
```
id                      INTEGER (NOT NULL) [PRIMARY KEY]
name                    VARCHAR (NOT NULL)
content_type_id         INTEGER (NOT NULL) -> FK: django_content_type.id
codename                VARCHAR (NOT NULL)
```

### 2. auth_group
```
id                      INTEGER (NOT NULL) [PRIMARY KEY]
name                    VARCHAR (NOT NULL)
```

### 3. django_content_type
```
id                      INTEGER (NOT NULL) [PRIMARY KEY]
app_label               VARCHAR (NOT NULL)
model                   VARCHAR (NOT NULL)
```

### 4. user_usuario
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
password                VARCHAR (NOT NULL)
last_login              TIMESTAMP WITH TIME ZONE (NULL)
is_superuser            BOOLEAN (NOT NULL)
email                   VARCHAR (NOT NULL) [UNIQUE]
username                VARCHAR (NOT NULL) [UNIQUE]
nombre                  VARCHAR (NOT NULL)
apellido                VARCHAR (NULL)
edad                    INTEGER (NULL)
telefono                VARCHAR (NULL)
tipo_usuario            VARCHAR (NULL)   -- choices: colaborador | lider | admin
area                    VARCHAR (NULL)   -- choices: ceo | direccion_comercial | tecnologia | accounting | finanzas | sales | operations | procurement | trade | brands | bi | sales_corporativo | sales_retail | people | quality
cargo                   VARCHAR (NULL)
jefe_directo_id         BIGINT (NULL) -> FK: user_usuario.id [SELF] [SET_NULL]
is_active               BOOLEAN (NOT NULL)
is_staff                BOOLEAN (NOT NULL)
```
> Auto-referencia: `jefe_directo` → user_usuario (related_name `reportes_directos`)

### 5. canal
```
id_canal                VARCHAR (NOT NULL) [PRIMARY KEY]
canal_nombre            VARCHAR (NOT NULL) [UNIQUE]
```

### 6. coordinador
```
id_coordinador          INTEGER (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
```

### 7. asesor
```
id_asesor               INTEGER (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
correo                  VARCHAR (NULL)
telefono                VARCHAR (NULL)
```

### 8. listado_productos_supli
```
UPC                     VARCHAR (NOT NULL) [PRIMARY KEY]
nombre_producto         VARCHAR (NOT NULL)
marca_producto          VARCHAR (NOT NULL)
```

### 9. listado_productos_internacionales
```
id                      INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
upc                     VARCHAR (NOT NULL)
fecha_lista             DATE (NOT NULL)
nombre                  VARCHAR (NOT NULL)
costo                   DECIMAL(12,2) (NOT NULL)
cantidad_disponible     INTEGER (NOT NULL)
proveedores             VARCHAR (NOT NULL)
factor_logistico        DECIMAL(6,2) (NOT NULL) [DEFAULT 0.00]
costo_con_factor_logistico DECIMAL(12,2) (NOT NULL) [COMPUTED: costo + (costo * factor_logistico / 100)]
```

### 10. listado_productos_nacionales
```
id                      INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
upc                     VARCHAR (NOT NULL) [UNIQUE]
nombre                  VARCHAR (NOT NULL)
costo                   DECIMAL(12,2) (NOT NULL)
cantidad_disponible     INTEGER (NOT NULL)
proveedor               VARCHAR (NOT NULL)
costos_adicionales      DECIMAL(12,2) (NOT NULL) [DEFAULT 0.00]
total_costo             DECIMAL(12,2) (NOT NULL) [COMPUTED: costo + costos_adicionales]
```

### 11. abastecimiento_claro
```
id                      UUID (NOT NULL) [PRIMARY KEY] [DEFAULT uuid4]
material                VARCHAR (NOT NULL)
producto                VARCHAR (NOT NULL)
centro_costos           VARCHAR (NOT NULL)
nombre_punto            VARCHAR (NOT NULL)
inventario_claro        INTEGER (NOT NULL) [DEFAULT 0]
transito_claro          INTEGER (NOT NULL) [DEFAULT 0]
ventas_pasadas_claro    INTEGER (NOT NULL) [DEFAULT 0]
ventas_actuales_claro   INTEGER (NOT NULL) [DEFAULT 0]
sugerido_claro          INTEGER (NOT NULL) [DEFAULT 0]
```

### 12. abastecimiento_coltrade
```
id                      UUID (NOT NULL) [PRIMARY KEY] [DEFAULT uuid4]
centro_costos           VARCHAR (NOT NULL)
punto_venta             VARCHAR (NOT NULL)
material                VARCHAR (NOT NULL)
producto                VARCHAR (NOT NULL)
marca                   VARCHAR (NOT NULL)
ventas_actuales         INTEGER (NOT NULL) [DEFAULT 0]
transitos               INTEGER (NOT NULL) [DEFAULT 0]
inventario              INTEGER (NOT NULL) [DEFAULT 0]
envio_inventario_3_meses INTEGER (NOT NULL) [DEFAULT 0]
sugerido_coltrade       INTEGER (NOT NULL) [DEFAULT 0]
```

### 13. valoracion_competencias
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
codigo                  VARCHAR(10) (NOT NULL)   -- ej: A, B, C
nombre                  VARCHAR(200) (NOT NULL)  -- ej: CULTURA, ESTRUCTURA OPERACIONAL
descripcion             TEXT (NOT NULL) [DEFAULT '']
orden                   INTEGER (NOT NULL) [DEFAULT 0] [CHECK >= 0]
activa                  BOOLEAN (NOT NULL) [DEFAULT True]
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```
> Categoría interna de las preguntas; solo visible para el administrador.

---

## NIVEL 2: Dependencias Simples (Dependen de Nivel 1)

### 14. auth_group_permissions
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
group_id                INTEGER (NOT NULL) -> FK: auth_group.id
permission_id           INTEGER (NOT NULL) -> FK: auth_permission.id
```

### 15. password_reset_codes
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
code                    VARCHAR(6) (NOT NULL)
created_at              TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
expires_at              TIMESTAMP WITH TIME ZONE (NOT NULL)
used_at                 TIMESTAMP WITH TIME ZONE (NULL)
user_id                 BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
```
> Índices: `(user_id, code)`, `(expires_at)`

### 16. user_usuario_groups
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
group_id                INTEGER (NOT NULL) -> FK: auth_group.id
```

### 17. user_usuario_user_permissions
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
permission_id           INTEGER (NOT NULL) -> FK: auth_permission.id
```

### 18. productos_abastecimiento
```
id_producto             VARCHAR (NOT NULL) [PRIMARY KEY]
nombre_producto         VARCHAR (NOT NULL)
marca                   VARCHAR (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal [PROTECT]
```

### 19. puntos_venta_abastecimiento
```
id_puntoventa           VARCHAR (NOT NULL) [PRIMARY KEY]
punto_venta             VARCHAR (NOT NULL)
canal_regional          VARCHAR (NOT NULL)
tipo                    VARCHAR (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal [PROTECT]
```

### 20. punto_venta_malla
```
id_punto                VARCHAR (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
zona                    VARCHAR (NOT NULL)   -- choices: Zona Sur | Zona Norte
coordinador_default_id  INTEGER (NULL) -> FK: coordinador.id_coordinador [SET_NULL]
asesor_default_id       INTEGER (NULL) -> FK: asesor.id_asesor [SET_NULL]
```

### 21. pps_acciones
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
descripcion             TEXT (NOT NULL)
nivel                   VARCHAR (NOT NULL)   -- choices: estrategico | tactico | desarrollo | activacion_bienestar | capacitacion
youtube_url             VARCHAR (NULL)
areas                   JSONB (NOT NULL) [DEFAULT []]
destinatarios           VARCHAR (NOT NULL)   -- choices: todos | lideres | colaboradores
aplica_empresa          BOOLEAN (NOT NULL) [DEFAULT False]
puntos_min              INTEGER (NOT NULL)
puntos_max              INTEGER (NOT NULL)
puntos_default          INTEGER (NOT NULL)
solo_lideres            BOOLEAN (NOT NULL) [DEFAULT False]
activa                  BOOLEAN (NOT NULL) [DEFAULT True]
aprobador_todos         BOOLEAN (NOT NULL) [DEFAULT True]
fecha_inicio            TIMESTAMP WITH TIME ZONE (NULL)
fecha_fin               TIMESTAMP WITH TIME ZONE (NULL)
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```
> ManyToMany: `aprobadores` → user_usuario (a través de pps_acciones_aprobadores)

### 22. pps_beneficios
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
descripcion             TEXT (NOT NULL)
categoria               VARCHAR (NOT NULL)   -- choices: reconocimiento | tiempo | certificado | sorteo | desarrollo
puntos_requeridos       INTEGER (NOT NULL)
disponible              BOOLEAN (NOT NULL) [DEFAULT True]
stock                   INTEGER (NULL)       -- NULL = ilimitado
imagen_url              VARCHAR (NULL)
niveles_permitidos      JSONB (NOT NULL) [DEFAULT []]   -- values: bronce | plata | oro | diamante
aprobador_todos         BOOLEAN (NOT NULL) [DEFAULT True]
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```
> ManyToMany: `aprobadores` → user_usuario (a través de pps_beneficios_aprobadores)

### 23. valoracion_preguntas
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
competencia_id          BIGINT (NOT NULL) -> FK: valoracion_competencias.id [PROTECT]
enunciado               TEXT (NOT NULL)
tipo_evaluacion         VARCHAR(20) (NOT NULL)   -- choices: lider | operativo
tipo_pregunta           VARCHAR(20) (NOT NULL) [DEFAULT 'likert']   -- choices: likert | abierta
peso                    DECIMAL(5,2) (NOT NULL) [DEFAULT 1.0]
orden                   INTEGER (NOT NULL) [DEFAULT 0] [CHECK >= 0]
obligatoria             BOOLEAN (NOT NULL) [DEFAULT True]
activa                  BOOLEAN (NOT NULL) [DEFAULT True]
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```

### 24. valoracion_ciclos
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR(200) (NOT NULL)
descripcion             TEXT (NOT NULL) [DEFAULT '']
tipo                    VARCHAR(20) (NOT NULL) [DEFAULT 'mixta']   -- choices: lider | operativo | mixta
fecha_inicio            TIMESTAMP WITH TIME ZONE (NOT NULL)
fecha_cierre            TIMESTAMP WITH TIME ZONE (NOT NULL)
estado                  VARCHAR(20) (NOT NULL) [DEFAULT 'programado']   -- choices: programado | activo | cerrado | cancelado | finalizado
anonimato               BOOLEAN (NOT NULL) [DEFAULT False]
comentarios_obligatorios BOOLEAN (NOT NULL) [DEFAULT False]
peso_jefe_lider         SMALLINT (NOT NULL) [DEFAULT 60] [CHECK >= 0]
peso_equipo_lider       SMALLINT (NOT NULL) [DEFAULT 40] [CHECK >= 0]
creado_por_id           BIGINT (NULL) -> FK: user_usuario.id [SET_NULL]
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
fecha_actualizacion     TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```

### 25. django_admin_log
```
id                      INTEGER (NOT NULL) [PRIMARY KEY]
action_time             TIMESTAMP WITH TIME ZONE (NOT NULL)
object_id               TEXT (NULL)
object_repr             VARCHAR (NOT NULL)
action_flag             SMALLINT (NOT NULL)
change_message          TEXT (NOT NULL)
content_type_id         INTEGER (NULL) -> FK: django_content_type.id
user_id                 BIGINT (NOT NULL) -> FK: user_usuario.id
```

### 26. django_session
```
session_key             VARCHAR (NOT NULL) [PRIMARY KEY]
session_data            TEXT (NOT NULL)
expire_date             TIMESTAMP WITH TIME ZONE (NOT NULL)
```

### 27. django_migrations
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
app                     VARCHAR (NOT NULL)
name                    VARCHAR (NOT NULL)
applied                 TIMESTAMP WITH TIME ZONE (NOT NULL)
```

---

## NIVEL 3: Dependencias Complejas (Dependen de Nivel 2)

### 28. pps_acciones_aprobadores
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
accionpps_id            BIGINT (NOT NULL) -> FK: pps_acciones.id
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
```
> Tabla through automática del ManyToMany `AccionPPS.aprobadores`

### 29. pps_beneficios_aprobadores
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
beneficio_id            BIGINT (NOT NULL) -> FK: pps_beneficios.id
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
```
> Tabla through automática del ManyToMany `Beneficio.aprobadores`

### 30. inventario_abastecimiento
```
id_inventario           INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_inventario     INTEGER (NOT NULL) [CHECK >= 0]
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal [PROTECT]
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto [PROTECT]
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa [PROTECT]
```

### 31. meta_abastecimiento
```
id_meta                 INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_meta           INTEGER (NOT NULL) [CHECK >= 0]
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal [PROTECT]
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto [PROTECT]
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa [PROTECT]
```

### 32. transitos_abastecimiento
```
id_transito             INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_transito       INTEGER (NOT NULL) [CHECK >= 0]
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal [PROTECT]
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto [PROTECT]
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa [PROTECT]
```

### 33. ventas_abastecimiento
```
id_venta                INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_venta          INTEGER (NOT NULL) [CHECK >= 0]
fecha_venta             DATE (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal [PROTECT]
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto [PROTECT]
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa [PROTECT]
```

### 34. pps_puntos_usuario
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
puntos_totales          INTEGER (NOT NULL) [DEFAULT 0]
nivel                   VARCHAR (NOT NULL) [DEFAULT 'bronce']   -- choices: bronce (<500) | plata (500-1499) | oro (1500-3999) | diamante (>=4000)
fecha_actualizacion     TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id [OneToOne] [UNIQUE] [CASCADE]
```
> Lógica: `actualizar_nivel()` recalcula el nivel según `puntos_totales`

### 35. pps_capacitaciones_progreso
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
progreso_pct            SMALLINT (NOT NULL) [DEFAULT 0] [CHECK >= 0]
puntos_otorgados        INTEGER (NOT NULL) [DEFAULT 0] [CHECK >= 0]
completado              BOOLEAN (NOT NULL) [DEFAULT False]
fecha_actualizacion     TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
accion_id               BIGINT (NOT NULL) -> FK: pps_acciones.id [CASCADE]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
```
> Constraint: `UNIQUE (usuario_id, accion_id)`

### 36. pps_registro_acciones
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
descripcion_evidencia   TEXT (NOT NULL)
fecha_registro          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
estado                  VARCHAR (NOT NULL) [DEFAULT 'pendiente']   -- choices: pendiente | aprobado | rechazado
puntos_asignados        INTEGER (NOT NULL) [DEFAULT 0]
fecha_resolucion        TIMESTAMP WITH TIME ZONE (NULL)
observacion_lider       TEXT (NOT NULL) [DEFAULT '']
accion_id               BIGINT (NOT NULL) -> FK: pps_acciones.id [PROTECT]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
aprobado_por_id         BIGINT (NULL) -> FK: user_usuario.id [SET_NULL]
```

### 37. pps_reclamos_beneficios
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
fecha_reclamo           TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
estado                  VARCHAR (NOT NULL) [DEFAULT 'pendiente']   -- choices: pendiente | entregado | cancelado
puntos_descontados      INTEGER (NOT NULL) [CHECK >= 0]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
beneficio_id            BIGINT (NOT NULL) -> FK: pps_beneficios.id [PROTECT]
aprobado_por_id         BIGINT (NULL) -> FK: user_usuario.id [SET_NULL]
```

### 38. registro_laboral
```
id_registro             INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
fecha                   DATE (NOT NULL)
estado                  VARCHAR (NOT NULL)   -- choices: ACTIVO | VACANTE | INCAPACIDAD | DESCANSO
hora_ingreso            TIME WITHOUT TIME ZONE (NULL)
hora_salida             TIME WITHOUT TIME ZONE (NULL)
horas_trabajadas        FLOAT (NOT NULL) [DEFAULT 0] [COMPUTED: (hora_salida - hora_ingreso) en horas]
punto_venta_id          VARCHAR (NOT NULL) -> FK: punto_venta_malla.id_punto [CASCADE]
coordinador_id          INTEGER (NULL) -> FK: coordinador.id_coordinador [CASCADE, default desde punto_venta]
asesor_id               INTEGER (NULL) -> FK: asesor.id_asesor [CASCADE, default desde punto_venta]
```

### 39. valoracion_asignaciones
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
ciclo_id                BIGINT (NOT NULL) -> FK: valoracion_ciclos.id [CASCADE]
evaluador_id            BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
evaluado_id             BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
rol_evaluador           VARCHAR(20) (NOT NULL)   -- choices: jefe | equipo | autoevaluacion
tipo_evaluacion         VARCHAR(20) (NOT NULL)   -- choices: lider | operativo
estado                  VARCHAR(20) (NOT NULL) [DEFAULT 'pendiente']   -- choices: pendiente | en_progreso | completada
observaciones_acuerdos  TEXT (NOT NULL) [DEFAULT '']
fecha_inicio_respuesta  TIMESTAMP WITH TIME ZONE (NULL)
fecha_completada        TIMESTAMP WITH TIME ZONE (NULL)
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```
> Constraint: `UNIQUE (ciclo_id, evaluador_id, evaluado_id)`

### 40. valoracion_resultados
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
ciclo_id                BIGINT (NOT NULL) -> FK: valoracion_ciclos.id [CASCADE]
evaluado_id             BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
tipo_evaluacion         VARCHAR(20) (NOT NULL)   -- choices: lider | operativo
puntaje_total           DECIMAL(6,2) (NOT NULL) [DEFAULT 0]
porcentaje              DECIMAL(5,2) (NOT NULL) [DEFAULT 0]
semaforo                VARCHAR(20) (NOT NULL) [DEFAULT 'intervencion']   -- choices: referente | consolidado | desarrollo | acompanamiento | intervencion
puntaje_jefe            DECIMAL(6,2) (NOT NULL) [DEFAULT 0]
puntaje_equipo          DECIMAL(6,2) (NOT NULL) [DEFAULT 0]
fortalezas              JSONB (NOT NULL) [DEFAULT []]
brechas                 JSONB (NOT NULL) [DEFAULT []]
fecha_calculo           TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```
> Constraint: `UNIQUE (ciclo_id, evaluado_id)`
> Semáforo por % : referente >=90 | consolidado >=75 | desarrollo >=60 | acompanamiento >=40 | intervencion >=0

---

## NIVEL 4: Dependencias sobre Nivel 3

### 41. valoracion_respuestas
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
asignacion_id           BIGINT (NOT NULL) -> FK: valoracion_asignaciones.id [CASCADE]
pregunta_id             BIGINT (NOT NULL) -> FK: valoracion_preguntas.id [PROTECT]
valor                   SMALLINT (NULL) [CHECK >= 0]   -- valor 1-5 para preguntas tipo likert
respuesta_abierta       TEXT (NOT NULL) [DEFAULT '']
fecha_respuesta         TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```
> Constraint: `UNIQUE (asignacion_id, pregunta_id)`

### 42. valoracion_planes_accion
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
resultado_id            BIGINT (NOT NULL) -> FK: valoracion_resultados.id [CASCADE]
descripcion             TEXT (NOT NULL)
responsable_id          BIGINT (NOT NULL) -> FK: user_usuario.id [CASCADE]
fecha_compromiso        DATE (NOT NULL)
estado                  VARCHAR(20) (NOT NULL) [DEFAULT 'pendiente']   -- choices: pendiente | en_proceso | cumplido | vencido
evidencia_url           VARCHAR (NULL)
observaciones           TEXT (NOT NULL) [DEFAULT '']
creado_por_id           BIGINT (NULL) -> FK: user_usuario.id [SET_NULL]
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
fecha_actualizacion     TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
```

---

## Resumen

**Total de Tablas: 42**

| Nivel | Cantidad | Descripción |
|-------|----------|-------------|
| Nivel 1 | 13 | Tablas base (sin dependencias) |
| Nivel 2 | 14 | Tablas con dependencias simples (Nivel 1) |
| Nivel 3 | 13 | Tablas con dependencias complejas (Nivel 2) |
| Nivel 4 | 2 | Tablas que dependen de Nivel 3 |

**Tablas Django internas (Framework):**
- auth_group, auth_permission, auth_group_permissions
- django_admin_log, django_content_type, django_migrations, django_session

**Tablas de Negocio:**
- **User Module:** user_usuario, password_reset_codes, user_usuario_groups, user_usuario_user_permissions
- **Abastecimiento:** canal, productos_abastecimiento, puntos_venta_abastecimiento, inventario_abastecimiento, meta_abastecimiento, transitos_abastecimiento, ventas_abastecimiento, abastecimiento_claro, abastecimiento_coltrade
- **Bienestar (PPS):** pps_acciones, pps_acciones_aprobadores, pps_beneficios, pps_beneficios_aprobadores, pps_capacitaciones_progreso, pps_puntos_usuario, pps_registro_acciones, pps_reclamos_beneficios
- **Malla Operaciones:** coordinador, asesor, punto_venta_malla, registro_laboral
- **Listado Compras:** listado_productos_supli, listado_productos_internacionales, listado_productos_nacionales
- **Valoración:** valoracion_competencias, valoracion_preguntas, valoracion_ciclos, valoracion_asignaciones, valoracion_resultados, valoracion_respuestas, valoracion_planes_accion

---

## Convenciones de Anotaciones

| Anotación | Significado |
|-----------|-------------|
| `[PRIMARY KEY]` | Clave primaria |
| `[AUTO]` | Valor generado automáticamente (AutoField / auto_now_add / auto_now / uuid4) |
| `[UNIQUE]` | Restricción de unicidad a nivel de columna |
| `[COMPUTED]` | Valor calculado en el método `save()` del modelo, no editable directamente |
| `[DEFAULT x]` | Valor por defecto en Django |
| `[CHECK >= 0]` | Restricción implícita por `PositiveIntegerField` / `PositiveSmallIntegerField` |
| `[OneToOne]` | Relación uno a uno (UNIQUE en la FK) |
| `[SELF]` | Auto-referencia (FK a la misma tabla) |
| `[CASCADE]` | `on_delete=CASCADE` |
| `[PROTECT]` | `on_delete=PROTECT` (impide borrar si hay registros relacionados) |
| `[SET_NULL]` | `on_delete=SET_NULL` |
| `choices: a \| b` | Valores permitidos para campos con `choices` en Django |
