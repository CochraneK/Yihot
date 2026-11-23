/** Admin redirects retain the deployed prefix and reject paths outside the admin. */
export function safeAdminReturn(target: string): string {
  let path = target;
  if (/^https?:\/\//i.test(path)) {
    try { const u = new URL(path); path = u.pathname + u.search; }
    catch { return "/yihot/admin"; }
  }
  if (/^\/admin(?:\/|\?|$)/.test(path)) path = `/yihot${path}`;
  return /^\/yihot\/admin(?:\/|\?|$)/.test(path) && !/[\\\r\n]/.test(path) ? path : "/yihot/admin";
}

export const ADMIN_COOKIE_NAMES = ["aihot_admin", "aihot_oauth_state"] as const;

/** Remove named cookies from an inbound Cookie header so sibling apps on the same origin never receive them. */
export function stripNamedCookies(header: string | undefined, names: readonly string[] = ADMIN_COOKIE_NAMES): string | undefined {
  if (!header) return undefined;
  const blocked = new Set(names);
  const kept = header
    .split(";")
    .map((part) => part.trim())
    .filter((part) => {
      if (!part) return false;
      const i = part.indexOf("=");
      const name = (i > 0 ? part.slice(0, i) : part).trim();
      return !blocked.has(name);
    });
  return kept.length ? kept.join("; ") : undefined;
}

/**
 * Scope admin Set-Cookie headers to the deployed prefix (e.g. /yihot) when served through the prefixed edge.
 * Also emits a root Path=/ clear (Max-Age=0) so pre-existing root-scoped cookies are purged on sign-in and logout.
 */
export function scopeAdminSetCookies(
  setCookie: string | string[] | undefined,
  prefix: string,
  names: readonly string[] = ADMIN_COOKIE_NAMES,
): string | string[] | undefined {
  if (!setCookie || !prefix || prefix === "/") return setCookie;
  const list = Array.isArray(setCookie) ? setCookie : [setCookie];
  const out: string[] = [];
  for (const entry of list) {
    const eq = entry.indexOf("=");
    const name = eq > 0 ? entry.slice(0, eq).trim() : "";
    if (!names.includes(name)) {
      out.push(entry);
      continue;
    }
    const scoped = entry.replace(/(;\s*Path=)\/(?=;|$)/i, `$1${prefix}`);
    out.push(scoped);
    if (scoped !== entry) {
      if (/;\s*Max-Age=0(?=;|$)/i.test(entry)) {
        out.push(entry);
      } else {
        const secure = /;\s*Secure(?=;|$)/i.test(entry) ? "; Secure" : "";
        out.push(`${name}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0${secure}`);
      }
    }
  }
  return Array.isArray(setCookie) || out.length > 1 ? out : out[0];
}
