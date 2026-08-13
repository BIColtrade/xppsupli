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
Todos los retos se califican con la misma estructura:

| Criterio | Puntaje |
|---|---|
| Cumplio el reto | 10 pts |
| Presento evidencia | 5 pts |
| Genero impacto demostrable | 10 pts |
| **TOTAL por reto** | **25 pts** |

## 2. Semaforo

| Puntaje | Estado |
|---|---|
| 90-100 | 🟢 Leadership Champion |
| 80-89 | 🟢 Alto desempeno |
| 70-79 | 🟡 En consolidacion |
| 60-69 | 🟠 Requiere fortalecimiento |
| Menos de 60 | 🔴 Requiere intervencion |

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
| `ParticipacionReto` | `pulse_participaciones` | Reporte del lider + calificacion 10/5/10 validada |
| `PuntajeMensual` | `pulse_puntajes_mensuales` | Consolidado mensual: puntaje, detalle por pilar, semaforo y posicion |

---

## 4. Flujo operativo

1. **Inscripcion automatica.** People entra a *Leadership Team* → **Sincronizar lideres**.
   Se inscriben todos los usuarios activos con `tipo_usuario` lider/admin o que tengan
   reportes directos. Tambien se puede inscribir manualmente.
2. **Configuracion del mes.** *Ciclos* → **Nuevo ciclo** (mes, ano, fechas, estado).
   Al guardar, se cargan los 4 pilares oficiales y se pasa directo a la carga de retos.
3. **Retos semanales.** Un reto por semana (1-4), cada uno asociado a un pilar, con sus
   criterios de cumplimiento, evidencia e impacto. Al crearlo, la participacion se genera
   automaticamente para todo el Leadership Team activo.
4. **Reporte del lider.** *Mis Retos* → **Reportar**: declara cumplimiento, adjunta enlace
   y/o descripcion de evidencia, y describe el impacto. Pasa a estado `en_revision`.
   No se acepta declarar cumplimiento sin soporte de evidencia.
5. **Validacion.** People/Admin entra a *Bandeja de Validacion*, revisa la evidencia
   objetiva y marca los tres criterios (10 + 5 + 10). Tambien puede **devolver** el reporte
   con observaciones (puntaje 0 hasta que se corrija).
6. **Consolidacion mensual.** *Ciclos* → **Consolidar**. Suma solo participaciones
   `validado`, arma el detalle por pilar, aplica el semaforo y calcula la posicion.
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
| Bandeja de validacion | `validacion/` | People / Admin |
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
- Solo suman las participaciones en estado **validado**; lo autodeclarado no puntua hasta
  que People lo respalde con evidencia.
- El puntaje mensual se topa en el maximo del ciclo (100 pts).
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
