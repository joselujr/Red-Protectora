# Red Protectora

**Web:** https://red-protectora.vercel.app

Red Protectora conecta a las protectoras de animales con las personas que quieren ayudarlas. Las protectoras publican los animales que buscan hogar y lo que necesitan de forma concreta (qué, cuánto y hasta cuándo: pienso, mantas, dinero para una operación, tiempo de voluntariado...). Los colaboradores eligen con qué necesidad ayudar o solicitan la adopción de un animal, y siguen el estado de todo desde su actividad.

Sin cuenta se puede ver todo el contenido público: necesidades, animales, protectoras y el mapa. La cuenta solo hace falta para colaborar, adoptar o gestionar una protectora.

---

## Índice

- [Tecnologías](#tecnologías)
- [Reglas del equipo](#reglas-del-equipo)
- [Flujo de trabajo](#flujo-de-trabajo)
- [Notas de Git](#notas-de-git)
- [Despliegue: Vercel + Supabase](#despliegue-vercel--supabase)
- [Base de datos en desarrollo](#base-de-datos-en-desarrollo)
- [Directorios](#directorios)
- [Modelo de datos](#modelo-de-datos)
- [Roles de usuario](#roles-de-usuario)
- [Secciones y páginas principales](#secciones-y-páginas-principales)
- [Lógica de estados](#lógica-de-estados)
- [Lógica de negocio de adopciones](#lógica-de-negocio-de-adopciones)
- [Lógica de negocio de necesidades](#lógica-de-negocio-de-necesidades)
- [APIs externas](#apis-externas)
- [Cloudinary](#cloudinary)

---

## Tecnologías

| Parte | Tecnología |
| --- | --- |
| Frontend | React 18 + Vite, React Router, Bootstrap 5, Leaflet (mapas) |
| Backend | Python 3.12, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended (autenticación) |
| Base de datos | PostgreSQL en Supabase |
| Imágenes y vídeos | Cloudinary |
| Alojamiento | Vercel (frontend y API en el mismo dominio) |
| Servicios externos | ip-api.com y Nominatim / OpenStreetMap (geolocalización y mapa) |

---

## Reglas del equipo

1. La rama `develop` está bloqueada para hacer push: todo se integra mediante Pull Request (Ruleset en GitHub).
2. No se sube el `.env` al repositorio (`.gitignore`).
3. No se sube `/migrations` al repositorio (`.gitignore`).
4. Documentar siempre en `.env.example` y en este README las variables que necesitemos y qué son.

---

## Flujo de trabajo

| Stage | Finalidad | Notas |
| --- | --- | --- |
| Backlog | Todas las ideas a desarrollar | Puede ser solo una idea |
| Ready to Work | Tareas aprobadas para realizar | Ya hemos aprobado que se hace |
| Work in progress | Tareas ya empezadas y asignadas a alguien que está trabajando en ellas | Aquí es donde te creas la rama para empezar a desarrollar: `git switch -c tareaXX` |
| Review | Hay un Pull Request pendiente de revisar | |
| Done | Finalizada y con merge en la rama `develop` | Al hacer merge en `develop`, Vercel publica la web automáticamente |

---

## Notas de Git

- `git fetch`: descarga la información de los cambios del remoto, sin aplicarlos
- `git pull`: descarga y aplica los cambios de la rama
- `git switch RAMA`: cambia de rama
- `git add .`: añade todo lo modificado al área de preparación (staging)
- `git commit -m "mensaje"`: crea el commit
- `git push -u origin tareaXXX`: sube la rama

**Integrar los cambios de `develop` en mi rama:**

```sh
git checkout develop
git pull origin develop
git checkout <nombre-de-tu-rama>
git pull origin develop
```

---

## Despliegue: Vercel + Supabase

- **Frontend y API en Vercel**, en el mismo dominio. [`vercel.json`](/vercel.json) construye Vite (`dist/`) y redirige `/api/*` a la función Python [`api/index.py`](/api/index.py), que carga `src/app.py`.
- **Despliegues automáticos:** cada merge en `develop` publica la web en producción (https://red-protectora.vercel.app). El resto de ramas generan un despliegue de prueba (Preview) al subirlas.
- **Base de datos en Supabase** (PostgreSQL). Vercel usa el *Transaction pooler* (puerto 6543); en Vercel la app no mantiene un pool de conexiones propio (`NullPool`, ver `src/app.py`).
- **Migraciones:** se aplican desde tu equipo contra el *Session pooler* (puerto 5432), nunca en el build: `DATABASE_URL=<session pooler> pipenv run upgrade`.
- **Variables en Vercel:** `DATABASE_URL`, `JWT_SECRET_KEY`, `FLASK_APP_KEY`, `CLOUDINARY_*`, `FLASK_DEBUG=0`, `VITE_BASENAME=/` y `VITE_PUBLIC_URL`. `VITE_BACKEND_URL` se deja vacía.
- **Solo en desarrollo** (`FLASK_DEBUG=1`): `/admin`, `/api/seed`, `/api/hello`, `/api/testgeo` y `/api/testip`. En producción responden 404; `/api/seed` se puede habilitar temporalmente con `ALLOW_SEED=1`.
- **Dependencias de Python:** Vercel usa `requirements.txt`. Si cambias el `Pipfile`, regenéralo con `pipenv requirements > requirements.txt`.

---

## Base de datos en desarrollo

Usa el [`Makefile`](/Makefile) de la raíz del proyecto (`make help` lista los comandos disponibles).

1. Vacía la base de datos actual y el registro de migraciones, y la inicializa de nuevo aplicando `migrate`/`upgrade`:

   ```sh
   make reset-db
   ```

2. Repuebla los datos de prueba (y las tablas auxiliares). Con el backend arrancado (`pipenv run start`), llama a `/api/seed` en la URL definida en `VITE_BACKEND_URL` de tu `.env`:

   ```sh
   make seed
   ```

---

## Directorios

| Tipo | Ruta | Finalidad |
| --- | --- | --- |
| Vistas | `/public/vistas` | Mockups de las vistas a desarrollar en Figma |
| UML | `/docs/database/uml.txt` | Documento UML del proyecto |
| Vercel | `/api` | Punto de entrada de la API Flask en Vercel (`index.py`) |
| Backend | `/src/api/data` | Almacén de JSON para seeds, fixtures y datos de prueba |
| Backend | `/src/api/routes` | Ficheros de rutas con los endpoints de la API |
| Backend | `/src/api/models` | Modelado de los objetos de la base de datos |
| Backend | `/src/api/repositories` | Capa de acceso a datos: encapsula todas las consultas, inserciones, actualizaciones y eliminaciones de la base de datos |
| Backend | `/src/api/services` | Lógica de la aplicación: aplica las reglas del sistema |
| Frontend | `/src/front/components` | Componentes React reutilizables |
| Frontend | `/src/front/components/navigation` | Navbar y menú de enlaces del usuario |
| Frontend | `/src/front/hooks` | Custom hooks y store (context) |
| Frontend | `/src/front/pages` | Páginas con contenido |
| Frontend | `/src/front/routes` | `routes.jsx` y componentes de guarda de rutas |
| Frontend | `/src/front/services` | Capa de lógica de la aplicación en JS (llamadas a la API) |

---

## Modelo de datos

- UML en formato texto: [ver UML](/docs/database/uml.txt), adaptado a https://dbdiagram.io/

![UML](/docs/database/UML.png)

---

## Roles de usuario

| Rol | Tipo |
| --- | --- |
| none | Visitante sin identificar |
| shelter_admin | Usuario de una protectora: gestiona los animales, las necesidades y las solicitudes de su protectora |
| volunteer | Colaborador, no vinculado a ninguna protectora: colabora con necesidades o solicita adoptar animales |

Cada cuenta tiene un solo rol, que se elige al registrarse.

---

## Secciones y páginas principales

### Home (`/`)
- Como usuario invitado o colaborador, muestra un hero con información sobre la plataforma y enlaces a las secciones principales.
- Con un usuario identificado como protectora, muestra el dashboard con atajos a las principales secciones de su panel.
- La imagen del hero rota entre un set de imágenes locales.

### Necesidades (`/necesidades`)
- Listado de necesidades con su representación en un mapa.
- Filtrado básico por tipo.
- `/necesidades/:id`: detalle de la necesidad, desde donde un colaborador se compromete con su parte («Colaborar»).

### Adoptar (`/adoptar`)
- Catálogo de animales con su representación en un mapa, paginado de 12 en 12.
- Filtros por especie (todos, perros, gatos, otros), edad (cachorro, adulto, senior) y tipo de entidad. Los filtros y la página se guardan en la URL, así que al volver atrás el listado sale como lo dejaste.
- Para una protectora, el catálogo muestra los animales de toda la red, con accesos directos a sus adopciones y sus animales.
- `/adoptar/:id`: ficha del animal (historia, salud, convivencia, hogar ideal y sus necesidades). Si su proceso de adopción está abierto, muestra el botón «Adoptar» para enviar la solicitud.

### Protectoras (`/protectoras`)
- Listado de protectoras con su ubicación en el mapa, paginado.
- Pestañas para ver todas, solo las que tienen necesidades urgentes o solo las que tienen animales en adopción, y filtro por tipo de entidad.
- `/protectoras/:id`: ficha pública de la protectora con sus datos, contacto, ubicación, sus necesidades actuales («Lo que más necesitan ahora») y sus animales en adopción («Buscan hogar»).

### Ayuda (`/ayuda`)
- Centro de ayuda: explica cómo funciona la plataforma en tres pasos.
- Guías paso a paso según el perfil: colaborar, adoptar, protectora y cuenta.
- Significado de las etiquetas de las tarjetas («En 2 días», «Cubierta», «En adopción», «Te necesita»...) y preguntas frecuentes filtrables por tema.

### Términos de uso y privacidad (`/terminos-y-privacidad`)
- Información legal en tres apartados: términos de uso, privacidad, y cookies y almacenamiento local.
- Se puede enlazar directamente a cada apartado (por ejemplo, el aviso de cookies enlaza a `#cookies`).

### Login, Signup y Logout (`/login`, `/signup`, `/logout`)
- **Signup:** crear cuenta eligiendo el rol (voluntario o protectora). Si es protectora, pide también los datos de la entidad: nombre, correo y teléfono públicos, tipo y dirección.
- **Login:** inicio de sesión con correo y contraseña. Si se llega desde una acción que requiere cuenta (colaborar o adoptar), devuelve al usuario a donde estaba.
- **Logout:** cierra la sesión, revoca el token en el servidor y redirige al login.
- **Recuperar contraseña:** pendiente de implementar. El enlace «¿Has olvidado tu contraseña?» del login apunta a `/recovery`, que todavía no existe.

---

## Lógica de estados

Los campos `status` del dominio de adopción tienen su fuente de verdad en el service que "posee" cada entidad, no en el modelo, ni en el repositorio, ni en el frontend. Modelos y repositorios son agnósticos del valor concreto (solo el `default` de columna fija un literal, por ser inevitable); rutas y frontend consumen constantes y mapas importados desde ahí en vez de repetir los strings.

### Animal y adopción

#### `Animal.status`: lo controla [`animals_service.py`](/src/api/services/animals_service.py)

| Valor | Significado |
| --- | --- |
| `activado` | Único estado visible en las vistas públicas (`/adoptar`, `/adoptar/:id`): `PUBLIC_STATUSES`. |
| `desactivado` | Oculto del catálogo público, reversible desde el panel de la protectora (botón Desactivar/Reactivar). |
| `borrador` | Ficha incompleta, nunca visible públicamente. |

#### `AddoptionProcess.status`: lo controla [`addoption_process_service.py`](/src/api/services/addoption_process_service.py)

| Valor | Significado |
| --- | --- |
| `abierto` | El proceso admite nuevas `AddoptionRequest` (sujeto también al rango de fechas); ver `is_process_open_for_requests`. |
| `cerrado` | Ya no admite solicitudes nuevas. |

- Punto que cierra un proceso: `close_addoption_process(process)`. Lo invocan tanto el cierre automático al alcanzar el límite de solicitudes simultáneas como la aceptación de una solicitud.
- Abrir o editar un proceso siempre lo deja en `abierto`, incluso si estaba `cerrado` (permite relanzarlo).

#### `AddoptionRequest.status`: lo controla [`addoption_request_service.py`](/src/api/services/addoption_request_service.py)

| Valor | Significado |
| --- | --- |
| `pendiente` | Recién creada, sin revisar. |
| `aceptada` | La protectora la ha aprobado. |
| `descartada` | Rechazada (individualmente o en bloque). |

- `accept_addoption_request`: marca la solicitud como `aceptada`, cierra el proceso asociado (`close_addoption_process`) y descarta automáticamente (`descartada`) el resto de solicitudes `pendiente` del mismo proceso, para que nunca quede más de una aceptada.
- `discard_addoption_requests`: descarte en bloque; solo afecta a las que siguen `pendiente`.

### Necesidades y colaboraciones

#### `Request.status`: lo controla [`requests_service.py`](/src/api/services/requests_service.py)

| Valor | Significado |
| --- | --- |
| `abierta` | Admite nuevas `UserRequest` (colaboraciones); ver `is_request_contributable`. |
| `cerrada` | Ya no admite colaboraciones nuevas: se alcanza automáticamente cuando la suma de colaboraciones cubre `amount_needed`. |
| `borrador` | Necesidad incompleta, nunca visible públicamente. |

- Punto que cierra una necesidad: `_close_request_if_conseguido` en [`user_request_service.py`](/src/api/services/user_request_service.py), invocado tras cada colaboración creada. Solo aplica si la necesidad tiene `amount_needed` definido; sin objetivo (`amount_needed=None`) no hay cierre automático por acumulado.
- A diferencia de `AddoptionProcess`, hoy no existe una vía para que la protectora reabra o cierre una necesidad a mano (`SETTABLE_STATUSES` solo admite `abierta`/`borrador` desde el formulario).

---

## Lógica de negocio de adopciones

Restricciones que aplican a `animal`, `addoption_process` y `addoption_request` al gestionar animales, procesos y solicitudes de adopción.

**Animales**

- Solo los animales en estado `activado` aparecen en el catálogo público y en su ficha; los que están en `borrador` o `desactivado` quedan ocultos aunque sigan existiendo.
- Una protectora solo puede ver y editar sus propios animales.
- Animales funciona como un catálogo de recursos de la protectora: muestra tanto los animales que pueden ser adoptados como los que tienen necesidades vinculadas.

**Procesos de adopción**

- Cada animal solo puede tener un proceso de adopción a la vez.
- Un proceso solo admite solicitudes nuevas mientras está `abierto` y, si tiene fechas configuradas, dentro de ese rango.
- Si se configura un límite de solicitudes simultáneas, el proceso se cierra cuando se alcanza ese número.
- El proceso se cierra solo en dos casos: cuando la protectora acepta una solicitud, o cuando se alcanza el límite de solicitudes simultáneas que ella misma configuró.
- Las fechas del proceso son opcionales y las configura la protectora. Fuera de esas fechas el proceso sigue abierto, pero no es accesible.
- Reabrir o editar un proceso siempre lo deja `abierto`, aunque estuviera cerrado.
- Un proceso solo se puede eliminar si todavía no ha recibido ninguna solicitud; si ya tiene alguna, la única opción es cerrarlo (se conserva el historial).

**Solicitudes de adopción**

- Un usuario solo puede enviar una solicitud por proceso de adopción, y no puede repetirla aunque la anterior haya sido descartada.
- Solo se puede solicitar la adopción de un animal si su proceso está abierto en ese momento.
- Hay que responder todas las preguntas del proceso para poder enviar la solicitud.
- Aprobar una solicitud es una acción individual (no en bloque) y descarta automáticamente el resto de solicitudes pendientes del mismo proceso, para que nunca quede más de una aceptada.
- Descartar en bloque solo afecta a las solicitudes que siguen pendientes; ignora las que ya estaban aprobadas o descartadas.
- Una protectora solo puede ver y gestionar las solicitudes de sus propios procesos de adopción.

---

## Lógica de negocio de necesidades

Restricciones que aplican a `request` y `user_request` al gestionar necesidades y colaboraciones.

**Necesidades**

- Solo las necesidades en estado `abierta` o `cerrada` son visibles públicamente (`/necesidades`, `/necesidades/:id`); las que están en `borrador` quedan ocultas aunque sigan existiendo.
- Una protectora solo puede ver y editar sus propias necesidades.
- Una necesidad puede tener un objetivo concreto (`amount_needed` definido, en la `unit` que corresponda: €, kg, turnos...) o quedar sin límite (`amount_needed=None`); solo las que tienen objetivo se cierran solas al cubrirse.

**Colaboraciones (`UserRequest`)**

- Solo se puede colaborar con una necesidad mientras está `abierta` y, si tiene fecha límite (`request_deadline`), dentro de ese plazo; ver `is_request_contributable`.
- Cada colaboración aporta una cantidad (`amount`, obligatoria si la necesidad tiene objetivo) y/o unos detalles en texto libre (`details`, por ejemplo cómo o cuándo se va a entregar); hace falta al menos uno de los dos.
- La web no gestiona pagos ni transacciones: la entrega se acuerda directamente con la protectora. Si el proyecto continúa, se integraría un sistema de pagos.
- Un mismo usuario puede colaborar varias veces con la misma necesidad (no hay restricción).

---

## APIs externas

### 1) IP-API ➡️ ip-api.com (gratuito, sin API key)

Geolocaliza de forma aproximada la IP del visitante, para centrar el mapa de inicio cuando el usuario todavía no ha compartido la ubicación de su navegador.

- Implementación: [`geolocation_service.py`](/src/api/services/geolocation_service.py) → `locate_ip(ip)`.
- Se consume desde `GET /api/data` ([`src/api/routes/data.py`](/src/api/routes/data.py)) y se expone al frontend como `user_location`.
- Devuelve `"lat,lon"`, o `None` si no puede obtener la IP o el servicio externo falla.
- Ruta de prueba manual (solo en desarrollo): `GET /api/testip`, en [`testgeo.py`](/src/api/routes/testgeo.py), con una llamada directa vía `requests` a modo de ejemplo y depuración.

### 2) Nominatim ➡️ nominatim.org (gratuito, sin API key)

Geocodifica una dirección en texto (calle, ciudad...) a sus coordenadas, para calcular el `map_positioning` de usuarios y protectoras.

- Implementación: [`geolocation_service.py`](/src/api/services/geolocation_service.py) → `locate_address(direccion)`. Requiere un `User-Agent` propio por la política de uso de Nominatim.
- Se consume desde `update_user_profile` ([`users_service.py`](/src/api/services/users_service.py)) y `update_shelter_profile` ([`shelters_service.py`](/src/api/services/shelters_service.py)) cada vez que cambia el campo `address`. Si el geocoding falla por cualquier motivo, no bloquea el guardado del resto del perfil: simplemente no actualiza `map_positioning`.
- Ruta de prueba manual (solo en desarrollo): `GET /api/testgeo`, en [`testgeo.py`](/src/api/routes/testgeo.py), con una llamada directa vía `requests` a modo de ejemplo y depuración.

### 3) Cloudinary

Almacena las imágenes y vídeos de los animales, las necesidades y los logos de las protectoras. Ver la sección [Cloudinary](#cloudinary).

---

## Cloudinary

Permite guardar en Cloudinary las imágenes y vídeos de los animales y las necesidades, y el logo de cada protectora.

### 1. Configuración

Consultar los requisitos en el mensaje fijado en Slack.

Completar en el `.env`:

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

En local, comprobar que `VITE_BACKEND_URL` apunta al backend del puerto 3001, sin `/api` al final.

No subir el `.env` a GitHub. En `.env.example`, dejar las credenciales vacías.

### 2. Iniciar la aplicación en local

En una terminal, iniciar el backend:

    pipenv run start

En otra terminal, iniciar el frontend:

    npm run start

Si se modifican las variables de entorno, reiniciar el servidor correspondiente.

### 3. Subir imágenes a una ficha

1. Iniciar sesión con una cuenta de protectora.
2. Abrir el formulario de creación o edición de un animal o una necesidad.
3. Seleccionar una imagen y guardar la ficha.
4. Actualizar la página para comprobar que la imagen sigue apareciendo.

El archivo se guarda en Cloudinary. Su URL y su identificador se guardan en la base de datos, asociados a la ficha.

Desde el formulario también se puede cambiar la portada o eliminar una imagen. Al eliminarla, se borra tanto su registro como el archivo de Cloudinary.

### 4. Subida directa (firmada)

El archivo **no pasa por la API**, porque Vercel no admite peticiones de más de 4,5 MB. La subida se hace en tres pasos (ver [`cloudinaryService.js`](/src/front/services/cloudinaryService.js) y [`media_upload_service.py`](/src/api/services/media_upload_service.py)):

1. `POST …/media/upload-signature` (`{content_type, size}`): el backend valida permisos, tipo y tamaño, y devuelve una firma.
2. El navegador sube el archivo directamente a Cloudinary con esa firma.
3. `POST …/media` (`{media_id, resource_type, is_cover}`): el backend comprueba en Cloudinary lo que se subió (formato y tamaño reales) y lo registra.

Rutas: `/api/shelter/animals/<id>/media`, `/api/shelter/requests/<id>/media` y `/api/shelter/logo`.

Límites: imágenes JPG o PNG de hasta 10 MB y vídeos MP4 o MOV de hasta 50 MB.

### 5. Comprobaciones realizadas

Se han probado, en animales y necesidades, la subida de imágenes y vídeos (también de más de 5 MB), la persistencia al recargar, el cambio de portada y la eliminación, además de la subida y eliminación del logo de la protectora.

Las imágenes locales anteriores siguen disponibles y no se migran automáticamente a Cloudinary.
