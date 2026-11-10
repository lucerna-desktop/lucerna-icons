"""A galeria de revisão: uma página HTML estática com os ícones pedidos.

Para cada ícone (e cada estado da família, que vem inteira): o original do
Lucide ao lado, quando derivado; o contorno e o preenchido nos 4 pesos; os
tamanhos do tema (14 a 64) com o peso automático, nos temas escuro e claro; o
bloco ativo e o inativo (como o Tile da central do shell); a animação do
preenchimento; e o Material Symbols que ele substitui, para comparar.

A saída (`--out`) leva o `index.html`, com o CSS, o JS e os SVGs embutidos, e
os 4 TTFs em `fontes/`, referenciados de forma relativa: a pasta abre direto
do disco. Os TTFs vêm de um `build --all` já feito (`--dist`) ou de um build
feito aqui, num diretório temporário.

Ids previsíveis (os testes e o controlador contam com eles):

    ic-<nome>                              o cartão do ícone
    ic-<nome>-lucide                       o original do Lucide (só derivados)
    ic-<nome>-{contorno,preenchido}-<peso> o desenho em cada peso (200…600)
    ic-<nome>-<tema>-<tipo>                a linha de um tipo num tema
    ic-<nome>-<tema>-<tipo>-<tamanho>      a célula de um tamanho
    ic-<nome>-<tema>-bloco-<estado>        os blocos (ativo, inativo,
                                           material-ativo, material-inativo)
    ic-<nome>-<tema>-anima                 a animação do preenchimento
    ic-<nome>-a-desenhar                   o aviso de um ícone ainda sem SVG
    familia-<família>                      a seção de uma família

`<tema>` é `escuro` ou `claro`; `<tipo>` é `contorno`, `preenchido`,
`material` ou `material-fill`. O que ainda não foi desenhado leva a classe
`a-desenhar`.
"""

import html
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import build, manifest

PASTA = Path(__file__).resolve().parent.parent / "gallery"
TAMANHOS = (14, 16, 20, 24, 32, 40, 64)
TRACO = {200: "1", 300: "1,5", 400: "2", 600: "2,5"}
ARQUIVO_PESO = {p.classe: f"LucernaIcons-{p.estilo}.ttf" for p in build.PESOS}
DESENHO_PX = 72  # 3 px por unidade da grade de 24
BLOCO_PX = 20  # o ícone do Tile da central
ANIMA_PX = 40


class ErroDeGaleria(Exception):
    pass


def peso_do_tamanho(px: int) -> int:
    """O peso automático: até 16 → traço 2,5; 17–24 → 2; 25–40 → 1,5; acima → 1."""
    if px <= 16:
        return 600
    if px <= 24:
        return 400
    if px <= 40:
        return 300
    return 200


@dataclass
class Item:
    icone: manifest.Icone
    contorno: Path | None  # None: ainda sem desenho
    preenchido: Path | None  # None: a desenhar (own) ou o próprio contorno (outline)

    @property
    def nome(self) -> str:
        return self.icone.name

    @property
    def preenchido_a_desenhar(self) -> bool:
        return self.icone.filled == "own" and self.preenchido is None


# --- Seleção -------------------------------------------------------------------


def icones_do_lote(raiz: Path, n: int, arquivo: Path | None = None) -> tuple[list[str], dict]:
    """Os nomes do lote `n` de `lotes.json` e a entrada dele."""
    arquivo = Path(arquivo) if arquivo else Path(raiz) / "lotes.json"
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ErroDeGaleria(f"não deu para ler o {arquivo.name}: {e}") from e
    for lote in dados.get("lotes", []) if isinstance(dados, dict) else []:
        if isinstance(lote, dict) and lote.get("n") == n:
            icones = lote.get("icones")
            if not isinstance(icones, list) or not all(isinstance(i, str) for i in icones):
                raise ErroDeGaleria(f"lote {n}: icones precisa ser uma lista de nomes")
            return list(icones), lote
    raise ErroDeGaleria(f"lote {n} não está no {arquivo.name}")


