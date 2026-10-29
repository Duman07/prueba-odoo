# Prueba de migración desde el computador de la casa (guía paso a paso, 29-10-2026)

Módulos: `addons/website_motos_alfa_showcase` y `addons/motos_trazabilidad`

**Qué se prueba:** que en un Odoo 18 **vacío** basta con traer el código y ejecutar **una** instalación para que
aparezca todo lo de la moto (sitio web, inventario, CRM), sin tocar Ajustes, Studio ni el editor del sitio. Es lo
mismo que hará el jefe en el Odoo de la empresa. En el computador del trabajo ya pasó (29-10-2026: 33 pruebas,
0 fallos); aquí se repite en un computador que nunca vio Db-demo.

- No se copia ninguna base de datos ni ningún archivo a mano: todo llega con `git pull`.
- La base de prueba se llama `prueba_casa`. Si en la casa tienes otra base (la del primer intento), **no se usa**.
- Tiempo aproximado: 40-60 minutos (la instalación sola tarda 5-10).
- Los comandos se escriben en una terminal, dentro de la carpeta del proyecto (la que tiene `docker-compose.yml`).
  En Windows sirven igual en PowerShell.

---

## Paso 0. Antes de salir del trabajo
- [ ] Hacer el commit de la instalación en base nueva (descripción lista, en la conversación del 29-10-2026) y
      `git push`. Sin el push, la casa no recibe nada.
- [ ] Comprobar en GitHub (rama `fix/pyjwt-requirement`) que está el commit y que existen
      `addons/website_motos_alfa_showcase/data/` y `addons/motos_trazabilidad/data/`.

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
- Al final, `git status` no debe mostrar nada dentro de `addons/`.

### 1.2 Traer el código
```bash
git fetch
git checkout fix/pyjwt-requirement
git pull
git log --oneline -1
```
`git log` debe mostrar el commit de la instalación en base nueva (o uno más nuevo).

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
- [ ] La última línea dice `0 failed, 0 error(s) of 33 tests when loading database 'prueba_casa'`
      (35 o más si ya incluye las pruebas de «Otras motos»).

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
- [ ] Pestaña **Ventas** → grupo **«Página de la moto»** con **«Color principal»** y **«Fotos 360°»**
      (solo si «Se puede vender» está marcado).
- [ ] Pestaña **Inventario** (o General): **«Rastrear inventario»** con la opción **«Por número de serie»**.
Descarta el producto (botón de descartar, la flecha curva).

### 6.3 Página Motocicletas
Abre `http://localhost:10018/motos`:
- [ ] Título «Motocicletas» y el bloque «Tipos de moto» (sin motos puede salir vacío).
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
- [ ] (Opcional) En el producto, con el **clip** de adjuntos (arriba a la derecha, en el chat), sube un `.glb`.

---

## Paso 8. Revisar la página de la moto
Abre `http://localhost:10018/motos` → tarjeta **Urbana** → **Moto Prueba** (o desde el menú «Modelos»).
- [ ] Nombre «Moto Prueba», precio `$ 9.990.000`, muestras **Rojo** y **Negro**; al tocar un color cambia la imagen.
- [ ] **«Especificaciones técnicas»**: acordeón con «Motor» abierto («−»), filas «Cilindraje / 160 cc» y
      «Potencia / 15 HP».
- [ ] Con las fotos del 7.4: aparece la sección «Explórala en 360°» y al arrastrar gira (moto-1 → moto-2 → moto-10).
      **Sin** fotos ni `.glb` esa sección no aparece (si quieres verlo, prueba antes del 7.4).
- [ ] **Sin imágenes rotas**: `F12` → pestaña **Consola** (y **Red**, filtrando por «404»): ningún error 404.
- [ ] En celular (`F12` → ícono de celular): se ve bien y el botón de WhatsApp no tapa el pie.
- [ ] `/motos/urbana-…` muestra la tarjeta de «Moto Prueba».

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
- [ ] La moto, sus fotos 360°, la serie con BIN y chasis y la oportunidad siguen ahí.
- [ ] Una sola categoría **MOTOS**; «Modelos» y «Motocicletas» una sola vez en el encabezado.
- [ ] «Variantes» y «Lotes y números de serie» siguen marcados.

---

## Paso 12. Resultado
- **Todo marcado:** la instalación en una base nueva funciona. Me lo cuentas y lo marco en
  `MIGRACION_A_OTRO_ESPACIO_DE_ODOO.md`.
- **Algo falló:** anota el número del paso, qué esperabas y qué salió (una captura o las líneas del log). **No lo
  arregles en Ajustes, Studio ni el editor**: el arreglo va en el código, si no el jefe tendría el mismo problema.

## Paso 13. Limpiar (opcional)
`http://localhost:10018/web/database/manager` → **Delete** junto a `prueba_casa` (pide la contraseña maestra).
**Revisa bien el nombre** antes de borrar.

## Archivos relacionados
- `addons/website_motos_alfa_showcase/README.md` y `addons/motos_trazabilidad/README.md`: qué hace cada archivo.
- En el computador del trabajo: `~/website_motos_alfa_showcase/MIGRACION_A_OTRO_ESPACIO_DE_ODOO.md` (el plan) y
  `PRUEBA_DE_MIGRACION_EN_BASE_NUEVA.md` (la misma prueba, hecha en el trabajo).
