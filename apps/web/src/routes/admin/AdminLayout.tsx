import { NavLink, Outlet } from "react-router";

const tabs = [
  { to: "/admin", label: "Übersicht", end: true },
  { to: "/admin/personen", label: "Personen" },
  { to: "/admin/schulungen", label: "Schulungen" },
  { to: "/admin/termine", label: "Termine" },
  { to: "/admin/dokumente", label: "Dokumente" },
  { to: "/admin/todos", label: "To-dos" },
];

export function AdminLayout() {
  return (
    <div className="page">
      <div className="container">
        <h1 style={{ marginBottom: 20 }}>Verwaltung</h1>
        <nav
          className="row row-wrap"
          style={{
            gap: 6,
            marginBottom: 28,
            borderBottom: "1px solid var(--line)",
            paddingBottom: 0,
          }}
        >
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              end={t.end}
              style={({ isActive }) => ({
                padding: "10px 14px",
                fontWeight: 600,
                fontSize: "0.94rem",
                color: isActive ? "var(--red)" : "var(--text)",
                borderBottom: isActive ? "2px solid var(--red)" : "2px solid transparent",
                marginBottom: -1,
              })}
            >
              {t.label}
            </NavLink>
          ))}
        </nav>
        <Outlet />
      </div>
    </div>
  );
}
