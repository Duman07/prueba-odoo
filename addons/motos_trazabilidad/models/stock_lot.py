from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = "stock.lot"

    bin_code = fields.Char(string="BIN", copy=False, index=True)
    chassis_code = fields.Char(string="Código de chasis", copy=False, index=True)
    is_motorcycle = fields.Boolean(
        string="Es una moto", default=False,
        help="Marcar si este lote o número de serie identifica una motocicleta completa.",
    )
    component_assignment_ids = fields.One2many(
        "moto.component.assignment", "motorcycle_lot_id", string="Historial de componentes"
    )

    _sql_constraints = [
        ("bin_code_unique", "unique(bin_code)", "El código BIN debe ser único."),
        ("chassis_code_unique", "unique(chassis_code)", "El código de chasis debe ser único."),
    ]

    @api.constrains("bin_code", "chassis_code")
    def _check_motorcycle_codes(self):
        for lot in self:
            if lot.bin_code and lot.bin_code.strip() != lot.bin_code:
                raise ValidationError(_("El BIN no debe comenzar ni terminar con espacios."))
            if lot.chassis_code and lot.chassis_code.strip() != lot.chassis_code:
                raise ValidationError(_("El código de chasis no debe comenzar ni terminar con espacios."))
