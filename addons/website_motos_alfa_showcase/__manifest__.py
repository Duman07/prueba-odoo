{
    "name": "Motos Alfa - Ficha de producto Hunk 150 XT",
    "version": "18.0.2.1.0",
    "summary": "Estructura base de la página de la Hero Hunk 150 XT, preparada para modelo 3D, animación de entrada y vista 360°",
    "category": "Website/Website",
    "author": "Personalización local",
    "license": "LGPL-3",
    # [Inventario de motos] Todo lo que usa una moto se instala con este módulo: tienda y variantes (website_sale),
    # CRM y su formulario (website_crm), inventario (stock) y BIN/chasis del lote (motos_trazabilidad)
    "depends": ["website", "website_sale", "website_crm", "stock", "motos_trazabilidad"],
    # Grupos de archivos relacionados (detalle en el README, «Relación entre archivos»):
    #   [Bloques] Bloques «Moto 3D» y «Visor 360°»
    #   [Páginas de motos] Páginas de cada moto (/moto/...) y mega menú «Modelos»
    #   [Formulario] Formulario: departamentos de Colombia, casilla de autorización de datos y botón ENVIAR
    #   [Tipos de moto] Bloque «Tipos de moto» en /motos y páginas /motos/<tipo>
    #   [whatsApp] Botón flotante de WhatsApp
    #   [Inventario de motos] Ajustes y registros que una moto necesita en una base nueva (sin configurar nada a mano)
    "data": [
        # [Inventario de motos] «Variantes» para todos los usuarios internos: colores, «Atributos», «Fotos 360°» por color
        "data/product_variant_group.xml",
        # [Inventario de motos] Categoría raíz MOTOS (solo al instalar y si no existe)
        "data/product_category_motos.xml",
        # [Formulario] País, Departamento y Ciudad del formulario de cotización van a sus campos de la oportunidad
        "data/crm_lead_form_whitelist.xml",
        # [Páginas de motos] «Plantilla de motos»: diseño de todas las páginas /moto/<moto> (controllers/motos.py);
        # («Especificaciones técnicas» es un acordeón .s_moto_specs que llena _fill_specs)
        # («Otras motos de tipo <tipo>» y «Volver a <tipo>» es la sección .s_moto_related que llena _fill_related;
        # «Galería» es .s_moto_gallery, bloque s_image_gallery de Odoo, que llena _fill_gallery;
        # «Datos clave» es .s_moto_keyspecs, bloque «Números» de Odoo, que llena _fill_key_specs con KEY_SPECS)
        "views/moto_template.xml",
        # [Tipos de moto] Página «Motocicletas» (/motos) con el carrusel (solo en /motos), el bloque «Tipos de moto» y su menú;
        # /motos/<tipo> usa su diseño (sin el carrusel: moto_type, controllers/motos.py)
        "views/motos_page.xml",
        # [Páginas de motos] Mega menú «Modelos» (el menú y su contenido)
        "views/moto_mega_menu.xml",
        # [Páginas de motos] Campo «Fotos 360°» en la variante (color) y en la moto (models/product.py)
        "views/product_moto_360_views.xml",
        # [Bloques] Plantillas de los bloques, grupo «Motos Alfa» y sus opciones
        # [Tipos de moto] Plantillas s_moto_types (bloque) y s_moto_types_content (tarjetas, controllers/motos.py)
        "views/snippets/s_moto_snippets.xml",
        # [whatsApp] boton flotante 
        "views/whatsapp_button.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            # [Bloques] Estilos, carga de <model-viewer>, secuencia de fotos y widget de cada bloque
            # [Páginas de motos] s_moto_snippets.scss también da estilo al precio y a su tarjeta
            # (clases s_moto_price / s_moto_price_label que pone _fill_price en controllers/moto_template.py)
            # [Formulario] ... y a la casilla de autorización (_fill_form) y al botón ENVIAR
            # [Bloques] frame_sequence.js: giro con fotos y puntos destacados ubicados en una foto
            # (puntos destacados ocultos por ahora con una regla de s_moto_snippets.scss, 27-10-2026)
            # [Páginas de motos] ... y hace que las filas del «Visor 360°» tomen el alto de su contenido (28-10-2026)
            # [Páginas de motos] ... y el acordeón «Especificaciones técnicas» (.s_moto_specs, variables $moto-specs-*, «+» / «−»)
            # [Páginas de motos] + [Tipos de moto] ... y el estilo de la página para lo que agrega el código: $moto-brand-red,
            # títulos .s_moto_heading en negrilla, enlaces .s_moto_back en rojo («Volver a <tipo>», «Todos los tipos»)
            # y botones .s_moto_btn en rojo (carrusel de /motos)
            # [Páginas de motos] ... y las fotos de la «Galería» del mismo tamaño (.s_moto_gallery, $moto-gallery-ratio)
            # y los «Datos clave» con el valor en rojo (.s_moto_keyspecs, $moto-keyspecs-*)
            "website_motos_alfa_showcase/static/src/snippets/s_moto_snippets.scss",
            "website_motos_alfa_showcase/static/src/js/model_viewer_loader.js",
            "website_motos_alfa_showcase/static/src/js/frame_sequence.js",
            # [Bloques] + [Páginas de motos]: en /moto/<moto>, s_moto_360/000.js avisa el color elegido
            # (data-main-src, de controllers/moto_template.py) y s_moto_3d/000.js gira con sus fotos 360°
            "website_motos_alfa_showcase/static/src/snippets/s_moto_3d/000.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_360/000.js",
            # [Tipos de moto] Pide las tarjetas del bloque a controllers/motos.py
            "website_motos_alfa_showcase/static/src/snippets/s_moto_types/000.js",
            # [Formulario] Departamentos de Colombia en los formularios del sitio
            "website_motos_alfa_showcase/static/src/js/colombia_form_states.js",
            # [whatsApp] boton flotante
            "website_motos_alfa_showcase/static/src/scss/whatsapp.scss",
        ],
        "website.assets_wysiwyg": [
            # [Bloques] Opciones de los bloques en el editor (subir archivo, ubicar puntos destacados en una foto 360°
            # o en el modelo 3D; options.js le pide el clic al widget s_moto_360/000.js con eventos propios)
            "website_motos_alfa_showcase/static/src/js/editor/model_upload_option.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_360/options.js",
        ],
    },
    "installable": True,
    "application": False,
}
