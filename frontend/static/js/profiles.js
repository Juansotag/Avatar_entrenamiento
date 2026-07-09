// ── Pestañas ──────────────────────────────────────────────────────────────────
function switchTab(tab) {
  document.getElementById("panel-negotiator").style.display = tab === "negotiator" ? "block" : "none";
  document.getElementById("panel-avatar").style.display    = tab === "avatar"      ? "block" : "none";
  document.getElementById("tab-negotiator").classList.toggle("active", tab === "negotiator");
  document.getElementById("tab-avatar").classList.toggle("active", tab === "avatar");
}

// ── Perfil del negociante ─────────────────────────────────────────────────────
async function loadNegotiator() {
  try {
    const res = await fetch("/api/profiles/negotiator");
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("neg-name").value       = data.name       ?? "";
    document.getElementById("neg-role").value       = data.role       ?? "";
    document.getElementById("neg-org").value        = data.organization ?? "";
    document.getElementById("neg-objectives").value = data.objectives ?? "";
  } catch (e) {
    console.error("No se pudo cargar el perfil del negociante:", e);
  }
}

async function saveNegotiator() {
  const btn    = document.getElementById("neg-save-btn");
  const status = document.getElementById("neg-status");

  btn.disabled   = true;
  btn.textContent = "Guardando…";
  status.textContent = "";
  status.className   = "save-status";

  try {
    const res = await fetch("/api/profiles/negotiator", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name:         document.getElementById("neg-name").value.trim(),
        role:         document.getElementById("neg-role").value.trim(),
        organization: document.getElementById("neg-org").value.trim(),
        objectives:   document.getElementById("neg-objectives").value.trim(),
      }),
    });
    if (res.ok) {
      status.textContent = "✓ Perfil guardado";
      status.className   = "save-status success";
    } else {
      status.textContent = "Error al guardar";
      status.className   = "save-status error";
    }
  } catch (e) {
    status.textContent = "Error de red";
    status.className   = "save-status error";
  } finally {
    btn.disabled   = false;
    btn.textContent = "Guardar perfil";
    setTimeout(() => { status.textContent = ""; status.className = "save-status"; }, 3000);
  }
}

// ── Perfil del avatar ─────────────────────────────────────────────────────────
async function loadAvatar() {
  try {
    const res = await fetch("/api/profiles/avatar");
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("av-perfil").value = data.perfil     ?? "";
    document.getElementById("av-tono").value   = data.tono_estilo ?? "";
    document.getElementById("av-reglas").value = data.reglas     ?? "";
  } catch (e) {
    console.error("No se pudo cargar el perfil del avatar:", e);
  }
}

async function saveAvatar() {
  const btn    = document.getElementById("av-save-btn");
  const status = document.getElementById("av-status");

  btn.disabled   = true;
  btn.textContent = "Guardando…";
  status.textContent = "";
  status.className   = "save-status";

  try {
    const res = await fetch("/api/profiles/avatar", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        perfil:     document.getElementById("av-perfil").value.trim(),
        tono_estilo: document.getElementById("av-tono").value.trim(),
        reglas:     document.getElementById("av-reglas").value.trim(),
      }),
    });
    if (res.ok) {
      status.textContent = "✓ Perfil del avatar guardado";
      status.className   = "save-status success";
    } else {
      status.textContent = "Error al guardar";
      status.className   = "save-status error";
    }
  } catch (e) {
    status.textContent = "Error de red";
    status.className   = "save-status error";
  } finally {
    btn.disabled   = false;
    btn.textContent = "Guardar perfil del avatar";
    setTimeout(() => { status.textContent = ""; status.className = "save-status"; }, 3000);
  }
}

// ── Inicialización ────────────────────────────────────────────────────────────
loadNegotiator();
loadAvatar();
