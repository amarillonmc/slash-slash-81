import { z } from "zod";

import { runPythonJson } from "../lib/opencode_cli.js";

export default {
  description: "Create a new battle run and initialize manifest/state.",
  args: {
    rulebooks: z.string().describe("Comma-separated rulebook titles."),
    rolesets: z.string().describe("Comma-separated role titles."),
    run_id: z.string().optional().describe("Optional fixed run id."),
  },
  async execute(args, context) {
    const command = [
      "-m",
      "app.cli.create_run",
      "--rulebooks",
      args.rulebooks,
      "--rolesets",
      args.rolesets,
    ];
    if (args.run_id) {
      command.push("--run-id", args.run_id);
    }
    return runPythonJson(context, command);
  },
};
