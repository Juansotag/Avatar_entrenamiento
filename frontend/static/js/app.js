// ── Estado del modal de edición ───────────────────────────────────────────────
let _editingCaseId = null;
let _loadedCases = []; // Caché global de casos cargados

// ── Helpers ───────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ── Carga de casos ────────────────────────────────────────────────────────────
async function loadCases() {
  const res = await fetch("/api/cases");
  const cases = await res.json();
  _loadedCases = cases;
  const container = document.getElementById("case-list");
  container.innerHTML = "";
  if (cases.length === 0) {
    container.innerHTML = "<p>Todavía no hay casos creados.</p>";
    return;
  }
  for (const c of cases) {
    const row = document.createElement("div");
    row.className = "case-item";
    const durationMins = Math.round((c.duration_seconds || 300) / 60);
    const userRoleStr = c.user_role || c.user_name || "Negociante";
    const avatarNameStr = c.avatar_name || "El Mandatario";
    const detailsId = `case-details-${c.id}`;

    const voiceLabels = {
      nova: "Voz femenina (Nova)",
      shimmer: "Voz femenina (Shimmer)",
      onyx: "Voz masculina (Onyx)",
      echo: "Voz masculina (Echo)",
      alloy: "Voz neutra (Alloy)"
    };
    const voiceLabel = voiceLabels[c.avatar_voice] || "Voz masculina (Onyx)";

    row.innerHTML = `
      <div class="case-item-info">
        <div class="case-item-title">
          <span>${escapeHtml(c.title)}</span>
          <span class="facet-chip facet-chip-scenario">${durationMins} min</span>
        </div>
        
        <div class="case-facets-row">
          <span class="facet-chip facet-chip-user" title="Rol del usuario en este caso">Tú: ${escapeHtml(userRoleStr)}</span>
          <span class="facet-chip facet-chip-avatar" title="Contraparte que interpreta la IA">Contraparte: ${escapeHtml(avatarNameStr)}</span>
          <span class="facet-chip" style="background:#f1f5f9; color:#475569; border:1px solid #cbd5e1;" title="Voz sintetizada para el avatar">${escapeHtml(voiceLabel)}</span>
          ${c.user_organization ? `<span class="facet-chip" style="background:rgba(0,0,0,0.05); color:#555;">${escapeHtml(c.user_organization)}</span>` : ''}
        </div>

        <div class="case-preview-text">
          ${escapeHtml(c.scenario_text).slice(0, 160)}…
        </div>

        <button type="button" class="ghost" style="font-size:0.78rem; padding:0.2rem 0.5rem; margin-top:0.45rem;" onclick="toggleDetails(${c.id})">
          <span id="toggle-lbl-${c.id}">Ver facetas completas</span>
        </button>

        <div id="${detailsId}" class="case-details-box" style="display:none;">
          <p style="margin:0 0 0.4rem 0;"><strong>Escenario:</strong> ${escapeHtml(c.scenario_text)}</p>
          ${c.user_objectives ? `<p style="margin:0 0 0.4rem 0;"><strong>Tus objetivos:</strong> ${escapeHtml(c.user_objectives)}</p>` : ''}
          ${c.avatar_profile ? `<p style="margin:0 0 0.4rem 0;"><strong>Perfil del Avatar:</strong> ${escapeHtml(c.avatar_profile)}</p>` : ''}
          <p style="margin:0 0 0.4rem 0;"><strong>Voz sintetizada:</strong> ${escapeHtml(voiceLabel)}</p>
          ${c.avatar_tone ? `<p style="margin:0 0 0.4rem 0;"><strong>Tono:</strong> ${escapeHtml(c.avatar_tone)}</p>` : ''}
          ${c.avatar_rules ? `<p style="margin:0;"><strong>Reglas y límites:</strong> ${escapeHtml(c.avatar_rules)}</p>` : ''}
        </div>
      </div>
      <div class="case-item-actions">
        <a href="/session.html?case_id=${c.id}"><button class="accent" id="negotiate-${c.id}">Negociar</button></a>
        <button class="ghost" id="edit-${c.id}" onclick="openEditModal(${c.id})">Editar</button>
        <button class="danger" id="delete-${c.id}" onclick="deleteCase(${c.id})">Eliminar</button>
      </div>
    `;
    container.appendChild(row);
  }
}

