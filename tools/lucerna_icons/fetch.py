"""O fetch: traz um ícone do Lucide para `svg/outline/` e o registra no manifesto.

    python -m lucerna_icons fetch <nome-no-lucide> [--as <nome>] [--material <ligadura>]...
                                  [--filled own|outline] [--family <família>]

Baixa `icons/<nome>.svg` da tag `lucideVersion` do repositório do Lucide
(raw.githubusercontent.com), normaliza os atributos para o padrão do pacote
(grade de 24, `currentColor`, traço 2, pontas e junções redondas), valida e
grava em `svg/outline/<nome>.svg`. A entrada do manifesto fica `pendente`, com
`origin: "lucide:<nome-no-lucide>"`.

Um ícone já aprovado nunca é sobrescrito. Um pendente é refeito: o SVG é
trocado e a origem atualizada; `material`, `filled` e `family` só mudam se
vierem na chamada.
"""

import http.client
import json
import sys
import os
import re
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from . import manifest, svgcheck

# O padrão: o arquivo cru do repositório do Lucide, na tag fixada.
URL_LUCIDE = "https://raw.githubusercontent.com/lucide-icons/lucide/{tag}/icons/{nome}.svg"
# Troca a URL (útil para um espelho ou para os testes); usa {tag} e {nome}.
VARIAVEL_URL = "LUCERNA_LUCIDE_URL"

SVG_NS = "http://www.w3.org/2000/svg"

# Os atributos do <svg>, como o Lucide publica, na ordem do Lucide.
ATRIBUTOS_RAIZ = {
    "width": "24",
    "height": "24",
    "viewBox": "0 0 24 24",
    "fill": "none",
    "stroke": "currentColor",
    "stroke-width": "2",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
}


class ErroDeFetch(Exception):
    pass


class ErroDeRede(ErroDeFetch):
    """A rede falhou (timeout, conexão, resposta cortada); diferente de um HTTP 404."""


# O tempo de espera do fetch e, mais curto, o da galeria (que não pode travar a geração).
TIMEOUT = 30
TIMEOUT_GALERIA = 5


def _baixar(url: str, timeout: float = TIMEOUT) -> str:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resposta:
            return resposta.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise ErroDeFetch(f"{url}: HTTP {e.code}") from e
    except UnicodeDecodeError as e:
        raise ErroDeFetch(f"{url}: {e}") from e
    except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
        raise ErroDeRede(f"{url}: {e}") from e


def _normalizar_elemento(el, na_mascara: bool):
    local = el.tag.rsplit("}", 1)[-1]
    na_mascara = na_mascara or local == "mask"
    el.attrib.pop("class", None)
    for prop in ("stroke-linecap", "stroke-linejoin"):
        if el.get(prop, "round") != "round":
            del el.attrib[prop]  # herda o round do <svg>
    if not na_mascara:
        for prop in ("fill", "stroke"):
            valor = el.get(prop)
            if valor is not None and valor.strip().lower() not in svgcheck.CORES_LIVRES:
                el.set(prop, "currentColor")
    for filho in el:
        _normalizar_elemento(filho, na_mascara)


def normalizar(texto: str) -> str:
    """O SVG do Lucide no padrão do pacote. Levanta ErroDeFetch se não der."""
    if re.search(r"<!(DOCTYPE|ENTITY)", texto, re.IGNORECASE):
        raise ErroDeFetch("o SVG tem DOCTYPE/ENTITY, recusado")
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError as e:
        raise ErroDeFetch(f"SVG inválido: {e}") from e
    if raiz.tag != f"{{{SVG_NS}}}svg":
        raise ErroDeFetch("a raiz não é um <svg> no namespace do SVG")
    viewbox = re.split(r"[\s,]+", raiz.get("viewBox", "").strip())
    if viewbox != ["0", "0", "24", "24"]:
        raise ErroDeFetch(f'viewBox "{raiz.get("viewBox")}": só a grade de 24 é aceita')

    raiz.attrib.clear()
    raiz.attrib.update(ATRIBUTOS_RAIZ)
    for filho in raiz:
        _normalizar_elemento(filho, False)

    ET.register_namespace("", SVG_NS)
    ET.indent(raiz, "  ")
    return ET.tostring(raiz, encoding="unicode") + "\n"


def caminho_original(raiz: Path, tag: str, nome_lucide: str) -> Path:
    """Onde fica o SVG cru do Lucide, como veio, para a galeria mostrar o original."""
    return Path(raiz) / ".cache" / "lucide" / tag / f"{nome_lucide}.svg"


def guardar_original(raiz: Path, tag: str, nome_lucide: str, texto: str) -> None:
    destino = caminho_original(raiz, tag, nome_lucide)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")


def svg_seguro(texto: str) -> bool:
    """O texto passa no svgcheck? (Ele vai embutido no HTML da galeria.)"""
    with tempfile.TemporaryDirectory(prefix="lucerna-original-") as tmp:
        arquivo = Path(tmp) / "original.svg"
        arquivo.write_text(texto, encoding="utf-8")
        return not svgcheck.validar_svg(arquivo)


