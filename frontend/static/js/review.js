const params = new URLSearchParams(window.location.search);
const sessionId = params.get("session_id");

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function statCard(value, label) {
  return `<div class="stat"><div class="value">${value}</div><div class="label">${label}</div></div>`;
}

let avatarName = "El Mandatario";

function renderSummary(summary) {
  const grid = document.getElementById("summary-grid");
  if (!summary || summary.sample_count === 0) {
    grid.innerHTML = "<p>No se registraron métricas de cámara para esta sesión.</p>";
    return;
  }
  grid.innerHTML = [
    statCard(`${summary.pct_looking_at_camera}%`, "Mirando a cámara"),
    statCard(`${summary.avg_yaw_abs}°`, "Giro horizontal (Yaw)"),
    statCard(`${summary.avg_pitch_abs}°`, "Giro vertical (Pitch)"),
    statCard(`${summary.pct_happiness}%`, "Felicidad"),
    statCard(`${summary.pct_anger}%`, "Enojo"),
    statCard(`${summary.pct_sadness}%`, "Tristeza"),
    statCard(`${summary.pct_fear}%`, "Miedo"),
  ].join("");
}

function renderTranscript(transcript) {
  const container = document.getElementById("transcript");
  container.innerHTML = "";
  for (const turn of transcript) {
    const div = document.createElement("div");
    div.className = `bubble ${turn.role}`;
    const audioTag = turn.audio_url ? `<div><audio controls src="${turn.audio_url}"></audio></div>` : "";
    div.innerHTML = `<div class="role">${turn.role === "persona" ? avatarName : "Tú"}</div>${escapeHtml(turn.text)}${audioTag}`;
    container.appendChild(div);
  }
}

let chartInstance = null;

