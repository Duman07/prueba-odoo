"""Llena la «Plantilla de motos» (views/moto_template.xml) con los datos de una moto.

Los datos se colocan en los bloques que ya usa el diseño, sin marcas especiales:
- «Moto 3D» (.s_moto_3d): foto, nombre en el <h1> y categoría en el texto que lo precede.
- Cualquier texto igual al título original del diseño: nombre de la moto.
- «Visor 360°» (.s_moto_360): modelo .glb o fotos 360° del primer color y una muestra por color, copiando la
  primera muestra del diseño. Elegir un color solo cambia la imagen principal («Moto 3D», data-main-src).
- «Especificaciones técnicas» (.s_moto_specs): un grupo del acordeón por especificación, copiando el primero.
- Secciones con imagen de fondo y videos del diseño: fotos y videos de «Medios adicionales» del primer color
  (o del producto), en orden; el título de la primera sección con fondo lleva la descripción del producto.
- Campo «Modelo» del formulario: lista de motos, con la actual elegida.
- antes del boton enviar del formulario: se agrega un campo de consentimiento de datos personales para recibir información sobre productos y servicios de la marca.
"""
import copy
import json
import re
from urllib.parse import unquote
from lxml import html

ZERO_WIDTH = re.compile("[​‌‍﻿]")


def _norm(text):
    return " ".join(ZERO_WIDTH.sub("", text or "").split()).casefold()


def _set_text(element, text):
    """Cambia el texto conservando el formato: baja por el único hijo (span > strong > font…)."""
    while len(element) == 1 and not (element.text or "").strip() and not (element[0].tail or "").strip():
        element = element[0]
    for child in list(element):
        element.remove(child)
    element.text = text


def _classes(element):
    return (element.get("class") or "").split()


def _find(root, css_class):
    return root.xpath(f".//*[contains(concat(' ', normalize-space(@class), ' '), ' {css_class} ')]")


def _fill_title(wrap, moto):
    """Nombre en el <h1> de «Moto 3D» y en los textos iguales a él; categoría en el texto de encima."""
    title_texts = set()
    for block in _find(wrap, "s_moto_3d"):
        title = next(iter(block.iter("h1")), None)
        if title is None:
            continue
        title_texts.add(_norm(title.text_content()))
        _set_text(title, moto.name.upper())
        previous = title.getprevious()
        if previous is not None and previous.tag == "p" and previous.text_content().strip():
            _set_text(previous, moto.categ_id.name.upper())
    if not title_texts:
        return
    for element in wrap.iter():
        if not isinstance(element.tag, str) or element.tag in ("h1", "script", "style", "option"):
            continue
        if element.text and _norm(element.text) in title_texts and len(element) == 0:
            element.text = moto.name


def _fill_viewers(wrap, intro_src, viewer_src, moto):
    for block in _find(wrap, "s_moto_3d"):
        block.set("data-model-src", intro_src)
        block.set("data-model-alt", moto.name)
    for block in _find(wrap, "s_moto_360"):
        block.set("data-model-src", viewer_src)
        block.set("data-model-alt", moto.name)


PRICE_TEXT = re.compile(r"^\$\s*0[.,]?$")
# Estatuto del consumidor
PRICE_NOTE = "Precio con IVA incluido, sujeto a cambios. No incluye matrícula ni SOAT."


def _fill_price(wrap, price):
    """Precio en «Moto 3D»: el texto «$0» del diseño lleva el precio de la moto y la clase s_moto_price
    (el «Precio desde:» de encima, s_moto_price_label); el estilo está en s_moto_snippets.scss.
    Si no tiene precio, se quitan los dos."""
    for block in _find(wrap, "s_moto_3d"):
        for element in list(block.iter("p")):
            if not PRICE_TEXT.match(_norm(element.text_content())):
                continue
            label = element.getprevious()
            if label is not None and "desde" not in _norm(label.text_content()):
                label = None
            if not price:
                if label is not None:
                    label.getparent().remove(label)
                element.getparent().remove(element)
                continue
            _set_text(element, "$" + f"{round(price):,}".replace(",", "."))
            element.set("class", " ".join(_classes(element) + ["s_moto_price"]))
            if label is not None:
                label.set("class", " ".join(_classes(label) + ["s_moto_price_label"]))
            note = html.Element("p", {"class": "s_moto_price_note"})
            note.text = PRICE_NOTE
            element.addnext(note)


