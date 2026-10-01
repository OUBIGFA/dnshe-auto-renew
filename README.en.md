<div align="center">
  <h1>DNSHE Free Domain Auto Renew</h1>
  <p>Automatically checks your DNSHE domains weekly and renews them for free before expiration</p>
  <p><a href="README.md">简体中文</a> | English</p>
  <p>
    <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-3776AB">
    <img alt="Platform" src="https://img.shields.io/badge/platform-GitHub%20Actions-2088FF">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-111827">
    <img alt="Schedule" src="https://img.shields.io/badge/schedule-Weekly-22c55e">
  </p>
</div>

> Deploy in 3 minutes, then your DNSHE free domains will be checked and renewed automatically every week.

## 3-Minute Deployment

### Step 0: Get DNSHE API Credentials

Open:

- https://my.dnshe.com

Prepare these two values:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

### Step 1: Import as a Private Repository via GitHub Importer

1. Log in to GitHub and open <https://github.com/new/import>
2. Fill in the following:

| Field | Value |
| --- | --- |
| `Your old repository's clone URL` | `https://github.com/OUBIGFA/dnshe-auto-renew` |
| `Owner` | Your GitHub account |
| `Repository name` | Your repo name, e.g. `my-dnshe-auto-renew` |
| `Privacy` | Select `Private` |

3. Click `Begin import` and wait for it to finish (usually tens of seconds to a few minutes)
4. Once imported, GitHub creates a private repository owned by you. All subsequent Secrets, Variables, and workflow configuration are done on this repo's page.

### Step 2: Add GitHub Secrets and Variables

Go to:

- `Settings -> Secrets and variables -> Actions`

Add these Secrets:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

Add this Variable:

- `DNSHE_DOMAINS`

### Step 3: Configure Domains

`DNSHE_DOMAINS` takes one domain per line:

```text
abc88.cc.cd
12366.cc.cd
```

### Step 4: Run the Workflow Manually

Open the `Actions` tab and manually run `DNSHE Auto Renew`.

The first run checks the domains. After that, the workflow runs automatically every week.

## Domain Management

### Format

One domain per line. Add a line for a new domain, remove a line to delete:

```text
abc88.cc.cd
12366.cc.cd
444.cc.cd
```

### Adding Domains

Simply append new domains to `DNSHE_DOMAINS`. The next workflow run detects new domains automatically and reads the expiration date returned by the API. No manual registration date or expiration date needed.

### Why No Manual Expiration Date

- The expiration date is read directly from the API's `expires_at`
- After a successful renewal the API returns a new `expires_at`, so the date rolls forward automatically
- Only when the API returns no expiration date does it fall back to `created_at + 365` days and write the state file

## Renewal Rules

Default behavior:

- The official renewal window opens `180` days before expiration; this tool acts at `175` days
- Checked once per week
- Renewal is only requested when a domain enters the renewal window

## Regenerating API Credentials

If you regenerate your DNSHE API credentials, simply update the GitHub Secrets:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

## Syncing with Upstream

`.github/workflows/sync-upstream.yml` aligns this repository with the upstream template every Monday: files upstream adds or changes are pulled in, and files upstream deletes are removed here too.

The one exception is `PROTECTED_PATHS`, which by default contains only `state/domains-state.json` — this repository's own record of expiration dates. Overwriting it would cause repeated renewals.

Two things to note:

- Any other file you keep in this repository is deleted on the next sync. Add it to `PROTECTED_PATHS` (space separated) to keep it.
- Secrets and Variables (`DNSHE_API_KEY`, `DNSHE_DOMAINS`, ...) live in the repository settings, not in the file tree, so the sync never touches them.

### Workflow files are not synced by default

The built-in `GITHUB_TOKEN` cannot create or modify files under `.github/workflows/` — a platform restriction that neither the `permissions` block nor the repository settings can lift. Without `SYNC_TOKEN` the sync skips that directory instead of failing the whole run.

To sync workflows automatically, create a fine-grained PAT (`Contents: Read and write` + `Workflows: Read and write`) and store it as the repository secret `SYNC_TOKEN`.

## Changing the Schedule

The default is every Monday at 04:23 UTC. Edit the `cron` field in `.github/workflows/dnshe-auto-renew.yml`, and add that file to `PROTECTED_PATHS` in `sync-upstream.yml`, otherwise the next sync reverts it.

## File Reference

- `scripts/dnshe_auto_renew.py` — Renewal script
- `.github/workflows/dnshe-auto-renew.yml` — Weekly GitHub Actions workflow
- `.github/workflows/sync-upstream.yml` — Syncs the whole repository from the upstream template every week
- `state/domains-state.json` — State file holding the last resolved expiration date, used as a fallback when the API returns none

## Official Links

- [DNSHE Dashboard](https://my.dnshe.com)
- [DNSHE API Manual](https://my.dnshe.com/knowledgebase/1/Free-Domain-Name-Service-API-User-Manual.html)

## License

MIT License