def selecionar(icones: list[manifest.Icone], nomes: list[str]) -> list[manifest.Icone]:
    """Os ícones pedidos, cada um com a família inteira (na ordem do manifesto), sem repetir."""
    por_nome = {ic.name: ic for ic in icones}
    faltam = [n for n in nomes if n not in por_nome]
    if faltam:
        raise ErroDeGaleria("não estão no manifesto: " + ", ".join(dict.fromkeys(faltam)))
    if not nomes:
        raise ErroDeGaleria("nenhum ícone pedido (dê os nomes ou --lote)")
    escolhidos: list[manifest.Icone] = []
    vistos: set[str] = set()
    for n in nomes:
        ic = por_nome[n]
        grupo = [x for x in icones if x.family == ic.family] if ic.family else [ic]
        for x in grupo:
            if x.name not in vistos:
                vistos.add(x.name)
                escolhidos.append(x)
    return escolhidos


# --- Peças do HTML ---------------------------------------------------------------


def _e(texto) -> str:
    return html.escape(str(texto), quote=True)


def _glifo(nome: str, px: int, peso: int, ident: str = "", classe: str = "") -> str:
    ida = f' id="{ident}"' if ident else ""
    classes = f"g {classe}".strip()
    return f'<span{ida} class="{classes}" style="font-size:{px}px;--peso:{peso}">{_e(nome)}</span>'


def _material(lig: str | None, px: int, cheio: bool, ident: str = "") -> str:
    ida = f' id="{ident}"' if ident else ""
    if not lig:
        return f'<span{ida} class="m-nada" title="sem equivalente no Material">—</span>'
    classe = "m cheio" if cheio else "m"
    opsz = max(20, min(48, px))
    return f'<span{ida} class="{classe}" style="font-size:{px}px;--opsz:{opsz}">{_e(lig)}</span>'


def _vazio(ident: str, texto: str = "a desenhar", classe: str = "") -> str:
    return f'<span id="{ident}" class="vazio a-desenhar {classe}">{_e(texto)}</span>'


def _par(item: Item, px: int) -> str:
    """O contorno e o preenchido sobrepostos, para a animação."""
    peso = peso_do_tamanho(px)
    return (
        f'<span class="par" style="font-size:{px}px">'
        f'{_glifo(item.nome, px, peso, classe="cont")}'
        f'{_glifo(item.nome + "-fill", px, peso, classe="fill")}'
        "</span>"
    )


def _cabecalho(item: Item, lucide: str) -> str:
    ic = item.icone
    if ic.origin.startswith("lucide:"):
        orig = ic.origin.removeprefix("lucide:")
        origem = (
            f'Lucide {_e(lucide)} · <a href="https://lucide.dev/icons/{_e(orig)}" '
            f'target="_blank" rel="noopener"><code>{_e(orig)}</code></a>'
        )
    else:
        origem = "original do Lucerna"
    if ic.filled == "outline":
        preench = "o próprio contorno"
    elif item.preenchido is not None:
        preench = "próprio"
    else:
        preench = 'próprio, <span class="falta">a desenhar</span>'
    material = " ".join(f"<code>{_e(m)}</code>" for m in ic.material) or "—"
    linhas = [("Origem", origem), ("Material", material), ("Preenchido", preench)]
    if ic.family:
        linhas.append(("Família", f"<code>{_e(ic.family)}</code>"))
    dl = "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in linhas)
    status = _e(ic.status)
    return (
        '<header class="cab">'
        f'<h3><code>{_e(ic.name)}</code></h3>'
        f'<span class="selo selo-{status}">{status}</span>'
        f"<dl>{dl}</dl>"
        "</header>"
    )


