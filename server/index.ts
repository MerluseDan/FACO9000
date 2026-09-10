import { createApp } from "./app.ts";

const port = Number(process.env.API_PORT ?? 3001);
const app = createApp();

app.listen(port, () => {
  console.log(`[faco9000] API listening on http://localhost:${port}`);
});
