# Trazabilidad de Motos y Componentes — Odoo 18

## Qué incluye
- Extiende `stock.lot` con `bin_code`, `chassis_code` e `is_motorcycle`.
- Añade el modelo `moto.component.assignment` para registrar instalación y retiro de componentes identificados por lote/serie.
- Agrega campos al formulario de lote/serie y un menú en Inventario.
- No cambia Ajustes (04-11-2026): «Lotes y números de serie» se activa a mano en Ajustes → Inventario → Trazabilidad
  (sin él no se ven los números de serie ni, por lo tanto, BIN y chasis).

## Relación entre archivos
Los archivos del manifiesto llevan la etiqueta de su grupo (`[Lotes de motos]`).

**[Lotes de motos] BIN, chasis, «Es una moto» e historial de componentes**
- `models/stock_lot.py`: campos `bin_code`, `chassis_code`, `is_motorcycle`, `component_assignment_ids` (únicos y sin espacios).
- `models/moto_component_assignment.py` + `security/ir.model.access.csv` + `views/moto_component_assignment_views.xml`:
  historial de componentes y menú Inventario → Trazabilidad de motos → Componentes instalados.
- `views/stock_lot_views.xml`: los campos y la pestaña «Componentes e historial» (solo si «Es una moto») en el lote/serie.
- `models/stock_quant.py` + `views/stock_quant_views.xml`: columnas BIN y chasis en Inventario → Existencias.
- Pruebas: `tests/test_lot_group.py` → `test_moto_lot_fields`.

## Instalación
Se instala sola con `website_motos_alfa_showcase` (está en sus `depends`). Para instalarla sin la página de motos:
`-i motos_trazabilidad`. La carpeta debe estar en la ruta de módulos (`addons/`, montada en `/mnt/extra-addons`).

## Probar
`-u motos_trazabilidad --test-tags /motos_trazabilidad --http-port 8099 --stop-after-init`.

## Limitaciones de esta primera versión
El módulo registra la trazabilidad funcional, pero no crea automáticamente movimientos de stock al instalar o retirar un componente. Debe probarse primero en una base de datos de desarrollo y verificarse contra las vistas y reglas de seguridad de la instalación exacta de Odoo 18.
