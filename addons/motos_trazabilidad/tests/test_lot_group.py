from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLotGroup(TransactionCase):
    """[Ajustes] y [Lotes de motos]: lo que el módulo deja listo en una base nueva."""

    def test_lots_for_internal_users(self):
        """data/stock_lot_group.xml: «Lotes y números de serie» para todos, también para los usuarios nuevos."""
        group_user = self.env.ref("base.group_user")
        self.assertIn(self.env.ref("stock.group_production_lot"), group_user.implied_ids)
        self.assertTrue(self.env.ref("base.user_admin").has_group("stock.group_production_lot"))
        user = self.env["res.users"].create({"name": "Bodega Motos", "login": "bodega_motos_prueba"})
        self.assertTrue(user.has_group("stock.group_production_lot"))

    def test_moto_lot_fields(self):
        """Un número de serie de moto guarda BIN y chasis, y las existencias los muestran."""
        product = self.env["product.product"].create({
            "name": "Moto Prueba Serie", "is_storable": True, "tracking": "serial",
        })
        lot = self.env["stock.lot"].create({
            "name": "SERIE-0001", "product_id": product.id, "is_motorcycle": True,
            "bin_code": "BIN-0001", "chassis_code": "CHASIS-0001",
        })
        location = self.env.ref("stock.stock_location_stock")
        self.env["stock.quant"]._update_available_quantity(product, location, 1, lot_id=lot)
        quant = self.env["stock.quant"].search([("lot_id", "=", lot.id), ("location_id", "=", location.id)])
        self.assertEqual(quant.bin_code, "BIN-0001")
        self.assertEqual(quant.chassis_code, "CHASIS-0001")
