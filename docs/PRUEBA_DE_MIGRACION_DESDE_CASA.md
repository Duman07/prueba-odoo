# Prueba de migración desde el computador de la casa (guía paso a paso, 29-10-2026; puesta al día el 29-10-2026 en la tarde)

Módulos: `addons/website_motos_alfa_showcase` y `addons/motos_trazabilidad`

**Qué se prueba:** que en un Odoo 18 **vacío** basta con traer el código y ejecutar **una** instalación para que
aparezca todo lo de la moto (sitio web, inventario, CRM), sin tocar Ajustes, Studio ni el editor del sitio. Es lo
mismo que hará el jefe en el Odoo de la empresa. En el computador del trabajo ya pasó (29-10-2026, con el código
hasta el commit `456c377`: instalación sin errores y 44 pruebas, 0 fallos); aquí se repite en un computador que nunca
vio Db-demo.

**Qué trae el código desde el primer intento** (todo se revisa en los pasos 6 a 9):
carrusel de `/motos`, «Datos clave» debajo de la imagen principal, «Galería», botón «Descargar ficha técnica (PDF)»,
«Otras motos de tipo…» con «Volver a…», datos para Google (JSON-LD), fotos con caché pública y el bloque
«Última moto vista» para el inicio.

- No se copia ninguna base de datos ni ningún archivo a mano: todo llega con `git pull`.
- La base de prueba se llama `prueba_casa`. Si en la casa tienes otra base (la del primer intento), **no se usa**.
- Tiempo aproximado: 40-60 minutos (la instalación sola tarda 5-10).
- Los comandos se escriben en una terminal, dentro de la carpeta del proyecto (la que tiene `docker-compose.yml`).
  En Windows sirven igual en PowerShell.

---

## Paso 0. Antes de salir del trabajo
- [ ] `git push` de la rama `fix/pyjwt-requirement`. `git status -sb` debe decir solo
      `## fix/pyjwt-requirement...origin/fix/pyjwt-requirement`, sin «adelante». Sin el push, la casa no recibe nada.
- [ ] Comprobar en GitHub (rama `fix/pyjwt-requirement`) que el último commit es `456c377` («pruebas de la seccion
      otras motos de tipo…») o uno más nuevo, y que existen `addons/website_motos_alfa_showcase/data/` y
      `addons/motos_trazabilidad/data/`.
- [ ] Tener a mano para el paso 7: 3-4 fotos cualquiera (`.jpg` o `.webp`) y un PDF cualquiera (de ficha técnica).

---

## Paso 1. Dejar el código de la casa igual al de GitHub

### 1.1 Quitar el arreglo que hiciste a mano en la casa
En el primer intento creaste en la casa `data/product_variant_group.xml` y cambiaste el manifiesto. Ese arreglo ya
está en el repositorio (y más completo). Si se queda, `git pull` falla con
`untracked working tree files would be overwritten`.
```bash
git status
```
- Si sale `addons/website_motos_alfa_showcase/data/product_variant_group.xml` como `??` (sin seguimiento), muévelo
  fuera del proyecto (por ejemplo al Escritorio) o bórralo.
- Si sale algún archivo como `M` (modificado) dentro de `addons/`, descarta el cambio:
  `git restore <archivo>` (o guárdalo aparte con `git stash` si quieres conservarlo).
- `addons/website_motos_alfa_showcase/tests/__pycache__/__init__.cpython-312.pyc` puede salir como `M`: es un archivo
  que Python vuelve a generar solo. Descártalo igual: `git restore addons/website_motos_alfa_showcase/tests/__pycache__/`.
- Al final, `git status` no debe mostrar nada dentro de `addons/`.

### 1.2 Traer el código
```bash
git fetch
git checkout fix/pyjwt-requirement
git pull
git log --oneline -1
```
`git log` debe mostrar `456c377 pruebas de la seccion otras motos de tipo…` (o uno más nuevo).

