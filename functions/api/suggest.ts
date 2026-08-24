/**
 * POST /api/suggest — "Suggest an edit" form handler (Cloudflare Pages Function).
 * Validates, checks the honeypot + Turnstile, delivers the submission via Formspree,
 * then 303-redirects to the thank-you page (works without client JS).
 */
import { Env, verifyTurnstile, submitToFormspree, seeOther, badRequest } from "./_lib";

export const onRequestPost: (ctx: { request: Request; env: Env }) => Promise<Response> = async ({ request, env }) => {
  const form = await request.formData();

  // Honeypot — bots fill "company"; accept silently so they don't retry.
  if ((form.get("company") || "").toString().trim()) return seeOther(request.url, "/suggest-edit-thanks/");

  const ip = request.headers.get("CF-Connecting-IP") || "";
  const token = (form.get("cf-turnstile-response") || "").toString();
  if (!(await verifyTurnstile(env, token, ip))) return badRequest("Verification failed — please go back and try again.");

  const district = (form.get("district") || "").toString().slice(0, 8);
  const name = (form.get("name") || "").toString().slice(0, 200);
  const email = (form.get("email") || "").toString().slice(0, 200);
  const message = (form.get("message") || "").toString().slice(0, 5000);
  if (!email.includes("@") || !message.trim()) return badRequest("An email address and a message are required.");

  await submitToFormspree(env, env.FORMSPREE_SUGGEST_ID, {
    _subject: `[Columbus Districts] Suggested edit — District ${district}`,
    district,
    name,
    email,
    message,
  });

  return seeOther(request.url, "/suggest-edit-thanks/");
};
