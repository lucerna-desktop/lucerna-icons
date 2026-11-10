"""O manifesto (`manifest.json`): leitura e validação, junto com os SVGs.

Esquema:

    {
      "lucideVersion": "<tag do Lucide de onde vêm os derivados>",
      "icons": [
        {
          "name": "wifi-2",              # kebab-case; a ligadura do contorno
          "origin": "lucide:wifi",       # ou "lucerna", para os originais
          "material": ["network_wifi_2_bar"],  # as ligaduras do Material que substitui
          "filled": "own",               # "own": tem svg/filled/<name>.svg;
                                         # "outline": o -fill usa o contorno
          "family": "wifi",              # os estados de uma família, ou null
          "status": "aprovado",          # ou "pendente"
          "layer": "battery-bolt"        # opcional: o glifo da camada de cima,
                                         # da mesma família (as cargas da bateria)
        }
      ]
    }

`layer` diz que o ícone é a camada de baixo de um ícone em duas camadas: o
shell sobrepõe o glifo `layer` (outra cor) a ele. A camada precisa existir no
manifesto, ser da mesma família e não ser o próprio ícone.

`lucideVersion` pode ficar como um texto qualquer (ex.: "pendente") enquanto
nenhum ícone vier do Lucide; com um derivado, precisa ser uma tag `X.Y.Z`.

Os SVGs só são exigidos dos ícones aprovados; os de um pendente, quando
existem, também são validados.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import svgcheck

CAMPOS = {"name", "origin", "material", "filled", "family", "status"}
OPCIONAIS = {"layer"}
NOME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ORIGEM_LUCIDE = re.compile(r"^lucide:[a-z0-9]+(-[a-z0-9]+)*$")
MATERIAL = re.compile(r"^[a-z0-9_]+$")
VERSAO = re.compile(r"^\d+\.\d+\.\d+$")
FILLED = {"own", "outline"}
STATUS = {"pendente", "aprovado"}


@dataclass(frozen=True)
class Erro:
    codigo: str
    icone: str | None
    mensagem: str

    def __str__(self):
        onde = f" [{self.icone}]" if self.icone else ""
        return f"{self.codigo}{onde}: {self.mensagem}"


@dataclass(frozen=True)
class Icone:
    name: str
    origin: str
    material: tuple[str, ...]
    filled: str
    family: str | None
    status: str
    layer: str | None = None

    @property
    def aprovado(self) -> bool:
        return self.status == "aprovado"


def svg_contorno(raiz: Path, nome: str) -> Path:
    return raiz / "svg" / "outline" / f"{nome}.svg"


def svg_preenchido(raiz: Path, nome: str) -> Path:
    return raiz / "svg" / "filled" / f"{nome}.svg"


def ler(raiz: Path) -> dict:
    """O JSON do manifesto. Levanta ValueError se não der para ler."""
    try:
        return json.loads((raiz / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"não deu para ler o manifest.json: {e}") from e


def _validar_entrada(i: int, e, erros: list[Erro]) -> Icone | None:
    if not isinstance(e, dict):
        erros.append(Erro("campo-invalido", None, f"a entrada {i} não é um objeto"))
        return None
    nome = e.get("name")
    rotulo = nome if isinstance(nome, str) and nome else f"#{i}"
    ok = True

    faltam, sobram = CAMPOS - e.keys(), e.keys() - CAMPOS - OPCIONAIS
    if faltam or sobram:
        partes = []
        if faltam:
            partes.append("faltam " + ", ".join(sorted(faltam)))
        if sobram:
            partes.append("sobram " + ", ".join(sorted(sobram)))
        erros.append(Erro("campo-invalido", rotulo, "; ".join(partes)))
        ok = False

    if not isinstance(nome, str) or not NOME.match(nome) or nome.endswith("-fill"):
        erros.append(
            Erro("nome-invalido", rotulo, f"{nome!r}: precisa ser kebab-case e não terminar em -fill")
        )
        ok = False

    origem = e.get("origin")
    if "origin" in e and not (origem == "lucerna" or (isinstance(origem, str) and ORIGEM_LUCIDE.match(origem))):
        erros.append(Erro("origem-invalida", rotulo, f'{origem!r}: precisa ser "lucerna" ou "lucide:<nome>"'))
        ok = False

    material = e.get("material")
    if "material" in e and not (
        isinstance(material, list) and all(isinstance(m, str) and MATERIAL.match(m) for m in material)
    ):
        erros.append(Erro("campo-invalido", rotulo, "material precisa ser uma lista de ligaduras do Material"))
        ok = False

    if "filled" in e and e["filled"] not in FILLED:
        erros.append(Erro("campo-invalido", rotulo, f'filled {e["filled"]!r}: precisa ser "own" ou "outline"'))
        ok = False

    familia = e.get("family")
    if "family" in e and familia is not None and not (isinstance(familia, str) and NOME.match(familia)):
        erros.append(Erro("campo-invalido", rotulo, f"family {familia!r}: precisa ser kebab-case ou null"))
        ok = False

    if "status" in e and e["status"] not in STATUS:
        erros.append(Erro("campo-invalido", rotulo, f'status {e["status"]!r}: precisa ser "pendente" ou "aprovado"'))
        ok = False

    camada = e.get("layer")
    if "layer" in e and not (isinstance(camada, str) and NOME.match(camada)):
        erros.append(Erro("camada-invalida", rotulo, f"layer {camada!r}: precisa ser o nome de um ícone"))
        ok = False

    if not ok:
        return None
    return Icone(nome, origem, tuple(material), e["filled"], familia, e["status"], camada)


def carregar(raiz: Path) -> tuple[dict, list[Icone], list[Erro]]:
    """O JSON, os ícones válidos e os erros do manifesto (sem olhar os SVGs)."""
    erros: list[Erro] = []
    try:
        dados = ler(raiz)
    except ValueError as e:
        return {}, [], [Erro("manifesto-invalido", None, str(e))]
    if not isinstance(dados, dict):
        return {}, [], [Erro("manifesto-invalido", None, "a raiz do manifesto não é um objeto")]

    if dados.keys() != {"lucideVersion", "icons"}:
        erros.append(Erro("manifesto-invalido", None, 'as chaves precisam ser só "lucideVersion" e "icons"'))
    versao = dados.get("lucideVersion")
    if not isinstance(versao, str) or not versao:
        erros.append(Erro("manifesto-invalido", None, "lucideVersion precisa ser um texto"))
    entradas = dados.get("icons")
    if not isinstance(entradas, list):
        erros.append(Erro("manifesto-invalido", None, "icons precisa ser uma lista"))
        entradas = []

    icones = [ic for i, e in enumerate(entradas) if (ic := _validar_entrada(i, e, erros))]

    vistos: set[str] = set()
    for ic in icones:
        if ic.name in vistos:
            erros.append(Erro("nome-duplicado", ic.name, "o nome aparece mais de uma vez"))
        vistos.add(ic.name)

    material: dict[str, str] = {}
    for ic in icones:
        for m in ic.material:
            if m in material:
                erros.append(Erro("material-duplicado", ic.name, f"{m!r} já é substituído por {material[m]!r}"))
            material.setdefault(m, ic.name)

    familias: dict[str, set[str]] = {}
    for ic in icones:
        if ic.family:
            familias.setdefault(ic.family, set()).add(ic.status)
    for fam, status in sorted(familias.items()):
        if len(status) > 1:
            erros.append(Erro("familia-status-misto", fam, "a família é aprovada junta; os status estão misturados"))

    por_nome = {ic.name: ic for ic in icones}
    for ic in icones:
        if ic.layer is None:
            continue
        alvo = por_nome.get(ic.layer)
        if ic.layer == ic.name:
            erros.append(Erro("camada-invalida", ic.name, "layer não pode ser o próprio ícone"))
        elif alvo is None:
            erros.append(Erro("camada-invalida", ic.name, f"layer {ic.layer!r} não está no manifesto"))
        elif not ic.family or alvo.family != ic.family:
            erros.append(
                Erro("camada-invalida", ic.name, f"layer {ic.layer!r} precisa ser da mesma família ({ic.family!r})")
            )

    derivados = [ic.name for ic in icones if ic.origin.startswith("lucide:")]
    if derivados and isinstance(versao, str) and not VERSAO.match(versao):
        erros.append(
            Erro("lucide-versao", None, f"há ícones do Lucide, e lucideVersion {versao!r} não é uma tag X.Y.Z")
        )

    return dados, icones, erros


def validar(raiz: Path) -> list[Erro]:
    """Todos os erros do manifesto e dos SVGs. Vazio quando está tudo certo."""
    raiz = Path(raiz)
    _, icones, erros = carregar(raiz)
    if any(e.codigo == "manifesto-invalido" for e in erros) and not icones:
        return erros

    for ic in icones:
        contorno, preenchido = svg_contorno(raiz, ic.name), svg_preenchido(raiz, ic.name)
        if not contorno.exists():
            if ic.aprovado:
                erros.append(Erro("svg-ausente", ic.name, f"falta {contorno.relative_to(raiz)}"))
        else:
            erros += [Erro(c, ic.name, f"{contorno.relative_to(raiz)}: {m}") for c, m in svgcheck.validar_svg(contorno)]
        if ic.filled == "own":
            if not preenchido.exists():
                if ic.aprovado:
                    erros.append(Erro("preenchido-ausente", ic.name, f"falta {preenchido.relative_to(raiz)}"))
            else:
                erros += [
                    Erro(c, ic.name, f"{preenchido.relative_to(raiz)}: {m}")
                    for c, m in svgcheck.validar_svg(preenchido)
                ]
        elif preenchido.exists():
            erros.append(
                Erro("preenchido-sobrando", ic.name, f'filled é "outline", mas existe {preenchido.relative_to(raiz)}')
            )

    nomes = {ic.name for ic in icones}
    for tipo in ("outline", "filled"):
        for svg in sorted((raiz / "svg" / tipo).glob("*.svg")):
            if svg.stem not in nomes:
                erros.append(Erro("svg-orfao", svg.stem, f"{svg.relative_to(raiz)} não está no manifesto"))

    return erros
