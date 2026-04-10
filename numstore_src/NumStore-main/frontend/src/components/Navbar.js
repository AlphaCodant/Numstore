import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="glass-nav sticky top-0 z-50" data-testid="navbar">
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3 group" data-testid="nav-logo">
            <div className="w-8 h-8 bg-champagne flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-noir" strokeWidth={1.5} />
            </div>
            <span className="font-heading text-xl font-semibold tracking-tight text-white group-hover:text-champagne transition-colors">
              NumStore
            </span>
          </Link>

          <div className="flex items-center gap-6">
            <Link
              to="/access"
              className="text-sm font-medium text-zinc-400 hover:text-champagne transition-colors tracking-wide"
              data-testid="nav-access"
            >
              J'ai un code
            </Link>
            <Link
              to="/admin"
              className="text-sm font-medium text-zinc-500 hover:text-zinc-300 transition-colors"
              data-testid="nav-admin"
            >
              Admin
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
