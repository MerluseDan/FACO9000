import express, { type Express, type Request, type Response } from "express";

export interface LogEntry {
  id: number;
  level: "info" | "warn" | "critical";
  message: string;
  at: string;
}

export interface ReactorState {
  status: "online" | "standby";
  outputMw: number;
  coreTempC: number;
  logs: LogEntry[];
}

const MIN_OUTPUT = 0;
const MAX_OUTPUT = 1200;
const AMBIENT_TEMP = 24;

function createInitialState(): ReactorState {
  return {
    status: "standby",
    outputMw: 0,
    coreTempC: AMBIENT_TEMP,
    logs: [
      {
        id: 1,
        level: "info",
        message: "FACO 9000 control system initialized.",
        at: new Date().toISOString(),
      },
    ],
  };
}

/**
 * Core temperature is derived from the requested output so the demo can show a
 * deterministic end-to-end effect: more power means a hotter core, and a
 * "critical" log is emitted once the core crosses the safety threshold.
 */
function tempForOutput(outputMw: number): number {
  return Math.round(AMBIENT_TEMP + outputMw * 0.6);
}

export function createApp(): Express {
  const app = express();
  app.use(express.json());

  const state = createInitialState();
  let nextLogId = state.logs.length + 1;

  const log = (level: LogEntry["level"], message: string): void => {
    state.logs.unshift({
      id: nextLogId++,
      level,
      message,
      at: new Date().toISOString(),
    });
    state.logs = state.logs.slice(0, 25);
  };

  app.get("/api/health", (_req: Request, res: Response) => {
    res.json({ ok: true, service: "faco9000", time: new Date().toISOString() });
  });

  app.get("/api/reactor", (_req: Request, res: Response) => {
    res.json(state);
  });

  app.post("/api/reactor/output", (req: Request, res: Response) => {
    const raw = (req.body as { outputMw?: unknown }).outputMw;
    const outputMw = Number(raw);

    if (!Number.isFinite(outputMw) || outputMw < MIN_OUTPUT || outputMw > MAX_OUTPUT) {
      res.status(400).json({
        error: `outputMw must be a number between ${MIN_OUTPUT} and ${MAX_OUTPUT}.`,
      });
      return;
    }

    state.outputMw = Math.round(outputMw);
    state.coreTempC = tempForOutput(state.outputMw);
    state.status = state.outputMw > 0 ? "online" : "standby";

    log("info", `Output set to ${state.outputMw} MW (core ${state.coreTempC}\u00b0C).`);
    if (state.coreTempC >= 600) {
      log("critical", "Core temperature above safe threshold — engage coolant.");
    } else if (state.coreTempC >= 400) {
      log("warn", "Core temperature elevated.");
    }

    res.json(state);
  });

  app.post("/api/reactor/scram", (_req: Request, res: Response) => {
    state.outputMw = 0;
    state.coreTempC = AMBIENT_TEMP;
    state.status = "standby";
    log("warn", "SCRAM triggered — reactor returned to standby.");
    res.json(state);
  });

  return app;
}
