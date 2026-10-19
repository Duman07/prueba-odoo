"""Llena la página maestra (diseñada en el editor del sitio) con los datos de una moto.

Los datos se colocan en los bloques que ya usa el diseño, sin marcas especiales:
- «Moto 3D» (.s_moto_3d): foto, nombre en el <h1> y categoría en el texto que lo precede.
- Cualquier texto igual al título original del diseño: nombre de la moto.
- «Visor 360°» (.s_moto_360): modelo .glb y una muestra por color, copiando la primera muestra del diseño;
  sin modelo, cada color muestra la foto de su variante (también en «Moto 3D»).
- Tarjetas de especificaciones (.s_card): una por especificación, copiando la primera tarjeta del diseño.
- Campo «Modelo» del formulario: lista de motos, con la actual elegida.
- Enlaces a la página maestra: pasan a la página de la moto.
"""
import copy
import re

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


def _fill_colors(wrap, colors, model_url, image_url):
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
            if model_url:
                # Con modelo 3D: si el .glb tiene una variante de material con el nombre del color, el visor la aplica.
                swatch.set("data-variant", color["name"])
            elif color["image_url"] or image_url:
                # Sin modelo 3D: al elegir el color se muestra la foto de esa variante (o la del producto si no tiene).
                swatch.set("data-model-src", color["image_url"] or image_url)
            swatch.set("data-attribute-value-ids", color["attribute_value_ids"])
            container.append(swatch)
        panel = container.getparent()
        if not colors and panel.getparent() is not None:
            # Moto sin variantes de color: no se muestra el panel «Colores».
            panel.getparent().remove(panel)
            continue
        for name in _find(panel, "s_moto_360_color_name"):
            _set_text(name, colors[0]["name"])


def _spec_targets(card):
    """En la tarjeta del diseño (<strong>Motor </strong><strong>160 cc 4V</strong>): nombre y valor."""
    strongs = [s for s in card.iter("strong") if s.text_content().strip() and not s.xpath("ancestor::figure")]
    if len(strongs) >= 2:
        return strongs[0], strongs[-1]
    titles = card.xpath(".//*[contains(@class, 'card-title')]")
    return (titles[0], None) if titles else (None, None)


def _fill_specs(wrap, specs):
    lists = _find(wrap, "s_product_list")
    cards = [card for block in lists for card in _find(block, "s_card")] or _find(wrap, "s_card")
    if not cards:
        return
    # Tarjeta modelo: la primera con nombre y valor (en el diseño, «Motor 160 cc 4V»).
    prototype_card = next((card for card in cards if _spec_targets(card)[1] is not None), cards[0])
    column = prototype_card.getparent()
    row = column.getparent()
    section = next(iter(row.iterancestors("section")), None)
    columns = [card.getparent() for card in cards if card.getparent().getparent() is row]
    position = row.index(columns[0])
    tail = columns[-1].tail
    prototype = copy.deepcopy(column)
    for old in columns:
        row.remove(old)
    if not specs:
        if section is not None and section.getparent() is not None:
            section.getparent().remove(section)
        return
    for offset, spec in enumerate(specs):
        new_column = copy.deepcopy(prototype)
        new_column.tail = tail
        card = _find(new_column, "s_card")[0] if _find(new_column, "s_card") else new_column
        figure = next(iter(card.iter("figure")), None)
        if figure is not None:
            image = next(iter(figure.iter("img")), None)
            if spec["image_url"] and image is not None:
                for attribute in list(image.attrib):
                    if attribute.startswith("data-"):
                        del image.attrib[attribute]
                image.set("src", spec["image_url"])
                image.set("alt", spec["name"])
                for link in figure.iter("a"):
                    link.attrib.pop("href", None)
            else:
                figure.getparent().remove(figure)
        name_el, value_el = _spec_targets(card)
        if value_el is not None:
            _set_text(name_el, f"{spec['name']} ")
            _set_text(value_el, spec["value"])
        elif name_el is not None:
            _set_text(name_el, f"{spec['name']}: {spec['value']}")
        row.insert(position + offset, new_column)


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


def _fill_links(wrap, master_url, moto_url):
    """Los botones del diseño apuntan a /hunk-160r-4v#…: en cada moto, a su propia página."""
    if not master_url:
        return
    for link in wrap.iter("a"):
        href = link.get("href") or ""
        path, _sep, fragment = href.partition("#")
        if path.rstrip("/").lower() == master_url.rstrip("/").lower():
            link.set("href", f"#{fragment}" if fragment else moto_url)


def fill_moto_page(page_html, moto, values, master_url, editor_notice=None):
    """Devuelve el HTML de la página con los datos de la moto en el contenido principal (<main>)."""
    start = page_html.find("<main>")
    end = page_html.rfind("</main>")
    if start < 0 or end < 0:
        return page_html
    start += len("<main>")
    container = html.fragment_fromstring(page_html[start:end], create_parent="div")
    _fill_title(container, moto)
    _fill_viewers(container, values["intro_src"], values["viewer_src"], moto)
    _fill_colors(container, values["colors"], values["model_url"], values["image_url"])
    _fill_specs(container, values["specs"])
    _fill_form(container, moto, values["motos"])
    _fill_links(container, master_url, moto._moto_url())
    if editor_notice is not None:
        wrap = container.get_element_by_id("wrap", None)
        (wrap if wrap is not None else container).insert(0, editor_notice)
    inner = (container.text or "") + "".join(
        html.tostring(child, encoding="unicode", method="html") for child in container
    )
    return page_html[:start] + inner + page_html[end:]