def _desenho(item: Item, lucide: str, svg_original: str | None) -> str:
    n = item.nome
    if item.contorno is None:
        return (
            '<div class="desenho">'
            f'<div id="ic-{n}-a-desenhar" class="aviso a-desenhar">'
            "<strong>A desenhar.</strong> Este ícone ainda não tem SVG"
            + ("; o Lucide não tem um equivalente" if item.icone.origin == "lucerna" else "")
            + ". Abaixo, o Material que ele vai substituir."
            "</div></div>"
        )
    grupos = []
    if svg_original is not None:
        grupos.append(
            '<div class="grupo"><h4>Original</h4><div class="cels">'
            f'<figure class="cel"><div class="quadro orig" id="ic-{n}-lucide">{svg_original}</div>'
            f"<figcaption>Lucide {_e(lucide)}<br><span>traço 2</span></figcaption></figure>"
            "</div></div>"
        )
    for tipo, titulo in (("contorno", "Contorno"), ("preenchido", "Preenchido")):
        cels = []
        for peso in (200, 300, 400, 600):
            ident = f"ic-{n}-{tipo}-{peso}"
            if tipo == "preenchido" and item.preenchido_a_desenhar:
                miolo = _vazio(ident, classe="quadro")
            else:
                lig = n if tipo == "contorno" else n + "-fill"
                miolo = f'<div class="quadro" id="{ident}">{_glifo(lig, DESENHO_PX, peso)}</div>'
            cels.append(
                f'<figure class="cel">{miolo}<figcaption>traço {TRACO[peso]}<br><span>{peso}</span></figcaption></figure>'
            )
        grupos.append(f'<div class="grupo"><h4>{titulo}</h4><div class="cels">{"".join(cels)}</div></div>')
    return f'<div class="desenho">{"".join(grupos)}</div>'


def _tabela(item: Item, tema: str) -> str:
    n = item.nome
    mat = item.icone.material[0] if item.icone.material else None
    cab = "".join(
        f'<th scope="col">{t}<span>traço {TRACO[peso_do_tamanho(t)]}</span></th>' for t in TAMANHOS
    )
    linhas = []

    def linha(tipo: str, rotulo: str, celula, vazio: str | None = None):
        ident = f"ic-{n}-{tema}-{tipo}"
        if vazio:
            corpo = f'<td colspan="{len(TAMANHOS)}" class="a-desenhar"><span class="vazio">{_e(vazio)}</span></td>'
            linhas.append(f'<tr id="{ident}" class="a-desenhar"><th scope="row">{rotulo}</th>{corpo}</tr>')
            return
        corpo = "".join(f"<td>{celula(t, f'{ident}-{t}')}</td>" for t in TAMANHOS)
        linhas.append(f'<tr id="{ident}"><th scope="row">{rotulo}</th>{corpo}</tr>')

    if item.contorno is not None:
        linha("contorno", "Contorno", lambda t, i: _glifo(n, t, peso_do_tamanho(t), i))
        if item.preenchido_a_desenhar:
            linha("preenchido", "Preenchido", None, vazio="preenchido a desenhar")
        else:
            linha("preenchido", "Preenchido", lambda t, i: _glifo(n + "-fill", t, peso_do_tamanho(t), i))
    linha("material", '<span class="rot-m">Material</span>', lambda t, i: _material(mat, t, False, i))
    linha("material-fill", '<span class="rot-m">Material cheio</span>', lambda t, i: _material(mat, t, True, i))
    return f'<table class="tamanhos"><thead><tr><th></th>{cab}</tr></thead><tbody>{"".join(linhas)}</tbody></table>'


def _bloco(ident: str, titulo: str, estado: str, icone: str, ativo: bool, extra: str = "") -> str:
    classe = "bloco ativo" if ativo else "bloco"
    return (
        f'<div id="{ident}" class="{classe}{extra}">'
        f'<span class="circulo">{icone}</span>'
        f'<span class="txt"><b>{_e(titulo)}</b><small>{_e(estado)}</small></span>'
        "</div>"
    )