def _fill_colors(wrap, colors):
    for container in _find(wrap, "s_moto_360_swatches"):
        swatches = _find(container, "s_moto_360_swatch")
        if not swatches:
            continue
        prototype = swatches[0]
        for swatch in swatches:
            container.remove(swatch)
        for color in colors:
            swatch = copy.deepcopy(prototype)
            swatch.tail = None
            for attribute in ("data-model-src", "data-variant"):
                swatch.attrib.pop(attribute, None)
            swatch.set("style", f"background-color: {color['html_color']};")
            swatch.set("data-color-name", color["name"])
            # Al elegir el color, la imagen principal muestra su foto (la primera foto 360°); el visor no cambia.
            if color["main_src"]:
                swatch.set("data-main-src", color["main_src"])
            swatch.set("data-attribute-value-ids", color["attribute_value_ids"])
            container.append(swatch)
        panel = container.getparent()
        if not colors and panel.getparent() is not None:
            # Moto sin variantes de color: no se muestra el panel «Colores».
            panel.getparent().remove(panel)
            continue
        for name in _find(panel, "s_moto_360_color_name"):
            _set_text(name, colors[0]["name"])


BACKGROUND_IMAGE = re.compile(r"background-image:\s*url\((&quot;|[\"']?)(.*?)\1\)")


def _inside_moto_block(element):
    return any({"s_moto_3d", "s_moto_360"} & set(_classes(el)) for el in element.iterancestors())


def _single_h1(wrap):
    """Un solo <h1> por página: el nombre de la moto en «Moto 3D». Los demás (p. ej. la frase de la sección con fondo)
    pasan a <h2> con la clase h1 de Bootstrap, que conserva su tamaño."""
    for title in list(wrap.iter("h1")):
        if any("s_moto_3d" in _classes(el) for el in title.iterancestors()):
            continue
        title.tag = "h2"
        title.set("class", " ".join(_classes(title) + ["h1"]))


def _fill_media(wrap, media, description):
    """Fondos de sección y videos del diseño (en orden) con los del producto; sin ellos se deja el del diseño."""
    sections = [
        el for el in _find(wrap, "oe_img_bg")
        if BACKGROUND_IMAGE.search(el.get("style") or "")
        and not {"s_moto_3d", "s_moto_360"} & set(_classes(el)) and not _inside_moto_block(el)
    ]
    for section, image in zip(sections, media["images"]):
        section.set("style", BACKGROUND_IMAGE.sub(f'background-image: url("{image}")', section.get("style"), count=1))
    used = min(len(sections), len(media["images"]))
    for video, src in zip(_find(wrap, "media_iframe_video"), media["videos"]):
        video.set("data-oe-expression", src)
        iframe = next(iter(video.iter("iframe")), None)
        if iframe is not None:
            iframe.set("src", src)
    if description and sections:
        title = next((el for el in sections[0].iter("h1", "h2", "h3", "h4", "h5", "h6")), None)
        if title is not None:
            _set_text(title, description)
    return used


def _fill_gallery(wrap, images, moto):
    """«Galería» (.s_moto_gallery): una foto por cada imagen de «Medios adicionales» que no se usó de fondo, copiando la
    primera del diseño; sin fotos se quita la sección. Al hacer clic Odoo la abre en grande (bloque s_image_gallery)."""
    for section in _find(wrap, "s_moto_gallery"):
        items = _find(section, "s_moto_gallery_item")
        if not images or not items:
            section.getparent().remove(section)
            continue
        row = items[0].getparent()
        prototype = items[0]
        for item in items:
            row.remove(item)
        for number, src in enumerate(images, start=1):
            item = copy.deepcopy(prototype)
            for image in item.iter("img"):
                image.set("src", src)
                image.set("alt", f"{moto.name} - foto {number}")
            row.append(item)


def _spec_rows(values):
    """Filas de una especificación: «Etiqueta: valor» → etiqueta (<dt>) y valor (<dd>); sin etiqueta, solo <dd>."""
    rows = html.Element("dl", {"class": "row mb-0"})
    for value in values:
        label, separator, detail = (part.strip() for part in value.partition(":"))
        if separator and detail:
            term = html.Element("dt", {"class": "col-sm-5"})
            term.text = label
            rows.append(term)
            row = html.Element("dd", {"class": "col-sm-7"})
            row.text = detail
        else:
            row = html.Element("dd", {"class": "col-12"})
            row.text = value
        rows.append(row)
    return rows


# «Datos clave»: etiquetas de especificación que se muestran arriba, en este orden (la etiqueta debe contener la palabra:
# «Max. Potencia» cuenta como «potencia»). Se muestran como máximo MAX_KEY_SPECS.
KEY_SPECS = ("cilindraje", "potencia", "torque", "freno", "consumo", "tanque", "peso")
MAX_KEY_SPECS = 4


