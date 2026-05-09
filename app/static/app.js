class ApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  setBaseUrl(value) {
    this.baseUrl = (value || "").replace(/\/$/, "");
  }

  url(path) {
    if (!this.baseUrl) return path;
    return `${this.baseUrl}${path}`;
  }

  async request(path, options = {}) {
    const resp = await fetch(this.url(path), {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });

    let body = null;
    const contentType = resp.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      body = await resp.json();
    }

    if (!resp.ok) {
      const message = body?.error?.message || `Request failed: ${resp.status}`;
      throw new Error(message);
    }
    return body;
  }

  listUsers(includeDeleted = false) {
    return this.request(`/v1/users?include_deleted=${includeDeleted}`, { method: "GET" });
  }

  createUser(displayName) {
    return this.request("/v1/users", {
      method: "POST",
      body: JSON.stringify({ display_name: displayName }),
    });
  }

  deleteUser(userId) {
    return this.request(`/v1/users/${userId}`, { method: "DELETE" });
  }

  restoreUser(userId) {
    return this.request(`/v1/users/${userId}/restore`, { method: "POST" });
  }

  listTexts(userId, language = "hebrew") {
    return this.request(`/v1/users/${userId}/texts?language=${encodeURIComponent(language)}`, { method: "GET" });
  }

  createText(userId, title, content, language = "hebrew") {
    return this.request(`/v1/users/${userId}/texts`, {
      method: "POST",
      body: JSON.stringify({ title, content, language }),
    });
  }

  renameText(userId, textId, title) {
    return this.request(`/v1/users/${userId}/texts/${textId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  }

  deleteText(userId, textId) {
    return this.request(`/v1/users/${userId}/texts/${textId}`, { method: "DELETE" });
  }

  loadSentence(userId, textId, sentenceIndex) {
    return this.request(`/v1/users/${userId}/texts/${textId}/sentences/${sentenceIndex}`, { method: "GET" });
  }

  markSentenceNikkudOff(userId, textId, sentenceIndex) {
    return this.request(`/v1/users/${userId}/texts/${textId}/sentences/${sentenceIndex}/nikkud-off`, { method: "POST" });
  }

  getTextPosition(userId, textId) {
    return this.request(`/v1/users/${userId}/texts/${textId}/position`, { method: "GET" });
  }

  updateTextPosition(userId, textId, sentenceIndex) {
    return this.request(`/v1/users/${userId}/texts/${textId}/position`, {
      method: "PUT",
      body: JSON.stringify({ sentence_index: sentenceIndex }),
    });
  }

  updateWordState(userId, normalizedWord, state, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}?language=${encodeURIComponent(language)}`, {
      method: "PUT",
      body: JSON.stringify({ state }),
    });
  }

  listWords(userId, state = "all", page = 1, limit = 50, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words?state=${state}&page=${page}&limit=${limit}&language=${encodeURIComponent(language)}`, {
      method: "GET",
    });
  }

  listMeanings(userId, normalizedWord, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings?language=${encodeURIComponent(language)}`, {
      method: "GET",
    });
  }

  createMeaning(userId, normalizedWord, meaningText, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings?language=${encodeURIComponent(language)}`, {
      method: "POST",
      body: JSON.stringify({ meaning_text: meaningText }),
    });
  }

  restateSentence(userId, textId, sentenceIndex) {
    return this.request(`/v1/users/${userId}/texts/${textId}/sentences/${sentenceIndex}/restate`, { method: "POST" });
  }

  analyzeSentenceGrammar(userId, textId, sentenceIndex) {
    return this.request(`/v1/users/${userId}/texts/${textId}/sentences/${sentenceIndex}/grammar`, { method: "POST" });
  }

  generateMeaning(userId, normalizedWord, sentenceContext, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/generate?language=${encodeURIComponent(language)}`, {
      method: "POST",
      body: JSON.stringify({ sentence_context: sentenceContext || null }),
    });
  }

  updateMeaning(userId, normalizedWord, meaningId, meaningText, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/${meaningId}?language=${encodeURIComponent(language)}`, {
      method: "PUT",
      body: JSON.stringify({ meaning_text: meaningText }),
    });
  }

  deleteMeaning(userId, normalizedWord, meaningId, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/${meaningId}?language=${encodeURIComponent(language)}`, {
      method: "DELETE",
    });
  }

  getWordDetails(userId, normalizedWord, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/details?language=${encodeURIComponent(language)}`, {
      method: "GET",
    });
  }

  updateWordDetails(userId, normalizedWord, mnemonic, language = "hebrew") {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/details?language=${encodeURIComponent(language)}`, {
      method: "PUT",
      body: JSON.stringify({ mnemonic }),
    });
  }

  getSrsSession(userId, timezoneOffsetMinutes, language = "hebrew") {
    return this.request(
      `/v1/users/${userId}/srs/session?timezone_offset_minutes=${encodeURIComponent(timezoneOffsetMinutes)}&language=${encodeURIComponent(language)}`,
      { method: "GET" }
    );
  }

  addSrsNewCards(userId, count, timezoneOffsetMinutes, language = "hebrew") {
    return this.request(`/v1/users/${userId}/srs/session/add-new`, {
      method: "POST",
      body: JSON.stringify({ count, timezone_offset_minutes: timezoneOffsetMinutes, language }),
    });
  }

  submitSrsReview(userId, normalizedWord, result, language = "hebrew") {
    return this.request(`/v1/users/${userId}/srs/review`, {
      method: "POST",
      body: JSON.stringify({ normalized_word: normalizedWord, result, language }),
    });
  }

  getBackupStatus() {
    return this.request("/v1/backup/status", { method: "GET" });
  }

  getProgressHistory(userId, range, language = "hebrew") {
    return this.request(`/v1/users/${userId}/progress/history?range=${encodeURIComponent(range)}&language=${encodeURIComponent(language)}`, { method: "GET" });
  }

  getWordsReadHistory(userId, range, language = "hebrew") {
    return this.request(`/v1/users/${userId}/progress/words-read?range=${encodeURIComponent(range)}&language=${encodeURIComponent(language)}`, { method: "GET" });
  }

  getSrsHistory(userId, range, language = "hebrew") {
    return this.request(`/v1/users/${userId}/progress/srs-history?range=${encodeURIComponent(range)}&language=${encodeURIComponent(language)}`, { method: "GET" });
  }

  getWordsReadSummary(userId, language = "hebrew") {
    return this.request(`/v1/users/${userId}/progress/words-read-summary?language=${encodeURIComponent(language)}`, { method: "GET" });
  }
}

// Percentage of words that are unique (not just variants with prefixes)
// Calculated from corpus: 714 unique base words / 881 total = 81.04%
const UNIQUE_WORD_ESTIMATE_PERCENT = 0.8104;

// Vocabulary milestone levels
const VOCAB_MILESTONES = [
  { threshold: 100, name: "Bronze", color: "#cd7f32" },
  { threshold: 500, name: "Silver", color: "#c0c0c0" },
  { threshold: 1000, name: "Gold", color: "#ffd700" },
  { threshold: 2000, name: "Platinum", color: "#e5e4e2" },
  { threshold: 4000, name: "Diamond", color: "#b9f2ff" },
];

function getCurrentVocabLevel(knownWords) {
  let currentLevel = null;
  for (const milestone of VOCAB_MILESTONES) {
    if (knownWords >= milestone.threshold) {
      currentLevel = milestone;
    } else {
      break;
    }
  }
  return currentLevel;
}

const state = {
  api: new ApiClient(localStorage.getItem("api_base_url") || ""),
  includeDeleted: false,
  users: [],
  activeUserId: localStorage.getItem("active_user_id") || "",
  texts: [],
  openTextId: "",
  sentenceIndex: 0,
  maxSentenceIndex: null,
  selectedWord: "",
  currentSentence: null,
  wordsPage: 1,
  wordsLimit: 50,
  currentView: "library",
  currentLanguage: localStorage.getItem("current_language") || "hebrew",
  isLoggedIn: !!localStorage.getItem("active_user_id"),
  selectedTextId: null,
  readerShowNikkud: false,
  srsDueQueue: [],
  srsCurrentCard: null,
  srsRevealed: false,
  srsDefinitions: [],
  srsMnemonic: null,
  srsMnemonicEditing: false,
  srsLoadingDetailsForWord: "",
  srsDailyNewRemaining: 0,
  srsAvailableNewCount: 0,
  srsDailyResetAt: "",
  srsUndoHistory: [], // Stack of {card, result, definitions, mnemonic}
  srsCardFlipped: false,
  progressRange: "month",
  progressShowUnique: true,
  progressChart: null,
  wordsReadChart: null,
  srsHistoryChart: null,
  requestVersion: {
    users: 0,
    texts: 0,
    sentence: 0,
    words: 0,
    meanings: 0,
    wordDetails: 0,
    wordSave: 0,
    srsSession: 0,
    srsDetails: 0,
    srsReview: 0,
    progressHistory: 0,
    wordsReadHistory: 0,
    srsHistory: 0,
  },
};

