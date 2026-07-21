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
- Las imágenes (`static/uploads`, `static/noticias`, `static/logos`,
  `static/fondos`, `logo.png`, `fondo.jpg`) **NO** están cubiertas por el
  Volume (Railway solo permite 1 Volume en el plan actual). Estas siguen
  viviendo en git como respaldo. Ver la sección "Imágenes" más abajo.

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

## Imágenes (uploads, noticias, logos, fondos)

Como estas NO están en el Volume, si un usuario sube una foto/logo nueva
**directamente en producción**, esa imagen solo existe en el contenedor
actual — un futuro deploy la puede perder si no está en git.

**Antes de hacer push de un cambio de código**, si sospechas que hay
imágenes nuevas subidas en producción que no tienes en local:

1. Entra a `/panel/admin/backup` (superadmin) en producción y descarga el zip.
2. Extrae y copia lo que haya en `static/logos/`, `static/fondos/`,
   `static/logo.png`, `static/fondo.jpg` sobre tu carpeta local.
3. Para fotos de propiedades (`static/uploads/`) y noticias
   (`static/noticias/`) no hay backup automático todavía — si es crítico,
   pide ayuda para agregarlas al backup antes de continuar.
4. `git add` esas imágenes junto con tu cambio de código y sube todo junto.

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
