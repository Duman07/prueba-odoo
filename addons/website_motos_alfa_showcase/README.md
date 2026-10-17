# Motos Alfa — Ficha de producto Hunk 150 XT (Odoo 18)

Estructura base de la página `/hunk-150-xt`, con fondo blanco y rojo como color de acento,
integrada en el sitio existente mediante `website.layout` (usa el encabezado, el menú y el pie de página del sitio).

## Qué incluye
- `views/hunk_150_xt_page.xml`: plantilla QWeb y registro `website.page` (se crea **sin publicar**).
- `static/src/scss/moto_showcase.scss`: estilos limitados a `.o_moto_showcase`.
- `static/src/js/moto_showcase.js`: widget público `MotoShowcase` con los puntos de extensión.

Secciones y contenedores reservados (`data-moto-slot`):

- Presentación: `model3d` (modelo GLB/glTF y animación de entrada, `data-moto-intro`).
- Vista 360° (`#moto-360`): `viewer360`, `colors`, `hotspots`.
- Especificaciones (`#moto-specs`): `specs`.
- Comercial (`#moto-comercial`): `pricing`, `benefits`.

No modifica el menú, otras páginas ni módulos existentes.

## Bloques del editor (grupo «Motos Alfa»)
En el editor del sitio: Editar → panel Bloques → categoría «Motos Alfa».

- «Moto 3D» (`s_moto_3d`): muestra un modelo GLB/glTF con animación de entrada (entrada, aceleración, giro a la derecha, frenada; 2,6 s). Se reproduce una vez al hacerse visible y tiene botón «Repetir animación». Se omite si el visitante pidió reducir el movimiento.
- «Visor 360°» (`s_moto_360`): rotación con arrastre, zoom, giro automático, restablecer vista y pantalla completa, con un panel lateral de Colores y Puntos destacados.
  - Colores: cada círculo se mueve, duplica o borra desde el editor. Opciones: color, nombre, un `.glb` propio para ese color o una variante de material del modelo.
  - Puntos destacados: el texto se edita directamente; cada punto se mueve, duplica o borra. Con la opción «Ubicación en el modelo → Ubicar» y un clic sobre la moto queda fijado su marcador numerado. En el editor, un número con borde punteado indica que el punto aún no está ubicado. Al pulsar un punto (en la lista o en el modelo), la cámara se acerca a ese detalle.

Opciones (pestaña Personalizar, con el bloque seleccionado):
- «Subir modelo o imagen»: sube el archivo desde el equipo (máx. 50 MB, solo usuarios que pueden editar el sitio) y rellena «Archivo (modelo o imagen)». También se puede pegar una URL.
  - Formatos: `.glb`, `.gltf` (solo con los datos incrustados; si usa archivos `.bin` o texturas aparte, exportar como `.glb`), `.png`, `.jpg`, `.webp`, `.gif` y `.avif`. Se comprueba el contenido real del archivo, no solo la extensión. SVG no se admite porque puede contener scripts.
  - Con una imagen, «Moto 3D» muestra la foto con la misma animación de entrada (el giro se simula con perspectiva) y el «Visor 360°» la muestra estática: se ocultan el giro, el zoom y restablecer, y se mantiene la pantalla completa. Los puntos destacados solo se pueden ubicar sobre un modelo 3D.
- «Subir fotos 360°» (Visor 360° y cada color): selecciona a la vez todas las fotos tomadas alrededor de la moto (p. ej. 24, una cada 15°). Se ordenan por nombre con orden natural (`moto-2` va antes que `moto-10`), así que conviene numerarlas en el orden del giro. Formatos: `.png`, `.jpg`, `.webp` y `.avif`. Las URL quedan en «Archivo», separadas por espacios.
  - El visitante gira la moto arrastrando (todo el ancho del visor = una vuelta) o con las flechas del teclado. Funcionan el giro automático, el zoom (botones, rueda y pellizco con dos dedos en el celular), restablecer y la pantalla completa. Los marcadores de los puntos destacados no se muestran, porque necesitan un modelo 3D.
  - «Invertir sentido (fotos)»: úsalo si al arrastrar la moto gira al revés.
  - En «Moto 3D», una secuencia muestra solo la primera foto.
