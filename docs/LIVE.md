# Running Edge against the live Odds API

Everything in Edge runs offline against bundled sample data by default. To use
**real** odds, scores and historical data, you need (1) network access to The
Odds API and (2) an API key. This doc captures the setup so it doesn't have to
be re-derived each time.

## TL;DR

```bash
pip install -e .
export ODDS_API_KEY=your_key          # keep this private — never commit it
edge sports --counts                  # confirms the key + lists in-season games
edge scan --live --sport baseball_mlb # real +EV board for an in-season sport
```

## 1. Get and protect an API key

- Sign up at <https://the-odds-api.com> to get a key (free tier available).
- The key is a secret. **Never** paste it into a chat, commit it, or hard-code
  it. Provide it via the `ODDS_API_KEY` environment variable.
- If a key is ever exposed, rotate it in your Odds API dashboard and update the
  environment variable / secret.

## 2. Network access

The live endpoints all live on the host `https://api.the-odds-api.com`.

### Local machine

No special setup — outbound HTTPS works, so the commands above just work.

### Claude Code on the web (remote/cloud sessions)

Cloud sessions run in a sandbox whose **outbound network is restricted to an
allowlist** chosen when the environment is created. By default
`api.the-odds-api.com` is **not** allowlisted, so every live call fails with:

```
Failed to ...: HTTP Error 403: Forbidden    # proxy: "Host not in allowlist"
```

This is a network-policy block, **not** a bad key — a new key will not fix it.
To enable live calls from a cloud session:

1. In the environment's settings, set a network policy that permits
   `api.the-odds-api.com` (custom allowlist, or a broader egress policy).
2. Add the key as an environment **secret** named `ODDS_API_KEY` (so it reaches
   the session without appearing in any conversation).
3. **Start a new session** — network policy and env vars are applied when the
   environment is created, so an existing session can't pick them up.

See the network-policy docs:
<https://code.claude.com/docs/en/claude-code-on-the-web>

## 3. Commands that use the live API

| Command | Endpoint | Quota cost |
|---|---|---|
| `edge sports [--counts]` | `/sports`, `/events` | free |
| `edge scan --live [--sport S] [--market M]` | `/odds` | markets × regions, per sport |
| `edge train --live [--sport S] [--days N]` | `/scores` | 2 with `--days`, else 1, per sport |
| `edge build-dataset ...` | historical `/odds` + `/scores` | 10 × markets × regions per snapshot (paid plan) |

Every live command prints remaining quota afterwards, e.g.:

```
(quota remaining: 487, last call cost: 3, used: 13)
```

Notes:
- It is currently **June 2026** for this project's data; NFL/NBA/NHL are
  off-season and return no events. Use `baseball_mlb` to see live lines.
- `/scores` only returns the **last 3 days** of completed games, so
  `build-dataset` snapshot dates must be recent.
- The historical-odds endpoint requires a **paid** Odds API plan.

## 4. Verifying the integration

```bash
ODDS_API_KEY=your_key pytest tests/test_live.py -v
```

The live smoke test is skipped automatically when `ODDS_API_KEY` is unset, so
the default test run stays offline and deterministic.
