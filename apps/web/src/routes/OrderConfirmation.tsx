import { Link } from "react-router";

export function OrderConfirmation() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 620 }}>
        <div className="card card-pad center">
          <div style={{ fontSize: "3rem", marginBottom: 8 }}>✅</div>
          <h1 style={{ fontSize: "1.7rem" }}>Bestellung bestätigt</h1>
          <p className="muted">
            Ihre Anmeldung war erfolgreich. Eine Bestätigung mit allen Details wurde an Ihre
            E-Mail-Adresse gesendet. Die Rechnung wird separat zugestellt.
          </p>
          <div className="row" style={{ justifyContent: "center", marginTop: 12 }}>
            <Link to="/bestellungen" className="btn btn-primary">
              Meine Bestellungen
            </Link>
            <Link to="/" className="btn btn-ghost">
              Weitere Schulungen
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
