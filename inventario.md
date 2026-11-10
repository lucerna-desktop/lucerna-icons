# Inventário dos ícones do shell

Todos os ícones que o `lucerna-shell` usa hoje, com o que vai substituir cada um. Fonte: `core/widgets/Icons.qml` e as ligaduras escritas direto nas telas (`icon: "..."`, os estados de Wi-Fi, bateria e volume, os ícones do tempo e dos dispositivos Bluetooth, os atalhos de `core/input/InputActions.qml`), no `main` do shell em 2026-11-09.

Os derivados vêm do **Lucide 1.70.0** (o `lucideVersion` do `manifest.json`). Tudo entra como `pendente`; a aprovação é do usuário, em lotes, na galeria.

Como ler:

- **Material**: as ligaduras do Material Symbols que o ícone substitui (às vezes mais de uma, quando o shell usa duas para o mesmo desenho).
- **Lucerna**: o nome no pacote (a ligadura nova). Igual ao do Lucide quando derivado; os estados têm sufixo numérico (`battery-0`…`battery-4`, `wifi-0`…`wifi-3`, `volume-0`…`volume-2`).
- **Lucide**: o ícone de origem, ou **desenhar** quando o Lucide não tem. ≈ marca um equivalente aproximado, a conferir na galeria.
- **filled**: `own` tem área para preencher (o preenchido é desenhado aqui, porque o Lucide só tem contorno); `outline` não tem, e o `-fill` mostra o próprio contorno.
- **Família**: os estados aprovados juntos.

## Barra

Os indicadores da barra (rede, volume, bateria) e as ações dela.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `battery_0_bar` | `battery-0` | **desenhar** (do `battery`) | outline | battery | vazia |
| `battery_1_bar`, `battery_2_bar` | `battery-1` | **desenhar** (do `battery`) | outline | battery | 25 % (preenchimento contínuo) |
| `battery_3_bar`, `battery_4_bar` | `battery-2` | **desenhar** (do `battery`) | outline | battery | 50 % |
| `battery_5_bar`, `battery_6_bar` | `battery-3` | **desenhar** (do `battery`) | outline | battery | 75 % |
| `battery_full` | `battery-4` | **desenhar** (do `battery`) | outline | battery | cheia: o corpo inteiro sólido |
| — | `battery-charging-0` | **desenhar** (do `battery-charging`) | outline | battery | carregando, vazia: o raio sólido no lado direito, recortando o corpo |
| — | `battery-charging-1` | **desenhar** (do `battery-charging`) | outline | battery | carregando, 25 %: o raio no lado direito, recortando o corpo e o preenchimento |
| — | `battery-charging-2` | **desenhar** (do `battery-charging`) | outline | battery | carregando, 50 % |
| — | `battery-charging-3` | **desenhar** (do `battery-charging`) | outline | battery | carregando, 75 % |
| `battery_charging_full` | `battery-charging-4` | **desenhar** (do `battery-charging`) | outline | battery | carregando, cheia |
| `battery_alert` | `battery-exclamation-point` | **desenhar** (do `battery-exclamation-point`) | outline | battery | bateria baixa: o corpo cheio com a “!” recortada |
| `signal_wifi_0_bar` | `wifi-0` | `wifi-zero` | outline | wifi | só o ponto |
| `network_wifi_1_bar` | `wifi-1` | `wifi-low` | outline | wifi | 1 arco |
| `network_wifi_2_bar`, `network_wifi_3_bar` | `wifi-2` | `wifi-high` | outline | wifi | 2 arcos; o Material tem 5 níveis e o Lucide 4, então o shell passa a dividir o sinal em 4 faixas na migração |
| `signal_wifi_4_bar`, `wifi` | `wifi-3` | `wifi` | outline | wifi | cheio (3 arcos); também o bloco do Wi-Fi ligado (wifiOn) |
| `wifi_off` | `wifi-off` | `wifi-off` | outline | wifi |  |
| `signal_wifi_bad` | `wifi-alert` | **desenhar** | outline | wifi | sem internet (offline): Wi-Fi com “!” |
| `lan` | `network` | `network` ≈ | own | — | cabo (ethernet) |
| `volume_mute` | `volume-0` | `volume` | own | volume | volume baixo: só o alto-falante |
| `volume_down` | `volume-1` | `volume-1` | own | volume | volume médio; também “abaixar o volume” |
| `volume_up` | `volume-2` | `volume-2` | own | volume | volume alto; também “aumentar o volume” |
| `volume_off` | `volume-off` | `volume-off` | own | volume | mudo |
| `sports_esports` | `gamepad-2` | `gamepad-2` | own | — | modo jogo |
| `stop` | `square` | `square` | own | — | parar a gravação |

