// ==========================================
// CONFIGURAÇÕES BASE
// ==========================================
const API = "/api";

// ==========================================
// SEGURANÇA E AUTENTICAÇÃO
// ==========================================
function getToken() {
    const token = sessionStorage.getItem("pm_token") || localStorage.getItem("pm_token");
    const expiresAt = parseInt(sessionStorage.getItem("pm_expires_at") || localStorage.getItem("pm_expires_at") || "0");
    
    if (!token || Date.now() >= expiresAt) return null;
    return token;
}

function logout() {
    sessionStorage.removeItem("pm_token");
    sessionStorage.removeItem("pm_expires_at");
    localStorage.removeItem("pm_token");
    localStorage.removeItem("pm_expires_at");
    
    window.location.href = "/login/";
}

function requireAuth() {
    if (!getToken()) {
        logout();
    }
}

// ==========================================
// COMUNICAÇÃO COM O BANCO DE DADOS (Rádio Blindado)
// ==========================================
/**
 * 🛡️ HARDENED API FETCH (Zero Trust Edition)
 */
async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    if (!token) {
        logout();
        return;
    }

    endpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    if (!endpoint.endsWith('/') && !endpoint.includes('?')) {
        endpoint += '/';
    }
    const url = `${API}/${endpoint}`;

    try {
        const res = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
                ...options.headers,
            },
            ...options,
        });

        if (res.status === 401) {
            logout();
            return;
        }

        if (!res.ok) {
            const err = await res.json().catch(() => ({
                detail: `HTTP ${res.status}: ${res.statusText}`
            }));
            throw new Error(err.detail || `Erro ${res.status}`);
        }

        if (res.status === 204) return null;
        return await res.json();
    } catch (e) {
        if (e.message === "Failed to fetch") {
            throw new Error("Servidor offline ou inacessível. Verifique sua conexão.");
        }
        throw e;
    }
}

// ==========================================
// UTILITÁRIOS E INTERFACE (UI)
// ==========================================
function toast(msg, tipo = "sucesso") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const t = document.createElement("div");
    const cores = {
        sucesso: "bg-emerald-600 border-emerald-400",
        erro: "bg-red-700 border-red-500",
        aviso: "bg-amber-600 border-amber-400",
        info: "bg-blue-700 border-blue-500"
    };
    const icones = { sucesso: "✔", erro: "✖", aviso: "⚠", info: "ℹ" };
    t.className = `toast-item flex items-center gap-3 px-4 py-3 rounded border text-white text-sm font-medium shadow-lg ${cores[tipo]}`;
    t.innerHTML = `<span class="text-lg">${icones[tipo]}</span><span>${msg}</span>`;
    container.appendChild(t);
    setTimeout(() => {
        t.style.opacity = "0";
        setTimeout(() => t.remove(), 400);
    }, 4000);
}

function abrirModal(id) { document.getElementById(id).classList.remove("hidden"); }
function fecharModal(id) { document.getElementById(id).classList.add("hidden"); }

function fmtData(dt) {
    return !dt ? "—" : new Date(dt).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function fmtDataCurta(dt) {
    return !dt ? "—" : new Date(dt).toLocaleDateString("pt-BR");
}

function badgeCondicao(c) {
    const m = { "Novo": "badge-verde", "Bom": "badge-azul", "Precisa de Manutenção": "badge-amarelo", "Inservível": "badge-vermelho" };
    return `<span class="badge ${m[c] || 'badge-cinza'}">${c}</span>`;
}

function badgeStatus(s) {
    const m = { "Ativo": "badge-verde", "Férias": "badge-amarelo", "Licença": "badge-azul", "Inativo": "badge-cinza" };
    return `<span class="badge ${m[s] || 'badge-cinza'}">${s}</span>`;
}

function badgeCautela(s) {
    return s === "Ativa" ? `<span class="badge badge-vermelho">● ATIVA</span>` : `<span class="badge badge-verde">✔ DEVOLVIDA</span>`;
}

function isAtrasada(c) {
    return c.status === "Ativa" && c.data_devolucao_prevista && new Date(c.data_devolucao_prevista) < new Date();
}

// ==========================================
// CONSTANTES DO SISTEMA
// ==========================================
const POSTOS = ["Sd","Cb","Sgt","Sub Ten","Ten","Cap","Maj","TC","Cel"];
const TIPOS_MATERIAL = ["Armamento","Munição","Colete Balístico","Rádio HT","Viatura","Fardamento","Diversos"];
const CONDICOES = ["Novo","Bom","Precisa de Manutenção","Inservível"];
const STATUS_POLICIAL = ["Ativo","Férias","Licença","Inativo"];