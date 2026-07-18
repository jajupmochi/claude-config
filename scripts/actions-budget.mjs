#!/usr/bin/env node
// actions-budget.mjs — offline budget check for GitHub Actions workflows.
//
// Point it at a repo. It reads .github/workflows/*.yml on disk and reports:
//   - which workflows fire on a PR update, on a merge to the default branch, and on a schedule
//   - how many jobs each of those fans out to (matrix expanded, reusable workflows followed)
//   - the billable minutes floor and estimate, converted to Linux-equivalent minutes and USD
//   - findings: workflows with no paths filter, no concurrency group, a non-Linux runner
//     (the multiplier trap), a push/pull_request double-run, no timeout, self-hosted runners
//
// Everything above works with no network access. `--live` additionally asks an authenticated
// `gh` for repository visibility and billing usage, and degrades with a stated reason when
// `gh` is missing, unauthenticated, or the endpoint returns nothing usable.
//
//   node scripts/actions-budget.mjs [repo-path] [options]
//
//   --plan <free|pro|team|enterprise>   included-minutes allowance to compare against (default free)
//   --visibility <public|private>       state it offline instead of probing with --live (default private)
//   --minutes-per-job <n>               duration assumption for the ESTIMATE column
//   --pushes-per-day <n>                PR-branch pushes per day, for the monthly projection
//   --merges-per-day <n>                merges to the default branch per day
//   --branch <name>                     default branch name (default: main)
//   --rates <path>                      alternative rate card
//   --json                              machine-readable output
//   --live                              read-only `gh` probe for visibility + billing usage
//   --fail-on <none|warn|error>         exit non-zero at or above this level (default none)
//
// Exit codes: 0 ok, 1 threshold hit via --fail-on, 2 usage/IO error.

import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve, basename } from "node:path";
import { spawnSync } from "node:child_process";

// ---------------------------------------------------------------------------
// 1. YAML subset parser
//
// Workflow files use a small, regular slice of YAML. Rather than take a
// dependency we parse that slice directly. Anything outside it (anchors,
// aliases, multi-document files, explicit tags) is NOT silently guessed at —
// it is pushed onto `warnings`, surfaced in the report, and counted as an
// `error` finding, because a wrong parse means wrong numbers.
// ---------------------------------------------------------------------------

class YamlSubsetError extends Error {}

const BLOCK_SCALAR = /^[|>][-+]?[0-9]*$/;

// Strip a trailing `# comment`, respecting quotes. A `#` only starts a comment
// at the start of the value or after whitespace.
export function stripComment(s) {
  let quote = null;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (quote) {
      if (c === "\\" && quote === '"') { i++; continue; }
      if (c === quote) quote = null;
      continue;
    }
    if (c === '"' || c === "'") { quote = c; continue; }
    if (c === "#" && (i === 0 || /\s/.test(s[i - 1]))) return s.slice(0, i);
  }
  return s;
}

// Split `key: value`. The key ends at the first `: ` (or a line-final `:`)
// that is outside quotes and outside a `${{ ... }}` expression.
export function splitKey(content) {
  let quote = null, expr = 0;
  for (let i = 0; i < content.length; i++) {
    const c = content[i];
    if (quote) {
      if (c === "\\" && quote === '"') { i++; continue; }
      if (c === quote) quote = null;
      continue;
    }
    if (c === '"' || c === "'") { quote = c; continue; }
    if (c === "$" && content.startsWith("${{", i)) { expr++; i += 2; continue; }
    if (c === "}" && content.startsWith("}}", i) && expr > 0) { expr--; i += 1; continue; }
    if (expr > 0) continue;
    if (c === ":" && (i === content.length - 1 || content[i + 1] === " " || content[i + 1] === "\t")) {
      return { key: unquote(content.slice(0, i).trim()), rest: content.slice(i + 1).trim() };
    }
  }
  return null;
}

function unquote(s) {
  if (s.length >= 2 && ((s[0] === '"' && s.endsWith('"')) || (s[0] === "'" && s.endsWith("'")))) {
    const body = s.slice(1, -1);
    return s[0] === '"' ? body.replace(/\\(.)/g, "$1") : body.replace(/''/g, "'");
  }
  return s;
}

function scalar(raw) {
  const s = raw.trim();
  if (s === "" || s === "~" || s === "null" || s === "Null" || s === "NULL") return null;
  if (s === "true" || s === "True" || s === "TRUE") return true;
  if (s === "false" || s === "False" || s === "FALSE") return false;
  if (/^-?\d+$/.test(s)) return parseInt(s, 10);
  if (/^-?\d*\.\d+$/.test(s)) return parseFloat(s);
  return unquote(s);
}

// Split a flow collection body on top-level commas, respecting quotes and nesting.
function splitFlow(body) {
  const parts = [];
  let depth = 0, quote = null, cur = "";
  for (let i = 0; i < body.length; i++) {
    const c = body[i];
    if (quote) {
      cur += c;
      if (c === "\\" && quote === '"') { cur += body[++i] ?? ""; continue; }
      if (c === quote) quote = null;
      continue;
    }
    if (c === '"' || c === "'") { quote = c; cur += c; continue; }
    if (c === "[" || c === "{") depth++;
    if (c === "]" || c === "}") depth--;
    if (c === "," && depth === 0) { parts.push(cur); cur = ""; continue; }
    cur += c;
  }
  if (cur.trim() !== "") parts.push(cur);
  return parts.map((p) => p.trim()).filter((p) => p !== "");
}

function parseFlow(s, warnings, where) {
  const t = s.trim();
  if (t.startsWith("[") && t.endsWith("]")) {
    return splitFlow(t.slice(1, -1)).map((p) => parseFlow(p, warnings, where));
  }
  if (t.startsWith("{") && t.endsWith("}")) {
    const obj = {};
    for (const p of splitFlow(t.slice(1, -1))) {
      const kv = splitKey(p) || (p.includes(":") ? { key: p.slice(0, p.indexOf(":")).trim(), rest: p.slice(p.indexOf(":") + 1).trim() } : null);
      if (!kv) { warnings.push(`${where}: cannot parse flow mapping entry \`${p}\``); continue; }
      obj[unquote(kv.key)] = parseFlow(kv.rest, warnings, where);
    }
    return obj;
  }
  if (/^[&*]\S/.test(t)) {
    warnings.push(`${where}: YAML anchors/aliases are outside the supported subset (\`${t}\`)`);
    return t;
  }
  return scalar(t);
}

