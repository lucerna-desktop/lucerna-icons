"""Build da fonte "Lucerna Icons" a partir dos SVGs.

Para cada peso (traço 1 / 1,5 / 2 / 2,5):
1. reescreve o `stroke-width` do SVG na proporção do traço (2 é o do desenho);
2. converte traços e formas em contornos com o picosvg e une tudo com o
   skia-pathops (as máscaras de recorte são aplicadas aqui, ver `_mascaras`);
3. desenha o glifo na grade de 1200 unidades (24 × 50), com o y invertido;
4. monta a fonte: as letras `a–z`, `0–9` e `-` viram glifos vazios de largura
   0, e o GSUB `liga` troca `<nome>` pelo contorno e `<nome>-fill` pelo
   preenchido (ou pelo próprio contorno, com `"filled": "outline"`).

Além dos TTFs, a saída leva os SVGs incluídos (`svg/{outline,filled}`) e o
`manifest.json`, prontos para instalar.
"""

import copy
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import pathops
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from lxml import etree
from picosvg.svg import SVG
from picosvg.svg_pathops import skia_path

from . import manifest

FAMILIA = "Lucerna Icons"
UPM = 1200
ESCALA = UPM / 24
TRACO_BASE = 2.0
VERSAO_FONTE = "1.000"


@dataclass(frozen=True)
class Peso:
    traco: float
    classe: int  # usWeightClass
    estilo: str  # o nome do estilo e o sufixo do arquivo


PESOS = (
    Peso(1.0, 200, "ExtraLight"),
    Peso(1.5, 300, "Light"),
    Peso(2.0, 400, "Regular"),
    Peso(2.5, 600, "SemiBold"),
)

# Os caracteres que formam os nomes, com os nomes de glifo do AGL.
_DIGITOS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
CARACTERES = {c: c for c in "abcdefghijklmnopqrstuvwxyz"}
CARACTERES.update({str(d): n for d, n in enumerate(_DIGITOS)})
CARACTERES["-"] = "hyphen"

SVG_NS = "http://www.w3.org/2000/svg"
_COR_MANTEM = {"white", "#fff", "#ffffff"}
_COR_RECORTA = {"black", "#000", "#000000"}


class ErroDeBuild(Exception):
    pass


def nome_glifo(nome: str, preenchido: bool = False) -> str:
    """O nome do glifo de um ícone. Hífen vira sublinhado (o nome nunca tem `_`)."""
    base = "icon_" + nome.replace("-", "_")
    return base + ".fill" if preenchido else base


# --- SVG → contorno --------------------------------------------------------


def _numero(v: float) -> str:
    return f"{v:g}"


def _reescrever_traco(raiz: etree._Element, traco: float) -> None:
    """Multiplica todo `stroke-width` por traco/2; sem nenhum, o padrão do SVG é 1."""
    fator = traco / TRACO_BASE
    if raiz.get("stroke-width") is None:
        raiz.set("stroke-width", _numero(1.0 * fator))
    for el in raiz.iter():
        if not isinstance(el.tag, str):
            continue
        valor = el.get("stroke-width")
        if valor is not None:
            el.set("stroke-width", _numero(float(valor.strip().removesuffix("px")) * fator))
        estilo = el.get("style")
        if estilo and "stroke-width" in estilo:
            el.set(
                "style",
                re.sub(
                    r"stroke-width\s*:\s*([\d.]+)",
                    lambda m: f"stroke-width:{_numero(float(m.group(1)) * fator)}",
                    estilo,
                ),
            )


def _formas(raiz: etree._Element) -> list[tuple[str, pathops.Path]]:
    """As formas pintadas do SVG, já como contornos: pares (cor, caminho)."""
    texto = etree.tostring(raiz, encoding="unicode")
    pico = SVG.fromstring(texto).topicosvg()
    formas = []
    for forma in pico.shapes():
        caminho = skia_path(forma.as_cmd_seq(), forma.fill_rule)
        formas.append((forma.fill.strip().lower(), caminho))
    return formas


def _uniao(caminhos: list[pathops.Path]) -> pathops.Path:
    resultado = pathops.Path()
    for c in caminhos:
        resultado = pathops.op(resultado, c, pathops.PathOp.UNION, fix_winding=True)
    return resultado


def _so(raiz: etree._Element, filhos: list[etree._Element]) -> etree._Element:
    """Uma cópia do `<svg>` (com os atributos herdáveis) contendo só `filhos`."""
    novo = etree.Element(raiz.tag, attrib=dict(raiz.attrib), nsmap=raiz.nsmap)
    for f in filhos:
        novo.append(f)
    return novo


