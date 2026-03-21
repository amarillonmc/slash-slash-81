import { z } from "zod";

import { runPythonJson } from "../lib/opencode_cli.js";

export default {
  description: "Generate the next round draft package for a run.",
  args: {
    run_id: z.string().describe("Target run id."),
  },
  async execute(args, context) {
    return runPythonJson(context, ["-m", "app.cli.generate_round", "--run-id", args.run_id]);
  },
};