## Notificações

O sino da barra e da central, e limpar tudo.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `notifications` | `bell` | `bell` | own | bell |  |
| `notifications_active` | `bell-ring` | `bell-ring` | own | bell | há notificações |
| `notifications_paused` | `bell-snooze` | **desenhar** | own | bell | não perturbe: sino com “z”; o Lucide só tem o bell-off |
| `delete_sweep` | `brush-cleaning` | `brush-cleaning` ≈ | own | — | limpar o histórico (o `clear_all` do `Icons.clearAll` não tem uso) |

## Central (Ações)

Os blocos, as páginas de Bluetooth, som e energia.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `bluetooth` | `bluetooth` | `bluetooth` | outline | bluetooth |  |
| `bluetooth_connected` | `bluetooth-connected` | `bluetooth-connected` | outline | bluetooth |  |
| `bluetooth_disabled` | `bluetooth-off` | `bluetooth-off` | outline | bluetooth |  |
| `bluetooth_searching` | `bluetooth-searching` | `bluetooth-searching` | outline | bluetooth |  |
| `headphones` | `headphones` | `headphones` | own | — | dispositivo Bluetooth |
| `headset_mic` | `headset` | `headset` | own | — | dispositivo Bluetooth |
| `keyboard` | `keyboard` | `keyboard` | own | — | dispositivo Bluetooth |
| `gamepad` | `gamepad-directional` | `gamepad-directional` | own | — | dispositivo Bluetooth (controle) |
| `smartphone` | `smartphone` | `smartphone` | own | — | dispositivo Bluetooth |
| `watch` | `watch` | `watch` | own | — | dispositivo Bluetooth |
| `computer` | `laptop` | `laptop` ≈ | own | — | dispositivo Bluetooth (o Material computer é um notebook) |
| `tv` | `tv` | `tv` | own | — | dispositivo Bluetooth |
| `speaker` | `speaker` | `speaker` | own | — | saída de som / dispositivo |
| `mic` | `mic` | `mic` | own | — |  |
| `mic_off` | `mic-off` | `mic-off` | own | — |  |
| `graphic_eq` | `audio-lines` | `audio-lines` | outline | — | som |
| `tune` | `sliders-horizontal` | `sliders-horizontal` | outline | — | a central; ajustes |
| `view_sidebar` | `panel-right` | `panel-right` | own | — | as Ações e as Notificações juntas |
| `eco` | `leaf` | `leaf` | own | — | perfil economia |
| `balance` | `scale` | `scale` | own | — | perfil equilibrado |
| `rocket_launch` | `rocket` | `rocket` | own | — | perfil desempenho |
| `electric_bolt` | `zap` | `zap` | own | — | carregando / energia |
| `sync` | `refresh-ccw` | `refresh-ccw` ≈ | outline | — | sincronizar |
| `coffee` | `coffee` | `coffee` | own | — | cafeína |
| `nightlight` | `moon-star` | `moon-star` | own | — | luz noturna |
| `delete` | `trash` | `trash` | own | — | esquecer / apagar |
| `cloud_off` | `cloud-off` | `cloud-off` | own | — | modo offline |

## OSD e brilho

O brilho no OSD e na central.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `brightness_low` | `sun-dim` | `sun-dim` | own | brightness |  |
| `brightness_medium` | `sun-medium` | `sun-medium` | own | brightness |  |
| `brightness_high`, `sunny`, `wb_sunny` | `sun` | `sun` | own | brightness | também o tempo ensolarado e o “desliga às” da luz noturna |

## Painel superior

