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

  health() {
    return this.request("/health", { method: "GET" });
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

  generateMeaning(userId, normalizedWord, sentenceContext) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/generate`, {
      method: "POST",
      body: JSON.stringify({ sentence_context: sentenceContext || null }),
    });
  }

  deleteMeaning(userId, normalizedWord, meaningId) {
    return this.request(`/v1/users/${userId}/words/${encodeURIComponent(normalizedWord)}/meanings/${meaningId}`, {
      method: "DELETE",
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
  isWordModalOpen: false,
  wordsPage: 1,
  wordsLimit: 50,
  activeView: localStorage.getItem("active_view") || "library",
  requestVersion: {
    users: 0,
    texts: 0,
    sentence: 0,
    words: 0,
    meanings: 0,
  },
  lastWordTriggerElement: null,
  lastWordTriggerId: "",
};

const el = {
  apiBaseUrl: document.getElementById("api-base-url"),
  saveApiBase: document.getElementById("save-api-base"),
  checkHealth: document.getElementById("check-health"),
  healthIndicator: document.getElementById("health-indicator"),
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
  jumpSentenceForm: document.getElementById("jump-sentence-form"),
  jumpSentenceIndex: document.getElementById("jump-sentence-index"),
  wordsFilter: document.getElementById("words-filter"),
  wordsLimit: document.getElementById("words-limit"),
  wordsPrevPage: document.getElementById("words-prev-page"),
  wordsNextPage: document.getElementById("words-next-page"),
  wordsPageLabel: document.getElementById("words-page-label"),
  refreshWords: document.getElementById("refresh-words"),
  wordsState: document.getElementById("words-state"),
  wordsList: document.getElementById("words-list"),
  meaningsWord: document.getElementById("meanings-word"),
  generateMeaningForm: document.getElementById("generate-meaning-form"),
  meaningContext: document.getElementById("meaning-context"),
  meaningsState: document.getElementById("meanings-state"),
  meaningsList: document.getElementById("meanings-list"),
  modalWordState: document.getElementById("modal-word-state"),
  wordModal: document.getElementById("word-modal"),
  wordModalBackdrop: document.getElementById("word-modal-backdrop"),
  closeWordModal: document.getElementById("close-word-modal"),
  wordModalSurface: document.getElementById("word-modal-surface"),
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

function setActiveView(viewName, persist = true) {
  const allowedViews = new Set(VIEW_ORDER);
  const nextView = allowedViews.has(viewName) ? viewName : "library";
  state.activeView = nextView;
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
    closeWordModal({ restoreFocus: false });
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
  state.selectedWord = "";
  state.wordsPage = 1;
  el.textsList.innerHTML = "";
  el.readerMeta.textContent = "No text open";
  setStateMessage(el.readerState, "");
  el.readerSentence.textContent = "";
  el.wordsList.innerHTML = "";
  el.wordsPageLabel.textContent = "Page 1";
  el.wordsPrevPage.disabled = true;
  el.wordsNextPage.disabled = true;
  el.meaningsList.innerHTML = "";
  closeWordModal({ restoreFocus: false });
  el.meaningsWord.textContent = "Select a word";
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
        el.readerMeta.textContent = "No text open";
        el.readerSentence.textContent = "";
        closeWordModal({ restoreFocus: false });
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

function isFocusableElement(node) {
  return node instanceof HTMLElement && node.isConnected && !node.hasAttribute("disabled");
}

function openWordModal(triggerElement = null) {
  if (isFocusableElement(triggerElement)) {
    state.lastWordTriggerElement = triggerElement;
  }
  state.lastWordTriggerId = triggerElement?.dataset?.wordButtonId || "";
  state.isWordModalOpen = true;
  el.wordModal.classList.add("is-open");
  el.wordModal.setAttribute("aria-hidden", "false");
  el.meaningsWord.textContent = state.selectedWord || "No word selected";
  const tokenState = state.currentSentence?.tokens?.find((t) => t.normalized_word === state.selectedWord)?.state;
  if (tokenState) {
    el.modalWordState.value = tokenState;
  }
  el.modalWordState.focus();
}

function closeWordModal(options = {}) {
  const { restoreFocus = true } = options;
  state.isWordModalOpen = false;
  el.wordModal.classList.remove("is-open");
  el.wordModal.setAttribute("aria-hidden", "true");
  el.wordModal.removeAttribute("data-busy");
  if (restoreFocus) {
    if (isFocusableElement(state.lastWordTriggerElement)) {
      state.lastWordTriggerElement.focus();
      return;
    }
    if (state.lastWordTriggerId) {
      const replacement = el.readerSentence.querySelector(`[data-word-button-id="${state.lastWordTriggerId}"]`);
      if (isFocusableElement(replacement)) {
        replacement.focus();
      }
    }
  }
}

function renderSentence(data) {
  state.currentSentence = data;
  el.readerMeta.textContent = `Text ${data.text_id} - sentence ${data.sentence_index}`;
  el.prevSentence.disabled = data.prev_sentence_index === null;
  el.nextSentence.disabled = data.next_sentence_index === null;
  el.prevSentence.dataset.target = data.prev_sentence_index;
  el.nextSentence.dataset.target = data.next_sentence_index;

  if (data.next_sentence_index === null) {
    state.maxSentenceIndex = data.sentence_index;
  }
  el.jumpSentenceIndex.value = String(data.sentence_index);
  el.jumpSentenceIndex.max = state.maxSentenceIndex === null ? "" : String(state.maxSentenceIndex);

  const wordStateByNormalized = buildWordStateMap(data.tokens);
  if (state.selectedWord && !wordStateByNormalized.has(state.selectedWord)) {
    state.selectedWord = "";
    closeWordModal({ restoreFocus: false });
    el.meaningsWord.textContent = "Select a word";
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
      btn.onclick = async () => {
        state.selectedWord = normalized;
        openWordModal(btn);
        renderSentence(state.currentSentence);
        await loadMeanings();
      };
      el.readerSentence.appendChild(btn);
    });
  }
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
  if (
    renderListState(el.meaningsList, el.meaningsState, {
      empty: data.items.length === 0,
      emptyMessage: "No meanings yet",
    })
  ) {
    return;
  }

  el.meaningsList.innerHTML = "";
  for (const item of data.items) {
    const li = document.createElement("li");
    li.innerHTML = `<div>${item.meaning_text}</div><small>${item.created_at}</small>`;
    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "Delete";
    del.onclick = async () => {
      try {
        li.classList.add("is-removing");
        del.disabled = true;
        el.wordModal.setAttribute("data-busy", "deleting");
        setStateMessage(el.meaningsState, "Deleting...");
        await state.api.deleteMeaning(state.activeUserId, state.selectedWord, item.meaning_id);
        await loadMeanings();
      } catch (err) {
        setStateMessage(el.meaningsState, String(err.message || err), true);
      } finally {
        el.wordModal.removeAttribute("data-busy");
      }
    };
    li.appendChild(del);
    el.meaningsList.appendChild(li);
  }
}

async function loadMeanings() {
  const requestVersion = nextRequestVersion("meanings");
  if (!state.activeUserId || !state.selectedWord) {
    renderListState(el.meaningsList, el.meaningsState, {
      empty: true,
      emptyMessage: "Pick a word in the reader first",
    });
    return;
  }
  const requestedWord = state.selectedWord;

  renderListState(el.meaningsList, el.meaningsState, { loading: true });
  try {
    const data = await state.api.listMeanings(state.activeUserId, requestedWord);
    if (!isCurrentRequest("meanings", requestVersion) || requestedWord !== state.selectedWord) {
      return;
    }
    renderMeanings(data);
  } catch (err) {
    if (!isCurrentRequest("meanings", requestVersion)) {
      return;
    }
    renderListState(el.meaningsList, el.meaningsState, { error: String(err.message || err) });
  }
}

async function updateSelectedWordState(nextState) {
  if (!["known", "unknown", "never_seen"].includes(nextState)) {
    setStateMessage(el.readerState, "Invalid word state", true);
    return;
  }
  if (!state.activeUserId || !state.selectedWord) {
    setStateMessage(el.readerState, "Select a word first", true);
    return;
  }

  try {
    el.modalWordState.disabled = true;
    setStateMessage(el.readerState, "Updating word state...");
    await state.api.updateWordState(state.activeUserId, state.selectedWord, nextState);
    await Promise.all([loadSentence(), loadWords(), loadTexts(), loadMeanings()]);
    setStateMessage(el.readerState, "");
  } catch (err) {
    setStateMessage(el.readerState, String(err.message || err), true);
  } finally {
    el.modalWordState.disabled = false;
  }
}

async function checkHealth() {
  try {
    el.healthIndicator.textContent = "Checking...";
    const result = await state.api.health();
    el.healthIndicator.textContent = result.status === "ok" ? "Healthy" : "Unhealthy";
  } catch (err) {
    el.healthIndicator.textContent = `Error: ${String(err.message || err)}`;
  }
}

el.apiBaseUrl.value = localStorage.getItem("api_base_url") || "";
el.saveApiBase.onclick = () => {
  localStorage.setItem("api_base_url", el.apiBaseUrl.value.trim());
  state.api.setBaseUrl(el.apiBaseUrl.value.trim());
  checkHealth();
};

el.checkHealth.onclick = () => checkHealth();
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
el.wordModalBackdrop.onclick = () => closeWordModal();
el.closeWordModal.onclick = () => closeWordModal();
el.modalWordState.onchange = () => updateSelectedWordState(el.modalWordState.value);
el.wordModalSurface.onkeydown = (event) => {
  if (event.key === "Escape") {
    closeWordModal();
  }
};
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.isWordModalOpen) {
    closeWordModal();
  }
});
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
  state.sentenceIndex = Number(el.prevSentence.dataset.target);
  await loadSentence();
};

el.nextSentence.onclick = async () => {
  if (!el.nextSentence.dataset.target) return;
  state.sentenceIndex = Number(el.nextSentence.dataset.target);
  await loadSentence();
};

el.jumpSentenceForm.onsubmit = async (event) => {
  event.preventDefault();
  if (!state.openTextId) {
    setStateMessage(el.readerState, "Open a text first", true);
    return;
  }

  const raw = Number(el.jumpSentenceIndex.value);
  if (!Number.isInteger(raw)) {
    setStateMessage(el.readerState, "Enter a whole sentence index", true);
    return;
  }

  const minClamped = Math.max(0, raw);
  const clamped =
    state.maxSentenceIndex === null ? minClamped : Math.min(state.maxSentenceIndex, minClamped);
  state.sentenceIndex = clamped;
  if (clamped !== raw) {
    setStateMessage(el.readerState, `Jump clamped to ${clamped}`, true);
  }
  await loadSentence();
};

el.generateMeaningForm.onsubmit = async (event) => {
  event.preventDefault();
  const submitButton = el.generateMeaningForm.querySelector("button[type='submit']");
  const originalSubmitText = submitButton ? submitButton.textContent : "";
  try {
    requireUser();
    if (!state.selectedWord) throw new Error("Pick a word in reader first");
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Generating...";
    }
    el.wordModal.setAttribute("data-busy", "generating");
    setStateMessage(el.meaningsState, "Generating...");
    await state.api.generateMeaning(state.activeUserId, state.selectedWord, el.meaningContext.value.trim());
    el.meaningContext.value = "";
    await loadMeanings();
  } catch (err) {
    setStateMessage(el.meaningsState, String(err.message || err), true);
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = originalSubmitText || "Generate English Meaning";
    }
    el.wordModal.removeAttribute("data-busy");
  }
};

(async function bootstrap() {
  el.wordsLimit.value = String(state.wordsLimit);
  setActiveView(state.activeView, false);
  await checkHealth();
  await loadUsers();
  if (state.activeUserId) {
    await Promise.all([loadTexts(), loadWords()]);
  }
})();
