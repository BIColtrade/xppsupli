# Orden de Dependencias de Tablas - Base de Datos xppcoltrade

## Apps / Módulos Django

| App | Módulo | Descripción |
|-----|--------|-------------|
| `user` | Usuarios | Custom user model + reset de contraseña |
| `abastecimientos` | Abastecimiento | Canales, productos, puntos de venta, inventarios |
| `malla_operaciones_trade` | Malla Operaciones | Coordinadores, asesores, puntos de venta y registro laboral |
| `listado_compras` | Listado Compras | Catálogos de productos Supli, nacionales e internacionales |
| `bienestar_coltrade` | Bienestar (PPS) | Sistema de puntos, acciones, beneficios y progreso |
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
is_active               BOOLEAN (NOT NULL)
is_staff                BOOLEAN (NOT NULL)
area                    VARCHAR (NULL)   -- choices: trade | supli | people | comercial | logistica | tecnologia | finanzas | administracion | otra
tipo_usuario            VARCHAR (NULL)   -- choices: colaborador | lider | admin
```

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

---

## NIVEL 2: Dependencias Simples (Dependen de Nivel 1)

### 13. auth_group_permissions
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
group_id                INTEGER (NOT NULL) -> FK: auth_group.id
permission_id           INTEGER (NOT NULL) -> FK: auth_permission.id
```

### 14. password_reset_codes
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
code                    VARCHAR(6) (NOT NULL)
created_at              TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
expires_at              TIMESTAMP WITH TIME ZONE (NOT NULL)
used_at                 TIMESTAMP WITH TIME ZONE (NULL)
user_id                 BIGINT (NOT NULL) -> FK: user_usuario.id
```
> Índices: `(user_id, code)`, `(expires_at)`

### 15. user_usuario_groups
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
group_id                INTEGER (NOT NULL) -> FK: auth_group.id
```