const el = {
  appRoot: document.querySelector("[data-testid='app-root']"),
  appHeader: document.getElementById("app-header"),
  mainContent: document.getElementById("main-content"),
  navLibrary: document.getElementById("nav-library"),
  navSrs: document.getElementById("nav-srs"),
  logoutLink: document.getElementById("logout-link"),
  userSelectionModal: document.getElementById("user-selection-modal"),
  userPicker: document.getElementById("user-picker"),
  userPickConfirm: document.getElementById("user-pick-confirm"),
  sectionLibrary: document.getElementById("section-library"),
  sectionReader: document.getElementById("section-reader"),
  sectionSrs: document.getElementById("section-srs"),
  readerExitBtn: document.getElementById("reader-exit-btn"),
  libraryGrid: document.getElementById("library-grid"),
  includeDeleted: document.getElementById("include-deleted"),
  refreshUsers: document.getElementById("refresh-users"),
  createUserForm: document.getElementById("create-user-form"),
  newUserName: document.getElementById("new-user-name"),
  activeUser: document.getElementById("active-user"),
  usersState: document.getElementById("users-state"),
  usersList: document.getElementById("users-list"),
  refreshTexts: document.getElementById("refresh-texts"),
  createTextForm: document.getElementById("create-text-form"),
  newTextTitle: document.getElementById("new-text-title"),
  newTextContent: document.getElementById("new-text-content"),
  textsState: document.getElementById("texts-state"),
  textsList: document.getElementById("texts-list"),
  readerMeta: document.getElementById("reader-meta"),
  readerState: document.getElementById("reader-state"),
  readerSentence: document.getElementById("reader-sentence"),
  prevSentence: document.getElementById("prev-sentence"),
  nextSentence: document.getElementById("next-sentence"),
  btnRestate: document.getElementById("btn-restate"),
  btnGrammar: document.getElementById("btn-grammar"),
  restatePanel: document.getElementById("restate-panel"),
  grammarPanel: document.getElementById("grammar-panel"),
  restateText: document.getElementById("restate-text"),
  grammarText: document.getElementById("grammar-text"),
  wordDetailsPanel: document.getElementById("word-details-panel"),
  wordDetailsWord: document.getElementById("word-details-word"),
  wordDetailsStatus: document.getElementById("word-details-status"),
  wordDetailsState: document.getElementById("word-details-state"),
  mnemonicForm: document.getElementById("mnemonic-form"),
  wordMnemonic: document.getElementById("word-mnemonic"),
  mnemonicState: document.getElementById("mnemonic-state"),
  addMeaningForm: document.getElementById("add-meaning-form"),
  manualMeaning: document.getElementById("manual-meaning"),
  generateMeaningForm: document.getElementById("generate-meaning-form"),
  meaningContext: document.getElementById("meaning-context"),
  meaningsState: document.getElementById("meanings-state"),
  meaningsPreview: document.getElementById("meanings-preview"),
  meaningsList: document.getElementById("meanings-list"),
  wordsFilter: document.getElementById("words-filter"),
  wordsLimit: document.getElementById("words-limit"),
  wordsPrevPage: document.getElementById("words-prev-page"),
  wordsNextPage: document.getElementById("words-next-page"),
  wordsPageLabel: document.getElementById("words-page-label"),
  refreshWords: document.getElementById("refresh-words"),
  wordsState: document.getElementById("words-state"),
  wordsList: document.getElementById("words-list"),
  viewButtons: Array.from(document.querySelectorAll("[data-view-target]")),
  viewPanels: Array.from(document.querySelectorAll("[data-view-panel]")),
  srsMeta: document.getElementById("srs-meta"),
  srsState: document.getElementById("srs-state"),
  srsReviewer: document.getElementById("srs-reviewer"),
  srsFrontWord: document.getElementById("srs-front-word"),
  srsReveal: document.getElementById("srs-reveal"),
  srsDefinitions: document.getElementById("srs-definitions"),
  srsMnemonicView: document.getElementById("srs-mnemonic-view"),
  srsMnemonicForm: document.getElementById("srs-mnemonic-form"),
  srsMnemonicInput: document.getElementById("srs-mnemonic-input"),
  srsMnemonicSave: document.getElementById("srs-mnemonic-save"),
  srsShow: document.getElementById("srs-show"),
  srsWrong: document.getElementById("srs-wrong"),
  srsRight: document.getElementById("srs-right"),
  srsAddNew: document.getElementById("srs-add-new"),
  srsAddNewForm: document.getElementById("srs-add-new-form"),
  srsAddCount: document.getElementById("srs-add-count"),
  srsAddSubmit: document.getElementById("srs-add-submit"),
  srsCaughtUp: document.getElementById("srs-caught-up"),
  backupStatus: document.getElementById("backup-status"),
  navProgress: document.getElementById("nav-progress"),
  sectionProgress: document.getElementById("section-progress"),
  progressState: document.getElementById("progress-state"),
  progressChartCanvas: document.getElementById("progress-chart"),
  progressLevel: document.getElementById("progress-level"),
  wordsReadChartCanvas: document.getElementById("words-read-chart"),
  wordsReadState: document.getElementById("words-read-state"),
  wordsReadSummary: document.getElementById("words-read-summary"),
  srsHistoryChartCanvas: document.getElementById("srs-history-chart"),
  srsHistoryState: document.getElementById("srs-history-state"),
  progressRangeBtns: [
    document.getElementById("progress-range-month"),
    document.getElementById("progress-range-year"),
    document.getElementById("progress-range-all"),
  ],
};
const VIEW_ORDER = ["library", "reader", "words", "srs"];

function nextRequestVersion(key) {
  state.requestVersion[key] += 1;
  return state.requestVersion[key];
}

function isCurrentRequest(key, version) {
  return state.requestVersion[key] === version;
}

function setStateMessage(node, text, isError = false) {
  if (!node) return;
  node.textContent = text || "";
  node.classList.toggle("error", Boolean(isError));
  node.classList.toggle("loading", text === "Loading...");
  node.classList.toggle("empty", text === "Empty");
}

function renderListState(listNode, stateNode, options) {
  if (!listNode || !stateNode) return true;
  const {
    loading = false,
    error = "",
    empty = false,
    emptyMessage = "Nothing to show",
    totalLabel = "",
  } = options;

  if (loading) {
    listNode.innerHTML = "";
    setStateMessage(stateNode, "Loading...");
    return true;
  }
  if (error) {
    listNode.innerHTML = "";
    setStateMessage(stateNode, error, true);
    return true;
  }
  if (empty) {
    listNode.innerHTML = "";
    setStateMessage(stateNode, "Empty");
    const li = document.createElement("li");
    li.className = "empty-row";
    li.textContent = emptyMessage;
    listNode.appendChild(li);
    return true;
  }

  setStateMessage(stateNode, totalLabel);
  return false;
}

function requireUser() {
  if (!state.activeUserId) {
    throw new Error("Select a user first");
  }
}

function clearWordDetailsPanel() {
  state.selectedWord = "";
  el.wordDetailsPanel.classList.add("is-hidden");
  el.wordDetailsWord.textContent = "No word selected";
  el.wordDetailsStatus.textContent = "Unseen";
  setStateMessage(el.wordDetailsState, "");
  setStateMessage(el.mnemonicState, "");
  setStateMessage(el.meaningsState, "");
  el.wordMnemonic.value = "";
  el.manualMeaning.value = "";
  el.meaningContext.value = "";
  el.meaningsPreview.innerHTML = "";
  el.meaningsList.innerHTML = "";
}

// === View Management Functions ===

function updateViewVisibility() {
  const v = state.currentView;
  const loggedIn = state.isLoggedIn;

  // Hide/show header
  el.appHeader.classList.toggle("is-hidden", !loggedIn || v === "reader");

  // Hide/show sections
  el.sectionLibrary.classList.toggle("active", loggedIn && v === "library");
  el.sectionSrs.classList.toggle("active", loggedIn && v === "srs");
  el.sectionProgress.classList.toggle("active", loggedIn && v === "progress");
  el.sectionReader.classList.toggle("active", loggedIn && v === "reader");

  // Hide/show exit button
  el.readerExitBtn.classList.toggle("active", v === "reader");

  // Update nav button active state
  if (el.navLibrary) el.navLibrary.classList.toggle("active", v === "library");
  if (el.navSrs) el.navSrs.classList.toggle("active", v === "srs");
  if (el.navProgress) el.navProgress.classList.toggle("active", v === "progress");
}

function switchView(view) {
  state.currentView = view;
  updateViewVisibility();

  // Side effects
  if (view === "srs" && state.isLoggedIn) {
    void loadSrsSession();
  }
  if (view === "progress" && state.isLoggedIn) {
    void loadProgressData();
    void loadWordsReadData();
    void loadWordsReadSummary();
    void loadSrsHistoryData();
  }
  if (view !== "reader") {
    clearWordDetailsPanel();
    renderSentence();
  }
}

function showUserSelection() {
  el.userSelectionModal.classList.remove("is-hidden");
}

function hideUserSelection() {
  el.userSelectionModal.classList.add("is-hidden");
}

async function renderUserPicker() {
  el.userPicker.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "-- Select a user --";
  el.userPicker.appendChild(empty);

  for (const user of state.users.filter((u) => u.deleted_at === null)) {
    const option = document.createElement("option");
    option.value = user.user_id;
    option.textContent = user.display_name;
    el.userPicker.appendChild(option);
  }
}

async function handleUserPick(userId) {
  if (!userId) return;
  state.activeUserId = userId;
  state.isLoggedIn = true;
  localStorage.setItem("active_user_id", userId);
  hideUserSelection();
  updateLanguageSwitcher();
  updateDirectionAttributes();
  await Promise.all([loadTexts(), loadWords()]);
  switchView("library");
}

function handleLogout() {
  state.activeUserId = "";
  state.isLoggedIn = false;
  state.selectedTextId = null;
  localStorage.removeItem("active_user_id");
  el.userPicker.value = "";
  updateLanguageSwitcher();
  showUserSelection();
}

const LANG_ATTRS = {
  hebrew: { dir: "rtl", lang: "he" },
  latin:  { dir: "ltr", lang: "la" },
};

function updateDirectionAttributes() {
  const attrs = LANG_ATTRS[state.currentLanguage] || LANG_ATTRS.hebrew;
  const sentence = document.getElementById("reader-sentence");
  const srsWord = document.getElementById("srs-front-word");
  const selectedWordDisplay = document.getElementById("word-details-word");
  if (sentence) { sentence.setAttribute("dir", attrs.dir); sentence.setAttribute("lang", attrs.lang); }
  if (srsWord) { srsWord.setAttribute("dir", attrs.dir); srsWord.setAttribute("lang", attrs.lang); }
  if (selectedWordDisplay) { selectedWordDisplay.setAttribute("dir", attrs.dir); selectedWordDisplay.setAttribute("lang", attrs.lang); }
}

function updateLanguageSwitcher() {
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.lang === state.currentLanguage);
  });
  const switcher = document.getElementById("language-switcher");
  if (switcher) {
    if (state.isLoggedIn) {
      switcher.classList.add("visible");
    } else {
      switcher.classList.remove("visible");
    }
  }
}

function handleLanguageSwitch(lang) {
  if (lang === state.currentLanguage) return;
  state.currentLanguage = lang;
  localStorage.setItem("current_language", lang);
  updateLanguageSwitcher();
  updateDirectionAttributes();
  void loadTexts();
  if (state.currentView === "srs") void loadSrsSession();
  if (state.currentView === "progress") {
    void loadProgressData();
    void loadWordsReadData();
    void loadWordsReadSummary();
    void loadSrsHistoryData();
  }
}

function colorForPercentage(pct) {
  const ranges = [
    [0, 70, [254, 226, 226], [220, 38, 38]],
    [70, 80, [254, 243, 199], [245, 158, 11]],
    [80, 90, [254, 249, 195], [132, 204, 22]],
    [90, 101, [220, 252, 231], [34, 197, 94]],
  ];

  for (const [lo, hi, from, to] of ranges) {
    if (pct >= lo && pct < hi) {
      const t = (pct - lo) / (hi - lo);
      const r = Math.round(from[0] + t * (to[0] - from[0]));
      const g = Math.round(from[1] + t * (to[1] - from[1]));
      const b = Math.round(from[2] + t * (to[2] - from[2]));
      return `rgb(${r},${g},${b})`;
    }
  }
  return `rgb(34,197,94)`;
}

