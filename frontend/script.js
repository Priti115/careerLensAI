const API_BASE = window.location.origin;

const textTab = document.querySelector("#textTab");
const pdfTab = document.querySelector("#pdfTab");
const textPanel = document.querySelector("#textPanel");
const pdfPanel = document.querySelector("#pdfPanel");
const form = document.querySelector("#analysisForm");
const analyzeBtn = document.querySelector("#analyzeBtn");
const sampleBtn = document.querySelector("#sampleBtn");
const apiStatus = document.querySelector("#apiStatus");
const emptyState = document.querySelector("#emptyState");
const results = document.querySelector("#results");
const resultTitle = document.querySelector("#resultTitle");
const scoreBadge = document.querySelector("#scoreBadge");
const chatLauncher = document.querySelector("#chatLauncher");
const chatPanel = document.querySelector("#chatPanel");
const chatClose = document.querySelector("#chatClose");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const chatSend = document.querySelector("#chatSend");
const chatMessages = document.querySelector("#chatMessages");
const chatContext = document.querySelector("#chatContext");
let lastAnalysis = null;
let chatHistory = [];

let mode = "text";

function setMode(nextMode) {
  mode = nextMode;
  textTab.classList.toggle("active", mode === "text");
  pdfTab.classList.toggle("active", mode === "pdf");
  textPanel.classList.toggle("active", mode === "text");
  pdfPanel.classList.toggle("active", mode === "pdf");
}

async function checkApi() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error("API unavailable");
    apiStatus.textContent = "API Online";
    apiStatus.className = "status-pill ok";
  } catch {
    apiStatus.textContent = "API Offline";
    apiStatus.className = "status-pill bad";
  }
}

function renderTags(targetId, items) {
  const target = document.querySelector(targetId);
  target.innerHTML = "";
  if (!items || items.length === 0) {
    target.innerHTML = '<span class="tag">None found</span>';
    return;
  }
  items.forEach((item) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = item;
    target.appendChild(tag);
  });
}

function renderPredictions(predictions) {
  const target = document.querySelector("#predictions");

  target.innerHTML = "";

  predictions.forEach((prediction, index) => {

    const confidence = Number(
      prediction.confidence || 0
    ).toFixed(1);

    const row = document.createElement("div");

    row.className = "prediction";

    row.innerHTML = `
      <div>
        <strong>${index + 1}. ${prediction.role}</strong>

        <div class="bar">
          <span style="width:${confidence}%"></span>
        </div>
      </div>

      <span>${confidence}%</span>
    `;

    target.appendChild(row);
  });
}

function renderRecommendations(data) {
  const target = document.querySelector("#recommendations");
  const improvements = data.recommendations?.improvements || [];
  const tips = data.recommendations?.resume_tips || [];
  target.innerHTML = "";

  [...improvements, ...tips]
    .slice(0, 14)
    .forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      target.appendChild(li);
    });
}

function renderLearningResources(resources) {
  const target = document.querySelector("#learningResources");
  target.innerHTML = "";
  if (!resources || resources.length === 0) {
    target.innerHTML = '<span class="tag">No missing-skill resources needed</span>';
    return;
  }
  resources.forEach((resource) => {
    const link = document.createElement("a");
    link.className = "resource";
    link.href = resource.url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.innerHTML = `<strong>${resource.skill}</strong><span>${resource.platform}</span>`;
    target.appendChild(link);
  });
}

function renderResult(data) {
  lastAnalysis = data;
  const topRole = data.top_predictions?.[0]?.role || "Analysis Complete";
  const score = data.resume_score?.score ?? "--";
  resultTitle.textContent = topRole;
  scoreBadge.textContent = `${score}/100`;
  renderPredictions(data.top_predictions || []);
  renderTags("#missingSkills", data.skill_gap?.missing_skills || []);
  renderTags("#matchedSkills", data.skill_gap?.matched_skills || []);
  renderRecommendations(data);
  renderLearningResources(data.recommendations?.learning_resources || []);
  document.querySelector("#parsedResume").textContent = JSON.stringify(data.parsed_resume || {}, null, 2);
  emptyState.classList.add("hidden");
  results.classList.remove("hidden");
  chatContext.textContent = `Context loaded: ${topRole}, score ${score}/100`;
  openChat(false);
  addMessage("assistant", `I loaded this resume analysis. Ask me about improving it for ${topRole}, missing skills, or project bullet points.`);
}

function openChat(focusInput = true) {
  chatPanel.classList.remove("hidden");
  if (focusInput) chatInput.focus();
}

function closeChat() {
  chatPanel.classList.add("hidden");
}

function addMessage(role, text, extraClass = "") {
  const message = document.createElement("div");
  message.className = `message ${role} ${extraClass}`.trim();
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  message.appendChild(paragraph);
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  if ((role === "user" || role === "assistant") && !extraClass.includes("pending")) {
    chatHistory.push({ role, content: text });
    chatHistory = chatHistory.slice(-12);
  }
  return message;
}

async function askChatbot(event) {
  event.preventDefault();
  const question = chatInput.value.trim();
  if (!question) {
    chatInput.focus();
    return;
  }

  chatInput.value = "";
  addMessage("user", question);
  const pending = addMessage("assistant", "Thinking...", "pending");
  chatSend.disabled = true;
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, analysis: lastAnalysis, history: chatHistory.slice(0, -1) }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Chat failed.");
    pending.remove();
    addMessage("assistant", data.answer);
  } catch (error) {
    pending.remove();
    addMessage("assistant", error.message);
  } finally {
    chatSend.disabled = false;
    chatInput.focus();
  }
}

async function analyze(event) {
  event.preventDefault();
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing...";

  try {
    let response;
    if (mode === "text") {
      const resume = document.querySelector("#resumeText").value.trim();
      response = await fetch(`${API_BASE}/analyze/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume }),
      });
    } else {
      const file = document.querySelector("#resumeFile").files[0];
      if (!file) throw new Error("Select a PDF first.");
      const formData = new FormData();
      formData.append("file", file);
      response = await fetch(`${API_BASE}/analyze/resume`, {
        method: "POST",
        body: formData,
      });
    }

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Analysis failed.");
    renderResult(data);
  } catch (error) {
    emptyState.classList.remove("hidden");
    results.classList.add("hidden");
    resultTitle.textContent = "Error";
    scoreBadge.textContent = "--";
    emptyState.textContent = error.message;
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze Resume";
  }
}

textTab.addEventListener("click", () => setMode("text"));
pdfTab.addEventListener("click", () => setMode("pdf"));
form.addEventListener("submit", analyze);
sampleBtn.addEventListener("click", () => {
  setMode("text");
  document.querySelector("#resumeText").focus();
});
chatLauncher.addEventListener("click", () => openChat());
chatClose.addEventListener("click", closeChat);
chatForm.addEventListener("submit", askChatbot);

checkApi();
