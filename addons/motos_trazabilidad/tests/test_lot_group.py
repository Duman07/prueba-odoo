from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLotGroup(TransactionCase):
    """[Lotes de motos]: BIN y chasis en el número de serie y en las existencias."""

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