async function renderLibraryGrid() {
  if (!state.activeUserId) return;

  const grid = el.libraryGrid;
  if (!grid) return;
  grid.innerHTML = "";

  if (state.texts.length === 0) {
    grid.className = "empty-state";
    const empty = document.createElement("div");
    empty.textContent = "No texts yet. Create one to get started.";
    grid.appendChild(empty);
    return;
  }

  grid.className = "";
  for (const text of state.texts) {
    const progress = text.progress || {};
    const knownPct = progress.known_percent ?? 0;
    const stage4Pct = progress.stage4_percent ?? 0;
    const highestPct = Math.max(knownPct, stage4Pct);
    const bgColor = colorForPercentage(highestPct);
    const totalWords = progress.total_words ?? (progress.known_count + progress.unknown_count + progress.never_seen_count) ?? 0;

    const widget = document.createElement("div");
    widget.className = "text-widget";
    widget.style.backgroundColor = bgColor;

    const title = document.createElement("h3");
    title.className = "text-widget__title";
    title.textContent = text.title;

    const stats = document.createElement("div");
    stats.className = "text-widget__stats";
    stats.innerHTML = `
      <div>Words: ${totalWords.toLocaleString()}</div>
      <div>Known: ${knownPct.toFixed(1)}% | Stage 4+: ${stage4Pct.toFixed(1)}%</div>
    `;

    const actionButtons = document.createElement("div");
    actionButtons.className = "action-buttons";

    const editBtn = document.createElement("button");
    editBtn.textContent = "✎";
    editBtn.type = "button";
    editBtn.onclick = (e) => {
      e.stopPropagation();
      void handleEditText(text.text_id, text.title);
    };

    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "🗑";
    deleteBtn.type = "button";
    deleteBtn.onclick = (e) => {
      e.stopPropagation();
      void handleDeleteText(text.text_id, text.title);
    };

    actionButtons.appendChild(editBtn);
    actionButtons.appendChild(deleteBtn);

    widget.appendChild(actionButtons);
    widget.appendChild(title);
    widget.appendChild(stats);

    widget.onclick = () => selectTextForReading(text.text_id);

    grid.appendChild(widget);
  }
}

async function selectTextForReading(textId) {
  state.openTextId = textId;
  state.selectedTextId = textId;
  const pos = await state.api.getTextPosition(state.activeUserId, textId);
  state.sentenceIndex = pos.sentence_index ?? 0;
  switchView("reader");
  await loadSentence();
}

function handleReaderExit() {
  state.selectedTextId = null;
  switchView("library");
}

async function handleEditText(textId, currentTitle) {
  const newTitle = prompt("Rename text:", currentTitle);
  if (!newTitle || newTitle === currentTitle) return;

  try {
    await state.api.renameText(state.activeUserId, textId, newTitle);
    await loadTexts();
  } catch (err) {
    console.error("Rename failed:", err);
  }
}

async function handleDeleteText(textId, title) {
  const confirmed = confirm(`Delete "${title}"? This cannot be undone.`);
  if (!confirmed) return;

  try {
    await state.api.deleteText(state.activeUserId, textId);
    await loadTexts();
  } catch (err) {
    console.error("Delete failed:", err);
  }
}

function setActiveView(viewName, persist = true) {
  const allowedViews = new Set(VIEW_ORDER);
  const nextView = allowedViews.has(viewName) ? viewName : "library";
  state.currentView = nextView;
  if (el.appRoot) {
    el.appRoot.classList.remove("view-library", "view-reader", "view-words", "view-srs");
    el.appRoot.classList.add(`view-${nextView}`);
  }
  if (persist) {
    localStorage.setItem("active_view", nextView);
  }

  for (const btn of el.viewButtons) {
    const isActive = btn.dataset.viewTarget === nextView;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-selected", isActive ? "true" : "false");
    btn.tabIndex = isActive ? 0 : -1;
  }
  for (const panel of el.viewPanels) {
    panel.classList.toggle("is-hidden", panel.dataset.viewPanel !== nextView);
  }

  if (nextView !== "reader") {
    clearWordDetailsPanel();
    renderSentence();
  }
  if (nextView === "srs" && state.activeUserId) {
    void loadSrsSession();
  }
}

function focusView(viewName) {
  const target = el.viewButtons.find((btn) => btn.dataset.viewTarget === viewName);
  if (target) {
    target.focus();
  }
}

function renderUserSelector() {
  el.activeUser.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "No user selected";
  el.activeUser.appendChild(empty);

  for (const user of state.users.filter((u) => u.deleted_at === null)) {
    const option = document.createElement("option");
    option.value = user.user_id;
    option.textContent = user.display_name;
    el.activeUser.appendChild(option);
  }

  el.activeUser.value = state.activeUserId;
}

