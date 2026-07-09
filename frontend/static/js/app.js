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
  _loadedCases = cases; // Guardamos en caché para evitar escapar comillas en inline HTML
  const container = document.getElementById("case-list");
  container.innerHTML = "";
  if (cases.length === 0) {
    container.innerHTML = "<p>Todavía no hay casos creados.</p>";
    return;
  }
  for (const c of cases) {
    const row = document.createElement("div");
    row.className = "case-item";
    row.innerHTML = `
      <div class="case-item-info">
        <strong>${escapeHtml(c.title)}</strong><br/>
        <span style="color:#666; font-size:13px;">${escapeHtml(c.scenario_text).slice(0, 120)}…</span>
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

// ── Crear caso ────────────────────────────────────────────────────────────────
document.getElementById("create-btn").addEventListener("click", async () => {
  const title = document.getElementById("title").value.trim();
  const scenario_text = document.getElementById("scenario").value.trim();
  const persona_notes = document.getElementById("notes").value.trim() || null;
  const avatar_name = document.getElementById("avatar_name").value.trim() || "El Mandatario";
  const duration_minutes = parseInt(document.getElementById("duration_minutes").value) || 5;
  const duration_seconds = duration_minutes * 60;
  if (!title || !scenario_text) {
    alert("Título y escenario son obligatorios");
    return;
  }
  const btn = document.getElementById("create-btn");
  btn.disabled = true;
  btn.textContent = "Creando…";
  await fetch("/api/cases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, scenario_text, persona_notes, avatar_name, duration_seconds }),
  });
  document.getElementById("title").value = "";
  document.getElementById("scenario").value = "";
  document.getElementById("notes").value = "";
  document.getElementById("avatar_name").value = "El Mandatario";
  document.getElementById("duration_minutes").value = "5";
  btn.disabled = false;
  btn.textContent = "Crear caso";
  loadCases();
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
  document.getElementById("edit-title").value = c.title;
  document.getElementById("edit-scenario").value = c.scenario_text;
  document.getElementById("edit-notes").value = c.persona_notes ?? "";
  document.getElementById("edit-avatar-name").value = c.avatar_name ?? "El Mandatario";
  document.getElementById("edit-duration-minutes").value = Math.round((c.duration_seconds ?? 300) / 60);
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
  const persona_notes = document.getElementById("edit-notes").value.trim() || null;
  const avatar_name = document.getElementById("edit-avatar-name").value.trim() || "El Mandatario";
  const duration_minutes = parseInt(document.getElementById("edit-duration-minutes").value) || 5;
  const duration_seconds = duration_minutes * 60;
  if (!title || !scenario_text) {
    alert("Título y escenario son obligatorios");
    return;
  }
  const btn = document.getElementById("modal-save-btn");
  btn.disabled = true;
  btn.textContent = "Guardando…";
  await fetch(`/api/cases/${_editingCaseId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, scenario_text, persona_notes, avatar_name, duration_seconds }),
  });
  btn.disabled = false;
  btn.textContent = "Guardar cambios";
  closeEditModal();
  loadCases();
});

// ── Inicialización ────────────────────────────────────────────────────────────
loadCases();
loadSessions();
