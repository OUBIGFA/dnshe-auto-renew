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

## 3-Minute Deployment

### Step 0: Get API Credentials

Grab these two values from <https://my.dnshe.com>:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

### Step 1: Import as Your Own Private Repository

1. Log in to GitHub and open <https://github.com/new/import>
2. Fill in the following:

| Field | Value |
| --- | --- |
| `Your old repository's clone URL` | `https://github.com/OUBIGFA/dnshe-auto-renew` |
| `Owner` | Your GitHub account |
| `Repository name` | Your repo name, e.g. `my-dnshe-auto-renew` |
| `Privacy` | Select `Private` |

3. Click `Begin import` and wait for it to finish
4. Configure Secrets, Variables and workflows on this new repository

### Step 2: Add Secrets and a Variable

Go to `Settings -> Secrets and variables -> Actions`.

Secrets (two):

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

Variable (one):

- `DNSHE_DOMAINS`

### Step 3: Configure Domains

`DNSHE_DOMAINS` takes one domain per line:

```text
abc88.cc.cd
12366.cc.cd
```

### Step 4: Run the Workflow Manually

Open the `Actions` tab and manually run `DNSHE Auto Renew`.

After that, the workflow runs automatically every week.

## Domain Management

One domain per line. Add a line for a new domain, remove a line to delete. New domains take effect on the next run.

```text
abc88.cc.cd
12366.cc.cd
444.cc.cd
```

## Renewal Rules

- The official renewal window opens **180** days before expiration; this tool acts at **175** days
- Checked once per week, and renewal is only requested when a domain enters the renewal window

## Regenerating API Credentials

If you regenerate your DNSHE API credentials, update these two Secrets:

- `DNSHE_API_KEY`
- `DNSHE_API_SECRET`

## Syncing with Upstream

`.github/workflows/sync-upstream.yml` aligns this repository with the upstream template every Monday: files upstream adds or changes are pulled in, and files upstream deletes are removed here too.

`state/domains-state.json` is excluded from the sync — it is this repository's own record of expiration dates.

Two things to note:

- Any other file you keep in this repository is deleted on the next sync. Add it to `PROTECTED_PATHS` (space separated) to keep it.
- Secrets and Variables live in the repository settings, not in the file tree, so the sync never touches them.

`.github/workflows/` is not synced by default. To sync it too, create a fine-grained PAT (`Contents: Read and write` + `Workflows: Read and write`) and store it as the repository secret `SYNC_TOKEN`.

## Changing the Schedule

The default is every Monday at **04:23 UTC**. Edit the `cron` field in `.github/workflows/dnshe-auto-renew.yml`. If you have configured `SYNC_TOKEN`, also add that file to `PROTECTED_PATHS` in `sync-upstream.yml`, otherwise the next sync reverts it.

## File Reference

- `scripts/dnshe_auto_renew.py` — Renewal script
- `.github/workflows/dnshe-auto-renew.yml` — Weekly renewal workflow
- `.github/workflows/sync-upstream.yml` — Syncs the whole repository from the upstream template every week
- `state/domains-state.json` — This repository's record of expiration dates, used as a fallback when the API returns none

## Official Links

- [DNSHE Dashboard](https://my.dnshe.com)
- [DNSHE API Manual](https://my.dnshe.com/knowledgebase/1/Free-Domain-Name-Service-API-User-Manual.html)

## License

MIT License
