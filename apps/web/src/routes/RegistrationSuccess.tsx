import { Link } from "react-router";

export function RegistrationSuccess() {
  return (
    <div className="auth-wrap">
      <div className="card card-pad auth-card center">
        <div style={{ fontSize: "3rem", marginBottom: 8 }}>✉️</div>
        <h1 style={{ fontSize: "1.6rem" }}>Registrierung erhalten</h1>
        <p className="muted">
          Vielen Dank! Ihr Konto wird von der Geschäftsstelle der Burgenländischen Rauchfangkehrer
          geprüft und freigeschaltet. Sie können sich anmelden, sobald die Freischaltung erfolgt ist.
        </p>
        <Link to="/login" className="btn btn-primary btn-block" style={{ marginTop: 12 }}>
          Zur Anmeldung
        </Link>
      </div>
    </div>
  );
}
