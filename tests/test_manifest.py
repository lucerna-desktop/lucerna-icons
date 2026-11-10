"""O check: valida o manifesto e os SVGs, e cada problema vira um erro com código."""

from pathlib import Path

import pytest

from conftest import FIXTURES, SVG_OK, icone
from lucerna_icons import manifest

RAIZ = Path(__file__).resolve().parent.parent


def codigos(raiz):
    return {e.codigo for e in manifest.validar(raiz)}


def test_o_manifesto_do_repositorio_passa():
    assert manifest.validar(RAIZ) == []


def test_as_fixtures_passam(repo_fixtures):
    assert manifest.validar(repo_fixtures.raiz) == []


def test_manifesto_ausente(repo):
    assert "manifesto-invalido" in codigos(repo.raiz)


def test_manifesto_com_json_quebrado(repo):
    (repo.raiz / "manifest.json").write_text("{")
    assert "manifesto-invalido" in codigos(repo.raiz)


def test_sem_lucide_version(repo):
    (repo.raiz / "manifest.json").write_text('{"icons": []}')
    assert "manifesto-invalido" in codigos(repo.raiz)


def test_icone_derivado_exige_lucide_version_real(repo):
    repo.svg("outline", "seta")
    repo.manifesto([icone("seta", origin="lucide:arrow-right")], lucide_version="pendente")
    assert "lucide-versao" in codigos(repo.raiz)


def test_campo_faltando_ou_sobrando(repo):
    repo.svg("outline", "a")
    repo.svg("outline", "b")
    sem_status = icone("a")
    del sem_status["status"]
    repo.manifesto([sem_status, icone("b", extra=1)])
    erros = [e for e in manifest.validar(repo.raiz) if e.codigo == "campo-invalido"]
    assert {e.icone for e in erros} == {"a", "b"}


def test_nome_duplicado(repo):
    repo.svg("outline", "seta")
    repo.manifesto([icone("seta"), icone("seta")])
    assert "nome-duplicado" in codigos(repo.raiz)


@pytest.mark.parametrize("nome", ["Seta", "seta_x", "-seta", "seta-", "seta--x", "seta-fill", ""])
def test_nome_invalido(repo, nome):
    repo.manifesto([icone(nome, status="pendente")])
    assert "nome-invalido" in codigos(repo.raiz)


@pytest.mark.parametrize("origem", ["lucide", "lucide:", "lucide:Arrow", "feather:x", "", None])
def test_origin_invalido(repo, origem):
    repo.svg("outline", "seta")
    repo.manifesto([icone("seta", origin=origem)], lucide_version="0.460.0")
    assert "origem-invalida" in codigos(repo.raiz)


def test_material_duplicado(repo):
    repo.svg("outline", "a")
    repo.svg("outline", "b")
    repo.manifesto([icone("a", material=["close"]), icone("b", material=["close"])])
    assert "material-duplicado" in codigos(repo.raiz)


def test_familia_com_status_misto(repo):
    repo.svg("outline", "wifi-1")
    repo.manifesto(
        [icone("wifi-1", family="wifi"), icone("wifi-2", family="wifi", status="pendente")]
    )
    assert "familia-status-misto" in codigos(repo.raiz)


def test_falta_o_svg_do_contorno_aprovado(repo):
    repo.manifesto([icone("seta")])
    erros = manifest.validar(repo.raiz)
    assert [(e.codigo, e.icone) for e in erros] == [("svg-ausente", "seta")]


def test_pendente_sem_svg_passa(repo):
    repo.manifesto([icone("seta", status="pendente", filled="own")])
    assert manifest.validar(repo.raiz) == []


def test_pendente_com_svg_ruim_e_validado(repo):
    repo.svg("outline", "seta", SVG_OK.replace("currentColor", "#000"))
    repo.manifesto([icone("seta", status="pendente")])
    assert "svg-cor-fixa" in codigos(repo.raiz)


def test_falta_o_preenchido_com_filled_own(repo):
    repo.svg("outline", "sino")
    repo.manifesto([icone("sino", filled="own")])
    assert "preenchido-ausente" in codigos(repo.raiz)


def test_preenchido_sobrando_com_filled_outline(repo):
    repo.svg("outline", "x")
    repo.svg("filled", "x")
    repo.manifesto([icone("x", filled="outline")])
    assert "preenchido-sobrando" in codigos(repo.raiz)


def test_filled_invalido(repo):
    repo.svg("outline", "x")
    repo.manifesto([icone("x", filled="sim")])
    assert "campo-invalido" in codigos(repo.raiz)


def test_svg_orfao(repo):
    repo.svg("outline", "solto")
    repo.manifesto([])
    assert "svg-orfao" in codigos(repo.raiz)


@pytest.mark.parametrize(
    "troca",
    [
        ('stroke="currentColor"', 'stroke="#000"'),
        ('stroke="currentColor"', 'stroke="black"'),
        ('fill="none"', 'fill="red"'),
        ('fill="none"', 'style="fill: rgb(0,0,0)"'),
        ('<path d="M5 12h14"/>', '<path d="M5 12h14" stroke="#fff"/>'),
    ],
)
def test_svg_com_cor_fixa(repo, troca):
    repo.svg("outline", "x", SVG_OK.replace(*troca))
    repo.manifesto([icone("x")])
    assert "svg-cor-fixa" in codigos(repo.raiz)


