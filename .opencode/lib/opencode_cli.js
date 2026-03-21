import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

function pythonCandidates() {
  if (process.env.OPENCODE_PYTHON) {
    return [[process.env.OPENCODE_PYTHON, []]];
  }
  if (process.platform === "win32") {
    return [["py", ["-3"]], ["python", []], ["python3", []]];
  }
  return [["python3", []], ["python", []]];
}

function buildError(error, commandText) {
  const stderr = error?.stderr?.toString?.().trim?.() || "";
  const stdout = error?.stdout?.toString?.().trim?.() || "";
  const detail = stderr || stdout || error?.message || "command failed";
  return new Error(`${commandText}: ${detail}`);
}

export async function runPythonJson(context, args) {
  const cwd = context?.worktree || context?.directory || process.cwd();
  let lastError = null;

  for (const [binary, prefix] of pythonCandidates()) {
    const command = [binary, ...prefix, ...args];
    try {
      const { stdout } = await execFileAsync(binary, [...prefix, ...args], {
        cwd,
        env: process.env,
      });
      return JSON.parse(stdout);
    } catch (error) {
      if (error?.code === "ENOENT") {
        lastError = error;
        continue;
      }
      throw buildError(error, command.join(" "));
    }
  }

  throw new Error(`Unable to find a Python interpreter for: ${args.join(" ")} (${lastError?.message || "no candidates"})`);
}
