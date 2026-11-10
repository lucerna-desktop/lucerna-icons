// A galeria de revisão: os controles (câmera lenta, grade, preencher), a
// animação do preenchimento e a detecção do Material Symbols.
(() => {
  "use strict";

  const corpo = document.body;

  const troca = (id, classe) => {
    const caixa = document.getElementById(id);
    if (!caixa) return;
    const aplicar = () => corpo.classList.toggle(classe, caixa.checked);
    caixa.addEventListener("change", aplicar);
    aplicar();
  };
  troca("lento", "lento");
  troca("grade", "com-grade");

  // Preencher: alterna a animação de um bloco de animação (o ícone grande, o
  // Material e o bloco que acende).
  const rotulo = (anima) => {
    const b = anima.querySelector("[data-alternar]");
    if (b) b.textContent = anima.classList.contains("cheio") ? "Esvaziar" : "Preencher";
  };
  const alternar = (anima, cheio) => {
    anima.classList.toggle("cheio", cheio);
    const bloco = anima.querySelector(".bloco.alterna");
    if (bloco) {
      const ligado = anima.classList.contains("cheio");
      bloco.classList.toggle("ativo", ligado);
      bloco.classList.toggle("cheio", ligado);
      const estado = bloco.querySelector("small");
      if (estado) estado.textContent = ligado ? "Ligado" : "Desligado";
    }
    rotulo(anima);
  };
  document.querySelectorAll("[data-alterna]").forEach((anima) => {
    anima.querySelector("[data-alternar]")?.addEventListener("click", () => alternar(anima));
    anima.querySelector(".bloco.alterna")?.addEventListener("click", () => alternar(anima));
  });
  const todos = document.getElementById("alternar-todos");
  todos?.addEventListener("click", () => {
    const encher = todos.dataset.cheio !== "1";
    todos.dataset.cheio = encher ? "1" : "0";
    todos.textContent = encher ? "Esvaziar todos" : "Preencher todos";
    document.querySelectorAll("[data-alterna]").forEach((a) => alternar(a, encher));
  });

  // O Material: o do sistema ("Material local") ou o do Google Fonts. Sem
  // nenhum, as células dele somem e o aviso diz por quê.
  const estado = document.getElementById("material-estado");
  const marcar = (ok, texto) => {
    corpo.classList.toggle("sem-material", !ok);
    if (estado) {
      estado.dataset.estado = ok ? "ok" : "falta";
      estado.textContent = texto;
    }
  };
  const tentar = (familia) =>
    document.fonts.load(`24px "${familia}"`, "home").then((faces) => {
      if (!faces.length) throw new Error(familia);
      return familia;
    });
  const prazo = new Promise((_, nao) => setTimeout(() => nao(new Error("prazo")), 6000));
  window.addEventListener("load", () => {
    Promise.race([
      tentar("Material local").catch(() => tentar("Material Symbols Rounded")),
      prazo,
    ])
      .then((familia) =>
        marcar(true, familia === "Material local" ? "Material: do sistema" : "Material: do Google Fonts"),
      )
      .catch(() => marcar(false, "Material: indisponível (sem a fonte e sem rede)"));
  });
})();
