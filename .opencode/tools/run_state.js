import { readFile } from "node:fs/promises";
import path from "node:path";
import { z } from "zod";

export default {
  description: "Read the persisted state.json for a run.",
  args: {
    run_id: z.string().describe("Target run id."),
  },
  async execute(args, context) {
    const root = context?.worktree || context?.directory || process.cwd();
    const file = path.join(root, "runs", args.run_id, "state.json");
    const raw = await readFile(file, "utf-8");
    return JSON.parse(raw);
  },
};
