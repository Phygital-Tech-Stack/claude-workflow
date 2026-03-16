# Security Skill - Deep Reference

## Scan Subcommand — Detailed Steps

### Step 1: Identify Scope

```bash
# Get changed files (staged + unstaged)
changed=$(git diff --name-only HEAD 2>/dev/null || git diff --name-only)
staged=$(git diff --name-only --cached)
all_changed=$(echo -e "$changed\n$staged" | sort -u | grep -v '^$')
```

### Step 2: Secret Pattern Scan

Scan changed files for these regex patterns:

| Pattern | Severity | Description |
|---------|----------|-------------|
| `(?i)(password\|passwd\|secret)\s*[:=]\s*['"][^'"]+['"]` | CRITICAL | Hardcoded password |
| `(?i)(api[_-]?key\|apikey)\s*[:=]\s*['"][^'"]+['"]` | CRITICAL | Hardcoded API key |
| `(?i)(access[_-]?token\|auth[_-]?token)\s*[:=]\s*['"][^'"]+['"]` | CRITICAL | Hardcoded token |
| `(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*` | WARNING | Possible bearer token |
| `[A-Za-z0-9+/]{40,}={0,2}` | INFO | Long base64 string (may be data, not secret) |

**Exclude**: Test files, mock data, comment lines, `.env.example` files.

### Step 3: Gitleaks Scan

```bash
gitleaks detect --no-git -c .gitleaks.toml --source . 2>&1
```

If gitleaks is not installed, fall back to regex scan only and note in report.

### Step 4: Debug Statement Scan

Language-specific patterns:

| Language | Pattern | Severity |
|----------|---------|----------|
| Python | `print(`, `breakpoint()`, `pdb.set_trace()` | WARNING |
| TypeScript/JS | `console.log(`, `console.debug(`, `debugger` | WARNING |
| Dart | `print(`, `debugPrint(` | WARNING |
| C# | `Console.WriteLine(`, `Debug.Log(` | WARNING |

**Exclude**: Test files, logging utilities.

### Step 5: Hardcoded URL Scan

```bash
grep -rn 'http://' <changed_files> | grep -v 'localhost' | grep -v '127.0.0.1' | grep -v 'test'
```

### Report Template

```
## Security Scan Report

| # | Finding | Severity | File:Line | Detail |
|---|---------|----------|-----------|--------|
| 1 | ... | CRITICAL/WARNING/INFO | ... | ... |

**Summary**: X CRITICAL, Y WARNING, Z INFO
**Verdict**: PASS / FAIL (FAIL if any CRITICAL)
```

## Deps Subcommand — Detailed Steps

### Severity Classification

| Condition | Severity |
|-----------|----------|
| Major version >2 behind | CRITICAL |
| Major version 1-2 behind | WARNING |
| Minor/patch behind | OK |
| Package in config but not in lock file | CRITICAL (hallucinated) |

### Report Template

```
## Dependency Freshness Report

| Package | Current | Latest | Behind | Severity |
|---------|---------|--------|--------|----------|
| ... | ... | ... | ... | ... |

**Summary**: X CRITICAL, Y WARNING, Z OK
```

## OWASP Subcommand — ASI Mapping

### OWASP ASI01-10 Coverage

| ASI# | Risk | Project Protection | Evidence |
|------|------|--------------------|----------|
| ASI01 | Prompt Injection | PreToolUse guard: prompt-injection detector | `.claude/settings.json` |
| ASI02 | Sensitive Info Disclosure | PreToolUse guard: env-secrets | `.claude/settings.json` |
| ASI03 | Supply Chain Vulnerabilities | `/security deps` + lock file verification | Lock file, `/security` skill |
| ASI04 | Output Handling | Conventional commits + code review agent | `/commit` skill |
| ASI05 | Improper Error Handling | PostToolUseFailure hook + error patterns | `.claude/hooks/post-failure.py` |
| ASI06 | Excessive Agency | `allowed-tools` in agent frontmatter | `.claude/agents/*.md` |
| ASI07 | Inter-Agent Security | SubagentStart hook + tool restrictions | WORKFLOW.md ASI07 section |
| ASI08 | Model Denial of Service | Context window efficiency + pre-compact hook | `.claude/hooks/pre-compact.py` |
| ASI09 | Metadata/Config Exploitation | Critical file guard + settings protection | Guard hooks |
| ASI10 | Unaligned Behavior | Decision log + progress files + human-in-loop | `/validate-change` Layer 5 |

### Regulatory Compliance Check

| Requirement | EU AI Act | NIST AI RMF | Evidence |
|-------------|-----------|-------------|----------|
| Human oversight | Art. 14 | MAP 1.6 | `/validate-change` Layer 5 |
| Transparency | Art. 13 | GOVERN 1.4 | `Co-Authored-By` trailer |
| Technical documentation | Art. 11 | MAP 3.1 | CLAUDE.md + WORKFLOW.md |
| Record-keeping | Art. 12 | GOVERN 1.2 | `.claude/decisions.log` + `.claude/progress/` |
| Risk management | Art. 9 | MAP 1.1 | `/score-guardrails` + guards |

### Report Template

```
## OWASP ASI Compliance Report

| ASI# | Risk | Status | Evidence |
|------|------|--------|----------|
| ASI01 | Prompt Injection | COVERED/PARTIAL/MISSING | ... |
| ... | ... | ... | ... |

**Coverage**: X/10 COVERED, Y PARTIAL, Z MISSING

### Regulatory Alignment
| Framework | Coverage |
|-----------|----------|
| EU AI Act | X/5 articles |
| NIST AI RMF | X/5 functions |
```
