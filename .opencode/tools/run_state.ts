import { readFileSync } from "node:fs";

export default async function runState(args: { run_id: string }) {
  const raw = readFileSync(`runs/${args.run_id}/state.json`, "utf-8");
  return JSON.parse(raw);
}
