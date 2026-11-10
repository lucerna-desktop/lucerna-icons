"""Linha de comando: `python -m lucerna_icons check|build|fetch|gallery`.

    check [--root .]                     valida o manifesto e os SVGs
    build [--all] [--out dist] [--root .]  gera a fonte (só aprovados; --all
                                           inclui os pendentes, para a galeria)
    fetch <nome-no-lucide> [--as <nome>] [--material <ligadura>]...
          [--filled own|outline] [--family <família>] [--root .] [--url <modelo>]
                                         baixa um ícone do Lucide (na tag
                                         lucideVersion) como pendente
    gallery <nome>... | --lote <n> [--lotes lotes.json] --out <pasta>
            [--dist dist/todos] [--root .]
                                         a página de revisão (index.html e
                                         os TTFs em fontes/); cada ícone vem
                                         com a família inteira
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

    p_fetch = sub.add_parser("fetch", help="baixa um ícone do Lucide e o registra como pendente")
    p_fetch.add_argument("nome", help="o nome do ícone no Lucide (ex.: battery-full)")
    p_fetch.add_argument("--as", dest="como", help="o nome no Lucerna (padrão: o do Lucide)")
    p_fetch.add_argument("--material", action="append", help="uma ligadura do Material que ele substitui (repetível)")
    p_fetch.add_argument("--filled", choices=["own", "outline"], help='"own" se tem área para preencher')
    p_fetch.add_argument("--family", help="a família de estados")
    p_fetch.add_argument("--root", type=Path, default=Path("."), help="a raiz do repositório")
    p_fetch.add_argument("--url", help="modelo da URL, com {tag} e {nome} (padrão: o raw do GitHub)")

    p_gal = sub.add_parser("gallery", help="gera a página de revisão dos ícones")
    p_gal.add_argument("nomes", nargs="*", help="os ícones (cada um vem com a família inteira)")
    p_gal.add_argument("--lote", type=int, help="os ícones do lote <n> do lotes.json, no lugar dos nomes")
    p_gal.add_argument("--lotes", type=Path, help="o arquivo dos lotes (padrão: <root>/lotes.json)")
    p_gal.add_argument("--out", type=Path, required=True, help="a pasta de saída")
    p_gal.add_argument("--dist", type=Path, help="um `build --all` já feito (padrão: faz um build temporário)")
    p_gal.add_argument("--root", type=Path, default=Path("."), help="a raiz do repositório")

    args = parser.parse_args(argv)

    if args.comando == "gallery":
        from . import gallery

        try:
            pagina = gallery.gerar(
                args.root, args.nomes, args.out, dist=args.dist, lote=args.lote, lotes=args.lotes
            )
        except gallery.ErroDeGaleria as e:
            print(f"gallery: {e}", file=sys.stderr)
            return 1
        print(pagina)
        return 0

    if args.comando == "fetch":
        from . import fetch

        try:
            caminho = fetch.buscar(
                args.root,
                args.nome,
                args.como,
                material=args.material,
                filled=args.filled,
                family=args.family,
                url=args.url,
            )
        except fetch.ErroDeFetch as e:
            print(f"fetch {args.nome}: {e}", file=sys.stderr)
            return 1
        print(caminho)
        return 0

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
