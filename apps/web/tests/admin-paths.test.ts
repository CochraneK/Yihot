import assert from "node:assert/strict";
import { test } from "node:test";
import { safeAdminReturn, scopeAdminSetCookies, stripNamedCookies } from "@aihot/contracts/admin-paths";
test("login retains deployed admin routes and legacy bookmarks, and rejects other paths", () => {
  assert.equal(safeAdminReturn("/yihot/admin/usage?days=14"), "/yihot/admin/usage?days=14");
  assert.equal(safeAdminReturn("/admin/content/item-1"), "/yihot/admin/content/item-1");
  for (const target of ["//evil.org", "/yihot/administer", "/futureme/admin", "/admin\\evil", "/admin\r\nLocation: x"]) {
    assert.equal(safeAdminReturn(target), "/yihot/admin");
  }
});

test("stripNamedCookies removes YiHot admin cookies while preserving sibling app cookies", () => {
  assert.equal(stripNamedCookies("aihot_admin=secret; theme=light; aihot_oauth_state=st"), "theme=light");
  assert.equal(stripNamedCookies("aihot_admin=only"), undefined);
  assert.equal(stripNamedCookies(undefined), undefined);
  assert.equal(stripNamedCookies("fm_session=abc; lang=zh"), "fm_session=abc; lang=zh");
});

test("scopeAdminSetCookies scopes admin cookies to /yihot and clears stale root cookies", () => {
  const login = scopeAdminSetCookies(
    "aihot_admin=tok123; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000; Secure",
    "/yihot",
  );
  assert.deepEqual(login, [
    "aihot_admin=tok123; Path=/yihot; HttpOnly; SameSite=Lax; Max-Age=2592000; Secure",
    "aihot_admin=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0; Secure",
  ]);

  const logout = scopeAdminSetCookies(
    "aihot_admin=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0",
    "/yihot",
  );
  assert.deepEqual(logout, [
    "aihot_admin=; Path=/yihot; HttpOnly; SameSite=Lax; Max-Age=0",
    "aihot_admin=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0",
  ]);

  const unrelated = scopeAdminSetCookies("other=1; Path=/", "/yihot");
  assert.equal(unrelated, "other=1; Path=/");
});

