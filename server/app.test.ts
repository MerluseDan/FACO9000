import { describe, expect, it } from "vitest";
import request from "supertest";
import { createApp } from "./app.ts";

describe("FACO 9000 API", () => {
  it("reports health", async () => {
    const res = await request(createApp()).get("/api/health");
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ ok: true, service: "faco9000" });
  });

  it("starts in standby with zero output", async () => {
    const res = await request(createApp()).get("/api/reactor");
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ status: "standby", outputMw: 0 });
  });

  it("brings the reactor online and derives core temperature", async () => {
    const app = createApp();
    const res = await request(app)
      .post("/api/reactor/output")
      .send({ outputMw: 500 });

    expect(res.status).toBe(200);
    expect(res.body.status).toBe("online");
    expect(res.body.outputMw).toBe(500);
    expect(res.body.coreTempC).toBe(324);
  });

  it("emits a critical log past the safety threshold", async () => {
    const app = createApp();
    const res = await request(app)
      .post("/api/reactor/output")
      .send({ outputMw: 1100 });

    expect(res.status).toBe(200);
    const levels = (res.body.logs as { level: string }[]).map((l) => l.level);
    expect(levels).toContain("critical");
  });

  it("rejects out-of-range output", async () => {
    const res = await request(createApp())
      .post("/api/reactor/output")
      .send({ outputMw: 99999 });
    expect(res.status).toBe(400);
    expect(res.body.error).toBeTruthy();
  });

  it("scrams back to standby", async () => {
    const app = createApp();
    await request(app).post("/api/reactor/output").send({ outputMw: 800 });
    const res = await request(app).post("/api/reactor/scram");
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ status: "standby", outputMw: 0 });
  });
});