def _key_specs(specs):
    """Datos clave de la moto: de sus filas «Etiqueta: valor», una por cada palabra de KEY_SPECS, en ese orden."""
    rows = []
    for spec in specs:
        for value in spec["values"]:
            label, separator, detail = (part.strip() for part in value.partition(":"))
            if separator and detail:
                rows.append((label, detail.rstrip(".")))
    keys = []
    for word in KEY_SPECS:
        row = next((row for row in rows if word in _norm(row[0]) and row not in keys), None)
        if row:
            keys.append(row)
    return keys[:MAX_KEY_SPECS]


def _fill_key_specs(wrap, specs):
    """«Datos clave» (.s_moto_keyspecs, bloque «Números» de Odoo): una casilla por dato, copiando la primera del diseño;
    sin datos clave se quita la sección."""
    keys = _key_specs(specs)
    for section in _find(wrap, "s_moto_keyspecs"):
        boxes = _find(section, "s_moto_keyspec")
        if not keys or not boxes:
            section.getparent().remove(section)
            continue
        row = boxes[0].getparent()
        prototype = boxes[0]
        for box in boxes:
            row.remove(box)
        for label, detail in keys:
            box = copy.deepcopy(prototype)
            for value in _find(box, "s_moto_keyspec_value"):
                _set_text(value, detail)
            for name in _find(box, "s_moto_keyspec_label"):
                _set_text(name, label)
            row.append(box)


def _fill_spec_sheet(wrap, url, moto):
    """Botón «Descargar ficha técnica (PDF)» (.s_moto_spec_sheet) con la ficha de la moto; sin ficha se quita."""
    for block in _find(wrap, "s_moto_spec_sheet"):
        link = next(block.iter("a"), None)
        if not url or link is None:
            block.getparent().remove(block)
            continue
        link.set("href", url)
        link.set("download", moto.moto_spec_sheet_name or f"{moto.name} - ficha técnica.pdf")


def _fill_specs(wrap, specs):
    """«Especificaciones técnicas» (.s_moto_specs): un grupo del acordeón por especificación, copiando el primero del
    diseño; solo el primero abierto. Sin especificaciones se quita la sección, salvo que tenga el botón de la ficha
    técnica (_fill_spec_sheet va antes): entonces se quita solo el acordeón."""
    for section in _find(wrap, "s_moto_specs"):
        accordion = next(iter(_find(section, "accordion")), None)
        items = _find(section, "accordion-item")
        if not specs or accordion is None or not items:
            if _find(section, "s_moto_spec_sheet"):
                for block in _find(section, "s_accordion"):
                    block.getparent().remove(block)
            else:
                section.getparent().remove(section)
            continue
        prototype = items[0]
        for item in items:
            item.getparent().remove(item)
        accordion_id = accordion.get("id") or "moto_specs"
        accordion.set("id", accordion_id)
        for index, spec in enumerate(specs, start=1):
            item = copy.deepcopy(prototype)
            button = _find(item, "accordion-button")[0]
            panel = _find(item, "accordion-collapse")[0]
            body = _find(item, "accordion-body")[0]
            button_id, panel_id = f"{accordion_id}_btn_{index}", f"{accordion_id}_{index}"
            button.set("id", button_id)
            button.set("data-bs-target", f"#{panel_id}")
            button.set("aria-controls", panel_id)
            panel.set("id", panel_id)
            panel.set("data-bs-parent", f"#{accordion_id}")
            panel.set("aria-labelledby", button_id)
            first = index == 1
            button.set("aria-expanded", "true" if first else "false")
            button.set("class", " ".join([c for c in _classes(button) if c != "collapsed"] + ([] if first else ["collapsed"])))
            panel.set("class", " ".join([c for c in _classes(panel) if c != "show"] + (["show"] if first else [])))
            _set_text(next(iter(button.iter("span")), button), spec["name"])
            for child in list(body):
                body.remove(child)
            body.text = None
            body.append(_spec_rows(spec["values"]))
            accordion.append(item)


