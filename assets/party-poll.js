(() => {
const form = document.querySelector("#poll-form");
if (!form) return;

const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));

// Keep in sync with functions/api/party-poll.js.
const PARTIES = [
  { id: "ndp", name: "BC NDP" },
  { id: "con", name: "Conservative Party of BC" },
  { id: "grn", name: "BC Greens" },
  { id: "cbc", name: "CentreBC" },
  { id: "one", name: "OneBC" },
  { id: "other", name: "Another party / independent" },
  { id: "und", name: "Undecided" }
];

const STORAGE_KEY = "bcvw_partypoll_voted_ui";

function landingSource() {
  try {
    const v = new URLSearchParams(location.search).get("utm_source");
    return v ? v.toLowerCase() : "direct";
  } catch (_) { return "direct"; }
}
const LANDING_SOURCE = landingSource();

function shareLink(base, source) {
  return `${base}?utm_source=${source}&utm_medium=poll_share`;
}

function renderOptions() {
  document.querySelector("#party-options").innerHTML = PARTIES.map(p =>
    `<label class="pick-card"><input class="ballot-mark" type="radio" name="party" value="${p.id}">${esc(p.name)}</label>`
  ).join("");
}

function updateSubmitState() {
  const picked = document.querySelector('input[name="party"]:checked');
  document.querySelector("#poll-submit").disabled = !picked;
}

function rankRows(counts) {
  return PARTIES
    .map(p => ({ id: p.id, name: p.name, count: counts[p.id] || 0 }))
    .sort((a, b) => b.count - a.count);
}

function renderResultRows(container, rows, total, leadSlots = 1) {
  container.innerHTML = rows.map((r, i) => {
    const pct = total > 0 ? Math.round((r.count / total) * 1000) / 10 : 0;
    return `<div class="result-row${i < leadSlots && r.count > 0 ? " is-lead" : ""}">
      <div class="result-head"><span>${esc(r.name)}</span><span>${pct}% · ${r.count}</span></div>
      <div class="result-track"><div class="result-fill" data-pct="${pct}"></div></div>
    </div>`;
  }).join("");
  requestAnimationFrame(() => requestAnimationFrame(() => {
    container.querySelectorAll(".result-fill").forEach(el => { el.style.width = el.dataset.pct + "%"; });
  }));
}

function renderLeaderCard(rows, total) {
  const el = document.querySelector("#party-leader");
  const top = rows[0];
  if (!top || !top.count) { el.innerHTML = ""; return; }
  const pct = total > 0 ? Math.round((top.count / total) * 1000) / 10 : 0;
  el.innerHTML = `<div class="leader-card">
    <div class="leader-badge">🏆</div>
    <div><p class="leader-eyebrow">Leading among readers</p><p class="leader-name">${esc(top.name)}</p></div>
    <div class="leader-stat">${pct}%<small>${top.count} vote${top.count === 1 ? "" : "s"}</small></div>
  </div>`;
}

function shareText(pickedPartyName) {
  return pickedPartyName
    ? `I just voted for ${pickedPartyName} in BC Vote Watch's 2026 reader poll — cast your vote and see live results:`
    : "See live results from BC Vote Watch's 2026 reader poll — cast your vote:";
}

