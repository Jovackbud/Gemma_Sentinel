const form = document.querySelector("#evidence-form");
const textInput = document.querySelector("#text-input");
const fileInput = document.querySelector("#file-input");
const fileList = document.querySelector("#file-list");
const composer = document.querySelector("#composer");
const attachBtn = document.querySelector("#attach-btn");
const analyseBtn = document.querySelector("#analyse-btn");
const clearBtn = document.querySelector("#clear-btn");
const loadDemoBtn = document.querySelector("#load-demo");
const emptyState = document.querySelector("#empty-state");
const loadingState = document.querySelector("#loading-state");
const resultView = document.querySelector("#result");
const notice = document.querySelector("#notice");

let files = [];
let lastVerdict = null;
const audioAttachmentsEnabled = false;

const demoText = `Good afternoon. I am Mr. Emmanuel Okafor, HR Director at Chevron Nigeria Ltd.
We reviewed your profile and you have been shortlisted for a Logistics Coordinator position.
Salary is N450,000 per month. To proceed, pay a N15,000 registration fee to secure your slot before Friday.
Reply ASAP as we have many candidates.`;

fileInput.addEventListener("change", () => addFiles([...fileInput.files]));

attachBtn.addEventListener("click", () => fileInput.click());

composer.addEventListener("dragover", (event) => {
  event.preventDefault();
  composer.classList.add("is-over");
});

composer.addEventListener("dragleave", () => composer.classList.remove("is-over"));

composer.addEventListener("drop", (event) => {
  event.preventDefault();
  composer.classList.remove("is-over");
  addFiles([...event.dataTransfer.files]);
});

loadDemoBtn.addEventListener("click", () => {
  textInput.value = demoText;
  textInput.focus();
});

clearBtn.addEventListener("click", () => {
  files = [];
  fileInput.value = "";
  textInput.value = "";
  lastVerdict = null;
  renderFiles();
  showEmpty();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const inputs = [];
  const text = textInput.value.trim();
  if (text) inputs.push({ type: "text", name: "Pasted message", content: text });

  for (const file of files) {
    inputs.push({
      type: file.type.startsWith("audio/") ? "audio" : "image",
      name: file.name,
      mimeType: file.type,
      content: await fileToBase64(file)
    });
  }

  if (inputs.length === 0) {
    showNoticeOnly("Add a message or screenshot before analysing.");
    return;
  }

  analyseBtn.disabled = true;
  showLoading();

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);

  try {
    const response = await fetch("/api/analyse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ inputs }),
      signal: controller.signal
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Analysis failed.");
    lastVerdict = data;
    renderVerdict(data);
  } catch (error) {
    const message = error.name === "AbortError"
      ? "Analysis timed out after 60 seconds. Try again or reduce the number of attachments."
      : (error.message || "Analysis failed. Please try again.");
    showNoticeOnly(message);
  } finally {
    clearTimeout(timeout);
    analyseBtn.disabled = false;
  }
});

document.querySelector("#export-btn").addEventListener("click", () => {
  if (!lastVerdict) return;
  window.print();
});

function addFiles(nextFiles) {
  const accepted = nextFiles.filter((file) => {
    const validType = /^image\/(png|jpe?g|webp)$/i.test(file.type) || (audioAttachmentsEnabled && /^audio\/(wav|wave|mpeg|mp3|mp4|m4a|webm|ogg|x-m4a)$/i.test(file.type));
    const validSize = file.size <= 8 * 1024 * 1024;
    return validType && validSize;
  });
  files = [...files, ...accepted].slice(0, 5);
  fileInput.value = "";
  renderFiles();
}

function renderFiles() {
  fileList.innerHTML = "";
  for (const [index, file] of files.entries()) {
    const row = document.createElement("div");
    row.className = "file-pill";
    const kind = file.type.startsWith("audio/") ? "Audio" : "Image";
    row.innerHTML = `<span>${kind}: ${escapeHtml(file.name)}</span><button class="ghost" type="button" aria-label="Remove ${escapeHtml(file.name)}">Remove</button>`;
    row.querySelector("button").addEventListener("click", () => {
      files = files.filter((_, i) => i !== index);
      renderFiles();
    });
    fileList.append(row);
  }
}

function renderVerdict(verdict) {
  emptyState.classList.add("hidden");
  loadingState.classList.add("hidden");
  resultView.classList.remove("hidden");

  const risk = String(verdict.riskScore || "medium").toLowerCase();
  const percent = Number(verdict.riskPercentage || 50);
  const colour = risk === "critical" ? "#fb7185" : risk === "high" ? "#f97316" : risk === "medium" ? "#fbbf24" : "#4ade80";

  document.querySelector("#risk-label").textContent = titleCase(risk);
  document.querySelector("#risk-percent").textContent = `${Math.round(percent)}%`;
  document.querySelector("#score-ring").style.setProperty("--score", `${percent * 3.6}deg`);
  document.querySelector("#score-ring").style.setProperty("--accent", colour);

  const badge = document.querySelector("#scam-badge");
  const isScam = verdict.isScam === true;
  badge.textContent = isScam ? "⚠ Scam detected" : "No scam detected";
  badge.setAttribute("data-scam", isScam ? "true" : "false");

  document.querySelector("#scam-type").textContent = verdict.scamType || "Unclear";
  document.querySelector("#confidence").textContent = titleCase(verdict.confidence || "medium");
  document.querySelector("#mode").textContent = modeLabel(verdict.mode);
  document.querySelector("#reasoning").textContent = verdict.reasoning || "";
  document.querySelector("#recommended-action").textContent = verdict.recommendedAction || "";

  const flags = document.querySelector("#red-flags");
  flags.innerHTML = "";
  for (const flag of verdict.redFlags || []) {
    const li = document.createElement("li");
    li.textContent = flag;
    flags.append(li);
  }

  if (verdict.notice) {
    notice.textContent = verdict.notice;
    notice.classList.remove("hidden");
  } else {
    notice.classList.add("hidden");
  }

  const timeline = document.querySelector("#timeline");
  if (verdict.timeline && verdict.timeline.attackNarrative) {
    document.querySelector("#timeline-text").textContent = `${verdict.timeline.attackNarrative} Ultimate goal: ${verdict.timeline.ultimateGoal || "Unknown"}`;
    timeline.classList.remove("hidden");
  } else {
    timeline.classList.add("hidden");
  }
}

function showLoading() {
  emptyState.classList.add("hidden");
  resultView.classList.add("hidden");
  loadingState.classList.remove("hidden");
}

function showEmpty() {
  emptyState.classList.remove("hidden");
  resultView.classList.add("hidden");
  loadingState.classList.add("hidden");
}

function showNoticeOnly(message) {
  lastVerdict = {
    riskScore: "medium",
    riskPercentage: 50,
    scamType: "Input issue",
    redFlags: [message],
    reasoning: "Sentinel needs usable evidence before it can produce a meaningful verdict.",
    recommendedAction: "Add a screenshot or paste the suspicious message, then try again.",
    confidence: "low",
    isScam: false,
    mode: "local"
  };
  renderVerdict(lastVerdict);
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
    reader.onerror = () => reject(new Error("Could not read image."));
    reader.readAsDataURL(file);
  });
}

function titleCase(value) {
  return String(value).replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function modeLabel(mode) {
  if (mode === "gemma_google") return "Google Gemma";
  if (mode === "gemma_llamacpp") return "Gemma local";
  if (mode === "rules") return "Rules";
  return "Local";
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[char]);
}
