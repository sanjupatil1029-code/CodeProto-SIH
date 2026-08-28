import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Compass, Menu, X } from "lucide-react";

export default function PublicNavbar() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-navy/[0.06] bg-mist/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2" onClick={() => setOpen(false)}>
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy text-white">
            <Compass size={18} />
          </span>
          <span className="font-display text-lg font-bold tracking-tight text-navy">NIRVAAN</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm font-semibold text-ink/80 md:flex">
          <Link to="/" className="hover:text-navy transition-colors">Home</Link>
          <Link to="/about" className="hover:text-navy transition-colors">About</Link>
          <Link to="/login" className="hover:text-navy transition-colors">Login</Link>
        </nav>
        <div className="flex items-center gap-2">
          <button onClick={() => navigate("/signup")} className="btn-accent !px-4 !py-2 text-sm">
            Sign Up
          </button>
          <button
            onClick={() => setOpen((v) => !v)}
            className="rounded-lg p-2 text-navy hover:bg-white md:hidden"
            aria-label={open ? "Close menu" : "Open menu"}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>
      {open && (
        <nav className="flex flex-col gap-1 border-t border-navy/[0.06] bg-white px-4 py-3 text-sm font-semibold text-ink/80 md:hidden">
          <Link to="/" onClick={() => setOpen(false)} className="rounded-lg px-2 py-2.5 hover:bg-mist hover:text-navy">Home</Link>
          <Link to="/about" onClick={() => setOpen(false)} className="rounded-lg px-2 py-2.5 hover:bg-mist hover:text-navy">About</Link>
          <Link to="/login" onClick={() => setOpen(false)} className="rounded-lg px-2 py-2.5 hover:bg-mist hover:text-navy">Login</Link>
        </nav>
      )}
    </header>
  );
}