function toggleDetails(id) {
  const box = document.getElementById(`case-details-${id}`);
  const lbl = document.getElementById(`toggle-lbl-${id}`);
  if (!box) return;
  if (box.style.display === "none") {
    box.style.display = "block";
    lbl.textContent = "Ocultar facetas";
  } else {
    box.style.display = "none";
    lbl.textContent = "Ver facetas completas";
  }
}

// ── Carga de sesiones ─────────────────────────────────────────────────────────
async function loadSessions() {
  const res = await fetch("/api/sessions");
  const sessions = await res.json();
  const container = document.getElementById("session-list");
  container.innerHTML = "";
  if (sessions.length === 0) {
    container.innerHTML = "<p>Todavía no hay sesiones registradas.</p>";
    return;
  }
  for (const s of sessions) {
    const row = document.createElement("div");
    row.className = "case-item";
    const date = new Date(s.started_at).toLocaleString("es-CO");
    const statusLabel = s.status === "completed" ? "Completada" : "Activa";
    row.innerHTML = `
      <div class="case-item-info">
        <strong>${escapeHtml(s.case_title)}</strong><br/>
        <span style="color:#666; font-size:13px;">${date} · ${statusLabel}</span>
      </div>
      <div class="case-item-actions">
        <a href="/review.html?session_id=${s.session_id}"><button id="review-${s.session_id}">Ver informe</button></a>
      </div>
    `;
    container.appendChild(row);
  }
}

// ── Auto-rellenar negociante desde perfil predeterminado ───────────────────────
const autofillBtn = document.getElementById("btn-autofill-user");
if (autofillBtn) {
  autofillBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/negotiator");
      if (!res.ok) return;
      const data = await res.json();
      if (data.name) document.getElementById("user_name").value = data.name;
      if (data.role) document.getElementById("user_role").value = data.role;
      if (data.organization) document.getElementById("user_organization").value = data.organization;
      if (data.objectives) document.getElementById("user_objectives").value = data.objectives;
      autofillBtn.textContent = "Datos cargados";
      setTimeout(() => { autofillBtn.textContent = "Usar mi perfil predeterminado"; }, 2000);
    } catch (err) {
      console.error("Error al cargar perfil predeterminado:", err);
    }
  });
}

