// Offline regression tests for the 2026-11-24 security & reliability hardening fixes.
import assert from "node:assert/strict";
import { test } from "node:test";
import { cookie, parseCookies } from "../packages/backend/src/admin/auth.ts";
import { switchModel } from "../packages/backend/src/admin/models.ts";
import { validateBudgetFloor } from "../packages/backend/src/admin/settings.ts";
import { DigestSchema } from "../packages/backend/src/events/digest.ts";
import { isModelConfigured, missingModelConfig } from "../packages/backend/src/providers/llm.ts";
import { LeadSchema, PeriodSchema } from "../packages/backend/src/reports/compose.ts";

test("parseCookies survives malformed percent-encoding and keeps first occurrence (RFC 6265 specificity)", () => {
  const parsed = parseCookies("bad=%E0%A4%A; aihot_admin=scoped-token; aihot_admin=stale-root-token; ok=hello%20world");
  assert.equal(parsed.bad, "%E0%A4%A");
  assert.equal(parsed.aihot_admin, "scoped-token");
  assert.equal(parsed.ok, "hello world");
  assert.equal(cookie("aihot_admin", "v", 60, true, "/yihot"), "aihot_admin=v; Path=/yihot; HttpOnly; SameSite=Lax; Max-Age=60; Secure");
});

test("switchModel refuses models whose runtime credentials are missing (prevents silent pipeline outages)", async () => {
  const prevBase = process.env.DASHSCOPE_BASE_URL;
  const prevKey = process.env.DASHSCOPE_API_KEY;
  delete process.env.DASHSCOPE_BASE_URL;
  delete process.env.DASHSCOPE_API_KEY;
  try {
    assert.equal(isModelConfigured("qwen3.7-flash"), false);
    assert.deepEqual(missingModelConfig("qwen3.7-flash"), ["DASHSCOPE_BASE_URL", "DASHSCOPE_API_KEY"]);
    await assert.rejects(
      () => switchModel("digest", "qwen3.7-flash", "test switch without creds", "admin:test"),
      (err: unknown) => {
        const e = err as { statusCode?: number; message?: string };
        return e.statusCode === 400 && /未配置凭据/.test(e.message ?? "");
      },
    );
  } finally {
    if (prevBase === undefined) delete process.env.DASHSCOPE_BASE_URL;
    else process.env.DASHSCOPE_BASE_URL = prevBase;
    if (prevKey === undefined) delete process.env.DASHSCOPE_API_KEY;
    else process.env.DASHSCOPE_API_KEY = prevKey;
  }
});

test("validateBudgetFloor blocks accidental circuit-breaker lockouts unless forced or explicitly zeroed", () => {
  assert.throws(
    () => validateBudgetFloor({ perMinute: 60, perHour: 1000, perDay: 500 }, { usedHour: 10, usedDay: 500 }),
    (err: unknown) => (err as { statusCode?: number }).statusCode === 400,
  );
  assert.throws(
    () => validateBudgetFloor({ perMinute: 60, perHour: 50, perDay: 2000 }, { usedHour: 55, usedDay: 100 }),
    (err: unknown) => (err as { statusCode?: number }).statusCode === 400,
  );
  // Explicit 0 stop, higher cap, and forced override are allowed.
  assert.doesNotThrow(() => validateBudgetFloor({ perMinute: 60, perHour: 1000, perDay: 0 }, { usedHour: 10, usedDay: 500 }));
  assert.doesNotThrow(() => validateBudgetFloor({ perMinute: 60, perHour: 1000, perDay: 501 }, { usedHour: 10, usedDay: 500 }));
  assert.doesNotThrow(() => validateBudgetFloor({ perMinute: 60, perHour: 1000, perDay: 400, force: true }, { usedHour: 10, usedDay: 500 }));
});

test("DigestSchema, LeadSchema and PeriodSchema reject leaked reasoning/prompt non-copy", () => {
  const leak = "We need to produce title_zh and summary_zh. <think>先分析材料</think> 某基金会发布年度报告。";
  assert.throws(() => DigestSchema.parse({ title: "正常事件标题", digest: leak, latest: "最新进展" }));
  assert.throws(() => DigestSchema.parse({ title: leak, digest: "某基金会发布年度报告，全年资助乡村儿童阅读项目覆盖十二个省份。", latest: "" }));
  assert.doesNotThrow(() => DigestSchema.parse({
    title: "某基金会发布乡村儿童阅读年报",
    digest: "某基金会发布年度报告，全年资助乡村儿童阅读项目覆盖十二个省份，并公开审计明细。",
    latest: "基金会已公开年度审计明细。",
  }));

  assert.throws(() => LeadSchema.parse({ title: "日报标题", leadParagraph: leak, highlights: [1] }));
  assert.doesNotThrow(() => LeadSchema.parse({
    title: "民政部更新社会组织公开指引",
    leadParagraph: "民政部发布新版信息公开指引，明确慈善组织项目执行与财务披露节点。",
    highlights: [1, 2],
  }));

  assert.throws(() => PeriodSchema.parse({
    headline: "本期周报",
    overview: leak,
    themes: [{ heading: "儿童保护", summary: "多地开展儿童保护服务。", refs: [1] }],
  }));
  assert.doesNotThrow(() => PeriodSchema.parse({
    headline: "多地推进慈善信息公开",
    overview: "本周样本覆盖 11 月 17 日至 23 日，重点围绕信息公开与儿童服务落地展开。",
    themes: [{ heading: "儿童保护", summary: "多地社会组织联合推进儿童保护项目落地。", refs: [1] }],
  }));
});
