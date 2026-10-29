{
    "name": "Trazabilidad de Motos y Componentes",
    "version": "18.0.1.1.0",
    "summary": "Identificación por BIN y chasis e historial de componentes instalados",
    "category": "Inventory/Inventory",
    "author": "Personalización local",
    "license": "LGPL-3",
    "depends": ["stock"],
    # Grupos de archivos relacionados (detalle en el README, «Relación entre archivos»):
    #   [Lotes de motos] BIN, chasis, «Es una moto» e historial de componentes en el lote/serie
    #   [Ajustes] Ajustes de Odoo que el módulo activa solo (sin tocar Ajustes a mano)
    "data": [
        # [Ajustes] «Lotes y números de serie» (stock.group_production_lot) para todos los usuarios internos
        "data/stock_lot_group.xml",
        # [Lotes de motos] Permisos del historial de componentes (moto.component.assignment)
        "security/ir.model.access.csv",
        # [Lotes de motos] BIN, chasis, «Es una moto» y pestaña «Componentes e historial» en el lote/serie
        "views/stock_lot_views.xml",
        # [Lotes de motos] Historial de componentes y menú Inventario → Trazabilidad de motos
        "views/moto_component_assignment_views.xml",
        # [Lotes de motos] Columnas BIN y chasis en Inventario → Existencias
        "views/stock_quant_views.xml",
    ],
    "installable": True,
    "application": True,
}
