// Transactional email via the native Cloudflare Email Service binding.
// Send failures never break the originating request — callers log and move on.

interface Mail {
  to: string;
  subject: string;
  html: string;
  text: string;
  replyTo?: string;
}

// The send_email binding exposes .send({...}); typed loosely to stay
// independent of the exact generated SendEmail shape.
type EmailBinding = { send: (m: Record<string, unknown>) => Promise<{ messageId?: string }> };

export async function sendMail(env: Env, mail: Mail): Promise<boolean> {
  try {
    await (env.EMAIL as unknown as EmailBinding).send({
      to: mail.to,
      from: { email: env.EMAIL_FROM, name: env.EMAIL_FROM_NAME },
      ...(mail.replyTo ? { replyTo: mail.replyTo } : {}),
      subject: mail.subject,
      text: mail.text,
      html: mail.html,
    });
    return true;
  } catch (err) {
    console.error("sendMail failed", mail.to, mail.subject, err);
    return false;
  }
}

function eur(cents: number): string {
  return (cents / 100).toLocaleString("de-AT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("de-AT", { dateStyle: "long", timeStyle: "short", timeZone: "Europe/Vienna" });
}

// Shared shell — brand red header, clean body.
function shell(heading: string, body: string): string {
  return `<!doctype html><html lang="de"><body style="margin:0;background:#f4f4f5;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#18181b;">
  <div style="max-width:600px;margin:0 auto;padding:24px;">
    <div style="background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);">
      <div style="background:#d11317;padding:20px 28px;">
        <span style="color:#fff;font-size:18px;font-weight:700;letter-spacing:.2px;">Bildungsplattform</span>
        <span style="color:#ffd400;font-size:13px;display:block;margin-top:2px;">Die Burgenländischen Rauchfangkehrer</span>
      </div>
      <div style="padding:28px;">
        <h1 style="margin:0 0 16px;font-size:20px;color:#18181b;">${heading}</h1>
        ${body}
        <p style="margin-top:28px;color:#71717a;font-size:13px;border-top:1px solid #e4e4e7;padding-top:16px;">
          Bei Fragen: <a href="mailto:bildungsplattform@rauchfangkehrer.or.at" style="color:#d11317;">bildungsplattform@rauchfangkehrer.or.at</a><br>
          Für Umwelt und Leben
        </p>
      </div>
    </div>
  </div></body></html>`;
}

function venueBlock(ort: VenueInfo | null): string {
  if (!ort) return "";
  const lines = [
    ort.name ? `<strong>${ort.name}</strong>` : "",
    ort.adresse ?? "",
    [ort.plz, ort.ort].filter(Boolean).join(" "),
    ort.kontakt ? `Kontakt: ${ort.kontakt}` : "",
    ort.telefon ? `Tel: ${ort.telefon}` : "",
  ].filter(Boolean);
  const maps =
    ort.adresse || ort.ort
      ? `<p style="margin-top:12px;"><a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
          [ort.name, ort.adresse, ort.plz, ort.ort].filter(Boolean).join(", "),
        )}" style="color:#d11317;">📍 Route in Google Maps</a></p>`
      : "";
  return `<div style="background:#fafafa;border-radius:10px;padding:16px;margin:16px 0;">
    <p style="margin:0 0 8px;font-weight:600;">Veranstaltungsort</p>
    <p style="margin:0;line-height:1.6;">${lines.join("<br>")}</p>${maps}</div>`;
}

export interface VenueInfo {
  name: string;
  adresse: string | null;
  plz: string | null;
  ort: string | null;
  kontakt: string | null;
  telefon: string | null;
}

export interface OrderEmailData {
  bestellungId: string;
  schulungName: string;
  datumVon: string;
  dauer: string | null;
  anzahl: number;
  gesamtpreisCents: number;
  ort: VenueInfo | null;
}

export function orderConfirmation(d: OrderEmailData): { subject: string; html: string; text: string } {
  const info = `
    <p>Sehr geehrte Damen und Herren,</p>
    <p>vielen Dank für Ihre Bestellung. Hiermit bestätigen wir Ihre Anmeldung:</p>
    <div style="background:#fafafa;border-radius:10px;padding:16px;margin:16px 0;line-height:1.8;">
      <div><strong>Bestellnummer:</strong> ${d.bestellungId.slice(0, 8)}</div>
      <div><strong>Schulung:</strong> ${d.schulungName}</div>
      <div><strong>Datum:</strong> ${fmtDate(d.datumVon)}</div>
      ${d.dauer ? `<div><strong>Dauer:</strong> ${d.dauer}</div>` : ""}
      <div><strong>Anzahl Teilnehmer:</strong> ${d.anzahl}</div>
      <div><strong>Gesamtpreis:</strong> € ${eur(d.gesamtpreisCents)}</div>
    </div>
    ${venueBlock(d.ort)}
    <p style="font-size:14px;color:#52525b;">Die Rechnung wird separat zugestellt und ist vor Schulungsbeginn zu begleichen.</p>`;
  return {
    subject: `Bestellbestätigung – ${d.schulungName}`,
    html: shell("Ihre Bestellung war erfolgreich", info),
    text: `Bestellbestätigung\n\nSchulung: ${d.schulungName}\nDatum: ${fmtDate(d.datumVon)}\nAnzahl: ${d.anzahl}\nGesamtpreis: EUR ${eur(d.gesamtpreisCents)}\nBestellnummer: ${d.bestellungId.slice(0, 8)}`,
  };
}

export function reminderEmail(d: { schulungName: string; datumVon: string; dauer: string | null; ort: VenueInfo | null }): {
  subject: string;
  html: string;
  text: string;
} {
  const body = `
    <p>Wir möchten Sie an Ihre bevorstehende Schulung erinnern:</p>
    <div style="background:#fafafa;border-radius:10px;padding:16px;margin:16px 0;line-height:1.8;">
      <div><strong>Schulung:</strong> ${d.schulungName}</div>
      <div><strong>Datum:</strong> ${fmtDate(d.datumVon)}</div>
      ${d.dauer ? `<div><strong>Dauer:</strong> ${d.dauer}</div>` : ""}
    </div>
    ${venueBlock(d.ort)}`;
  return {
    subject: `Schulungserinnerung: ${d.schulungName}`,
    html: shell("Erinnerung an Ihre Schulung", body),
    text: `Erinnerung\n\nSchulung: ${d.schulungName}\nDatum: ${fmtDate(d.datumVon)}`,
  };
}

export function activationEmail(appUrl: string): { subject: string; html: string; text: string } {
  const body = `
    <p>Ihr Konto auf der Bildungsplattform wurde freigeschaltet.</p>
    <p>Sie können sich jetzt anmelden und Schulungen buchen.</p>
    <p style="margin-top:20px;"><a href="${appUrl}/login" style="background:#d11317;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:600;">Jetzt anmelden</a></p>`;
  return {
    subject: "Ihr Konto wurde aktiviert",
    html: shell("Willkommen!", body),
    text: `Ihr Konto wurde aktiviert. Anmelden: ${appUrl}/login`,
  };
}

export function passwordResetEmail(d: { appUrl: string; token: string }): {
  subject: string;
  html: string;
  text: string;
} {
  const link = `${d.appUrl}/passwort-zuruecksetzen?token=${encodeURIComponent(d.token)}`;
  const body = `
    <p>Sie haben das Zurücksetzen Ihres Passworts angefordert.</p>
    <p>Klicken Sie auf den folgenden Button, um ein neues Passwort zu vergeben. Der Link ist
       <strong>60 Minuten</strong> gültig.</p>
    <p style="margin:24px 0;"><a href="${link}" style="background:#d11317;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:600;">Neues Passwort festlegen</a></p>
    <p style="font-size:13px;color:#71717a;">Falls Sie diese Anfrage nicht gestellt haben, können Sie diese
       E-Mail ignorieren — Ihr Passwort bleibt unverändert.</p>`;
  return {
    subject: "Passwort zurücksetzen",
    html: shell("Passwort zurücksetzen", body),
    text: `Passwort zurücksetzen (60 Minuten gültig): ${link}\n\nFalls Sie das nicht angefordert haben, ignorieren Sie diese E-Mail.`,
  };
}

export function certificateReadyEmail(d: { schulungName: string; appUrl: string }): {
  subject: string;
  html: string;
  text: string;
} {
  const body = `
    <p>Herzlichen Glückwunsch! Ihre Teilnahme an der folgenden Schulung wurde bestätigt:</p>
    <div style="background:#fafafa;border-radius:10px;padding:16px;margin:16px 0;">
      <strong>${d.schulungName}</strong>
    </div>
    <p>Ihre Teilnahmebestätigung steht ab sofort zum Download bereit.</p>
    <p style="margin-top:20px;"><a href="${d.appUrl}/meine-schulungen" style="background:#d11317;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:600;">Teilnahmebestätigung herunterladen</a></p>`;
  return {
    subject: `Teilnahmebestätigung: ${d.schulungName}`,
    html: shell("Ihre Teilnahmebestätigung ist bereit", body),
    text: `Ihre Teilnahme an "${d.schulungName}" wurde bestätigt. Teilnahmebestätigung herunterladen: ${d.appUrl}/meine-schulungen`,
  };
}

export function adminRegistrationNotice(d: { name: string; email: string; username: string; dsv: boolean }, appUrl: string): {
  subject: string;
  html: string;
  text: string;
} {
  const body = `
    <p>Eine neue Registrierung wartet auf Freischaltung:</p>
    <div style="background:#fafafa;border-radius:10px;padding:16px;margin:16px 0;line-height:1.8;">
      <div><strong>Name:</strong> ${d.name}</div>
      <div><strong>E-Mail:</strong> ${d.email}</div>
      <div><strong>Benutzername:</strong> ${d.username}</div>
      <div><strong>DSV akzeptiert:</strong> ${d.dsv ? "Ja" : "Nein"}</div>
    </div>
    <p><a href="${appUrl}/admin/personen" style="color:#d11317;">Im Admin-Bereich freischalten</a></p>`;
  return {
    subject: "Neue Registrierung – Aktivierung erforderlich",
    html: shell("Neue Registrierung", body),
    text: `Neue Registrierung: ${d.name} (${d.email}, ${d.username}). Freischaltung erforderlich.`,
  };
}
