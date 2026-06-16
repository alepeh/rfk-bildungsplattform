import { Routes, Route, Navigate } from "react-router";
import type { ReactNode } from "react";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui";
import { useAuth } from "./auth";

import { Home } from "./routes/Home";
import { Course } from "./routes/Course";
import { Login } from "./routes/Login";
import { Register } from "./routes/Register";
import { RegistrationSuccess } from "./routes/RegistrationSuccess";
import { MyCourses } from "./routes/MyCourses";
import { Orders } from "./routes/Orders";
import { OrderConfirmation } from "./routes/OrderConfirmation";
import { Documents } from "./routes/Documents";
import { Mitarbeiter } from "./routes/Mitarbeiter";
import { Account } from "./routes/Account";
import { Impressum, AGB } from "./routes/Static";
import { AdminLayout } from "./routes/admin/AdminLayout";
import { AdminDashboard } from "./routes/admin/Dashboard";
import { AdminPersonen } from "./routes/admin/Personen";
import { AdminSchulungen } from "./routes/admin/Schulungen";
import { AdminTermine } from "./routes/admin/Termine";
import { AdminTeilnehmer } from "./routes/admin/Teilnehmer";
import { AdminDokumente } from "./routes/admin/Dokumente";
import { AdminTodos } from "./routes/admin/Todos";

function RequireAuth({ children, staff }: { children: ReactNode; staff?: boolean }) {
  const { me, loading } = useAuth();
  if (loading) return <Spinner center />;
  if (!me) return <Navigate to="/login" replace />;
  if (staff && !me.is_staff) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/schulung/:id" element={<Course />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registrieren" element={<Register />} />
        <Route path="/registrierung-erfolgreich" element={<RegistrationSuccess />} />
        <Route path="/impressum" element={<Impressum />} />
        <Route path="/agb" element={<AGB />} />

        <Route path="/meine-schulungen" element={<RequireAuth><MyCourses /></RequireAuth>} />
        <Route path="/bestellungen" element={<RequireAuth><Orders /></RequireAuth>} />
        <Route path="/bestellung/:id" element={<RequireAuth><OrderConfirmation /></RequireAuth>} />
        <Route path="/dokumente" element={<RequireAuth><Documents /></RequireAuth>} />
        <Route path="/mitarbeiter" element={<RequireAuth><Mitarbeiter /></RequireAuth>} />
        <Route path="/konto" element={<RequireAuth><Account /></RequireAuth>} />

        <Route path="/admin" element={<RequireAuth staff><AdminLayout /></RequireAuth>}>
          <Route index element={<AdminDashboard />} />
          <Route path="personen" element={<AdminPersonen />} />
          <Route path="schulungen" element={<AdminSchulungen />} />
          <Route path="termine" element={<AdminTermine />} />
          <Route path="termine/:id/teilnehmer" element={<AdminTeilnehmer />} />
          <Route path="dokumente" element={<AdminDokumente />} />
          <Route path="todos" element={<AdminTodos />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