function renderUsersList() {
  if (
    renderListState(el.usersList, el.usersState, {
      empty: state.users.length === 0,
      emptyMessage: "No users yet",
    })
  ) {
    return;
  }

  el.usersList.innerHTML = "";
  for (const user of state.users) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${user.display_name}</strong> <small>${user.user_id}</small>`;

    const actions = document.createElement("div");
    if (user.deleted_at) {
      const restore = document.createElement("button");
      restore.type = "button";
      restore.textContent = "Restore";
      restore.onclick = async () => {
        await state.api.restoreUser(user.user_id);
        await loadUsers();
      };
      actions.appendChild(restore);
    } else {
      const del = document.createElement("button");
      del.type = "button";
      del.textContent = "Delete";
      del.onclick = async () => {
        await state.api.deleteUser(user.user_id);
        if (state.activeUserId === user.user_id) {
          state.activeUserId = "";
          localStorage.removeItem("active_user_id");
        }
        await loadUsers();
        clearUserScopedViews();
      };
      actions.appendChild(del);
    }

    li.appendChild(actions);
    el.usersList.appendChild(li);
  }
}

function clearUserScopedViews() {
  state.texts = [];
  state.openTextId = "";
  state.maxSentenceIndex = null;
  state.currentSentence = null;
  state.wordsPage = 1;
  if (el.textsList) el.textsList.innerHTML = "";
  el.readerMeta.textContent = "No text open";
  setStateMessage(el.readerState, "");
  el.readerSentence.textContent = "";
  if (el.wordsList) el.wordsList.innerHTML = "";
  el.wordsPageLabel.textContent = "Page 1";
  el.wordsPrevPage.disabled = true;
  el.wordsNextPage.disabled = true;
  clearWordDetailsPanel();
  clearSrsState();
  state.progressRange = "month";
  state.progressShowUnique = false;
  if (el.progressUniqueToggle) el.progressUniqueToggle.checked = false;
  if (state.progressChart) { state.progressChart.destroy(); state.progressChart = null; }
  if (state.wordsReadChart) { state.wordsReadChart.destroy(); state.wordsReadChart = null; }
  if (state.srsHistoryChart) { state.srsHistoryChart.destroy(); state.srsHistoryChart = null; }
  setStateMessage(el.progressState, "");
  setStateMessage(el.wordsReadState, "");
  setStateMessage(el.srsHistoryState, "");
  if (el.wordsReadSummary) el.wordsReadSummary.innerHTML = "";
}

function clearSrsState() {
  state.srsDueQueue = [];
  state.srsCurrentCard = null;
  state.srsRevealed = false;
  state.srsDefinitions = [];
  state.srsMnemonic = null;
  state.srsMnemonicEditing = false;
  state.srsLoadingDetailsForWord = "";
  state.srsDailyNewRemaining = 0;
  state.srsAvailableNewCount = 0;
  state.srsDailyResetAt = "";
  state.srsUndoHistory = [];
  state.srsCardFlipped = false;
  el.srsMeta.textContent = "No session loaded";
  setStateMessage(el.srsState, "");
  renderSrs();
}

function timezoneOffsetMinutes() {
  return new Date().getTimezoneOffset();
}

function srsReinsertWrongCard(card) {
  if (!card) return;
  const len = state.srsDueQueue.length;
  if (len >= 2) {
    // Insert at a random position between index 2 and end (inclusive)
    const insertAt = 2 + Math.floor(Math.random() * (len - 1));
    state.srsDueQueue.splice(insertAt, 0, card);
    return;
  }
  state.srsDueQueue.push(card);
}

function renderSrsDefinitions() {
  if (el.srsDefinitions) el.srsDefinitions.innerHTML = "";
  if (state.srsDefinitions.length === 0) {
    const li = document.createElement("li");
    li.className = "empty-row";
    li.textContent = "No definitions yet";
    el.srsDefinitions.appendChild(li);
    return;
  }
  for (const item of state.srsDefinitions) {
    const li = document.createElement("li");
    li.textContent = item.meaning_text;
    el.srsDefinitions.appendChild(li);
  }
}

function renderSrsMnemonic() {
  const hasMnemonic = Boolean((state.srsMnemonic || "").trim());
  const displayText = hasMnemonic ? state.srsMnemonic : "No mnemonic yet";

  el.srsMnemonicView.textContent = displayText;
  el.srsMnemonicView.classList.toggle("is-empty", !hasMnemonic);
  el.srsMnemonicView.setAttribute("role", "button");
  el.srsMnemonicView.setAttribute("tabindex", state.srsMnemonicEditing ? "-1" : "0");
  el.srsMnemonicView.setAttribute("aria-label", hasMnemonic ? "Edit mnemonic" : "Add mnemonic");
  el.srsMnemonicView.title = hasMnemonic ? "Click to edit mnemonic" : "Click to add mnemonic";

  if (!state.srsMnemonicEditing) {
    el.srsMnemonicView.classList.remove("is-hidden");
    el.srsMnemonicForm.classList.add("is-hidden");
    return;
  }

  el.srsMnemonicView.classList.add("is-hidden");
  el.srsMnemonicForm.classList.remove("is-hidden");
  el.srsMnemonicInput.value = state.srsMnemonic || "";
  requestAnimationFrame(() => {
    el.srsMnemonicInput.focus();
    el.srsMnemonicInput.select();
  });
}

function startSrsMnemonicEdit() {
  if (!state.srsCurrentCard || !state.srsRevealed) {
    return;
  }
  state.srsMnemonicEditing = true;
  renderSrsMnemonic();
}

function cancelSrsMnemonicEdit() {
  state.srsMnemonicEditing = false;
  el.srsMnemonicInput.value = "";
  renderSrsMnemonic();
}

function renderSrs() {
  const hasActiveCard = Boolean(state.srsCurrentCard);
  const dueCount = state.srsDueQueue.length + (hasActiveCard ? 1 : 0);
  const available = state.srsAvailableNewCount;
  const remaining = state.srsDailyNewRemaining;
  el.srsMeta.textContent = `Due ${dueCount} | New available ${available} | Daily remaining ${remaining}`;

  const isReviewingDone = !hasActiveCard && dueCount === 0;
  const canAddNewCards = isReviewingDone && available > 0 && remaining > 0;
  const isTrulyAllCaughtUp = isReviewingDone && available === 0;

  el.srsReviewer.classList.toggle("is-hidden", !hasActiveCard);
  el.srsAddNew.classList.toggle("is-hidden", !canAddNewCards);
  el.srsCaughtUp.classList.toggle("is-hidden", !isTrulyAllCaughtUp);
  el.srsMeta.hidden = !hasActiveCard;
  el.srsState.hidden = !hasActiveCard;

  if (!hasActiveCard) {
    if (available > 0 && remaining <= 0) {
      setStateMessage(el.srsState, "Daily new-card cap reached. More new cards unlock after reset.");
    }
    return;
  }

  el.srsFrontWord.textContent = state.srsCurrentCard.display_word || state.srsCurrentCard.normalized_word;

  // Manage flip card state
  const flipCard = document.querySelector(".srs-card-flip");
  if (flipCard) {
    flipCard.classList.toggle("flipped", state.srsRevealed);
  }

  // Manage reveal content
  el.srsReveal.classList.toggle("is-hidden", !state.srsRevealed);
  if (state.srsRevealed) {
    renderSrsDefinitions();
    renderSrsMnemonic();
  }
}

function applySrsSessionData(cards, data) {
  state.srsDueQueue = [...(cards || [])];
  state.srsCurrentCard = state.srsDueQueue.shift() || null;
  state.srsRevealed = false;
  state.srsDefinitions = [];
  state.srsMnemonic = null;
  state.srsMnemonicEditing = false;
  state.srsDailyNewRemaining = data.daily_new_remaining || 0;
  state.srsAvailableNewCount = data.available_new_count || 0;
  state.srsDailyResetAt = data.daily_reset_at || "";
  state.srsUndoHistory = [];
  state.srsCardFlipped = false;
}

async function loadSrsSession() {
  const requestVersion = nextRequestVersion("srsSession");
  if (!state.activeUserId) {
    clearSrsState();
    setStateMessage(el.srsState, "Select a user first");
    return;
  }
  setStateMessage(el.srsState, "Loading...");
  try {
    const data = await state.api.getSrsSession(state.activeUserId, timezoneOffsetMinutes(), state.currentLanguage);
    if (!isCurrentRequest("srsSession", requestVersion)) {
      return;
    }
    applySrsSessionData(data.due_cards, data);
    setStateMessage(el.srsState, "");
    renderSrs();
  } catch (err) {
    if (!isCurrentRequest("srsSession", requestVersion)) {
      return;
    }
    setStateMessage(el.srsState, String(err.message || err), true);
  }
}

async function loadSrsDetailsForCurrentCard() {
  const word = state.srsCurrentCard?.normalized_word;
  const requestVersion = nextRequestVersion("srsDetails");
  if (!state.activeUserId || !word) {
    return;
  }
  state.srsLoadingDetailsForWord = word;
  try {
    const [meanings, details] = await Promise.all([
      state.api.listMeanings(state.activeUserId, word, state.currentLanguage),
      state.api.getWordDetails(state.activeUserId, word, state.currentLanguage),
    ]);
    if (!isCurrentRequest("srsDetails", requestVersion) || state.srsCurrentCard?.normalized_word !== word) {
      return;
    }
    state.srsDefinitions = meanings.items || [];
    state.srsMnemonic = details?.mnemonic || null;
    renderSrs();
  } catch (err) {
    if (!isCurrentRequest("srsDetails", requestVersion)) {
      return;
    }
    setStateMessage(el.srsState, `Failed to load card details: ${String(err.message || err)}`, true);
  } finally {
    if (state.srsLoadingDetailsForWord === word) {
      state.srsLoadingDetailsForWord = "";
    }
  }
}

async function revealSrsCard() {
  if (!state.srsCurrentCard || state.srsRevealed) {
    return;
  }
  state.srsRevealed = true;
  renderSrs();
  await loadSrsDetailsForCurrentCard();
}

async function submitSrsResult(result) {
  const card = state.srsCurrentCard;
  if (!card || !state.srsRevealed) {
    return;
  }
  const requestVersion = nextRequestVersion("srsReview");
  try {
    await state.api.submitSrsReview(state.activeUserId, card.normalized_word, result, state.currentLanguage);
    if (!isCurrentRequest("srsReview", requestVersion)) {
      return;
    }
    // Save to undo history before moving to next card
    state.srsUndoHistory.push({
      card,
      result,
      definitions: [...state.srsDefinitions],
      mnemonic: state.srsMnemonic,
    });

    if (result === "wrong") {
      srsReinsertWrongCard(card);
    }
    state.srsCurrentCard = state.srsDueQueue.shift() || null;
    state.srsRevealed = false;
    state.srsDefinitions = [];
    state.srsMnemonic = null;
    state.srsMnemonicEditing = false;
    state.srsCardFlipped = false;
    setStateMessage(el.srsState, "");
    renderSrs();
  } catch (err) {
    if (!isCurrentRequest("srsReview", requestVersion)) {
      return;
    }
    setStateMessage(el.srsState, `Review failed: ${String(err.message || err)}`, true);
  }
}

async function undoSrsReview() {
  if (state.srsUndoHistory.length === 0) {
    return;
  }

  const undoEntry = state.srsUndoHistory.pop();
  const requestVersion = nextRequestVersion("srsUndo");

  try {
    // Reverse the previous submission
    const reverseResult = undoEntry.result === "wrong" ? "right" : "wrong";
    await state.api.submitSrsReview(state.activeUserId, undoEntry.card.normalized_word, reverseResult, state.currentLanguage);

    if (!isCurrentRequest("srsUndo", requestVersion)) {
      return;
    }

    // Restore the card to the queue
    state.srsDueQueue.unshift(state.srsCurrentCard);
    state.srsCurrentCard = undoEntry.card;
    state.srsRevealed = true;
    state.srsDefinitions = undoEntry.definitions;
    state.srsMnemonic = undoEntry.mnemonic;
    state.srsMnemonicEditing = false;
    state.srsCardFlipped = true;

    setStateMessage(el.srsState, "Undo successful");
    renderSrs();

    // Clear the message after 2 seconds
    setTimeout(() => {
      if (state.currentView === "srs") {
        setStateMessage(el.srsState, "");
      }
    }, 2000);
  } catch (err) {
    if (!isCurrentRequest("srsUndo", requestVersion)) {
      return;
    }
    setStateMessage(el.srsState, `Undo failed: ${String(err.message || err)}`, true);
  }
}

async function loadProgressData() {
  const requestVersion = nextRequestVersion("progressHistory");
  if (!state.activeUserId) {
    setStateMessage(el.progressState, "Select a user first");
    return;
  }
  setStateMessage(el.progressState, "Loading...");
  try {
    const data = await state.api.getProgressHistory(state.activeUserId, state.progressRange, state.currentLanguage);
    if (!isCurrentRequest("progressHistory", requestVersion)) {
      return;
    }
    renderProgressChart(data);
  } catch (err) {
    if (!isCurrentRequest("progressHistory", requestVersion)) {
      return;
    }
    setStateMessage(el.progressState, String(err.message || err), true);
  }
}

async function loadWordsReadData() {
  const requestVersion = nextRequestVersion("wordsReadHistory");
  if (!state.activeUserId) {
    setStateMessage(el.wordsReadState, "Select a user first");
    return;
  }
  setStateMessage(el.wordsReadState, "Loading...");
  try {
    const data = await state.api.getWordsReadHistory(state.activeUserId, state.progressRange, state.currentLanguage);
    if (!isCurrentRequest("wordsReadHistory", requestVersion)) {
      return;
    }
    renderWordsReadChart(data);
  } catch (err) {
    if (!isCurrentRequest("wordsReadHistory", requestVersion)) {
      return;
    }
    setStateMessage(el.wordsReadState, String(err.message || err), true);
  }
}

async function loadWordsReadSummary() {
  if (!state.activeUserId || !el.wordsReadSummary) return;
  try {
    const data = await state.api.getWordsReadSummary(state.activeUserId, state.currentLanguage);
    renderWordsReadSummary(data);
  } catch (_) {
    // non-critical, silently ignore
  }
}

function renderWordsReadSummary(data) {
  if (!el.wordsReadSummary) return;
  const fmt = (n) => n.toLocaleString();
  el.wordsReadSummary.innerHTML = `
    <div class="words-read-stat">
      <span class="stat-value">${fmt(data.words_today)}</span>
      <span class="stat-label">Words today</span>
    </div>
    <div class="words-read-stat">
      <span class="stat-value">${fmt(Math.round(data.daily_rate_14d))}</span>
      <span class="stat-label">Daily avg (14d)</span>
    </div>
    <div class="words-read-stat">
      <span class="stat-value">${fmt(data.projected_month)}</span>
      <span class="stat-label">Projected / month</span>
    </div>
    <div class="words-read-stat">
      <span class="stat-value">${fmt(data.projected_year)}</span>
      <span class="stat-label">Projected / year</span>
    </div>
  `;
}

async function loadSrsHistoryData() {
  const requestVersion = nextRequestVersion("srsHistory");
  if (!state.activeUserId) {
    setStateMessage(el.srsHistoryState, "Select a user first");
    return;
  }
  setStateMessage(el.srsHistoryState, "Loading...");
  try {
    const data = await state.api.getSrsHistory(state.activeUserId, state.progressRange, state.currentLanguage);
    if (!isCurrentRequest("srsHistory", requestVersion)) {
      return;
    }
    renderSrsHistoryChart(data);
  } catch (err) {
    if (!isCurrentRequest("srsHistory", requestVersion)) {
      return;
    }
    setStateMessage(el.srsHistoryState, String(err.message || err), true);
  }
}

async function loadUsers() {
  const requestVersion = nextRequestVersion("users");
  renderListState(el.usersList, el.usersState, { loading: true });
  try {
    const data = await state.api.listUsers(state.includeDeleted);
    if (!isCurrentRequest("users", requestVersion)) {
      return;
    }
    state.users = data.items;

    if (!state.users.some((u) => u.user_id === state.activeUserId && u.deleted_at === null)) {
      state.activeUserId = "";
      localStorage.removeItem("active_user_id");
    }

    renderUserSelector();
    renderUsersList();
  } catch (err) {
    if (!isCurrentRequest("users", requestVersion)) {
      return;
    }
    renderListState(el.usersList, el.usersState, { error: String(err.message || err) });
  }
}

function renderTexts() {
  if (
    renderListState(el.textsList, el.textsState, {
      empty: state.texts.length === 0,
      emptyMessage: "No texts for selected user",
    })
  ) {
    return;
  }

  if (el.textsList) el.textsList.innerHTML = "";
  for (const text of state.texts) {
    const li = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = text.title;
    const progress = document.createElement("div");
    const totalEngaged = text.progress.known_percent + text.progress.stage3_percent;
    progress.innerHTML = `<small>Known: ${text.progress.known_count} | Unknown: ${text.progress.unknown_count} | Never: ${text.progress.never_seen_count} | ${text.progress.known_percent}% / ${totalEngaged}%</small>`;
    const renameState = document.createElement("div");
    renameState.className = "state";

    const controls = document.createElement("div");

    const open = document.createElement("button");
    open.type = "button";
    open.textContent = "Open in Reader";
    open.title = "Open this text in Reader view";
    open.onclick = async () => {
      state.openTextId = text.text_id;
      try {
        const position = await state.api.getTextPosition(state.activeUserId, text.text_id);
        state.sentenceIndex = Math.max(0, Number(position?.sentence_index || 0));
      } catch (_) {
        state.sentenceIndex = 0;
      }
      state.maxSentenceIndex = null;
      state.currentSentence = null;
      clearWordDetailsPanel();
      setActiveView("reader");
      await loadSentence();
    };

    const rename = document.createElement("button");
    rename.type = "button";
    rename.textContent = "Rename";
    rename.title = "Rename this text";

    const renameForm = document.createElement("form");
    renameForm.className = "inline-form rename-form";
    renameForm.hidden = true;
    const renameInput = document.createElement("input");
    renameInput.type = "text";
    renameInput.required = true;
    renameInput.maxLength = 200;
    renameInput.value = text.title;
    renameInput.setAttribute("aria-label", `Rename ${text.title}`);
    const saveRename = document.createElement("button");
    saveRename.type = "submit";
    saveRename.textContent = "Save";
    const cancelRename = document.createElement("button");
    cancelRename.type = "button";
    cancelRename.textContent = "Cancel";
    cancelRename.className = "secondary";
    cancelRename.onclick = () => {
      renameInput.value = text.title;
      renameForm.hidden = true;
      rename.disabled = false;
      setStateMessage(renameState, "");
    };
    renameForm.append(renameInput, saveRename, cancelRename);

    rename.onclick = () => {
      renameForm.hidden = false;
      rename.disabled = true;
      renameInput.focus();
      renameInput.select();
    };

    renameForm.onsubmit = async (event) => {
      event.preventDefault();
      const nextTitle = renameInput.value.trim();
      if (!nextTitle) {
        setStateMessage(renameState, "Title is required", true);
        return;
      }
      if (nextTitle.length > 200) {
        setStateMessage(renameState, "Title must be 200 chars or less", true);
        return;
      }
      try {
        saveRename.disabled = true;
        cancelRename.disabled = true;
        setStateMessage(renameState, "Saving...");
        await state.api.renameText(state.activeUserId, text.text_id, nextTitle);
        await loadTexts();
      } catch (err) {
        setStateMessage(renameState, String(err.message || err), true);
      } finally {
        saveRename.disabled = false;
        cancelRename.disabled = false;
      }
    };

    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "Delete";
    del.onclick = async () => {
      await state.api.deleteText(state.activeUserId, text.text_id);
      if (state.openTextId === text.text_id) {
        state.openTextId = "";
        state.maxSentenceIndex = null;
        state.currentSentence = null;
        clearWordDetailsPanel();
        el.readerMeta.textContent = "No text open";
        el.readerSentence.textContent = "";
      }
      await loadTexts();
    };

    controls.append(open, rename, del);
    li.append(title, progress, controls, renameForm, renameState);
    el.textsList.appendChild(li);
  }
}

async function loadTexts() {
  const requestVersion = nextRequestVersion("texts");
  if (!state.activeUserId) {
    setStateMessage(el.textsState, "Select a user first");
    return;
  }

  setStateMessage(el.textsState, "Loading...");
  try {
    const data = await state.api.listTexts(state.activeUserId, state.currentLanguage);
    if (!isCurrentRequest("texts", requestVersion)) {
      return;
    }
    state.texts = data.items;
    await renderLibraryGrid();
    setStateMessage(el.textsState, "");
  } catch (err) {
    if (!isCurrentRequest("texts", requestVersion)) {
      return;
    }
    setStateMessage(el.textsState, String(err.message || err), true);
  }
}

const SENTENCE_SPLIT_RE = /([\s,;:!?()[\]{}"'“”׳״]+)/;
const HEBREW_MAQAF = "\u05be";
const NIKKUD_RE = /[\u0591-\u05bd\u05bf-\u05c7]/g;
const NUMERIC_ONLY_RE = /^\d+$/;
const PUNCT_ONLY_RE = /^[^\w\u0590-\u05ff]+$/u;

function normalizeTokenForLookup(token) {
  const cleaned = (token || "").replaceAll(NIKKUD_RE, "").trim();
  if (!cleaned || NUMERIC_ONLY_RE.test(cleaned) || PUNCT_ONLY_RE.test(cleaned)) {
    return null;
  }
  const hasLatin = /[a-z]/i.test(cleaned);
  return hasLatin ? cleaned.toLowerCase() : cleaned;
}

function buildWordStateMap(tokens) {
  const out = new Map();
  for (const token of tokens) {
    out.set(token.normalized_word, token.state);
  }
  return out;
}

function stateLabel(value) {
  if (value === "known") return "Known";
  if (value === "unknown") return "Unknown";
  return "Unseen";
}

function cycleState(value) {
  if (value === "never_seen") return "unknown";
  if (value === "unknown") return "known";
  return "never_seen";
}

function selectedToken() {
  if (!state.currentSentence || !state.selectedWord) {
    return null;
  }
  return state.currentSentence.tokens.find((token) => token.normalized_word === state.selectedWord) || null;
}

function updateSelectedWordTokens(nextState) {
  if (!state.currentSentence || !state.selectedWord) {
    return;
  }
  for (const token of state.currentSentence.tokens) {
    if (token.normalized_word === state.selectedWord) {
      token.state = nextState;
    }
  }
}

function renderWordDetailsPanel() {
  if (!state.selectedWord) {
    el.wordDetailsPanel.classList.add("is-hidden");
    return;
  }

  const token = selectedToken();
  el.wordDetailsPanel.classList.remove("is-hidden");
  el.wordDetailsWord.textContent = state.selectedWord;
  el.wordDetailsStatus.textContent = stateLabel(token?.state || "never_seen");
  if (state.currentSentence?.sentence_text && !el.meaningContext.value.trim()) {
    el.meaningContext.value = state.currentSentence.sentence_text;
  }
}


function animateSelectionPulse() {
  const activeButtons = Array.from(el.readerSentence.querySelectorAll(".sentence-word.active"));
  for (const node of activeButtons) {
    node.classList.remove("pulse");
    // force restart animation
    void node.offsetWidth;
    node.classList.add("pulse");
  }
}

function clearSentenceAiPanels() {
  el.restatePanel.classList.add("is-hidden");
  el.grammarPanel.classList.add("is-hidden");
  el.restateText.textContent = "";
  el.grammarText.textContent = "";
}

function renderSentence(data = state.currentSentence) {
  if (!data) {
    el.readerSentence.textContent = "";
    return;
  }

  clearSentenceAiPanels();
  state.currentSentence = data;
  el.readerMeta.textContent = `Text ${data.text_id} - sentence ${data.sentence_index} | Nikkud: ${state.readerShowNikkud ? "on (F3)" : "off (F3)"}`;
  el.prevSentence.disabled = data.prev_sentence_index === null;
  el.nextSentence.disabled = data.next_sentence_index === null;
  el.prevSentence.dataset.target = data.prev_sentence_index;
  el.nextSentence.dataset.target = data.next_sentence_index;

  if (data.next_sentence_index === null) {
    state.maxSentenceIndex = data.sentence_index;
  }

  const wordStateByNormalized = buildWordStateMap(data.tokens);
  if (state.selectedWord && !wordStateByNormalized.has(state.selectedWord)) {
    clearWordDetailsPanel();
  }

  el.readerSentence.innerHTML = "";
  let clickableWordIndex = 0;
  const fragments = data.sentence_text.split(SENTENCE_SPLIT_RE);
  for (const fragment of fragments) {
    if (!fragment) {
      continue;
    }
    if (SENTENCE_SPLIT_RE.test(fragment)) {
      el.readerSentence.appendChild(document.createTextNode(fragment));
      continue;
    }

    const maqafParts = fragment.split(HEBREW_MAQAF);
    maqafParts.forEach((part, index) => {
      if (index > 0) {
        el.readerSentence.appendChild(document.createTextNode(HEBREW_MAQAF));
      }
      const normalized = normalizeTokenForLookup(part);
      const tokenState = normalized ? wordStateByNormalized.get(normalized) : null;
      if (!normalized || !tokenState) {
        el.readerSentence.appendChild(document.createTextNode(part));
        return;
      }

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `sentence-word ${tokenState}`;
      btn.textContent = state.readerShowNikkud ? part : part.replace(NIKKUD_RE, "");
      const wordButtonId = `${normalized}:${clickableWordIndex}`;
      clickableWordIndex += 1;
      btn.dataset.wordButtonId = wordButtonId;
      btn.title = `Open details for ${part}`;
      btn.setAttribute("aria-label", `Open details for ${part}`);
      if (state.selectedWord === normalized) {
        btn.classList.add("active");
      }

      const activateWord = () => onSentenceWordActivated(normalized);
      btn.onclick = activateWord;
      btn.onkeydown = (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          activateWord();
        }
      };
      el.readerSentence.appendChild(btn);
    });
  }

  renderWordDetailsPanel();
}

async function loadSentence() {
  const requestVersion = nextRequestVersion("sentence");
  if (!state.activeUserId || !state.openTextId) {
    setStateMessage(el.readerState, "Select a text first");
    return;
  }
  const requestedUserId = state.activeUserId;
  const requestedTextId = state.openTextId;
  const requestedSentenceIndex = state.sentenceIndex;

  try {
    setStateMessage(el.readerState, "Loading...");
    const data = await state.api.loadSentence(requestedUserId, requestedTextId, requestedSentenceIndex);
    if (
      !isCurrentRequest("sentence", requestVersion) ||
      requestedUserId !== state.activeUserId ||
      requestedTextId !== state.openTextId ||
      requestedSentenceIndex !== state.sentenceIndex
    ) {
      return;
    }
    renderSentence(data);
    try {
      await state.api.updateTextPosition(requestedUserId, requestedTextId, data.sentence_index);
    } catch (_) {
      // Don't block reader rendering if position persistence fails.
    }
    setStateMessage(el.readerState, "");
  } catch (err) {
    if (!isCurrentRequest("sentence", requestVersion)) {
      return;
    }
    if (String(err.message || err) === "sentence_not_found") {
      if (requestedSentenceIndex !== 0) {
        state.sentenceIndex = 0;
        try {
          await state.api.updateTextPosition(requestedUserId, requestedTextId, 0);
        } catch (_) {
          // Ignore persistence failure and still fallback to first sentence.
        }
        await loadSentence();
        return;
      }
      setStateMessage(el.readerState, `Sentence ${state.sentenceIndex} is out of range for this text`, true);
      return;
    }
    setStateMessage(el.readerState, String(err.message || err), true);
  }
}

function renderWords(data) {
  state.wordsPage = data.page;
  state.wordsLimit = data.limit;
  const totalPages = Math.max(1, Math.ceil(data.total / data.limit));
  el.wordsPageLabel.textContent = `Page ${data.page} / ${totalPages}`;
  el.wordsPrevPage.disabled = data.page <= 1;
  el.wordsNextPage.disabled = data.page >= totalPages;

  if (
    renderListState(el.wordsList, el.wordsState, {
      empty: data.items.length === 0,
      emptyMessage: "No words for this filter",
      totalLabel: `Total: ${data.total}`,
    })
  ) {
    return;
  }

  if (el.wordsList) el.wordsList.innerHTML = "";
  for (const item of data.items) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${item.normalized_word}</strong> <small>${item.state}</small>`;
    const select = document.createElement("select");
    for (const value of ["known", "unknown", "never_seen"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value === "never_seen" ? "Never seen" : value[0].toUpperCase() + value.slice(1);
      option.selected = item.state === value;
      select.appendChild(option);
    }
    select.onchange = async () => {
      await state.api.updateWordState(state.activeUserId, item.normalized_word, select.value, state.currentLanguage);
      await Promise.all([loadWords(), loadTexts()]);
    };
    li.appendChild(select);
    el.wordsList.appendChild(li);
  }
}

