# Trazabilidad de Motos y Componentes — Odoo 18

## Qué incluye
- Extiende `stock.lot` con `bin_code`, `chassis_code` e `is_motorcycle`.
- Añade el modelo `moto.component.assignment` para registrar instalación y retiro de componentes identificados por lote/serie.
- Agrega campos al formulario de lote/serie y un menú en Inventario.

## Instalación en este entorno Docker Compose
1. Copia la carpeta `motos_trazabilidad` a `~/compose-demo/odoo-one/addons/`.
2. Verifica que el volumen de addons del compose la monte dentro del contenedor en `/mnt/extra-addons`.
3. Reinicia Odoo: `docker compose restart odoo18`.
4. En Odoo, activa modo desarrollador y actualiza la lista de aplicaciones.
5. Busca e instala “Trazabilidad de Motos y Componentes”.

## Limitaciones de esta primera versión
El módulo registra la trazabilidad funcional, pero no crea automáticamente movimientos de stock al instalar o retirar un componente. Debe probarse primero en una base de datos de desarrollo y verificarse contra las vistas y reglas de seguridad de la instalación exacta de Odoo 18.
