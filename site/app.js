const paths = {
  prefix: 'data/task_weighted_calibration.json',
  training: 'data/crossfold_training.json',
  evaluation: 'data/crossfold_evaluation.json',
  replication: 'data/crossfold_replication.json',
  solver: 'data/solver_v2_benchmark.json',
  v3Holdout: 'data/representation_v3_holdout.json',
  v3Public: 'data/representation_v3_public.json',
  leaderboard: 'data/leaderboard_measurement_v2.json'
};

const fmt = (x, d = 1) => Number.isFinite(Number(x)) ? `${(100 * Number(x)).toFixed(d)}%` : '—';
const pp = (x, d = 1) => Number.isFinite(Number(x)) ? `${Number(x) >= 0 ? '+' : ''}${(100 * Number(x)).toFixed(d)} pp` : '—';
const ci = (interval, formatter = fmt) => Array.isArray(interval) && interval.length === 2 ? `${formatter(interval[0])} to ${formatter(interval[1])}` : '—';
const countRate = section => section && Number.isFinite(Number(section.successes)) && Number.isFinite(Number(section.trials)) ? `${section.successes}/${section.trials} (${fmt(section.rate)})` : '—';

async function load(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  return response.json();
}

function metricCard(title, row) {
  const interval = row.task_cluster_bootstrap_ci95 || row.task_cluster_bootstrap_ci || [null, null];
  return `<article class="metric"><b>${fmt(row.task_weighted_rate)}</b><span>${title}</span><small>${row.n_tasks || '—'} tasks · 95% CI ${fmt(interval[0])}–${fmt(interval[1])}</small></article>`;
}

function kRow(payload, k) {
  return (payload?.results_by_k || []).find(row => Number(row.k) === Number(k));
}

function metric(payload, k, name) {
  const row = kRow(payload, k);
  if (!row) return null;
  if (row.metrics?.[name]) return row.metrics[name];
  if (row[name] && typeof row[name] === 'object') return row[name];
  if (Number.isFinite(Number(row[name]))) return { task_weighted_mean: Number(row[name]), ci95: null };
  return null;
}

function contrast(payload, name = 'k=2 minus k=1') {
  return (payload?.same_holdout_adjacent_k_contrasts || []).find(item => item.contrast === name) || null;
}

function renderCrossfold(training, evaluation, replication) {
  const trainK1Coverage = metric(training, 1, 'coverage');
  const trainK1Reliability = metric(training, 1, 'candidate_reliability');
  const trainK2Reliability = metric(training, 2, 'candidate_reliability');
  const evalK1Coverage = metric(evaluation, 1, 'coverage');
  const evalK1Consensus = metric(evaluation, 1, 'consensus_yield');
  const primary = contrast(training);
  const primaryCoverage = primary?.metrics?.coverage;
  const primaryConsensus = primary?.metrics?.consensus_yield;

  const cards = [
    `<div class="result-card"><strong>Training DSL coverage at k=1</strong><div class="big">${fmt(trainK1Coverage?.task_weighted_mean)}</div><span>95% task CI ${ci(trainK1Coverage?.ci95)}</span></div>`,
    `<div class="result-card"><strong>Candidate reliability: k=1 → k=2</strong><div class="big">${fmt(trainK1Reliability?.task_weighted_mean)} → ${fmt(trainK2Reliability?.task_weighted_mean)}</div><span>Conditional on candidate generation</span></div>`,
    `<div class="result-card"><strong>Same-target coverage effect</strong><div class="big">${pp(primaryCoverage?.task_weighted_delta)}</div><span>95% task CI ${ci(primaryCoverage?.ci95, pp)}</span></div>`,
    `<div class="result-card"><strong>Primary consensus-yield effect</strong><div class="big">${pp(primaryConsensus?.task_weighted_delta)}</div><span>95% task CI ${ci(primaryConsensus?.ci95, pp)} · registered negative</span></div>`,
    `<div class="result-card"><strong>One-shot evaluation coverage / yield</strong><div class="big">${fmt(evalK1Coverage?.task_weighted_mean)} / ${fmt(evalK1Consensus?.task_weighted_mean)}</div><span>Evaluation demonstrations; analysis frozen before run</span></div>`
  ];
  document.getElementById('crossfoldSummary').innerHTML = cards.join('');

  const selection = training?.ambiguous_subset_selection || {};
  const labels = {
    random: 'Random candidate',
    legacy_first_shortest: 'Legacy first-shortest',
    mdl_random_tie: 'Random minimum-complexity tie',
    mdl_vote_tie: 'Tie-aware MDL vote',
    consensus: 'All-candidate consensus',
    oracle: 'Candidate oracle'
  };
  const rows = Object.entries(labels).map(([key, label]) => {
    const item = selection.overall?.[key] || {};
    return `<tr><td>${label}</td><td>${fmt(item.task_weighted_rate)}</td><td>${ci(item.ci95)}</td></tr>`;
  }).join('');
  const mdlGain = selection.contrasts?.mdl_vote_minus_random;
  const oracleGap = selection.contrasts?.oracle_minus_mdl_vote;
  document.getElementById('selectorTable').innerHTML = `<table><thead><tr><th>Rule</th><th>Task-weighted accuracy</th><th>95% task CI</th></tr></thead><tbody>${rows}</tbody></table><p class="note">Ambiguous cells: ${selection.n_cells ?? '—'} across ${selection.n_tasks ?? '—'} tasks. MDL minus random: ${pp(mdlGain?.task_weighted_difference)} (${ci(mdlGain?.ci95, pp)}). Oracle minus MDL: ${pp(oracleGap?.task_weighted_difference)} (${ci(oracleGap?.ci95, pp)}).</p>`;

  const rep = replication?.primary_same_holdout_replication?.same_direction?.consensus_yield;
  if (rep) {
    const direction = rep.same_nonzero_direction === true ? 'replicated in direction' : rep.same_nonzero_direction === false ? 'did not replicate in direction' : 'replication inconclusive';
    document.getElementById('runDetail').textContent = `The registered same-target consensus effect was ${pp(rep.training_delta)} in training and ${pp(rep.evaluation_delta)} in the one-shot public-evaluation replication: ${direction}.`;
  }
}