### 16. user_usuario_user_permissions
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
permission_id           INTEGER (NOT NULL) -> FK: auth_permission.id
```

### 17. productos_abastecimiento
```
id_producto             VARCHAR (NOT NULL) [PRIMARY KEY]
nombre_producto         VARCHAR (NOT NULL)
marca                   VARCHAR (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal
```

### 18. puntos_venta_abastecimiento
```
id_puntoventa           VARCHAR (NOT NULL) [PRIMARY KEY]
punto_venta             VARCHAR (NOT NULL)
canal_regional          VARCHAR (NOT NULL)
tipo                    VARCHAR (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal
```

### 19. punto_venta_malla
```
id_punto                VARCHAR (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
zona                    VARCHAR (NOT NULL)   -- choices: Zona Sur | Zona Norte
coordinador_default_id  INTEGER (NULL) -> FK: coordinador.id_coordinador [SET_NULL]
asesor_default_id       INTEGER (NULL) -> FK: asesor.id_asesor [SET_NULL]
```

### 20. pps_acciones
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
descripcion             TEXT (NOT NULL)
nivel                   VARCHAR (NOT NULL)   -- choices: estrategico | tactico | desarrollo | activacion_bienestar | capacitacion
puntos_min              INTEGER (NOT NULL)
puntos_max              INTEGER (NOT NULL)
puntos_default          INTEGER (NOT NULL)
solo_lideres            BOOLEAN (NOT NULL) [DEFAULT False]
activa                  BOOLEAN (NOT NULL) [DEFAULT True]
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
youtube_url             VARCHAR (NULL)
areas                   JSONB (NOT NULL) [DEFAULT []]
destinatarios           VARCHAR (NOT NULL)   -- choices: todos | lideres | colaboradores
aplica_empresa          BOOLEAN (NOT NULL) [DEFAULT False]
fecha_fin               TIMESTAMP WITH TIME ZONE (NULL)
fecha_inicio            TIMESTAMP WITH TIME ZONE (NULL)
aprobador_todos         BOOLEAN (NOT NULL) [DEFAULT True]
```
> ManyToMany: `aprobadores` → user_usuario (a través de pps_acciones_aprobadores)

### 21. pps_beneficios
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
nombre                  VARCHAR (NOT NULL)
descripcion             TEXT (NOT NULL)
categoria               VARCHAR (NOT NULL)   -- choices: reconocimiento | tiempo | certificado | sorteo | desarrollo
puntos_requeridos       INTEGER (NOT NULL)
disponible              BOOLEAN (NOT NULL) [DEFAULT True]
stock                   INTEGER (NULL)       -- NULL = ilimitado
fecha_creacion          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
aprobador_todos         BOOLEAN (NOT NULL) [DEFAULT True]
imagen_url              VARCHAR (NULL)
niveles_permitidos      JSONB (NOT NULL) [DEFAULT []]   -- values: bronce | plata | oro | diamante
```
> ManyToMany: `aprobadores` → user_usuario (a través de pps_beneficios_aprobadores)

### 22. django_admin_log
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

### 23. django_session
```
session_key             VARCHAR (NOT NULL) [PRIMARY KEY]
session_data            TEXT (NOT NULL)
expire_date             TIMESTAMP WITH TIME ZONE (NOT NULL)
```

### 24. django_migrations
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
app                     VARCHAR (NOT NULL)
name                    VARCHAR (NOT NULL)
applied                 TIMESTAMP WITH TIME ZONE (NOT NULL)
```

---

## NIVEL 3: Dependencias Complejas (Dependen de Nivel 2)

### 25. pps_acciones_aprobadores
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
accionpps_id            BIGINT (NOT NULL) -> FK: pps_acciones.id
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
```
> Tabla through automática del ManyToMany `AccionPPS.aprobadores`

### 26. pps_beneficios_aprobadores
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
beneficio_id            BIGINT (NOT NULL) -> FK: pps_beneficios.id
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
```
> Tabla through automática del ManyToMany `Beneficio.aprobadores`

### 27. inventario_abastecimiento
```
id_inventario           INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_inventario     INTEGER (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa
```

### 28. meta_abastecimiento
```
id_meta                 INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_meta           INTEGER (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa
```

### 29. transitos_abastecimiento
```
id_transito             INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_transito       INTEGER (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa
```

### 30. ventas_abastecimiento
```
id_venta                INTEGER (NOT NULL) [PRIMARY KEY] [AUTO]
cantidad_venta          INTEGER (NOT NULL)
fecha_venta             DATE (NOT NULL)
id_canal_id             VARCHAR (NOT NULL) -> FK: canal.id_canal
id_producto_id          VARCHAR (NOT NULL) -> FK: productos_abastecimiento.id_producto
id_puntoventa_id        VARCHAR (NOT NULL) -> FK: puntos_venta_abastecimiento.id_puntoventa
```

### 31. pps_puntos_usuario
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
puntos_totales          INTEGER (NOT NULL) [DEFAULT 0]
nivel                   VARCHAR (NOT NULL) [DEFAULT 'bronce']   -- choices: bronce (<500) | plata (500-1499) | oro (1500-3999) | diamante (>=4000)
fecha_actualizacion     TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id [OneToOne] [UNIQUE]
```
> Lógica: `actualizar_nivel()` recalcula el nivel según `puntos_totales`

### 32. pps_capacitaciones_progreso
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
progreso_pct            SMALLINT (NOT NULL) [DEFAULT 0] [CHECK >= 0]
puntos_otorgados        INTEGER (NOT NULL) [DEFAULT 0] [CHECK >= 0]
completado              BOOLEAN (NOT NULL) [DEFAULT False]
fecha_actualizacion     TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
accion_id               BIGINT (NOT NULL) -> FK: pps_acciones.id
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
```
> Constraint: `UNIQUE (usuario_id, accion_id)`

### 33. pps_registro_acciones
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
descripcion_evidencia   TEXT (NOT NULL)
fecha_registro          TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
estado                  VARCHAR (NOT NULL) [DEFAULT 'pendiente']   -- choices: pendiente | aprobado | rechazado
puntos_asignados        INTEGER (NOT NULL) [DEFAULT 0]
fecha_resolucion        TIMESTAMP WITH TIME ZONE (NULL)
observacion_lider       TEXT (NOT NULL) [DEFAULT '']
accion_id               BIGINT (NOT NULL) -> FK: pps_acciones.id [PROTECT]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
aprobado_por_id         BIGINT (NULL) -> FK: user_usuario.id [SET_NULL]
```

### 34. pps_reclamos_beneficios
```
id                      BIGINT (NOT NULL) [PRIMARY KEY]
fecha_reclamo           TIMESTAMP WITH TIME ZONE (NOT NULL) [AUTO]
estado                  VARCHAR (NOT NULL) [DEFAULT 'pendiente']   -- choices: pendiente | entregado | cancelado
puntos_descontados      INTEGER (NOT NULL) [CHECK >= 0]
usuario_id              BIGINT (NOT NULL) -> FK: user_usuario.id
beneficio_id            BIGINT (NOT NULL) -> FK: pps_beneficios.id [PROTECT]
aprobado_por_id         BIGINT (NULL) -> FK: user_usuario.id [SET_NULL]
```

### 35. registro_laboral
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

---

## Resumen

**Total de Tablas: 35**

| Nivel | Cantidad | Descripción |
|-------|----------|-------------|
| Nivel 1 | 12 | Tablas base (sin dependencias) |
| Nivel 2 | 12 | Tablas con dependencias simples |
| Nivel 3 | 11 | Tablas con múltiples o dependencias complejas |

**Tablas Django internas (Framework):**
- auth_group, auth_permission, auth_group_permissions
- django_admin_log, django_content_type, django_migrations, django_session

**Tablas de Negocio:**
- **User Module:** user_usuario, password_reset_codes, user_usuario_groups, user_usuario_user_permissions
- **Abastecimiento:** canal, productos_abastecimiento, puntos_venta_abastecimiento, inventario_abastecimiento, meta_abastecimiento, transitos_abastecimiento, ventas_abastecimiento, abastecimiento_claro, abastecimiento_coltrade
- **Bienestar (PPS):** pps_acciones, pps_acciones_aprobadores, pps_beneficios, pps_beneficios_aprobadores, pps_capacitaciones_progreso, pps_puntos_usuario, pps_registro_acciones, pps_reclamos_beneficios
- **Malla Operaciones:** coordinador, asesor, punto_venta_malla, registro_laboral
- **Listado Compras:** listado_productos_supli, listado_productos_internacionales, listado_productos_nacionales

---

## Convenciones de Anotaciones

| Anotación | Significado |
|-----------|-------------|
| `[PRIMARY KEY]` | Clave primaria |
| `[AUTO]` | Valor generado automáticamente (AutoField / auto_now_add / uuid4) |
| `[UNIQUE]` | Restricción de unicidad a nivel de columna |
| `[COMPUTED]` | Valor calculado en el método `save()` del modelo, no editable directamente |
| `[DEFAULT x]` | Valor por defecto en Django |
| `[CHECK >= 0]` | Restricción implícita por `PositiveIntegerField` / `PositiveSmallIntegerField` |
| `[OneToOne]` | Relación uno a uno (UNIQUE en la FK) |
| `[CASCADE]` | `on_delete=CASCADE` |
| `[PROTECT]` | `on_delete=PROTECT` (impide borrar si hay registros relacionados) |
| `[SET_NULL]` | `on_delete=SET_NULL` |
| `choices: a \| b` | Valores permitidos para campos con `choices` en Django |
