import { useState, useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Compass,
  LayoutDashboard,
  Briefcase,
  Waypoints,
  FolderOpen,
  ClipboardList,
  Bell,
  Award,
  LogOut,
  Landmark,
  Menu,
  X,
} from "lucide-react";
import { useApp } from "../context/AppContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/project", label: "My Project", icon: Briefcase },
  { to: "/roadmap", label: "Approval Roadmap", icon: Waypoints },
  { to: "/documents", label: "Documents", icon: FolderOpen },
  { to: "/applications", label: "Applications", icon: ClipboardList },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/schemes", label: "Schemes", icon: Award },
  { to: "/departments", label: "Departments to Contact", icon: Landmark },
];

export default function AppShell({ children, hideProfileBar }: { children: React.ReactNode; hideProfileBar?: boolean }) {
  const { user, logout, profile, alerts } = useApp();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  const unread = alerts.filter((a) => !a.read).length;

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
    navigate("/");
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center justify-between gap-2 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${
      isActive ? "bg-lavender text-navy" : "text-slate-soft hover:bg-mist hover:text-ink"
    }`;

  const SidebarContent = (
    <>
      <div className="mb-8 flex items-center gap-2 px-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy text-white">
          <Compass size={18} />
        </span>
        <span className="font-display text-lg font-bold tracking-tight text-navy">NIRVAAN</span>
      </div>

      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} className={navLinkClass} onClick={() => setMenuOpen(false)}>
            <span className="flex items-center gap-2.5">
              <item.icon size={17} />
              {item.label}
            </span>
            {item.to === "/alerts" && unread > 0 && (
              <span className="rounded-full bg-danger px-1.5 py-0.5 text-[10px] font-bold text-white">{unread}</span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-4 border-t border-navy/[0.06] pt-4">
        <div className="px-3 text-xs text-slate-soft">
          Signed in as
          <div className="truncate font-semibold text-ink">{user?.name || user?.email}</div>
        </div>
        <button
          onClick={handleLogout}
          className="mt-3 flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-semibold text-danger hover:bg-danger-light"
        >
          <LogOut size={17} />
          Logout
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-mist">
      <div className="flex">
        {/* Desktop sidebar */}
        <aside className="sticky top-0 hidden h-screen w-64 flex-col border-r border-navy/[0.06] bg-white px-4 py-6 md:flex">
          {SidebarContent}
        </aside>

        {/* Mobile slide-in drawer */}
        {menuOpen && (
          <div className="fixed inset-0 z-50 md:hidden">
            <div className="absolute inset-0 bg-ink/40" onClick={() => setMenuOpen(false)} />
            <aside className="absolute left-0 top-0 flex h-full w-72 max-w-[85vw] flex-col overflow-y-auto bg-white px-4 py-6 shadow-cardHover">
              <button
                onClick={() => setMenuOpen(false)}
                className="absolute right-3 top-3 rounded-lg p-2 text-slate-soft hover:bg-mist hover:text-ink"
                aria-label="Close menu"
              >
                <X size={18} />
              </button>
              {SidebarContent}
            </aside>
          </div>
        )}

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-navy/[0.06] bg-mist/85 px-4 py-3.5 backdrop-blur sm:px-6">
            <button
              onClick={() => setMenuOpen(true)}
              className="rounded-lg p-2 text-slate-soft hover:bg-white hover:text-navy md:hidden"
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
            <span className="flex items-center gap-2 md:hidden">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy text-white">
                <Compass size={15} />
              </span>
            </span>

            {!hideProfileBar && (
              <div className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto text-sm">
                {profile ? (
                  <>
                    <span className="pill flex-shrink-0 bg-navy/[0.06] text-navy">{profile.companyName}</span>
                    <span className="pill flex-shrink-0 bg-indigo/10 text-indigo">{profile.state}</span>
                    <span className="hidden pill flex-shrink-0 bg-saffron/10 text-saffron-dark sm:inline-flex">{profile.size}</span>
                    <span className="hidden pill flex-shrink-0 bg-success-light text-success sm:inline-flex">{profile.projectType}</span>
                  </>
                ) : (
                  <span className="text-sm text-slate-soft">No project selected yet</span>
                )}
              </div>
            )}
            {hideProfileBar && <div className="flex-1" />}
            <div className="flex flex-shrink-0 items-center gap-3">
              <button
                onClick={() => navigate("/alerts")}
                className="relative rounded-lg p-2 text-slate-soft hover:bg-white hover:text-navy"
              >
                <Bell size={19} />
                {unread > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-danger ring-2 ring-mist" />
                )}
              </button>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