O painel, a mídia, o desempenho e o clima.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `dashboard` | `layout-dashboard` | `layout-dashboard` | own | — |  |
| `music_note` | `eighth-note` | `eighth-note` | own | — | mídia (o music do Lucide virou eighth-note no 1.x) |
| `music_off` | `eighth-note-off` | **desenhar** | own | — | sem mídia: a nota com um corte |
| `play_arrow` | `play` | `play` | own | — |  |
| `pause` | `pause` | `pause` | own | — |  |
| `skip_next` | `skip-forward` | `skip-forward` | own | — |  |
| `skip_previous` | `skip-back` | `skip-back` | own | — |  |
| `lyrics` | `mic-vocal` | `mic-vocal` ≈ | own | — | letra da música |
| `album` | `disc` | `disc` ≈ | own | — |  |
| `speed` | `gauge` | `gauge` | outline | — | desempenho; taxa de atualização; velocidade do ponteiro |
| `developer_board` | `cpu` | `cpu` | own | — |  |
| `memory_alt` | `memory-stick` | `memory-stick` | own | — |  |
| `hard_drive` | `hard-drive` | `hard-drive` | own | — |  |
| `videogame_asset` | `gamepad` | `gamepad` ≈ | own | — | GPU |
| `swap_vert` | `arrow-down-up` | `arrow-down-up` | outline | — | rede |
| `download` | `download` | `download` | outline | — |  |
| `upload` | `upload` | `upload` | outline | — |  |
| `device_thermostat`, `thermostat` | `thermometer` | `thermometer` | own | — | temperatura; também a da luz noturna |
| `schedule` | `clock` | `clock` | own | — | tempo ligado |
| `calendar_month` | `calendar-days` | `calendar-days` | own | — |  |
| `person` | `user` | `user` | own | — |  |
| `location_on` | `map-pin` | `map-pin` | own | — |  |
| `cloud` | `cloud` | `cloud` | own | — | clima; nublado |
| `partly_cloudy_day` | `cloud-sun` | `cloud-sun` | own | — |  |
| `partly_cloudy_night` | `cloud-moon` | `cloud-moon` | own | — |  |
| `foggy` | `cloud-fog` | `cloud-fog` | own | — |  |
| `rainy_light` | `cloud-drizzle` | `cloud-drizzle` | own | — |  |
| `rainy` | `cloud-rain` | `cloud-rain` | own | — |  |
| `rainy_heavy` | `cloud-rain-wind` | `cloud-rain-wind` | own | — | chuva forte |
| `weather_hail` | `cloud-hail` | `cloud-hail` | own | — |  |
| `weather_snowy` | `cloud-snow` | `cloud-snow` | own | — |  |
| `thunderstorm` | `cloud-lightning` | `cloud-lightning` | own | — |  |
| `humidity_percentage` | `droplets` | `droplets` | own | — | umidade |
| `air` | `wind` | `wind` | outline | — | vento |
| `wb_twilight` | `sunrise` | `sunrise` | own | — | nascer do sol |

## Energia, bloqueio e sessão

O menu de energia, a tela de bloqueio e o modo de segurança.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `power_settings_new` | `power` | `power` | outline | — |  |
| `logout` | `log-out` | `log-out` | outline | — |  |
| `restart_alt` | `rotate-ccw` | `rotate-ccw` | outline | — | reiniciar |
| `bedtime`, `clear_night` | `moon` | `moon` | own | — | suspender; também a noite limpa e o pôr do sol |
| `lock` | `lock` | `lock` | own | — |  |
| `warning` | `triangle-exclamation-point` | `triangle-exclamation-point` | own | — | modo de segurança |
| `terminal` | `square-terminal` | `square-terminal` ≈ | own | — | o terminal do Lucide é só “>_”; este tem a moldura, como o Material |

## Lançador

