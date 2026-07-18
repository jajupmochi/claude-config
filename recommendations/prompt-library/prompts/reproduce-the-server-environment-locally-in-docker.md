---
title: Reproduce the server environment locally in Docker
scenarios: infra,deployment,testing
tags: docker,parity,one-command,no-side-effects
source: opencode
session:
date: 2026-04-10
---

# Reproduce the server environment locally in Docker

> Use when local development has diverged from the server badly enough that you cannot trust local results, and you want the server's environment reproducible in one command.

## Original

```text
I think nothing works. Do this: write a bash script which deploys and opens all front end, back end and agent services in a Docker environment on my local machine. Reuse the current cicd / scripts if possible. This Docker should be <the same base OS as the server>, which is the same as the server. And mimic the deployment as close as the server env. Then test everything until it runs.

Tell me what you have done, what you have changed, how to run the script, the logic of the script, and how to check each url.

Do not touch any original code. Do not change anything on my local machine (only Docker).
```

## Optimized

```text
Write one bash script that brings up every service — <list them> — in Docker on my machine.

Requirements:
- Reuse the existing CI and deploy scripts wherever possible. Do not write a parallel deployment path
  that can drift from the real one.
- The image must match the server: same base OS, same versions. Mirror the server's deployment steps
  as closely as you can, and list every place you had to deviate.
- Iterate until every service actually comes up. "The script exists" is not done.

Hard constraints:
- Do not modify any application code.
- Do not change anything on my host machine. Everything lives inside Docker.

Report: what you did, what you changed, how to run it, how the script works step by step, and the URL
to check for each service with what a healthy response looks like.
```

## When to use

Use when local development has diverged from the server badly enough that you cannot trust local
results, and you want the server's environment reproducible in one command.

- Debugging something that only happens on the server.
- Onboarding, where the alternative is a page of setup instructions that goes stale.
- Before a risky deploy, to rehearse it somewhere harmless.

The two hard constraints are the point. Without them an agent will "fix" the app code or install
things on your host to make the script pass.

## When NOT to use

Skip it when the stack already runs under a maintained compose file. Extend that instead of generating
a second entry point.

Skip it when the divergence is data, not environment. Docker parity will not reproduce a bug caused by
production records.

Do not use it for services that cannot run locally at all, such as a managed database with no
container equivalent. Stub those explicitly rather than pretending the environment matches.
