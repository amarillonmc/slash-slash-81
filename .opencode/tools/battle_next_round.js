import { z } from "zod";

import { runPythonJson } from "../lib/opencode_cli.js";

export default {
  description: "Run the full next-round automation loop for a run.",
  args: {
    run_id: z.string().describe("Target run id."),
  },
  async execute(args, context) {
    return runPythonJson(context, ["-m", "app.cli.next_round", "--run-id", args.run_id]);
  },
};
