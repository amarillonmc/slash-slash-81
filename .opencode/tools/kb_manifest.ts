import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export default async function kbManifest(args: { run_id: string; rulebooks: string[]; rolesets: string[] }) {
  const { stdout } = await execFileAsync("python", [
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
  return JSON.parse(stdout);
}
