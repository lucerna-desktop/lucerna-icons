"""Ajudantes comuns dos testes: um repositório de ícones de mentira num tmp."""

import json
import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# Um SVG mínimo válido, no formato do Lucide.
SVG_OK = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round">\n  <path d="M5 12h14"/>\n</svg>\n'
)


def icone(name, **campos):
    """Uma entrada do manifesto com os valores padrão, trocando o que vier em `campos`."""
    entrada = {
        "name": name,
        "origin": "lucerna",
        "material": [],
        "filled": "outline",
        "family": None,
        "status": "aprovado",
    }
    entrada.update(campos)
    return entrada


class Repo:
    """Um repositório do lucerna-icons num diretório temporário."""

    def __init__(self, raiz: Path):
        self.raiz = raiz
        (raiz / "svg" / "outline").mkdir(parents=True)
        (raiz / "svg" / "filled").mkdir(parents=True)

    def manifesto(self, icons, lucide_version="pendente"):
        dados = {"lucideVersion": lucide_version, "icons": icons}
        (self.raiz / "manifest.json").write_text(json.dumps(dados, indent=2))

    def svg(self, tipo, nome, texto=SVG_OK):
        (self.raiz / "svg" / tipo / f"{nome}.svg").write_text(texto)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path / "repo")


@pytest.fixture
def repo_fixtures(tmp_path):
    """O repositório com os SVGs de tests/fixtures, todos aprovados."""
    r = Repo(tmp_path / "repo")
    for tipo in ("outline", "filled"):
        for f in (FIXTURES / "svg" / tipo).glob("*.svg"):
            shutil.copy(f, r.raiz / "svg" / tipo / f.name)
    r.manifesto(
        [
            icone("seta", origin="lucide:arrow-right", material=["arrow_forward"]),
            icone("wifi", origin="lucide:wifi", material=["wifi"], family="wifi"),
            icone(
                "wifi-2",
                origin="lucerna",
                material=["network_wifi_2_bar"],
                filled="own",
                family="wifi",
            ),
            icone("bateria", material=["battery_charging_full"], filled="own"),
        ],
        lucide_version="0.460.0",
    )
    return r