### 1.3 Comprobar que están las dos carpetas y los archivos nuevos
```bash
ls addons
ls addons/website_motos_alfa_showcase/data addons/motos_trazabilidad/data
```
- [ ] En `addons` están `website_motos_alfa_showcase` **y** `motos_trazabilidad` (este faltaba en el primer intento).
- [ ] En `website_motos_alfa_showcase/data`: `crm_lead_form_whitelist.xml`, `product_category_motos.xml`,
      `product_variant_group.xml`. En `motos_trazabilidad/data`: `stock_lot_group.xml`.

---

## Paso 2. Levantar Odoo
```bash
docker compose up -d
docker ps --format '{{.Names}}'
```
(Si tu Docker es viejo y no existe `docker compose`, usa `docker-compose up -d`.)

Anota el nombre del contenedor de Odoo (el que termina en `odoo18-1`). En el trabajo es `odoo-one-odoo18-1`; en la
casa puede cambiar si la carpeta del proyecto se llama distinto. **En los comandos de abajo reemplaza
`odoo-one-odoo18-1` por el tuyo.**

Si ya estaba levantado de antes, **reinícialo** para que lea los manifiestos nuevos:
```bash
docker restart odoo-one-odoo18-1
```

Comprueba que `pyjwt` está instalado (lo pide `auth_jwt`; el contenedor lo instala al arrancar desde
`etc/requirements.txt`):
```bash
docker exec odoo-one-odoo18-1 python3 -c "import jwt; print('pyjwt', jwt.__version__)"
```
- [ ] Sale `pyjwt` y un número. (Si dice `No module named 'jwt'`, revisa que `etc/requirements.txt` tenga la línea
      `pyjwt` y reinicia el contenedor.)

---

## Paso 3. Crear la base nueva con UNA sola instalación
```bash
docker exec odoo-one-odoo18-1 sh -c 'odoo -c /etc/odoo/odoo.conf -d prueba_casa --db_host=db --db_user=odoo --db_password="$PASSWORD" -i website_motos_alfa_showcase --without-demo=all --load-language=es_CO --stop-after-init --no-http'
```
- **Solo** se nombra `website_motos_alfa_showcase`. Él trae por sus `depends` el Comercio electrónico, el CRM, el
  Inventario y `motos_trazabilidad`, y activa «Variantes» y «Lotes y números de serie». Si hubiera que nombrar otro
  módulo para que algo funcione, la prueba **falla** (anótalo).
- `--without-demo=all`: sin datos de ejemplo, como la empresa. `--load-language=es_CO`: español de Colombia.
- `--stop-after-init --no-http`: instala y se apaga, sin chocar con el Odoo que ya está corriendo.
- En pantalla pueden salir líneas `Unexpected indentation` o `Block quote ends without a blank line`: son avisos
  de Odoo al leer los README de los módulos, **no** son errores.

Al terminar, busca errores:
```bash
docker exec odoo-one-odoo18-1 sh -c 'grep -E " ERROR | CRITICAL " /etc/odoo/odoo-server.log | grep prueba_casa | tail -5'
```
- [ ] No sale nada. (Si salen líneas, cópialas tal cual: son el resultado de la prueba.)

---

## Paso 4. Correr las pruebas automáticas
```bash
docker exec odoo-one-odoo18-1 sh -c 'odoo -c /etc/odoo/odoo.conf -d prueba_casa --db_host=db --db_user=odoo --db_password="$PASSWORD" -u website_motos_alfa_showcase,motos_trazabilidad --test-tags /website_motos_alfa_showcase,/motos_trazabilidad --http-port 8099 --stop-after-init'
docker exec odoo-one-odoo18-1 sh -c 'grep -E "FAIL:|ERROR: |tests when loading" /etc/odoo/odoo-server.log | grep -v Db-demo | tail -5'
```
- [ ] La última línea dice `0 failed, 0 error(s) of 44 tests when loading database 'prueba_casa'`
      (o más, si después se agregan pruebas).

---

