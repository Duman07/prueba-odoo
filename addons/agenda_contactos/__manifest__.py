{
    'name':'Agenda de Contactos',
    'version': '18.0.1.0.0',
    'summary': 'Registro de contactos',
    'description': 'Permite registrar contactos',
    'category': 'Productividad',
    'author': 'Duman',
    'lecense': 'LGPL-3',
    'depends': ['base'],
    'data':[
        'security/ir.model.access.csv',
        'views/contacto_views.xml',
    ],
    'application': True,
    'installable': True,
}