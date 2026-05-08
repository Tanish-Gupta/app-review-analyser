import fs from "fs";
import path from "path";
import { listPulseRunIds } from "./pulses";

export function getHistoryRunIds(): string[] {
  const ids = listPulseRunIds();
  const samplePath = path.join(process.cwd(), "public", "sample", "pulse.json");
  if (fs.existsSync(samplePath) && !ids.includes("sample")) {
    return [...ids, "sample"];
  }
  return ids;
}
