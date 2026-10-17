from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MotoComponentAssignment(models.Model):
    _name = "moto.component.assignment"
    _description = "Historial de componentes instalados en motos"
    _order = "installed_date desc, id desc"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_display_name", store=True)
    motorcycle_lot_id = fields.Many2one(
        "stock.lot", string="Moto", required=True, index=True, ondelete="restrict",
        domain="[('is_motorcycle', '=', True)]",
    )
    component_lot_id = fields.Many2one(
        "stock.lot", string="Componente", required=True, index=True, ondelete="restrict"
    )
    installed_date = fields.Date(
        string="Fecha de instalación", required=True, default=fields.Date.context_today
    )
    removed_date = fields.Date(string="Fecha de retiro")
    active = fields.Boolean(string="Actualmente instalado", default=True, index=True)
    notes = fields.Text(string="Observaciones")
    company_id = fields.Many2one(related="motorcycle_lot_id.company_id", store=True, readonly=True)

    @api.depends("motorcycle_lot_id", "component_lot_id", "installed_date")
    def _compute_display_name(self):
        for record in self:
            moto = record.motorcycle_lot_id.name or "Moto"
            component = record.component_lot_id.name or "Componente"
            date = record.installed_date or "sin fecha"
            record.display_name = "%s — %s (%s)" % (moto, component, date)

    @api.constrains("motorcycle_lot_id", "component_lot_id")
    def _check_different_records(self):
        for record in self:
            if record.motorcycle_lot_id == record.component_lot_id:
                raise ValidationError(_("La moto no puede registrarse como componente de sí misma."))
            if not record.motorcycle_lot_id.is_motorcycle:
                raise ValidationError(_("Marca el registro de la moto como 'Es una moto' antes de asignarle componentes."))

    @api.constrains("active", "removed_date", "installed_date", "component_lot_id")
    def _check_dates_and_unique_active_component(self):
        for record in self:
            if record.removed_date and record.removed_date < record.installed_date:
                raise ValidationError(_("La fecha de retiro no puede ser anterior a la instalación."))
            if record.active and record.removed_date:
                raise ValidationError(_("Un componente actualmente instalado no puede tener fecha de retiro."))
            if record.active:
                duplicate = self.search([
                    ("id", "!=", record.id),
                    ("component_lot_id", "=", record.component_lot_id.id),
                    ("active", "=", True),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_("Este componente ya figura instalado en otra asignación activa."))

    def action_mark_removed(self):
        for record in self:
            record.write({"active": False, "removed_date": fields.Date.context_today(self)})
        return True
