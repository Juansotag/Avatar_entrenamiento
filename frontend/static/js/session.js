import { startNonverbalTracking, stopNonverbalTracking } from "./facelandmarker.js";

const params = new URLSearchParams(window.location.search);
const caseId = params.get("case_id");

let sessionId = null;
let durationSeconds = 300;
let remainingSeconds = 300;
let timerInterval = null;
let recorder = null;
let ending = false;
let isTimerPaused = false;

const transcriptEl = document.getElementById("transcript");
const timerEl = document.getElementById("timer");
const recordBtn = document.getElementById("record-btn");
const endBtn = document.getElementById("end-btn");
const turnStatusEl = document.getElementById("turn-status");
const nonverbalStatusEl = document.getElementById("nonverbal-status");
const personaAudioEl = document.getElementById("persona-audio");
const videoEl = document.getElementById("user-video");

let avatarName = "El Mandatario";

function addBubble(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.innerHTML = `<div class="role">${role === "persona" ? avatarName : "Tú"}</div>${escapeHtml(text)}`;
  transcriptEl.appendChild(div);
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function startTimer() {
  timerEl.textContent = formatTime(remainingSeconds);
  timerInterval = setInterval(() => {
    if (isTimerPaused) return; // Pausar si el avatar está pensando
    remainingSeconds -= 1;
    timerEl.textContent = formatTime(Math.max(remainingSeconds, 0));
    if (remainingSeconds <= 0) {
      clearInterval(timerInterval);
      endSession();
    }
  }, 1000);
}

async function playAudioIfAny(url) {
  if (!url) return;
  personaAudioEl.src = url;
  try {
    await personaAudioEl.play();
  } catch (err) {
    console.warn("No se pudo reproducir el audio automaticamente", err);
  }
}

async function startSession() {
  // Deshabilitar botón y mostrar burbuja de carga inicial
  recordBtn.disabled = true;
  recordBtn.textContent = "🎙 Cargando avatar...";
  transcriptEl.innerHTML = `
    <div class="bubble persona" id="initial-loading-bubble">
      <div class="role">Avatar</div>
      <div>⏳ Conectando con el avatar y preparando negociación...</div>
    </div>
  `;

  const res = await fetch(`/api/sessions?case_id=${caseId}`, { method: "POST" });
  if (!res.ok) {
    alert("No se pudo iniciar la sesión. Revisa que el caso exista y que la API de Claude esté configurada.");
    return;
  }
  const data = await res.json();
  sessionId = data.session_id;
  durationSeconds = data.duration_seconds;
  remainingSeconds = durationSeconds;

  avatarName = data.case.avatar_name || "El Mandatario";
  document.querySelector(".persona-name").textContent = avatarName;
  document.getElementById("persona-photo").alt = avatarName;

  document.getElementById("case-title").textContent = data.case.title;
  
  // Limpiar carga y añadir burbuja real
  transcriptEl.innerHTML = "";
  addBubble("persona", data.opening_turn.text);
  await playAudioIfAny(data.opening_turn.audio_url);

  startTimer();
  await setupCamera();

  recordBtn.disabled = false;
  recordBtn.textContent = "🎙 Haz clic para hablar";
}

async function setupCamera() {
  let stream = null;
  let hasVideo = false;
  
  // 1. Intentar acceder a la cámara y micrófono
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    videoEl.srcObject = stream;
    hasVideo = true;
  } catch (err) {
    console.warn("No se pudo iniciar video+audio, intentando solo audio...", err);
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      nonverbalStatusEl.textContent = "Cámara desactivada por permisos. Análisis no verbal desactivado.";
    } catch (audioErr) {
      console.error("No se pudo acceder al micrófono:", audioErr);
      nonverbalStatusEl.textContent = "No se pudo acceder al micrófono/cámara.";
    }
  }

  // 2. Si la cámara está activa, iniciar el rastreo no verbal de MediaPipe
  if (hasVideo && stream) {
    try {
      nonverbalStatusEl.textContent = "Cargando detector de expresiones faciales (MediaPipe)...";
      await startNonverbalTracking(sessionId, videoEl);
      nonverbalStatusEl.textContent = "Analizando lenguaje no verbal...";
    } catch (modelErr) {
      console.error("Error cargando MediaPipe Face Landmarker:", modelErr);
      nonverbalStatusEl.textContent = "⚠️ Error al cargar el modelo de IA (posible bloqueo de red o ad-blocker).";
    }
  }
  
  // 3. Crear el grabador de audio
  if (stream) {
    const audioOnlyStream = new MediaStream(stream.getAudioTracks());
    recorder = new TurnRecorder(audioOnlyStream);
  }
}