## Paso 5. Entrar a la base nueva
1. Abre `http://localhost:10018/web/login?db=prueba_casa` (cambia `10018` si en la casa usas otro puerto).
2. Usuario `admin`, contraseña `admin` (la que pone Odoo a una base creada por comando; solo para esta prueba).
3. Si sale en inglés: avatar (arriba a la derecha) → **Preferencias** → **Idioma: Spanish (CO)** → guardar.

---

## Paso 6. Revisar lo que el módulo crea solo (sin crear nada todavía)

### 6.1 Menús y ajustes
- [ ] En el menú principal están **Inventario**, **CRM**, **Sitio web** y **Ventas**.
- [ ] **Ajustes → Inventario**: «Lotes y números de serie» está **marcado**. **Ajustes → Ventas** (o Inventario):
      «Variantes» está **marcado**. (No los toques: solo se mira.)
- [ ] **Inventario → Configuración → Atributos** existe.
- [ ] **Inventario → Configuración → Categorías de productos**: ya existe **MOTOS** (una sola).
- [ ] **Inventario → Productos → Números de serie/lote** existe.
- [ ] **Inventario → Trazabilidad de motos → Componentes instalados** existe.

### 6.2 Formulario del producto
**Inventario → Productos → Nuevo**, escribe un nombre cualquiera (no guardes todavía):
- [ ] Pestaña **Atributos y variantes** visible.
- [ ] Pestaña **Ventas** → grupo **«Página de la moto»** con **«Color principal»**, **«Fotos 360°»** y
      **«Ficha técnica (PDF)»** (solo si «Se puede vender» está marcado).
- [ ] Pestaña **Inventario** (o General): **«Rastrear inventario»** con la opción **«Por número de serie»**.
Descarta el producto (botón de descartar, la flecha curva).

### 6.3 Página Motocicletas
Abre `http://localhost:10018/motos`:
- [ ] Título «Motocicletas», el **carrusel** (con las fotos y textos de ejemplo de Odoo, botones rojos) y el bloque
      «Tipos de moto» (sin motos puede salir vacío).
- [ ] En el encabezado, **«Modelos»** y **«Motocicletas»**, cada uno **una sola vez**.

---

## Paso 7. Crear la moto de prueba (a mano, como lo hará el jefe)

### 7.1 Categorías
Inventario → Configuración → **Categorías de productos** → Nuevo:
1. `Urbana`, con categoría padre `MOTOS`.
2. `Prueba`, con categoría padre `MOTOS / Urbana`.

### 7.2 Atributos
Inventario → Configuración → **Atributos** → Nuevo:
- `Color`: tipo de visualización **Color**, creación de variantes **Instantáneamente**; valores `Rojo` y `Negro`
  (elige su color en la columna de color).
- `Motor`: creación de variantes **Nunca**; valores `Cilindraje: 160 cc` y `Potencia: 15 HP`.

### 7.3 La moto
Inventario → Productos → Nuevo:
- Nombre `Moto Prueba`; marcar **Se puede vender**; precio de venta `9990000`.
- Categoría `MOTOS / Urbana / Prueba`.
- **Rastrear inventario** marcado → **Por número de serie**.
- Pestaña **Atributos y variantes**: `Color` (Rojo, Negro) y `Motor` (los dos valores).
- Sube una foto del producto (la imagen de arriba a la derecha del formulario).
- Guarda. Luego botón **Sitio web** (arriba) → **Publicar** (o «Ir al sitio web» → interruptor «Publicado»).

### 7.4 Subir archivos (lo que no salía en el primer intento)
- [ ] Botón **Variantes** (arriba en el producto) → abre **Rojo** → grupo **«Fotos 360°»** → sube 3 fotos a la vez
      (cualquier `.jpg`/`.webp` llamadas `moto-1`, `moto-2`, `moto-10`). Se ven las tres. Guarda.
- [ ] En la variante **Rojo**, **«Medios adicionales»** (o en el producto, pestaña Ventas → «Medios adicionales para
      el producto»): agrega 3 fotos. La primera será el fondo de la sección con la frase; las otras dos, la «Galería».
