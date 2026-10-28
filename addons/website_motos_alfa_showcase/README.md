# Motos Alfa — Páginas de motos y bloques 3D / 360° (Odoo 18)

Integrado en el sitio existente mediante `website.layout` (usa el encabezado, el menú y el pie de página del sitio).

## Relación entre archivos
Los archivos del manifiesto llevan la etiqueta de su grupo (`[Bloques]`, `[Páginas de motos]`, `[Formulario]`, `[Tipos de moto]`, `[whatsApp]`).

**[Bloques] «Moto 3D» y «Visor 360°»**
- `views/snippets/s_moto_snippets.xml`: plantillas `s_moto_3d` y `s_moto_360`, grupo «Motos Alfa» del panel (miniaturas en `static/src/img/snippets_thumbs/`) y opciones del panel Personalizar.
- `static/src/snippets/s_moto_snippets.scss`: estilos de ambos bloques.
- `static/src/snippets/s_moto_3d/000.js` y `static/src/snippets/s_moto_360/000.js`: widgets de los bloques; importan
  `static/src/js/model_viewer_loader.js` (carga `static/lib/model-viewer/model-viewer.min.js`) y `static/src/js/frame_sequence.js`.
- `static/src/js/editor/model_upload_option.js`: subir archivos desde el editor → `controllers/main.py` (`/website_motos_alfa_showcase/upload_model`).
- `static/src/snippets/s_moto_360/options.js`: ubicar los puntos destacados en una foto 360° («Foto n.º» + «Ubicar») o sobre
  el modelo 3D. Para las fotos le pide el clic al widget (`s_moto_360/000.js`) con los eventos `moto-show-frame` y
  `moto-pick-photo`; el widget usa `pickPoint()`/`pointToView()` de `static/src/js/frame_sequence.js` y dibuja el círculo
  con la burbuja del texto (estilos en `s_moto_snippets.scss`).
- **Puntos destacados ocultos por ahora (27-10-2026)**, se dejan para más adelante: una regla de
  `s_moto_snippets.scss` esconde el panel y los marcadores, y el panel está comentado en `s_moto_snippets.xml`
  (el bloque nuevo ya no lo trae). Las plantillas guardadas conservan sus puntos. Para volver a mostrarlos: borrar esa
  regla y descomentar el panel. Pendiente: guardarlos por moto (en el producto) y no en la plantilla.
- En `s_moto_360` cada panel («Colores», «Puntos destacados») va en su propia columna: en cuadrícula se mueven por separado.
  Los puntos destacados deben quedar dentro de la sección «Visor 360°» (`s_moto_360/000.js` solo los busca ahí);
  el panel «Colores» también puede ir en «Moto 3D» (lo atiende `s_moto_3d/000.js`).
- Pruebas: `tests/test_model_upload.py`.

**[Páginas de motos] `/moto/<moto>` y mega menú «Modelos»**
- `views/moto_template.xml` (28-10-2026): la **«Plantilla de motos»**, diseño de todas las `/moto/<moto>` (sale de
  `/plantilla-hunk`); «Especificaciones técnicas» es un acordeón (`s_moto_specs`). El diseño se cambia ahí, no en el editor.
- `controllers/motos.py`: rutas `/moto/<moto>`, `/moto/media/...` y redirección de `/shop/<moto>`; dibuja
  `MOTO_TEMPLATE` (la plantilla de arriba) y usa `controllers/moto_template.py` (la rellena; depende de las clases
  de los bloques `s_moto_3d`/`s_moto_360`) y `models/product.py`.
- `models/product.py`: `_moto_url()` del producto y sus datos (colores, especificaciones, «Medios adicionales» y
  descripción).
- `views/product_moto_360_views.xml`: campos «Fotos 360°» (variante y moto) y «Color principal» (moto), de `models/product.py`.
  Las fotos se sirven con `/moto/media/<moto>/giro/<id>/…` y los «Medios adicionales» con `/moto/media/<moto>/medio/<id>/…`
  (`controllers/motos.py`).
- Cambio de color: `controllers/moto_template.py` pone en cada muestra `data-main-src` (fotos 360° o foto del color);
  `static/src/snippets/s_moto_360/000.js` lo envía con el evento `moto-color-change` y `static/src/snippets/s_moto_3d/000.js`
  cambia la foto de la imagen principal. Si el panel «Colores» está dentro de «Moto 3D», lo atiende
  `s_moto_3d/000.js` directamente. Ambos usan `linkedSwatchIndex()` de `static/src/js/model_viewer_loader.js`
  (color del enlace de la tienda).
