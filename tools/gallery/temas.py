"""Gera `temas.json`: o retrato das cores de dois temas do lucerna-shell.

A galeria é independente do shell, então leva as cores copiadas. Os tokens
derivados (o contêiner do destaque, o texto e o ícone sobre ele) são
calculados aqui com as mesmas funções do `core/theme/ThemeManager.qml` do
shell (`mix` com arredondamento em 8 bits, `containerOf`, `onContainerOf`,
`towardContrast`/`iconOn`, `fillOf`), traduzidas uma a uma.

Uso (da raiz do repositório):

    python3 tools/gallery/temas.py ../lucerna-shell > tools/gallery/temas.json

Lê `themes/catppuccin-mocha.json` e `themes/catppuccin-latte.json` do shell
e registra no JSON a origem e o commit dele.
"""

import json
import math
import subprocess
import sys
from pathlib import Path

TEMAS = {"escuro": "catppuccin-mocha", "claro": "catppuccin-latte"}
COPIADAS = ["base", "surface", "raised", "border", "text", "textMuted", "textFaint", "accent", "danger"]

Cor = tuple[float, float, float, float]
PRETO: Cor = (0.0, 0.0, 0.0, 1.0)
BRANCO: Cor = (1.0, 1.0, 1.0, 1.0)


def de_hex(h: str) -> Cor:
    h = h.lstrip("#")
    if len(h) == 6:
        h += "ff"
    elif len(h) == 8:  # o #aarrggbb do Qt
        h = h[2:] + h[:2]
    r, g, b, a = (int(h[i : i + 2], 16) / 255 for i in range(0, 8, 2))
    return (r, g, b, a)


def para_hex(c: Cor) -> str:
    return "#" + "".join(f"{round(v * 255):02x}" for v in c[:3])


def luminancia(c: Cor) -> float:
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])


def contraste(a: Cor, b: Cor) -> float:
    la, lb = luminancia(a), luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _round_js(x: float) -> float:
    # Math.round do JavaScript: meio arredonda para cima (o round do Python é o do banqueiro).
    return math.floor(x + 0.5)


def mix(a: Cor, b: Cor, t: float) -> Cor:
    return tuple(_round_js((x + (y - x) * t) * 255) / 255 for x, y in zip(a, b))  # type: ignore[return-value]


def container_of(c: Cor, base: Cor, text: Cor, dark: bool) -> Cor:
    for i in range(60 if dark else 50, 0, -1):
        r = mix(base, c, i / 100)
        if contraste(text, r) >= 4.5:
            return r
    return base


def on_container_of(bg: Cor, text: Cor, base: Cor) -> Cor:
    if contraste(text, bg) >= 4.5:
        return text
    best = text
    for x in (text, base, PRETO, BRANCO):
        if contraste(bg, x) > contraste(bg, best):
            best = x
    return best


def toward_contrast(c: Cor, bg: Cor, aways: list[Cor], minimo: float) -> Cor | None:
    for i in range(21):
        for away in aways:
            f = c if i == 0 else mix(c, away, i / 20)
            if contraste(f, bg) >= minimo:
                return f
    return None


def icon_on(c: Cor, bg: Cor, dark: bool) -> Cor:
    first, second = (BRANCO, PRETO) if dark else (PRETO, BRANCO)
    return toward_contrast(c, bg, [first], 3) or toward_contrast(c, bg, [second], 3) or c


def fill_of(accent: Cor, surface: Cor, track: Cor) -> Cor:
    soft = mix(accent, surface, 0.15)
    if contraste(soft, track) >= 3:
        return soft
    away = PRETO if contraste(PRETO, track) > contraste(BRANCO, track) else BRANCO
    return toward_contrast(accent, track, [away], 3) or away


def derivados(cores: dict, dark: bool) -> dict:
    """O `derivedColors` do shell, só com os tokens que a galeria usa."""

    def get(nome):
        return de_hex(cores.get(nome, "#ff00ff"))

    track = de_hex(cores["track"]) if "track" in cores else get("raised" if dark else "border")
    container = (
        de_hex(cores["accentContainer"])
        if "accentContainer" in cores
        else container_of(get("accent"), get("base"), get("text"), dark)
    )
    on_container = (
        de_hex(cores["onAccentContainer"])
        if "onAccentContainer" in cores
        else on_container_of(container, get("text"), get("base"))
    )
    icone = de_hex(cores["accentIcon"]) if "accentIcon" in cores else icon_on(get("accent"), container, dark)
    preenchimento = (
        de_hex(cores["accentFill"]) if "accentFill" in cores else fill_of(get("accent"), get("surface"), track)
    )
    return {
        "track": para_hex(track),
        "accentContainer": para_hex(container),
        "onAccentContainer": para_hex(on_container),
        "accentIcon": para_hex(icone),
        "accentFill": para_hex(preenchimento),
    }


def retrato(shell: Path) -> dict:
    commit = subprocess.run(
        ["git", "-C", str(shell), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    temas = {}
    for papel, ident in TEMAS.items():
        dados = json.loads((shell / "themes" / f"{ident}.json").read_text(encoding="utf-8"))
        cores, dark = dados["colors"], dados.get("dark", True)
        temas[papel] = {
            "id": ident,
            "nome": dados["name"],
            "dark": dark,
            "cores": {k: cores[k] for k in COPIADAS} | derivados(cores, dark),
        }
    return {
        "fonte": "lucerna-shell: themes/*.json; derivados como no core/theme/ThemeManager.qml "
        "(gerado por tools/gallery/temas.py)",
        "commit": commit,
        "temas": temas,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: temas.py <caminho do lucerna-shell>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(retrato(Path(sys.argv[1])), indent=2, ensure_ascii=False))