def _blocos(item: Item, tema: str) -> str:
    n = item.nome
    mat = item.icone.material[0] if item.icone.material else None
    pre = f"ic-{n}-{tema}"
    partes = []
    if item.contorno is not None:
        partes.append(_bloco(f"{pre}-bloco-inativo", n, "Desligado", _par(item, BLOCO_PX), False))
        partes.append(_bloco(f"{pre}-bloco-ativo", n, "Ligado", _par(item, BLOCO_PX), True, " cheio"))
    if mat:
        partes.append(
            _bloco(f"{pre}-bloco-material-inativo", "Material", "Desligado", _material(mat, BLOCO_PX, False), False)
        )
        partes.append(
            _bloco(f"{pre}-bloco-material-ativo", "Material", "Ligado", _material(mat, BLOCO_PX, True), True)
        )
    if not partes:
        return ""
    nota = ""
    if item.contorno is not None and item.preenchido_a_desenhar:
        nota = '<p class="nota">O preenchido ainda não foi desenhado: o ativo mostra o contorno.</p>'
    return f'<div class="blocos">{"".join(partes)}</div>{nota}'


def _anima(item: Item, tema: str) -> str:
    if item.contorno is None:
        return ""
    n = item.nome
    mat = item.icone.material[0] if item.icone.material else None
    m = ""
    if mat:
        m = f'<span class="lado"><span class="m anim" style="font-size:{ANIMA_PX}px;--opsz:40">{_e(mat)}</span><small>Material</small></span>'
    tile = _bloco(f"ic-{n}-{tema}-anima-bloco", n, "Toque para alternar", _par(item, BLOCO_PX), False, " alterna")
    return (
        f'<div id="ic-{n}-{tema}-anima" class="anima" data-alterna>'
        f'<span class="lado"><span class="g-anima">{_par(item, ANIMA_PX)}</span><small>Lucerna</small></span>'
        f"{m}{tile}"
        '<button type="button" class="botao" data-alternar>Preencher</button>'
        "</div>"
    )


def _paineis(item: Item, temas: dict) -> str:
    paineis = []
    for papel, tema in temas.items():
        rotulo = "escuro" if tema["dark"] else "claro"
        paineis.append(
            f'<section class="tema tema-{papel}" aria-label="{_e(tema["nome"])}">'
            f'<h4>{_e(tema["nome"])} <span>{rotulo}</span></h4>'
            f"{_tabela(item, papel)}{_blocos(item, papel)}{_anima(item, papel)}"
            "</section>"
        )
    return f'<div class="temas">{"".join(paineis)}</div>'


def _cartao(item: Item, lucide: str, svg_original: str | None, temas: dict) -> str:
    classe = "icone a-desenhar" if item.contorno is None else "icone"
    return (
        f'<article id="ic-{item.nome}" class="{classe}">'
        f"{_cabecalho(item, lucide)}{_desenho(item, lucide, svg_original)}{_paineis(item, temas)}"
        "</article>"
    )


def _faixa(itens: list[Item], temas: dict) -> str:
    """Os estados da família lado a lado, contorno e preenchido em 24, nos dois temas."""
    paineis = []
    for papel, tema in temas.items():
        colunas = []
        for it in itens:
            if it.contorno is None:
                cel = '<span class="vazio mini">a desenhar</span>'
            else:
                fill = (
                    '<span class="vazio mini">—</span>'
                    if it.preenchido_a_desenhar
                    else _glifo(it.nome + "-fill", 24, peso_do_tamanho(24))
                )
                cel = f"{_glifo(it.nome, 24, peso_do_tamanho(24))}{fill}"
            colunas.append(f'<div class="estado"><div class="pilha">{cel}</div><code>{_e(it.nome)}</code></div>')
        paineis.append(
            f'<div class="tema tema-{papel} faixa"><h4>{_e(tema["nome"])}</h4>'
            f'<div class="estados">{"".join(colunas)}</div></div>'
        )
    return f'<div class="faixas">{"".join(paineis)}</div>'


