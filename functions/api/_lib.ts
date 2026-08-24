/**
 * _lib.ts — shared helpers for the Columbus Districts form-handling Pages Functions.
 * (Leading-underscore files are not routed by Cloudflare Pages Functions.)
 *
 * Env (set in the Cloudflare Pages dashboard → Settings → Environment variables):
 *   FORMSPREE_FORM_ID        — Formspree form id; submissions are delivered here.
 *                              Its destination inbox (info@columbusdistricts.com) is set in
 *                              the Formspree dashboard. Optional per-form overrides below.
 *   FORMSPREE_SUGGEST_ID     — optional: separate Formspree form for "Suggest an edit"
 *   FORMSPREE_NAME_ID        — optional: separate Formspree form for "Name the district"
 *   TURNSTILE_SECRET_KEY     — Cloudflare Turnstile secret (verification skipped if unset)
 */
export interface Env {
  FORMSPREE_FORM_ID?: string;
  FORMSPREE_SUGGEST_ID?: string;
  FORMSPREE_NAME_ID?: string;
  TURNSTILE_SECRET_KEY?: string;
}

/** Verify a Turnstile token. Returns true when Turnstile isn't configured (local/dev). */
export async function verifyTurnstile(env: Env, token: string, ip: string): Promise<boolean> {
  if (!env.TURNSTILE_SECRET_KEY) return true; // not configured — rely on the honeypot
  if (!token) return false;
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ secret: env.TURNSTILE_SECRET_KEY, response: token, remoteip: ip }),
  });
  const data = (await r.json()) as { success?: boolean };
  return !!data.success;
}

/**
 * Deliver a validated submission to Formspree, which emails it to the form's configured
 * inbox (info@columbusdistricts.com) and keeps a record in the Formspree dashboard.
 * `formId` picks the form (a per-form id, or the shared FORMSPREE_FORM_ID). Formspree
 * recognizes `email` (reply-to) and `_subject`. No-ops (logs) if no form id is configured.
 */
export async function submitToFormspree(
  env: Env,
  formId: string | undefined,
  fields: Record<string, string>
): Promise<{ ok: boolean; skipped?: boolean; status?: number }> {
  const id = formId || env.FORMSPREE_FORM_ID;
  if (!id) {
    console.log("[forms] No Formspree form id configured — not delivered:", fields._subject);
    return { ok: false, skipped: true };
  }
  const body = new URLSearchParams(fields);
  const r = await fetch(`https://formspree.io/f/${id}`, {
    method: "POST",
    headers: { Accept: "application/json", "content-type": "application/x-www-form-urlencoded" },
    body,
  });
  return { ok: r.ok, status: r.status };
}

/** 303-redirect to a same-origin path (progressive-enhancement thank-you flow). */
export function seeOther(requestUrl: string, path: string): Response {
  return Response.redirect(new URL(path, requestUrl).toString(), 303);
}

export function badRequest(msg: string): Response {
  return new Response(msg, { status: 400, headers: { "content-type": "text/plain; charset=utf-8" } });
}
