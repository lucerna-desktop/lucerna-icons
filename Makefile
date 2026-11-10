# lucerna-icons: validação, build da fonte e instalação.
#
# As dependências Python ficam num .venv local (`make venv`), criado sozinho
# pelos outros alvos quando falta. Nada é instalado no sistema.

PYTHON ?= python3
VENV   := .venv
PY     := $(VENV)/bin/python
RUN    := PYTHONPATH=tools $(PY) -m lucerna_icons

PREFIX  ?= /usr/local
DESTDIR ?=
FONTDIR := $(DESTDIR)$(PREFIX)/share/fonts/lucerna-icons
DATADIR := $(DESTDIR)$(PREFIX)/share/lucerna-icons

DIST     := dist
DISTALL  := $(DIST)/todos

.PHONY: venv deps check check-tests test build build-all install uninstall clean

# O venv é refeito quando o requirements.txt muda.
$(VENV)/.ok: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements.txt
	touch $@

venv deps: $(VENV)/.ok

# Valida o manifesto e os SVGs.
check: $(VENV)/.ok
	$(RUN) check

# Os testes (pytest).
check-tests test: $(VENV)/.ok
	$(PY) -m pytest -q

# A fonte e os SVGs só dos ícones aprovados, em dist/: o que se instala e o
# que vai para a release.
build: $(VENV)/.ok
	rm -rf $(DIST)/*.ttf $(DIST)/svg $(DIST)/manifest.json
	$(RUN) build --out $(DIST)

# Inclui os pendentes, para a galeria; vai para dist/todos e nunca é instalado.
build-all: $(VENV)/.ok
	rm -rf $(DISTALL)
	$(RUN) build --all --out $(DISTALL)

install: build
	install -d $(FONTDIR) $(DATADIR)/svg/outline $(DATADIR)/svg/filled
	install -m644 $(DIST)/*.ttf $(FONTDIR)/
	install -m644 $(DIST)/manifest.json $(DATADIR)/manifest.json
	for tipo in outline filled; do \
	  for f in $(DIST)/svg/$$tipo/*.svg; do \
	    [ -e "$$f" ] || continue; \
	    install -m644 "$$f" $(DATADIR)/svg/$$tipo/; \
	  done; \
	done

uninstall:
	rm -rf $(FONTDIR) $(DATADIR)

clean:
	rm -rf $(DIST)
