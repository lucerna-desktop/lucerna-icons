# lucerna-icons

Ícones de interface do Lucerna, baseados no Lucide, cada um com **contorno** e **preenchido**. É usado pelo [`lucerna-shell`](https://github.com/lucerna-desktop/lucerna-shell) e pelas interfaces Qt dos apps do ecossistema, para que tudo tenha o mesmo visual.

Baseado no [Lucide](https://lucide.dev).

**Situação:** o build da fonte e a validação já existem, e o [inventário](inventario.md) dos ícones do shell está no `manifest.json`, todos `pendente` (os do Lucide 1.70.0 já com o contorno baixado; os outros, para desenhar). Nenhum foi aprovado ainda. O desenho está no [spec](https://github.com/lucerna-desktop/lucerna-shell/blob/main/docs/superpowers/specs/2026-11-09-lucerna-icons-design.md) do `lucerna-shell`.

## O que é

- **Só os ícones usados.** O pacote cresce sob demanda, quando um ícone novo for preciso; não inclui o Lucide inteiro.
- **Contorno e preenchido.** O Lucide só tem contorno, então o preenchido é desenhado aqui.
- **Variações no nível do Material**: onde o Material Symbols tem mais estados (os do Wi-Fi, o volume), desenhamos os que faltam. A bateria é desenho nosso, com 5 níveis de 4 barras.
- **Ícones originais** onde o Lucide não tem, na mesma linguagem: grade de 24, traço 2, pontas e junções redondas.
- Só ícones de interface; ícones de aplicativos e de tipos de arquivo do tema do sistema ficam de fora.

## Estrutura prevista

Marcado com `[x]` o que já existe.

- [x] `manifest.json`: a versão do Lucide de onde vêm os derivados e uma entrada por ícone (veja "O manifesto").
- [x] `inventario.md`: a tabela legível do inventário, por área do shell: a ligadura do Material, o nome Lucerna, o ícone do Lucide (ou "desenhar"), o `filled` e a família.
- [ ] `svg/outline/<nome>.svg` e `svg/filled/<nome>.svg`: a fonte da verdade, na grade de 24. Hoje só os contornos vindos do Lucide; os preenchidos e os ícones novos ainda serão desenhados.
- [x] `tools/gallery`: a página estática de galeria usada na revisão (`make gallery`).
- [x] `tools/lucerna_icons`: o `check` (manifesto e SVGs), o `fetch` (traz um ícone do Lucide) e o `build` da fonte **"Lucerna Icons"**, com uma ligadura por ícone: `<nome>` para o contorno e `<nome>-fill` para o preenchido.
- [x] Alvo de instalação (`make install`) para `share/fonts/lucerna-icons` e `share/lucerna-icons/svg`.
- [x] O CI (`.github/workflows/ci.yml`): `check` e `build` em PR e no `main`; a release nas tags `v*`.

## O manifesto

```json
{
  "lucideVersion": "1.70.0",
  "icons": [
    {
      "name": "battery-1",
      "origin": "lucerna",
      "material": ["battery_1_bar", "battery_2_bar"],
      "filled": "own",
      "family": "battery",
      "status": "pendente"
    }
  ]
}
```

- `lucideVersion`: a tag do Lucide de onde vêm os derivados (hoje `1.70.0`; as tags do Lucide 1.x não têm o `v`). Enquanto nenhum ícone vier do Lucide, pode ficar como `"pendente"`.
- `name`: o nome do Lucerna, em kebab-case (igual ao do Lucide quando derivado); não termina em `-fill`.
- `origin`: `"lucide:<nome>"` ou `"lucerna"`, para os originais.
- `material`: as ligaduras do Material Symbols que ele substitui (cada uma em um só ícone).
- `filled`: `"own"` quando tem `svg/filled/<nome>.svg`; `"outline"` para os sem área a preencher (fechar, setas), em que o `<nome>-fill` mostra o próprio contorno.
- `family`: os estados de uma família (`battery-0`…`battery-4`) levam o mesmo nome aqui, e a família é aprovada junta; `null` quando não tem.
- `status`: `"pendente"` ou `"aprovado"`. Só os aprovados entram na fonte instalada; um pendente pode não ter SVG ainda.
- `layer` (opcional): o glifo da camada de cima de um ícone em duas camadas, que o shell sobrepõe em outra cor. A galeria mostra a composição, com o ícone em `text` e a camada na cor do estado. Hoje só o `battery-0` (o corpo vazio) usa, com `"layer": "battery-fill-1"` (só o preenchimento de 25 %, na posição exata do `battery-1`). Na migração, quando a bateria está baixa, o shell desenha o corpo na cor normal e o preenchimento em `danger`. A camada precisa existir no manifesto e ser da mesma família.
- `background` (opcional): o glifo de fundo, desenhado **apagado** por baixo do ícone, diferente do `layer` (a camada de cima colorida). O shell desenha o fundo na cor do ícone com a opacidade `OPACIDADE_FUNDO` (0,3, em `tools/lucerna_icons/manifest.py`) e o ícone por cima, na cor cheia. Hoje o `wifi-0`, o `wifi-1` e o `wifi-2` têm `"background": "wifi-3"`: o sinal incompleto mostra os arcos que faltam apagados, como no Android, e o `wifi-3` não tem fundo. O fundo precisa existir no manifesto, ser da mesma família e cobrir o glifo: o `check` confere, nos 4 pesos, que o desenho do nível cabe dentro do desenho do fundo (`fundo-nao-cobre`). A galeria mostra os níveis lado a lado sobre o fundo, em 18, 20 e 64 px, nos dois temas.
- `minSize` (opcional): o menor tamanho, em px, em que o ícone precisa funcionar no shell. Sem o campo, vale 14, o menor token. Os estados de uma família declaram o mesmo valor, e o `check` confere isso. A galeria esmaece os tamanhos abaixo dele, com o rótulo "fora do uso". A família `battery` tem `minSize: 18`, porque aparece em 18 px na barra e em 20 px ou mais no resto; a `wifi` e a `bluetooth` também têm 18, e a `brightness`, 14 (o controle de brilho da central).

## Os SVGs

- `viewBox="0 0 24 24"`, como o Lucide: traço 2, `stroke-linecap` e `stroke-linejoin` `round` no `<svg>`.
- Cor só `currentColor` ou `none`, nunca fixa.
- Para recortar um traço de dentro de um preenchido (o raio dentro da bateria cheia), usa-se uma `<mask>`: um retângulo `white` (o que fica) e o traço `black` (o que sai), e o elemento pintado leva `mask="url(#id)"`. Um exemplo está em `tests/fixtures/svg/filled/bateria.svg`. Furos geométricos também valem com `fill-rule="evenodd"`.

## Desenvolvimento

As dependências Python ficam num `.venv` local, criado sozinho pelo Makefile (ou com `make venv`); nada vai para o sistema.

```sh
make check          # valida o manifesto e os SVGs
make check-tests    # os testes (pytest)
make build          # dist/: os 4 TTFs, os SVGs e o manifesto, só dos aprovados
make build-all      # dist/todos/: o mesmo com os pendentes, para a galeria
make gallery ICONS="battery-0 wifi"   # a galeria de revisão em gallery-out/
make gallery LOTE=1                   # ... ou a de um lote do lotes.json
```

A galeria (`python -m lucerna_icons gallery <nome>... | --lote <n> --out <pasta> [--dist dist/todos]`) gera um `index.html` com os TTFs em `fontes/`, que abre direto do disco. Cada ícone vem com a família inteira e mostra o original do Lucide (quando derivado), o contorno e o preenchido nos 4 pesos, os tamanhos 14 a 64 com o peso automático, os temas catppuccin-mocha e catppuccin-latte, o bloco ativo e o inativo, a animação do preenchimento e o Material Symbols ao lado (o do sistema ou, com rede, o do Google Fonts). O que ainda não foi desenhado aparece como "a desenhar". As cores dos temas são um retrato do shell em `tools/gallery/temas.json`, refeito com `python3 tools/gallery/temas.py <caminho do lucerna-shell> > tools/gallery/temas.json`.

Para instalar, primeiro o build como usuário e depois a cópia como root (o `install` só copia o que está em `dist/` e falha se o build não foi feito):

```sh
make build
sudo make install PREFIX=/usr   # TTFs em $(PREFIX)/share/fonts/lucerna-icons/,
                                # SVGs e manifesto em $(PREFIX)/share/lucerna-icons/
                                # LICENSE e LICENSE-LUCIDE em $(PREFIX)/share/licenses/lucerna-icons/
```

Direto pela ferramenta: `PYTHONPATH=tools .venv/bin/python -m lucerna_icons check` e `... build [--all] --out dist/`.

Para trazer um ícone do Lucide (da tag `lucideVersion`, pelo raw.githubusercontent.com):

```sh
PYTHONPATH=tools .venv/bin/python -m lucerna_icons fetch volume-2 \
    --material volume_up --filled own --family volume
```

O `fetch` grava `svg/outline/<nome>.svg` com os atributos normalizados (grade de 24, `currentColor`, traço 2, pontas e junções redondas) e cria a entrada `pendente` com `origin: "lucide:<nome>"`. Um ícone aprovado nunca é sobrescrito; num pendente, o SVG e a origem são refeitos, e `material`, `filled` e `family` só mudam se vierem na chamada. A variável `LUCERNA_LUCIDE_URL` (ou `--url`) troca a URL, com `{tag}` e `{nome}`.

A fonte tem 4 pesos, gerados dos mesmos SVGs com o traço reescrito: traço 1 → `LucernaIcons-ExtraLight.ttf` (200), 1,5 → `Light` (300), 2 → `Regular` (400) e 2,5 → `SemiBold` (600). Os traços viram contornos com o [picosvg](https://github.com/googlefonts/picosvg) e o skia-pathops, e a fonte é montada com o fontTools.

## Como um ícone entra

Nenhum ícone entra no pacote sem ser aprovado. A revisão é **em lotes de 10–15 ícones**, cada um com a família inteira:

1. Escolhe-se o próximo lote do `manifest.json` (os ícones começam como `pendente`).
2. Para cada ícone do lote, monta-se o contorno, o preenchido e todos os estados (os 5 da bateria, por exemplo), com o original do Lucide ao lado quando houver.
3. A galeria mostra cada ícone em 14, 16, 20, 24, 32, 40 e 64 px (com o peso automático), nos temas escuro e claro, num bloco ativo e com a animação do preenchimento, ao lado do Material atual.
4. O lote é aprovado, ou os que precisam de ajuste voltam no lote seguinte. Só um ícone aprovado vira `aprovado`, e a família é aprovada junta.

## Licença

O código e os ícones originais são **MIT** (veja [`LICENSE`](LICENSE)).

Os ícones derivados vêm do [Lucide](https://lucide.dev), licenciado sob ISC; os que o Lucide herdou do [Feather](https://feathericons.com) são MIT, de Cole Bemis. O aviso de copyright e o texto integral da licença do Lucide estão em [`LICENSE-LUCIDE`](LICENSE-LUCIDE) e acompanham toda cópia, inclusive as editadas. O `manifest.json` registra, por ícone, o que é derivado do Lucide e o que é original.
