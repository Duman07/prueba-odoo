{
    "name": "Trazabilidad de Motos y Componentes",
    "version": "18.0.1.0.0",
    "summary": "Identificación por BIN y chasis e historial de componentes instalados",
    "category": "Inventory/Inventory",
    "author": "Personalización local",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_lot_views.xml",
        "views/moto_component_assignment_views.xml",
        "views/stock_quant_views.xml",
        
    ],
    "installable": True,
    "application": True,
}