function balanced(s) {
  let depth = 0, quote = null;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (quote) { if (c === "\\" && quote === '"') i++; else if (c === quote) quote = null; continue; }
    if (c === '"' || c === "'") { quote = c; continue; }
    if (c === "[" || c === "{") depth++;
    if (c === "]" || c === "}") depth--;
  }
  return depth <= 0;
}

function tokenize(text, warnings) {
  const out = [];
  const raw = text.split(/\r?\n/);
  for (let i = 0; i < raw.length; i++) {
    const line = raw[i].replace(/\t/g, "  ");
    if (/^\s*$/.test(line)) continue;
    if (/^\s*#/.test(line)) continue;
    if (/^---\s*$/.test(line)) { if (out.length) warnings.push(`line ${i + 1}: multi-document YAML is outside the supported subset`); continue; }
    if (/^\.\.\.\s*$/.test(line)) continue;
    const indent = line.length - line.replace(/^ +/, "").length;
    out.push({ indent, content: stripComment(line.slice(indent)).trimEnd(), line: i + 1 });
  }
  return out;
}

function parseNode(lines, i, indent, warnings) {
  if (i >= lines.length) return [null, i];
  return lines[i].content.startsWith("-") && (lines[i].content === "-" || lines[i].content[1] === " ")
    ? parseSequence(lines, i, indent, warnings)
    : parseMapping(lines, i, indent, warnings);
}

function parseMapping(lines, i, indent, warnings) {
  const obj = {};
  while (i < lines.length && lines[i].indent >= indent) {
    if (lines[i].indent > indent) throw new YamlSubsetError(`line ${lines[i].line}: unexpected indent`);
    const c = lines[i].content;
    if (c === "-" || c.startsWith("- ")) break; // a sequence sibling ends this mapping
    const kv = splitKey(c);
    if (!kv) throw new YamlSubsetError(`line ${lines[i].line}: expected \`key: value\`, got \`${c}\``);
    const { key, rest } = kv;
    if (rest === "") {
      const j = i + 1;
      if (j < lines.length && lines[j].indent > indent) {
        const [val, ni] = parseNode(lines, j, lines[j].indent, warnings);
        obj[key] = val; i = ni;
      } else if (j < lines.length && lines[j].indent === indent && (lines[j].content === "-" || lines[j].content.startsWith("- "))) {
        const [val, ni] = parseSequence(lines, j, indent, warnings);
        obj[key] = val; i = ni;
      } else { obj[key] = null; i = j; }
    } else if (BLOCK_SCALAR.test(rest)) {
      let j = i + 1;
      const buf = [];
      while (j < lines.length && lines[j].indent > indent) { buf.push(lines[j].content); j++; }
      obj[key] = buf.join("\n"); i = j;
    } else {
      let value = rest, j = i;
      while (!balanced(value) && j + 1 < lines.length) { j++; value += " " + lines[j].content; }
      obj[key] = parseFlow(value, warnings, `line ${lines[i].line}`);
      i = j + 1;
    }
  }
  return [obj, i];
}

function parseSequence(lines, i, indent, warnings) {
  const arr = [];
  while (i < lines.length && lines[i].indent === indent && (lines[i].content === "-" || lines[i].content.startsWith("- "))) {
    const c = lines[i].content;
    const after = c === "-" ? "" : c.slice(1).replace(/^ +/, "");
    const itemIndent = indent + (c.length - after.length);
    if (after === "") {
      const j = i + 1;
      if (j < lines.length && lines[j].indent > indent) {
        const [val, ni] = parseNode(lines, j, lines[j].indent, warnings);
        arr.push(val); i = ni;
      } else { arr.push(null); i = j; }
    } else if (splitKey(after)) {
      // Compact mapping (`- uses: x`) whose continuation lines sit at itemIndent.
      const saved = lines[i];
      lines[i] = { indent: itemIndent, content: after, line: saved.line };
      const [val, ni] = parseMapping(lines, i, itemIndent, warnings);
      lines[i] = saved;
      arr.push(val); i = ni;
    } else {
      let value = after, j = i;
      while (!balanced(value) && j + 1 < lines.length) { j++; value += " " + lines[j].content; }
      arr.push(parseFlow(value, warnings, `line ${lines[i].line}`));
      i = j + 1;
    }
  }
  return [arr, i];
}

// Parse the YAML subset used by workflow files. Returns { doc, warnings }.
// Never throws for content problems; a parse failure is returned as a warning
// with doc === null so the caller reports it rather than producing silent zeros.
export function parseYamlSubset(text) {
  const warnings = [];
  try {
    const lines = tokenize(text, warnings);
    if (lines.length === 0) return { doc: {}, warnings };
    const [doc, end] = parseNode(lines, 0, lines[0].indent, warnings);
    if (end < lines.length) warnings.push(`line ${lines[end].line}: trailing content could not be parsed`);
    return { doc, warnings };
  } catch (e) {
    warnings.push(String(e.message || e));
    return { doc: null, warnings };
  }
}

// ---------------------------------------------------------------------------
// 2. Workflow model
// ---------------------------------------------------------------------------

// `on:` is a YAML 1.1 boolean in some parsers. Ours keeps the literal key, but
// accept the alternatives so a doc produced elsewhere still works.
function readTriggers(doc) {
  const on = doc?.on ?? doc?.["on"] ?? doc?.true ?? doc?.True;
  if (on == null) return {};
  if (typeof on === "string") return { [on]: {} };
  if (Array.isArray(on)) return Object.fromEntries(on.map((e) => [String(e), {}]));
  if (typeof on === "object") return Object.fromEntries(Object.entries(on).map(([k, v]) => [k, v ?? {}]));
  return {};
}

// GitHub branch/tag filter globbing: `*` (no slash), `**` (any), `?`, `!` negation.
// Character classes and `+` are approximated, which is noted in the report.
export function globToRegExp(pattern) {
  let out = "^";
  for (let i = 0; i < pattern.length; i++) {
    const c = pattern[i];
    if (c === "*") {
      if (pattern[i + 1] === "*") { out += ".*"; i++; } else out += "[^/]*";
    } else if (c === "?") out += "[^/]";
    else if ("\\^$.|+()[]{}".includes(c)) out += "\\" + c;
    else out += c;
  }
  return new RegExp(out + "$");
}

export function branchMatches(spec, branch) {
  const inc = spec?.branches, exc = spec?.["branches-ignore"];
  if (Array.isArray(exc) && exc.length) return !exc.some((p) => globToRegExp(String(p)).test(branch));
  if (!Array.isArray(inc) || inc.length === 0) return true;
  let included = false;
  for (const p of inc) {
    const s = String(p);
    const neg = s.startsWith("!");
    if (globToRegExp(neg ? s.slice(1) : s).test(branch)) included = !neg;
  }
  return included;
}

export function expandMatrix(strategy, cap) {
  const warnings = [];
  const matrix = strategy?.matrix;
  if (matrix == null) return { combos: [{}], warnings };
  if (typeof matrix === "string") return { combos: [{}], warnings: [`matrix is an expression (\`${matrix}\`); counted as 1 job`] };
  const keys = Object.keys(matrix).filter((k) => k !== "include" && k !== "exclude");
  let combos = [{}];
  for (const k of keys) {
    const v = matrix[k];
    if (!Array.isArray(v)) { warnings.push(`matrix.${k} is not a list (expression?); counted as 1 value`); continue; }
    const next = [];
    for (const c of combos) for (const val of v) next.push({ ...c, [k]: val });
    combos = next;
    if (combos.length > cap) { warnings.push(`matrix expansion exceeded cap ${cap}; truncated`); combos = combos.slice(0, cap); break; }
  }
  const excl = Array.isArray(matrix.exclude) ? matrix.exclude : [];
  if (excl.length) {
    combos = combos.filter((c) => !excl.some((e) => Object.entries(e).every(([k, v]) => String(c[k]) === String(v))));
  }
  const incl = Array.isArray(matrix.include) ? matrix.include : [];
  if (incl.length) {
    if (keys.length === 0) return { combos: incl.map((x) => ({ ...x })), warnings };
    for (const inc of incl) {
      const overlap = Object.keys(inc).filter((k) => keys.includes(k));
      let extended = false;
      if (overlap.length) {
        for (const c of combos) {
          if (overlap.every((k) => String(c[k]) === String(inc[k]))) { Object.assign(c, inc); extended = true; }
        }
      }
      if (!extended) combos.push({ ...inc });
    }
  }
  return { combos, warnings };
}

// Resolve `${{ matrix.x }}` and `${{ inputs.x }}` against the values we know.
// Anything still unresolved stays literal, and the caller reports it as unknown
// rather than assuming Linux.
function substituteMatrix(value, combo, inputs = {}) {
  if (typeof value !== "string") return value;
  const out = value
    .replace(/\$\{\{\s*matrix\.([A-Za-z0-9_.-]+)\s*\}\}/g, (m, k) => (k in combo ? String(combo[k]) : m))
    .replace(/\$\{\{\s*inputs\.([A-Za-z0-9_.-]+)\s*\}\}/g, (m, k) => (k in inputs && inputs[k] != null ? String(inputs[k]) : m));
  // `${{ inputs.runner || 'ubuntu-latest' }}` still has a knowable answer once the
  // left side turned out to be unresolvable: the literal fallback is what runs.
  return out.replace(/\$\{\{\s*[A-Za-z0-9_.-]+\s*\|\|\s*'([^']*)'\s*\}\}/g, (m, lit) => lit);
}

// Three-valued evaluation of a job-level `if:` for one event. A job whose `if`
// is false never gets a runner and costs nothing, which is how the label gate and
// the platform gate in templates/actions-frugal-ci earn their keep. Anything this
// cannot decide returns null and is counted at full cost, so the report is an
// upper bound rather than an optimistic one.
export function evalIf(expr, ctx) {
  if (expr == null) return true;
  let s = String(expr).trim();
  s = s.replace(/^\$\{\{/, "").replace(/\}\}$/, "").trim();
  if (s === "") return true;

  const splitTop = (str, op) => {
    const parts = [];
    let depth = 0, quote = null, last = 0;
    for (let i = 0; i < str.length; i++) {
      const c = str[i];
      if (quote) { if (c === quote) quote = null; continue; }
      if (c === '"' || c === "'") { quote = c; continue; }
      if (c === "(") depth++;
      if (c === ")") depth--;
      if (depth === 0 && str.startsWith(op, i)) { parts.push(str.slice(last, i)); i += op.length - 1; last = i + 1; }
    }
    parts.push(str.slice(last));
    return parts.map((p) => p.trim());
  };

  const or = splitTop(s, "||");
  if (or.length > 1) {
    const vals = or.map((p) => evalIf(p, ctx));
    if (vals.some((v) => v === true)) return true;
    if (vals.every((v) => v === false)) return false;
    return null;
  }
  const and = splitTop(s, "&&");
  if (and.length > 1) {
    const vals = and.map((p) => evalIf(p, ctx));
    if (vals.some((v) => v === false)) return false;
    if (vals.every((v) => v === true)) return true;
    return null;
  }
  if (s.startsWith("(") && s.endsWith(")") && balanced(s.slice(1, -1))) return evalIf(s.slice(1, -1), ctx);
  if (/^always\(\s*\)$/.test(s)) return true;
  if (/^success\(\s*\)$/.test(s)) return true;

  const cmp = s.match(/^github\.event_name\s*(==|!=)\s*['"]([A-Za-z_]+)['"]$/);
  if (cmp) {
    const eq = cmp[1] === "==", want = cmp[2];
    if (ctx.event_name == null) return null;
    return eq ? ctx.event_name === want : ctx.event_name !== want;
  }
  return null; // labels, needs outputs, draft state, anything else: undecidable here
}

const evalIfAll = (exprs, ctx) => {
  const vals = (exprs ?? []).map((e) => evalIf(e, ctx));
  if (vals.some((v) => v === false)) return false;
  if (vals.every((v) => v === true)) return true;
  return null;
};

// Map a runs-on value to a billing class using the rate card's classification table.
export function classifyRunner(runsOn, combo, rates, inputs = {}) {
  const rc = rates.runnerClassification;
  let labels;
  if (runsOn == null) return { cls: "unknown", label: "(none)", resolved: false };
  if (Array.isArray(runsOn)) labels = runsOn.map((l) => substituteMatrix(l, combo, inputs));
  else if (typeof runsOn === "object") labels = [].concat(runsOn.labels ?? [], runsOn.group ?? []).map((l) => substituteMatrix(l, combo, inputs));
  else labels = [substituteMatrix(runsOn, combo, inputs)];
  labels = labels.filter((l) => l != null).map((l) => String(l));
  if (labels.length === 0) return { cls: "unknown", label: "(none)", resolved: false };
  const lower = labels.map((l) => l.toLowerCase().trim());
  if (lower.includes(rc.selfHostedLabel)) return { cls: "self-hosted", label: labels.join(","), resolved: true };
  for (const l of lower) {
    if (l.includes("${{")) continue;
    let base = null, bestLen = 0;
    for (const [prefix, cls] of Object.entries(rc.basePrefixes)) {
      if (prefix.startsWith("_")) continue;
      if (l.startsWith(prefix) && prefix.length > bestLen) { base = cls; bestLen = prefix.length; }
    }
    if (!base) continue;
    for (const [suffix, variant] of Object.entries(rc.variantSuffixes)) {
      if (suffix.startsWith("_")) continue;
      if (l.endsWith(suffix)) {
        const combined = rc.variantClass[`${base}+${variant}`];
        if (combined) return { cls: combined, label: labels.join(","), resolved: true };
      }
    }
    return { cls: base, label: labels.join(","), resolved: true };
  }
  return { cls: "unknown", label: labels.join(","), resolved: false };
}

function readWorkflowFile(file, rates) {
  const text = readFileSync(file, "utf8");
  const { doc, warnings } = parseYamlSubset(text);
  return { file, name: doc?.name ?? basename(file), doc, warnings, parsed: doc !== null };
}

// Read the `default:` values a reusable workflow declares for its workflow_call inputs.
function callInputDefaults(child) {
  const decl = readTriggers(child.doc ?? {}).workflow_call?.inputs;
  const out = {};
  if (decl && typeof decl === "object") {
    for (const [k, v] of Object.entries(decl)) if (v && typeof v === "object" && "default" in v) out[k] = v.default;
  }
  return out;
}

// Expand a workflow into concrete job instances. A job can carry BOTH a matrix and
// a `uses:`, so the matrix is expanded first and the reusable workflow is followed
// once per combination, with the caller's `with:` values resolved against it.
export function expandJobs(wf, index, rates, seen = new Set(), depth = 0, inherited = { inputs: {}, ifExprs: [] }) {
  const out = [], warnings = [];
  const jobs = wf.doc?.jobs;
  if (!jobs || typeof jobs !== "object") return { jobs: out, warnings };

  for (const [id, job] of Object.entries(jobs)) {
    if (!job || typeof job !== "object") continue;
    const ownIf = typeof job.if === "string" ? job.if : null;
    const ifExprs = [...inherited.ifExprs, ...(ownIf ? [ownIf] : [])];
    const { combos, warnings: mw } = expandMatrix(job.strategy, rates.thresholds.matrixExpansionCap);
    for (const w of mw) warnings.push(`${wf.name}/${id}: ${w}`);
    if (combos.length >= rates.thresholds.largeMatrixJobs) warnings.push(`${wf.name}/${id}: matrix fans out to ${combos.length} jobs`);
    const suffix = (combo) => (combos.length > 1 ? ` (${Object.entries(combo).map(([k, v]) => `${k}=${v}`).join(", ")})` : "");

    for (const combo of combos) {
      if (typeof job.uses === "string") {
        const target = job.uses.trim();
        const base = { id: id + suffix(combo), timeout: job["timeout-minutes"] ?? null, ifExprs, source: wf.file };
        if (!target.startsWith("./")) {
          warnings.push(`${wf.name}/${id}: remote reusable workflow \`${target}\`; job count unknown, counted as 1`);
          out.push({ ...base, cls: "unknown", label: "(remote reusable)", resolved: false });
          continue;
        }
        const key = target.replace(/^\.\//, "");
        const child = index.get(key);
        if (!child || !child.parsed) {
          warnings.push(`${wf.name}/${id}: reusable workflow \`${target}\` ${child ? "failed to parse" : "not found on disk"}; counted as 1 job`);
          out.push({ ...base, cls: "unknown", label: "(reusable, unresolved)", resolved: false });
          continue;
        }
        if (seen.has(key) || depth > 5) {
          warnings.push(`${wf.name}/${id}: reusable workflow recursion guard hit at \`${target}\``);
          continue;
        }
        const childInputs = { ...callInputDefaults(child) };
        for (const [k, v] of Object.entries(job.with ?? {})) childInputs[k] = substituteMatrix(v, combo, inherited.inputs);
        const sub = expandJobs(child, index, rates, new Set([...seen, key]), depth + 1, { inputs: childInputs, ifExprs });
        warnings.push(...sub.warnings);
        for (const j of sub.jobs) out.push({ ...j, id: `${id}${suffix(combo)} -> ${j.id}` });
        continue;
      }

      const { cls, label, resolved } = classifyRunner(job["runs-on"], combo, rates, inherited.inputs);
      if (!resolved) warnings.push(`${wf.name}/${id}: could not classify runs-on \`${label}\`; priced at the 'unknown' rate`);
      out.push({ id: id + suffix(combo), cls, label, resolved, timeout: job["timeout-minutes"] ?? null, ifExprs, source: wf.file });
    }
  }
  return { jobs: out, warnings };
}

// ---------------------------------------------------------------------------
// 3. Cron frequency (exact for the 5-field subset GitHub accepts)
// ---------------------------------------------------------------------------

const DOW_NAMES = { sun: 0, mon: 1, tue: 2, wed: 3, thu: 4, fri: 5, sat: 6 };
const MON_NAMES = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

function fieldValue(tok, names) {
  const t = tok.trim().toLowerCase();
  if (names && t in names) return names[t];
  return /^\d+$/.test(t) ? parseInt(t, 10) : null;
}

export function expandCronField(field, min, max, names) {
  const set = new Set();
  for (const part of String(field).split(",")) {
    const [range, stepStr] = part.split("/");
    const step = stepStr === undefined ? 1 : parseInt(stepStr, 10);
    if (!Number.isFinite(step) || step < 1) return null;
    let lo, hi;
    if (range === "*" || range === "?") { lo = min; hi = max; }
    else if (range.includes("-")) {
      const [a, b] = range.split("-");
      lo = fieldValue(a, names); hi = fieldValue(b, names);
    } else { lo = hi = fieldValue(range, names); }
    if (lo === null || hi === null || lo < min || hi > max || lo > hi) return null;
    for (let v = lo; v <= hi; v += step) set.add(v);
  }
  return set;
}

// Runs per 30 days for a 5-field UTC cron. Returns null when the expression is
// outside the supported subset, so the caller can say so instead of guessing.
export function cronRunsPerMonth(expr, daysPerMonth = 30) {
  const f = String(expr).trim().split(/\s+/);
  if (f.length !== 5) return null;
  const minutes = expandCronField(f[0], 0, 59, null);
  const hours = expandCronField(f[1], 0, 23, null);
  const doms = expandCronField(f[2], 1, 31, null);
  const months = expandCronField(f[3], 1, 12, MON_NAMES);
  const dows = expandCronField(f[4], 0, 7, DOW_NAMES);
  if (!minutes || !hours || !doms || !months || !dows) return null;
  const dowSet = new Set([...dows].map((d) => (d === 7 ? 0 : d)));
  const domRestricted = f[2] !== "*" && f[2] !== "?";
  const dowRestricted = f[4] !== "*" && f[4] !== "?";
  const perDay = minutes.size * hours.size;
  let days = 0;
  const YEAR = 2027; // a non-leap reference year
  for (let m = 1; m <= 12; m++) {
    if (!months.has(m)) continue;
    const dim = new Date(Date.UTC(YEAR, m, 0)).getUTCDate();
    for (let d = 1; d <= dim; d++) {
      const dow = new Date(Date.UTC(YEAR, m - 1, d)).getUTCDay();
      const okDom = doms.has(d), okDow = dowSet.has(dow);
      const ok = domRestricted && dowRestricted ? okDom || okDow : domRestricted ? okDom : dowRestricted ? okDow : true;
      if (ok) days++;
    }
  }
  return (days * perDay * daysPerMonth) / 365;
}

// ---------------------------------------------------------------------------
// 4. Cost model
// ---------------------------------------------------------------------------

function rateFor(cls, rates) {
  const r = rates.billing.usdPerMinute[cls];
  return r === undefined ? rates.billing.usdPerMinute.unknown : r;
}

export function costJobs(jobs, rates, minutesPerJob) {
  const roundUp = rates.billing.roundUpPerJobMinutes;
  const baseline = rateFor(rates.billing.baselineClass, rates);
  const byClass = {};
  let floorUsd = 0, estUsd = 0, floorMin = 0, estMin = 0;
  for (const j of jobs) {
    const rate = rateFor(j.cls, rates);
    const fMin = roundUp;
    const eMin = Math.max(roundUp, Math.ceil(minutesPerJob));
    floorMin += fMin; estMin += eMin;
    floorUsd += fMin * rate; estUsd += eMin * rate;
    byClass[j.cls] = (byClass[j.cls] ?? 0) + 1;
  }
  return {
    jobs: jobs.length,
    byClass,
    wallMinutesFloor: floorMin,
    wallMinutesEstimate: estMin,
    usdFloor: round4(floorUsd),
    usdEstimate: round4(estUsd),
    linuxEqMinutesFloor: round2(floorUsd / baseline),
    linuxEqMinutesEstimate: round2(estUsd / baseline),
  };
}

const round2 = (n) => Math.round(n * 100) / 100;
const round4 = (n) => Math.round(n * 10000) / 10000;

// ---------------------------------------------------------------------------
// 5. Analysis
// ---------------------------------------------------------------------------

export function findWorkflowFiles(repoPath) {
  const dir = join(repoPath, ".github", "workflows");
  if (!existsSync(dir) || !statSync(dir).isDirectory()) return [];
  return readdirSync(dir)
    .filter((f) => /\.ya?ml$/i.test(f))
    .sort()
    .map((f) => join(dir, f));
}

export function analyzeRepo(repoPath, opts = {}) {
  const rates = opts.rates ?? loadRates();
  const branch = opts.branch ?? "main";
  const featureBranch = opts.featureBranch ?? "topic/example";
  const minutesPerJob = opts.minutesPerJob ?? rates.assumptions.defaultMinutesPerJob;
  const files = findWorkflowFiles(repoPath);
  const workflows = files.map((f) => readWorkflowFile(f, rates));
  const index = new Map(workflows.map((w) => [w.file.slice(resolve(repoPath).length + 1).replace(/\\/g, "/"), w]));

  const findings = [];
  const add = (level, id, message, where) => findings.push({ level, id, message, where });

  const perWorkflow = [];
  for (const wf of workflows) {
    const rel = wf.file.slice(resolve(repoPath).length + 1).replace(/\\/g, "/");
    if (!wf.parsed) {
      add("error", "parse-failed", `could not parse: ${wf.warnings.join("; ")}`, rel);
      perWorkflow.push({ file: rel, name: wf.name, parsed: false, triggers: {}, jobs: [], warnings: wf.warnings });
      continue;
    }
    for (const w of wf.warnings) add("error", "parse-warning", w, rel);
    const triggers = readTriggers(wf.doc);
    // Analysed standalone, a reusable workflow has no caller, so its own declared
    // workflow_call input defaults are what its jobs would actually see.
    const { jobs, warnings } = expandJobs(wf, index, rates, new Set(), 0, { inputs: callInputDefaults(wf), ifExprs: [] });
    for (const w of warnings) {
      add(w.includes("could not classify") || w.includes("not found on disk") ? "warn" : "info", "expansion", w, rel);
    }

    const mpj = rates.assumptions.perWorkflowMinutesPerJob?.[rel] ?? minutesPerJob;
    const isPrTriggered = "pull_request" in triggers || "pull_request_target" in triggers;
    const isPushTriggered = "push" in triggers;

    // --- findings -------------------------------------------------------
    const conc = wf.doc.concurrency;
    const cancel = conc && typeof conc === "object" ? conc["cancel-in-progress"] : undefined;
    // `cancel-in-progress` may be an expression, which is the documented way to
    // cancel superseded pull request runs while leaving default-branch runs alone.
    // https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
    const concCancels = cancel === true || (typeof cancel === "string" && cancel.includes("${{"));
    if ((isPrTriggered || isPushTriggered) && !concCancels) {
      add("warn", "missing-concurrency", conc
        ? "has a concurrency group but cancel-in-progress is neither true nor an expression, so superseded runs keep burning minutes"
        : "no top-level concurrency group, so a rapid second push runs the whole workflow twice", rel);
    }
    const unfilteredEvents = ["push", "pull_request"].filter((ev) => {
      const spec = triggers[ev];
      if (spec === undefined) return false;
      return !(spec && typeof spec === "object" && (spec.paths || spec["paths-ignore"]));
    });
    if (unfilteredEvents.length) {
      const verb = unfilteredEvents.length > 1 ? "have" : "has";
      add("info", "missing-paths-filter", `on.${unfilteredEvents.join(" and on.")} ${verb} no paths / paths-ignore filter, so a docs-only change runs the whole workflow. If this workflow is a required check, gate the jobs with an \`if:\` instead of a paths filter, because a workflow skipped by a paths filter leaves its check Pending and blocks the merge (https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)`, rel);
    }
    const pushSpec = triggers.push;
    const pushUnfiltered = pushSpec != null && !(typeof pushSpec === "object" && (pushSpec.branches || pushSpec["branches-ignore"]));
    if (pushUnfiltered && isPrTriggered) {
      add("warn", "push-pr-double-run", "on.push has no branch filter and on.pull_request is also set, so every push to a PR branch runs this workflow twice", rel);
    }
    // Aggregate per-job findings so a wide matrix does not bury the report.
    const premium = {};
    for (const j of jobs) {
      if (j.cls !== "linux" && j.cls !== "self-hosted" && j.cls !== "unknown") {
        (premium[j.cls] ??= { n: 0, labels: new Set() });
        premium[j.cls].n++; premium[j.cls].labels.add(j.label);
      }
    }
    for (const [cls, info] of Object.entries(premium)) {
      const ratio = round2(rateFor(cls, rates) / rateFor(rates.billing.baselineClass, rates));
      add("warn", "non-linux-runner", `${info.n} job(s) on ${[...info.labels].join(", ")} (${cls}) draw down the allowance ${ratio}x faster than Linux. Moving them to Linux saves ${round2(((ratio - 1) / ratio) * 100)}% of their cost`, rel);
    }
    const selfHosted = jobs.filter((j) => j.cls === "self-hosted");
    if (selfHosted.length) {
      add("warn", "self-hosted-runner", `${selfHosted.length} job(s) target a self-hosted runner. Those consume no included minutes today, but GitHub recommends self-hosted runners only for private repositories, because a fork pull request can run attacker code on the runner (https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners)`, rel);
    }
    const noTimeout = jobs.filter((j) => j.timeout == null);
    if (noTimeout.length) {
      add("info", "missing-timeout", `${noTimeout.length} of ${jobs.length} job(s) set no timeout-minutes, so a hung job can bill up to the 6 hour ceiling`, rel);
    }
    if (jobs.length >= rates.thresholds.manyJobsPerEvent) {
      add("info", "job-roundup-tax", `${jobs.length} jobs per run. GitHub rounds every job up to a whole minute, so this run bills at least ${jobs.length} minutes even if each job takes seconds`, rel);
    }

    // --- schedule -------------------------------------------------------
    let scheduleRuns = 0;
    const scheduledJobs = jobs.filter((j) => evalIfAll(j.ifExprs, { event_name: "schedule" }) !== false);
    const sched = triggers.schedule;
    if (Array.isArray(sched)) {
      for (const s of sched) {
        const expr = s?.cron;
        if (!expr) { add("warn", "schedule-unparsed", "schedule entry has no cron expression", rel); continue; }
        const runs = cronRunsPerMonth(expr, rates.assumptions.daysPerMonth);
        if (runs === null) { add("warn", "schedule-unparsed", `cron \`${expr}\` is outside the supported subset; excluded from the projection`, rel); continue; }
        scheduleRuns += runs;
      }
      if (scheduleRuns > 0) {
        const c = costJobs(scheduledJobs, rates, mpj);
        add("info", "schedule-cost", `scheduled ~${round2(scheduleRuns)} runs/month at ~${c.linuxEqMinutesEstimate} Linux-equivalent min/run = ~${round2(scheduleRuns * c.linuxEqMinutesEstimate)} min/month`, rel);
      }
    }

    perWorkflow.push({
      file: rel, name: wf.name, parsed: true, triggers: Object.keys(triggers), jobs, minutesPerJob: mpj,
      runsOn: {
        pull_request: isPrTriggered,
        pushDefault: isPushTriggered && branchMatches(typeof pushSpec === "object" ? pushSpec : {}, branch),
        pushFeature: isPushTriggered && branchMatches(typeof pushSpec === "object" ? pushSpec : {}, featureBranch),
      },
      scheduleRunsPerMonth: scheduleRuns,
      scheduledJobs,
      cost: costJobs(jobs, rates, mpj),
    });
  }

  // --- scenarios ---------------------------------------------------------
  // A job whose `if:` is decidably false for this event never gets a runner, so it
  // is dropped. A job we cannot decide is counted at full cost and reported under
  // `conditionalJobs`, which keeps every figure an upper bound.
  const costOf = (sel, eventName) => {
    const rows = perWorkflow.filter((w) => w.parsed && sel(w));
    const merged = { jobs: 0, conditionalJobs: 0, byClass: {}, wallMinutesFloor: 0, wallMinutesEstimate: 0, usdFloor: 0, usdEstimate: 0 };
    for (const r of rows) {
      const live = r.jobs.filter((j) => evalIfAll(j.ifExprs, { event_name: eventName }) !== false);
      merged.conditionalJobs += live.filter((j) => evalIfAll(j.ifExprs, { event_name: eventName }) === null).length;
      const c = costJobs(live, rates, r.minutesPerJob);
      merged.jobs += c.jobs; merged.wallMinutesFloor += c.wallMinutesFloor; merged.wallMinutesEstimate += c.wallMinutesEstimate;
      merged.usdFloor += c.usdFloor; merged.usdEstimate += c.usdEstimate;
      for (const [k, v] of Object.entries(c.byClass)) merged.byClass[k] = (merged.byClass[k] ?? 0) + v;
    }
    const baseline = rateFor(rates.billing.baselineClass, rates);
    return {
      ...merged,
      usdFloor: round4(merged.usdFloor), usdEstimate: round4(merged.usdEstimate),
      linuxEqMinutesFloor: round2(merged.usdFloor / baseline),
      linuxEqMinutesEstimate: round2(merged.usdEstimate / baseline),
      workflows: rows.map((r) => r.file),
    };
  };

  // A push to a PR branch is one git operation that can start TWO runs of the same
  // workflow: one for `pull_request` and one for `push`. So pr_update ADDS the two
  // scenarios rather than taking the union of the workflows, which would hide the
  // double run that `push-pr-double-run` reports.
  const baselineRate = rateFor(rates.billing.baselineClass, rates);
  const sumCosts = (a, b) => {
    const byClass = { ...a.byClass };
    for (const [k, v] of Object.entries(b.byClass)) byClass[k] = (byClass[k] ?? 0) + v;
    const usdFloor = a.usdFloor + b.usdFloor, usdEstimate = a.usdEstimate + b.usdEstimate;
    return {
      jobs: a.jobs + b.jobs, conditionalJobs: a.conditionalJobs + b.conditionalJobs, byClass,
      wallMinutesFloor: a.wallMinutesFloor + b.wallMinutesFloor,
      wallMinutesEstimate: a.wallMinutesEstimate + b.wallMinutesEstimate,
      usdFloor: round4(usdFloor), usdEstimate: round4(usdEstimate),
      linuxEqMinutesFloor: round2(usdFloor / baselineRate),
      linuxEqMinutesEstimate: round2(usdEstimate / baselineRate),
      workflows: [...new Set([...a.workflows, ...b.workflows])],
    };
  };
  const scenarios = {
    pull_request: costOf((w) => w.runsOn.pull_request, "pull_request"),
    push_feature: costOf((w) => w.runsOn.pushFeature, "push"),
    push_default: costOf((w) => w.runsOn.pushDefault, "push"),
  };
  scenarios.pr_update = sumCosts(scenarios.pull_request, scenarios.push_feature);

  const scheduleMonthly = perWorkflow
    .filter((w) => w.parsed && w.scheduleRunsPerMonth > 0)
    .reduce((acc, w) => acc + w.scheduleRunsPerMonth * costJobs(w.scheduledJobs, rates, w.minutesPerJob).linuxEqMinutesEstimate, 0);

  const pushesPerDay = opts.pushesPerDay ?? rates.assumptions.pushesPerDay;
  const mergesPerDay = opts.mergesPerDay ?? rates.assumptions.mergesPerDay;
  const days = rates.assumptions.daysPerMonth;
  const monthly = {
    pushesPerDay, mergesPerDay, daysPerMonth: days,
    floor: round2(days * (pushesPerDay * scenarios.pr_update.linuxEqMinutesFloor + mergesPerDay * scenarios.push_default.linuxEqMinutesFloor) + scheduleMonthly),
    estimate: round2(days * (pushesPerDay * scenarios.pr_update.linuxEqMinutesEstimate + mergesPerDay * scenarios.push_default.linuxEqMinutesEstimate) + scheduleMonthly),
    scheduleMinutes: round2(scheduleMonthly),
  };

  const plan = rates.plans[opts.plan ?? "free"] ?? rates.plans.free;
  monthly.planIncludedMinutes = plan.includedMinutes;
  monthly.percentOfPlanEstimate = round2((monthly.estimate / plan.includedMinutes) * 100);
  monthly.percentOfPlanFloor = round2((monthly.floor / plan.includedMinutes) * 100);
  if (monthly.estimate > plan.includedMinutes) {
    add("warn", "over-allowance", `projected ${monthly.estimate} Linux-equivalent min/month exceeds the ${opts.plan ?? "free"} plan allowance of ${plan.includedMinutes}`, "(repo)");
  }
  if (files.length === 0) add("info", "no-workflows", "no .github/workflows/*.yml found; nothing runs remotely", "(repo)");
  else if (opts.visibility === "public") add("info", "visibility-public", "you stated this repository is public: standard GitHub-hosted runners are free there, so every minute figure below is informational rather than billed", "(repo)");
  else if (opts.visibility === "private") add("info", "visibility-private", "you stated this repository is private, so these minutes draw down the allowance of the account that OWNS the repo — a personal repo bills the personal account, an org repo bills the org at the org's plan", "(repo)");
  else add("info", "visibility-unknown", "these figures assume a private repository. Standard GitHub-hosted runners are free in public repositories, where the numbers are informational only. Pass --visibility, or run with --live to have gh report the actual value", "(repo)");

  return {
    repo: resolve(repoPath), branch, featureBranch, plan: opts.plan ?? "free",
    minutesPerJob, ratesAsOf: rates._asOf,
    workflows: perWorkflow, scenarios, monthly, findings,
    totals: { workflowFiles: files.length, jobsPerPrUpdate: scenarios.pr_update.jobs },
  };
}

// ---------------------------------------------------------------------------
// 6. Live probe (read-only, opt-in)
// ---------------------------------------------------------------------------

function ghJson(args, cwd) {
  const r = spawnSync("gh", args, { cwd, encoding: "utf8", timeout: 20000 });
  if (r.error) return { ok: false, reason: r.error.code === "ENOENT" ? "gh is not installed" : String(r.error.message) };
  if (r.status !== 0) return { ok: false, reason: (r.stderr || "").trim().split("\n")[0] || `gh exited ${r.status}` };
  try { return { ok: true, data: JSON.parse(r.stdout) }; }
  catch { return { ok: true, data: r.stdout.trim() }; }
}

export function liveProbe(repoPath) {
  const out = { attempted: true, visibility: null, nameWithOwner: null, billing: null, notes: [] };
  const auth = spawnSync("gh", ["auth", "status"], { cwd: repoPath, encoding: "utf8", timeout: 20000 });
  if (auth.error) { out.notes.push(auth.error.code === "ENOENT" ? "gh is not installed; live quota skipped" : `gh failed: ${auth.error.message}`); return out; }
  if (auth.status !== 0) { out.notes.push("gh is not authenticated (`gh auth login`); live quota skipped"); return out; }

  const repo = ghJson(["repo", "view", "--json", "visibility,nameWithOwner"], repoPath);
  if (repo.ok && repo.data && typeof repo.data === "object") {
    out.visibility = String(repo.data.visibility || "").toLowerCase();
    out.nameWithOwner = repo.data.nameWithOwner ?? null;
    if (out.visibility === "public") out.notes.push("repository is public: standard GitHub-hosted runners are free, so the minute figures below are informational rather than billed");
  } else out.notes.push(`repository visibility unavailable: ${repo.reason ?? "unexpected response"}`);

  const who = ghJson(["api", "user", "--jq", ".login"], repoPath);
  if (!who.ok) { out.notes.push(`could not resolve the authenticated user: ${who.reason}`); return out; }
  const login = String(who.data).trim();

  const usage = ghJson(["api", `/users/${login}/settings/billing/usage`], repoPath);
  if (usage.ok) out.billing = usage.data;
  else {
    out.notes.push(`billing usage endpoint unavailable: ${usage.reason}`);
    out.notes.push("GitHub retired the per-product Actions billing endpoint; the enhanced billing usage API is scoped to organization and enterprise administrators, so a personal account often has no readable live quota. See https://docs.github.com/en/rest/billing/usage");
  }
  return out;
}

// ---------------------------------------------------------------------------
// 7. Rendering
// ---------------------------------------------------------------------------

const LEVEL_ORDER = { info: 0, warn: 1, error: 2 };

function pad(s, n) { s = String(s); return s.length >= n ? s : s + " ".repeat(n - s.length); }
function padL(s, n) { s = String(s); return s.length >= n ? s : " ".repeat(n - s.length) + s; }
function clip(s, n) { s = String(s); return s.length <= n ? s : s.slice(0, n - 1) + "…"; }

function renderText(a) {
  const L = [];
  L.push(`GitHub Actions budget — ${a.repo}`);
  L.push(`  plan=${a.plan}  default-branch=${a.branch}  minutes-per-job=${a.minutesPerJob}  rates as of ${a.ratesAsOf}`);
  L.push("");

  if (a.totals.workflowFiles === 0) {
    L.push("  No workflow files found under .github/workflows/.");
  } else {
    L.push("Workflows (under .github/workflows/)");
    L.push(`  ${pad("file", 28)}${pad("triggers", 42)}${padL("jobs", 5)}${padL("floor", 9)}${padL("est", 9)}`);
    for (const w of a.workflows) {
      const short = clip(w.file.replace(/^\.github\/workflows\//, ""), 27);
      if (!w.parsed) { L.push(`  ${pad(short, 28)}(parse failed)`); continue; }
      L.push(`  ${pad(short, 28)}${pad(clip(w.triggers.join(",") || "(none)", 41), 42)}${padL(w.cost.jobs, 5)}${padL(w.cost.linuxEqMinutesFloor, 9)}${padL(w.cost.linuxEqMinutesEstimate, 9)}`);
    }
    L.push("");
    L.push("What runs, in Linux-equivalent minutes (floor = every job billed the 1 minute round-up; est = minutes-per-job assumption)");
    const rows = [
      ["one PR update (pull_request + branch push)", a.scenarios.pr_update],
      ["  of which pull_request", a.scenarios.pull_request],
      ["  of which push to the PR branch", a.scenarios.push_feature],
      [`push/merge to ${a.branch}`, a.scenarios.push_default],
    ];
    L.push(`  ${pad("scenario", 46)}${padL("jobs", 5)}${padL("floor", 9)}${padL("est", 9)}${padL("est USD", 10)}`);
    for (const [label, s] of rows) {
      L.push(`  ${pad(label, 46)}${padL(s.jobs, 5)}${padL(s.linuxEqMinutesFloor, 9)}${padL(s.linuxEqMinutesEstimate, 9)}${padL("$" + s.usdEstimate.toFixed(3), 10)}`);
    }
    const cls = a.scenarios.pr_update.byClass;
    if (Object.keys(cls).length) L.push(`  runner mix per PR update: ${Object.entries(cls).map(([k, v]) => `${k}=${v}`).join("  ")}`);
    L.push("");
    L.push("Monthly projection");
    L.push(`  ${a.monthly.pushesPerDay} PR-branch pushes/day + ${a.monthly.mergesPerDay} merges/day over ${a.monthly.daysPerMonth} days, plus schedules`);
    L.push(`  floor    ${padL(a.monthly.floor, 9)} min  (${a.monthly.percentOfPlanFloor}% of the ${a.plan} allowance of ${a.monthly.planIncludedMinutes})`);
    L.push(`  estimate ${padL(a.monthly.estimate, 9)} min  (${a.monthly.percentOfPlanEstimate}% of the ${a.plan} allowance of ${a.monthly.planIncludedMinutes})`);
    if (a.monthly.scheduleMinutes > 0) L.push(`  of which scheduled runs: ${a.monthly.scheduleMinutes} min/month`);
  }

  L.push("");
  const order = ["error", "warn", "info"];
  const counts = { error: 0, warn: 0, info: 0 };
  for (const f of a.findings) counts[f.level]++;
  L.push(`Findings — ${counts.error} error, ${counts.warn} warn, ${counts.info} info`);
  for (const lvl of order) {
    const group = a.findings.filter((f) => f.level === lvl);
    for (const f of group) L.push(`  [${lvl}] ${pad(f.id, 22)} ${f.where}: ${f.message}`);
  }

  if (a.live) {
    L.push("");
    L.push("Live probe");
    if (a.live.nameWithOwner) L.push(`  repository: ${a.live.nameWithOwner} (${a.live.visibility})`);
    for (const n of a.live.notes) L.push(`  - ${n}`);
    if (a.live.billing) L.push(`  billing usage payload received (${JSON.stringify(a.live.billing).length} bytes)`);
  }
  return L.join("\n");
}

// ---------------------------------------------------------------------------
// 8. CLI
// ---------------------------------------------------------------------------

export function loadRates(path) {
  const p = path ?? join(dirname(fileURLToPath(import.meta.url)), "actions-budget.rates.json");
  return JSON.parse(readFileSync(p, "utf8"));
}

function parseArgs(argv) {
  const o = { positional: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) { o.positional.push(a); continue; }
    const key = a.slice(2);
    const takesValue = ["plan", "visibility", "minutes-per-job", "pushes-per-day", "merges-per-day", "branch", "rates", "fail-on"];
    if (takesValue.includes(key)) { o[key] = argv[++i]; continue; }
    o[key] = true;
  }
  return o;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || args.h) {
    process.stdout.write(readFileSync(fileURLToPath(import.meta.url), "utf8").split("\n").filter((l) => l.startsWith("//")).map((l) => l.replace(/^\/\/ ?/, "")).join("\n") + "\n");
    return;
  }
  const repoPath = resolve(args.positional[0] ?? process.cwd());
  if (!existsSync(repoPath)) { console.error(`no such path: ${repoPath}`); process.exit(2); }

  const num = (v, name) => {
    if (v === undefined) return undefined;
    const n = Number(v);
    if (!Number.isFinite(n) || n < 0) { console.error(`--${name} must be a non-negative number, got \`${v}\``); process.exit(2); }
    return n;
  };
  const plan = args.plan ?? "free";
  let rates;
  try { rates = loadRates(args.rates); }
  catch (e) { console.error(`cannot read rate card: ${e.message}`); process.exit(2); }
  if (!rates.plans[plan]) { console.error(`unknown --plan \`${plan}\` (known: ${Object.keys(rates.plans).join(", ")})`); process.exit(2); }
  const visibility = args.visibility;
  if (visibility !== undefined && !["public", "private"].includes(visibility)) {
    console.error(`unknown --visibility \`${visibility}\` (known: public, private)`); process.exit(2);
  }

  let analysis;
  try {
    analysis = analyzeRepo(repoPath, {
      rates, plan, visibility,
      branch: args.branch,
      minutesPerJob: num(args["minutes-per-job"], "minutes-per-job"),
      pushesPerDay: num(args["pushes-per-day"], "pushes-per-day"),
      mergesPerDay: num(args["merges-per-day"], "merges-per-day"),
    });
  } catch (e) { console.error(`analysis failed: ${e.message}`); process.exit(2); }

  if (args.live) analysis.live = liveProbe(repoPath);

  process.stdout.write((args.json ? JSON.stringify(analysis, null, 2) : renderText(analysis)) + "\n");

  const failOn = args["fail-on"] ?? "none";
  if (failOn !== "none") {
    if (!(failOn in LEVEL_ORDER)) { console.error(`unknown --fail-on \`${failOn}\` (none|warn|error)`); process.exit(2); }
    const worst = analysis.findings.reduce((m, f) => Math.max(m, LEVEL_ORDER[f.level]), -1);
    if (worst >= LEVEL_ORDER[failOn]) process.exit(1);
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) main();
