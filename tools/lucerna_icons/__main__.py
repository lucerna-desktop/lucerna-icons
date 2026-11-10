"""Linha de comando: `python -m lucerna_icons check|build`.

    check [--root .]                     valida o manifesto e os SVGs
    build [--all] [--out dist] [--root .]  gera a fonte (só aprovados; --all
                                           inclui os pendentes, para a galeria)
"""

import argparse
import sys
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="lucerna_icons", description="Ferramentas do lucerna-icons.")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_check = sub.add_parser("check", help="valida o manifesto e os SVGs")
    p_check.add_argument("--root", type=Path, default=Path("."), help="a raiz do repositório")

    p_build = sub.add_parser("build", help="gera os TTFs, os SVGs e o manifesto")
    p_build.add_argument("--root", type=Path, default=Path("."), help="a raiz do repositório")
    p_build.add_argument("--out", type=Path, default=Path("dist"), help="a pasta de saída")
    p_build.add_argument("--all", action="store_true", help="inclui os ícones pendentes")

    args = parser.parse_args(argv)

    if args.comando == "check":
        from . import manifest

        erros = manifest.validar(args.root)
        for e in erros:
            print(e, file=sys.stderr)
        if erros:
            print(f"{len(erros)} erro(s).", file=sys.stderr)
            return 1
        print("check: ok")
        return 0

    from . import build

    try:
        arquivos = build.construir(args.root, args.out, todos=args.all)
    except build.ErroDeBuild as e:
        print(e, file=sys.stderr)
        return 1
    for a in arquivos:
        print(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
