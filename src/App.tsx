import { useEffect, useState } from "react";
import { getReactor, scram, setOutput, type ReactorState } from "./api.ts";
import "./App.css";

const MAX_OUTPUT = 1200;

function Gauge({
  label,
  value,
  unit,
  max,
  tone,
}: {
  label: string;
  value: number;
  unit: string;
  max: number;
  tone: "cyan" | "amber";
}) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div className="gauge">
      <div className="gauge__head">
        <span className="gauge__label">{label}</span>
        <span className="gauge__value">
          {value}
          <span className="gauge__unit">{unit}</span>
        </span>
      </div>
      <div className="gauge__track">
        <div
          className={`gauge__fill gauge__fill--${tone}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function App() {
  const [reactor, setReactor] = useState<ReactorState | null>(null);
  const [target, setTarget] = useState(500);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReactor().then(setReactor).catch((e: Error) => setError(e.message));
  }, []);

  async function run(action: () => Promise<ReactorState>) {
    setBusy(true);
    setError(null);
    try {
      setReactor(await action());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const online = reactor?.status === "online";

  return (
    <div className="app">
      <header className="app__header">
        <div className="brand">
          <span className={`brand__dot brand__dot--${reactor?.status ?? "standby"}`} />
          <div>
            <h1>FACO 9000</h1>
            <p>Fusion Array Control &amp; Orchestration</p>
          </div>
        </div>
        <span className={`status status--${reactor?.status ?? "standby"}`}>
          {(reactor?.status ?? "connecting").toUpperCase()}
        </span>
      </header>

      {error && <div className="banner banner--error">{error}</div>}

      <section className="panel">
        <div className="gauges">
          <Gauge
            label="Power Output"
            value={reactor?.outputMw ?? 0}
            unit=" MW"
            max={MAX_OUTPUT}
            tone="cyan"
          />
          <Gauge
            label="Core Temperature"
            value={reactor?.coreTempC ?? 0}
            unit=" \u00b0C"
            max={760}
            tone="amber"
          />
        </div>

        <div className="controls">
          <label className="controls__label" htmlFor="output">
            Target output: <strong>{target} MW</strong>
          </label>
          <input
            id="output"
            type="range"
            min={0}
            max={MAX_OUTPUT}
            step={50}
            value={target}
            onChange={(e) => setTarget(Number(e.target.value))}
          />
          <div className="controls__buttons">
            <button
              className="btn btn--primary"
              disabled={busy}
              onClick={() => run(() => setOutput(target))}
            >
              Engage
            </button>
            <button
              className="btn btn--danger"
              disabled={busy || !online}
              onClick={() => run(() => scram())}
            >
              SCRAM
            </button>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2 className="panel__title">Activity Log</h2>
        <ul className="log">
          {reactor?.logs.map((entry) => (
            <li key={entry.id} className={`log__item log__item--${entry.level}`}>
              <span className="log__level">{entry.level}</span>
              <span className="log__msg">{entry.message}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