function normalizeSolverMethod(method) {
  if (!method) return { pass1: null, pass2: null, correct: null, trials: null };
  const p1 = method.pass1?.rate ?? method.pass_at_1 ?? method.pass1;
  const p2 = method.pass2?.rate ?? method.pass_at_2 ?? method.pass2;
  const correct = method.pass2?.correct;
  const trials = method.pass2?.trials;
  return { pass1: Number(p1), pass2: Number(p2), correct, trials };
}

function renderSolver(payload, v3Holdout, v3Public) {
  const methods = payload?.methods || payload?.benchmarks?.public_evaluation?.methods || {};
  const legacy = normalizeSolverMethod(methods.baseline_vote_then_mdl || methods.legacy || methods.legacy_vote_mdl);
  const evidence = normalizeSolverMethod(methods.evidence_weighted || methods.evidence);
  const cards = [
    `<div class="result-card"><strong>Released baseline pass@2</strong><div class="big">${fmt(legacy.pass2)}</div><span>${legacy.correct ?? '—'} / ${legacy.trials ?? '—'} public-evaluation outputs</span></div>`,
    `<div class="result-card"><strong>Evidence-weighted v2 pass@2</strong><div class="big">${fmt(evidence.pass2)}</div><span>Delta vs baseline ${pp(evidence.pass2 - legacy.pass2)} · promotion gate not met</span></div>`
  ];

  if (v3Holdout?.output_level) {
    const baseline = v3Holdout.output_level.baseline_pass2;
    const expanded = v3Holdout.output_level.v3_pass2;
    const paired = v3Holdout.output_level.paired_v3_vs_baseline_pass2 || {};
    const verdict = paired.a_only > paired.b_only ? (paired.exact_two_sided_p < .05 ? 'clear' : 'directional') : paired.a_only === paired.b_only ? 'null' : 'failure';
    cards.push(`<div class="result-card"><strong>Registered representation-v3 training holdout</strong><div class="big">${countRate(baseline)} → ${countRate(expanded)}</div><span>${paired.a_only ?? '—'} v3-only win, p=${Number(paired.exact_two_sided_p ?? 1).toFixed(3)} · ${verdict}</span></div>`);
  }

  if (v3Public?.output_level) {
    const pass2 = v3Public.output_level.pass2;
    const paired = v3Public.paired_vs_v2_baseline || {};
    cards.push(`<div class="result-card"><strong>Frozen v3 public-evaluation pass@2</strong><div class="big">${countRate(pass2)}</div><span>${v3Public.registered_verdict || 'registered result'} · ${paired.v3_only_wins ?? '—'} v3-only wins · p=${Number(paired.exact_two_sided_p ?? 1).toFixed(3)}</span></div>`);
  } else {
    cards.push(`<div class="result-card"><strong>Frozen v3 public-evaluation run</strong><div class="big">Pending</div><span>The dashboard will update from the committed one-shot result.</span></div>`);
  }
  document.getElementById('solverSummary').innerHTML = cards.join('');
}

