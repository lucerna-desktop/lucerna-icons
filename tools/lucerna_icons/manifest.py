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
          "layer": "battery-fill-1",     # opcional: o glifo da camada de cima,
                                         # da mesma família (a bateria baixa)
          "background": "wifi-3",        # opcional: o glifo de fundo, desenhado
                                         # apagado por baixo (o sinal que falta)
          "minSize": 18                  # opcional: o menor tamanho (px) em que
                                         # precisa funcionar; sem ele, 14
        }
      ]
    }

`layer` diz que o ícone é a camada de baixo de um ícone em duas camadas: o
shell sobrepõe o glifo `layer`, em outra cor, a ele. A camada precisa existir no
manifesto, ser da mesma família e não ser o próprio ícone.

`background` diz que o ícone é um nível desenhado sobre um fundo apagado: o
shell desenha o glifo `background` por baixo, na cor do ícone com a opacidade
`OPACIDADE_FUNDO`, e o ícone por cima, na cor cheia (o Wi-Fi com os arcos que
faltam apagados, como no Android). O fundo precisa existir no manifesto, ser da
mesma família e não ser o próprio ícone, e precisa cobrir o glifo: o desenho do
nível é um subconjunto do desenho do fundo, nos 4 pesos (`fundo-nao-cobre`).

`minSize` é o menor tamanho, em px, em que o ícone precisa funcionar no shell
(sem o campo, vale `MIN_SIZE_PADRAO`, o menor token de tamanho). A família tem
um valor só: todos os estados declaram o mesmo.

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
OPCIONAIS = {"layer", "background", "minSize"}
MIN_SIZE_PADRAO = 14
# A opacidade do fundo (`background`) sobre a cor do ícone; o shell usa a mesma.
OPACIDADE_FUNDO = 0.3
# A área (em unidades² da grade de 24) que o nível pode ter fora do fundo: só o
# ruído da conversão do traço em contorno.
FOLGA_FUNDO = 0.01
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
    min_size: int = MIN_SIZE_PADRAO
    background: str | None = None

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

    fundo = e.get("background")
    if "background" in e and not (isinstance(fundo, str) and NOME.match(fundo)):
        erros.append(Erro("fundo-invalido", rotulo, f"background {fundo!r}: precisa ser o nome de um ícone"))
        ok = False

    minimo = e.get("minSize", MIN_SIZE_PADRAO)
    if not (isinstance(minimo, int) and not isinstance(minimo, bool) and 8 <= minimo <= 128):
        erros.append(Erro("min-size-invalido", rotulo, f"minSize {minimo!r}: precisa ser um inteiro de 8 a 128 (px)"))
        ok = False

    if not ok:
        return None
    return Icone(nome, origem, tuple(material), e["filled"], familia, e["status"], camada, minimo, fundo)


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

    minimos: dict[str, set[int]] = {}
    for ic in icones:
        if ic.family:
            minimos.setdefault(ic.family, set()).add(ic.min_size)
    for fam, valores in sorted(minimos.items()):
        if len(valores) > 1:
            erros.append(
                Erro("familia-min-size-misto", fam, f"os estados declaram minSize diferentes: {sorted(valores)}")
            )

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

    for ic in icones:
        if ic.background is None:
            continue
        alvo = por_nome.get(ic.background)
        if ic.background == ic.name:
            erros.append(Erro("fundo-invalido", ic.name, "background não pode ser o próprio ícone"))
        elif alvo is None:
            erros.append(Erro("fundo-invalido", ic.name, f"background {ic.background!r} não está no manifesto"))
        elif not ic.family or alvo.family != ic.family:
            erros.append(
                Erro("fundo-invalido", ic.name, f"background {ic.background!r} precisa ser da mesma família ({ic.family!r})")
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

    erros += _fundos_cobrem(raiz, icones, erros)

    nomes = {ic.name for ic in icones}
    for tipo in ("outline", "filled"):
        for svg in sorted((raiz / "svg" / tipo).glob("*.svg")):
            if svg.stem not in nomes:
                erros.append(Erro("svg-orfao", svg.stem, f"{svg.relative_to(raiz)} não está no manifesto"))

    return erros


def _fundos_cobrem(raiz: Path, icones: list[Icone], erros: list[Erro]) -> list[Erro]:
    """O desenho de cada nível com `background` fica dentro do desenho do fundo, nos 4 pesos."""
    import pathops

    from . import build

    invalidos = {e.icone for e in erros if e.codigo == "fundo-invalido"}
    com_svg_ruim = {e.icone for e in erros if e.codigo.startswith("svg-")}
    novos = []
    for ic in icones:
        if ic.background is None or ic.name in invalidos or {ic.name, ic.background} & com_svg_ruim:
            continue
        nivel, fundo = svg_contorno(raiz, ic.name), svg_contorno(raiz, ic.background)
        if not (nivel.exists() and fundo.exists()):
            continue
        for peso in build.PESOS:
            try:
                fora = pathops.op(
                    build.contorno_svg(nivel, peso.traco),
                    build.contorno_svg(fundo, peso.traco),
                    pathops.PathOp.DIFFERENCE,
                    fix_winding=True,
                )
            except build.ErroDeBuild as e:
                novos.append(Erro("fundo-nao-cobre", ic.name, f"não deu para comparar com o fundo: {e}"))
                break
            area = abs(fora.area)
            if area > FOLGA_FUNDO:
                novos.append(
                    Erro(
                        "fundo-nao-cobre",
                        ic.name,
                        f"no traço {peso.traco:g}, {area:.3f} unidades² do desenho ficam fora de {ic.background!r}",
                    )
                )
                break
    return novos