O lançador, a busca de arquivos e a web.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `apps` | `layout-grid` | `layout-grid` | own | — |  |
| `widgets` | `blocks` | `blocks` | own | — | aplicativo |
| `search` | `search` | `search` | outline | — |  |
| `folder` | `folder` | `folder` | own | — |  |
| `folder_open` | `folder-open` | `folder-open` | own | — |  |
| `description` | `file-text` | `file-text` | own | — | documento |
| `picture_as_pdf` | `file-pdf` | **desenhar** | own | — | o Lucide não tem PDF |
| `folder_zip` | `folder-archive` | `folder-archive` | own | — | arquivo compactado |
| `image` | `image` | `image` | own | — |  |
| `movie` | `clapperboard` | `clapperboard` | own | — | vídeo |
| `language` | `globe` | `globe` | outline | — | web; layout do teclado |
| `travel_explore` | `earth` | `earth` ≈ | outline | — | pesquisar na web |
| `history` | `rotate-ccw-clock` | `rotate-ccw-clock` | outline | — | recentes (o history do Lucide virou rotate-ccw-clock) |
| `hourglass_top` | `hourglass` | `hourglass` | own | — | buscando |
| `star`, `star_outline` | `star` | `star` | own | — | favorito: o star_outline é o contorno, o star é o -fill |
| `visibility_off` | `eye-off` | `eye-off` | own | — | ocultar |
| `content_copy` | `copy` | `copy` | own | — | copiar |
| `keyboard_return` | `corner-down-left` | `corner-down-left` | outline | — | Enter |
| `arrow_forward`, `east` | `arrow-right` | `arrow-right` | outline | — | também a direção “à direita” dos atalhos |

## Captura de tela

A barra de ferramentas da captura.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `photo_camera` | `camera` | `camera` | own | — |  |
| `videocam` | `video` | `video` | own | — |  |
| `crop_free` | `scan` | `scan` | outline | — | área |
| `select_window` | `app-window` | `app-window` ≈ | own | — | janela |
| `fit_screen` | `fullscreen` | `fullscreen` | own | — | tela inteira |
| `screenshot_region` | `square-dashed` | `square-dashed` ≈ | outline | — | capturar (atalho e configuração) |
| `screen_record` | `screen-record` | **desenhar** | own | — | gravar: o ponto de gravação entre cantos |
| `radio_button_checked` | `circle-dot` | `circle-dot` | own | — | gravando |
| `arrow_selector_tool` | `mouse-pointer` | `mouse-pointer` | own | — | mostrar o ponteiro |
| `timer` | `timer` | `timer` | own | — | também a ociosidade e o modo jogo |

## Área de transferência

O histórico e a página dele nas configurações.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `content_paste` | `clipboard` | `clipboard` | own | clipboard |  |
| `content_paste_go` | `clipboard-paste` | `clipboard-paste` | own | clipboard | colar ao escolher |
| `content_paste_off` | `clipboard-off` | **desenhar** | own | clipboard | histórico desligado: a prancheta com um corte |
| `notes` | `text-align-start` | `text-align-start` ≈ | outline | — | item de texto |
| `format_list_numbered` | `list-ordered` | `list-ordered` | outline | — | quantos guardar |

## Atalhos e áreas de trabalho

As ações dos atalhos e a visão geral.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `counter_1`, `looks_one` | `counter-1` | **desenhar** | own | counter | área de trabalho 1; também identificar o monitor |
| `counter_2` | `counter-2` | **desenhar** | own | counter | o Lucide não tem números em forma |
| `counter_3` | `counter-3` | **desenhar** | own | counter |  |
| `counter_4` | `counter-4` | **desenhar** | own | counter |  |
| `counter_5` | `counter-5` | **desenhar** | own | counter |  |
| `counter_6` | `counter-6` | **desenhar** | own | counter |  |
| `counter_7` | `counter-7` | **desenhar** | own | counter |  |
| `counter_8` | `counter-8` | **desenhar** | own | counter |  |
| `counter_9` | `counter-9` | **desenhar** | own | counter |  |
| `north`, `arrow_upward` | `arrow-up` | `arrow-up` | outline | — | também “subir uma pasta” |
| `south` | `arrow-down` | `arrow-down` | outline | — |  |
| `west` | `arrow-left` | `arrow-left` | outline | — |  |
| `move_item` | `square-arrow-right-enter` | `square-arrow-right-enter` ≈ | outline | — | mover a janela para a área |
| `drag_pan` | `move` | `move` | outline | — | arrastar a janela |
| `open_in_full` | `maximize-2` | `maximize-2` | outline | — | redimensionar a janela |
| `fullscreen` | `maximize` | `maximize` | outline | — | tela cheia |
| `picture_in_picture` | `picture-in-picture-2` | `picture-in-picture-2` | own | — | flutuar |
| `keep` | `pin` | `pin` | own | — | fixar |
| `first_page` | `chevron-first` | `chevron-first` | outline | — | área anterior |
| `last_page` | `chevron-last` | `chevron-last` | outline | — | próxima área |
| `block` | `ban` | `ban` | outline | — | nenhuma ação |
| `overview_key` | `gallery-horizontal` | `gallery-horizontal` ≈ | own | — | visão geral |
| `keyboard_command_key` | `command` | `command` | outline | — | atalho de teclado; tecla compose |

