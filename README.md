# FACO 9000

**Fusion Array Control & Orchestration** — a small full-stack demo used to bootstrap
and validate the Cloud Agent development environment for this repository.

It's a single-page reactor control panel (React + Vite) backed by a small Express API.
Adjusting the power output changes the derived core temperature and appends entries to a
live activity log, exercising a real end-to-end request/response flow.

## Stack

- **Frontend:** React 18 + TypeScript, built with Vite. Dev server on port `5173`.
- **Backend:** Express + TypeScript, run with `tsx`. API on port `3001`.
- **Tests:** Vitest (API tests via `supertest`, component tests via Testing Library + jsdom).
- **Lint:** ESLint 9 (flat config) with `typescript-eslint`.

The Vite dev server proxies `/api/*` to the Express server, so the browser only talks to
one origin during development.

## Getting started

```bash
npm install       # install dependencies
npm run dev       # run API (3001) + web (5173) together
```

Then open http://localhost:5173.

## Common commands

| Command          | What it does                                        |
| ---------------- | --------------------------------------------------- |
| `npm run dev`    | Run the API and web dev servers concurrently.       |
| `npm run dev:api`| Run only the Express API (with watch).              |
| `npm run dev:web`| Run only the Vite dev server.                       |
| `npm run build`  | Type-check and build the production frontend bundle.|
| `npm test`       | Run the Vitest suite once.                          |
| `npm run lint`   | Lint the project with ESLint.                       |
| `npm start`      | Run the API server (production entry).              |

## API

| Method & path               | Description                                      |
| --------------------------- | ------------------------------------------------ |
| `GET  /api/health`          | Liveness probe.                                  |
| `GET  /api/reactor`         | Current reactor state (status, output, temp, log)|
| `POST /api/reactor/output`  | Set target output in MW (`{ "outputMw": 500 }`). |
| `POST /api/reactor/scram`   | Emergency stop — return to standby.              |

## Cloud Agent environment

The environment is defined in [`.cursor/environment.json`](.cursor/environment.json):
`install` runs `npm ci`, and two terminals bring up the `api` and `web` dev servers on
each boot.
