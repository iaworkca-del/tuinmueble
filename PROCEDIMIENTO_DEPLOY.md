# Procedimiento: cambios en local → producción

Este documento existe porque el 2026-07-11 casi se pierden datos reales de
producción (usuarios, propiedades, configuración) al hacer push de cambios
de código. Esto **ya no puede volver a pasar** si se sigue este procedimiento,
porque ahora la base de datos vive en un **Volume persistente de Railway**
(`/app/data`), separado de git.

## Cómo está protegido ahora

- `data/propiedades.db` y `data/branding*.json` están en `.gitignore`.
  Git **ya no los toca**. Viven solo en el Volume de Railway.
- Un `git push` a `tuinmueble.git` (repo conectado a Railway) actualiza el
  **código**. El Volume con los datos reales **no se ve afectado** por un
  deploy, sin importar qué haya en el `data/` del repositorio.
- (2026-07-22) Las imágenes subidas por usuarios — `uploads` (fotos/PDFs de
  propiedades), `logos`, `fondos`, `plantillas_custom` y `noticias` — se
  movieron a `data/uploads`, `data/logos`, `data/fondos`,
  `data/plantillas_custom` y `data/noticias` (dentro del mismo Volume, no
  hace falta un segundo Volume). Se siguen sirviendo en las mismas URLs
  `/static/uploads/...`, `/static/logos/...`, etc. gracias a mounts
  específicos en `main.py`. Antes vivían en `static/` y un logo o foto
  subida directo en producción se perdía en el siguiente deploy — ya no.
  `logo.png` y `fondo.jpg` (los valores por defecto de fábrica) siguen en
  `static/` porque son un asset del código, no contenido de usuario.

## Flujo normal de trabajo

1. Trabaja y prueba localmente como siempre (`data/propiedades.db` local
   puede tener datos de prueba, no importa — ya no se sube a git).
2. Antes de hacer commit, corre `git status` y confirma que **no aparece**
   `data/propiedades.db` ni `data/branding*.json` en la lista de cambios.
   Si aparecen, algo está mal — avisa antes de continuar.
3. `git add` solo de los archivos de código/plantillas que realmente
   cambiaste (nunca `git add -A` a ciegas en este proyecto).
4. Commit + `git push origin main` (repo `tuinmueble.git`).
5. Railway redespliega el código. La base de datos del Volume sigue intacta.
6. Verifica en producción con un GET normal (no hace falta nada especial).

## Imágenes (uploads, noticias, logos, fondos, plantillas)

Desde el 2026-07-22 estas carpetas viven en `data/` (Volume persistente),
igual que la base de datos. Un logo o foto subida directo en producción
**ya sobrevive** a los deploys de código sin necesidad de nada manual.

Si en algún momento se recrea el Volume desde cero (raro, pero posible),
usa `/panel/admin/backup` (incluye `logos/` y `fondos/`, no `uploads/` ni
`noticias/` por su tamaño) y `/panel/admin/restaurar` para recuperarlo.

## Reglas duras (nunca)

- Nunca `git add data/propiedades.db` ni `data/branding*.json` a mano.
- Nunca hacer POST de prueba a `/configuracion`, `/generar`, ni otros
  endpoints que graban datos reales en producción.
- Nunca borrar ni recrear el Volume de Railway sin bajar antes un backup
  fresco vía `/panel/admin/backup`.
- Si algún día se necesita restaurar datos en el Volume (por ejemplo tras
  crear un Volume nuevo), usar `/panel/admin/restaurar` (superadmin) con
  un zip generado por `/panel/admin/backup`. Nunca reemplazar el Volume
  a mano sin ese respaldo.

## Endpoints relevantes (solo superadmin)

- `GET /panel/admin/backup` — descarga zip con datos actuales (db + branding + logos/fondos).
- `GET /panel/admin/restaurar` — sube un zip y sobrescribe los datos del Volume con su contenido.
