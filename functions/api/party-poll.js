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
  if (new URL(request.url).searchParams.get("survey") === "1") {
    return jsonResponse({ ok: true, survey: await loadSurvey(env), alreadySubmitted: await surveySubmitted(request, env) });
  }
  if (new URL(request.url).searchParams.get("sources") === "1") {
    return jsonResponse({ ok: true, sources: await loadSources(env) });
  }
  const results = await loadResults(env);
  return jsonResponse({ ok: true, results });
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get("Origin");
  if (origin) {
    let sameHost = false;
    try { sameHost = new URL(origin).origin === new URL(request.url).origin; } catch (_) {}
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

  if (new URL(request.url).searchParams.get("survey") === "1") {
    return submitSurvey(request, env, body);
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

// The structured survey never reads or writes the historic "results" key.
const SURVEY_KEY = "structured:v1:results";
const SURVEY_COOKIE = "bcvw_structured_v1";
const SURVEY_TTL = 60 * 60 * 24 * 120;
const ISSUES = new Set(["living","healthcare","economy","housing","spending","crime","drugs","homelessness","education","environment","energy","taxes","federal","other"]);
const ELIGIBILITY = new Set(["yes","no","unsure"]);
const CERTAINTY = new Set(["very","fairly","change","uncertain"]);
const PAST_VOTE = new Set(["ndp","con","grn","other","did_not_vote","ineligible","unknown"]);
const REGIONS = new Set(["metro","fraser","island","south","north","other"]);
const AGES = new Set(["18_34","35_54","55_plus","prefer_not"]);
const GENDERS = new Set(["woman","man","another","prefer_not"]);
const EDUCATION = new Set(["high_school","college","university","postgrad","prefer_not"]);
const SECOND = new Set([...PARTY_IDS, "none"]);

function emptyBucket() {
  return { total: 0, initialChoice: {}, decidedLeaning: {}, certainty: {}, turnout: {}, turnoutSum: 0,
    secondChoice: {}, issues: {}, pastVote: {}, region: {}, age: {}, gender: {}, education: {},
    answered: { lean: 0, secondChoice: 0, issues: 0, region: 0, age: 0, gender: 0, education: 0 },
    answeredKnown: { issues: true } };
}
function emptySurvey() {
  return { version: 1, totalRespondents: 0, eligibleRespondents: 0, likelyVoters: 0,
    scopes: { all: emptyBucket(), eligible: emptyBucket(), likely: emptyBucket() }, updatedAt: null };
}
async function loadSurvey(env) {
  const raw = await env.PARTY_POLL_KV.get(SURVEY_KEY);
  if (!raw) return emptySurvey();
  try {
    const value = JSON.parse(raw);
    return value && value.version === 1 && value.scopes ? normalizeSurvey(value) : emptySurvey();
  } catch (_) { return emptySurvey(); }
}
function increment(obj, key) { obj[key] = (obj[key] || 0) + 1; }
function countValues(obj) { return Object.values(obj || {}).reduce((sum, value) => sum + (Number.isFinite(Number(value)) ? Number(value) : 0), 0); }
function normalizeBucket(old = {}) {
  const base = emptyBucket();
  const bucket = { ...base, ...old };
  const saved = old.answered || {};
  bucket.answered = {
    lean: saved.lean ?? Number(old.initialChoice?.und || 0),
    secondChoice: saved.secondChoice ?? countValues(old.secondChoice),
    issues: saved.issues ?? 0,
    region: saved.region ?? countValues(old.region),
    age: saved.age ?? countValues(old.age),
    gender: saved.gender ?? countValues(old.gender),
    education: saved.education ?? countValues(old.education)
  };
  bucket.answeredKnown = { issues: saved.issues !== undefined ? (old.answeredKnown?.issues !== false) : Number(old.total || 0) === 0 };
  return bucket;
}
function normalizeSurvey(value) {
  const empty = emptySurvey();
  return { ...empty, ...value, scopes: Object.fromEntries(["all", "eligible", "likely"].map(name => [name, normalizeBucket(value.scopes?.[name])])) };
}
function addResponse(bucket, answer) {
  bucket.total++;
  increment(bucket.initialChoice, answer.choice);
  increment(bucket.decidedLeaning, answer.choice === "und" ? (answer.lean || "und") : answer.choice);
  increment(bucket.certainty, answer.certainty);
  increment(bucket.turnout, String(answer.turnout));
  bucket.turnoutSum += answer.turnout;
  if (answer.lean) increment(bucket.answered, "lean");
  if (answer.secondChoice) { increment(bucket.secondChoice, answer.secondChoice); increment(bucket.answered, "secondChoice"); }
  if (Array.isArray(answer.issues)) increment(bucket.answered, "issues");
  for (const issue of answer.issues || []) increment(bucket.issues, issue);
  increment(bucket.pastVote, answer.pastVote);
  for (const field of ["region", "age", "gender", "education"]) {
    if (answer[field]) { increment(bucket[field], answer[field]); increment(bucket.answered, field); }
  }
}
function optionalEnumValid(value, whitelist) { return value === undefined || value === null || value === "" || whitelist.has(value); }
function validSurvey(a) {
  if (!a || typeof a !== "object" || Array.isArray(a)) return false;
  if (!ELIGIBILITY.has(a.eligibility) || !PARTY_IDS.has(a.choice)) return false;
  if (!optionalEnumValid(a.lean, PARTY_IDS)) return false;
  if (!CERTAINTY.has(a.certainty) || !Number.isInteger(a.turnout) || a.turnout < 0 || a.turnout > 10) return false;
  if (!optionalEnumValid(a.secondChoice, SECOND)) return false;
  if (a.secondChoice && (a.secondChoice === a.choice || (a.choice === "und" && a.secondChoice === a.lean && a.secondChoice !== "und"))) return false;
  if (a.issues !== undefined && a.issues !== null && a.issues !== "" && (!Array.isArray(a.issues) || a.issues.length > 3 || new Set(a.issues).size !== a.issues.length || a.issues.some(i => !ISSUES.has(i)))) return false;
  return PAST_VOTE.has(a.pastVote) && optionalEnumValid(a.region, REGIONS) && optionalEnumValid(a.age, AGES) && optionalEnumValid(a.gender, GENDERS) && optionalEnumValid(a.education, EDUCATION);
}
async function surveyDedupKey(request, env) {
  const ip = request.headers.get("CF-Connecting-IP");
  if (!ip || !env.POLL_IP_SALT) return null;
  return `structured:v1:voter:${await sha256Hex(`${ip}:${env.POLL_IP_SALT}:bc-survey-v1`)}`;
}
async function surveySubmitted(request, env) {
  if (parseCookies(request.headers.get("Cookie"))[SURVEY_COOKIE] === "1") return true;
  const key = await surveyDedupKey(request, env);
  return key ? (await env.PARTY_POLL_KV.get(key)) !== null : false;
}
function surveyWave(date) {
  // Fixed four-day periods beginning with the launch date.
  return 1 + Math.max(0, Math.floor((Date.parse(date.slice(0, 10) + "T00:00:00Z") - Date.UTC(2026, 8, 26)) / (4 * 86400000)));
}
async function submitSurvey(request, env, answer) {
  if (!validSurvey(answer)) return jsonResponse({ ok: false, error: "invalid_survey" }, 400);
  const dedupKey = await surveyDedupKey(request, env);
  if (!dedupKey) return jsonResponse({ ok: false, error: "survey_unavailable" }, 503);
  if (await surveySubmitted(request, env)) return jsonResponse({ ok: true, alreadySubmitted: true, survey: await loadSurvey(env) });
  const submittedAt = new Date().toISOString();
  const record = { eligibility: answer.eligibility, choice: answer.choice,
    lean: answer.choice === "und" ? (answer.lean || null) : null,
    certainty: answer.certainty, turnout: answer.turnout, secondChoice: answer.secondChoice || null,
    issues: Array.isArray(answer.issues) ? answer.issues : null, pastVote: answer.pastVote,
    region: answer.region || null, age: answer.age || null, gender: answer.gender || null,
    education: answer.education || null, submittedAt, wave: surveyWave(submittedAt) };
  const survey = await loadSurvey(env);
  addResponse(survey.scopes.all, record);
  survey.totalRespondents++;
  if (record.eligibility === "yes") {
    addResponse(survey.scopes.eligible, record);
    survey.eligibleRespondents++;
    if (record.turnout >= 8) {
      addResponse(survey.scopes.likely, record);
      survey.likelyVoters++;
    }
  }
  survey.updatedAt = submittedAt;
  await env.PARTY_POLL_KV.put(`structured:v1:entry:${crypto.randomUUID()}`, JSON.stringify(record));
  await env.PARTY_POLL_KV.put(SURVEY_KEY, JSON.stringify(survey));
  await env.PARTY_POLL_KV.put(dedupKey, "1", { expirationTtl: SURVEY_TTL });
  return jsonResponse({ ok: true, alreadySubmitted: false, survey }, 200, {
    "Set-Cookie": `${SURVEY_COOKIE}=1; Path=/; Max-Age=${SURVEY_TTL}; HttpOnly; Secure; SameSite=Lax`
  });
}