- Texto alternativo, Orientación del modelo (0/90/180/270°) para corregir modelos exportados con otro eje frontal.
- Animación de entrada (Moto 3D) y Giro automático (Visor 360°).
- En cada color del Visor 360°: «Subir modelo o imagen de este color». Al elegir ese color el visor carga su archivo (se pueden mezclar colores con modelo y colores con foto). Si el bloque no tiene archivo principal, el primero que se sube también se usa como principal.

Los archivos se guardan como adjuntos públicos (`/web/content/<id>/<nombre>`) mediante la ruta `/website_motos_alfa_showcase/upload_model` (`controllers/main.py`).

## Reutilizar para otras motos
Los bloques no dependen de ningún modelo concreto: cada copia guarda sus propios textos, colores, puntos y archivos.
- Duplicar una página ya armada (Sitio web → Páginas → Duplicar) y cambiar textos y archivos .glb.
- O guardar un bloque configurado como bloque personalizado (botón «Guardar» del bloque) y reutilizarlo desde la categoría «Personalizado».

Mientras no hay modelo, los visitantes no ven el Visor 360° ni el recuadro 3D de «Moto 3D» (el nombre y los botones sí se muestran).
Los ajustes finos de la animación están al inicio de `static/src/snippets/s_moto_3d/000.js`.
El 3D usa `<model-viewer>` 4.0.0 (Google, Apache-2.0) en `static/lib/model-viewer/`, cargado solo en páginas con estos bloques.

## Instalar
```bash
docker exec odoo-one-odoo18-1 sh -c 'odoo -c /etc/odoo/odoo.conf -d Db-demo --db_host=db --db_user=odoo --db_password="$PASSWORD" -i website_motos_alfa_showcase --stop-after-init --no-http'
```
O desde Aplicaciones → Actualizar lista → instalar «Motos Alfa - Ficha de producto Hunk 150 XT».

Tras cambiar SCSS/JS, actualiza con `-u website_motos_alfa_showcase` para regenerar los assets.
Si se agrega o quita un archivo en `assets` del manifiesto, además reinicia el contenedor (`docker restart odoo-one-odoo18-1`): el servidor en marcha conserva el manifiesto que leyó al arrancar y, si falta un módulo JS importado, los bloques no muestran nada.

## Probar
Pruebas automáticas: `-u website_motos_alfa_showcase --test-tags /website_motos_alfa_showcase --http-port 8099` (con el servidor principal ya ocupando el 8069).

1. Inicia sesión como administrador y abre `/hunk-150-xt` (los administradores ven páginas sin publicar).
2. Publica la página desde el sitio (interruptor «Publicado») cuando corresponda.
3. Para enlazarla desde el menú, edita el mega menú «Vehículos → Hunk 150 XT» en el editor del sitio y apunta el enlace a `/hunk-150-xt`.

## Revertir
Desinstala el módulo desde Aplicaciones (elimina la página, la plantilla y los assets) y borra esta carpeta.

## Siguientes etapas
- Modelo 3D: subir el `.glb` como adjunto (o en `static/models/`) y poner su URL en `data-model-src` del contenedor `.o_moto_showcase`; implementar `_mountModel()` (p. ej. con `<model-viewer>` o three.js cargados de forma diferida).
- Animación: implementar `_playIntro()` recorriendo `INTRO_PHASES` (`enter`, `accelerate`, `turnRight`, `brake`, `settle`) y omitirla si `reducedMotion` es verdadero.
- 360°: implementar `_mount360()` en el slot `viewer360`.
- Al montar contenido en un slot, añadir la clase `o_moto_slot_filled` para quitar el estilo de marcador.
