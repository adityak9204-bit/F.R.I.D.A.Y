const askBtn = document.getElementById('askBtn');
const listenBtn = document.getElementById('listenBtn');
const stopBtn = document.getElementById('stopBtn');
const resetBtn = document.getElementById('resetBtn');
const promptEl = document.getElementById('prompt');
const logEl = document.getElementById('log');
const statusEl = document.getElementById('status');
const sessionEl = document.getElementById('session');

let recognition = null;
let listening = false;
let silenceTimer = null;
let speaking = false;

const sessionId = localStorage.getItem('friday_session_id') || crypto.randomUUID();
localStorage.setItem('friday_session_id', sessionId);
sessionEl.textContent = `Session: ${sessionId}`;

function log(message) {
  logEl.textContent = `${message}\n\n${logEl.textContent}`.trim();
}

function pickIrishFemaleVoice() {
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;

  const exact = voices.find(v => v.lang.toLowerCase().startsWith('en-ie') && /female|samantha|moira|ava|serena/i.test(v.name));
  if (exact) return exact;

  const irish = voices.find(v => v.lang.toLowerCase().startsWith('en-ie'));
  if (irish) return irish;

  const en = voices.find(v => v.lang.toLowerCase().startsWith('en-'));
  return en || voices[0];
}

function pauseRecognitionForSpeech() {
  if (recognition && listening) {
    try { recognition.stop(); } catch (_) { /* no-op */ }
  }
}

function resumeRecognitionAfterSpeech() {
  if (recognition && listening && !speaking) {
    try { recognition.start(); } catch (_) { /* no-op */ }
  }
}

function speak(text) {
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 1.0;
  utter.pitch = 1.05;

  const voice = pickIrishFemaleVoice();
  if (voice) utter.voice = voice;

  utter.onstart = () => {
    speaking = true;
    pauseRecognitionForSpeech();
  };
  utter.onend = () => {
    speaking = false;
    resumeRecognitionAfterSpeech();
  };

  speechSynthesis.cancel();
  speechSynthesis.speak(utter);
}

async function askAssistant(text) {
  const cleaned = text.trim();
  if (!cleaned) return;

  statusEl.textContent = 'Status: thinking...';
  const res = await fetch('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: cleaned, session_id: sessionId })
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Request failed (${res.status}): ${body}`);
  }

  const data = await res.json();
  statusEl.textContent = 'Status: ready';
  log(`You: ${cleaned}\n\nFriday: ${data.answer}`);
  speak(data.answer);
}

function dispatchFromSpeech(text) {
  if (silenceTimer) clearTimeout(silenceTimer);
  silenceTimer = setTimeout(() => {
    askAssistant(text).catch((err) => {
      statusEl.textContent = 'Status: error';
      log(`Error: ${err.message}`);
    });
    promptEl.value = '';
  }, 1000);
}

askBtn.addEventListener('click', async () => {
  const text = promptEl.value;
  try {
    await askAssistant(text);
  } catch (err) {
    statusEl.textContent = 'Status: error';
    log(`Error: ${err.message}`);
  }
});

resetBtn.addEventListener('click', async () => {
  try {
    await fetch(`/reset/${sessionId}`, { method: 'POST' });
    log('Friday: Memory reset for this session.');
  } catch (err) {
    log(`Error resetting memory: ${err.message}`);
  }
});

function setupRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    statusEl.textContent = 'Status: speech recognition not supported in this browser';
    return;
  }

  recognition = new SR();
  recognition.lang = 'en-IE';
  recognition.continuous = true;
  recognition.interimResults = true;

  let finalTranscript = '';

  recognition.onresult = (event) => {
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i];
      if (result.isFinal) {
        finalTranscript += `${result[0].transcript} `;
      } else {
        interim += result[0].transcript;
      }
    }

    const combined = `${finalTranscript}${interim}`.trim();
    promptEl.value = combined;

    if (finalTranscript.trim()) {
      dispatchFromSpeech(finalTranscript.trim());
      finalTranscript = '';
    }
  };

  recognition.onerror = (e) => {
    log(`Speech error: ${e.error}`);
  };

  recognition.onend = () => {
    if (listening && !speaking) {
      try { recognition.start(); } catch (_) { /* no-op */ }
    }
  };
}

listenBtn.addEventListener('click', () => {
  if (!recognition) setupRecognition();
  if (!recognition) return;
  listening = true;
  try { recognition.start(); } catch (_) { /* no-op */ }
  statusEl.textContent = 'Status: listening';
});

stopBtn.addEventListener('click', () => {
  listening = false;
  if (recognition) {
    try { recognition.stop(); } catch (_) { /* no-op */ }
  }
  statusEl.textContent = 'Status: stopped';
});

window.speechSynthesis.onvoiceschanged = () => {
  pickIrishFemaleVoice();
};
