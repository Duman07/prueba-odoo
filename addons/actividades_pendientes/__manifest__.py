{
'name': 'Actividades Pendientes',
'version': '18.0.1.0.0',
'summary': 'Gestión de actividades y tareas pendientes',
'description': 'Módulo para organizar actividades y marcarlas como hechas.',
'category': 'Productivity',
'author': 'Dgital2',
'license': 'LGPL-3',
'depends': ['base','agenda_contactos'],
'data': [
'security/ir.model.access.csv',
'views/actividad_views.xml',
],
'application': True,
'installable': True,
}