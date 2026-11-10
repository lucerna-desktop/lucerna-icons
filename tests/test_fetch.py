"""O fetch: baixa um ícone do Lucide na tag fixada, normaliza e registra no manifesto.

Sem rede: um servidor HTTP local faz o papel do raw.githubusercontent.com.
"""

import json
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from conftest import SVG_OK, icone
from lucerna_icons import fetch, manifest, svgcheck
from lucerna_icons.__main__ import main

SVG_NS = "{http://www.w3.org/2000/svg}"
TAG = "1.70.0"

# Um SVG "sujo", com tudo o que o fetch precisa arrumar.
SVG_SUJO = """<svg
  xmlns="http://www.w3.org/2000/svg"
  class="lucide lucide-bell"
  width="48"
  height="48"
  viewBox="0 0 24 24"
  fill="none"
  stroke="#000000"
  stroke-width="1.5"
  stroke-linecap="butt"
>
  <path d="M10.268 21a2 2 0 0 0 3.464 0" stroke-linejoin="miter" />
  <circle cx="12" cy="5" r="1" fill="#ff0000" />
  <path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326" />
</svg>
"""


class Lucide:
    """Um raw.githubusercontent.com de mentira: responde `/<tag>/icons/<nome>.svg`."""

    def __init__(self):
        self.arquivos: dict[str, str] = {}
        self.pedidos: list[str] = []
        dono = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                dono.pedidos.append(self.path)
                corpo = dono.arquivos.get(self.path)
                if corpo is None:
                    self.send_error(404)
                    return
                dados = corpo.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(dados)))
                self.end_headers()
                self.wfile.write(dados)

            def log_message(self, *args):
                pass

        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.servidor.server_port}/{{tag}}/icons/{{nome}}.svg"
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def icone(self, nome, texto, tag=TAG):
        self.arquivos[f"/{tag}/icons/{nome}.svg"] = texto

    def fechar(self):
        self.servidor.shutdown()
        self.servidor.server_close()


@pytest.fixture
def lucide():
    servidor = Lucide()
    yield servidor
    servidor.fechar()


def ler_manifesto(repo):
    return json.loads((repo.raiz / "manifest.json").read_text())


def entrada(repo, nome):
    return next(e for e in ler_manifesto(repo)["icons"] if e["name"] == nome)


def test_baixa_da_tag_fixada_e_registra_a_origem(repo, lucide):
    repo.manifesto([], lucide_version=TAG)
    lucide.icone("bell", SVG_OK)

    caminho = fetch.buscar(repo.raiz, "bell", url=lucide.url)

    assert lucide.pedidos == [f"/{TAG}/icons/bell.svg"]
    assert caminho == repo.raiz / "svg" / "outline" / "bell.svg"
    assert entrada(repo, "bell") == {
        "name": "bell",
        "origin": "lucide:bell",
        "material": [],
        "filled": "outline",
        "family": None,
        "status": "pendente",
    }
    assert manifest.validar(repo.raiz) == []


def test_normaliza_os_atributos(repo, lucide):
    repo.manifesto([], lucide_version=TAG)
    lucide.icone("bell", SVG_SUJO)

    caminho = fetch.buscar(repo.raiz, "bell", url=lucide.url)

    assert svgcheck.validar_svg(caminho) == []
    raiz = ET.parse(caminho).getroot()
    assert raiz.attrib == {
        "width": "24",
        "height": "24",
        "viewBox": "0 0 24 24",
        "fill": "none",
        "stroke": "currentColor",
        "stroke-width": "2",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
    }
    filhos = list(raiz)
    assert [f.tag for f in filhos] == [SVG_NS + "path", SVG_NS + "circle", SVG_NS + "path"]
    # A junção trocada no filho sai (herda o round do <svg>), e a cor fixa vira currentColor.
    assert "stroke-linejoin" not in filhos[0].attrib
    assert filhos[1].get("fill") == "currentColor"
    # O desenho em si não muda.
    assert filhos[0].get("d") == "M10.268 21a2 2 0 0 0 3.464 0"
    texto = caminho.read_text()
    assert "ns0:" not in texto and texto.endswith("</svg>\n")


def test_as_com_outro_nome_e_os_campos(repo, lucide):
    repo.manifesto([], lucide_version=TAG)
    lucide.icone("battery", SVG_OK)

    fetch.buscar(
        repo.raiz, "battery", como="battery-0", material=["battery_0_bar"], filled="own", family="battery", url=lucide.url
    )

    assert (repo.raiz / "svg" / "outline" / "battery-0.svg").exists()
    assert not (repo.raiz / "svg" / "outline" / "battery.svg").exists()
    assert entrada(repo, "battery-0") == {
        "name": "battery-0",
        "origin": "lucide:battery",
        "material": ["battery_0_bar"],
        "filled": "own",
        "family": "battery",
        "status": "pendente",
    }
    assert manifest.validar(repo.raiz) == []


