# Leadership Pulse

> El sistema que convierte el liderazgo en una ventaja competitiva.

Modulo de reconocimiento, seguimiento y desarrollo del Leadership Team, integrado a
Leadership OS para fortalecer la adopcion de SUPLI OS mediante una cultura high
performance, mejora continua y excelencia en la ejecucion.

URL base: `/leadership/pulse/`

---

## 1. Estructura de puntaje

| Pilar | Puntaje maximo |
|---|---|
| Cultura High Performance | 25 |
| Ritmo SUPLI | 25 |
| Infraestructura Tecnologica | 25 |
| KMS | 25 |
| **TOTAL mensual** | **100** |

Cada semana del ciclo tiene **un reto** asociado a un pilar y vale **25 puntos**.

### Medicion vigente: cumple / no cumple

Por ahora se mide **unicamente si el lider cumple o no** el reto asignado. Por cada
persona y reto se registran tres cosas:

| Campo | Que es |
|---|---|
| **Participo** | Si la persona participo o no en el reto |
| **Cumplio** | Unico criterio de calificacion: cumple o no cumple |
| **Observaciones** | Campo libre de seguimiento, se diligencia reto a reto |

El puntaje es binario: el reto vale **25 pts completos si se cumple** y **0 si no**.
Quien no participa no puede cumplir (el sistema lo fuerza en `recalcular_puntaje`).

De ahi salen las dos metricas de seguimiento individual:

- **% de participacion** = retos participados / retos asignados
- **% de cumplimiento** = retos cumplidos / retos asignados

Los criterios de evidencia e impacto (el antiguo esquema 10 + 5 + 10) quedaron
inactivos, no se califican ni suman. Las columnas siguen en la base
(`pts_evidencia`, `pts_impacto`, `criterio_evidencia`, `criterio_impacto`) por si se
retoma ese modelo mas adelante.

## 2. Semaforo

Se lee sobre el **% de cumplimiento**, no sobre el puntaje bruto, para que sea
comparable aunque el ciclo aun no tenga sus 4 retos cargados.

| % de cumplimiento | Estado |
|---|---|
| 90-100 | Leadership Champion |
| 80-89 | Alto desempeno |
| 70-79 | En consolidacion |
| 60-69 | Requiere fortalecimiento |
| Menos de 60 | Requiere intervencion |

El semaforo se calcula en `leadership_pulse/models.py` (`calcular_semaforo`) a partir
de `SEMAFORO_RANGOS`.

---

## 3. Modelo de datos

| Modelo | Tabla | Rol |
|---|---|---|
| `Pilar` | `pulse_pilares` | Los 4 pilares SUPLI OS y su puntaje maximo |
| `MiembroLeadershipTeam` | `pulse_miembros` | Lideres inscritos (participacion automatica) |
| `CicloPulse` | `pulse_ciclos` | Mes de evaluacion (100 pts), estado y publicacion del ranking |
| `RetoSemanal` | `pulse_retos` | Reto de la semana (1-4), pilar, criterios y vigencia |
| `ParticipacionReto` | `pulse_participaciones` | Registro por persona y reto: `participo`, `cumplio`, `observaciones` |
| `PuntajeMensual` | `pulse_puntajes_mensuales` | Consolidado mensual: % participacion, % cumplimiento, semaforo y posicion |

---

## 4. Flujo operativo

1. **Inscripcion automatica.** People entra a *Leadership Team* → **Sincronizar lideres**.
   Se inscriben todos los usuarios activos con `tipo_usuario` lider/admin o que tengan
   reportes directos. Tambien se puede inscribir manualmente.
2. **Configuracion del mes.** *Ciclos* → **Nuevo ciclo** (mes, ano, fechas, estado).
   Al guardar, se cargan los 4 pilares oficiales y se pasa directo a la carga de retos.
3. **Retos semanales.** Un reto por semana (1-4), cada uno asociado a un pilar, con su
   criterio de cumplimiento. Al crearlo, la participacion se genera automaticamente para
   todo el Leadership Team activo.
