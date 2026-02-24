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

  listTexts(userId) {
    return this.request(`/v1/users/${userId}/texts`, { method: "GET" });
  }

  createText(userId, title, content) {
    return this.request(`/v1/users/${userId}/texts`, {
      method: "POST",
      body: JSON.stringify({ title, content }),
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

  updateWordState(userId, normalizedWord, state) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}`, {
      method: "PUT",
      body: JSON.stringify({ state }),
    });
  }

  listWords(userId, state = "all", page = 1, limit = 50) {
    return this.request(`/v1/users/${userId}/words?state=${state}&page=${page}&limit=${limit}`, {
      method: "GET",
    });
  }

  listMeanings(userId, normalizedWord) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings`, {
      method: "GET",
    });
  }

  createMeaning(userId, normalizedWord, meaningText) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings`, {
      method: "POST",
      body: JSON.stringify({ meaning_text: meaningText }),
    });
  }

  generateMeaning(userId, normalizedWord, sentenceContext) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/generate`, {
      method: "POST",
      body: JSON.stringify({ sentence_context: sentenceContext || null }),
    });
  }

  updateMeaning(userId, normalizedWord, meaningId, meaningText) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/${meaningId}`, {
      method: "PUT",
      body: JSON.stringify({ meaning_text: meaningText }),
    });
  }

  deleteMeaning(userId, normalizedWord, meaningId) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/${meaningId}`, {
      method: "DELETE",
    });
  }

  getWordDetails(userId, normalizedWord) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/details`, {
      method: "GET",
    });
  }

  updateWordDetails(userId, normalizedWord, mnemonic) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/details`, {
      method: "PUT",
      body: JSON.stringify({ mnemonic }),
    });
  }
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
  activeView: localStorage.getItem("active_view") || "library",
  requestVersion: {
    users: 0,
    texts: 0,
    sentence: 0,
    words: 0,
    meanings: 0,
    wordDetails: 0,
    wordSave: 0,
  },
};

const el = {
  appRoot: document.querySelector("[data-testid='app-root']"),
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
};
const VIEW_ORDER = ["library", "reader", "words"];

function nextRequestVersion(key) {
  state.requestVersion[key] += 1;
  return state.requestVersion[key];
}

function isCurrentRequest(key, version) {
  return state.requestVersion[key] === version;
}

function setStateMessage(node, text, isError = false) {
  node.textContent = text || "";
  node.classList.toggle("error", Boolean(isError));
  node.classList.toggle("loading", text === "Loading...");
  node.classList.toggle("empty", text === "Empty");
}

function renderListState(listNode, stateNode, options) {
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
  el.meaningsPreview.innerHTML = "";
  el.meaningsList.innerHTML = "";
}

