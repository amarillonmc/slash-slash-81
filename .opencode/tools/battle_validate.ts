import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export default async function battleValidate(args: { run_id: string; round_no: number; draft: string; finalize?: boolean }) {
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
  const { stdout } = await execFileAsync("python", command);
  return JSON.parse(stdout);
}