def _area_da_mascara(raiz: etree._Element, mascara: etree._Element) -> pathops.Path:
    """A área que a máscara deixa ver: o branco soma, o preto tira, na ordem."""
    grupo = etree.Element(f"{{{SVG_NS}}}g")
    for k, v in mascara.attrib.items():
        if k not in {"id", "x", "y", "width", "height", "maskUnits", "maskContentUnits"}:
            grupo.set(k, v)
    for filho in mascara:
        grupo.append(copy.deepcopy(filho))
    area = pathops.Path()
    for cor, caminho in _formas(_so(raiz, [grupo])):
        if cor in _COR_MANTEM:
            area = pathops.op(area, caminho, pathops.PathOp.UNION, fix_winding=True)
        elif cor in _COR_RECORTA:
            area = pathops.op(area, caminho, pathops.PathOp.DIFFERENCE, fix_winding=True)
        else:
            raise ErroDeBuild(f"cor {cor!r} numa máscara (só white e black)")
    return area


def _mascaras(raiz: etree._Element) -> list[pathops.Path]:
    """Tira do SVG os elementos com `mask` e devolve o contorno de cada um, já recortado.

    É a forma de recortar um traço de dentro de um preenchido: o elemento
    pintado leva `mask="url(#id)"`, e a `<mask>` tem um retângulo branco (o que
    fica) e, por cima, os traços pretos (o que sai). Só máscaras por id, em
    coordenadas do usuário.
    """
    mascaras = {m.get("id"): m for m in raiz.iter(f"{{{SVG_NS}}}mask")}
    resultado = []
    for el in list(raiz.iter()):
        ref = el.get("mask") if isinstance(el.tag, str) else None
        if ref is None:
            continue
        m = re.fullmatch(r"\s*url\(\s*#([^)\s]+)\s*\)\s*", ref)
        if not m or m.group(1) not in mascaras:
            raise ErroDeBuild(f"máscara {ref!r} não encontrada")
        area = _area_da_mascara(raiz, mascaras[m.group(1)])

        # O elemento com o que herda dos ancestrais (os grupos no caminho até a raiz).
        alvo = copy.deepcopy(el)
        del alvo.attrib["mask"]
        for ancestral in el.iterancestors():
            if ancestral is raiz:
                break
            envoltorio = etree.Element(ancestral.tag, attrib=dict(ancestral.attrib))
            envoltorio.attrib.pop("mask", None)
            envoltorio.append(alvo)
            alvo = envoltorio
        conteudo = _uniao([c for _, c in _formas(_so(raiz, [alvo]))])
        resultado.append(pathops.op(conteudo, area, pathops.PathOp.INTERSECTION, fix_winding=True))
        el.getparent().remove(el)

    for mascara in mascaras.values():
        mascara.getparent().remove(mascara)
    return resultado


def contorno_svg(caminho: Path, traco: float) -> pathops.Path:
    """O contorno de um SVG de ícone com o traço dado, na grade de 24 (y para baixo)."""
    try:
        raiz = etree.parse(str(caminho), etree.XMLParser(resolve_entities=False, no_network=True)).getroot()
        _reescrever_traco(raiz, traco)
        partes = _mascaras(raiz)
        partes += [c for _, c in _formas(raiz)]
        return _uniao(partes)
    except ErroDeBuild as e:
        raise ErroDeBuild(f"{caminho}: {e}") from e
    except Exception as e:  # picosvg e pathops levantam de tudo
        raise ErroDeBuild(f"{caminho}: não deu para converter ({type(e).__name__}: {e})") from e


def glifo(caminho: pathops.Path):
    """O glifo TrueType: escala 50, y invertido, cúbicas em quadráticas, sentido horário."""
    pen = TTGlyphPen(None)
    # O skia, com fix_winding, deixa o externo no sentido anti-horário em y
    # para baixo; o y invertido o deixa no horário que o TrueType espera.
    quad = Cu2QuPen(pen, max_err=0.5)
    caminho.draw(TransformPen(quad, (ESCALA, 0, 0, -ESCALA, 0, UPM)))
    return pen.glyph()


# --- Fonte ------------------------------------------------------------------


@dataclass
class Entrada:
    """Um ícone incluído no build: os SVGs que existem."""

    icone: manifest.Icone
    contorno: Path
    preenchido: Path | None  # None: o -fill aponta para o contorno


def _entradas(raiz: Path, icones: list[manifest.Icone], todos: bool) -> list[Entrada]:
    entradas = []
    for ic in icones:
        if not (ic.aprovado or todos):
            continue
        contorno = manifest.svg_contorno(raiz, ic.name)
        if not contorno.exists():
            print(f"aviso: {ic.name} sem SVG do contorno, fica de fora", file=sys.stderr)
            continue
        preenchido = None
        if ic.filled == "own":
            preenchido = manifest.svg_preenchido(raiz, ic.name)
            if not preenchido.exists():
                print(f"aviso: {ic.name} sem o preenchido, o -fill mostra o contorno", file=sys.stderr)
                preenchido = None
        entradas.append(Entrada(ic, contorno, preenchido))
    return entradas


