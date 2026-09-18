---
name: release-ops
description: Bosun's post-merge lane for a Fly.io micro-SaaS fleet — deploying merged work, generating release notes and changelogs, rolling back a bad release, and triaging production incidents across many small apps run by one person. Use whenever a PR has merged and needs deploying, when production is broken or erroring, when someone asks to roll back, or when release notes or an incident note are needed.
---

# Release Ops (Bosun)

A merge that never deployed is an open incident, not a finished job.

## Deploy
Gated behind a GitHub Environment with required reviewers — a compromised workflow must not be able to self-approve production credentials.

```bash
export FLEET_JOB_ID=deploy-<product>-<date> FLEET_BOT=bosun
fly deploy --app <product> --strategy rolling
```
Record the previous image tag **before** you deploy. A rollback you have to go find is a rollback you do at 3am.
```bash
fly releases --app <product> --json | head -40   # capture last-good image
```
Meter the build and machine time:
```bash
python3 scripts/meter.py fly_build <builder_seconds>
python3 scripts/meter.py fly_machine <machine_seconds> --meta size=shared_cpu_1x_256mb
```

## Rollback
```bash
fly deploy --app <product> --image <last-good-tag>
```
Rollback first, diagnose second. Never debug forward on a live revenue product.

## Release notes
Generated from conventional-commit PR titles since the last tag. Run it as a Batch job — it is not interactive and batch is half price.

## Incident triage (one person, many apps)
| Severity | Definition | Response |
|---|---|---|
| **S1** | Paying users cannot use the product, or data is at risk | Roll back now, then notify Affan |
| **S2** | Degraded, workaround exists | Fix within the day, file an issue |
| **S3** | Cosmetic, single-user, or noisy log | Issue only, no interrupt |

First action on any S1/S2: pull the stack trace from error monitoring, write the incident note, roll back if S1. Do **not** start editing product code — that is Factory Floor's job, via an issue.

```md
# Incident: <product> · <date>
Severity: S<n>
Symptom: <what a user saw>
Trigger: <release/commit if known>
Action taken: <rollback / patch / monitor>
Follow-up issue: #<N>
Cost of this incident: <RUN LEDGER>
```

## Fleet hygiene
Scale-to-zero on low-traffic products — but remember a stopped machine still bills its attached volume. Flag any product whose idle cost exceeds its MRR; that is Purser's kill-list input.

## Forbidden
Merging. Editing product logic. Deploying without the Environment gate. Silently retrying a failed deploy more than once.
