import { z } from "zod";

import { runPythonJson } from "../lib/opencode_cli.js";

export default {
  description: "Validate a round draft and optionally finalize it into state.",
  args: {
    run_id: z.string().describe("Target run id."),
    round_no: z.number().int().describe("Round number to validate."),
    draft: z.string().describe("Path to the draft markdown file."),
    finalize: z.boolean().optional().describe("Whether to promote the draft to final and update state."),
  },
  async execute(args, context) {
    const command = [
      "-m",
      "app.cli.validate_round",
      "--run-id",
      args.run_id,
      "--round-no",
      String(args.round_no),
      "--draft",
      args.draft,
    ];
    if (args.finalize) {
      command.push("--finalize");
    }
    return runPythonJson(context, command);
  },
};
