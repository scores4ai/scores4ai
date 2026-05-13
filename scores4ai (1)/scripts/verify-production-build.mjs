import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const clientDir = join(process.cwd(), "dist", "client");
const indexHtml = join(clientDir, "index.html");

if (!existsSync(indexHtml)) {
  throw new Error(
    "Netlify publish output is missing dist/client/index.html. The SPA fallback would serve a 404.",
  );
}

const forbiddenPatterns = [
  /SUPABASE_SERVICE_ROLE_KEY/,
  /service[_-]?role/i,
  /sk-or-v1-[A-Za-z0-9_-]+/,
  /OPENROUTER_API_KEY/,
  /openrouter\.ai\/api\/v1\/models/,
];

function* walk(dir) {
  for (const entry of readdirSync(dir)) {
    const filePath = join(dir, entry);
    const stats = statSync(filePath);
    if (stats.isDirectory()) {
      yield* walk(filePath);
    } else {
      yield filePath;
    }
  }
}

for (const filePath of walk(clientDir)) {
  const content = readFileSync(filePath, "utf8");
  for (const pattern of forbiddenPatterns) {
    if (pattern.test(content)) {
      throw new Error(
        `Client bundle contains forbidden secret marker in ${filePath}`,
      );
    }
  }
}

console.log(
  "Production build verification passed: Netlify index exists and client bundle has no server secret markers or OpenRouter API calls.",
);