@pytest.mark.parametrize(
    "troca",
    [
        ('viewBox="0 0 24 24"', 'viewBox="0 0 48 48"'),
        ('viewBox="0 0 24 24" ', ""),
        ('width="24"', 'width="48"'),
    ],
)
def test_svg_fora_da_grade_de_24(repo, troca):
    repo.svg("outline", "x", SVG_OK.replace(*troca))
    repo.manifesto([icone("x")])
    assert "svg-viewbox" in codigos(repo.raiz)


@pytest.mark.parametrize(
    "troca",
    [
        ('stroke-linecap="round"', 'stroke-linecap="butt"'),
        (' stroke-linejoin="round"', ""),
        ('<path d="M5 12h14"/>', '<path d="M5 12h14" stroke-linejoin="miter"/>'),
    ],
)
def test_svg_sem_pontas_redondas(repo, troca):
    repo.svg("outline", "x", SVG_OK.replace(*troca))
    repo.manifesto([icone("x")])
    assert "svg-ponta" in codigos(repo.raiz)


def test_svg_com_elemento_proibido(repo):
    repo.svg("outline", "x", SVG_OK.replace("</svg>", '<text x="1" y="1">a</text></svg>'))
    repo.manifesto([icone("x")])
    assert "svg-elemento" in codigos(repo.raiz)


def test_svg_que_nao_e_xml(repo):
    repo.svg("outline", "x", "<svg")
    repo.manifesto([icone("x")])
    assert "svg-invalido" in codigos(repo.raiz)


def test_mascara_so_aceita_branco_e_preto(repo):
    texto = (FIXTURES / "svg" / "filled" / "bateria.svg").read_text()
    repo.svg("outline", "b")
    repo.svg("filled", "b", texto.replace('stroke="black"', 'stroke="red"'))
    repo.manifesto([icone("b", filled="own")])
    assert "svg-cor-fixa" in codigos(repo.raiz)


def test_cli_check_sai_com_erro_e_lista(repo, capsys):
    from lucerna_icons.__main__ import main

    repo.manifesto([icone("seta")])
    assert main(["check", "--root", str(repo.raiz)]) != 0
    saida = capsys.readouterr()
    assert "svg-ausente" in saida.err and "seta" in saida.err


def test_cli_check_passa(repo_fixtures, capsys):
    from lucerna_icons.__main__ import main

    assert main(["check", "--root", str(repo_fixtures.raiz)]) == 0


@pytest.mark.parametrize("atributo", ["onclick", "onLoad", "ONMOUSEOVER"])
def test_svg_com_atributo_de_evento(repo, atributo):
    repo.svg("outline", "x", SVG_OK.replace("<path ", f'<path {atributo}="alert(1)" '))
    repo.manifesto([icone("x")])
    assert "svg-evento" in codigos(repo.raiz)


@pytest.mark.parametrize("atributo", ["href", "xlink:href"])
def test_svg_com_href(repo, atributo):
    texto = SVG_OK.replace("<svg ", '<svg xmlns:xlink="http://www.w3.org/1999/xlink" ', 1)
    repo.svg("outline", "x", texto.replace("<path ", f'<path {atributo}="https://exemplo.org/x" '))
    repo.manifesto([icone("x")])
    assert "svg-href" in codigos(repo.raiz)


def test_svg_com_use_e_proibido(repo):
    repo.svg("outline", "x", SVG_OK.replace("</svg>", '<use width="1"/></svg>'))
    repo.manifesto([icone("x")])
    assert "svg-elemento" in codigos(repo.raiz)


def test_camada_da_mesma_familia_passa(repo):
    for n in ("bat-1", "raio"):
        repo.svg("outline", n)
    repo.manifesto([icone("bat-1", family="bat", layer="raio"), icone("raio", family="bat")])
    assert manifest.validar(repo.raiz) == []
    _, icones, _ = manifest.carregar(repo.raiz)
    assert {ic.name: ic.layer for ic in icones} == {"bat-1": "raio", "raio": None}


@pytest.mark.parametrize(
    "entradas",
    [
        [icone("bat-1", family="bat", layer="raio")],  # a camada não existe
        [icone("bat-1", family="bat", layer="raio"), icone("raio", family="outra")],  # outra família
        [icone("bat-1", layer="raio"), icone("raio")],  # sem família
        [icone("bat-1", family="bat", layer="bat-1")],  # o próprio ícone
        [icone("bat-1", family="bat", layer="Raio!")],  # nome inválido
        [icone("bat-1", family="bat", layer=None)],  # não é texto
    ],
)
def test_camada_invalida(repo, entradas):
    for e in entradas:
        repo.svg("outline", e["name"])
    repo.manifesto(entradas)
    assert "camada-invalida" in codigos(repo.raiz)
