---
name: workflow-fix-template
template-for: fixing CI/CD workflow failures
min-capability: medium
last-updated: 2026-07-08
template-version: 1
version-history:
  - version: 1
    date: 2026-07-08
    author: codex/deepseek-v3
    changes: Initial template extracted from claude-config workflow fix sessions
---

# workflow-fix-template

## RESEARCH phase checklist

1. List ALL workflow files: `ls .github/workflows/`
2. Check CI run logs (gh CLI or web UI): `gh run list --limit 5; gh run view <id> --log`
3. Identify EVERY failing job — do not stop at the first one
4. For each failure: read the log output, identify root cause
5. Common failure patterns:
   - Gitleaks false positives → needs .gitleaks.toml
   - npm ERR_OSSL_EVP_UNSUPPORTED → needs NODE_OPTIONS=--openssl-legacy-provider
   - Missing binary → check bin field in package.json
   - Permission denied → check chmod +x, workflow scope
   - Raw URL 404 → check file paths in raw-url job

## DESIGN phase checklist

1. For each failure: design minimal fix
2. Check if fix affects other jobs in the same workflow
3. Check if fix affects the OTHER workflow file (install-verify ↔ privacy-scan)
4. Any new config files needed? (.gitleaks.toml, .npmrc, etc.)

## PLAN template

```
1. Fix [JOB_NAME] in [WORKFLOW_FILE]: [ROOT_CAUSE] → [FIX]
2. Fix [JOB_NAME] in [WORKFLOW_FILE]: [ROOT_CAUSE] → [FIX]
3. Create [CONFIG_FILE] if needed
4. Local verify: [VERIFY_COMMANDS]
5. Commit with conventional format: fix(ci): [DESCRIPTION]
6. Push
7. Check CI status: gh run watch
```

## VERIFY phase checklist

1. Run CI locally if possible
2. Push and watch: `gh run watch`
3. ALL jobs must pass — if any fail, go back to RESEARCH
4. Check both main AND codex-adapter branches
5. Confirm no regression in previously-passing jobs

## Anti-patterns

- Fixing only the first error found → audit ALL failures
- Assuming a fix works without checking CI → always verify
- Forgetting to check the OTHER workflow file → cross-check both
- Using force push for workflow fixes → use normal push, let CI validate
