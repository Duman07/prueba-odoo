from odoo import fields, models

class ActividadPendiente(models.Model):
    _name = "actividades.pendientes"
    _description = "Actividades Pendientes"
    _order = 'id desc'

    name = fields.Char(
        string = "Nombre",
        required = True,
    )

    description = fields.Char(
        string = "Descripcion del pendiente",
        required = True,
    )

    done = fields.Boolean(
        string = "Hecho",
        default = "false",
    )

    date_time = fields.Datetime(
        string = "Fecha final",
        required = True,
    )

    contacto_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contacto',
        help='Selecciona un contacto de la agenda',
    )

    def action_toggle_hecho(self):
        for record in self:
            record.hecho = not record.hecho