import type { ReactNode } from "react";

export function Spinner({ center }: { center?: boolean }) {
  const el = <div className="spinner" role="status" aria-label="Lädt" />;
  return center ? <div className="empty">{el}</div> : el;
}

export function Badge({ children, tone }: { children: ReactNode; tone?: "green" | "amber" | "red" | "yellow" }) {
  return <span className={`badge${tone ? ` badge-${tone}` : ""}`}>{children}</span>;
}

export function Alert({ kind, children }: { kind: "error" | "success" | "info"; children: ReactNode }) {
  return <div className={`alert alert-${kind}`}>{children}</div>;
}

export function Empty({ icon, title, children }: { icon?: string; title: string; children?: ReactNode }) {
  return (
    <div className="empty">
      {icon && <div className="icon">{icon}</div>}
      <h3>{title}</h3>
      {children && <p className="muted">{children}</p>}
    </div>
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      {children}
      {hint && <span className="hint">{hint}</span>}
    </div>
  );
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="spread" style={{ marginBottom: 28 }}>
      <div>
        <h1 style={{ marginBottom: subtitle ? 6 : 0 }}>{title}</h1>
        {subtitle && <p className="muted" style={{ margin: 0 }}>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
