// Party list matches the parties tracked on /bc-party-leaders and in the
// polling table on /bc-election-polls. Candidate nominations are not final
// until October 3, so this reader poll asks about party choice, not candidates.
const PARTIES = [
  { id: "ndp", name: "BC NDP" },
  { id: "con", name: "Conservative Party of BC" },
  { id: "grn", name: "BC Greens" },
  { id: "cbc", name: "CentreBC" },
  { id: "one", name: "OneBC" },
  { id: "other", name: "Another party / independent" },
  { id: "und", name: "Undecided" }
];

const PARTY_IDS = new Set(PARTIES.map(p => p.id));

const VOTE_COOKIE = "bcvw_partypoll_voted";
const DEDUP_TTL_SECONDS = 60 * 60 * 24 * 120; // covers Oct 24, 2026 election day plus a buffer

const SOURCE_LABELS = new Set(["google","bing","duckduckgo","yahoo","baidu","facebook","instagram","x","reddit","wechat","whatsapp","weibo","youtube","linkedin","copy","share","internal","other","direct"]);
const SOURCES_KEY = "sources";

const ALLOWED_ORIGINS = new Set([
  "https://bcvotewatch.ca",
  "https://www.bcvotewatch.ca",
  "https://bcvotewatch-ca.pages.dev",
  "https://bcvotewatch.pages.dev"
]);

function parseCookies(header) {
  return Object.fromEntries((header || "").split(";").map(part => {
    const index = part.indexOf("=");
    return index < 0 ? ["", ""] : [part.slice(0, index).trim(), part.slice(index + 1).trim()];
  }).filter(([key]) => key));
}

async function sha256Hex(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
}

function zeroCounts() {
  return Object.fromEntries(PARTIES.map(p => [p.id, 0]));
}

function emptyResults() {
  return {
    party: zeroCounts(),
    partyBC: zeroCounts(),
    totalBallots: 0,
    totalBallotsBC: 0,
    updatedAt: new Date().toISOString()
  };
}

// Backfills the BC-only fields onto results saved before that breakdown
// existed, so earlier votes aren't lost when this shape is read back.
function withBCFields(parsed) {
  return {
    partyBC: zeroCounts(),
    totalBallotsBC: 0,
    ...parsed
  };
}

async function loadResults(env) {
  const raw = await env.PARTY_POLL_KV.get("results");
  if (!raw) return emptyResults();
  try {
    const parsed = JSON.parse(raw);
    if (parsed && parsed.party) return withBCFields(parsed);
  } catch (_) {}
  return emptyResults();
}

// Cloudflare's request.cf carries MaxMind-derived geolocation (region-level, not
// verified) — good enough for a "BC readers vs. everyone" split on an informal
// reader poll, not for anything that needs certainty about a voter's location.
function isBC(request) {
  const cf = request.cf;
  if (!cf || cf.country !== "CA") return false;
  return cf.regionCode === "BC" || cf.region === "British Columbia";
}

function jsonResponse(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...extraHeaders }
  });
}

async function loadSources(env) {
  try {
    const raw = await env.PARTY_POLL_KV.get(SOURCES_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (_) {
    return {};
  }
}

export async function onRequestGet({ request, env }) {
  if (new URL(request.url).searchParams.get("sources") === "1") {
    return jsonResponse({ ok: true, sources: await loadSources(env) });
  }
  const results = await loadResults(env);
  return jsonResponse({ ok: true, results });
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get("Origin");
  if (origin) {
    const sameHost = new URL(origin).host === request.headers.get("Host");
    if (!sameHost && !ALLOWED_ORIGINS.has(origin)) {
      return jsonResponse({ ok: false, error: "invalid_origin" }, 403);
    }
  }

  let body;
  try {
    body = await request.json();
  } catch (_) {
    return jsonResponse({ ok: false, error: "invalid_json" }, 400);
  }

  const partyId = String(body.partyId || "");
  if (!PARTY_IDS.has(partyId)) {
    return jsonResponse({ ok: false, error: "invalid_party" }, 400);
  }

  const cookies = parseCookies(request.headers.get("Cookie"));
  const ip = request.headers.get("CF-Connecting-IP") || "";
  const ipHash = await sha256Hex(`${ip}:${env.POLL_IP_SALT || ""}`);
  const dedupKey = `voter:${ipHash}`;

  const alreadyVoted = cookies[VOTE_COOKIE] === "1" || (await env.PARTY_POLL_KV.get(dedupKey)) !== null;
  if (alreadyVoted) {
    return jsonResponse({ ok: true, alreadyVoted: true, results: await loadResults(env) });
  }

  const results = await loadResults(env);
  const fromBC = isBC(request);
  results.party[partyId] = (results.party[partyId] || 0) + 1;
  results.totalBallots += 1;
  if (fromBC) {
    results.partyBC[partyId] = (results.partyBC[partyId] || 0) + 1;
    results.totalBallotsBC += 1;
  }
  results.updatedAt = new Date().toISOString();

  await env.PARTY_POLL_KV.put("results", JSON.stringify(results));
  await env.PARTY_POLL_KV.put(dedupKey, "1", { expirationTtl: DEDUP_TTL_SECONDS });

  const source = SOURCE_LABELS.has(body.source) ? body.source : "direct";
  const sources = await loadSources(env);
  sources[source] = (sources[source] || 0) + 1;
  await env.PARTY_POLL_KV.put(SOURCES_KEY, JSON.stringify(sources));

  return jsonResponse({ ok: true, alreadyVoted: false, results }, 200, {
    "Set-Cookie": `${VOTE_COOKIE}=1; Path=/; Max-Age=${DEDUP_TTL_SECONDS}; HttpOnly; Secure; SameSite=Lax`
  });
}
