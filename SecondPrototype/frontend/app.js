(() => {
  // ---------- Mode switching ----------
  const liveModeTab = document.getElementById("liveModeTab");
  const demoModeTab = document.getElementById("demoModeTab");
  const liveMode = document.getElementById("liveMode");
  const demoMode = document.getElementById("demoMode");

  function setMode(mode) {
    const isLive = mode === "live";
    liveMode.hidden = !isLive;
    demoMode.hidden = isLive;
    liveModeTab.classList.toggle("active", isLive);
    demoModeTab.classList.toggle("active", !isLive);
    liveModeTab.setAttribute("aria-selected", String(isLive));
    demoModeTab.setAttribute("aria-selected", String(!isLive));
  }
  liveModeTab.addEventListener("click", () => setMode("live"));
  demoModeTab.addEventListener("click", () => setMode("demo"));

  // ---------- Demo Mode ----------
  const phraseCategories = document.getElementById("phraseCategories");
  const phraseSearch = document.getElementById("phraseSearch");
  const demoSourceText = document.getElementById("demoSourceText");
  const demoSantaliText = document.getElementById("demoSantaliText");
  const demoAudio = document.getElementById("demoAudio");
  const demoPlayBtn = document.getElementById("demoPlayBtn");
  const demoLangRadios = document.querySelectorAll('input[name="demoLang"]');

  let allPhrases = []; // Cache all phrases for filtering

  // The static file server here doesn't support HTTP Range requests, which
  // <audio src="..."> relies on to start loading -- it just stalls forever
  // (networkState stays "loading", readyState never advances). Fetching the
  // whole file as a blob sidesteps that entirely, and prefetching them all up
  // front makes every click instant with no per-click network wait. With
  // dozens of phrases, firing every fetch at once is unnecessary network/
  // memory pressure, so this runs them a few at a time instead.
  async function fetchAsBlobUrl(url) {
    const res = await fetch(url);
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  }

  const PREFETCH_CONCURRENCY = 5;
  async function prefetchWithConcurrencyLimit(items, worker) {
    let next = 0;
    async function runNext() {
      const i = next++;
      if (i >= items.length) return;
      await worker(items[i]);
      await runNext();
    }
    await Promise.all(Array.from({ length: PREFETCH_CONCURRENCY }, runNext));
  }

  function getSelectedDemoLang() {
    const selected = document.querySelector('input[name="demoLang"]:checked');
    return selected ? selected.value : "en";
  }

  function renderPhrasebook(phrases) {
    const byCategory = new Map();
    phrases.forEach((p) => {
      if (!byCategory.has(p.category)) byCategory.set(p.category, []);
      byCategory.get(p.category).push(p);
    });

    phraseCategories.innerHTML = "";
    const buttonJobs = [];
    for (const [category, items] of byCategory) {
      const section = document.createElement("div");
      section.className = "phrase-category";

      const heading = document.createElement("h3");
      heading.className = "phrase-category-title";
      heading.textContent = category;
      section.appendChild(heading);

      const grid = document.createElement("div");
      grid.className = "phrase-grid";
      section.appendChild(grid);

      items.forEach((p) => {
        const btn = document.createElement("button");
        btn.className = "phrase-btn";
        btn.textContent = p.source_text;
        btn.disabled = true;
        grid.appendChild(btn);
        buttonJobs.push({ phrase: p, btn });
      });

      phraseCategories.appendChild(section);
    }

    prefetchWithConcurrencyLimit(buttonJobs, async ({ phrase: p, btn }) => {
      const blobUrl = await fetchAsBlobUrl(p.audio_url);
      btn.disabled = false;
      btn.addEventListener("click", () => {
        demoSourceText.textContent = p.source_text;
        demoSantaliText.textContent = p.santali_text;
        demoAudio.src = blobUrl;
        demoPlayBtn.disabled = false;
        demoAudio.play().catch(() => {});
      });
    });
  }

  async function loadPhrasebook() {
    try {
      const res = await fetch("/api/phrasebook");
      allPhrases = await res.json();
      if (!allPhrases.length) {
        phraseCategories.innerHTML = '<p class="phrase-loading">No phrasebook found. Run scripts/build_phrasebook.py on the backend first.</p>';
        return;
      }
      const lang = getSelectedDemoLang();
      const filtered = allPhrases.filter(p => p.source_lang === lang);
      renderPhrasebook(filtered);
    } catch (err) {
      phraseCategories.innerHTML = '<p class="phrase-loading">Could not load phrasebook: ' + err.message + "</p>";
    }
  }

  function filterPhrasebook() {
    const lang = getSelectedDemoLang();
    const filtered = allPhrases.filter(p => p.source_lang === lang);
    renderPhrasebook(filtered);
  }

  demoLangRadios.forEach(radio => {
    radio.addEventListener("change", filterPhrasebook);
  });

  demoPlayBtn.addEventListener("click", () => demoAudio.play().catch(() => {}));
  document.getElementById("demoVolumeSlider").addEventListener("input", (e) => {
    demoAudio.volume = Number(e.target.value) / 100;
  });
  loadPhrasebook();

  phraseSearch.addEventListener("input", () => {
    const q = phraseSearch.value.trim().toLowerCase();
    phraseCategories.querySelectorAll(".phrase-category").forEach((section) => {
      let anyVisible = false;
      section.querySelectorAll(".phrase-btn").forEach((btn) => {
        const match = !q || btn.textContent.toLowerCase().includes(q);
        btn.hidden = !match;
        if (match) anyVisible = true;
      });
      section.hidden = !anyVisible;
    });
  });

  // ---------- Live Mode ----------
  const talkBtn = document.getElementById("talkBtn");
  const recordingIndicator = document.getElementById("recordingIndicator");
  const statusEl = document.getElementById("status");
  const sourceTextEl = document.getElementById("sourceText");
  const santaliTextEl = document.getElementById("santaliText");
  const cacheBadge = document.getElementById("cacheBadge");
  const santaliAudioEl = document.getElementById("santaliAudio");
  const playBtn = document.getElementById("playBtn");
  const audioStatusEl = document.getElementById("audioStatus");
  const errorBoxEl = document.getElementById("errorBox");
  const timingBoxEl = document.getElementById("timingBox");

  let ws = null;
  let mediaRecorder = null;
  let mediaStream = null;
  let isRecording = false;
  let currentRequestId = null;

  // WebSocket reconnection state
  let wsReconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 10;
  const BASE_RECONNECT_DELAY = 1000; // ms
  const MAX_RECONNECT_DELAY = 30000; // ms
  let wsReconnectTimer = null;
  let wsIntentionallyClosed = false;

  function setStatus(text) {
    statusEl.textContent = text;
  }
  function showError(message) {
    errorBoxEl.textContent = message;
    errorBoxEl.hidden = false;
  }
  function clearError() {
    errorBoxEl.hidden = true;
    errorBoxEl.textContent = "";
  }
  function wsUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${location.host}/ws/translate`;
  }

  function scheduleReconnect() {
    if (wsIntentionallyClosed) return;
    if (wsReconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      setStatus("Connection lost. Please refresh the page.");
      showError("Unable to reconnect to server. Please refresh the page.");
      return;
    }
    const delay = Math.min(BASE_RECONNECT_DELAY * Math.pow(2, wsReconnectAttempts), MAX_RECONNECT_DELAY);
    // Add jitter to avoid thundering herd
    const jitter = Math.random() * 500;
    const totalDelay = delay + jitter;
    wsReconnectAttempts++;
    setStatus(`Disconnected. Reconnecting in ${(totalDelay / 1000).toFixed(1)}s... (attempt ${wsReconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
    wsReconnectTimer = setTimeout(() => {
      ensureSocket();
    }, totalDelay);
  }

  function resetReconnectState() {
    wsReconnectAttempts = 0;
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = null;
    }
  }

  function ensureSocket() {
    // If there's already a socket in a good state, reuse it
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return ws;
    }
    // Clean up any existing socket
    if (ws) {
      ws.onopen = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.onmessage = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    }
    ws = new WebSocket(wsUrl());
    ws.onopen = () => {
      resetReconnectState();
      setStatus("Connected. Hold the button and speak.");
    };
    ws.onclose = () => {
      if (!wsIntentionallyClosed) {
        scheduleReconnect();
      }
    };
    ws.onerror = () => {
      // onclose will fire after onerror, so we don't need to schedule reconnect here
      // Just show a brief error if we're not already reconnecting
      if (wsReconnectAttempts === 0) {
        showError("Connection error. Reconnecting...");
      }
    };
    ws.onmessage = (event) => handleServerMessage(JSON.parse(event.data));
    return ws;
  }

  // ROOT CAUSE (found 2026-09-15): MediaRecorder's first dataavailable chunk
  // carries the WebM container header (verified: decoding the raw bytes
  // received server-side with that first chunk stripped off throws
  // "Invalid data found when processing input" -- every later chunk alone is
  // undecodable without it). ondataavailable only calls ws.send() when
  // ws.readyState === OPEN, silently dropping chunks otherwise, and
  // startRecording() used to call mediaRecorder.start() right after
  // ensureSocket() without waiting for the socket to actually finish
  // connecting. getUserMedia() often resolves near-instantly once permission
  // is already granted, so it could win the race against the WebSocket
  // handshake -- especially right after ws.onclose's "Reconnecting on next
  // press" -- dropping the header chunk and corrupting the whole utterance.
  // This surfaced as Whisper/decode silently "not hearing" the teacher even
  // though the browser had captured real audio. Waiting here guarantees the
  // socket is OPEN before the recorder's first chunk can ever be produced.
  function waitForSocketOpen(socket) {
    if (socket.readyState === WebSocket.OPEN) return Promise.resolve();
    return new Promise((resolve, reject) => {
      function cleanup() {
        socket.removeEventListener("open", onOpen);
        socket.removeEventListener("close", onFail);
        socket.removeEventListener("error", onFail);
      }
      function onOpen() {
        cleanup();
        resolve();
      }
      function onFail() {
        cleanup();
        reject(new Error("WebSocket failed to connect."));
      }
      socket.addEventListener("open", onOpen);
      socket.addEventListener("close", onFail);
      socket.addEventListener("error", onFail);
    });
  }

  function playAudioFromBase64(base64Audio) {
    const bytes = atob(base64Audio);
    const buffer = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) buffer[i] = bytes.charCodeAt(i);
    const blob = new Blob([buffer], { type: "audio/wav" });
    santaliAudioEl.src = URL.createObjectURL(blob);
    playBtn.disabled = false;
    santaliAudioEl.play().catch(() => {});
  }

  function getErrorMessage(data) {
    const errorCode = data.error_code;
    const baseMessage = data.message || "Unknown error.";
    
    switch (errorCode) {
      case "NO_SPEECH":
        return "No speech detected. Please try speaking louder or closer to the microphone.";
      case "NO_AUDIO":
        return "No audio received. Please hold the button longer while speaking.";
      case "AUDIO_TOO_LONG":
        return "Recording too long. Please keep utterances under 30 seconds.";
      case "STT_TRANSLATE_FAILED":
        return "Failed to process speech. Please try again.";
      case "PROCESSING_TIMEOUT":
        return "Processing timed out. Please try a shorter phrase.";
      case "PROCESSING_ERROR":
        return "Processing error. Please try again.";
      case "WS_TIMEOUT":
        return "Connection timed out. Please try again.";
      case "SERVER_ERROR":
        return "Server error. Please refresh the page and try again.";
      case "CACHE_MISSING":
        return "Cached audio unavailable. Generating live audio instead...";
      case "INVALID_JSON":
        return "Invalid message format. Please refresh the page.";
      default:
        return baseMessage;
    }
  }

  function handleServerMessage(data) {
    if (data.type === "processing") {
      setStatus("Recognizing speech and translating...");
      return;
    }

    if (data.type === "error") {
      showError(getErrorMessage(data));
      setStatus("Idle. Hold the button and speak.");
      talkBtn.disabled = false;
      return;
    }

    if (data.type === "text_result") {
      clearError();
      currentRequestId = data.request_id;
      sourceTextEl.textContent = data.source_text || "—";
      santaliTextEl.textContent = data.text || "—";
      cacheBadge.hidden = true;
      playBtn.disabled = true;
      audioStatusEl.textContent = "";

      if (data.timing) {
        const t = data.timing;
        timingBoxEl.textContent =
          `upload ${t.audio_upload.toFixed(1)}s | stt ${t.stt.toFixed(1)}s | ` +
          `translate ${t.translate.toFixed(1)}s | match ${(t.phrase_matching * 1000).toFixed(0)}ms | ` +
          `total text ${t.total_text_latency.toFixed(1)}s`;
      }

      setStatus("Text ready. Audio follows below.");
      talkBtn.disabled = false;
      return;
    }

    if (data.type === "audio_result") {
      if (data.request_id !== currentRequestId) return; // stale, a newer utterance is showing
      cacheBadge.hidden = data.source !== "cache";
      cacheBadge.textContent = "instant (cached phrase)";
      if (data.source === "cache") {
        audioStatusEl.textContent = `Cached audio (total ${data.timing.total_cached_audio_latency.toFixed(1)}s).`;
      } else {
        audioStatusEl.textContent = `Live audio ready (${data.timing.tts.toFixed(1)}s to generate).`;
      }
      playAudioFromBase64(data.audio);
      return;
    }

    if (data.type === "audio_pending") {
      if (data.request_id !== currentRequestId) return;
      audioStatusEl.textContent = data.message;
      return;
    }

    if (data.type === "audio_error") {
      if (data.request_id !== currentRequestId) return;
      showError(data.message || "Live audio generation failed.");
      return;
    }
  }

  async function startRecording() {
    // Item 6: only one recording per Hold-to-Speak press. talkBtn.disabled
    // during processing already prevents this via the UI, but guard directly
    // too in case startRecording is ever invoked some other way.
    if (mediaRecorder && mediaRecorder.state === "recording") {
      console.warn("[audio-debug] startRecording called while already recording -- ignoring.");
      return;
    }

    clearError();
    const socket = ensureSocket();

    // Improved microphone constraints for better speech recognition
    // echoCancellation, noiseSuppression, autoGainControl help in classroom environments
    const audioConstraints = {
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 16000,  // Whisper expects 16kHz
      }
    };

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia(audioConstraints);
    } catch (err) {
      // Fallback to basic audio if constraints not supported
      console.warn("[audio-debug] Constrained getUserMedia failed, falling back:", err.message);
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (err2) {
        showError("Could not access the microphone: " + err2.message);
        return;
      }
    }

    try {
      await waitForSocketOpen(socket);
    } catch (err) {
      showError("Could not connect to the server: " + err.message);
      mediaStream.getTracks().forEach((t) => t.stop());
      mediaStream = null;
      return;
    }

    // Diagnostics -- which mic device was actually selected, and
    // what MediaRecorder MIME types this browser actually supports.
    const track = mediaStream.getAudioTracks()[0];
    console.log("[audio-debug] mic track:", track && track.label, track && track.getSettings());
    console.log(
      "[audio-debug] isTypeSupported webm+opus:",
      MediaRecorder.isTypeSupported("audio/webm;codecs=opus"),
      "| webm (no codec):",
      MediaRecorder.isTypeSupported("audio/webm")
    );

    // audio/webm;codecs=opus is used when supported (Chrome/Edge/Firefox all
    // support it) -- PyAV/ffmpeg (which faster-whisper uses internally to
    // decode the received file) reads Opus-in-WebM natively and reliably;
    // this is the same combination Chrome's own WebRTC stack uses, so it's
    // about as safe a choice as exists for this pipeline.
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType });

    let recordStartTime = performance.now();
    console.log(`[audio-debug] recording start t=0ms mimeType=${mediaRecorder.mimeType}`);

    mediaRecorder.ondataavailable = (event) => {
      if (!(event.data && event.data.size > 0)) return;
      const chunkIndex = mediaRecorder._chunkIndex || 0;
      mediaRecorder._chunkIndex = chunkIndex + 1;
      console.log(
        `[audio-debug] chunk ${chunkIndex} size=${event.data.size}B t=${(performance.now() - recordStartTime).toFixed(0)}ms`
      );
      // Sent synchronously and in the exact order dataavailable fires, as a
      // Blob directly -- WebSocket.send() accepts Blob natively.
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const stopTime = performance.now();
      console.log(
        `[audio-debug] recording stop t=${(stopTime - recordStartTime).toFixed(0)}ms`
      );

      mediaStream.getTracks().forEach((track) => track.stop());
      if (ws && ws.readyState === WebSocket.OPEN) {
        const selected = document.querySelector('input[name="sourceLang"]:checked');
        const language = selected ? selected.value : "en";
        ws.send(
          JSON.stringify({
            type: "end",
            language,
            mimeType: mediaRecorder.mimeType,
          })
        );
      }
    };

    mediaRecorder.start(1000);
    isRecording = true;
    talkBtn.classList.add("recording");
    talkBtn.textContent = "Listening...";
    recordingIndicator.hidden = false;
    setStatus("Recording...");
  }

  function stopRecording() {
    if (!isRecording) return;
    isRecording = false;
    talkBtn.classList.remove("recording");
    talkBtn.textContent = "Hold to Speak";
    talkBtn.disabled = true;
    recordingIndicator.hidden = true;
    setStatus("Finishing recording...");
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
  }

  talkBtn.addEventListener("mousedown", startRecording);
  talkBtn.addEventListener("touchstart", (e) => {
    e.preventDefault();
    startRecording();
  });
  ["mouseup", "mouseleave"].forEach((evt) =>
    talkBtn.addEventListener(evt, () => {
      if (isRecording) stopRecording();
    })
  );
  talkBtn.addEventListener("touchend", (e) => {
    e.preventDefault();
    if (isRecording) stopRecording();
  });
  playBtn.addEventListener("click", () => santaliAudioEl.play().catch(() => {}));
  document.getElementById("volumeSlider").addEventListener("input", (e) => {
    santaliAudioEl.volume = Number(e.target.value) / 100;
  });

  // Handle page unload - intentionally close WebSocket
  window.addEventListener("beforeunload", () => {
    wsIntentionallyClosed = true;
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer);
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });
})();