async function loadWords() {
  const requestVersion = nextRequestVersion("words");
  if (!state.activeUserId) {
    renderListState(el.wordsList, el.wordsState, { empty: true, emptyMessage: "Select a user first" });
    return;
  }

  renderListState(el.wordsList, el.wordsState, { loading: true });
  try {
    const data = await state.api.listWords(state.activeUserId, el.wordsFilter.value, state.wordsPage, state.wordsLimit, state.currentLanguage);
    if (!isCurrentRequest("words", requestVersion)) {
      return;
    }
    renderWords(data);
  } catch (err) {
    if (!isCurrentRequest("words", requestVersion)) {
      return;
    }
    renderListState(el.wordsList, el.wordsState, { error: String(err.message || err) });
  }
}

function renderMeanings(data) {
  const items = data.items || [];
  const newest = items[items.length - 1] || null;

  if (newest) {
    el.meaningsPreview.innerHTML = `
      <div class="meaning-preview-card">
        <div class="meaning-preview-title">Latest meaning</div>
        <div>${newest.meaning_text}</div>
      </div>
    `;
  } else {
    el.meaningsPreview.innerHTML = '<div class="meaning-empty">No meanings yet. Generate one.</div>';
  }

  el.meaningsList.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    const editor = document.createElement("textarea");
    editor.value = item.meaning_text;
    editor.className = "meaning-editor";
    editor.setAttribute("aria-label", "Meaning text");
    li.appendChild(editor);

    const meta = document.createElement("small");
    meta.textContent = item.created_at;
    li.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "row-form";
    const save = document.createElement("button");
    save.type = "button";
    save.textContent = "Save";
    save.onclick = () => updateMeaning(item.meaning_id, editor, save);
    actions.appendChild(save);

    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "Delete";
    del.onclick = () => deleteMeaning(item.meaning_id, li);
    actions.appendChild(del);
    li.appendChild(actions);
    el.meaningsList.appendChild(li);
  }

  setStateMessage(el.meaningsState, "");
}

