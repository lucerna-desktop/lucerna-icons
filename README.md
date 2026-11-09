# lucerna-icons

Ícones de interface do Lucerna, baseados no Lucide, cada um com **contorno** e **preenchido**. É usado pelo [`lucerna-shell`](https://github.com/lucerna-desktop/lucerna-shell) e pelas interfaces Qt dos apps do ecossistema, para que tudo tenha o mesmo visual.

Baseado no [Lucide](https://lucide.dev).

**Situação:** o repositório acabou de nascer. Ainda não há nenhum ícone nem ferramenta de build; o desenho está no [spec](https://github.com/lucerna-desktop/lucerna-shell/blob/main/docs/superpowers/specs/2026-11-09-lucerna-icons-design.md) do `lucerna-shell`.

## O que é

- **Só os ícones usados.** O pacote cresce sob demanda, quando um ícone novo for preciso; não inclui o Lucide inteiro.
- **Contorno e preenchido.** O Lucide só tem contorno, então o preenchido é desenhado aqui.
- **Variações no nível do Material**: onde o Material Symbols tem mais estados (os 8 níveis da bateria, os do Wi-Fi, o volume), desenhamos os que faltam.
- **Ícones originais** onde o Lucide não tem, na mesma linguagem: grade de 24, traço 2, pontas e junções redondas.
- Só ícones de interface; ícones de aplicativos e de tipos de arquivo do tema do sistema ficam de fora.

## Estrutura prevista

Marcado com `[x]` o que já existe.

- [x] `manifest.json`: uma entrada por ícone (`name`, `origin`, `material`, `status`, variações). Hoje está vazio.
- [ ] `svg/outline/<nome>.svg` e `svg/filled/<nome>.svg`: a fonte da verdade, na grade de 24. Hoje só as pastas existem.
- [ ] `tools/gallery`: a página estática de galeria usada na revisão.
- [ ] A fonte **"Lucerna Icons"**, gerada a partir dos SVGs aprovados, com uma ligadura por ícone: `<nome>` para o contorno e `<nome>-fill` para o preenchido. A ferramenta de build ainda não foi escolhida.
- [ ] Alvo de instalação para `/usr/share/fonts` e `/usr/share/lucerna-icons/svg`.
- [ ] Um check de CI que valida o manifesto e os SVGs.

## Como um ícone entra

Nenhum ícone entra no pacote sem ser aprovado, **um de cada vez**:

1. Escolhe-se o próximo ícone do `manifest.json` (começa como `pendente`).
2. Monta-se o contorno, o preenchido e os estados, com o original do Lucide ao lado quando houver.
3. A galeria mostra o ícone em 16, 20, 24 e 28 px, nos temas escuro e claro, num bloco ativo e com a animação do preenchimento, ao lado do Material atual.
4. Só depois da aprovação o ícone vira `aprovado`.

## Licença

O código e os ícones originais são **MIT** (veja [`LICENSE`](LICENSE)).

Os ícones derivados vêm do [Lucide](https://lucide.dev), licenciado sob ISC; os que o Lucide herdou do [Feather](https://feathericons.com) são MIT, de Cole Bemis. O aviso de copyright e o texto integral da licença do Lucide estão em [`LICENSE-LUCIDE`](LICENSE-LUCIDE) e acompanham toda cópia, inclusive as editadas. O `manifest.json` registra, por ícone, o que é derivado do Lucide e o que é original.
