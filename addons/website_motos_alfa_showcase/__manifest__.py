{
    "name": "Motos Alfa - Ficha de producto Hunk 150 XT",
    "version": "18.0.2.0.0",
    "summary": "Estructura base de la página de la Hero Hunk 150 XT, preparada para modelo 3D, animación de entrada y vista 360°",
    "category": "Website/Website",
    "author": "Personalización local",
    "license": "LGPL-3",
    "depends": ["website", "website_sale"],
    # Grupos de archivos relacionados (detalle en el README, «Relación entre archivos»):
    #   [Bloques] Bloques «Moto 3D» y «Visor 360°»
    #   [Páginas de motos] Páginas de cada moto (/moto/...) y mega menú «Modelos»
    #   [Formulario] Formulario: departamentos de Colombia, casilla de autorización de datos y botón ENVIAR
    #   [Tipos de moto] Bloque «Tipos de moto» en /motos y páginas /motos/<tipo>
    #   [whatsApp] Botón flotante de WhatsApp
    "data": [
        # [Páginas de motos] «Plantilla de motos»: diseño de todas las páginas /moto/<moto> (controllers/motos.py);
        # sus imágenes están en static/src/img/plantilla/
        "views/moto_template.xml",
        # [Tipos de moto] Página «Motocicletas» (/motos) con el bloque «Tipos de moto»; /motos/<tipo> usa su diseño
        "views/motos_page.xml",
        # [Páginas de motos] Mega menú «Modelos»
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
