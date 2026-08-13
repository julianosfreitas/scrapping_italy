// Perfil do estudante: cofre de documentos e comparativo das universidades.
//
// Extraído do <script> inline de perfil.html na Sprint 6. O id do dono do
// perfil chega por data-attribute (data-estudante-id) em vez de interpolação
// Jinja, o que mantém este arquivo 100% estático — cacheável pelo navegador e
// compatível com uma Content-Security-Policy sem 'unsafe-inline'.

(() => {
  "use strict";

  const raiz = document.getElementById("perfil");
  if (!raiz) return;

  const donoId = raiz.dataset.estudanteId;
  const token = localStorage.getItem("token");
  const meuId = localStorage.getItem("estudante_id");
  const ehDono = Boolean(token) && String(donoId) === meuId;

  const cofre = document.getElementById("cofre");
  const aviso = document.getElementById("cofre-aviso");

  const rotulos = {
    identidade: "Identidade",
    academico: "Acadêmico",
    financeiro: "Financeiro",
    idioma: "Idioma",
    visto: "Visto",
    outros: "Outros",
  };
  const badges = {
    ok: "bg-verde-claro text-verde",
    vencendo: "bg-amber-100 text-amber-800",
    vencido: "bg-red-100 text-red-800",
  };
  const textoBadge = { ok: "Em dia", vencendo: "Vencendo", vencido: "Vencido" };
  const rotuloStatus = {
    interessado: "Interessado",
    preparando: "Preparando",
    inscrito: "Inscrito",
    aceito: "Aceito",
  };

  const autenticado = (extra = {}) => ({ ...extra, Authorization: "Bearer " + token });

  const escapar = (texto) =>
    String(texto ?? "").replace(
      /[&<>"']/g,
      (caractere) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[caractere],
    );

  async function carregarCofre() {
    if (!ehDono) {
      aviso.textContent = token
        ? "O cofre de documentos é privado: só o dono do perfil pode vê-lo."
        : "Entre na sua conta para ver o cofre de documentos.";
      return;
    }
    document.getElementById("btn-upload").classList.remove("hidden");

    const resposta = await fetch(`/api/estudantes/${donoId}/documentos`, {
      headers: autenticado(),
    });
    if (!resposta.ok) {
      aviso.textContent = "Sessão expirada — entre novamente.";
      return;
    }

    const documentos = await resposta.json();
    if (documentos.length === 0) {
      aviso.textContent = "Nenhum documento no cofre ainda.";
      return;
    }
    aviso.classList.add("hidden");

    const porCategoria = {};
    for (const documento of documentos) {
      (porCategoria[documento.categoria] ??= []).push(documento);
    }

    cofre.innerHTML = Object.entries(porCategoria)
      .map(
        ([categoria, docs]) => `
      <div>
        <h3 class="text-sm font-bold uppercase tracking-wide text-gray-500">${escapar(rotulos[categoria] ?? categoria)}</h3>
        <div class="mt-3 grid gap-3 sm:grid-cols-2">
          ${docs
            .map(
              (d) => `
            <div class="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-semibold">${escapar(d.tipo)}</p>
                  <p class="text-xs text-gray-500 mt-0.5">${escapar(d.nome_arquivo)}</p>
                  ${d.data_validade ? `<p class="text-xs text-gray-500 mt-0.5">Válido até ${escapar(d.data_validade)}</p>` : ""}
                </div>
                <span class="rounded-full px-3 py-1 text-xs font-semibold ${badges[d.status]}">${textoBadge[d.status]}</span>
              </div>
              <button data-doc="${d.id}" class="baixar mt-4 text-sm font-semibold text-verde hover:underline focus:outline-none focus:ring-2 focus:ring-verde rounded">Baixar</button>
            </div>`,
            )
            .join("")}
        </div>
      </div>`,
      )
      .join("");

    for (const botao of document.querySelectorAll(".baixar")) {
      botao.addEventListener("click", async () => {
        const url = await fetch(`/api/documentos/${botao.dataset.doc}/url-assinada`, {
          headers: autenticado(),
        });
        if (url.ok) window.open((await url.json()).url, "_blank", "noopener");
      });
    }
  }

  async function carregarMinhasUniversidades() {
    const avisoUnis = document.getElementById("unis-aviso");
    const alvo = document.getElementById("minhas-unis");
    if (!ehDono) {
      avisoUnis.textContent = token
        ? "A lista de universidades é privada: só o dono do perfil pode vê-la."
        : "Entre na sua conta para acompanhar suas universidades.";
      return;
    }

    const resposta = await fetch(`/api/estudantes/${donoId}/universidades`, {
      headers: autenticado(),
    });
    if (!resposta.ok) {
      avisoUnis.textContent = "Sessão expirada — entre novamente.";
      return;
    }

    const minhas = await resposta.json();
    if (minhas.length === 0) {
      avisoUnis.innerHTML =
        'Nenhum curso salvo ainda — explore as ' +
        '<a href="/universidades" class="font-semibold text-verde hover:underline">universidades</a>.';
      return;
    }
    avisoUnis.classList.add("hidden");

    const itemGap = (itens, cor, icone) =>
      itens
        .map(
          (i) => `
      <li class="flex items-start gap-2 text-sm"><span class="${cor} font-bold" aria-hidden="true">${icone}</span>
        <span>${escapar(i.descricao)}${i.documentos.length ? ` <span class="text-xs text-gray-500">(${escapar(i.documentos.join(", "))})</span>` : ""}</span>
      </li>`,
        )
        .join("");

    alvo.innerHTML = minhas
      .map(
        (m) => `
      <div class="rounded-2xl bg-white border border-gray-100 p-6 shadow-sm">
        <div class="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h3 class="font-bold">${escapar(m.curso.nome)}</h3>
            <p class="text-sm text-gray-600">${escapar(m.universidade.nome)} · ${escapar(m.universidade.cidade)}</p>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            ${
              m.alerta_prazo && m.curso.prazo_proximo
                ? '<span class="rounded-full bg-amber-100 text-amber-800 px-3 py-1 text-xs font-semibold">⏰ Prazo próximo</span>'
                : ""
            }
            <span class="rounded-full bg-gray-100 text-gray-600 px-3 py-1 text-xs font-semibold">${rotuloStatus[m.status]}</span>
            <span class="rounded-full bg-verde-claro text-verde px-3 py-1 text-xs font-semibold">${m.gap.percentual_pronto}% pronto</span>
          </div>
        </div>
        <div class="mt-3 h-2 rounded-full bg-gray-100 overflow-hidden"
             role="progressbar" aria-valuenow="${m.gap.percentual_pronto}" aria-valuemin="0" aria-valuemax="100"
             aria-label="Prontidão da documentação">
          <div class="h-full bg-verde" style="width:${m.gap.percentual_pronto}%"></div>
        </div>
        <ul class="mt-4 space-y-1.5">
          ${itemGap(m.gap.atendidos, "text-verde", "✓")}
          ${itemGap(m.gap.vencendo, "text-amber-600", "!")}
          ${itemGap(m.gap.faltando, "text-red-600", "✗")}
        </ul>
      </div>`,
      )
      .join("");
  }

  document
    .getElementById("btn-upload")
    .addEventListener("click", () =>
      document.getElementById("form-upload").classList.toggle("hidden"),
    );

  document.getElementById("form-upload").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const erro = document.getElementById("erro-upload");
    erro.classList.add("hidden");

    const dados = new FormData();
    dados.append("arquivo", document.getElementById("arquivo").files[0]);
    dados.append("categoria", document.getElementById("categoria").value);
    dados.append("tipo", document.getElementById("tipo").value);
    const validade = document.getElementById("validade").value;
    if (validade) dados.append("data_validade", validade);

    const resposta = await fetch(`/api/estudantes/${donoId}/documentos`, {
      method: "POST",
      headers: autenticado(),
      body: dados,
    });
    if (!resposta.ok) {
      erro.textContent = (await resposta.json()).detail || "Falha no envio";
      erro.classList.remove("hidden");
      return;
    }

    const formulario = document.getElementById("form-upload");
    formulario.reset();
    formulario.classList.add("hidden");
    carregarCofre();
  });

  carregarMinhasUniversidades();
  carregarCofre();
})();
