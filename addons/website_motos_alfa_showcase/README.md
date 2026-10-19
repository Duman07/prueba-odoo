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

## Motos del inventario: páginas y mega menú automáticos
Cada producto de la categoría **MOTOS** (o de sus subcategorías) que se pueda vender tiene su página en `/moto/<nombre>-<id>`.
Cada una usa el **diseño de una página maestra** hecha en el editor del sitio:
- La de su categoría: campo «Página maestra (diseño web)» en Inventario → Configuración → Categorías de producto.
- Si su categoría no tiene, la de la categoría padre más cercana (p. ej. MOTOS / HUNK / SPORT usa la de MOTOS / HUNK).
- Si ninguna tiene, la general `/hunk-160r-4v` (vista `website.hunk-160r-4v`; otra se elige con el parámetro del sistema `website_motos_alfa_showcase.master_page_key`).
Cada página maestra se edita como cualquier otra (mover bloques, tamaños, colores, textos) y conviene dejarla sin publicar.

Al mostrar una moto se colocan sus datos en los bloques del diseño (`controllers/moto_template.py`):
- «Moto 3D»: imagen del producto; el título (`<h1>`) lleva el nombre y el texto de encima, la categoría. Cualquier otro texto igual al título del diseño también pasa a ser el nombre.
- «Visor 360°»: primer adjunto `.glb`/`.gltf` del producto (clip de adjuntos); sin modelo, la foto. Una muestra por variante de color, copiando la primera muestra del diseño. El color es el color HTML del valor del atributo (tipo «Color») o se deduce del nombre (Negro, Rojo, Verde…). Al llegar desde el bloque «Productos» (`#attribute_values=…`) el visor abre en el color elegido.
- Tarjetas de especificaciones (`s_card` dentro de «Elementos»): una por atributo con «Creación de variantes: Nunca» (p. ej. Motor = 160 cc 4V), copiando la primera tarjeta con nombre y valor. Un adjunto de imagen con el nombre del atributo (`Motor.jpg`) es la foto de la tarjeta. Sin especificaciones, la sección no se muestra.
- Campo «Modelo» del formulario: todas las motos, con la actual elegida.
- Enlaces a la página maestra (`/hunk-160r-4v#…`): apuntan a la página de la moto.

Estos bloques se pueden mover, redimensionar y cambiar de estilo, pero si se borran de la página maestra sus datos no se muestran.
Las páginas de cada moto se generan sin las marcas del editor: no se pueden editar (así no se guardan datos de una moto en el diseño)
y los editores ven un aviso con el enlace a la página maestra.

Las motos enlazan a su página en el bloque «Productos», la tienda y la búsqueda; `/shop/<moto>` redirige a `/moto/<moto>`.
Solo se publican la imagen del producto y los adjuntos que son imágenes o modelos 3D; los demás adjuntos (PDF, etc.) no.

El mega menú **Modelos** (`views/moto_mega_menu.xml`) lista las motos, una columna por subcategoría de MOTOS
(p. ej. MOTOS / ECO, MOTOS / HUNK), y se actualiza solo al crear, renombrar, archivar o mover una moto.

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