- Precio: `controllers/motos.py` pasa `list_price` y `_fill_price` (`controllers/moto_template.py`) cambia el «$0.» de
  «Moto 3D» por el precio y pone las clases `s_moto_price` / `s_moto_price_label`; su estilo y el de la tarjeta están en
  `static/src/snippets/s_moto_snippets.scss`. Debajo va la nota legal `PRICE_NOTE` (clase `s_moto_price_note`, 27-10-2026).
- Sin giro, sin sección 360° (28-10-2026): `values["has_360"]` (`controllers/motos.py`) y `_drop_360`
  (`controllers/moto_template.py`) quitan «Explórala en 360°» y el botón «Ver en 360°» si la moto no tiene `.glb` ni
  fotos 360°.
- Un solo `<h1>` (27-10-2026): `_single_h1` (`controllers/moto_template.py`) pasa a `<h2 class="h1">` los `<h1>` del
  diseño fuera de «Moto 3D»; el `<h1>` es el nombre de la moto.
- Sitemap (27-10-2026): `sitemap_motos` (`controllers/motos.py`) pone las `/moto/…` publicadas en `/sitemap.xml` y
  `models/website.py` (`_enumerate_pages`) quita sus `/shop/…`, que redirigen.
- SEO y vista previa al compartir (27-10-2026): `controllers/motos.py` pasa la moto como `main_object` y
  `_default_website_meta` (`models/product.py`) usa su «Descripción para comercio electrónico» como meta descripción;
  la imagen al compartir (`og:image`) es la foto del producto.
- Motos sin publicar (27-10-2026): `_moto_domain` (`models/product.py`) pide `is_published`, así que no salen en el mega
  menú, «Tipos de moto» ni el formulario; `_get_moto` (`controllers/motos.py`) da 404 a su página y fotos, salvo a los
  editores del sitio. `MENU_FIELDS` incluye `is_published`/`website_published` para refrescar el menú al publicar.
- `views/moto_mega_menu.xml` + `models/website_menu.py`: el menú «Modelos» del encabezado (28-10-2026, antes se
  creaba a mano) y su mega menú con las motos por subcategoría.
- Pruebas: `tests/test_moto_pages.py` (reutiliza `FAKE_GLB` de `tests/test_model_upload.py`; `test_moto_template_from_module` dibuja la plantilla real).

**[Tipos de moto] Bloque «Tipos de moto» en `/motos` y páginas `/motos/<tipo>`**
- `views/snippets/s_moto_snippets.xml`: plantillas `s_moto_types` (el bloque, solo con su aviso) y `s_moto_types_content` (las tarjetas).
- `static/src/snippets/s_moto_types/000.js`: pide las tarjetas a `controllers/motos.py` (`/website_motos_alfa_showcase/moto_types[/<tipo>]`) y las pone en el bloque.
- `views/motos_page.xml` (28-10-2026): la página «Motocicletas» (`/motos`) con su diseño (título y el bloque) y el menú
  «Motocicletas» del encabezado (Odoo lo copia en cada sitio al instalar).
- `controllers/motos.py`: `moto_types_content` (tarjetas) y `moto_type_page` (`/motos/<tipo>`, muestra la página
  `MOTOS_PAGE`).
- `models/product.py`: `_moto_types`, `_moto_is_type`, `_moto_type_motos` y `_moto_type_url` de la categoría.
- `static/src/snippets/s_moto_snippets.scss`: recuadro del aviso (oculto para los visitantes).
- Pruebas: `tests/test_moto_types.py` (reutiliza `PIXEL_PNG` de `tests/test_moto_pages.py`).

**[Formulario] Departamentos de Colombia, casilla de autorización y botón ENVIAR**
- `static/src/js/colombia_form_states.js` (formularios `.s_website_form`) → `controllers/colombia.py` (`/website_motos_alfa_showcase/colombia_states`).
- Casilla de autorización de datos: `controllers/moto_template.py` (`CONSENT_FIELD`, `_fill_form`) la pone antes de ENVIAR en
  `/moto/<moto>`; su estilo y el del botón ENVIAR están en `static/src/snippets/s_moto_snippets.scss`.
