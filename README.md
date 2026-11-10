# lucerna-icons

Ícones de interface do Lucerna, baseados no Lucide, cada um com **contorno** e **preenchido**. É usado pelo [`lucerna-shell`](https://github.com/lucerna-desktop/lucerna-shell) e pelas interfaces Qt dos apps do ecossistema, para que tudo tenha o mesmo visual.

Baseado no [Lucide](https://lucide.dev).

**Situação:** o build da fonte e a validação já existem; ainda não há nenhum ícone. O desenho está no [spec](https://github.com/lucerna-desktop/lucerna-shell/blob/main/docs/superpowers/specs/2026-11-09-lucerna-icons-design.md) do `lucerna-shell`.

## O que é

- **Só os ícones usados.** O pacote cresce sob demanda, quando um ícone novo for preciso; não inclui o Lucide inteiro.
- **Contorno e preenchido.** O Lucide só tem contorno, então o preenchido é desenhado aqui.
- **Variações no nível do Material**: onde o Material Symbols tem mais estados (os 8 níveis da bateria, os do Wi-Fi, o volume), desenhamos os que faltam.
- **Ícones originais** onde o Lucide não tem, na mesma linguagem: grade de 24, traço 2, pontas e junções redondas.
- Só ícones de interface; ícones de aplicativos e de tipos de arquivo do tema do sistema ficam de fora.

## Estrutura prevista

Marcado com `[x]` o que já existe.

- [x] `manifest.json`: a versão do Lucide de onde vêm os derivados e uma entrada por ícone (veja "O manifesto"). Hoje está vazio.
- [ ] `svg/outline/<nome>.svg` e `svg/filled/<nome>.svg`: a fonte da verdade, na grade de 24. Hoje só as pastas existem.
- [ ] `tools/gallery`: a página estática de galeria usada na revisão.
- [x] `tools/lucerna_icons`: o `check` (manifesto e SVGs) e o `build` da fonte **"Lucerna Icons"**, com uma ligadura por ícone: `<nome>` para o contorno e `<nome>-fill` para o preenchido.
- [x] Alvo de instalação (`make install`) para `share/fonts/lucerna-icons` e `share/lucerna-icons/svg`.
- [x] O CI (`.github/workflows/ci.yml`): `check` e `build` em PR e no `main`; a release nas tags `v*`.

## O manifesto

```json
{
  "lucideVersion": "0.460.0",
  "icons": [
    {
      "name": "wifi-2",
      "origin": "lucide:wifi",
      "material": ["network_wifi_2_bar"],
      "filled": "own",
      "family": "wifi",
      "status": "aprovado"
    }
  ]
}
```

- `lucideVersion`: a tag do Lucide de onde vêm os derivados. Enquanto nenhum ícone vier do Lucide, pode ficar como `"pendente"`.
- `name`: o nome do Lucerna, em kebab-case (igual ao do Lucide quando derivado); não termina em `-fill`.
- `origin`: `"lucide:<nome>"` ou `"lucerna"`, para os originais.
- `material`: as ligaduras do Material Symbols que ele substitui (cada uma em um só ícone).
- `filled`: `"own"` quando tem `svg/filled/<nome>.svg`; `"outline"` para os sem área a preencher (fechar, setas), em que o `<nome>-fill` mostra o próprio contorno.
- `family`: os estados de uma família (`battery-1`…`battery-8`) levam o mesmo nome aqui, e a família é aprovada junta; `null` quando não tem.
- `status`: `"pendente"` ou `"aprovado"`. Só os aprovados entram na fonte instalada; um pendente pode não ter SVG ainda.

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
sudo make install PREFIX=/usr   # TTFs em $(PREFIX)/share/fonts/lucerna-icons/,
                                # SVGs e manifesto em $(PREFIX)/share/lucerna-icons/
```

Direto pela ferramenta: `PYTHONPATH=tools .venv/bin/python -m lucerna_icons check` e `... build [--all] --out dist/`.

A fonte tem 4 pesos, gerados dos mesmos SVGs com o traço reescrito: traço 1 → `LucernaIcons-ExtraLight.ttf` (200), 1,5 → `Light` (300), 2 → `Regular` (400) e 2,5 → `SemiBold` (600). Os traços viram contornos com o [picosvg](https://github.com/googlefonts/picosvg) e o skia-pathops, e a fonte é montada com o fontTools.

## Como um ícone entra

Nenhum ícone entra no pacote sem ser aprovado, **um de cada vez**:

1. Escolhe-se o próximo ícone do `manifest.json` (começa como `pendente`).
2. Monta-se o contorno, o preenchido e os estados, com o original do Lucide ao lado quando houver.
3. A galeria mostra o ícone em 16, 20, 24 e 28 px, nos temas escuro e claro, num bloco ativo e com a animação do preenchimento, ao lado do Material atual.
4. Só depois da aprovação o ícone vira `aprovado`.

## Licença

O código e os ícones originais são **MIT** (veja [`LICENSE`](LICENSE)).

Os ícones derivados vêm do [Lucide](https://lucide.dev), licenciado sob ISC; os que o Lucide herdou do [Feather](https://feathericons.com) são MIT, de Cole Bemis. O aviso de copyright e o texto integral da licença do Lucide estão em [`LICENSE-LUCIDE`](LICENSE-LUCIDE) e acompanham toda cópia, inclusive as editadas. O `manifest.json` registra, por ícone, o que é derivado do Lucide e o que é original.