def test_nao_sobrescreve_um_aprovado(repo, lucide):
    repo.svg("outline", "bell")
    repo.manifesto([icone("bell", origin="lucide:bell")], lucide_version=TAG)
    antes = (repo.raiz / "svg" / "outline" / "bell.svg").read_text()
    manifesto_antes = (repo.raiz / "manifest.json").read_text()
    lucide.icone("bell", SVG_SUJO)

    with pytest.raises(fetch.ErroDeFetch, match="aprovado"):
        fetch.buscar(repo.raiz, "bell", url=lucide.url)

    assert (repo.raiz / "svg" / "outline" / "bell.svg").read_text() == antes
    assert (repo.raiz / "manifest.json").read_text() == manifesto_antes
    assert lucide.pedidos == []


def test_refaz_um_pendente_e_mantem_os_campos(repo, lucide):
    repo.svg("outline", "sino", SVG_OK.replace("M5 12h14", "M1 1h2"))
    repo.manifesto(
        [icone("sino", origin="lucerna", material=["notifications"], filled="own", family="bell", status="pendente")],
        lucide_version=TAG,
    )
    lucide.icone("bell", SVG_OK)

    fetch.buscar(repo.raiz, "bell", como="sino", url=lucide.url)

    assert "M5 12h14" in (repo.raiz / "svg" / "outline" / "sino.svg").read_text()
    assert entrada(repo, "sino") == {
        "name": "sino",
        "origin": "lucide:bell",
        "material": ["notifications"],
        "filled": "own",
        "family": "bell",
        "status": "pendente",
    }
    assert len(ler_manifesto(repo)["icons"]) == 1


def test_icone_que_nao_existe_no_lucide(repo, lucide):
    repo.manifesto([], lucide_version=TAG)

    with pytest.raises(fetch.ErroDeFetch, match="404"):
        fetch.buscar(repo.raiz, "nao-existe", url=lucide.url)

    assert ler_manifesto(repo)["icons"] == []
    assert list((repo.raiz / "svg" / "outline").iterdir()) == []


def test_exige_a_tag_fixada(repo, lucide):
    repo.manifesto([], lucide_version="pendente")
    lucide.icone("bell", SVG_OK)

    with pytest.raises(fetch.ErroDeFetch, match="lucideVersion"):
        fetch.buscar(repo.raiz, "bell", url=lucide.url)
    assert lucide.pedidos == []


@pytest.mark.parametrize("nome", ["Bell", "bell.svg", "../bell", "bell_ring", ""])
def test_nome_do_lucide_invalido(repo, lucide, nome):
    repo.manifesto([], lucide_version=TAG)
    with pytest.raises(fetch.ErroDeFetch):
        fetch.buscar(repo.raiz, nome, url=lucide.url)
    assert lucide.pedidos == []


def test_nome_lucerna_invalido(repo, lucide):
    repo.manifesto([], lucide_version=TAG)
    lucide.icone("bell", SVG_OK)
    with pytest.raises(fetch.ErroDeFetch):
        fetch.buscar(repo.raiz, "bell", como="bell-fill", url=lucide.url)


def test_svg_que_nao_da_para_normalizar(repo, lucide):
    repo.manifesto([], lucide_version=TAG)
    lucide.icone("bell", SVG_OK.replace('viewBox="0 0 24 24"', 'viewBox="0 0 32 32"'))

    with pytest.raises(fetch.ErroDeFetch, match="viewBox"):
        fetch.buscar(repo.raiz, "bell", url=lucide.url)
    assert ler_manifesto(repo)["icons"] == []


def test_linha_de_comando(repo, lucide, capsys):
    repo.manifesto([], lucide_version=TAG)
    lucide.icone("wifi", SVG_OK)

    codigo = main(
        [
            "fetch", "wifi", "--as", "wifi-4", "--material", "signal_wifi_4_bar", "--material", "wifi",
            "--family", "wifi", "--root", str(repo.raiz), "--url", lucide.url,
        ]
    )

    assert codigo == 0
    assert "svg/outline/wifi-4.svg" in capsys.readouterr().out
    assert entrada(repo, "wifi-4")["material"] == ["signal_wifi_4_bar", "wifi"]


def test_linha_de_comando_com_erro(repo, lucide, capsys):
    repo.manifesto([], lucide_version=TAG)
    assert main(["fetch", "nao-existe", "--root", str(repo.raiz), "--url", lucide.url]) == 1
    assert "nao-existe" in capsys.readouterr().err
