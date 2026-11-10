"""Validação de um SVG de ícone: grade de 24, sem cor fixa, pontas redondas.

As regras:
- o `<svg>` tem `viewBox="0 0 24 24"` e, se tiver `width`/`height`, são 24;
- `fill` e `stroke` (atributo ou `style`) só valem `none` ou `currentColor`,
  para o ícone herdar a cor de quem o usa. A exceção é o conteúdo de `<mask>`:
  lá só `white` (mantém) e `black` (recorta), que é como se recorta um traço
  de dentro de um preenchido;
- `stroke-linecap` e `stroke-linejoin` são `round` no `<svg>` e nenhum
  elemento troca por outro valor;
- nada de texto, imagem, gradiente, filtro, script nem `<style>`;
- nenhum atributo de evento (`on*`) nem `href`/`xlink:href`: o SVG é só desenho.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "{http://www.w3.org/2000/svg}"

CORES_LIVRES = {"none", "currentcolor"}
CORES_MASCARA = {"none", "white", "#fff", "#ffffff", "black", "#000", "#000000"}
PROIBIDOS = {
    "text", "tspan", "textPath", "image", "style", "script", "foreignObject",
    "linearGradient", "radialGradient", "pattern", "filter", "use", "symbol",
}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _estilo(el) -> dict:
    """As propriedades do atributo `style`, mais os atributos de apresentação."""
    props = {}
    for decl in el.get("style", "").split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            props[k.strip()] = v.strip()
    for k in ("fill", "stroke", "stroke-linecap", "stroke-linejoin"):
        if k in el.attrib:
            props.setdefault(k, el.get(k).strip())
    return props


def validar_svg(caminho: Path) -> list[tuple[str, str]]:
    """Os problemas do SVG, como pares (código, mensagem). Vazio quando está ok."""
    try:
        raiz = ET.parse(caminho).getroot()
    except (ET.ParseError, OSError) as e:
        return [("svg-invalido", f"não deu para ler o SVG: {e}")]
    if raiz.tag != SVG_NS + "svg":
        return [("svg-invalido", "a raiz não é um <svg> no namespace do SVG")]

    erros = []
    viewbox = re.split(r"[\s,]+", raiz.get("viewBox", "").strip())
    try:
        ok = [float(v) for v in viewbox] == [0, 0, 24, 24]
    except ValueError:
        ok = False
    if not ok:
        erros.append(("svg-viewbox", f'viewBox é "{raiz.get("viewBox")}", deveria ser "0 0 24 24"'))
    for dim in ("width", "height"):
        valor = raiz.get(dim)
        if valor is not None and valor.strip().removesuffix("px") != "24":
            erros.append(("svg-viewbox", f'{dim}="{valor}", deveria ser 24 ou ausente'))

    estilo_raiz = _estilo(raiz)
    for prop in ("stroke-linecap", "stroke-linejoin"):
        if estilo_raiz.get(prop) != "round":
            erros.append(("svg-ponta", f'o <svg> precisa de {prop}="round"'))

    def visitar(el, na_mascara):
        nome = _local(el.tag)
        if nome in PROIBIDOS:
            erros.append(("svg-elemento", f"<{nome}> não é permitido"))
        for atributo in el.attrib:
            local = _local(atributo).lower()
            if local.startswith("on"):
                erros.append(("svg-evento", f'<{nome}> tem o atributo de evento "{_local(atributo)}"'))
            elif local == "href":
                erros.append(("svg-href", f'<{nome}> tem o atributo "{_local(atributo)}" (href não é permitido)'))
        na_mascara = na_mascara or nome == "mask"
        props = _estilo(el)
        for prop in ("fill", "stroke"):
            if prop not in props:
                continue
            valor = props[prop].lower()
            permitidas = CORES_MASCARA if na_mascara and nome != "mask" else CORES_LIVRES
            if valor not in permitidas:
                onde = "na máscara (só white/black)" if na_mascara else "(só none/currentColor)"
                erros.append(("svg-cor-fixa", f'<{nome}> tem {prop}="{props[prop]}" {onde}'))
        if el is not raiz:
            for prop in ("stroke-linecap", "stroke-linejoin"):
                if prop in props and props[prop] != "round":
                    erros.append(("svg-ponta", f'<{nome}> tem {prop}="{props[prop]}"'))
        for filho in el:
            visitar(filho, na_mascara)

    visitar(raiz, False)
    return erros
