"""Actualización desde 18.0.2.1.0 o anterior (no se ejecuta al instalar en una base nueva).

Antes el mega menú de motos se reconocía por el nombre «Modelos»; ahora por el campo moto_catalog
(models/website_menu.py). Se marcan los mismos menús que la versión anterior ya trataba como catálogo, incluidas
las copias de cada sitio web, para que el sitio siga igual después de actualizar.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """UPDATE website_menu m
              SET moto_catalog = true
            WHERE m.mega_menu_content IS NOT NULL
              AND EXISTS (
                  SELECT 1 FROM jsonb_each_text(m.name) AS v
                  WHERE lower(trim(v.value)) = 'modelos'
              )"""
    )
