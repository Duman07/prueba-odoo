{
    "name": "Motos Alfa - Ficha de producto Hunk 150 XT",
    "version": "18.0.1.2.0",
    "summary": "Estructura base de la página de la Hero Hunk 150 XT, preparada para modelo 3D, animación de entrada y vista 360°",
    "category": "Website/Website",
    "author": "Personalización local",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "views/hunk_150_xt_page.xml",
        "views/snippets/s_moto_snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_motos_alfa_showcase/static/src/scss/moto_showcase.scss",
            "website_motos_alfa_showcase/static/src/js/moto_showcase.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_snippets.scss",
            "website_motos_alfa_showcase/static/src/js/model_viewer_loader.js",
            "website_motos_alfa_showcase/static/src/js/frame_sequence.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_3d/000.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_360/000.js",
        ],
        "website.assets_wysiwyg": [
            "website_motos_alfa_showcase/static/src/js/editor/model_upload_option.js",
            "website_motos_alfa_showcase/static/src/snippets/s_moto_360/options.js",
        ],
    },
    "installable": True,
    "application": False,
}
