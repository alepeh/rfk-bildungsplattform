// PDF generation via pdf-lib (pure JS — runs inside the Worker, no container).
// Two documents: the attendance sheet (admin) and the completion certificate
// (Teilnahmebestätigung), both ports of the legacy ReportLab output.

import { PDFDocument, StandardFonts, rgb, type PDFFont } from "pdf-lib";

const RED = rgb(0.82, 0.075, 0.09); // brand #d11317
const INK = rgb(0.086, 0.094, 0.114);
const GREY = rgb(0.42, 0.45, 0.5);
const LINE = rgb(0.85, 0.86, 0.88);

export interface AttendanceRow {
  name: string;
  betrieb: string;
  email: string;
  telefon: string;
  dsv: boolean;
}

export interface AttendanceSheet {
  schulungName: string;
  datum: string; // already formatted, e.g. "15. September 2026"
  ort: string | null;
  rows: AttendanceRow[];
}

// Landscape A4 attendance list: Name, Betrieb, Email, Telefon, Unterschrift, DSV.
export async function attendanceSheetPdf(data: AttendanceSheet): Promise<Uint8Array> {
  const doc = await PDFDocument.create();
  const font = await doc.embedFont(StandardFonts.Helvetica);
  const bold = await doc.embedFont(StandardFonts.HelveticaBold);

  const A4_LANDSCAPE: [number, number] = [841.89, 595.28];
  const margin = 36;
  const cols = [
    { label: "Name", w: 170 },
    { label: "Betrieb", w: 150 },
    { label: "E-Mail", w: 170 },
    { label: "Telefon", w: 95 },
    { label: "Unterschrift", w: 130 },
    { label: "DSV", w: 55 },
  ];
  const rowH = 26;
  const tableW = cols.reduce((s, c) => s + c.w, 0);

  let page = doc.addPage(A4_LANDSCAPE);
  let y = A4_LANDSCAPE[1] - margin;

  function header() {
    page.drawText("Teilnehmerliste", { x: margin, y: y - 18, size: 18, font: bold, color: INK });
    page.drawText(data.schulungName, { x: margin, y: y - 38, size: 12, font: bold, color: RED });
    const sub = [data.datum, data.ort].filter(Boolean).join(" · ");
    page.drawText(sub, { x: margin, y: y - 54, size: 10, font, color: GREY });
    y -= 78;
    drawRow(cols.map((c) => c.label), bold, true);
  }

  function drawRow(cells: string[], f: PDFFont, isHeader = false) {
    if (isHeader) {
      page.drawRectangle({ x: margin, y: y - rowH + 6, width: tableW, height: rowH, color: rgb(0.98, 0.98, 0.99) });
    }
    let x = margin;
    cells.forEach((cell, i) => {
      const text = truncate(cell, cols[i]!.w - 10, f, 9);
      page.drawText(text, { x: x + 5, y: y - rowH + 14, size: 9, font: f, color: isHeader ? GREY : INK });
      x += cols[i]!.w;
    });
    // bottom border
    page.drawLine({ start: { x: margin, y: y - rowH + 6 }, end: { x: margin + tableW, y: y - rowH + 6 }, thickness: 0.5, color: LINE });
    y -= rowH;
  }

  function truncate(s: string, maxW: number, f: PDFFont, size: number): string {
    if (f.widthOfTextAtSize(s, size) <= maxW) return s;
    let out = s;
    while (out.length > 1 && f.widthOfTextAtSize(out + "…", size) > maxW) out = out.slice(0, -1);
    return out + "…";
  }

  header();
  const bottom = margin + 40;
  for (const r of data.rows) {
    if (y - rowH < bottom) {
      page = doc.addPage(A4_LANDSCAPE);
      y = A4_LANDSCAPE[1] - margin;
      header();
    }
    drawRow([r.name, r.betrieb, r.email, r.telefon, "", r.dsv ? "Ja" : "Nein"], font);
  }
  // a few blank rows for walk-ins
  for (let i = 0; i < 3 && y - rowH > bottom; i++) drawRow(["", "", "", "", "", ""], font);

  page.drawText("* DSV = Datenschutzvereinbarung akzeptiert", {
    x: margin,
    y: bottom - 8,
    size: 8,
    font,
    color: GREY,
  });

  return doc.save();
}

export interface Certificate {
  participantName: string;
  schulungName: string;
  datum: string;
  ort: string | null;
  dauer: string | null;
}

// A4 portrait completion certificate (Teilnahmebestätigung).
export async function certificatePdf(data: Certificate): Promise<Uint8Array> {
  const doc = await PDFDocument.create();
  const font = await doc.embedFont(StandardFonts.Helvetica);
  const bold = await doc.embedFont(StandardFonts.HelveticaBold);
  const A4: [number, number] = [595.28, 841.89];
  const page = doc.addPage(A4);
  const w = A4[0];
  const cx = w / 2;

  const center = (text: string, y: number, size: number, f: PDFFont, color = INK) => {
    const tw = f.widthOfTextAtSize(text, size);
    page.drawText(text, { x: cx - tw / 2, y, size, font: f, color });
  };

  // Decorative brand bar
  page.drawRectangle({ x: 0, y: A4[1] - 8, width: w, height: 8, color: RED });
  page.drawRectangle({ x: 0, y: A4[1] - 14, width: w, height: 6, color: rgb(1, 0.83, 0) });

  center("TEILNAHMEBESTÄTIGUNG", A4[1] - 140, 24, bold, RED);
  center("Die Burgenländischen Rauchfangkehrer", A4[1] - 168, 12, font, GREY);

  center("hiermit wird bestätigt, dass", A4[1] - 250, 12, font, GREY);
  center(data.participantName, A4[1] - 290, 22, bold, INK);
  center("erfolgreich an der folgenden Schulung teilgenommen hat:", A4[1] - 326, 12, font, GREY);

  center(data.schulungName, A4[1] - 380, 16, bold, INK);
  const meta = [data.datum, data.dauer ? `Dauer: ${data.dauer}` : "", data.ort ?? ""].filter(Boolean);
  let my = A4[1] - 410;
  for (const line of meta) {
    center(line, my, 11, font, GREY);
    my -= 18;
  }

  // Signature line
  const sigY = 180;
  page.drawLine({ start: { x: cx - 110, y: sigY }, end: { x: cx + 110, y: sigY }, thickness: 0.75, color: LINE });
  center("WTG Burgenland · Geschäftsstelle", sigY - 16, 10, font, GREY);
  center("Für Umwelt und Leben", 120, 10, font, RED);

  return doc.save();
}