- Pruebas: `tests/test_colombia_states.py` y `test_consent_before_submit` en `tests/test_moto_pages.py`.
**[whatsApp] Botón flotante**
- `views/whatsapp_button.xml`: el botón en las páginas del sitio; `static/src/scss/whatsapp.scss`: su estilo (computador y celular).
  En celular, `#wrapwrap` deja 4.5rem abajo para que el botón no tape el pie (28-10-2026, D7), menos en el editor.

## Tipos de moto: página Motocicletas
Las subcategorías **directas** de MOTOS son los **tipos** (Trabajadora, Urbana, Doble propósito, Scooter) y dentro de
cada tipo van las líneas (ECO, Hunk, XPULSE, XOOM) con sus motos: `MOTOS / Urbana / Hunk`.
- Bloque «Tipos de moto» (grupo «Motos Alfa»): está en la página `/motos` (`views/motos_page.xml`). Ahí muestra una tarjeta por
  tipo que tenga motos (foto de su primera moto con foto), en el orden en que se crearon los tipos.
- Al hacer clic se abre `/motos/<tipo>` (p. ej. `/motos/urbana-95`): la misma página `/motos` (mismo diseño), con el
  nombre del tipo, «Todos los tipos» y una tarjeta por moto que lleva a su página `/moto/...`.
- Las tarjetas no se guardan en la página: se arman al abrirla, así un tipo o una moto nueva aparece sola.
- Si `/motos` no está publicada, `/motos/<tipo>` tampoco se ve (salvo para los editores). El diseño se cambia en `views/motos_page.xml`.

## Motos del inventario: páginas y mega menú automáticos
Cada producto de la categoría **MOTOS** (o de sus subcategorías) que se pueda vender tiene su página en `/moto/<nombre>-<id>`.
Todas usan el **mismo diseño**: la «Plantilla de motos» (`views/moto_template.xml`, 28-10-2026). Antes cada categoría
elegía una página maestra hecha en el editor; eso se quitó para que el diseño viaje con el código. El diseño se cambia
en ese XML y se actualiza el módulo (`-u`).

Al mostrar una moto se colocan sus datos en los bloques del diseño (`controllers/moto_template.py`):
- «Moto 3D»: foto fija del primer color (la foto de su variante) o, sin ella, su primera foto 360° (de frente) o la del producto; el título (`<h1>`) lleva el nombre y el texto de encima, la categoría. Cualquier otro texto igual al título del diseño también pasa a ser el nombre.
- «Visor 360°»: primer adjunto `.glb`/`.gltf` del producto (clip de adjuntos); sin modelo, las fotos 360° del primer color (giro con arrastre) o su foto. Una muestra por variante de color, copiando la primera muestra del diseño. El color es el color HTML del valor del atributo (tipo «Color») o se deduce del nombre (Negro, Rojo, Verde…).
- Color principal: Producto → pestaña Ventas → «Página de la moto» → «Color principal». Es la primera muestra y el color con el que abre la página (imagen principal, visor, fondo y video). Vacío: el primero de Odoo (por referencia interna).
- El panel «Colores» se puede dejar en el «Visor 360°» o moverlo dentro del bloque «Moto 3D» (junto a la imagen principal).
- Elegir un color solo cambia la **imagen principal** («Moto 3D»): muestra su foto (la foto de la variante o, sin ella, la primera foto 360°, de frente), sin animación. El visor, el fondo y el video no cambian. Al llegar desde el bloque «Productos» (`#attribute_values=…`) la imagen principal muestra el color elegido.
- Fotos 360°: Producto → Variantes → la variante (color) → «Fotos 360°»: se seleccionan todas a la vez (p. ej. 24, una cada 15°) y se ordenan por nombre con orden natural (`moto-2` antes que `moto-10`); la primera es la vista de frente. Para motos sin colores o colores sin fotos propias, el mismo campo en la ficha de la moto (pestaña Ventas).
- «Especificaciones técnicas» (acordeón `s_moto_specs`, 28-10-2026): un grupo por atributo **de esa moto** con «Creación de variantes: Nunca» (p. ej. Motor), copiando el primer grupo del diseño; solo el primero abierto. Cada valor del atributo es una fila: «Cilindraje: 160 cc» → etiqueta y valor; sin «:», el texto completo. Sin especificaciones, la sección no se muestra. Estilo (línea bajo cada grupo, «+» cerrado / «−» abierto, colores, tamaños): variables `$moto-specs-*` de `static/src/snippets/s_moto_snippets.scss`.
- Fondos y videos: cada sección con imagen de fondo (p. ej. «Título de la imagen») y cada video del diseño
  se cambian, en orden, por las fotos y los videos de **Medios adicionales** del primer color (Producto → Variantes → la variante).
  Si ese color no tiene, se usan los del producto (pestaña Ventas → «Medios adicionales para el producto») y, si tampoco,
  los del diseño. No cambian al elegir otro color. El orden se cambia arrastrando los medios.
