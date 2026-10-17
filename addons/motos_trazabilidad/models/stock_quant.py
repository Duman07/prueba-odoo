from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    bin_code = fields.Char(
        string="BIN",
        related="lot_id.bin_code",
        readonly=True,
    )

    chassis_code = fields.Char(
        string="Chasis",
        related="lot_id.chassis_code",
        readonly=True,
    )
