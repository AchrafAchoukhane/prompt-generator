import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("the product page covers the complete optimization workflow", async () => {
  const page = await readFile(new URL("../src/PromptWorkspace.tsx", import.meta.url), "utf8");
  for (const label of ["Prompt original", "Prompt optimisé", "Améliorations", "Informations manquantes", "Optimisations récentes"]) {
    assert.match(page, new RegExp(label));
  }
  assert.match(page, /\/optimizations/);
  assert.match(page, /original_score/);
  assert.match(page, /optimized_score/);
});

test("the starter preview has been fully replaced", async () => {
  const [app, index, packageJson] = await Promise.all([
    readFile(new URL("../src/App.tsx", import.meta.url), "utf8"),
    readFile(new URL("../index.html", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);
  assert.match(app, /PromptWorkspace/);
  assert.match(index, /lang="fr"/);
  assert.doesNotMatch(app + index + packageJson, /SkeletonPreview|react-loading-skeleton|codex-preview/);
});