def _svg_embutido(caminho: Path) -> str:
    texto = caminho.read_text(encoding="utf-8")
    inicio = texto.find("<svg")
    return texto[inicio:].strip() if inicio >= 0 else ""


# --- Página ------------------------------------------------------------------------


def _css_temas(temas: dict) -> str:
    def rgba(h: str, a: float) -> str:
        h = h.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {a})"

    blocos = []
    for papel, tema in temas.items():
        c = tema["cores"]
        props = {
            "--base": c["base"],
            "--surface": c["surface"],
            "--raised": c["raised"],
            "--border": c["border"],
            "--text": c["text"],
            "--text-muted": c["textMuted"],
            "--text-faint": c["textFaint"],
            "--accent": c["accent"],
            "--accent-container": c["accentContainer"],
            "--on-accent-container": c["onAccentContainer"],
            "--accent-icon": c["accentIcon"],
            "--circulo": rgba(c["text"], 0.07),
            "--circulo-ativo": rgba(c["base"], 0.1),
            "--grad": "-25" if tema["dark"] else "0",
        }
        corpo = "; ".join(f"{k}: {v}" for k, v in props.items())
        blocos.append(f".tema-{papel} {{ {corpo}; color-scheme: {'dark' if tema['dark'] else 'light'}; }}")
    return "\n".join(blocos)


def _css_fontes() -> str:
    faces = [
        f'@font-face {{ font-family: "Lucerna Icons"; font-weight: {peso}; font-display: block; '
        f'src: url("fontes/{arq}") format("truetype"); }}'
        for peso, arq in sorted(ARQUIVO_PESO.items())
    ]
    # O Material instalado no sistema primeiro; o do Google Fonts (o <link>) se faltar.
    faces.append(
        '@font-face { font-family: "Material local"; font-display: block; '
        'src: local("Material Symbols Rounded"), local("MaterialSymbolsRounded"); }'
    )
    return "\n".join(faces)


def _cabecalho_pagina(lote: dict | None) -> tuple[str, str]:
    if lote is not None:
        titulo = f"Lote {lote.get('n')}"
        partes = []
        if lote.get("data"):
            partes.append(_e(lote["data"]))
        decisao = lote.get("decisao")
        if decisao is not None:
            if isinstance(decisao, str):
                partes.append(f"decisão: {_e(decisao)}")
            else:
                partes.append(f"decisão: <code>{_e(json.dumps(decisao, ensure_ascii=False))}</code>")
        sub = " · ".join(partes)
    else:
        titulo = "Seleção"
        sub = ""
    return titulo, sub


def _indice(itens: list[Item]) -> str:
    chips = []
    for it in itens:
        classe = "chip"
        if it.contorno is None:
            classe += " chip-vazio"
        classe += f" chip-{_e(it.icone.status)}"
        chips.append(f'<a class="{classe}" href="#ic-{_e(it.nome)}">{_e(it.nome)}</a>')
    return "".join(chips)


