import { useState } from "react";
import { NavLink, Link, Outlet, useNavigate } from "react-router";
import { useAuth } from "../auth";

export function Layout() {
  const { me, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const nav = useNavigate();

  function doLogout() {
    logout();
    setOpen(false);
    nav("/");
  }

  const links = (
    <>
      <NavLink to="/" end onClick={() => setOpen(false)}>
        Schulungen
      </NavLink>
      {me && (
        <NavLink to="/meine-schulungen" onClick={() => setOpen(false)}>
          Meine Schulungen
        </NavLink>
      )}
      {me?.is_geschaeftsfuehrer && (
        <>
          <NavLink to="/mitarbeiter" onClick={() => setOpen(false)}>
            Mitarbeiter
          </NavLink>
          <NavLink to="/bestellungen" onClick={() => setOpen(false)}>
            Bestellungen
          </NavLink>
        </>
      )}
      {me && (
        <NavLink to="/dokumente" onClick={() => setOpen(false)}>
          Dokumente
        </NavLink>
      )}
      {me?.is_staff && (
        <NavLink to="/admin" onClick={() => setOpen(false)}>
          Verwaltung
        </NavLink>
      )}
      {me ? (
        <div className="row" style={{ gap: 8, marginLeft: 6 }}>
          <Link to="/konto" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>
            {me.person ? me.person.vorname : me.username}
          </Link>
          <button className="btn btn-dark btn-sm" onClick={doLogout}>
            Abmelden
          </button>
        </div>
      ) : (
        <div className="row" style={{ gap: 8, marginLeft: 6 }}>
          <Link to="/login" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>
            Anmelden
          </Link>
          <Link to="/registrieren" className="btn btn-primary btn-sm" onClick={() => setOpen(false)}>
            Registrieren
          </Link>
        </div>
      )}
    </>
  );

  return (
    <>
      <header className="nav">
        <div className="container nav-inner">
          <Link to="/" className="brand">
            <img src="/logo-rfk.png" alt="Die Burgenländischen Rauchfangkehrer" />
            <span className="brand-text">
              Bildungsplattform
              <small>Burgenländische Rauchfangkehrer</small>
            </span>
          </Link>
          <button className="nav-toggle" aria-label="Menü" onClick={() => setOpen((o) => !o)}>
            ☰
          </button>
          <nav className={`nav-links${open ? " open" : ""}`}>{links}</nav>
        </div>
      </header>

      <main>
        <Outlet />
      </main>

      <footer className="footer">
        <div className="container">
          <div className="spread">
            <div>
              <strong style={{ color: "var(--ink)" }}>Die Burgenländischen Rauchfangkehrer</strong>
              <p className="muted" style={{ margin: "4px 0 0", fontSize: "0.9rem" }}>
                Für Umwelt und Leben · © 2024–{new Date().getFullYear()} WTG Burgenland
              </p>
            </div>
            <div>
              <Link to="/agb">AGB / Datenschutz</Link>
              <Link to="/impressum">Impressum</Link>
            </div>
          </div>
          <div style={{ marginTop: 20 }}>
            <img src="/oecert-logo.jpg" alt="ÖCert" />
          </div>
        </div>
      </footer>
    </>
  );
}
