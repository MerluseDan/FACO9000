// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import App from "./App.tsx";
import type { ReactorState } from "./api.ts";

const initial: ReactorState = {
  status: "standby",
  outputMw: 0,
  coreTempC: 24,
  logs: [{ id: 1, level: "info", message: "System initialized.", at: "now" }],
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("<App />", () => {
  it("renders reactor state fetched from the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => initial,
      })) as unknown as typeof fetch,
    );

    render(<App />);

    expect(screen.getByRole("heading", { name: "FACO 9000" })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("System initialized.")).toBeInTheDocument(),
    );
    expect(screen.getAllByText("STANDBY").length).toBeGreaterThan(0);
  });
});