4. **Reporte del lider (opcional).** *Mis Retos* → **Reportar**: marca si participo, si
   cumplio, y adjunta un soporte o comentario. Pasa a estado `en_revision`. Es informativo:
   el registro que cuenta lo hace People.
5. **Registro del seguimiento.** People/Admin entra a *Seguimiento de Retos*. Tiene dos
   formas de registrar:
   - **Grilla por semana** (`retos/<id>/registro/`): una fila por lider con las casillas
     *Participo* / *Cumplio* y su campo de observaciones. Se guarda todo el equipo de una vez.
   - **Registro individual**: la misma informacion persona por persona, con opcion de
     **devolver** el reporte al lider.
6. **Consolidacion mensual.** *Ciclos* → **Consolidar**. Cuenta retos participados y
   cumplidos, calcula los dos porcentajes, arma el detalle por pilar, aplica el semaforo
   sobre el % de cumplimiento y calcula la posicion del ranking.
7. **Publicacion del ranking.** *Ciclos* → **Publicar ranking**. Mientras no se publique,
   los lideres no ven la clasificacion; People, CEO y BI/Tech si.

---

## 5. Vistas y permisos

| Vista | URL | Acceso |
|---|---|---|
| Home Leadership Pulse | `home/` | Todo usuario autenticado con acceso al modulo |
| Mis Retos | `mis-retos/` | Lider (sus propios retos) |
| Reportar reto | `mis-retos/<id>/reportar/` | Dueno del reto o People/Admin |
| Mi Pulse | `mi-pulse/` | Cada lider |
| Pulse de un lider | `pulse/<usuario_id>/` | People / CEO / BI / Tech / Admin |
| Ranking | `ranking/` | Todos si esta publicado; People/CEO/BI/Tech siempre |
| Seguimiento de retos | `validacion/` | People / Admin |
| Grilla de registro por reto | `retos/<reto_id>/registro/` | People / Admin |
| Ciclos y retos | `ciclos/`, `ciclos/<id>/retos/` | People / BI / Tech / Admin |
| Pilares | `pilares/` | People / BI / Tech / Admin |
| Leadership Team | `miembros/` | People / Admin |

Roles (en `views.py`):

- `_es_admin_people` — area `people` con `tipo_usuario` admin/lider, o admin global.
- `_es_bi_tech` — area `bi` o `tecnologia`.
- `_es_ceo` — area `ceo`.
- `_es_lider` — `tipo_usuario` lider o con reportes directos.

El acceso al prefijo `/leadership/pulse/` tambien se filtra en
`core/middleware.py` (`GroupAccessMiddleware`): admin, grupo `leadershippulse`, areas
people/bi/tecnologia/ceo o `tipo_usuario` admin/lider.

---

## 6. Reglas de negocio implementadas

- La participacion es **automatica**: todo miembro activo del Leadership Team recibe cada
  reto sin accion manual, y la sincronizacion es idempotente.
- Solo cuentan las participaciones ya registradas por People; lo autodeclarado por el
  lider no puntua hasta que quede registrado.
- **Quien no participa no puede cumplir**: si `participo` es falso, `cumplio` se fuerza a
  falso y el puntaje queda en 0.
- El puntaje mensual se topa en el maximo del ciclo (100 pts).
- El ranking se ordena por **% de cumplimiento**, y desempata por **% de participacion**.
- Un reto no puede eliminarse si ya tiene participaciones validadas.
- No puede existir mas de un ciclo por mes/ano, ni mas de un reto por semana dentro del ciclo.
- El ranking muestra el **Top 3** y la tabla completa con semaforo y avance por lider.

---

## 7. Puesta en marcha

```bash
python manage.py migrate leadership_pulse
```

Luego, con un usuario People/Admin:

1. `/leadership/pulse/pilares/` → **Cargar pilares oficiales**.
2. `/leadership/pulse/miembros/` → **Sincronizar lideres**.
3. `/leadership/pulse/ciclos/` → **Nuevo ciclo** y sus 4 retos.

Opcionalmente, crear el grupo `leadershippulse` para dar acceso a usuarios que no
sean lider/People/BI/Tech/CEO.