function wireShare(pickedPartyName) {
  const baseUrl = location.origin + location.pathname;
  const text = shareText(pickedPartyName);
  const t = encodeURIComponent(text);
  const u = src => encodeURIComponent(shareLink(baseUrl, src));
  const links = {
    ".share-x": `https://twitter.com/intent/tweet?url=${u("x")}&text=${t}`,
    ".share-facebook": `https://www.facebook.com/sharer/sharer.php?u=${u("facebook")}`,
    ".share-whatsapp": `https://api.whatsapp.com/send?text=${t}%20${u("whatsapp")}`,
    ".share-weibo": `https://service.weibo.com/share/share.php?url=${u("weibo")}&title=${t}`
  };
  Object.entries(links).forEach(([sel, href]) => {
    const el = document.querySelector(sel);
    if (el) el.href = href;
  });
  const status = document.querySelector("#share-status");
  const copyBtn = document.querySelector("#share-copy");
  if (copyBtn) copyBtn.onclick = async () => {
    try { await navigator.clipboard.writeText(shareLink(baseUrl, "copy")); status.textContent = "Link copied."; }
    catch (_) { status.textContent = shareLink(baseUrl, "copy"); }
  };
  const nativeBtn = document.querySelector("#share-native");
  if (nativeBtn && navigator.share) {
    nativeBtn.hidden = false;
    nativeBtn.onclick = async () => { try { await navigator.share({ title: text, url: shareLink(baseUrl, "share") }); } catch (_) {} };
  }
}

let latestResults = null;
let activeScope = "all";

function renderScope(scope) {
  if (!latestResults) return;
  activeScope = scope;
  document.querySelectorAll(".scope-tab").forEach(btn => {
    btn.setAttribute("aria-pressed", String(btn.dataset.scope === scope));
  });
  const counts = scope === "bc" ? latestResults.partyBC : latestResults.party;
  const total = (scope === "bc" ? latestResults.totalBallotsBC : latestResults.totalBallots) || 0;
  const scopeLabel = scope === "bc" ? "BC reader ballot" : "reader ballot";
  document.querySelector("#results-total").textContent =
    total > 0 ? `${total.toLocaleString("en-CA")} ${scopeLabel}${total === 1 ? "" : "s"} cast so far.` : `No ${scopeLabel}s yet.`;
  const rows = rankRows(counts);
  renderLeaderCard(rows, total);
  renderResultRows(document.querySelector("#party-results"), rows, total);
}

function showResults(results, opts = {}) {
  document.querySelector("#poll-form").hidden = true;
  const panel = document.querySelector("#poll-results");
  panel.hidden = false;
  document.querySelector("#vote-banner").hidden = !opts.justVoted;
  latestResults = results;
  renderScope(activeScope);
  wireShare(opts.pickedPartyName);
}

async function loadResultsOnly() {
  try {
    const res = await fetch("/api/party-poll", { headers: { Accept: "application/json" } });
    const data = await res.json();
    if (data.ok) showResults(data.results);
  } catch (_) {}
}

function setMessage(text) {
  const el = document.querySelector("#poll-msg");
  el.textContent = text;
  el.hidden = !text;
}

async function submitVote(e) {
  e.preventDefault();
  const partyInput = document.querySelector('input[name="party"]:checked');
  if (!partyInput) return;
  const submitBtn = document.querySelector("#poll-submit");
  submitBtn.disabled = true;
  setMessage("");
  try {
    const res = await fetch("/api/party-poll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ partyId: partyInput.value, source: LANDING_SOURCE })
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setMessage("Something went wrong submitting your vote. Please try again.");
      submitBtn.disabled = false;
      return;
    }
    try { localStorage.setItem(STORAGE_KEY, "1"); } catch (_) {}
    const picked = PARTIES.find(p => p.id === partyInput.value);
    showResults(data.results, { justVoted: !data.alreadyVoted, pickedPartyName: picked && picked.name });
  } catch (_) {
    setMessage("Network error — please check your connection and try again.");
    submitBtn.disabled = false;
  }
}

function init() {
  renderOptions();
  document.querySelectorAll('input[name="party"]').forEach(r => r.addEventListener("change", updateSubmitState));
  form.addEventListener("submit", submitVote);
  document.querySelectorAll(".scope-tab").forEach(btn => btn.addEventListener("click", () => renderScope(btn.dataset.scope)));

  let alreadyVoted = false;
  try { alreadyVoted = localStorage.getItem(STORAGE_KEY) === "1"; } catch (_) {}
  if (alreadyVoted) {
    form.hidden = true;
    loadResultsOnly();
  }
}

init();
})();