function renderWordDetails(data) {
  el.wordMnemonic.value = data?.mnemonic || "";
  setStateMessage(el.mnemonicState, "");
}

function renderProgressChart(data) {
  const labels = data.buckets.map(b => b.date);
  let knownData = data.buckets.map(b => b.cumulative_known);
  const encounterData = data.buckets.map(b => b.cumulative_encountered);

  // Always apply unique word estimate
  knownData = knownData.map(k => Math.round(k * UNIQUE_WORD_ESTIMATE_PERCENT));

  const knownLabel = "Known Words (Unique Est.)";
  const maxKnown = Math.max(...knownData, 0);
  const currentLevel = getCurrentVocabLevel(maxKnown);
  const ctx = el.progressChartCanvas.getContext("2d");

  // Plugin to draw milestone lines
  const milestonesPlugin = {
    id: "milestonesPlugin",
    afterDatasetsDraw(chart) {
      const ctx = chart.ctx;
      const yAxis = chart.scales.y;
      const xStart = chart.chartArea.left;
      const xEnd = chart.chartArea.right;

      // Draw lines only for milestones that are visible
      VOCAB_MILESTONES.forEach(milestone => {
        const yValue = yAxis.getPixelForValue(milestone.threshold);
        if (yValue >= chart.chartArea.top && yValue <= chart.chartArea.bottom) {
          ctx.save();
          ctx.strokeStyle = milestone.color;
          ctx.lineWidth = 1.5;
          ctx.globalAlpha = 0.3;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.moveTo(xStart, yValue);
          ctx.lineTo(xEnd, yValue);
          ctx.stroke();
          ctx.restore();
        }
      });
    },
  };

  if (state.progressChart) {
    state.progressChart.data.labels = labels;
    state.progressChart.data.datasets[0].label = knownLabel;
    state.progressChart.data.datasets[0].data = knownData;
    state.progressChart.data.datasets[1].data = encounterData;
    state.progressChart.update();
  } else {
    state.progressChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: knownLabel,
            data: knownData,
            borderColor: "#22c55e",
            backgroundColor: "rgba(34, 197, 94, 0.1)",
            fill: "origin",
            tension: 0.3,
          },
          {
            label: "Encountered Words",
            data: encounterData,
            borderColor: "#9ca3af",
            backgroundColor: "rgba(156, 163, 175, 0.05)",
            fill: "-1",
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
          milestonesPlugin: {},
        },
        scales: {
          y: {
            beginAtZero: true,
            stacked: false,
          },
        },
      },
      plugins: [milestonesPlugin],
    });
  }
  setStateMessage(el.progressState, "");

  // Display current level
  if (el.progressLevel) {
    if (currentLevel) {
      el.progressLevel.textContent = `Current: ${currentLevel.name} (${maxKnown} words)`;
    } else {
      el.progressLevel.textContent = `${maxKnown} words learned`;
    }
  }
}

function renderWordsReadChart(data) {
  const labels = data.buckets.map(b => b.date);
  const wordsData = data.buckets.map(b => b.cumulative_words);
  const nikkudOffData = data.buckets.map(b => b.cumulative_words_nikkud_off);
  const ctx = el.wordsReadChartCanvas.getContext("2d");

  if (state.wordsReadChart) {
    state.wordsReadChart.data.labels = labels;
    state.wordsReadChart.data.datasets[0].data = wordsData;
    state.wordsReadChart.data.datasets[1].data = nikkudOffData;
    state.wordsReadChart.update();
  } else {
    state.wordsReadChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Words Read (cumulative)",
            data: wordsData,
            borderColor: "#60a5fa",
            backgroundColor: "rgba(96, 165, 250, 0.1)",
            fill: "origin",
            tension: 0.3,
          },
          {
            label: "Words Read without Nikkud (cumulative)",
            data: nikkudOffData,
            borderColor: "#f97316",
            backgroundColor: "rgba(249, 115, 22, 0.1)",
            fill: "origin",
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: true, position: "top" },
        },
        scales: {
          y: { beginAtZero: true },
        },
      },
    });
  }
  setStateMessage(el.wordsReadState, "");
}

function renderSrsHistoryChart(data) {
  const buckets = data.buckets;
  const labels = buckets.map(b => b.date);

  // Mature stages listed first so they stack at the bottom of the area chart
  const seriesDefs = [
    { label: "Stage 5+", key: "stage4_plus", color: "52, 211, 153" },
    { label: "Stage 4",  key: "stage3",      color: "74, 222, 128" },
    { label: "Stage 3",  key: "stage2",      color: "250, 204, 21" },
    { label: "Stage 2",  key: "stage1",      color: "251, 146, 60" },
    { label: "Stage 1",  key: "stage0",      color: "248, 113, 113" },
  ];

  const datasets = seriesDefs.map(s => ({
    label: s.label,
    data: buckets.map(b => b[s.key]),
    borderColor: `rgba(${s.color}, 0.8)`,
    backgroundColor: `rgba(${s.color}, 0.6)`,
    fill: true,
    tension: 0.3,
    pointRadius: 0,
  }));

  const ctx = el.srsHistoryChartCanvas.getContext("2d");

  if (state.srsHistoryChart) {
    state.srsHistoryChart.data.labels = labels;
    datasets.forEach((ds, i) => {
      state.srsHistoryChart.data.datasets[i].data = ds.data;
    });
    state.srsHistoryChart.update();
  } else {
    state.srsHistoryChart = new Chart(ctx, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: true, position: "top" },
        },
        scales: {
          x: { stacked: true },
          y: { stacked: true, beginAtZero: true, title: { display: true, text: "Cards" } },
        },
      },
    });
  }
  setStateMessage(el.srsHistoryState, "");
}

async function renderBackupStatus() {
  try {
    const data = await state.api.getBackupStatus();
    const elBackup = el.backupStatus;
    if (!elBackup) return;

    elBackup.textContent = "";
    elBackup.className = "backup-status";

    if (data.status === "ok") {
      elBackup.textContent = `✓ backed up ${data.last_backup_date}`;
      elBackup.classList.add("ok");
    } else if (data.status === "overdue") {
      elBackup.textContent = "⚠ no backup yet";
      elBackup.classList.add("overdue");
    } else if (data.status === "failed") {
      elBackup.textContent = "⚠ backup failed";
      elBackup.classList.add("failed");
    }
  } catch (error) {
    // Silently fail if backup status is unavailable
    if (el.backupStatus) {
      el.backupStatus.textContent = "";
    }
  }
}