function setActiveView(viewName, persist = true) {
  const allowedViews = new Set(VIEW_ORDER);
  const nextView = allowedViews.has(viewName) ? viewName : "library";
  state.activeView = nextView;
  if (el.appRoot) {
    el.appRoot.classList.remove("view-library", "view-reader", "view-words");
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
  el.textsList.innerHTML = "";
  el.readerMeta.textContent = "No text open";
  setStateMessage(el.readerState, "");
  el.readerSentence.textContent = "";
  el.wordsList.innerHTML = "";
  el.wordsPageLabel.textContent = "Page 1";
  el.wordsPrevPage.disabled = true;
  el.wordsNextPage.disabled = true;
  clearWordDetailsPanel();
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

  el.textsList.innerHTML = "";
  for (const text of state.texts) {
    const li = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = text.title;
    const progress = document.createElement("div");
    progress.innerHTML = `<small>Known: ${text.progress.known_count} | Unknown: ${text.progress.unknown_count} | Never: ${text.progress.never_seen_count} | ${text.progress.known_percent}%</small>`;
    const renameState = document.createElement("div");
    renameState.className = "state";

    const controls = document.createElement("div");

    const open = document.createElement("button");
    open.type = "button";
    open.textContent = "Open in Reader";
    open.title = "Open this text in Reader view";
    open.onclick = async () => {
      state.openTextId = text.text_id;
      state.sentenceIndex = 0;
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
    renderListState(el.textsList, el.textsState, { empty: true, emptyMessage: "Select a user first" });
    return;
  }

  renderListState(el.textsList, el.textsState, { loading: true });
  try {
    const data = await state.api.listTexts(state.activeUserId);
    if (!isCurrentRequest("texts", requestVersion)) {
      return;
    }
    state.texts = data.items;
    renderTexts();
  } catch (err) {
    if (!isCurrentRequest("texts", requestVersion)) {
      return;
    }
    renderListState(el.textsList, el.textsState, { error: String(err.message || err) });
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
  if (!el.meaningContext.value.trim() && state.currentSentence?.sentence_text) {
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

function renderSentence(data = state.currentSentence) {
  if (!data) {
    el.readerSentence.textContent = "";
    return;
  }

  state.currentSentence = data;
  el.readerMeta.textContent = `Text ${data.text_id} - sentence ${data.sentence_index}`;
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
      btn.textContent = part;
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
    setStateMessage(el.readerState, "");
  } catch (err) {
    if (!isCurrentRequest("sentence", requestVersion)) {
      return;
    }
    if (String(err.message || err) === "sentence_not_found") {
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

  el.wordsList.innerHTML = "";
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
      await state.api.updateWordState(state.activeUserId, item.normalized_word, select.value);
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
    const data = await state.api.listWords(state.activeUserId, el.wordsFilter.value, state.wordsPage, state.wordsLimit);
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

async function loadWordDetailsForWord(word) {
  const requestVersion = nextRequestVersion("wordDetails");
  if (!state.activeUserId || !word) {
    el.wordMnemonic.value = "";
    return;
  }
  setStateMessage(el.mnemonicState, "Loading...");
  try {
    const data = await state.api.getWordDetails(state.activeUserId, word);
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
    const data = await state.api.listMeanings(state.activeUserId, word);
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
    await state.api.updateMeaning(state.activeUserId, actionWord, meaningId, newText);
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
    await state.api.updateWordState(state.activeUserId, wordAtSaveStart, nextState);
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
    await state.api.deleteMeaning(state.activeUserId, actionWord, meaningId);
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

el.includeDeleted.onchange = () => {
  state.includeDeleted = el.includeDeleted.checked;
  loadUsers();
};
el.refreshUsers.onclick = () => loadUsers();
el.refreshTexts.onclick = () => loadTexts();
el.refreshWords.onclick = () => loadWords();
el.wordsFilter.onchange = () => {
  state.wordsPage = 1;
  loadWords();
};
el.wordsLimit.onchange = () => {
  state.wordsLimit = Number(el.wordsLimit.value);
  state.wordsPage = 1;
  loadWords();
};
el.wordsPrevPage.onclick = () => {
  if (state.wordsPage <= 1) return;
  state.wordsPage -= 1;
  loadWords();
};
el.wordsNextPage.onclick = () => {
  state.wordsPage += 1;
  loadWords();
};
window.addEventListener("pointermove", (event) => {
  const x = `${Math.round((event.clientX / window.innerWidth) * 100)}%`;
  const y = `${Math.round((event.clientY / window.innerHeight) * 100)}%`;
  document.documentElement.style.setProperty("--mouse-x", x);
  document.documentElement.style.setProperty("--mouse-y", y);
});

el.createUserForm.onsubmit = async (event) => {
  event.preventDefault();
  try {
    const name = el.newUserName.value.trim();
    if (!name) return;
    const created = await state.api.createUser(name);
    state.activeUserId = created.user_id;
    localStorage.setItem("active_user_id", state.activeUserId);
    el.newUserName.value = "";
    await loadUsers();
    await Promise.all([loadTexts(), loadWords()]);
  } catch (err) {
    setStateMessage(el.usersState, String(err.message || err), true);
  }
};

el.activeUser.onchange = async () => {
  state.activeUserId = el.activeUser.value;
  localStorage.setItem("active_user_id", state.activeUserId);
  clearUserScopedViews();
  state.wordsLimit = Number(el.wordsLimit.value);
  await Promise.all([loadTexts(), loadWords()]);
};

el.createTextForm.onsubmit = async (event) => {
  event.preventDefault();
  try {
    requireUser();
    const title = el.newTextTitle.value.trim();
    const content = el.newTextContent.value.trim();
    if (!title || !content) return;
    await state.api.createText(state.activeUserId, title, content);
    el.newTextTitle.value = "";
    el.newTextContent.value = "";
    await loadTexts();
  } catch (err) {
    setStateMessage(el.textsState, String(err.message || err), true);
  }
};

el.prevSentence.onclick = async () => {
  if (!el.prevSentence.dataset.target) return;
  clearWordDetailsPanel();
  state.sentenceIndex = Number(el.prevSentence.dataset.target);
  await loadSentence();
};

el.nextSentence.onclick = async () => {
  if (!el.nextSentence.dataset.target) return;
  clearWordDetailsPanel();
  state.sentenceIndex = Number(el.nextSentence.dataset.target);
  await loadSentence();
};

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
    await state.api.updateWordDetails(state.activeUserId, actionWord, el.wordMnemonic.value.trim() || null);
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
    await state.api.createMeaning(state.activeUserId, actionWord, meaningText);
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
    await state.api.generateMeaning(state.activeUserId, actionWord, el.meaningContext.value.trim());
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

(async function bootstrap() {
  el.wordsLimit.value = String(state.wordsLimit);
  setActiveView(state.activeView, false);
  await loadUsers();
  if (state.activeUserId) {
    await Promise.all([loadTexts(), loadWords()]);
  }
})();