def _fea(ligaduras: dict[str, str]) -> str:
    """O GSUB `liga`, das sequências mais longas para as mais curtas."""
    if not ligaduras:
        return ""
    linhas = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "", "feature liga {"]
    for texto in sorted(ligaduras, key=lambda t: (-len(t), t)):
        seq = " ".join(CARACTERES[c] for c in texto)
        linhas.append(f"  sub {seq} by {ligaduras[texto]};")
    linhas.append("} liga;")
    return "\n".join(linhas) + "\n"


def fonte(entradas: list[Entrada], peso: Peso):
    vazio = TTGlyphPen(None).glyph()
    glifos = {".notdef": vazio}
    metricas = {".notdef": (UPM, 0)}
    for g in CARACTERES.values():
        glifos[g] = TTGlyphPen(None).glyph()
        metricas[g] = (0, 0)

    ligaduras = {}
    for e in entradas:
        nome = e.icone.name
        g = nome_glifo(nome)
        glifos[g] = glifo(contorno_svg(e.contorno, peso.traco))
        ligaduras[nome] = g
        if e.preenchido is not None:
            gp = nome_glifo(nome, preenchido=True)
            glifos[gp] = glifo(contorno_svg(e.preenchido, peso.traco))
            ligaduras[f"{nome}-fill"] = gp
        else:
            ligaduras[f"{nome}-fill"] = g
    for g, gl in glifos.items():
        if g not in metricas:
            gl.recalcBounds(None)
            metricas[g] = (UPM, getattr(gl, "xMin", 0))

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(list(glifos))
    fb.setupCharacterMap({ord(c): g for c, g in CARACTERES.items()})
    fb.setupGlyf(glifos)
    fb.setupHorizontalMetrics(metricas)
    fb.setupHorizontalHeader(ascent=UPM, descent=0)
    regular = peso.estilo == "Regular"
    fb.setupNameTable(
        {
            "familyName": FAMILIA if regular else f"{FAMILIA} {peso.estilo}",
            "styleName": "Regular",
            "typographicFamily": FAMILIA,
            "typographicSubfamily": peso.estilo,
            "uniqueFontIdentifier": f"Lucerna:{FAMILIA}-{peso.estilo}:{VERSAO_FONTE}",
            "fullName": f"{FAMILIA} {peso.estilo}",
            "psName": f"LucernaIcons-{peso.estilo}",
            "version": f"Version {VERSAO_FONTE}",
            "copyright": "Copyright (c) 2026 Lucerna. Ícones derivados do Lucide (ISC) e do Feather (MIT).",
            "licenseDescription": "MIT; os derivados do Lucide seguem o LICENSE-LUCIDE.",
        }
    )
    fb.setupOS2(
        version=4,
        usWeightClass=peso.classe,
        sTypoAscender=UPM,
        sTypoDescender=0,
        sTypoLineGap=0,
        usWinAscent=UPM,
        usWinDescent=0,
        fsSelection=(1 << 6) | (1 << 7),  # REGULAR + USE_TYPO_METRICS
        achVendID="LUCE",
    )
    fb.setupPost()
    fea = _fea(ligaduras)
    if fea:
        addOpenTypeFeaturesFromString(fb.font, fea)
    return fb.font


def construir(raiz: Path, saida: Path, todos: bool = False) -> list[Path]:
    """Gera os 4 TTFs, os SVGs e o manifesto em `saida`. Recusa um manifesto com erro."""
    raiz, saida = Path(raiz), Path(saida)
    erros = manifest.validar(raiz)
    if erros:
        raise ErroDeBuild("o check falhou:\n" + "\n".join(f"  {e}" for e in erros))
    _, icones, _ = manifest.carregar(raiz)
    entradas = _entradas(raiz, icones, todos)

    saida.mkdir(parents=True, exist_ok=True)
    arquivos = []
    for peso in PESOS:
        arquivo = saida / f"LucernaIcons-{peso.estilo}.ttf"
        fonte(entradas, peso).save(arquivo)
        arquivos.append(arquivo)

    for tipo in ("outline", "filled"):
        pasta = saida / "svg" / tipo
        shutil.rmtree(pasta, ignore_errors=True)
        pasta.mkdir(parents=True)
    for e in entradas:
        shutil.copy(e.contorno, saida / "svg" / "outline" / e.contorno.name)
        if e.preenchido is not None:
            shutil.copy(e.preenchido, saida / "svg" / "filled" / e.preenchido.name)
    shutil.copy(raiz / "manifest.json", saida / "manifest.json")
    return arquivos
