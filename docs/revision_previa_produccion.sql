-- =====================================================================================================
-- Revisión previa a instalar website_motos_alfa_showcase + motos_trazabilidad en PRODUCCIÓN.
--
-- SOLO LECTURA: la primera línea pone la sesión en modo solo lectura; PostgreSQL rechaza cualquier
-- cambio. No modifica nada de la base.
--
-- Cómo ejecutarlo (cambiar <usuario> y <base> por los de producción):
--   psql -U <usuario> -d <base> -f revision_previa_produccion.sql > resultado_revision.txt
-- Con Docker:
--   docker compose exec -T db psql -U <usuario> -d <base> < revision_previa_produccion.sql > resultado_revision.txt
--
-- Si alguna consulta da error (p. ej. porque la Tienda no está instalada y no existe la columna), es normal:
-- el resto sigue ejecutándose. Enviar el archivo resultado_revision.txt completo.
-- =====================================================================================================

SET default_transaction_read_only = on;
\pset pager off

\echo '\n=== 1. Versión de Odoo (debe empezar por 18.0) ==='
SELECT latest_version FROM ir_module_module WHERE name = 'base';

\echo '\n=== 2. Apps que el módulo necesita (si alguna NO está «installed», se instalará sola) ==='
SELECT name, state
FROM ir_module_module
WHERE name IN ('website', 'website_sale', 'website_crm', 'crm', 'stock', 'product', 'sale')
ORDER BY name;

\echo '\n=== 3. ¿Ya existen estos módulos (u otros con nombres parecidos)? ==='
SELECT name, state, latest_version
FROM ir_module_module
WHERE name IN ('website_motos_alfa_showcase', 'motos_trazabilidad') OR name ILIKE '%moto%'
ORDER BY name;

\echo '\n=== 4. Ajustes que el módulo activa para todos los usuarios internos (t = ya activo, f = se activará) ==='
SELECT 'Variantes de producto' AS ajuste,
       EXISTS (
           SELECT 1 FROM res_groups_implied_rel r
           WHERE r.gid = (SELECT res_id FROM ir_model_data WHERE module = 'base' AND name = 'group_user')
             AND r.hid = (SELECT res_id FROM ir_model_data WHERE module = 'product' AND name = 'group_product_variant')
       ) AS ya_activo
UNION ALL
SELECT 'Lotes y números de serie',
       EXISTS (
           SELECT 1 FROM res_groups_implied_rel r
           WHERE r.gid = (SELECT res_id FROM ir_model_data WHERE module = 'base' AND name = 'group_user')
             AND r.hid = (SELECT res_id FROM ir_model_data WHERE module = 'stock' AND name = 'group_production_lot')
       );

\echo '\n=== 5. ¿Existe ya una categoría raíz llamada MOTOS? (si sale, sus productos pasan a ser «motos») ==='
SELECT id, name, parent_path
FROM product_category
WHERE parent_id IS NULL AND name ILIKE 'motos';

\echo '\n=== 5b. Productos dentro de esa categoría (y subcategorías) que tendrían página /moto/... ==='
SELECT t.id, t.name->>'es_CO' AS nombre_es, t.name->>'en_US' AS nombre_en, c.name AS categoria,
       t.sale_ok AS se_vende, t.is_published AS publicado, t.active AS activo
FROM product_template t
JOIN product_category c ON c.id = t.categ_id
JOIN product_category root ON root.parent_id IS NULL AND root.name ILIKE 'motos'
WHERE c.parent_path LIKE root.parent_path || '%'
ORDER BY t.id
LIMIT 200;

\echo '\n=== 6. ¿Hay un menú «Modelos» en el sitio? (si es mega menú, se llenará solo con las motos) ==='
SELECT id, name, (mega_menu_content IS NOT NULL) AS es_mega_menu, url, website_id
FROM website_menu
WHERE name::text ILIKE '%modelos%';