async function loadWordDetailsForWord(word) {
  const requestVersion = nextRequestVersion("wordDetails");
  if (!state.activeUserId || !word) {
    el.wordMnemonic.value = "";
    return;
  }
  setStateMessage(el.mnemonicState, "Loading...");
  try {
    const data = await state.api.getWordDetails(state.activeUserId, word, state.currentLanguage);
    if (!isCurrentRequest("wordDetails", requestVersion) || word !== state.selectedWord) {
      return;
    }
    renderWordDetails(data);
  } catch (err) {
    if (!isCurrentRequest("wordDetails", requestVersion) || word !== state.selectedWord) {
      return;
    }
    setStateMessage(el.mnemonicState, String(err.message || err), true);
  }
}

async function loadMeaningsForWord(word) {
  const requestVersion = nextRequestVersion("meanings");
  if (!state.activeUserId || !word) {
    el.meaningsPreview.innerHTML = '<div class="meaning-empty">Pick a word in the reader first.</div>';
    el.meaningsList.innerHTML = "";
    return;
  }

  renderListState(el.meaningsList, el.meaningsState, { loading: true });
  try {
    const data = await state.api.listMeanings(state.activeUserId, word, state.currentLanguage);
    if (!isCurrentRequest("meanings", requestVersion) || word !== state.selectedWord) {
      return;
    }
    renderMeanings(data);
  } catch (err) {
    if (!isCurrentRequest("meanings", requestVersion) || word !== state.selectedWord) {
      return;
    }
    renderListState(el.meaningsList, el.meaningsState, { error: String(err.message || err) });
  }
}

function setSelectedWord(word) {
  state.selectedWord = word;
  setStateMessage(el.wordDetailsState, "");
  setStateMessage(el.mnemonicState, "");
  renderSentence();
  void loadWordDetailsForWord(word);
  void loadMeaningsForWord(word);
}

async function updateMeaning(meaningId, editorNode, saveButton) {
  const actionWord = state.selectedWord;
  if (!actionWord) {
    return;
  }
  const newText = editorNode.value.trim();
  if (!newText) {
    setStateMessage(el.meaningsState, "Meaning cannot be empty", true);
    return;
  }
  const originalButtonText = saveButton.textContent;
  try {
    saveButton.disabled = true;
    saveButton.textContent = "Saving...";
    setStateMessage(el.meaningsState, "Saving...");
    await state.api.updateMeaning(state.activeUserId, actionWord, meaningId, newText, state.currentLanguage);
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.meaningsState, "");
    await loadMeaningsForWord(actionWord);
  } catch (err) {
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.meaningsState, `Save failed: ${String(err.message || err)}`, true);
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = originalButtonText || "Save";
  }
}

async function onSentenceWordActivated(word) {
  if (!state.currentSentence || !word) {
    return;
  }

  if (state.selectedWord !== word) {
    setSelectedWord(word);
    return;
  }

  const token = selectedToken();
  if (!token) {
    return;
  }

  const nextState = cycleState(token.state);
  updateSelectedWordTokens(nextState);
  setStateMessage(el.wordDetailsState, "");
  renderSentence();
  animateSelectionPulse();

  const requestVersion = nextRequestVersion("wordSave");
  const wordAtSaveStart = word;
  try {
    await state.api.updateWordState(state.activeUserId, wordAtSaveStart, nextState, state.currentLanguage);
    if (!isCurrentRequest("wordSave", requestVersion) || state.selectedWord !== wordAtSaveStart) {
      return;
    }
    setStateMessage(el.wordDetailsState, "");
  } catch (err) {
    if (!isCurrentRequest("wordSave", requestVersion) || state.selectedWord !== wordAtSaveStart) {
      return;
    }
    setStateMessage(el.wordDetailsState, `Save failed: ${String(err.message || err)}`, true);
  }
}

async function deleteMeaning(meaningId, rowNode) {
  const actionWord = state.selectedWord;
  if (!actionWord) {
    return;
  }
  try {
    rowNode.classList.add("is-removing");
    setStateMessage(el.meaningsState, "Deleting...");
    await state.api.deleteMeaning(state.activeUserId, actionWord, meaningId, state.currentLanguage);
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.meaningsState, "");
    await loadMeaningsForWord(actionWord);
  } catch (err) {
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.meaningsState, `Delete failed: ${String(err.message || err)}`, true);
  }
}

for (const button of el.viewButtons) {
  button.onclick = () => setActiveView(button.dataset.viewTarget || "library");
  button.onkeydown = (event) => {
    const currentView = button.dataset.viewTarget || "library";
    const currentIndex = VIEW_ORDER.indexOf(currentView);
    if (event.key === "ArrowRight") {
      event.preventDefault();
      const nextView = VIEW_ORDER[(currentIndex + 1) % VIEW_ORDER.length];
      setActiveView(nextView);
      focusView(nextView);
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      const nextView = VIEW_ORDER[(currentIndex - 1 + VIEW_ORDER.length) % VIEW_ORDER.length];
      setActiveView(nextView);
      focusView(nextView);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      setActiveView(VIEW_ORDER[0]);
      focusView(VIEW_ORDER[0]);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      const lastView = VIEW_ORDER[VIEW_ORDER.length - 1];
      setActiveView(lastView);
      focusView(lastView);
    }
  };
}

if (el.includeDeleted) {
  el.includeDeleted.onchange = () => {
    state.includeDeleted = el.includeDeleted.checked;
    loadUsers();
  };
}
if (el.refreshUsers) el.refreshUsers.onclick = () => loadUsers();
if (el.refreshTexts) el.refreshTexts.onclick = () => loadTexts();
if (el.refreshWords) el.refreshWords.onclick = () => loadWords();
if (el.wordsFilter) {
  el.wordsFilter.onchange = () => {
    state.wordsPage = 1;
    loadWords();
  };
}
if (el.wordsLimit) {
  el.wordsLimit.onchange = () => {
    state.wordsLimit = Number(el.wordsLimit.value);
    state.wordsPage = 1;
    loadWords();
  };
}
if (el.wordsPrevPage) {
  el.wordsPrevPage.onclick = () => {
    if (state.wordsPage <= 1) return;
    state.wordsPage -= 1;
    loadWords();
  };
}
if (el.wordsNextPage) {
  el.wordsNextPage.onclick = () => {
    state.wordsPage += 1;
    loadWords();
  };
}

// === New UI Event Listeners ===

if (el.navLibrary) {
  el.navLibrary.onclick = () => {
    switchView("library");
  };
}

if (el.navSrs) {
  el.navSrs.onclick = () => {
    switchView("srs");
  };
}

if (el.navProgress) {
  el.navProgress.onclick = () => {
    switchView("progress");
  };
}

for (const btn of el.progressRangeBtns) {
  btn.onclick = () => {
    state.progressRange = btn.dataset.range;
    el.progressRangeBtns.forEach(b => b.classList.toggle("active", b === btn));
    void loadProgressData();
    void loadWordsReadData();
    void loadWordsReadSummary();
    void loadSrsHistoryData();
  };
}

document.querySelectorAll(".lang-btn").forEach(btn => {
  btn.onclick = () => handleLanguageSwitch(btn.dataset.lang);
});

if (el.logoutLink) {
  el.logoutLink.onclick = (event) => {
    event.preventDefault();
    handleLogout();
  };
}

if (el.userPickConfirm) {
  el.userPickConfirm.onclick = async () => {
    const userId = el.userPicker.value;
    if (userId) {
      await handleUserPick(userId);
    }
  };
}

if (el.userPicker) {
  el.userPicker.onchange = () => {
    const userId = el.userPicker.value;
    if (userId) {
      void handleUserPick(userId);
    }
  };
}

if (el.readerExitBtn) {
  el.readerExitBtn.onclick = () => {
    handleReaderExit();
  };
}

window.addEventListener("pointermove", (event) => {
  const x = `${Math.round((event.clientX / window.innerWidth) * 100)}%`;
  const y = `${Math.round((event.clientY / window.innerHeight) * 100)}%`;
  document.documentElement.style.setProperty("--mouse-x", x);
  document.documentElement.style.setProperty("--mouse-y", y);
});

if (el.createUserForm) {
  el.createUserForm.onsubmit = async (event) => {
    event.preventDefault();
    try {
      const name = el.newUserName.value.trim();
      if (!name) return;
      const created = await state.api.createUser(name);
      state.activeUserId = created.user_id;
      state.isLoggedIn = true;
      localStorage.setItem("active_user_id", state.activeUserId);
      el.newUserName.value = "";
      await loadUsers();
      await Promise.all([loadTexts(), loadWords()]);
      hideUserSelection();
      switchView("library");
    } catch (err) {
      setStateMessage(el.usersState, String(err.message || err), true);
    }
  };
}

if (el.activeUser) {
  el.activeUser.onchange = async () => {
    state.activeUserId = el.activeUser.value;
    localStorage.setItem("active_user_id", state.activeUserId);
    clearUserScopedViews();
    state.wordsLimit = Number(el.wordsLimit?.value || 50);
    await Promise.all([loadTexts(), loadWords()]);
    if (state.currentView === "srs") {
      await loadSrsSession();
    }
  };
}

if (el.createTextForm) {
  el.createTextForm.onsubmit = async (event) => {
    event.preventDefault();
    try {
      requireUser();
      const title = el.newTextTitle.value.trim();
      const content = el.newTextContent.value.trim();
      if (!title || !content) return;
      await state.api.createText(state.activeUserId, title, content, state.currentLanguage);
      el.newTextTitle.value = "";
      el.newTextContent.value = "";
      await loadTexts();
    } catch (err) {
      setStateMessage(el.textsState, String(err.message || err), true);
    }
  };
}

if (el.prevSentence) {
  el.prevSentence.onclick = async () => {
    if (!el.prevSentence.dataset.target) return;
    clearWordDetailsPanel();
    if (!state.readerShowNikkud && state.currentSentence && state.activeUserId && state.openTextId) {
      void state.api.markSentenceNikkudOff(state.activeUserId, state.openTextId, state.currentSentence.sentence_index);
    }
    state.sentenceIndex = Number(el.prevSentence.dataset.target);
    state.readerShowNikkud = false;
    await loadSentence();
  };
}

if (el.nextSentence) {
  el.nextSentence.onclick = async () => {
    if (!el.nextSentence.dataset.target) return;
    clearWordDetailsPanel();
    if (!state.readerShowNikkud && state.currentSentence && state.activeUserId && state.openTextId) {
      void state.api.markSentenceNikkudOff(state.activeUserId, state.openTextId, state.currentSentence.sentence_index);
    }
    state.sentenceIndex = Number(el.nextSentence.dataset.target);
    state.readerShowNikkud = false;
    await loadSentence();
  };
}

