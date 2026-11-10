# lucerna-icons — Pendências

O que falta fazer no `lucerna-icons`. Cada item vira um PR; ao terminar, ele é marcado aqui. Os concluídos ficam como histórico. O desenho do projeto está no [spec](https://github.com/lucerna-desktop/lucerna-shell/blob/main/docs/superpowers/specs/2026-11-09-lucerna-icons-design.md) do `lucerna-shell`.

- [x] Criar o repositório, com a licença MIT, o `LICENSE-LUCIDE` e o `manifest.json` vazio.
- [x] Escolher a ferramenta de build da fonte e a de conversão de traço em contorno: picosvg + skia-pathops + fontTools (`tools/lucerna_icons`).
- [x] A galeria (`tools/gallery`).
- [x] Um check de CI que valida o manifesto e os SVGs (`make check`, jobs `check` e `build`).
- [x] Alvo de instalação (`make install PREFIX=/usr`).
- [ ] Ligar `check` e `build` como status obrigatórios no ruleset do `main`, depois do primeiro CI verde.
- [x] Fixar a tag do Lucide no `lucideVersion` do manifesto (`1.70.0`).
- [x] O inventário dos ícones do shell (`inventario.md`) e o `fetch` dos que existem no Lucide.
- [ ] Desenhar e aprovar os ícones, em lotes de 10–15, cada um com a família inteira, na ordem do spec: bateria, Wi-Fi, volume, Bluetooth, blocos da central, barra e o resto.
- [ ] Depois de todos aprovados, a migração do `lucerna-shell` (nas Pendências de lá).