async function submitTurn(blob) {
  isTimerPaused = true;
  turnStatusEl.textContent = `${avatarName} está pensando...`;
  recordBtn.disabled = true;
  const formData = new FormData();
  formData.append("audio", blob, "turn.webm");
  formData.append("remaining_seconds", remainingSeconds);

  try {
    const res = await fetch(`/api/sessions/${sessionId}/turns`, { method: "POST", body: formData });
    if (!res.ok) {
      turnStatusEl.textContent = "Hubo un error procesando el turno.";
      return;
    }
    const data = await res.json();
    addBubble("user", data.user_text);
    addBubble("persona", data.persona_text);
    await playAudioIfAny(data.persona_audio_url);
    turnStatusEl.textContent = "";
  } finally {
    isTimerPaused = false;
    recordBtn.disabled = false;
    recordBtn.textContent = "🎙 Haz clic para hablar";
  }
}

let isRecording = false;

async function handleRecordClick() {
  if (!recorder) return;
  if (!isRecording) {
    recorder.start();
    isRecording = true;
    turnStatusEl.textContent = "Grabando...";
    recordBtn.textContent = "🛑 Grabando... Haz clic para enviar";
    recordBtn.classList.add("recording");
  } else {
    if (recorder.mediaRecorder && recorder.mediaRecorder.state === "recording") {
      recordBtn.textContent = "Procesando audio...";
      recordBtn.classList.remove("recording");
      isRecording = false;
      const blob = await recorder.stop();
      await submitTurn(blob);
    }
  }
}

recordBtn.addEventListener("click", handleRecordClick);

async function endSession() {
  if (ending) return;
  ending = true;

  clearInterval(timerInterval);
  endBtn.disabled = true;
  endBtn.textContent = "⌛ Analizando sesión...";
  turnStatusEl.textContent = "Generando informe de coaching por IA. Por favor espera unos segundos...";

  try {
    await stopNonverbalTracking();
  } catch (err) {
    console.warn("No se pudo detener el seguimiento no verbal:", err);
  }

  if (sessionId) {
    try {
      await fetch(`/api/sessions/${sessionId}/end`, { method: "POST" });
    } catch (err) {
      console.error("Error al finalizar la sesión en la API:", err);
    }
  }
  window.location.href = `/review.html?session_id=${sessionId}`;
}

endBtn.addEventListener("click", endSession);

async function requestTimeExtension() {
  if (ending) return;
  
  // Pausar tiempo y bloquear controles
  isTimerPaused = true;
  recordBtn.disabled = true;
  recordBtn.textContent = "🎙 Solicitando extensión...";
  if (addTimeBtn) {
    addTimeBtn.disabled = true;
    addTimeBtn.textContent = "Procesando...";
  }
  
  // Agregar burbuja de diálogo
  addBubble("user", "¿Podríamos extender el tiempo de la reunión?");
  turnStatusEl.textContent = `${avatarName} está evaluando tu solicitud de tiempo...`;

  const formData = new FormData();
  formData.append("text", "Solicito una extensión del tiempo de negociación.");
  formData.append("remaining_seconds", remainingSeconds);
  formData.append("request_extension", "true");

  try {
    const res = await fetch(`/api/sessions/${sessionId}/turns`, { method: "POST", body: formData });
    if (!res.ok) {
      turnStatusEl.textContent = "No se pudo procesar la solicitud de extensión.";
      return;
    }
    const data = await res.json();
    addBubble("persona", data.persona_text);
    await playAudioIfAny(data.persona_audio_url);
    
    if (data.granted_seconds > 0) {
      remainingSeconds += data.granted_seconds;
      durationSeconds += data.granted_seconds;
      timerEl.textContent = formatTime(remainingSeconds);
      
      // Flash verde visual
      timerEl.style.color = "#15803d";
      setTimeout(() => { timerEl.style.color = ""; }, 1500);
      
      const extraMins = Math.round(data.granted_seconds / 60);
      turnStatusEl.textContent = `¡Extensión concedida! +${extraMins} min adicionales.`;
    } else {
      // Flash rojo visual
      timerEl.style.color = "var(--c-red)";
      setTimeout(() => { timerEl.style.color = ""; }, 1500);
      turnStatusEl.textContent = "Extensión denegada por la contraparte.";
    }
  } catch (err) {
    console.error("Error solicitando extensión:", err);
    turnStatusEl.textContent = "Error de red al solicitar extensión.";
  } finally {
    isTimerPaused = false;
    recordBtn.disabled = false;
    recordBtn.textContent = "🎙 Haz clic para hablar";
    if (addTimeBtn) {
      addTimeBtn.disabled = false;
      addTimeBtn.textContent = "+1 Minuto";
    }
  }
}

const addTimeBtn = document.getElementById("add-time-btn");
if (addTimeBtn) {
  addTimeBtn.addEventListener("click", requestTimeExtension);
}

if (!caseId) {
  alert("Falta el caso. Volviendo al inicio.");
  window.location.href = "/index.html";
} else {
  startSession();
}
