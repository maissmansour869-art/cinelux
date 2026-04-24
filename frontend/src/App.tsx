import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { Clapperboard, LayoutDashboard, LogOut, ScanLine, Ticket, UserRound } from "lucide-react";
import { useAuth } from "./state/auth";
import CataloguePage from "./pages/CataloguePage";
import MoviePage from "./pages/MoviePage";
import BookingPage from "./pages/BookingPage";
import AccountPage from "./pages/AccountPage";
import StaffPage from "./pages/StaffPage";
import AdminPage from "./pages/AdminPage";
import AuthPage from "./pages/AuthPage";
import { initials } from "./utils";

function Guard({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/auth" replace />;
  if (roles && user && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/" className="brand" aria-label="CineLux home">
          <span className="brand-mark">CL</span>
          <span>
            <strong>CineLux</strong>
            <small>Premium cinema booking</small>
          </span>
        </NavLink>
        <nav className="topnav" aria-label="Primary">
          <NavLink to="/" end><Clapperboard size={17} /> Movies</NavLink>
          {isAuthenticated && <NavLink to="/account"><Ticket size={17} /> Bookings</NavLink>}
          {user?.role === "STAFF" || user?.role === "ADMIN" ? <NavLink to="/staff"><ScanLine size={17} /> Validate</NavLink> : null}
          {user?.role === "ADMIN" && <NavLink to="/admin"><LayoutDashboard size={17} /> Admin</NavLink>}
        </nav>
        <div className="session-chip">
          {isAuthenticated ? (
            <>
              <span className="avatar">{initials(user?.firstName, user?.lastName)}</span>
              <span>{user?.firstName ?? "Member"}</span>
              <button className="icon-button" onClick={logout} aria-label="Sign out"><LogOut size={17} /></button>
            </>
          ) : (
            <NavLink className="login-link" to="/auth"><UserRound size={17} /> Sign in</NavLink>
          )}
        </div>
      </header>
      <Routes>
        <Route path="/" element={<CataloguePage />} />
        <Route path="/movies/:movieId" element={<MoviePage />} />
        <Route path="/book/:showtimeId" element={<Guard><BookingPage /></Guard>} />
        <Route path="/account" element={<Guard><AccountPage /></Guard>} />
        <Route path="/staff" element={<Guard roles={["STAFF", "ADMIN"]}><StaffPage /></Guard>} />
        <Route path="/admin" element={<Guard roles={["ADMIN"]}><AdminPage /></Guard>} />
        <Route path="/auth" element={<AuthPage />} />
      </Routes>
    </div>
  );
}
