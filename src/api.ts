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

async function parse(res: Response): Promise<ReactorState> {
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { error?: string };
    throw new Error(body.error ?? `Request failed (${res.status})`);
  }
  return (await res.json()) as ReactorState;
}

export async function getReactor(): Promise<ReactorState> {
  return parse(await fetch("/api/reactor"));
}

export async function setOutput(outputMw: number): Promise<ReactorState> {
  return parse(
    await fetch("/api/reactor/output", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ outputMw }),
    }),
  );
}

export async function scram(): Promise<ReactorState> {
  return parse(await fetch("/api/reactor/scram", { method: "POST" }));
}
