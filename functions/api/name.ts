/**
 * POST /api/name — "Name the district" form handler (Cloudflare Pages Function).
 * Validates, checks the honeypot + Turnstile, delivers the submission via Formspree,
 * then 303-redirects to the thank-you page (works without client JS).
 */
import { Env, verifyTurnstile, submitToFormspree, seeOther, badRequest } from "./_lib";

export const onRequestPost: (ctx: { request: Request; env: Env }) => Promise<Response> = async ({ request, env }) => {
  const form = await request.formData();

  if ((form.get("company") || "").toString().trim()) return seeOther(request.url, "/name-the-districts/thanks/");

  const ip = request.headers.get("CF-Connecting-IP") || "";
  const token = (form.get("cf-turnstile-response") || "").toString();
  if (!(await verifyTurnstile(env, token, ip))) return badRequest("Verification failed — please go back and try again.");

  const district = (form.get("district") || "").toString().slice(0, 8);
  const name = (form.get("name") || "").toString().slice(0, 200);
  const email = (form.get("email") || "").toString().slice(0, 200);
  const suggested = (form.get("suggested_name") || "").toString().slice(0, 200);
  const reason = (form.get("reason") || "").toString().slice(0, 2000);
  if (!email.includes("@") || !suggested.trim()) return badRequest("An email address and a suggested name are required.");

  await submitToFormspree(env, env.FORMSPREE_NAME_ID, {
    _subject: `[Columbus Districts] Name suggestion — District ${district}`,
    district,
    name,
    email,
    suggested_name: suggested,
    reason,
  });

  return seeOther(request.url, "/name-the-districts/thanks/");
};
