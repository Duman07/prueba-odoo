"""Actualización desde 18.0.2.1.0 o anterior (no se ejecuta al instalar en una base nueva).

Antes la categoría MOTOS se reconocía por el nombre; ahora por el id interno category_motos
(data/product_category_motos.xml). Para no crear una segunda «MOTOS» en las bases donde el módulo ya estaba
instalado, se le asigna ese id a la categoría raíz «MOTOS» que la versión anterior ya usaba.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "SELECT 1 FROM ir_model_data WHERE module = %s AND name = %s",
        ("website_motos_alfa_showcase", "category_motos"),
    )
    if cr.fetchone():
        return
    cr.execute("SELECT id FROM product_category WHERE parent_id IS NULL AND name ILIKE 'motos' ORDER BY id LIMIT 1")
    row = cr.fetchone()
    if row:
        cr.execute(
            """INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
               VALUES (%s, %s, 'product.category', %s, true)""",
            ("website_motos_alfa_showcase", "category_motos", row[0]),
        )