- [ ] En el producto, pestaña **Ventas** → «Página de la moto» → **«Ficha técnica (PDF)»**: sube el PDF. Guarda.
- [ ] (Opcional) En el producto, con el **clip** de adjuntos (arriba a la derecha, en el chat), sube un `.glb`.

### 7.5 Una segunda moto del mismo tipo (para «Otras motos»)
Inventario → Productos → Nuevo: nombre `Moto Prueba Dos`, **Se puede vender**, categoría `MOTOS / Urbana / Prueba`,
una foto. Guarda y **publícala** (como en 7.3).

---

## Paso 8. Revisar la página de la moto
Abre `http://localhost:10018/motos` → tarjeta **Urbana** → **Moto Prueba** (o desde el menú «Modelos»).
- [ ] Nombre «Moto Prueba», precio `$ 9.990.000`, muestras **Rojo** y **Negro**; al tocar un color cambia la imagen.
- [ ] **«Datos clave»** debajo de la imagen principal: «160 cc» y «15 HP» en rojo, con «Cilindraje» y «Potencia»
      en gris debajo.
- [ ] **«Especificaciones técnicas»**: acordeón con «Motor» abierto («−»), filas «Cilindraje / 160 cc» y
      «Potencia / 15 HP». Debajo, el botón rojo **«Descargar ficha técnica (PDF)»**: al dar clic descarga el PDF del 7.4.
- [ ] **«Galería»** («Fotos de la moto»): las 2 fotos de «Medios adicionales» que no fueron de fondo. Al dar clic, la
      foto se abre en grande.
- [ ] Al final, **«Otras motos de tipo Urbana»** en negrilla con la tarjeta de «Moto Prueba Dos», y **«Volver a
      Urbana»** en rojo (no en morado), que lleva a `/motos/urbana-…`.
- [ ] Con las fotos del 7.4: aparece la sección «Explórala en 360°» y al arrastrar gira (moto-1 → moto-2 → moto-10).
      **Sin** fotos ni `.glb` esa sección no aparece (si quieres verlo, prueba antes del 7.4).
- [ ] **Sin imágenes rotas**: `F12` → pestaña **Consola** (y **Red**, filtrando por «404»): ningún error 404.
- [ ] En celular (`F12` → ícono de celular): se ve bien y el botón de WhatsApp no tapa el pie.
- [ ] `/motos/urbana-…` muestra las tarjetas de «Moto Prueba» y «Moto Prueba Dos», **sin** el carrusel.
- [ ] **Datos para Google:** `Ctrl+U` (ver código fuente) → `Ctrl+F` «ld+json»: sale un bloque con `"Moto Prueba"`,
      `"Hero"`, `"price": "9990000"` y `"priceCurrency": "COP"`.
- [ ] **Caché de las fotos:** `F12` → **Red** → recarga → clic en una foto de `/moto/media/…` → **Encabezados de
      respuesta**: `Cache-Control: public, max-age=86400`.

### 8.1 Bloque «Última moto vista» en el inicio
Esto sí se hace en el editor, porque es lo mismo que hará el jefe en el inicio de la empresa (paso 9 de «En
producción» en `MIGRACION_A_OTRO_ESPACIO_DE_ODOO.md`):
1. Abre el inicio (`http://localhost:10018/`) → **Editar** → panel de bloques, grupo **«Motos Alfa»** → arrastra
   **«Última moto vista»** a la página → **Guardar**.
2. Abre el inicio en una **ventana privada** (`Ctrl+Shift+N`):
   - [ ] El bloque **no** aparece (todavía no has visto ninguna moto en esa ventana).
3. En esa misma ventana abre «Moto Prueba» y vuelve al inicio:
   - [ ] Sale la **foto en grande** y el **nombre** de «Moto Prueba»; clic → su página.
4. Abre «Moto Prueba Dos» y vuelve al inicio:
   - [ ] Ahora sale «Moto Prueba Dos» (se recuerda solo la última).

