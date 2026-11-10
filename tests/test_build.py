"""O build: os 4 TTFs, as ligaduras e a forma dos glifos, sobre as fixtures."""

import json

import pytest
import uharfbuzz as hb
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from pathlib import Path

from conftest import icone
from lucerna_icons import build

PESOS = {
    "LucernaIcons-ExtraLight.ttf": 200,
    "LucernaIcons-Light.ttf": 300,
    "LucernaIcons-Regular.ttf": 400,
    "LucernaIcons-SemiBold.ttf": 600,
}
NOMES = ["seta", "wifi", "wifi-2", "bateria"]


@pytest.fixture
def dist(repo_fixtures, tmp_path):
    saida = tmp_path / "dist"
    build.construir(repo_fixtures.raiz, saida)
    return saida


def moldar(caminho, texto):
    """Os nomes dos glifos que o HarfBuzz produz para `texto`, com `liga` ligada."""
    fonte = hb.Font(hb.Face(hb.Blob.from_file_path(str(caminho))))
    buf = hb.Buffer()
    buf.add_str(texto)
    buf.guess_segment_properties()
    hb.shape(fonte, buf, {"liga": True})
    return [fonte.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def area(fonte, glifo):
    pen = AreaPen(fonte.getGlyphSet())
    fonte.getGlyphSet()[glifo].draw(pen)
    return pen.value


def contornos(fonte, glifo):
    """Cada contorno do glifo como (área com sinal, caixa)."""
    rec = RecordingPen()
    fonte.getGlyphSet()[glifo].draw(rec)
    resultado, atual = [], []
    for op, args in rec.value:
        atual.append((op, args))
        if op in ("closePath", "endPath"):
            sub = RecordingPen()
            sub.value = atual
            pen = AreaPen()
            sub.replay(pen)
            pts = [p for _, a in atual for p in a]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            resultado.append((pen.value, (min(xs), min(ys), max(xs), max(ys))))
            atual = []
    return resultado


def test_gera_os_quatro_pesos(dist):
    assert sorted(p.name for p in dist.glob("*.ttf")) == sorted(PESOS)
    for arquivo, peso in PESOS.items():
        fonte = TTFont(dist / arquivo)
        assert fonte["OS/2"].usWeightClass == peso
        nomes = fonte["name"]
        familia = nomes.getDebugName(16) or nomes.getDebugName(1)
        assert familia == "Lucerna Icons"
        assert fonte["head"].unitsPerEm == 1200


@pytest.mark.parametrize("arquivo", list(PESOS))
@pytest.mark.parametrize("nome", NOMES)
def test_ligadura_do_contorno_e_do_preenchido_dao_um_glifo(dist, arquivo, nome):
    assert moldar(dist / arquivo, nome) == [build.nome_glifo(nome)]
    assert len(moldar(dist / arquivo, f"{nome}-fill")) == 1


def test_wifi_2_fill_nao_e_wifi_2_mais_o_resto(dist):
    assert moldar(dist / "LucernaIcons-Regular.ttf", "wifi-2-fill") == [
        build.nome_glifo("wifi-2", preenchido=True)
    ]
    # E o prefixo mais curto não engole o mais longo.
    assert moldar(dist / "LucernaIcons-Regular.ttf", "wifi-2") == [build.nome_glifo("wifi-2")]


def test_texto_sem_ligadura_nao_aparece(dist):
    fonte = TTFont(dist / "LucernaIcons-Regular.ttf")
    for glifo in moldar(dist / "LucernaIcons-Regular.ttf", "xyz-9"):
        assert fonte["hmtx"][glifo][0] == 0
        assert area(fonte, glifo) == 0


def test_traco_mais_grosso_da_glifo_maior(dist):
    fino = TTFont(dist / "LucernaIcons-ExtraLight.ttf")
    grosso = TTFont(dist / "LucernaIcons-SemiBold.ttf")
    for nome in NOMES:
        g = build.nome_glifo(nome)
        assert abs(area(grosso, g)) > abs(area(fino, g)) * 1.5


def test_filled_outline_aponta_para_o_contorno(dist):
    for arquivo in PESOS:
        assert moldar(dist / arquivo, "seta-fill") == moldar(dist / arquivo, "seta")


def test_filled_own_tem_glifo_proprio(dist):
    for arquivo in PESOS:
        assert moldar(dist / arquivo, "wifi-2-fill") != moldar(dist / arquivo, "wifi-2")


def test_preenchido_com_traco_interno_tem_furo(dist):
    for arquivo in PESOS:
        fonte = TTFont(dist / arquivo)
        cs = contornos(fonte, build.nome_glifo("bateria", preenchido=True))
        # O corpo (externo) e o raio recortado (interno, sentido contrário,
        # dentro da caixa do corpo); o polo da bateria é um terceiro, à parte.
        externos = [c for c in cs if c[0] < 0]
        internos = [c for c in cs if c[0] > 0]
        assert len(internos) == 1, cs
        (x0, y0, x1, y1) = internos[0][1]
        corpo = max(externos, key=lambda c: abs(c[0]))[1]
        assert corpo[0] < x0 and corpo[1] < y0 and x1 < corpo[2] and y1 < corpo[3]


def test_contornos_externos_no_sentido_do_truetype(dist):
    # TrueType: contorno externo no sentido horário, área negativa no AreaPen.
    fonte = TTFont(dist / "LucernaIcons-Regular.ttf")
    for nome in NOMES:
        assert area(fonte, build.nome_glifo(nome)) < 0


def test_glifo_dentro_da_grade(dist):
    fonte = TTFont(dist / "LucernaIcons-Regular.ttf")
    glyf = fonte["glyf"]
    for nome in NOMES:
        g = glyf[build.nome_glifo(nome)]
        assert 0 <= g.xMin and g.xMax <= 1200 and 0 <= g.yMin and g.yMax <= 1200
        assert fonte["hmtx"][build.nome_glifo(nome)][0] == 1200


def test_build_so_inclui_aprovados(repo_fixtures, tmp_path):
    dados = json.loads((repo_fixtures.raiz / "manifest.json").read_text())
    dados["icons"][0]["status"] = "pendente"  # seta
    (repo_fixtures.raiz / "manifest.json").write_text(json.dumps(dados))

    so_aprovados = tmp_path / "a"
    build.construir(repo_fixtures.raiz, so_aprovados)
    fonte = so_aprovados / "LucernaIcons-Regular.ttf"
    assert len(moldar(fonte, "seta")) == 4
    assert not (so_aprovados / "svg" / "outline" / "seta.svg").exists()
    assert (so_aprovados / "svg" / "outline" / "wifi.svg").exists()
    assert (so_aprovados / "svg" / "filled" / "bateria.svg").exists()
    nomes = [i["name"] for i in json.loads((so_aprovados / "manifest.json").read_text())["icons"]]
    assert nomes == ["wifi", "wifi-2", "bateria"]

    todos = tmp_path / "b"
    build.construir(repo_fixtures.raiz, todos, todos=True)
    assert moldar(todos / "LucernaIcons-Regular.ttf", "seta") == [build.nome_glifo("seta")]
    dados = json.loads((todos / "manifest.json").read_text())
    assert dados["lucideVersion"] == "0.460.0"
    assert [i["name"] for i in dados["icons"]] == ["seta", "wifi", "wifi-2", "bateria"]


def test_build_com_pendente_sem_svg(repo, tmp_path):
    repo.svg("outline", "a")
    repo.manifesto([icone("a", filled="own", status="pendente"), icone("b", status="pendente")])
    build.construir(repo.raiz, tmp_path / "d", todos=True)
    fonte = tmp_path / "d" / "LucernaIcons-Regular.ttf"
    # Sem o preenchido ainda, o -fill mostra o contorno; sem SVG, o ícone fica de fora.
    assert moldar(fonte, "a-fill") == [build.nome_glifo("a")]
    assert len(moldar(fonte, "b")) == 1 and moldar(fonte, "b") != [build.nome_glifo("b")]
    # E o manifesto da saída só tem o que entrou.
    dados = json.loads((tmp_path / "d" / "manifest.json").read_text())
    assert [i["name"] for i in dados["icons"]] == ["a"]


def test_build_com_manifesto_vazio(repo, tmp_path):
    repo.manifesto([])
    build.construir(repo.raiz, tmp_path / "d")
    assert len(list((tmp_path / "d").glob("*.ttf"))) == 4


def test_build_recusa_manifesto_invalido(repo, tmp_path):
    repo.manifesto([icone("a")])  # aprovado sem SVG
    with pytest.raises(build.ErroDeBuild):
        build.construir(repo.raiz, tmp_path / "d")


def test_a_fonte_traz_os_avisos_do_lucide_e_do_feather(dist):
    nomes = TTFont(dist / "LucernaIcons-Regular.ttf")["name"]
    aviso = nomes.getDebugName(0)
    assert "Copyright (c) 2026 Lucerna" in aviso
    assert "Copyright (c) 2026 Lucide Icons and Contributors" in aviso
    assert "Copyright (c) 2013-present Cole Bemis" in aviso
    assert "MIT" in nomes.getDebugName(13) and "LICENSE-LUCIDE" in nomes.getDebugName(13)
    assert nomes.getDebugName(14) == "https://github.com/lucerna-desktop/lucerna-icons/blob/main/LICENSE-LUCIDE"


def test_install_leva_as_duas_licencas(tmp_path):
    import shutil
    import subprocess

    raiz = Path(__file__).resolve().parent.parent
    dist = tmp_path / "dist"
    (dist / "svg").mkdir(parents=True)
    (dist / "LucernaIcons-Regular.ttf").write_bytes(b"x")
    (dist / "manifest.json").write_text("{}")
    copia = tmp_path / "repo"
    copia.mkdir()
    for arq in ("Makefile", "LICENSE", "LICENSE-LUCIDE"):
        shutil.copy(raiz / arq, copia / arq)
    shutil.move(str(dist), copia / "dist")
    subprocess.run(
        ["make", "install", "PREFIX=/usr", f"DESTDIR={tmp_path / 'raiz'}"], cwd=copia, check=True, capture_output=True
    )
    lic = tmp_path / "raiz" / "usr" / "share" / "licenses" / "lucerna-icons"
    assert (lic / "LICENSE").read_text() == (raiz / "LICENSE").read_text()
    assert (lic / "LICENSE-LUCIDE").read_text() == (raiz / "LICENSE-LUCIDE").read_text()


def test_recorte_da_mascara_cresce_com_o_traco(tmp_path):
    # O traço preto de uma <mask> também é reescrito pelo peso: o vão do
    # recorte cresce junto com o traço do desenho (as cargas da bateria).
    svg = tmp_path / "corte.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<defs><mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="24" height="24">'
        '<rect width="24" height="24" fill="white" stroke="none"/>'
        '<path d="M12 4v16" stroke="black" stroke-width="4"/></mask></defs>'
        '<rect x="4" y="4" width="16" height="16" fill="currentColor" stroke="none" mask="url(#m)"/></svg>'
    )
    def area(traco):
        pen = AreaPen()
        build.contorno_svg(svg, traco).draw(pen)
        return abs(pen.value)
    # 16 × (16 − 4·traço/2): o recorte tem 2, 4 e 5 de largura.
    assert area(1.0) == pytest.approx(16 * 14, rel=1e-3)
    assert area(2.0) == pytest.approx(16 * 12, rel=1e-3)
    assert area(2.5) == pytest.approx(16 * 11, rel=1e-3)


@pytest.mark.parametrize("traco", [1.0, 1.5, 2.0, 2.5])
def test_battery_fill_1_sobre_o_battery_0_da_o_battery_1(traco):
    # A bateria baixa: o corpo vazio mais a camada do preenchimento é o nível 1, em todos os pesos.
    import pathops

    svg = Path(__file__).parent.parent / "svg" / "outline"
    corpo, camada, nivel = (build.contorno_svg(svg / f"{n}.svg", traco) for n in ("battery-0", "battery-fill-1", "battery-1"))
    sobra = pathops.op(pathops.op(corpo, camada, pathops.PathOp.UNION), nivel, pathops.PathOp.XOR)
    pen = AreaPen()
    sobra.draw(pen)
    assert abs(pen.value) < 1e-3