// ── Crear caso (3 Facetas) ───────────────────────────────────────────────────
document.getElementById("create-btn").addEventListener("click", async () => {
  // Faceta 1: Escenario
  const title = document.getElementById("title").value.trim();
  const scenario_text = document.getElementById("scenario").value.trim();
  const duration_minutes = parseInt(document.getElementById("duration_minutes").value) || 5;
  const duration_seconds = duration_minutes * 60;

  // Faceta 2: Negociante (Usuario)
  const user_name = document.getElementById("user_name").value.trim() || null;
  const user_role = document.getElementById("user_role").value.trim() || null;
  const user_organization = document.getElementById("user_organization").value.trim() || null;
  const user_objectives = document.getElementById("user_objectives").value.trim() || null;

  // Faceta 3: Contraparte (Avatar)
  const avatar_name = document.getElementById("avatar_name").value.trim() || "El Mandatario";
  const avatar_voice = document.getElementById("avatar_voice").value || "onyx";
  const avatar_profile = document.getElementById("avatar_profile").value.trim() || null;
  const avatar_tone = document.getElementById("avatar_tone").value.trim() || null;
  const avatar_rules = document.getElementById("avatar_rules").value.trim() || null;
  const persona_notes = document.getElementById("notes").value.trim() || null;

  if (!title || !scenario_text) {
    alert("Título y escenario son obligatorios.");
    return;
  }

  const btn = document.getElementById("create-btn");
  btn.disabled = true;
  btn.textContent = "Guardando caso…";

  try {
    const res = await fetch("/api/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        scenario_text,
        duration_seconds,
        user_name,
        user_role,
        user_organization,
        user_objectives,
        avatar_name,
        avatar_voice,
        avatar_profile,
        avatar_tone,
        avatar_rules,
        persona_notes,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      alert("Error al crear caso: " + (err.detail || JSON.stringify(err)));
      return;
    }

    // Limpiar formulario
    document.getElementById("title").value = "";
    document.getElementById("scenario").value = "";
    document.getElementById("duration_minutes").value = "5";
    document.getElementById("user_name").value = "";
    document.getElementById("user_role").value = "";
    document.getElementById("user_organization").value = "";
    document.getElementById("user_objectives").value = "";
    document.getElementById("avatar_name").value = "El Mandatario";
    document.getElementById("avatar_voice").value = "onyx";
    document.getElementById("avatar_profile").value = "";
    document.getElementById("avatar_tone").value = "";
    document.getElementById("avatar_rules").value = "";
    document.getElementById("notes").value = "";

    loadCases();
  } catch (err) {
    console.error(err);
    alert("Error de conexión al crear caso.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Guardar caso completo";
  }
});

// ── Eliminar caso ─────────────────────────────────────────────────────────────
async function deleteCase(id) {
  if (!confirm("¿Seguro que quieres eliminar este caso? Esta acción no se puede deshacer.")) return;
  await fetch(`/api/cases/${id}`, { method: "DELETE" });
  loadCases();
}

// ── Modal de edición ──────────────────────────────────────────────────────────
function openEditModal(id) {
  const c = _loadedCases.find(item => item.id === id);
  if (!c) return;
  _editingCaseId = id;

  // Faceta 1
  document.getElementById("edit-title").value = c.title || "";
  document.getElementById("edit-scenario").value = c.scenario_text || "";
  document.getElementById("edit-duration-minutes").value = Math.round((c.duration_seconds ?? 300) / 60);

  // Faceta 2
  document.getElementById("edit-user-name").value = c.user_name || "";
  document.getElementById("edit-user-role").value = c.user_role || "";
  document.getElementById("edit-user-org").value = c.user_organization || "";
  document.getElementById("edit-user-objectives").value = c.user_objectives || "";

  // Faceta 3
  document.getElementById("edit-avatar-name").value = c.avatar_name || "El Mandatario";
  document.getElementById("edit-avatar-voice").value = c.avatar_voice || "onyx";
  document.getElementById("edit-avatar-profile").value = c.avatar_profile || "";
  document.getElementById("edit-avatar-tone").value = c.avatar_tone || "";
  document.getElementById("edit-avatar-rules").value = c.avatar_rules || "";
  document.getElementById("edit-notes").value = c.persona_notes || "";

  document.getElementById("edit-modal").style.display = "flex";
}

function closeEditModal() {
  _editingCaseId = null;
  document.getElementById("edit-modal").style.display = "none";
}

document.getElementById("modal-close-btn").addEventListener("click", closeEditModal);
document.getElementById("modal-cancel-btn").addEventListener("click", closeEditModal);

document.getElementById("edit-modal").addEventListener("click", (e) => {
  if (e.target === document.getElementById("edit-modal")) closeEditModal();
});

document.getElementById("modal-save-btn").addEventListener("click", async () => {
  if (!_editingCaseId) return;

  const title = document.getElementById("edit-title").value.trim();
  const scenario_text = document.getElementById("edit-scenario").value.trim();
  const duration_minutes = parseInt(document.getElementById("edit-duration-minutes").value) || 5;
  const duration_seconds = duration_minutes * 60;

  const user_name = document.getElementById("edit-user-name").value.trim() || null;
  const user_role = document.getElementById("edit-user-role").value.trim() || null;
  const user_organization = document.getElementById("edit-user-org").value.trim() || null;
  const user_objectives = document.getElementById("edit-user-objectives").value.trim() || null;

  const avatar_name = document.getElementById("edit-avatar-name").value.trim() || "El Mandatario";
  const avatar_voice = document.getElementById("edit-avatar-voice").value || "onyx";
  const avatar_profile = document.getElementById("edit-avatar-profile").value.trim() || null;
  const avatar_tone = document.getElementById("edit-avatar-tone").value.trim() || null;
  const avatar_rules = document.getElementById("edit-avatar-rules").value.trim() || null;
  const persona_notes = document.getElementById("edit-notes").value.trim() || null;

  if (!title || !scenario_text) {
    alert("Título y escenario son obligatorios");
    return;
  }

  const btn = document.getElementById("modal-save-btn");
  btn.disabled = true;
  btn.textContent = "Guardando…";

  try {
    await fetch(`/api/cases/${_editingCaseId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        scenario_text,
        duration_seconds,
        user_name,
        user_role,
        user_organization,
        user_objectives,
        avatar_name,
        avatar_voice,
        avatar_profile,
        avatar_tone,
        avatar_rules,
        persona_notes,
      }),
    });
    closeEditModal();
    loadCases();
  } catch (err) {
    console.error(err);
    alert("Error al guardar cambios");
  } finally {
    btn.disabled = false;
    btn.textContent = "Guardar cambios";
  }
});

// ── Inicialización ────────────────────────────────────────────────────────────
loadCases();
loadSessions();