if (el.btnRestate) {
  el.btnRestate.onclick = async () => {
    if (!state.activeUserId || !state.openTextId || state.currentSentence == null) return;
    const userId = state.activeUserId;
    const textId = state.openTextId;
    const sentenceIndex = state.currentSentence.sentence_index;
    const origText = el.btnRestate.textContent;
    el.btnRestate.disabled = true;
    el.btnRestate.textContent = "Restating…";
    el.restatePanel.classList.add("is-hidden");
    try {
      const data = await state.api.restateSentence(userId, textId, sentenceIndex);
      el.restateText.textContent = data.text;
      el.restatePanel.classList.remove("is-hidden");
    } catch (err) {
      el.restateText.textContent = `Error: ${String(err.message || err)}`;
      el.restatePanel.classList.remove("is-hidden");
    } finally {
      el.btnRestate.disabled = false;
      el.btnRestate.textContent = origText;
    }
  };
}

if (el.btnGrammar) {
  el.btnGrammar.onclick = async () => {
    if (!state.activeUserId || !state.openTextId || state.currentSentence == null) return;
    const userId = state.activeUserId;
    const textId = state.openTextId;
    const sentenceIndex = state.currentSentence.sentence_index;
    const origText = el.btnGrammar.textContent;
    el.btnGrammar.disabled = true;
    el.btnGrammar.textContent = "Analyzing…";
    el.grammarPanel.classList.add("is-hidden");
    try {
      const data = await state.api.analyzeSentenceGrammar(userId, textId, sentenceIndex);
      el.grammarText.textContent = data.text;
      el.grammarPanel.classList.remove("is-hidden");
    } catch (err) {
      el.grammarText.textContent = `Error: ${String(err.message || err)}`;
      el.grammarPanel.classList.remove("is-hidden");
    } finally {
      el.btnGrammar.disabled = false;
      el.btnGrammar.textContent = origText;
    }
  };
}

el.mnemonicForm.onsubmit = async (event) => {
  event.preventDefault();
  const actionWord = state.selectedWord;
  if (!actionWord) {
    setStateMessage(el.mnemonicState, "Pick a word in reader first", true);
    return;
  }
  const submitButton = el.mnemonicForm.querySelector("button[type='submit']");
  const originalSubmitText = submitButton ? submitButton.textContent : "";
  try {
    requireUser();
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Saving...";
    }
    setStateMessage(el.mnemonicState, "Saving...");
    await state.api.updateWordDetails(state.activeUserId, actionWord, el.wordMnemonic.value.trim() || null, state.currentLanguage);
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.mnemonicState, "Saved");
  } catch (err) {
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.mnemonicState, `Save failed: ${String(err.message || err)}`, true);
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = originalSubmitText || "Save Mnemonic";
    }
  }
};

el.addMeaningForm.onsubmit = async (event) => {
  event.preventDefault();
  const actionWord = state.selectedWord;
  const meaningText = el.manualMeaning.value.trim();
  if (!actionWord) {
    setStateMessage(el.meaningsState, "Pick a word in reader first", true);
    return;
  }
  if (!meaningText) {
    setStateMessage(el.meaningsState, "Meaning cannot be empty", true);
    return;
  }
  const submitButton = el.addMeaningForm.querySelector("button[type='submit']");
  const originalSubmitText = submitButton ? submitButton.textContent : "";
  try {
    requireUser();
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Adding...";
    }
    setStateMessage(el.meaningsState, "Saving...");
    await state.api.createMeaning(state.activeUserId, actionWord, meaningText, state.currentLanguage);
    if (state.selectedWord !== actionWord) {
      return;
    }
    el.manualMeaning.value = "";
    setStateMessage(el.meaningsState, "");
    await loadMeaningsForWord(actionWord);
  } catch (err) {
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.meaningsState, `Save failed: ${String(err.message || err)}`, true);
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = originalSubmitText || "Add Meaning";
    }
  }
};

el.generateMeaningForm.onsubmit = async (event) => {
  event.preventDefault();
  const actionWord = state.selectedWord;
  if (!actionWord) {
    setStateMessage(el.meaningsState, "Pick a word in reader first", true);
    return;
  }
  const submitButton = el.generateMeaningForm.querySelector("button[type='submit']");
  const originalSubmitText = submitButton ? submitButton.textContent : "";
  try {
    requireUser();
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Generating...";
    }
    setStateMessage(el.meaningsState, "Generating...");
    await state.api.generateMeaning(state.activeUserId, actionWord, el.meaningContext.value.trim(), state.currentLanguage);
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.meaningsState, "");
    el.meaningContext.value = "";
    await loadMeaningsForWord(actionWord);
  } catch (err) {
    if (state.selectedWord !== actionWord) {
      return;
    }
    setStateMessage(el.meaningsState, `Generate failed: ${String(err.message || err)}`, true);
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = originalSubmitText || "Generate English Meaning";
    }
  }
};

// Keyboard controls for SRS
document.addEventListener("keydown", async (event) => {
  if (event.key === "A" && event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey) {
    if (state.currentView !== "reader" || !state.activeUserId || !state.currentSentence) {
      return;
    }
    const tokens = state.currentSentence.tokens;
    const toMark = tokens.filter((t) => t.state !== "known");
    if (toMark.length === 0) return;
    try {
      await Promise.all(
        toMark.map((t) =>
          state.api.updateWordState(state.activeUserId, t.normalized_word, "known", state.currentLanguage)
        )
      );
      // Update local token states and re-render
      for (const t of state.currentSentence.tokens) {
        t.state = "known";
      }
      renderSentence();
    } catch (_) {
      // Silent fail — no UI disruption for a secret shortcut
    }
    return;
  }
});

document.addEventListener("keydown", (event) => {
  if (state.currentView !== "srs" || !state.srsCurrentCard) {
    return;
  }
  const activeTag = document.activeElement?.tagName?.toLowerCase() || "";
  if (activeTag === "input" || activeTag === "textarea" || activeTag === "select") {
    return;
  }

  // Space: flip card
  if (event.code === "Space" && !state.srsRevealed) {
    event.preventDefault();
    void revealSrsCard();
    return;
  }

  // 0: wrong (only when revealed)
  if (event.key === "0" && state.srsRevealed) {
    event.preventDefault();
    void submitSrsResult("wrong");
    return;
  }

  // 1: right (only when revealed)
  if (event.key === "1" && state.srsRevealed) {
    event.preventDefault();
    void submitSrsResult("right");
    return;
  }

  // Ctrl+Z: undo
  if ((event.ctrlKey || event.metaKey) && event.key === "z" && state.srsUndoHistory.length > 0) {
    event.preventDefault();
    void undoSrsReview();
    return;
  }
});

el.srsMnemonicView.addEventListener("click", startSrsMnemonicEdit);

el.srsMnemonicView.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    startSrsMnemonicEdit();
  }
});

el.srsMnemonicInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    el.srsMnemonicForm.requestSubmit();
    return;
  }
  if (event.key === "Escape") {
    event.preventDefault();
    cancelSrsMnemonicEdit();
  }
});

el.srsAddNewForm.onsubmit = async (event) => {
  event.preventDefault();
  if (!state.activeUserId) {
    setStateMessage(el.srsState, "Select a user first", true);
    return;
  }
  if (state.srsCurrentCard || state.srsDueQueue.length > 0) {
    setStateMessage(el.srsState, "Clear due reviews first", true);
    return;
  }

  const count = Math.max(1, Number(el.srsAddCount.value || "10"));
  const submitButton = el.srsAddSubmit;
  const previousText = submitButton.textContent;
  try {
    submitButton.disabled = true;
    submitButton.textContent = "Adding...";
    setStateMessage(el.srsState, "Adding...");
    const data = await state.api.addSrsNewCards(state.activeUserId, count, timezoneOffsetMinutes(), state.currentLanguage);
    applySrsSessionData(data.added_cards, data);
    setStateMessage(el.srsState, "");
    renderSrs();
  } catch (err) {
    setStateMessage(el.srsState, String(err.message || err), true);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = previousText || "Add New Cards";
  }
};

el.srsMnemonicForm.onsubmit = async (event) => {
  event.preventDefault();
  const word = state.srsCurrentCard?.normalized_word;
  if (!word || !state.activeUserId) {
    return;
  }
  const nextMnemonic = el.srsMnemonicInput.value.trim() || null;
  const previousText = el.srsMnemonicSave.textContent;
  try {
    el.srsMnemonicSave.disabled = true;
    el.srsMnemonicSave.textContent = "Saving...";
    setStateMessage(el.srsState, "Saving mnemonic...");
    const data = await state.api.updateWordDetails(state.activeUserId, word, nextMnemonic, state.currentLanguage);
    if (state.srsCurrentCard?.normalized_word !== word) {
      return;
    }
    state.srsMnemonic = data?.mnemonic || null;
    state.srsMnemonicEditing = false;
    setStateMessage(el.srsState, "");
    renderSrs();
  } catch (err) {
    setStateMessage(el.srsState, `Mnemonic save failed: ${String(err.message || err)}`, true);
  } finally {
    el.srsMnemonicSave.disabled = false;
    el.srsMnemonicSave.textContent = previousText || "Save";
  }
};

window.addEventListener("keydown", (event) => {
  if (state.currentView === "reader" && event.key === "F3") {
    event.preventDefault();
    state.readerShowNikkud = !state.readerShowNikkud;
    renderSentence();
    return;
  }

  if (state.currentView !== "srs") {
    return;
  }
  const activeTag = document.activeElement?.tagName?.toLowerCase() || "";
  if (activeTag === "textarea") {
    return;
  }
  if (event.key === " " || event.code === "Space") {
    if (state.srsCurrentCard && !state.srsRevealed) {
      event.preventDefault();
      void revealSrsCard();
    }
    return;
  }
  if (event.key === "0") {
    if (state.srsCurrentCard && state.srsRevealed) {
      event.preventDefault();
      void submitSrsResult("wrong");
    }
    return;
  }
  if (event.key === "1" && state.srsCurrentCard && state.srsRevealed) {
    event.preventDefault();
    void submitSrsResult("right");
  }
});

(async function bootstrap() {
  if (el.wordsLimit) {
    el.wordsLimit.value = String(state.wordsLimit);
  }
  void renderBackupStatus();

  // Load users first
  await loadUsers();
  await renderUserPicker();

  // Check if there's a logged-in user from localStorage
  if (state.activeUserId) {
    state.isLoggedIn = true;
    state.currentView = "library";
    updateViewVisibility();
    updateLanguageSwitcher();
    updateDirectionAttributes();
    await Promise.all([loadTexts(), loadWords()]);
    hideUserSelection();
  } else {
    // No logged-in user, show only the modal on blank page
    state.isLoggedIn = false;
    state.currentView = "library";
    el.appHeader.classList.add("is-hidden");
    el.sectionLibrary.classList.remove("active");
    el.sectionSrs.classList.remove("active");
    el.sectionReader.classList.remove("active");
    el.readerExitBtn.classList.remove("active");
    showUserSelection();
  }
})();
