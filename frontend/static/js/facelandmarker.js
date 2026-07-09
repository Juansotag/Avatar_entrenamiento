// Integracion con MediaPipe Face Landmarker (Tasks Vision), corriendo enteramente
// en el navegador. No se sube video crudo al servidor, solo metricas derivadas.
//
// IMPORTANTE: los nombres exactos de las categorias de blendshape, la forma exacta
// de facialTransformationMatrixes (orden de los datos, mayor/menor de columna) y
// los nombres de las opciones (outputFaceBlendshapes, etc.) deben verificarse
// contra la documentacion viva de @mediapipe/tasks-vision antes de la demo. Lo de
// abajo es la mejor interpretacion disponible al escribir este archivo, no una
// garantia. Calibrar visualmente: al mirar de frente a la camara, yaw/pitch/roll
// deberian rondar 0 grados.

import {
  FaceLandmarker,
  FilesetResolver,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";

const LOOKING_AT_CAMERA_THRESHOLD_DEG = 15;
const FLUSH_INTERVAL_MS = 1500;

let faceLandmarker = null;
let buffer = [];
let flushTimer = null;
let rafId = null;
let sessionIdGlobal = null;
let videoEl = null;
let startedAtMs = 0;

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}
function radToDeg(r) {
  return (r * 180) / Math.PI;
}

function rotationMatrixToEuler(m) {
  // m: Float32Array(16), 4x4 columna-mayor asumida. R[i][j] = m[i + j*4].
  const r00 = m[0], r10 = m[1], r20 = m[2];
  const r01 = m[4], r11 = m[5];
  const r21 = m[6], r22 = m[10];

  const pitch = Math.asin(clamp(-r20, -1, 1));
  let yaw, roll;
  if (Math.abs(r20) < 0.9999) {
    yaw = Math.atan2(r10, r00);
    roll = Math.atan2(r21, r22);
  } else {
    yaw = Math.atan2(-r01, r11);
    roll = 0;
  }
  return { yaw: radToDeg(yaw), pitch: radToDeg(pitch), roll: radToDeg(roll) };
}

function smileScoreFrom(blendshapes) {
  if (!blendshapes || blendshapes.length === 0) return null;
  const categories = blendshapes[0].categories || [];
  const left = categories.find((c) => c.categoryName === "mouthSmileLeft");
  const right = categories.find((c) => c.categoryName === "mouthSmileRight");
  if (!left || !right) return null;
  return (left.score + right.score) / 2;
}

async function initFaceLandmarker() {
  const filesetResolver = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
  );
  faceLandmarker = await FaceLandmarker.createFromOptions(filesetResolver, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
      delegate: "GPU",
    },
    outputFaceBlendshapes: true,
    outputFacialTransformationMatrixes: true,
    runningMode: "VIDEO",
    numFaces: 1,
  });
}

async function flushBuffer() {
  if (buffer.length === 0 || !sessionIdGlobal) return;
  const toSend = buffer;
  buffer = [];
  try {
    await fetch(`/api/sessions/${sessionIdGlobal}/nonverbal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ snapshots: toSend }),
    });
  } catch (err) {
    console.warn("No se pudieron enviar metricas no verbales, se descartan", err);
  }
}

function emotionsFrom(blendshapes) {
  if (!blendshapes || blendshapes.length === 0) {
    return { happiness: 0.0, anger: 0.0, sadness: 0.0, fear: 0.0 };
  }
  const categories = blendshapes[0].categories || [];
  const getScore = (name) => {
    const cat = categories.find((c) => c.categoryName === name);
    return cat ? cat.score : 0.0;
  };

  const smileLeft = getScore("mouthSmileLeft");
  const smileRight = getScore("mouthSmileRight");
  const happiness = (smileLeft + smileRight) / 2;

  const browDownLeft = getScore("browDownLeft");
  const browDownRight = getScore("browDownRight");
  const anger = (browDownLeft + browDownRight) / 2;

  const browInnerUp = getScore("browInnerUp");
  const frownLeft = getScore("mouthFrownLeft");
  const frownRight = getScore("mouthFrownRight");
  const sadness = (frownLeft + frownRight + browInnerUp) / 3;

  const eyeWideLeft = getScore("eyeWideLeft");
  const eyeWideRight = getScore("eyeWideRight");
  const browOuterUpLeft = getScore("browOuterUpLeft");
  const browOuterUpRight = getScore("browOuterUpRight");
  const fear = (eyeWideLeft + eyeWideRight + browOuterUpLeft + browOuterUpRight) / 4;

  return { happiness, anger, sadness, fear };
}

function detectLoop() {
  if (!faceLandmarker || videoEl.readyState < 2) {
    rafId = requestAnimationFrame(detectLoop);
    return;
  }
  const nowMs = performance.now();
  const results = faceLandmarker.detectForVideo(videoEl, nowMs);

  if (results.facialTransformationMatrixes && results.facialTransformationMatrixes.length > 0) {
    const { yaw, pitch, roll } = rotationMatrixToEuler(results.facialTransformationMatrixes[0].data);
    const lookingAtCamera =
      Math.abs(yaw) < LOOKING_AT_CAMERA_THRESHOLD_DEG && Math.abs(pitch) < LOOKING_AT_CAMERA_THRESHOLD_DEG;
    const smile = smileScoreFrom(results.faceBlendshapes);
    const emotions = emotionsFrom(results.faceBlendshapes);

    buffer.push({
      ts_ms: Math.round(nowMs - startedAtMs),
      yaw,
      pitch,
      roll,
      looking_at_camera: lookingAtCamera,
      smile_score: smile,
      happiness: emotions.happiness,
      anger: emotions.anger,
      sadness: emotions.sadness,
      fear: emotions.fear,
      raw_json: null,
    });
  }

  rafId = requestAnimationFrame(detectLoop);
}

export async function startNonverbalTracking(sessionId, videoElement) {
  sessionIdGlobal = sessionId;
  videoEl = videoElement;
  startedAtMs = performance.now();
  await initFaceLandmarker();
  flushTimer = setInterval(flushBuffer, FLUSH_INTERVAL_MS);
  detectLoop();
}

export async function stopNonverbalTracking() {
  if (rafId) cancelAnimationFrame(rafId);
  if (flushTimer) clearInterval(flushTimer);
  await flushBuffer();
}
