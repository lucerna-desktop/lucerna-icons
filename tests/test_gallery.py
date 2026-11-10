"""A galeria de revisão: a página gerada, os ids das células, os lotes e as cores dos temas."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

from conftest import SVG_OK, icone
from lucerna_icons import build, fetch, gallery
from lucerna_icons.__main__ import main

PESOS = (200, 300, 400, 600)
TAMANHOS = (14, 16, 20, 24, 32, 40, 64)
TEMAS = ("escuro", "claro")
PASTA_GALERIA = Path(__file__).parent.parent / "tools" / "gallery"


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch):
    """Nenhum teste da galeria fala com a rede: a URL do Lucide aponta para uma porta fechada."""
    monkeypatch.setenv("LUCERNA_LUCIDE_URL", "http://127.0.0.1:9/{tag}/icons/{nome}.svg")


@pytest.fixture
def repo_galeria(repo_fixtures):
    """As fixtures, mais um pendente sem desenho e um `own` ainda sem o preenchido."""
    r = repo_fixtures
    dados = json.loads((r.raiz / "manifest.json").read_text())
    dados["icons"] = [dict(i, status="pendente") for i in dados["icons"]]
    dados["icons"] += [
        icone("novo", material=["new_thing"], filled="own", status="pendente"),
        icone("caixa", origin="lucide:box", material=["inventory_2"], filled="own", status="pendente"),
    ]
    (r.raiz / "manifest.json").write_text(json.dumps(dados))
    r.svg("outline", "caixa", SVG_OK)
    return r


@pytest.fixture(scope="module")
def fontes(tmp_path_factory):
    """Um build qualquer, só para a galeria ter os TTFs (os testes não olham os glifos)."""
    from conftest import Repo

    r = Repo(tmp_path_factory.mktemp("fontes") / "repo")
    r.manifesto([icone("seta")])
    r.svg("outline", "seta")
    saida = r.raiz / "dist"
    build.construir(r.raiz, saida)
    return saida


def gerar(repo, nomes, tmp_path, fontes, **kw):
    saida = tmp_path / "galeria"
    pagina = gallery.gerar(repo.raiz, nomes, saida, dist=fontes, **kw)
    return pagina.read_text(encoding="utf-8"), saida


def ids(texto):
    return set(re.findall(r'\bid="([^"]+)"', texto))


def classes_de(texto, ident):
    m = re.search(rf'<[^>]*\bid="{re.escape(ident)}"[^>]*>', texto)
    assert m, f"falta o id {ident}"
    c = re.search(r'class="([^"]*)"', m.group(0))
    return set(c.group(1).split()) if c else set()


def test_celulas_de_um_icone_completo(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["bateria"], tmp_path, fontes)
    achados = ids(texto)
    assert "ic-bateria" in achados
    for peso in PESOS:
        assert f"ic-bateria-contorno-{peso}" in achados
        assert f"ic-bateria-preenchido-{peso}" in achados
    for tema in TEMAS:
        for tipo in ("contorno", "preenchido", "material", "material-fill"):
            for t in TAMANHOS:
                assert f"ic-bateria-{tema}-{tipo}-{t}" in achados
        for bloco in ("ativo", "inativo", "material-ativo", "material-inativo"):
            assert f"ic-bateria-{tema}-bloco-{bloco}" in achados
        assert f"ic-bateria-{tema}-anima" in achados
    # Original da casa: sem o Lucide ao lado.
    assert "ic-bateria-lucide" not in achados
    assert "pendente" in texto


def test_peso_automatico_pelo_tamanho(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["bateria"], tmp_path, fontes)
    esperado = {14: 600, 16: 600, 20: 400, 24: 400, 32: 300, 40: 300, 64: 200}
    for t, peso in esperado.items():
        m = re.search(rf'<[^>]*\bid="ic-bateria-escuro-contorno-{t}"[^>]*>', texto)
        assert f"--peso:{peso}" in m.group(0).replace(" ", ""), (t, m.group(0))
        assert f"font-size:{t}px" in m.group(0).replace(" ", ""), (t, m.group(0))


def test_original_vem_do_cache_do_lucide(repo_galeria, tmp_path, fontes):
    cache = repo_galeria.raiz / ".cache" / "lucide" / "0.460.0"
    cache.mkdir(parents=True)
    (cache / "arrow-right.svg").write_text(SVG_OK.replace("M5 12h14", "M1 1h2").replace("<svg ", "<!-- @license ISC -->\n<svg ", 1))
    texto, _ = gerar(repo_galeria, ["seta"], tmp_path, fontes)
    assert "ic-seta-lucide" in ids(texto)
    assert 'd="M1 1h2"' in texto  # o cru do cache, não o contorno atual
    assert "original indisponível" not in texto


def test_sem_cache_nem_rede_cai_no_contorno_atual(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["seta"], tmp_path, fontes)
    assert "ic-seta-lucide" in ids(texto)
    assert "contorno atual (original indisponível)" in texto


def test_sem_cache_baixa_da_tag_fixada_e_guarda(repo_galeria, tmp_path, fontes, monkeypatch):
    from test_fetch import Lucide

    servidor = Lucide()
    try:
        servidor.icone("arrow-right", SVG_OK.replace("M5 12h14", "M7 7h7"), tag="0.460.0")
        monkeypatch.setenv("LUCERNA_LUCIDE_URL", servidor.url)
        texto, _ = gerar(repo_galeria, ["seta"], tmp_path, fontes)
        assert servidor.pedidos == ["/0.460.0/icons/arrow-right.svg"]
    finally:
        servidor.fechar()
    assert 'd="M7 7h7"' in texto
    assert (repo_galeria.raiz / ".cache" / "lucide" / "0.460.0" / "arrow-right.svg").exists()


def test_derivado_do_lucide_mostra_o_original(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["seta"], tmp_path, fontes)
    assert "ic-seta-lucide" in ids(texto)
    assert "Lucide 1.70.0" not in texto  # a fixture fixa a 0.460.0
    assert "Lucide 0.460.0" in texto
    # O SVG do contorno, como foi baixado, vai embutido.
    assert 'd="M5 12h14"' in texto


def test_filled_outline_preenchido_e_o_contorno(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["seta"], tmp_path, fontes)
    # A célula do preenchido existe (a ligadura -fill dá o contorno) e não é "a desenhar".
    assert "a-desenhar" not in classes_de(texto, "ic-seta-preenchido-400")
    assert "seta-fill" in texto


def test_own_sem_preenchido_mostra_a_desenhar(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["caixa"], tmp_path, fontes)
    achados = ids(texto)
    assert "a-desenhar" not in classes_de(texto, "ic-caixa-contorno-400")
    for peso in PESOS:
        assert "a-desenhar" in classes_de(texto, f"ic-caixa-preenchido-{peso}")
    for tema in TEMAS:
        assert "a-desenhar" in classes_de(texto, f"ic-caixa-{tema}-preenchido")
        assert f"ic-caixa-{tema}-contorno-24" in achados


def test_icone_sem_desenho_nao_e_erro(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["novo"], tmp_path, fontes)
    achados = ids(texto)
    assert "a-desenhar" in classes_de(texto, "ic-novo")
    assert "ic-novo-a-desenhar" in achados
    # O Material continua ao lado, para comparar.
    for tema in TEMAS:
        assert f"ic-novo-{tema}-material-24" in achados
    assert "ic-novo-contorno-400" not in achados
    # Sem contorno, não há bloco do Lucerna, então não há a nota do preenchido.
    assert "o ativo mostra o contorno" not in texto


def test_familia_vem_inteira(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["wifi-2"], tmp_path, fontes)
    achados = ids(texto)
    assert {"ic-wifi", "ic-wifi-2", "familia-wifi"} <= achados
    # Na ordem do manifesto.
    assert texto.index('id="ic-wifi"') < texto.index('id="ic-wifi-2"')


def test_repetidos_entram_uma_vez(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["wifi", "wifi-2", "seta", "seta"], tmp_path, fontes)
    assert texto.count('id="ic-seta"') == 1
    assert texto.count('id="ic-wifi"') == 1


def test_nome_inexistente_falha(repo_galeria, tmp_path, fontes):
    with pytest.raises(gallery.ErroDeGaleria, match="naoexiste"):
        gallery.gerar(repo_galeria.raiz, ["seta", "naoexiste"], tmp_path / "g", dist=fontes)
    assert not (tmp_path / "g" / "index.html").exists()


def test_sem_nenhum_icone_falha(repo_galeria, tmp_path, fontes):
    with pytest.raises(gallery.ErroDeGaleria):
        gallery.gerar(repo_galeria.raiz, [], tmp_path / "g", dist=fontes)


def test_saida_tem_as_fontes_relativas(repo_galeria, tmp_path, fontes):
    texto, saida = gerar(repo_galeria, ["seta"], tmp_path, fontes)
    for estilo, peso in (("ExtraLight", 200), ("Light", 300), ("Regular", 400), ("SemiBold", 600)):
        assert (saida / "fontes" / f"LucernaIcons-{estilo}.ttf").exists()
        assert f'url("fontes/LucernaIcons-{estilo}.ttf")' in texto
    assert 'font-family: "Lucerna Icons"' in texto
    assert 'local("Material Symbols Rounded")' in texto
    # Autocontida: o CSS e o JS vão dentro da página.
    assert "<style>" in texto and "<script>" in texto
    assert 'href="gallery.css"' not in texto and 'src="gallery.js"' not in texto
    # Os temas, com os tokens do contêiner.
    temas = json.loads((PASTA_GALERIA / "temas.json").read_text())
    for papel in TEMAS:
        assert temas["temas"][papel]["cores"]["accentContainer"].lower() in texto.lower()


def test_sem_dist_faz_o_build(repo_galeria, tmp_path):
    saida = tmp_path / "g"
    gallery.gerar(repo_galeria.raiz, ["seta"], saida)
    assert (saida / "fontes" / "LucernaIcons-Regular.ttf").exists()


def test_dist_sem_fontes_falha(repo_galeria, tmp_path):
    with pytest.raises(gallery.ErroDeGaleria, match="TTF"):
        gallery.gerar(repo_galeria.raiz, ["seta"], tmp_path / "g", dist=tmp_path / "vazio")


# --- Lotes -------------------------------------------------------------------


def escrever_lotes(raiz, lotes):
    (raiz / "lotes.json").write_text(json.dumps({"lotes": lotes}))


def test_lote(repo_galeria, tmp_path, fontes):
    escrever_lotes(
        repo_galeria.raiz,
        [
            {"n": 1, "icones": ["seta", "bateria"], "data": "2026-11-10", "decisao": None},
            {"n": 2, "icones": ["caixa"], "data": "2026-11-11", "decisao": None},
        ],
    )
    assert gallery.icones_do_lote(repo_galeria.raiz, 1) == (["seta", "bateria"], {"n": 1, "icones": ["seta", "bateria"], "data": "2026-11-10", "decisao": None})
    texto, _ = gerar(repo_galeria, [], tmp_path, fontes, lote=1)
    achados = ids(texto)
    assert {"ic-seta", "ic-bateria"} <= achados
    assert "ic-caixa" not in achados
    assert "Lote 1" in texto and "2026-11-10" in texto


def test_lote_inexistente_falha(repo_galeria, tmp_path, fontes):
    escrever_lotes(repo_galeria.raiz, [{"n": 1, "icones": ["seta"], "data": "2026-11-10", "decisao": None}])
    with pytest.raises(gallery.ErroDeGaleria, match="lote 3"):
        gallery.gerar(repo_galeria.raiz, [], tmp_path / "g", dist=fontes, lote=3)


def test_lote_sem_arquivo_falha(repo_galeria, tmp_path, fontes):
    with pytest.raises(gallery.ErroDeGaleria, match="lotes.json"):
        gallery.gerar(repo_galeria.raiz, [], tmp_path / "g", dist=fontes, lote=1)


def test_lote_com_nome_inexistente_falha(repo_galeria, tmp_path, fontes):
    escrever_lotes(repo_galeria.raiz, [{"n": 1, "icones": ["seta", "sumiu"], "data": "2026-11-10", "decisao": None}])
    with pytest.raises(gallery.ErroDeGaleria, match="sumiu"):
        gallery.gerar(repo_galeria.raiz, [], tmp_path / "g", dist=fontes, lote=1)


# --- A linha de comando ---------------------------------------------------------


def test_cli(repo_galeria, tmp_path, fontes, capsys):
    saida = tmp_path / "g"
    codigo = main(["gallery", "seta", "novo", "--root", str(repo_galeria.raiz), "--out", str(saida), "--dist", str(fontes)])
    assert codigo == 0
    assert (saida / "index.html").exists()
    assert str(saida / "index.html") in capsys.readouterr().out


def test_cli_nome_inexistente(repo_galeria, tmp_path, fontes, capsys):
    codigo = main(["gallery", "naoexiste", "--root", str(repo_galeria.raiz), "--out", str(tmp_path / "g"), "--dist", str(fontes)])
    assert codigo == 1
    assert "naoexiste" in capsys.readouterr().err


def test_cli_nomes_e_lote_juntos_falha(repo_galeria, tmp_path, fontes, capsys):
    escrever_lotes(repo_galeria.raiz, [{"n": 1, "icones": ["seta"], "data": "2026-11-10", "decisao": None}])
    codigo = main(["gallery", "seta", "--lote", "1", "--root", str(repo_galeria.raiz), "--out", str(tmp_path / "g"), "--dist", str(fontes)])
    assert codigo == 1


# --- As cores dos temas ------------------------------------------------------------


def _temas_py():
    spec = importlib.util.spec_from_file_location("temas", PASTA_GALERIA / "temas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_temas_json_bate_com_as_funcoes_do_shell():
    t = _temas_py()
    dados = json.loads((PASTA_GALERIA / "temas.json").read_text())
    assert re.fullmatch(r"[0-9a-f]{7,}", dados["commit"])
    for papel in TEMAS:
        tema = dados["temas"][papel]
        cores = tema["cores"]
        # Os derivados recalculados das cores copiadas dão o mesmo JSON.
        base = {k: cores[k] for k in t.COPIADAS} | {"track": cores["track"]}
        assert t.derivados(base, tema["dark"]) == {k: cores[k] for k in t.derivados(base, tema["dark"])}
        c = {k: t.de_hex(v) for k, v in cores.items()}
        assert t.contraste(c["onAccentContainer"], c["accentContainer"]) >= 4.5
        assert t.contraste(c["accentIcon"], c["accentContainer"]) >= 3


def test_temas_valores_do_shell():
    """Os valores do shell em ae65557 (conferidos rodando as funções do ThemeManager.qml no node)."""
    dados = json.loads((PASTA_GALERIA / "temas.json").read_text())
    escuro, claro = dados["temas"]["escuro"]["cores"], dados["temas"]["claro"]["cores"]
    assert (escuro["accentContainer"], escuro["onAccentContainer"], escuro["accentIcon"]) == ("#4b5d84", "#cdd6f4", "#89b4fa")
    assert (claro["accentContainer"], claro["onAccentContainer"], claro["accentIcon"]) == ("#aac3f5", "#4c4f69", "#1c61e9")


def test_mix_arredonda_como_o_javascript():
    t = _temas_py()
    # Meio canal (0,5) sobe para 1, como o Math.round; o round do Python daria 0.
    assert t.mix((0, 0, 0, 1), (1 / 255, 1 / 255, 1 / 255, 1), 0.5)[0] == 1 / 255


@pytest.mark.parametrize(
    "sujo",
    [
        SVG_OK.replace("<path ", '<path onload="alert(1)" '),
        SVG_OK.replace("</svg>", "<script>alert(1)</script></svg>"),
    ],
)
def test_original_inseguro_no_cache_cai_no_contorno_atual(repo_galeria, tmp_path, fontes, sujo):
    cache = repo_galeria.raiz / ".cache" / "lucide" / "0.460.0"
    cache.mkdir(parents=True)
    (cache / "arrow-right.svg").write_text(sujo)
    texto, _ = gerar(repo_galeria, ["seta"], tmp_path, fontes)
    assert "alert(1)" not in texto
    assert "contorno atual (original indisponível)" in texto


def test_falha_de_rede_nao_tenta_de_novo_na_mesma_geracao(repo_galeria, tmp_path, fontes, monkeypatch, capsys):
    chamadas = []

    def baixar(url, timeout=0):
        chamadas.append(timeout)
        raise fetch.ErroDeRede("timeout")

    monkeypatch.setattr(fetch, "_baixar", baixar)
    texto, _ = gerar(repo_galeria, ["seta", "caixa", "wifi"], tmp_path, fontes)
    assert chamadas == [fetch.TIMEOUT_GALERIA]
    assert capsys.readouterr().err.count("aviso: sem rede") == 1


def test_resposta_cortada_nao_derruba_a_galeria(repo_galeria, tmp_path, fontes, monkeypatch):
    import http.client

    def baixar(url, timeout=0):
        raise http.client.IncompleteRead(b"x")

    monkeypatch.setattr(fetch, "_baixar", baixar)
    assert fetch.original(repo_galeria.raiz, "0.460.0", "arrow-right") is None


def test_preencher_todos_tem_botao_e_ganchos(repo_galeria, tmp_path, fontes):
    texto, saida = gerar(repo_galeria, ["bateria", "caixa"], tmp_path, fontes)
    assert 'id="alternar-todos"' in texto
    # O botão liga a classe do corpo, que o CSS propaga para a tabela, os blocos e o Material.
    js = (PASTA_GALERIA / "gallery.js").read_text(encoding="utf-8")
    css = (PASTA_GALERIA / "gallery.css").read_text(encoding="utf-8")
    assert 'toggle("todos-cheios"' in js
    for alvo in (".todos-cheios .tamanhos .par", ".todos-cheios .blocos .bloco", ".todos-cheios .blocos .m"):
        assert alvo in css
    # A linha "Contorno" da tabela é um par (contorno + preenchido sobrepostos), com o id no contorno.
    m = re.search(r'<tr id="ic-bateria-escuro-contorno">.*?</tr>', texto, re.S)
    assert m and m.group(0).count('class="par"') == len(TAMANHOS)
    assert "cont" in classes_de(texto, "ic-bateria-escuro-contorno-24")
    # Sem o preenchido desenhado, não há par na linha (nada para trocar).
    m = re.search(r'<tr id="ic-caixa-escuro-contorno">.*?</tr>', texto, re.S)
    assert m and 'class="par"' not in m.group(0)
    # A seção de animação segue com o próprio botão.
    assert "data-alternar" in texto


def test_camadas_mostram_a_composicao_na_cor_do_estado(repo_galeria, tmp_path, fontes):
    dados = json.loads((repo_galeria.raiz / "manifest.json").read_text())
    dados["icons"] += [
        icone("battery-0", family="battery", status="pendente", layer="battery-fill-1"),
        icone("battery-fill-1", family="battery", status="pendente"),
    ]
    (repo_galeria.raiz / "manifest.json").write_text(json.dumps(dados))
    for n in ("battery-0", "battery-fill-1"):
        repo_galeria.svg("outline", n)
    texto, _ = gerar(repo_galeria, ["battery-0"], tmp_path, fontes)
    achados = ids(texto)
    for tema in TEMAS:
        assert f"familia-battery-{tema}-cor" in achados
        for px in gallery.CAMADAS_PX:
            ident = f"ic-battery-0-{tema}-camadas-{px}"
            assert ident in achados
            assert {"camadas", "estado-danger"} <= classes_de(texto, ident)
    # A camada de cima vai sobre a de baixo.
    assert re.search(r'class="g baixo"[^>]*>battery-0<.*?class="g cima"[^>]*>battery-fill-1<', texto)
    # A cor de estado vem do temas.json.
    temas = json.loads((PASTA_GALERIA / "temas.json").read_text())
    for papel in TEMAS:
        assert f"--danger: {temas['temas'][papel]['cores']['danger']}" in texto


def test_sem_camada_nao_tem_composicao(repo_galeria, tmp_path, fontes):
    texto, _ = gerar(repo_galeria, ["wifi-2"], tmp_path, fontes)
    assert not any(i.endswith("-cor") for i in ids(texto))


def test_tamanhos_abaixo_do_min_size_ficam_fora_do_uso(repo_galeria, tmp_path, fontes):
    dados = json.loads((repo_galeria.raiz / "manifest.json").read_text())
    for i in dados["icons"]:
        if i["name"] == "seta":
            i["minSize"] = 18
    (repo_galeria.raiz / "manifest.json").write_text(json.dumps(dados))
    texto, _ = gerar(repo_galeria, ["seta", "caixa"], tmp_path, fontes)
    for t in TAMANHOS:
        fora = "fora-do-uso" in re.search(rf'<td[^>]*>(?:(?!</td>).)*id="ic-seta-escuro-contorno-{t}"', texto, re.S).group(0)
        assert fora == (t < 18)
    # Sem o campo, vale 14: nenhum tamanho da tabela fica fora.
    assert not re.search(r'class="fora-do-uso"[^>]*>(?:(?!</td>).)*id="ic-caixa-', texto, re.S)
