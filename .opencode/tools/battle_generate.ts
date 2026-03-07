import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export default async function battleGenerate(args: { run_id: string }) {
  const { stdout } = await execFileAsync("python", ["-m", "app.cli.generate_round", "--run-id", args.run_id]);
  return JSON.parse(stdout);
}