def _fill_related(wrap, related):
    """«Otras motos» (.s_moto_related): nombre y enlace del tipo, y una tarjeta por cada otra moto del tipo,
    copiando la primera del diseño. Sin tipo se quita la sección; sin otras motos queda solo «Volver a <tipo>»."""
    for section in _find(wrap, "s_moto_related"):
        if not related["type_name"]:
            section.getparent().remove(section)
            continue
        for name in _find(section, "s_moto_related_type"):
            _set_text(name, related["type_name"])
        for link in _find(section, "s_moto_related_back"):
            link.set("href", related["type_url"])
        cards = _find(section, "s_moto_related_card")
        if not cards:
            continue
        row = cards[0].getparent()
        prototype = cards[0]
        for card in cards:
            row.remove(card)
        for data in related["cards"]:
            card = copy.deepcopy(prototype)
            for link in card.iter("a"):
                link.set("href", data["url"])
            for image in card.iter("img"):
                image.set("alt", data["name"])
                if data["image_url"]:
                    image.set("src", data["image_url"])
            for title in _find(card, "card-title"):
                _set_text(title, data["name"])
            row.append(card)
        if not related["cards"]:
            for title in section.iter("h2"):
                title.getparent().remove(title)
            row.getparent().remove(row)


CONSENT_FIELD = """
<div class="s_website_form_field s_website_form_custom s_website_form_custom s_website_form_required s_moto_form_consent mb-3 col-12" data-type="boolean">
    <div class="form-check">
        <input type="checkbox" class="s_website_form_input form-check-input form-check-input" id="moto_consent"
          name="Autorización de datos" value="Sí" required="required"/>
        <label class="form-check-label" for="moto_consent">Autorizo el tratamiento de mis datos personales para recibir información sobre productos de la marca.
           <a href="https://motosalfa.com.co/politica-tratamiento" target="_blank" style="color: rgb(226, 0, 0)">Política de Tratamiento de Datos</a>
        </label>
    </div>
</div>
"""


def _fill_form(wrap, moto, motos):
    for select in wrap.xpath(".//select[@name='Modelo']"):
        for option in list(select):
            select.remove(option)
        for index, other in enumerate(motos):
            option = html.Element("option", value=other.name, id=f"{select.get('id') or 'moto_model'}{index}")
            option.text = other.name
            if other == moto:
                option.set("selected", "selected")
            select.append(option)
    for submit in _find(wrap, "s_website_form_submit"):
        if submit.getparent().xpath(".//*[contains(@class, 's_moto_form_consent')]"):
            continue
        submit.addprevious(html.fragment_fromstring(CONSENT_FIELD))


def _drop_360(wrap):
    """Sin modelo .glb ni fotos 360°: se quita «Explórala en 360°» y los botones que llevan a ella."""
    for block in _find(wrap, "s_moto_360"):
        anchor = block.get("id")
        if anchor:
            for link in list(wrap.iter("a")):
                if unquote(link.get("href") or "") == f"#{anchor}":
                    link.drop_tree()
        block.getparent().remove(block)


def _add_structured_data(wrap, data):
    """Datos de la moto para Google (_moto_structured_data de models/product.py) en un <script type="application/ld+json">
    al final del contenido. «</» se escribe «<\\/» para que un texto de la moto no pueda cerrar el <script>."""
    script = html.Element("script", {"type": "application/ld+json"})
    script.text = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    wrap.append(script)


def fill_moto_page(page_html, moto, values, editor_notice=None):
    """Devuelve el HTML de la página con los datos de la moto en el contenido principal (<main>)."""
    start = page_html.find("<main>")
    end = page_html.rfind("</main>")
    if start < 0 or end < 0:
        return page_html
    start += len("<main>")
    container = html.fragment_fromstring(page_html[start:end], create_parent="div")
    _fill_title(container, moto)
    _fill_price(container, values["price"])
    _fill_viewers(container, values["intro_src"], values["viewer_src"], moto)
    _fill_colors(container, values["colors"])
    _fill_key_specs(container, values["specs"])
    _fill_spec_sheet(container, values.get("spec_sheet_url"), moto)
    _fill_specs(container, values["specs"])
    _fill_related(container, values["related"])
    colors = values["colors"]
    page_media = (
        {"images": colors[0]["media_images"], "videos": colors[0]["media_videos"]} if colors else values["media"]
    )
    used = _fill_media(container, page_media, values["description"])
    _fill_gallery(container, page_media["images"][used:], moto)
    _fill_form(container, moto, values["motos"])
    _single_h1(container)
    if not values["has_360"]:
        _drop_360(container)
    if values.get("structured_data"):
        _add_structured_data(container, values["structured_data"])
    if editor_notice is not None:
        wrap = container.get_element_by_id("wrap", None)
        (wrap if wrap is not None else container).insert(0, editor_notice)
    inner = (container.text or "") + "".join(
        html.tostring(child, encoding="unicode", method="html") for child in container
    )
    return page_html[:start] + inner + page_html[end:]
