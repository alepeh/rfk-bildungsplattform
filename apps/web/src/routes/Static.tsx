export function Impressum() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 760 }}>
        <h1>Impressum</h1>
        <div className="card card-pad stack">
          <div>
            <h3>Medieninhaber & Herausgeber</h3>
            <p className="muted" style={{ margin: 0 }}>
              Landesinnung der Burgenländischen Rauchfangkehrer
              <br />
              WTG Burgenland
              <br />
              7000 Eisenstadt, Österreich
            </p>
          </div>
          <div>
            <h3>Kontakt</h3>
            <p className="muted" style={{ margin: 0 }}>
              E-Mail:{" "}
              <a href="mailto:bildungsplattform@rauchfangkehrer.or.at">
                bildungsplattform@rauchfangkehrer.or.at
              </a>
            </p>
          </div>
          <p className="muted" style={{ margin: 0, fontSize: "0.88rem" }}>
            Diese Bildungsplattform dient der Organisation von Schulungen und Weiterbildungen für das
            burgenländische Rauchfangkehrerhandwerk.
          </p>
        </div>
      </div>
    </div>
  );
}

export function AGB() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 760 }}>
        <h1>AGB & Datenschutz</h1>
        <div className="card card-pad stack">
          <div>
            <h3>Allgemeine Geschäftsbedingungen</h3>
            <p className="muted" style={{ margin: 0 }}>
              Mit der Buchung einer Schulung kommt ein verbindlicher Vertrag zustande. Die Rechnung
              wird separat zugestellt und ist vor Schulungsbeginn zu begleichen. Stornierungen sind
              rechtzeitig der Geschäftsstelle bekanntzugeben.
            </p>
          </div>
          <div>
            <h3>Datenschutz (DSV)</h3>
            <p className="muted" style={{ margin: 0 }}>
              Ihre personenbezogenen Daten werden ausschließlich zur Abwicklung der Schulungsanmeldung
              und der gesetzlich vorgeschriebenen Dokumentation verarbeitet. Die Daten werden nicht an
              unbefugte Dritte weitergegeben. Sie haben jederzeit das Recht auf Auskunft, Berichtigung
              und Löschung Ihrer Daten.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
