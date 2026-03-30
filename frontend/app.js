// ===== User ID persistant =====
function getUserId() {
  let id = localStorage.getItem("carBetting_userId");
  if (!id) {
    id = "user_" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("carBetting_userId", id);
  }
  return id;
}

const USER_ID = getUserId();
const ROUND_DURATION = 30;

let selectedOption = null;
let currentPhase = null;
let lastRoundId = null;
let history = [];
let betOptions = [];
let prevCount = 0;

const balanceEl = document.getElementById("balance");
const roundIdEl = document.getElementById("round-id");
const timerEl = document.getElementById("timer");
const timerBarEl = document.getElementById("timer-bar");
const vehicleCountEl = document.getElementById("vehicle-count");
const phaseLabelEl = document.getElementById("phase-label");
const betOptionsEl = document.getElementById("bet-options");
const betAmountEl = document.getElementById("bet-amount");
const betFeedbackEl = document.getElementById("bet-feedback");
const resultBlockEl = document.getElementById("result-block");
const resultContentEl = document.getElementById("result-content");
const historyListEl = document.getElementById("history-list");

let ws = null;
let reconnectDelay = 1000;

function connect() {
  const url = `ws://${location.host}/ws?user_id=${USER_ID}`;
  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectDelay = 1000;
    showFeedback("Connecté au serveur.", "success", 2000);
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "state") handleState(msg);
    else if (msg.type === "bet_response") handleBetResponse(msg);
  };

  ws.onclose = () => {
    setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 1.5, 10000);
  };

  ws.onerror = () => ws.close();
}

function handleState(state) {
  if (state.balance !== undefined) {
    balanceEl.textContent = state.balance;
  }

  if (state.round_id !== lastRoundId && lastRoundId !== null) {
    selectedOption = null;
    updateBetButtons();
  }
  lastRoundId = state.round_id;
  roundIdEl.textContent = state.round_id;

  const t = state.timer_seconds_remaining;
  timerEl.textContent = t;
  const pct = (t / ROUND_DURATION) * 100;
  timerBarEl.style.width = pct + "%";
  timerBarEl.classList.toggle("urgent", t <= 8);

  const newCount = state.count;
  if (newCount !== prevCount) {
    vehicleCountEl.classList.remove("bump");
    void vehicleCountEl.offsetWidth;
    vehicleCountEl.classList.add("bump");
    setTimeout(() => vehicleCountEl.classList.remove("bump"), 150);
  }
  vehicleCountEl.textContent = newCount;
  prevCount = newCount;

  updatePhase(state.phase);

  if (state.bet_options && state.bet_options.length) {
    betOptions = state.bet_options;
    renderBetOptions(state.bet_options, state.phase === "betting");
  }

  if (state.current_bet) {
    selectedOption = state.current_bet.option;
    updateBetButtons();
  }

  if (state.last_result) {
    showResult(state.last_result);
  }
}

function updatePhase(phase) {
  if (phase === currentPhase) return;
  currentPhase = phase;

  phaseLabelEl.className = "phase-label " + phase;

  if (phase === "betting") {
    phaseLabelEl.textContent = "PARIS OUVERTS";
    resultBlockEl.style.display = "none";
  } else if (phase === "active") {
    phaseLabelEl.textContent = "ROUND EN COURS";
  } else if (phase === "resolved") {
    phaseLabelEl.textContent = "ROUND TERMINÉ";
  }

  const enabled = phase === "betting";
  document.querySelectorAll(".bet-btn").forEach(btn => {
    btn.disabled = !enabled;
  });
}

function renderBetOptions(options, enabled) {
  if (betOptionsEl.children.length === options.length) return;

  betOptionsEl.innerHTML = "";
  options.forEach(opt => {
    const btn = document.createElement("button");
    btn.className = "bet-btn" + (selectedOption === opt.id ? " selected" : "");
    btn.disabled = !enabled;
    btn.dataset.option = opt.id;
    btn.innerHTML = `
      <span>${opt.label}</span>
      <span class="bet-multiplier">x${opt.multiplier.toFixed(1)}</span>
    `;
    btn.addEventListener("click", () => onBetClick(opt.id));
    betOptionsEl.appendChild(btn);
  });
}

function updateBetButtons() {
  document.querySelectorAll(".bet-btn").forEach(btn => {
    btn.classList.toggle("selected", btn.dataset.option === selectedOption);
  });
}

function onBetClick(option) {
  if (currentPhase !== "betting") return;

  const amount = parseInt(betAmountEl.value, 10);
  if (!amount || amount <= 0) {
    showFeedback("Entre un montant valide.", "error");
    return;
  }

  selectedOption = option;
  updateBetButtons();

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: "bet", option, amount }));
  }
}

function handleBetResponse(msg) {
  showFeedback(msg.message, msg.success ? "success" : "error");
  if (msg.success && msg.balance !== undefined) {
    balanceEl.textContent = msg.balance;
  }
}

function showResult(result) {
  const alreadyShown = resultBlockEl.dataset.roundId === String(result.round_id);
  if (alreadyShown) return;
  resultBlockEl.dataset.roundId = result.round_id;
  resultBlockEl.style.display = "block";

  const winOpt = betOptions.find(o => o.id === result.winning_option);
  const winLabel = winOpt ? winOpt.label : result.winning_option;

  resultContentEl.innerHTML = `
    <div>Total : <strong>${result.final_count}</strong> véhicule(s)</div>
    <div>Gagnant : <strong>${winLabel}</strong></div>
  `;

  addHistory(result, winLabel);
}

function addHistory(result, winLabel) {
  history.unshift(result);
  if (history.length > 5) history.pop();

  historyListEl.innerHTML = history.map(r => `
    <li>
      <span>Round ${r.round_id}</span>
      <span>${r.final_count} véh.</span>
      <span>${winLabel || r.winning_option}</span>
    </li>
  `).join("");
}

function showFeedback(msg, type = "", duration = 3000) {
  betFeedbackEl.textContent = msg;
  betFeedbackEl.className = "bet-feedback " + type;
  if (duration) {
    setTimeout(() => {
      betFeedbackEl.textContent = "";
      betFeedbackEl.className = "bet-feedback";
    }, duration);
  }
}

connect();
