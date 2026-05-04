// static/app.js - Utilitários compartilhados entre todas as páginas
const API = "http://localhost:8000";

// ─────────────────────────────────────────────────────────────
// UTILITÁRIOS DE API
// ─────────────────────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
    try {
        const res = await fetch(`${API}${endpoint}`, {
            headers: { "Content-Type": "application/json", ...options.headers },
            ...options
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Erro desconhecido." }));
            throw new Error(err.detail || `Erro ${res.status}`);
        }
        if (res.status === 204) return null;
        return await res.json();
    } catch (e) {
        throw e;
    }
}

// ─────────────────────────────────────────────────────────────
// NOTIFICAÇÕES (Toast)
// ─────────────────────────────────────────────────────────────
function toast(msg, tipo = "sucesso") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const t = document.createElement("div");
    const cores = {
        sucesso: "bg-emerald-600 border-emerald-400",
        erro:    "bg-red-700 border-red-500",
        aviso:   "bg-amber-600 border-amber-400",
        info:    "bg-blue-700 border-blue-500"
    };
    const icones = { sucesso: "✔", erro: "✖", aviso: "⚠", info: "ℹ" };
    t.className = `toast-item flex items-center gap-3 px-4 py-3 rounded border text-white text-sm font-medium shadow-lg ${cores[tipo]}`;
    t.innerHTML = `<span class="text-lg">${icones[tipo]}</span><span>${msg}</span>`;
    container.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 400); }, 4000);
}

// ─────────────────────────────────────────────────────────────
// MODAL UTILITÁRIO
// ─────────────────────────────────────────────────────────────
function abrirModal(id) { document.getElementById(id).classList.remove("hidden"); }
function fecharModal(id) { document.getElementById(id).classList.add("hidden"); }

// ─────────────────────────────────────────────────────────────
// FORMATADORES
// ─────────────────────────────────────────────────────────────
function fmtData(dt) {
    if (!dt) return "—";
    return new Date(dt).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
function fmtDataCurta(dt) {
    if (!dt) return "—";
    return new Date(dt).toLocaleDateString("pt-BR");
}

// Badge de condição
function badgeCondicao(c) {
    const m = {
        "Novo":                  "badge-verde",
        "Bom":                   "badge-azul",
        "Precisa de Manutenção": "badge-amarelo",
        "Inservível":            "badge-vermelho"
    };
    return `<span class="badge ${m[c] || 'badge-cinza'}">${c}</span>`;
}

// Badge de status policial
function badgeStatus(s) {
    const m = {
        "Ativo":    "badge-verde",
        "Férias":   "badge-amarelo",
        "Licença":  "badge-azul",
        "Inativo":  "badge-cinza"
    };
    return `<span class="badge ${m[s] || 'badge-cinza'}">${s}</span>`;
}

// Badge de cautela
function badgeCautela(s) {
    return s === "Ativa"
        ? `<span class="badge badge-vermelho">● ATIVA</span>`
        : `<span class="badge badge-verde">✔ DEVOLVIDA</span>`;
}

// Highlight de atraso
function isAtrasada(c) {
    return c.status === "Ativa" && c.data_devolucao_prevista && new Date(c.data_devolucao_prevista) < new Date();
}

// ─────────────────────────────────────────────────────────────
// CONSTANTES
// ─────────────────────────────────────────────────────────────
const POSTOS = ["Sd","Cb","Sgt","Sub Ten","Ten","Cap","Maj","TC","Cel"];
const TIPOS_MATERIAL = ["Armamento","Munição","Colete Balístico","Rádio HT","Viatura","Fardamento","Diversos"];
const CONDICOES = ["Novo","Bom","Precisa de Manutenção","Inservível"];
const STATUS_POLICIAL = ["Ativo","Férias","Licença","Inativo"];
