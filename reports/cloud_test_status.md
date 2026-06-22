# Cloud Test Status

- Status: BLOCKED
- Stage: `remote_acceptance`
- Local ready: `True`
- Cloud config ready: `True`

## Missing
- None

## Connection Check Details

Missing from connection check:
- `GITHUB_TOKEN or GH_TOKEN`

Token handling: Token is read from environment or prompt only; do not save it to files.

Root commands:

```powershell
.\check-cloud-config-from-root.cmd
.\setup-cloud-test-from-root.cmd
.\run-cloud-test-from-root.cmd -CreateRepo
```

## Next Commands

Use real values only. Do not copy placeholder text such as `owner/repository`, `yourname/...`, or Chinese example words.

From the organized project root:

```powershell
.\check-cloud-config-from-root.cmd
.\setup-cloud-test-from-root.cmd
.\run-cloud-test-from-root.cmd -CreateRepo
```

From the source project directory:

Token setup details: `docs/github-token-setup.md`

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup-cloud-test.ps1
```

or:

```powershell
$env:GITHUB_TOKEN = "ghp_real_token_here"
$env:GITHUB_REPOSITORY = "real-github-login/international-trade-ai"
.\run-cloud-test.cmd -CreateRepo
```

## Completion Evidence Required
- reports/cloud_run.json has ok: true and stage: accepted
- reports/cloud_acceptance_remote.json has ok: true and conclusion: success
- GitHub Actions run URL is present
- remote reports/cloud_acceptance.md says PASS