- Frase: el título de la primera sección con imagen de fondo es la «Descripción para comercio electrónico» del producto
  (solo el texto). Sin descripción se deja la frase del diseño.
- Campo «Modelo» del formulario: todas las motos, con la actual elegida.
- Sin modelo ni fotos 360°: no se muestran la sección «Explórala en 360°» ni el botón «Ver en 360°».

Estos bloques se pueden mover y cambiar de estilo en la plantilla, pero si se quitan de ella sus datos no se muestran.
Las páginas de cada moto se generan sin las marcas del editor: no se pueden editar (así no se guardan datos de una moto en el diseño)
y los editores ven un aviso que dice que el diseño está en `views/moto_template.xml`.

Las motos enlazan a su página en el bloque «Productos», la tienda y la búsqueda; `/shop/<moto>` redirige a `/moto/<moto>`.
Solo se publican la imagen del producto y los adjuntos que son imágenes o modelos 3D; los demás adjuntos (PDF, etc.) no.

El mega menú **Modelos** (`views/moto_mega_menu.xml`) lista las motos, una columna por subcategoría de MOTOS
(p. ej. MOTOS / ECO, MOTOS / HUNK), y se actualiza solo al crear, renombrar, archivar o mover una moto.

## Bloques del editor (grupo «Motos Alfa»)
En el editor del sitio: Editar → panel Bloques → categoría «Motos Alfa».

- «Moto 3D» (`s_moto_3d`): muestra un modelo GLB/glTF con animación de entrada (entrada, aceleración, giro a la derecha, frenada; 2,6 s). Se reproduce una vez al hacerse visible y tiene botón «Repetir animación». Con una foto (o fotos 360°, de las que usa la primera) muestra la foto fija, sin animación. Se omite si el visitante pidió reducir el movimiento o si la opción «Animación de entrada» está apagada.
- «Visor 360°» (`s_moto_360`): rotación con arrastre, zoom, giro automático, restablecer vista y pantalla completa, con un panel lateral de Colores y Puntos destacados.
  - Colores: cada círculo se mueve, duplica o borra desde el editor. Opciones: color, nombre, un `.glb` propio para ese color o una variante de material del modelo.
  - Puntos destacados: el texto se edita directamente; cada punto se mueve, duplica o borra. Con la opción «Ubicación en el modelo → Ubicar» y un clic sobre la moto queda fijado su marcador numerado. En el editor, un número con borde punteado indica que el punto aún no está ubicado. Al pulsar un punto (en la lista o en el modelo), la cámara se acerca a ese detalle.

Opciones (pestaña Personalizar, con el bloque seleccionado):
- «Subir modelo o imagen»: sube el archivo desde el equipo (máx. 50 MB, solo usuarios que pueden editar el sitio) y rellena «Archivo (modelo o imagen)». También se puede pegar una URL.
  - Formatos: `.glb`, `.gltf` (solo con los datos incrustados; si usa archivos `.bin` o texturas aparte, exportar como `.glb`), `.png`, `.jpg`, `.webp`, `.gif` y `.avif`. Se comprueba el contenido real del archivo, no solo la extensión. SVG no se admite porque puede contener scripts.
  - Con una imagen, «Moto 3D» muestra la foto fija y el «Visor 360°» la muestra estática: se ocultan el giro, el zoom y restablecer, y se mantiene la pantalla completa. Los puntos destacados solo se pueden ubicar sobre un modelo 3D.
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

## Revertir
Desinstala el módulo desde Aplicaciones (elimina los bloques, las vistas y los assets) y borra esta carpeta.
