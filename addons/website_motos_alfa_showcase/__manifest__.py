{
    "name": "Motos Alfa - Ficha de producto Hunk 150 XT",
    "version": "18.0.1.7.0",
    "summary": "Estructura base de la página de la Hero Hunk 150 XT, preparada para modelo 3D, animación de entrada y vista 360°",
    "category": "Website/Website",
    "author": "Personalización local",
    "license": "LGPL-3",
    "depends": ["website", "website_sale"],
    # Grupos de archivos relacionados (detalle en el README, «Relación entre archivos»):
    #   [Bloques] Bloques «Moto 3D» y «Visor 360°»
    #   [Páginas de motos] Páginas de cada moto (/moto/...) y mega menú «Modelos»
    #   [Formulario] Formulario: departamentos de Colombia
    "data": [
        # [Páginas de motos] Campo «Página maestra» de la categoría y mega menú «Modelos»
        "views/product_category_views.xml",
        "views/moto_mega_menu.xml",
        # [Páginas de motos] Campo «Fotos 360°» en la variante (color) y en la moto (models/product.py)
        "views/product_moto_360_views.xml",
        # [Bloques] Plantillas de los bloques, grupo «Motos Alfa» y sus opciones
        "views/snippets/s_moto_snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            # [Bloques] Estilos, carga de <model-viewer>, secuencia de fotos y widget de cada bloque
            "website_motos_alfa_showcase/static/src/snippets/s_moto_snippets.scss",
            "website_motos_alfa_showcase/static/src/js/model_viewer_loader.js",
            "website_motos_alfa_showcase/static/src/js/frame_sequence.js",
            # [Bloques] + [Páginas de motos]: en /moto/<moto>, s_moto_360/000.js avisa el color elegido
            # (data-main-src, de controllers/moto_template.py) y s_moto_3d/000.js gira con sus fotos 360°
            "website_motos_alfa_showcase/static/src/snippets/s_moto_3d/000.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_360/000.js",
            # [Formulario] Departamentos de Colombia en los formularios del sitio
            "website_motos_alfa_showcase/static/src/js/colombia_form_states.js",
        ],
        "website.assets_wysiwyg": [
            # [Bloques] Opciones de los bloques en el editor (subir archivo, ubicar puntos destacados)
            "website_motos_alfa_showcase/static/src/js/editor/model_upload_option.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_360/options.js",
        ],
    },
    "installable": True,
    "application": False,
}