def pagina(itens: list[Item], lucide: str, temas_json: dict, lote: dict | None) -> str:
    temas = temas_json["temas"]
    corpo = []
    i = 0
    while i < len(itens):
        fam = itens[i].icone.family
        grupo = [itens[i]]
        while fam and i + len(grupo) < len(itens) and itens[i + len(grupo)].icone.family == fam:
            grupo.append(itens[i + len(grupo)])
        cartoes = "".join(
            _cartao(
                it,
                lucide,
                _svg_embutido(it.contorno) if it.contorno and it.icone.origin.startswith("lucide:") else None,
                temas,
            )
            for it in grupo
        )
        if fam:
            n = len(grupo)
            corpo.append(
                f'<section id="familia-{_e(fam)}" class="familia">'
                f'<header class="cab-familia"><h2>Família <code>{_e(fam)}</code></h2>'
                f"<span>{n} {'estado' if n == 1 else 'estados'}, aprovados juntos</span></header>"
                f"{_faixa(grupo, temas)}{cartoes}</section>"
            )
        else:
            corpo.append(cartoes)
        i += len(grupo)

    titulo, sub = _cabecalho_pagina(lote)
    sem = sum(1 for it in itens if it.contorno is None)
    resumo = f"{len(itens)} ícone{'s' if len(itens) != 1 else ''}"
    if sem:
        resumo += f", {sem} a desenhar"
    legenda = " · ".join(
        f"<span><b>{t}</b> traço {TRACO[peso_do_tamanho(t)]}</span>" for t in TAMANHOS
    )
    fonte_temas = f"cores de {_e(temas_json.get('fonte', ''))} @ {_e(temas_json.get('commit', ''))}"

    modelo = (PASTA / "template.html").read_text(encoding="utf-8")
    trocas = {
        "{{titulo}}": _e(titulo),
        "{{subtitulo}}": sub,
        "{{resumo}}": resumo,
        "{{lucide}}": _e(lucide),
        "{{legenda}}": legenda,
        "{{indice}}": _indice(itens),
        "{{corpo}}": "".join(corpo),
        "{{fonte_temas}}": fonte_temas,
        "{{css}}": _css_fontes() + "\n" + _css_temas(temas) + "\n" + (PASTA / "gallery.css").read_text(encoding="utf-8"),
        "{{js}}": (PASTA / "gallery.js").read_text(encoding="utf-8"),
    }
    for k, v in trocas.items():
        modelo = modelo.replace(k, v)
    return modelo


# --- Geração ------------------------------------------------------------------------


def _copiar_fontes(dist: Path, destino: Path) -> None:
    faltam = [a for a in ARQUIVO_PESO.values() if not (dist / a).exists()]
    if faltam:
        raise ErroDeGaleria(f"faltam os TTFs em {dist}: {', '.join(faltam)} (rode `make build-all`)")
    destino.mkdir(parents=True, exist_ok=True)
    for a in ARQUIVO_PESO.values():
        shutil.copy(dist / a, destino / a)


def gerar(
    raiz: Path,
    nomes: list[str],
    saida: Path,
    dist: Path | None = None,
    lote: int | None = None,
    lotes: Path | None = None,
) -> Path:
    """Gera `saida/index.html` e `saida/fontes/`. Devolve o caminho da página."""
    raiz, saida = Path(raiz), Path(saida)
    dados, icones, erros = manifest.carregar(raiz)
    if erros:
        raise ErroDeGaleria("o manifesto tem erros:\n" + "\n".join(f"  {e}" for e in erros))

    entrada_lote = None
    if lote is not None:
        if nomes:
            raise ErroDeGaleria("dê os nomes ou --lote, não os dois")
        nomes, entrada_lote = icones_do_lote(raiz, lote, lotes)
    escolhidos = selecionar(icones, list(nomes))

    itens = []
    for ic in escolhidos:
        contorno = manifest.svg_contorno(raiz, ic.name)
        preenchido = manifest.svg_preenchido(raiz, ic.name)
        itens.append(
            Item(
                ic,
                contorno if contorno.exists() else None,
                preenchido if ic.filled == "own" and preenchido.exists() else None,
            )
        )

    temas = json.loads((PASTA / "temas.json").read_text(encoding="utf-8"))
    texto = pagina(itens, str(dados.get("lucideVersion", "")), temas, entrada_lote)

    if dist is not None:
        _copiar_fontes(Path(dist), saida / "fontes")
    else:
        with tempfile.TemporaryDirectory(prefix="lucerna-galeria-") as tmp:
            try:
                build.construir(raiz, Path(tmp), todos=True)
            except build.ErroDeBuild as e:
                raise ErroDeGaleria(str(e)) from e
            _copiar_fontes(Path(tmp), saida / "fontes")

    saida.mkdir(parents=True, exist_ok=True)
    destino = saida / "index.html"
    destino.write_text(texto, encoding="utf-8")
    return destino