---

## Paso 9. Recepción de la moto con número de serie, BIN y chasis
1. **Inventario → Operaciones → Recepciones → Nuevo**: proveedor cualquiera; en la línea, producto
   `Moto Prueba (Rojo)`, cantidad `1`. **Guardar** → **Marcar como por hacer** (si sale).
2. En la línea, el ícono de lista (detalles) o la columna **Números de serie/lote**: escribe `SERIE-CASA-001`.
3. **Validar**.
4. **Inventario → Productos → Números de serie/lote** → abre `SERIE-CASA-001`:
   - [ ] Están **BIN**, **Código de chasis** y **«Es una moto»**.
   - [ ] Marca «Es una moto», escribe BIN `BIN-CASA-001` y chasis `CHASIS-CASA-001`, guarda.
   - [ ] Aparece la pestaña **«Componentes e historial»**.
5. **Inventario → Informes → Existencias**: la fila de la moto tiene las columnas **BIN** y **Chasis** con lo que
   escribiste (si no se ven, actívalas en el ícono de columnas a la derecha).

---

## Paso 10. Formulario de cotización
En la página de la moto, «Solicita la cotización de tu moto»:
- [ ] «Modelo» trae «Moto Prueba» elegida; «Departamento» muestra los de Colombia; la casilla de autorización está
      antes de **ENVIAR** y es obligatoria.
- [ ] Llénalo (País Colombia, un Departamento, Ciudad `Medellín`) y envíalo → página de gracias.
- [ ] **CRM** → abre la oportunidad nueva: **País**, **Departamento** y **Ciudad** están **en sus campos**
      (pestaña o bloque de dirección). En **«Notas internas» / «Otra información»** NO deben aparecer como texto.

---

## Paso 11. Actualizar otra vez y ver que nada se pierde ni se duplica
```bash
docker exec odoo-one-odoo18-1 sh -c 'odoo -c /etc/odoo/odoo.conf -d prueba_casa --db_host=db --db_user=odoo --db_password="$PASSWORD" -u website_motos_alfa_showcase,motos_trazabilidad --stop-after-init --no-http'
```
Recarga Odoo y revisa:
- [ ] La moto, sus fotos 360°, sus «Medios adicionales», la ficha PDF, la serie con BIN y chasis y la oportunidad
      siguen ahí.
- [ ] El bloque «Última moto vista» sigue en el inicio.
- [ ] Una sola categoría **MOTOS**; «Modelos» y «Motocicletas» una sola vez en el encabezado.
- [ ] «Variantes» y «Lotes y números de serie» siguen marcados.

---

## Paso 12. Resultado
- **Todo marcado:** la instalación en una base nueva funciona. Me lo cuentas y lo marco en
  `MIGRACION_A_OTRO_ESPACIO_DE_ODOO.md`.
- **Algo falló:** anota el número del paso, qué esperabas y qué salió (una captura o las líneas del log). **No lo
  arregles en Ajustes, Studio ni el editor**: el arreglo va en el código, si no el jefe tendría el mismo problema.
- **No guardes cambios en el editor sobre `/motos` ni las páginas de las motos** durante la prueba: crearían copias de
  la página que tapan las del módulo (lo que pasó en el trabajo el 29-10-2026). El único guardado en el editor es el
  del bloque en el inicio (8.1).

## Paso 13. Limpiar (opcional)
`http://localhost:10018/web/database/manager` → **Delete** junto a `prueba_casa` (pide la contraseña maestra).
**Revisa bien el nombre** antes de borrar.

## Archivos relacionados
- `addons/website_motos_alfa_showcase/README.md` y `addons/motos_trazabilidad/README.md`: qué hace cada archivo.
- En el computador del trabajo: `~/website_motos_alfa_showcase/MIGRACION_A_OTRO_ESPACIO_DE_ODOO.md` (el plan) y
  `PRUEBA_DE_MIGRACION_EN_BASE_NUEVA.md` (la misma prueba, hecha en el trabajo).