def original(
    raiz: Path, tag: str, nome_lucide: str, url: str | None = None, rede: dict | None = None
) -> str | None:
    """O SVG cru do Lucide: do cache e, se faltar, baixado da tag fixada (e guardado).
    None quando não está no cache, não deu para baixar ou o texto não passa no svgcheck.
    `rede` é um estado compartilhado da geração: depois de uma falha de rede (`rede["fora"]`),
    nenhum outro download é tentado."""
    if not manifest.VERSAO.match(tag) or not manifest.ORIGEM_LUCIDE.match(f"lucide:{nome_lucide}"):
        return None
    arquivo = caminho_original(raiz, tag, nome_lucide)
    try:
        texto = arquivo.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        texto = None
    if texto is None:
        if rede is not None and rede.get("fora"):
            return None
        endereco = (url or os.environ.get(VARIAVEL_URL) or URL_LUCIDE).format(tag=tag, nome=nome_lucide)
        try:
            texto = _baixar(endereco, timeout=TIMEOUT_GALERIA)
        except ErroDeFetch as e:
            if isinstance(e, ErroDeRede) and rede is not None:
                rede["fora"] = True
                print(f"aviso: sem rede para baixar os originais do Lucide ({e}); usando o contorno atual", file=sys.stderr)
            return None
        except (OSError, http.client.HTTPException):
            return None
        if not svg_seguro(texto):
            return None
        try:
            guardar_original(raiz, tag, nome_lucide, texto)
        except OSError:
            pass
        return texto
    return texto if svg_seguro(texto) else None


def _escrever_manifesto(raiz: Path, dados: dict):
    texto = json.dumps(dados, indent=2, ensure_ascii=False) + "\n"
    (raiz / "manifest.json").write_text(texto, encoding="utf-8")


def buscar(
    raiz: Path,
    nome_lucide: str,
    como: str | None = None,
    *,
    material: list[str] | None = None,
    filled: str | None = None,
    family: str | None = None,
    url: str | None = None,
) -> Path:
    """Baixa `nome_lucide` e grava como `svg/outline/<como>.svg`. Devolve o caminho."""
    raiz = Path(raiz)
    nome = como or nome_lucide
    if not manifest.ORIGEM_LUCIDE.match(f"lucide:{nome_lucide}"):
        raise ErroDeFetch(f"{nome_lucide!r}: nome do Lucide inválido (kebab-case)")
    if not manifest.NOME.match(nome) or nome.endswith("-fill"):
        raise ErroDeFetch(f"{nome!r}: precisa ser kebab-case e não terminar em -fill")
    if filled is not None and filled not in manifest.FILLED:
        raise ErroDeFetch(f'filled {filled!r}: precisa ser "own" ou "outline"')
    if family is not None and not manifest.NOME.match(family):
        raise ErroDeFetch(f"family {family!r}: precisa ser kebab-case")
    for m in material or []:
        if not manifest.MATERIAL.match(m):
            raise ErroDeFetch(f"{m!r}: não é uma ligadura do Material")

    try:
        dados = manifest.ler(raiz)
    except ValueError as e:
        raise ErroDeFetch(str(e)) from e
    tag = dados.get("lucideVersion")
    if not isinstance(tag, str) or not manifest.VERSAO.match(tag):
        raise ErroDeFetch(f"lucideVersion {tag!r} não é uma tag X.Y.Z: fixe a tag do Lucide no manifesto antes")

    icones = dados.setdefault("icons", [])
    existente = next((e for e in icones if isinstance(e, dict) and e.get("name") == nome), None)
    if existente is not None and existente.get("status") == "aprovado":
        raise ErroDeFetch(f"{nome!r} já está aprovado; o fetch não sobrescreve um ícone aprovado")

    endereco = (url or os.environ.get(VARIAVEL_URL) or URL_LUCIDE).format(tag=tag, nome=nome_lucide)
    cru = _baixar(endereco)
    svg = normalizar(cru)

    destino = manifest.svg_contorno(raiz, nome)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Valida antes de trocar o arquivo: grava ao lado e só então renomeia.
    with tempfile.NamedTemporaryFile("w", suffix=".svg", dir=destino.parent, delete=False, encoding="utf-8") as tmp:
        tmp.write(svg)
    temporario = Path(tmp.name)
    problemas = svgcheck.validar_svg(temporario)
    if problemas:
        temporario.unlink()
        raise ErroDeFetch(f"{nome_lucide}: " + "; ".join(m for _, m in problemas))
    temporario.replace(destino)
    guardar_original(raiz, tag, nome_lucide, cru)

    if existente is None:
        existente = {
            "name": nome,
            "origin": "",
            "material": [],
            "filled": "outline",
            "family": None,
            "status": "pendente",
        }
        icones.append(existente)
    existente["origin"] = f"lucide:{nome_lucide}"
    if material is not None:
        existente["material"] = list(material)
    if filled is not None:
        existente["filled"] = filled
    if family is not None:
        existente["family"] = family
    _escrever_manifesto(raiz, dados)
    return destino
