(() => {
  const root = document.querySelector('#structured-survey');
  const quickResults = document.querySelector('#poll-results');
  if (!root || !quickResults) return;
  const richmond = root.dataset.site === 'richmond';
  const language = 'en';
  const localeIndex = -1;
  const TRANSLATIONS = {};
  const t = value => value;
  function translateStatic() {}
  const candidates = [
    ['65','CHEUNG, Dickens'],['78','HEED, Kash'],['54','HOWARD, Rob'],
    ['66','KANG, Mei'],['99','KING, Goldentiger'],['87','LEE, Dennet "The Cat Guy"'],['69','LOO, Alexa']
  ];
  const parties = [
    ['ndp','BC NDP'],['con','Conservative Party of BC'],['grn','BC Greens'],
    ['cbc','CentreBC'],['one','OneBC'],['other','Another party / independent'],['und','Undecided']
  ];
  const choices = richmond ? [...candidates,['und','Undecided'],['no_vote','Would not vote'],['prefer_not','Prefer not to say']] : parties;
  const leanChoices = richmond ? [...candidates,['und','Still undecided']] : [...parties.filter(x => x[0] !== 'und'),['und','Still undecided']];
  const secondChoices = richmond ? [...candidates,['none','No second choice'],['und','Undecided']] : [...parties.filter(x => x[0] !== 'und'),['none','No second choice'],['und','Undecided']];
  const issues = richmond ? [
    ['taxes','Property taxes / city spending'],['housing_cost','Housing affordability'],['housing_supply','Housing development / supply'],
    ['traffic','Traffic congestion'],['road_safety','Road safety'],['transit','Public transit'],['crime','Crime / public safety'],
    ['drugs','Drug use / addiction'],['homelessness','Homelessness'],['flood','Flood protection'],['infrastructure','Infrastructure'],
    ['parks','Parks / recreation / community services'],['business','Local business / economic development'],['other','Other']
  ] : [
    ['living','Cost of living / inflation'],['healthcare','Healthcare'],['economy','Economy / jobs'],['housing','Housing affordability'],
    ['spending','Government spending / deficit'],['crime','Crime / public safety'],['drugs','Drug use / addictions'],
    ['homelessness','Homelessness'],['education','Education'],['environment','Environment / climate'],['energy','Energy'],
    ['taxes','Taxes'],['federal','Federal-provincial relations'],['other','Other']
  ];
  const eligibility = richmond ? [['resident','Yes — Richmond resident elector'],['property','Yes — non-resident property elector'],['no','No'],['unsure','Not sure']] : [['yes','Yes'],['no','No'],['unsure','Not sure']];
  const certainty = [['very','Very certain'],['fairly','Fairly certain'],['change','Could change my mind'],['uncertain','Very uncertain']];
  const past = richmond ? [['yes','Yes'],['no','No'],['ineligible','Was not eligible'],['unknown',"Can't remember / prefer not to say"]] : [
    ['ndp','Voted BC NDP'],['con','Voted Conservative Party of BC'],['grn','Voted BC Greens'],
    ['other','Voted another party / independent'],['did_not_vote','Eligible but did not vote'],
    ['ineligible','Was not eligible'],['unknown',"Don't remember / prefer not to say"]
  ];
  const regions = richmond ? [['steveston','Steveston'],['centre','City Centre'],['broadmoor','Broadmoor / South Arm'],['east','East Richmond'],['west','West Richmond'],['other','Other / not sure']] : [
    ['metro','Metro Vancouver'],['fraser','Fraser Valley'],['island','Vancouver Island / Coast'],
    ['south','Southern Interior'],['north','Northern Interior / North'],['other','Other / not sure']
  ];
  const ages = [['18_34','18–34'],['35_54','35–54'],['55_plus','55+'],['prefer_not','Prefer not to say']];
  const genders = [['woman','Woman'],['man','Man'],['another','Another identity'],['prefer_not','Prefer not to say']];
  const education = [['high_school','High school or less'],['college','College / trades / certificate'],['university','University degree'],['postgrad','Postgraduate degree'],['prefer_not','Prefer not to say']];
  const labels = Object.fromEntries([...choices,...leanChoices,...secondChoices,...issues,...eligibility,...certainty,...past,...regions,...ages,...genders,...education]);
  const escape = x => String(x).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const shuffled = list => [...list].sort(() => Math.random() - .5);
  const radios = (name, list, required = false) => `<div class="survey-options">${list.map(([id,label]) => `<label class="survey-option"><input type="radio" name="${name}" value="${escape(id)}" ${required ? 'required' : ''}> ${escape(label)}</label>`).join('')}</div>`;
  const field = (name, title, list, required = false) => `<fieldset class="survey-field"><legend>${escape(title)} <span class="survey-requirement">${required ? 'Required' : 'Optional'}</span></legend>${radios(name,list,required)}</fieldset>`;
  const issueField = `<fieldset class="survey-field"><legend>${richmond ? 'Which three Richmond issues are most important to you?':'Which three issues are most important to you when deciding how to vote?'}</legend><p>Optional — choose up to 3. <span id="issue-count">0</span>/3 selected.</p><div class="survey-options survey-issues">${shuffled(issues).map(([id,label]) => `<label class="survey-option"><input type="checkbox" name="issues" value="${id}"> ${escape(label)}</label>`).join('')}</div></fieldset>`;
  const method = `<details class="survey-method"><summary>Methodology</summary><p>Recruitment: self-selected website visitors. Sampling: a non-probability, self-selected reader sample. No demographic weighting is currently applied. Browser token/cookie and hashed IP checks discourage duplicate submissions; eligibility is self-reported. Five core fields are required for inclusion in the structured poll: eligibility, current choice, vote certainty, likelihood to vote, and past vote/turnout. All other questions are optional. Likely voters are eligible respondents with a turnout score of 8–10; this is a transparent subset, not a scientific model. The historical quick poll and structured survey are separate datasets. These results are not an official poll, a scientific poll, or an election forecast.</p></details>`;
  root.innerHTML = `<div id="survey-results" tabindex="-1" hidden><h2>Structured survey results</h2><p id="survey-done" role="status"></p><div class="scope-tabs" role="tablist" aria-label="Structured survey respondent group"><button type="button" class="survey-tab" data-scope="all" aria-pressed="true">All respondents</button><button type="button" class="survey-tab" data-scope="eligible" aria-pressed="false">Eligible respondents</button><button type="button" class="survey-tab" data-scope="likely" aria-pressed="false">Likely voters</button></div><p id="survey-total"></p><div id="survey-breakdowns"></div><p>Likely voters means self-reported eligible respondents with a turnout score of 8–10. This is a transparent reader-sample subset, not a scientific likely-voter model.</p></div>
    <form id="structured-form">
    <h2>Help make the survey more informative — about 60 seconds</h2><p>5 core questions are required. The remaining questions are optional and help us understand the sample.</p>
    <h3 class="survey-section-title">Core questions — required</h3>
    ${field('eligibility',richmond?'Are you eligible to vote in the Richmond municipal election?':'Are you eligible to vote in the October 24, 2026 BC provincial election?',eligibility,true)}
    ${field('choice',richmond?'If the Richmond election were held today, who would you choose for mayor?':"If the BC provincial election were held today, which party's candidate in your electoral district would you be most likely to support?",choices,true)}
    <div id="survey-lean" hidden>${field('lean',richmond?'Even if you have not decided, is there one mayoral candidate you are currently leaning toward?':'Even if you have not decided, is there one party you are currently leaning toward?',leanChoices)}</div>
    ${field('certainty','How certain are you of your current choice?',certainty,true)}
    <fieldset class="survey-field"><legend>How likely are you to vote? <span class="survey-requirement">Required</span></legend><select id="survey-turnout" required><option value="">Select a score</option><option value="0">0</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option><option value="6">6</option><option value="7">7</option><option value="8">8</option><option value="9">9</option><option value="10">10</option></select><p>0 = definitely will not vote · 10 = definitely will vote</p></fieldset>
    ${field(richmond?'pastTurnout':'pastVote',richmond?'Did you vote in the 2022 Richmond municipal election?':'In the 2024 BC provincial election, what best describes you?',past,true)}
    <h3 class="survey-section-title">Optional questions</h3><p>Optional — help us understand the sample.</p>
    ${field('secondChoice',richmond?'If your first choice were not available, who would be your second choice for mayor?':'If your first choice were not available, what would be your second choice?',secondChoices)}
    ${issueField}
    ${field('region',richmond?'Which Richmond area best describes where you live?':'Which region best describes where you live?',regions)}
    ${field('age','Your age group',ages)}${field('gender','Your gender',genders)}
    ${richmond?'':field('education','Your highest completed education',education)}
    ${richmond?'<div id="survey-turnstile"></div>':''}
    <p id="survey-error" class="poll-msg" role="alert" hidden></p><button class="poll-submit" id="survey-submit" type="submit">Submit voter survey</button></form>${method}`
  translateStatic(root);
  if (localeIndex >= 0) root.querySelector('#survey-results .scope-tabs').setAttribute('aria-label', t('Structured survey respondent group'));
  const form = root.querySelector('#structured-form');
  const error = root.querySelector('#survey-error');
  const choiceInput = () => form.querySelector('input[name="choice"]:checked')?.value;
  const checked = name => form.querySelector(`input[name="${name}"]:checked`)?.value;
  const second = () => form.querySelectorAll('input[name="secondChoice"]').forEach(input => {
    const excluded = input.value === choiceInput() || (choiceInput() === 'und' && input.value === checked('lean') && input.value !== 'und');
    input.disabled = excluded;
    if (excluded) input.checked = false;
  });
  form.querySelectorAll('input[name="choice"],input[name="lean"]').forEach(input => input.addEventListener('change', () => {
    const undecided = choiceInput() === 'und';
    root.querySelector('#survey-lean').hidden = !undecided;
    if (!undecided) form.querySelectorAll('input[name="lean"]').forEach(i => { i.checked = false; });
    second();
  }));
  const turnout = root.querySelector('#survey-turnout');
  const issueBoxes = [...form.querySelectorAll('input[name="issues"]')];
  let issueTouched = false;
  issueBoxes.forEach(box => box.addEventListener('change', () => {
    issueTouched = true;
    const count = issueBoxes.filter(x => x.checked).length;
    root.querySelector('#issue-count').textContent = count;
    issueBoxes.forEach(x => { x.disabled = !x.checked && count >= 3; });
  }));
  let survey = null;
  let activeScope = 'all';
  function rows(title, counts, options, denominator, { optional = false, denominatorKnown = true } = {}) {
    const sorted = options.map(([id,label]) => [id,label,Number(counts?.[id] || 0)]).sort((a,b) => b[2]-a[2]);
    return `<section class="survey-breakdown"><h3>${escape(t(title))}</h3>${sorted.map(([,label,n]) => {
      const stat = optional
        ? denominatorKnown ? `${denominator ? Math.round(n*1000/denominator)/10 : '—'}% · ${localeIndex < 0 ? `${n} of ${denominator} answering` : `${n} / ${denominator} ${t('respondents answered')}`}` : `${n} · ${t('historical answer denominator unavailable')}`
        : `${denominator ? Math.round(n*1000/denominator)/10 : 0}% · ${n}`;
      return `<div class="survey-row"><span>${escape(t(label))}</span><strong>${stat}</strong></div>`;
    }).join('')}</section>`;
  }
  function render() {
    const b = survey?.scopes?.[activeScope];
    if (!b) return;
    root.querySelectorAll('.survey-tab').forEach(btn => btn.setAttribute('aria-pressed', String(btn.dataset.scope === activeScope)));
    root.querySelector('#survey-total').textContent = localeIndex < 0 ? `${b.total.toLocaleString('en-CA')} structured respondent${b.total === 1 ? '' : 's'} · average turnout score ${b.total ? (b.turnoutSum/b.total).toFixed(1) : '—'}/10` : `${b.total.toLocaleString(language)}${t('份回答','份回答')} · ${t('平均投票可能性','平均投票可能性')} ${b.total ? (b.turnoutSum/b.total).toFixed(1) : '—'}/10`;
    const answered = b.answered || {};
    const answeredKnown = b.answeredKnown || {};
    root.querySelector('#survey-breakdowns').innerHTML =
      rows('Initial choice',b.initialChoice,choices,b.total) +
      rows('Decided + leaning',b.decidedLeaning,choices,b.total) +
      rows('Vote certainty',b.certainty,certainty,b.total) +
      rows(richmond?'Past municipal turnout':'Past vote',b[richmond?'pastTurnout':'pastVote'],past,b.total) +
      rows('Top issues',b.issues,issues,Number(answered.issues || 0),{optional:true,denominatorKnown:answeredKnown.issues !== false}) +
      rows('Second choice',b.secondChoice,secondChoices,Number(answered.secondChoice || 0),{optional:true}) +
      rows('Age',b.age,ages,Number(answered.age || 0),{optional:true}) +
      rows('Gender',b.gender,genders,Number(answered.gender || 0),{optional:true}) +
      rows('Region',b.region,regions,Number(answered.region || 0),{optional:true}) +
      (richmond?'':rows('Education',b.education,education,Number(answered.education || 0),{optional:true}));
  }
  root.querySelectorAll('.survey-tab').forEach(btn => btn.addEventListener('click', () => { activeScope=btn.dataset.scope;render(); }));
  function showSurveyResults(message) {
    form.hidden = true;
    const results = root.querySelector('#survey-results');
    results.hidden = false;
    root.querySelector('#survey-done').textContent = t(message);
    render();
    requestAnimationFrame(() => {
      results.focus({ preventScroll: true });
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
  let turnstileToken = '';
  let widgetId = null;
  function mountTurnstile() {
    if (!richmond || widgetId !== null || !window.turnstile) return;
    widgetId = window.turnstile.render(root.querySelector('#survey-turnstile'), {
      sitekey: '0x4AAAAAAFEAteWT79UPR7fb', language: 'auto', callback: token => { turnstileToken = token; },
      'expired-callback': () => { turnstileToken = ''; }, 'error-callback': () => { turnstileToken = ''; }
    });
  }
  let loaded = false;
  async function reveal() {
    if (quickResults.hidden || loaded) return;
    loaded = true; root.hidden = false;
    try {
      const response = await fetch((richmond?'/api/mayor-poll':'/api/party-poll')+'?survey=1',{cache:'no-store'});
      const data = await response.json();
      if (data.ok) {
        survey = data.survey;
        root.querySelector('#survey-results').hidden = false;
        render();
        if (data.alreadySubmitted) { showSurveyResults('You have already submitted this structured survey.'); return; }
      }
    } catch (_) { /* The form remains available when a temporary GET fails. */ }
    if (richmond) {
      mountTurnstile();
      const timer = setInterval(() => { mountTurnstile(); if (widgetId !== null) clearInterval(timer); }, 250);
      setTimeout(() => clearInterval(timer), 10000);
    }
  }
  new MutationObserver(reveal).observe(quickResults,{attributes:true,attributeFilter:['hidden']});
  reveal();
  form.addEventListener('submit', async e => {
    e.preventDefault(); error.hidden = true;
    const answer = { eligibility: checked('eligibility') || null, choice: choiceInput() || null,
      lean: choiceInput()==='und' ? (checked('lean') || null) : null,
      certainty: checked('certainty') || null, turnout: turnout.value === '' ? null : Number(turnout.value),
      secondChoice: checked('secondChoice') || null,
      issues: issueTouched ? issueBoxes.filter(x=>x.checked).map(x=>x.value) : null, region: checked('region') || null,
      age: checked('age') || null, gender: checked('gender') || null,
      language: richmond ? language : undefined };
    answer[richmond?'pastTurnout':'pastVote'] = checked(richmond?'pastTurnout':'pastVote') || null;
    if (!richmond) answer.education = checked('education') || null;
    if (richmond) answer.turnstileToken = turnstileToken;
    if (!answer.eligibility || !answer.choice || !answer.certainty || !answer.pastVote && !answer.pastTurnout || !Number.isInteger(answer.turnout) || answer.turnout < 0 || answer.turnout > 10 || (richmond && !turnstileToken)) {
      error.textContent = richmond && !turnstileToken ? t('Please complete the verification check.') : t('Please answer the five core questions.');
      error.hidden = false; error.scrollIntoView({block:'nearest'}); return;
    }
    const button = root.querySelector('#survey-submit');
    button.disabled = true; button.textContent = t('Submitting…');
    try {
      const response = await fetch((richmond?'/api/mayor-poll':'/api/party-poll')+'?survey=1',{
        method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(answer)
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw Error(data.error || 'submission_failed');
      survey = data.survey;
      showSurveyResults(data.alreadySubmitted?'You have already submitted this structured survey.':'Thank you — your structured survey response was recorded.');
    } catch (err) {
      error.textContent = t(err.message === 'turnstile_failed' ? 'Verification expired. Please complete the check again.' : 'Survey submission failed. Please review your answers and try again.');
      error.hidden = false;
      if (richmond && widgetId !== null && window.turnstile) { window.turnstile.reset(widgetId); turnstileToken = ''; }
    } finally { button.disabled = false; button.textContent = t('Submit voter survey'); }
  });
})();
