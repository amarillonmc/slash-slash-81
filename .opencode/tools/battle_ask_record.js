import { z } from "zod";

import { runPythonJson } from "../lib/opencode_cli.js";

export default {
  description: "Answer a question against a run record and append QA output.",
  args: {
    run_id: z.string().describe("Target run id."),
    question: z.string().describe("Question to answer from the run record."),
  },
  async execute(args, context) {
    return runPythonJson(context, [
      "-m",
      "app.cli.ask_record",
      "--run-id",
      args.run_id,
      "--question",
      args.question,
    ]);
  },
};
