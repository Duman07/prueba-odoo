from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.website_motos_alfa_showcase.models import product


@tagged("post_install", "-at_install")
class TestMenuCache(TransactionCase):
    """La caché de plantillas (encabezado con el mega menú) solo se limpia cuando cambia algo de las motos,
    no con cualquier producto o categoría (p. ej. al importar muchos productos de otras categorías)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env["product.category"]
        root = Category._moto_root() or Category.create({"name": "MOTOS"})
        cls.moto_line = Category.create({"name": "Línea Caché", "parent_id": root.id})
        cls.other = Category.create({"name": "Repuestos Caché"})

    def _clears(self):
        return patch.object(product, "_clear_menu_cache")

    def test_other_products_do_not_clear(self):
        with self._clears() as clear:
            item = self.env["product.template"].create({"name": "Casco", "categ_id": self.other.id})
            item.write({"name": "Casco 2"})
            item.unlink()
            self.other.write({"name": "Repuestos Caché 2"})
        clear.assert_not_called()

    def test_moto_changes_clear(self):
        with self._clears() as clear:
            moto = self.env["product.template"].create({"name": "Moto Caché", "categ_id": self.moto_line.id})
        clear.assert_called()
        with self._clears() as clear:
            moto.write({"name": "Moto Caché 2"})
        clear.assert_called()
        with self._clears() as clear:
            moto.unlink()
        clear.assert_called()
        with self._clears() as clear:
            self.moto_line.write({"name": "Línea Caché 2"})
        clear.assert_called()

    def test_leaving_motos_clears(self):
        moto = self.env["product.template"].create({"name": "Moto Sale", "categ_id": self.moto_line.id})
        with self._clears() as clear:
            moto.write({"categ_id": self.other.id})
        clear.assert_called()

    def test_unwatched_field_does_not_clear(self):
        moto = self.env["product.template"].create({"name": "Moto Precio", "categ_id": self.moto_line.id})
        with self._clears() as clear:
            moto.write({"list_price": 1000})
        clear.assert_not_called()