## Configurações

As páginas das configurações.

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `settings` | `settings` | `settings` | own | — |  |
| `palette` | `palette` | `palette` | own | — | temas |
| `wallpaper` | `wallpaper` | `wallpaper` | own | — |  |
| `add_photo_alternate` | `image-plus` | `image-plus` | own | — | adicionar papel de parede |
| `desktop_windows` | `monitor` | `monitor` | own | — |  |
| `desktop_access_disabled` | `monitor-off` | `monitor-off` | own | — | desligar a tela |
| `aspect_ratio` | `proportions` | `proportions` ≈ | outline | — | resolução |
| `zoom_in` | `zoom-in` | `zoom-in` | outline | — | escala |
| `screen_rotation` | `rotate-ccw-square` | `rotate-ccw-square` ≈ | outline | — | girar a tela |
| `screen_share` | `screen-share` | `screen-share` | own | — | espelhar |
| `motion_blur` | `motion-blur` | **desenhar** | own | — | VRR: o círculo com rastro de movimento |
| `gradient` | `swatch-book` | `swatch-book` ≈ | own | — | profundidade de cor |
| `stacks` | `layers` | `layers` | own | — | painéis |
| `toolbar` | `panel-top` | `panel-top` ≈ | own | — | barra |
| `blur_on` | `blur` | **desenhar** | outline | blur | desfoque: a grade de pontos |
| `blur_off` | `blur-off` | **desenhar** | outline | blur | sem desfoque |
| `opacity` | `blend` | `blend` ≈ | outline | — | transparência |
| `animation` | `animation` | **desenhar** | outline | — | animações: os círculos em sequência |
| `mouse` | `mouse` | `mouse` | own | — | também o dispositivo Bluetooth |
| `touchpad_mouse` | `touchpad` | `touchpad` | own | — |  |
| `swap_horiz` | `arrow-left-right` | `arrow-left-right` | outline | — | trocar os botões; também na mídia |
| `keyboard_double_arrow_right` | `chevrons-right` | `chevrons-right` | outline | — | repetição de tecla |
| `swipe_vertical` | `move-vertical` | `move-vertical` ≈ | outline | — | rolagem |
| `touch_app` | `pointer` | `pointer` | own | — | toque para clicar |
| `back_hand` | `hand` | `hand` | own | — | canhoto |
| `ads_click` | `mouse-pointer-click` | `mouse-pointer-click` | own | — | foco segue o mouse |
| `dialpad` | `grip` | `grip` | outline | — | Num Lock |
| `settings_backup_restore` | `refresh-ccw-dot` | `refresh-ccw-dot` | outline | — | restaurar o padrão |
| `volunteer_activism` | `hand-heart` | `hand-heart` | own | — | créditos |
| `playlist_add_check` | `list-check` | `list-check` | outline | — | lista de jogos |
| `playlist_remove` | `list-x` | `list-x` | outline | — | lista de exceções |
| `info` | `info` | `info` | own | — | sobre |
| `open_in_new` | `external-link` | `external-link` | outline | — | abrir fora |

## Comuns

Os controles usados em várias telas (fechar, confirmar, expandir…).

