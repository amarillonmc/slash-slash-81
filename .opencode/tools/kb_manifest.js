import { z } from "zod";

import { runPythonJson } from "../lib/opencode_cli.js";

export default {
  description: "Build a run manifest from the KB topic index.",
  args: {
    run_id: z.string().describe("Target run id."),
    rulebooks: z.array(z.string()).describe("Rulebook titles to resolve from the KB index."),
    rolesets: z.array(z.string()).describe("Role titles to resolve from the KB index."),
  },
  async execute(args, context) {
    return runPythonJson(context, [
      "-m",
      "app.cli.build_manifest",
      "--run-id",
      args.run_id,
      "--rulebooks",
      args.rulebooks.join(","),
      "--rolesets",
      args.rolesets.join(","),
      "--output",
      `runs/${args.run_id}/manifest.json`,
    ]);
  },
};