function renderTimeline(timeline) {
  const ctx = document.getElementById("timeline-chart").getContext("2d");
  if (chartInstance) {
    chartInstance.destroy();
  }

  if (!timeline || timeline.length === 0) return;

  // Downsample if timeline has too many entries (performance optimization for Chart.js)
  let dataPoints = timeline;
  const maxPoints = 200;
  if (timeline.length > maxPoints) {
    const step = Math.ceil(timeline.length / maxPoints);
    dataPoints = timeline.filter((_, idx) => idx % step === 0);
  }

  const labels = dataPoints.map(p => `${Math.round(p.ts_ms / 1000)}s`);

  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Desviación Horizontal (Yaw °)",
          data: dataPoints.map(p => p.yaw),
          borderColor: "#00135B",
          backgroundColor: "rgba(0, 19, 91, 0.05)",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          yAxisID: "y-degrees",
        },
        {
          label: "Desviación Vertical (Pitch °)",
          data: dataPoints.map(p => p.pitch),
          borderColor: "#93AAC9",
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          yAxisID: "y-degrees",
        },
        {
          label: "Felicidad (%)",
          data: dataPoints.map(p => Math.round((p.happiness ?? 0) * 100)),
          borderColor: "#f8a719",
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          yAxisID: "y-percent",
        },
        {
          label: "Enojo (%)",
          data: dataPoints.map(p => Math.round((p.anger ?? 0) * 100)),
          borderColor: "#96272D",
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          yAxisID: "y-percent",
        },
        {
          label: "Tristeza (%)",
          data: dataPoints.map(p => Math.round((p.sadness ?? 0) * 100)),
          borderColor: "#9013fe",
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          yAxisID: "y-percent",
        },
        {
          label: "Miedo (%)",
          data: dataPoints.map(p => Math.round((p.fear ?? 0) * 100)),
          borderColor: "#7ed321",
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          yAxisID: "y-percent",
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: {
            boxWidth: 12,
            font: { family: "Libre Franklin", size: 11 }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          title: { display: true, text: "Duración de Negociación", font: { weight: "bold" } }
        },
        "y-degrees": {
          type: "linear",
          position: "left",
          suggestedMin: -25,
          suggestedMax: 25,
          title: { display: true, text: "Desviación (Grados °)" }
        },
        "y-percent": {
          type: "linear",
          position: "right",
          min: 0,
          max: 100,
          title: { display: true, text: "Intensidad (%)" },
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

// ─── Informe de Coaching de Claude ───────────────────────────────────────────

const RESULTADO_LABELS = {
  acuerdo_parcial: "Acuerdo parcial",
  aplazamiento: "Aplazamiento",
  rechazo: "Rechazo",
  sin_datos: "Sin datos",
};

const RESULTADO_CLASSES = {
  acuerdo_parcial: "acuerdo",
  aplazamiento: "aplazamiento",
  rechazo: "rechazo",
  sin_datos: "",
};

function renderCoachingReport(report) {
  if (!report) return;

  document.getElementById("coaching-card").style.display = "";

  // Puntaje
  const scoreEl = document.getElementById("score-value");
  scoreEl.textContent = report.score !== null ? report.score : "–";

  // Resultado badge
  const badgeEl = document.getElementById("resultado-badge");
  const resultadoKey = (report.resultado_final || "sin_datos").replace(/ /g, "_");
  badgeEl.textContent = RESULTADO_LABELS[resultadoKey] || report.resultado_final || "";
  const badgeClass = RESULTADO_CLASSES[resultadoKey] || "";
  if (badgeClass) badgeEl.classList.add(badgeClass);

  // Resumen ejecutivo
  document.getElementById("resumen-ejecutivo").textContent = report.resumen_ejecutivo || "";

  // Fortalezas
  if (report.fortalezas && report.fortalezas.length > 0) {
    document.getElementById("section-fortalezas").style.display = "";
    const container = document.getElementById("list-fortalezas");
    container.innerHTML = report.fortalezas.map(f => `
      <div class="coaching-item strength">
        <div class="item-title">✓ ${escapeHtml(f.titulo)}</div>
        <div class="item-desc">${escapeHtml(f.descripcion)}</div>
        ${f.cita_usuario ? `<blockquote>"${escapeHtml(f.cita_usuario)}"</blockquote>` : ""}
      </div>
    `).join("");
  }

  // Áreas de mejora
  if (report.areas_de_mejora && report.areas_de_mejora.length > 0) {
    document.getElementById("section-mejoras").style.display = "";
    const container = document.getElementById("list-mejoras");
    container.innerHTML = report.areas_de_mejora.map(a => `
      <div class="coaching-item improvement">
        <div class="item-title">⚠ ${escapeHtml(a.titulo)}</div>
        <div class="item-desc">${escapeHtml(a.descripcion)}</div>
        ${a.cita_usuario ? `<blockquote>"${escapeHtml(a.cita_usuario)}"</blockquote>` : ""}
        ${a.sugerencia_reformulacion ? `
          <div class="reformulacion">
            <strong>Cómo reformularlo:</strong><br>${escapeHtml(a.sugerencia_reformulacion)}
          </div>
        ` : ""}
      </div>
    `).join("");
  }

  // Tácticas efectivas
  if (report.tacticas_efectivas && report.tacticas_efectivas.length > 0) {
    document.getElementById("section-tacticas").style.display = "";
    const container = document.getElementById("list-tacticas");
    container.innerHTML = report.tacticas_efectivas.map(t =>
      `<span class="coaching-tag">✓ ${escapeHtml(t)}</span>`
    ).join("");
  }

  // Oportunidades perdidas
  if (report.oportunidades_perdidas && report.oportunidades_perdidas.length > 0) {
    document.getElementById("section-oportunidades").style.display = "";
    const container = document.getElementById("list-oportunidades");
    container.innerHTML = report.oportunidades_perdidas.map(o =>
      `<span class="coaching-tag">✕ ${escapeHtml(o)}</span>`
    ).join("");
  }

  // Recomendación principal
  if (report.recomendacion_principal) {
    document.getElementById("section-recomendacion").style.display = "";
    document.getElementById("recomendacion-text").textContent = report.recomendacion_principal;
  }
}

// ─── Carga principal ──────────────────────────────────────────────────────────

async function load() {
  if (!sessionId) {
    alert("Falta el id de sesión.");
    window.location.href = "/index.html";
    return;
  }
  const res = await fetch(`/api/sessions/${sessionId}`);
  if (!res.ok) {
    alert("No se encontró la sesión.");
    return;
  }
  const data = await res.json();
  avatarName = data.case.avatar_name || "El Mandatario";
  document.getElementById("case-title").textContent = data.case.title;
  document.getElementById("scenario-text").textContent = data.case.scenario_text;
  const started = new Date(data.started_at).toLocaleString("es-CO");
  document.getElementById("session-meta").textContent = `Iniciada: ${started}, estado: ${data.status}`;

  // Renderizar informe de coaching si existe
  if (data.coaching_report) {
    renderCoachingReport(data.coaching_report);
  }

  renderSummary(data.nonverbal_summary);
  renderTranscript(data.transcript);
  renderTimeline(data.nonverbal_timeline);
}

load();