\echo '\n=== 7. ¿Hay páginas o redirecciones del sitio en /moto o /motos? (chocarían con las del módulo; deberían salir vacías) ==='
SELECT 'página' AS tipo, id, url AS ruta, website_id FROM website_page WHERE url ILIKE '/moto%'
UNION ALL
SELECT 'redirección', id, url_from, website_id FROM website_rewrite WHERE url_from ILIKE '/moto%' OR url_to ILIKE '/moto%';

\echo '\n=== 8. Otros módulos que ya modifican las mismas vistas que este módulo modifica ==='
SELECT parent.module || '.' || parent.name AS vista_de_odoo,
       COALESCE(d.module, '(sin módulo: hecha a mano o con Studio)') AS modificada_por,
       v.name AS vista_que_la_modifica, v.active AS activa
FROM ir_model_data parent
JOIN ir_ui_view v ON v.inherit_id = parent.res_id
LEFT JOIN ir_model_data d ON d.model = 'ir.ui.view' AND d.res_id = v.id
WHERE parent.model = 'ir.ui.view'
  AND (parent.module, parent.name) IN (
      ('website', 'layout'),
      ('website', 'snippets'),
      ('website', 'snippet_options'),
      ('website', 'submenu'),
      ('website_sale', 'product_template_form_view'),
      ('website_sale', 'product_product_view_form_easy_inherit_website_sale'),
      ('stock', 'view_production_lot_form')
  )
  AND COALESCE(d.module, '') NOT IN (
      'website', 'website_sale', 'website_crm', 'crm', 'stock', 'product', 'sale', 'web_editor', 'website_mass_mailing',
      'website_payment', 'website_sale_stock', 'website_sale_wishlist', 'website_sale_comparison', 'website_links',
      'website_livechat', 'website_blog', 'website_event', 'website_slides', 'website_forum', 'website_hr_recruitment',
      'website_sms', 'website_google_map', 'website_customer', 'website_partner', 'website_sale_loyalty',
      'website_sale_slides', 'website_sale_mrp', 'website_sale_autocomplete', 'website_sale_collect',
      'website_crm_partner_assign', 'website_profile', 'mrp', 'purchase_stock', 'sale_stock', 'stock_account',
      'quality_control', 'mrp_repair', 'repair', 'product_expiry', 'website_sale_stock_wishlist',
      'website_crm_sms', 'website_sale_picking', 'website_form_project', 'website_project', 'website_cf_turnstile',
      'website_sale_mondialrelay', 'website_jitsi', 'website_event_track', 'website_event_sale',
      'website_event_exhibitor', 'website_event_booth', 'website_event_meet', 'website_mail', 'website_crm_iap_reveal',
      'website_mail_group', 'website_twitter', 'website_sale_product_configurator', 'website_hr_recruitment_skills',
      'website_appointment', 'website_helpdesk', 'website_knowledge', 'website_studio', 'website_documents'
  )
ORDER BY 1, 2;

\echo '\n=== 9. Módulos instalados que NO son de Odoo S.A. (personalizados o de terceros) ==='
SELECT name, author, latest_version
FROM ir_module_module
WHERE state = 'installed' AND COALESCE(author, '') NOT ILIKE '%Odoo S.A.%'
ORDER BY name;

\echo '\n=== 10. ¿Ya existen campos o tablas con los mismos nombres que crea el módulo? (si el módulo no está instalado, deberían salir vacíos) ==='
SELECT table_name, column_name
FROM information_schema.columns
WHERE (table_name = 'stock_lot' AND column_name IN ('bin_code', 'chassis_code', 'is_motorcycle'))
   OR (table_name = 'product_template' AND column_name IN ('moto_main_variant_id', 'moto_spec_sheet', 'moto_spec_sheet_name'));
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('moto_component_assignment', 'product_template_moto_360_rel', 'product_product_moto_360_rel');

\echo '\n=== 11. Sitios web y país de la compañía (el formulario de cotización usa los departamentos de Colombia) ==='
SELECT w.id, w.name AS sitio, c.name AS compania, co.code AS pais
FROM website w
JOIN res_company c ON c.id = w.company_id
LEFT JOIN res_partner p ON p.id = c.partner_id
LEFT JOIN res_country co ON co.id = p.country_id
ORDER BY w.id;

\echo '\n=== Fin de la revisión ==='