async function render() {
  const status = document.getElementById('status');
  const entries = await Promise.allSettled(Object.entries(paths).map(async ([key, path]) => [key, await load(path)]));
  const data = {};
  for (const entry of entries) {
    if (entry.status === 'fulfilled' && entry.value[1]?.status !== 'pending') data[entry.value[0]] = entry.value[1];
    else if (entry.status === 'rejected') console.warn(entry.reason);
  }

  if (data.prefix) {
    const rows = data.prefix.results_by_k || [];
    document.getElementById('prefixMetrics').innerHTML = [1, 2, 3].map(k => {
      const row = rows.find(item => Number(item.k) === k) || {};
      return metricCard(`${k} demonstration${k > 1 ? 's' : ''} fit`, row);
    }).join('');
  }

  if (data.training) {
    renderCrossfold(data.training, data.evaluation || {}, data.replication || {});
    document.getElementById('runTitle').textContent = 'Full-corpus registered evidence is live.';
    status.classList.add('ready');
  } else {
    document.getElementById('crossfoldSummary').innerHTML = '<div class="result-card"><strong>The registered result file is unavailable.</strong><p>See the repository evidence ledger.</p></div>';
  }

  renderSolver(data.solver || {}, data.v3Holdout || {}, data.v3Public || {});
  if (data.leaderboard?.test_output_count) {
    document.getElementById('taskCount').value = data.leaderboard.test_output_count;
    calculate();
  }

  if (!Object.keys(data).length) {
    status.classList.add('error');
    document.getElementById('runTitle').textContent = 'Evidence files are not available yet.';
  }
}

function wilson(p, n, z = 1.96) {
  const d = 1 + z * z / n;
  const c = p + z * z / (2 * n);
  const h = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n));
  return [(c - h) / d, (c + h) / d];
}
function erf(x) {
  const sign = x < 0 ? -1 : 1;
  const a1 = .254829592, a2 = -.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = .3275911;
  const t = 1 / (1 + p * Math.abs(x));
  const y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return sign * y;
}
const normalCdf = x => .5 * (1 + erf(x / Math.sqrt(2)));
function calculate() {
  const n = Math.max(10, Number(document.getElementById('taskCount').value) || 167);
  const requestedA = Math.min(1, Math.max(0, Number(document.getElementById('scoreA').value) / 100));
  const requestedB = Math.min(1, Math.max(0, Number(document.getElementById('scoreB').value) / 100));
  const successesA = Math.round(requestedA * n), successesB = Math.round(requestedB * n);
  const a = successesA / n, b = successesB / n;
  const ia = wilson(a, n), ib = wilson(b, n), pooled = (successesA + successesB) / (2 * n);
  const se = Math.sqrt(2 * pooled * (1 - pooled) / n);
  const z = se ? Math.abs(a - b) / se : 0;
  const p = 2 * (1 - normalCdf(z));
  document.getElementById('calcResult').innerHTML = `<strong>System A:</strong> ${successesA}/${n} = ${fmt(a)} (Wilson ${fmt(ia[0])}–${fmt(ia[1])})<br><strong>System B:</strong> ${successesB}/${n} = ${fmt(b)} (Wilson ${fmt(ib[0])}–${fmt(ib[1])})<br><strong>Unpaired output-level approximation:</strong> z=${z.toFixed(2)}, p=${p.toFixed(3)}.<br><small>Use paired per-output outcomes and task-clustered uncertainty for a defensible comparison.</small>`;
}

document.getElementById('calcForm').addEventListener('submit', event => { event.preventDefault(); calculate(); });
calculate();
render();