| Material | Lucerna | Lucide | filled | Família | Observação |
|---|---|---|---|---|---|
| `close` | `x` | `x` | outline | — |  |
| `check` | `check` | `check` | outline | — |  |
| `cancel` | `circle-x` | `circle-x` | own | — | limpar a busca |
| `add` | `plus` | `plus` | outline | — |  |
| `edit` | `pencil` | `pencil` | own | — |  |
| `refresh` | `refresh-cw` | `refresh-cw` | outline | — |  |
| `chevron_left` | `chevron-left` | `chevron-left` | outline | — |  |
| `chevron_right` | `chevron-right` | `chevron-right` | outline | — |  |
| `expand_more`, `keyboard_arrow_down` | `chevron-down` | `chevron-down` | outline | — | expandir; descer na lista |
| `keyboard_arrow_up` | `chevron-up` | `chevron-up` | outline | — | subir na lista |

## Resumo

| | Ícones |
|---|---|
| Total de ícones (glifos de contorno) | 200 |
| Ligaduras do Material substituídas | 210 |
| Vindos do Lucide | 170 |
| Aproximados (≈), a conferir | 20 |
| Para desenhar (contorno novo) | 30 |
| Com preenchido (`own`) | 124 |
| … dos quais o contorno também é para desenhar | 15 |
| Sem preenchido próprio (`outline`, o `-fill` usa o contorno: sem área, e a família `battery`) | 76 |

Todo preenchido é desenhado aqui, porque o Lucide só tem contorno: são **124 preenchidos para desenhar** (109 sobre um contorno do Lucide e 15 sobre um contorno novo). Somando os 30 contornos novos, são **154 desenhos** ao todo, além dos ajustes que a galeria pedir.

Nomes do Lucide terminados em dígito que não são estados: `gamepad-2` e `picture-in-picture-2` (variantes do Lucide, sem relação com uma família `gamepad` ou `picture-in-picture`). `volume-1` e `volume-2` são do Lucide e também são estados da família `volume`.

**Fora do pacote.** Cinco propriedades do `Icons.qml` não têm uso no shell e saíram do inventário: `soon`/`auto_awesome` (`sparkles`), `unlink`/`link_off` (`unlink`), `lockOpen`/`lock_open` (`lock-open`), `rain`/`water_drop` (`droplet`) e `clearAll`/`clear_all` (só a ligadura; o `brush-cleaning` fica por causa do `delete_sweep`). Elas saem do `Icons.qml` na migração do shell.

**Bateria com 5 níveis.** A bateria é desenho nosso, derivado do `battery` do Lucide: deitada, mais fina e comprida (corpo de 8 de altura), com o polo curto colado no corpo como no Material e 5 níveis (`battery-0` a `battery-4`). Sem células: o nível é um preenchimento sólido contínuo da esquerda até 0, 25, 50, 75 ou 100 %, colado ao traço do corpo (sem vão), como no Material; a borda direita é reta, e o `battery-4` é o corpo inteiro sólido. O nível é a mesma fração do interior em todos os pesos: como o traço engrossa para dentro, a parte da borda que depende do peso é um traço vertical de largura 1 (no traço 2), somado ao preenchimento nos 25 % e recortado dele na máscara nos 75 %, e o build o engrossa como qualquer traço. A carga mostra o nível, como no Material (`battery_charging_20`…`full`): em `battery-charging-0` a `-4`, um raio sólido na diagonal (a ponta de cima à direita) fica no lado direito do corpo, junto do polo, como no `battery_android_frame_bolt` do Material Symbols, e recorta o contorno, o polo e o preenchimento em volta dele, com um vão de 1,25 no traço 2. O vão e o raio (forma cheia mais um traço do mesmo contorno) são traços, e por isso crescem com o peso. O preenchimento à esquerda fica livre para mostrar o nível. O alerta (`battery-exclamation-point`) é o corpo cheio com a "!" recortada, cheio por ser um estado de alerta. O shell passa a dividir a porcentagem em 5 faixas na migração e, carregando, escolhe a variante de carga pelo mesmo nível (`battery-charging-N`); e duas ligaduras do Material vão para o mesmo nível. A família inteira tem o preenchido igual ao contorno, como no Material; o nível é o preenchimento (`filled: outline`, o `-fill` mostra o contorno).

**Wi-Fi com 4 níveis.** O Lucide tem 4 níveis (`wifi-0` a `wifi-3`, de 0 a 3 arcos), então o shell passa a dividir o sinal em 4 faixas na migração. O `wifi-alert` continua a desenhar.
