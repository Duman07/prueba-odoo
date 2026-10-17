from odoo import fields,models

class AgendaContacto(models.Model):
    _name = 'agenda.contacto'
    _description = 'Contactod de la agenda'
    _order = 'name asc'

    name = fields.Char(
        string='Nombre completo',
        required= True,
        index=True,
    )

    telefono = fields.Char(
        string='Telefono'
    )
    correo = fields.Char(
        string='Correo Elctronico'
    )
    direccion = fields.Char(
        string = 'Dirección'
    )
    empresa = fields.Char(
        string = 'Empresa'
    )
    notas = fields.Text(
        string = 'Notas'
    )