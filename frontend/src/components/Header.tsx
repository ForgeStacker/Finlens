import { Eye, LogOut, ChevronDown } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ThemeToggle } from "@/components/theme-toggle";

const navTabs = [
  { label: "Overview", path: "/" },
  { label: "Reports", path: "/reports" },
];

export function Header() {
  const { selectedAccount, selectedRegion, backToAccounts } = useAppStore();
  const location = useLocation();
  const navigate = useNavigate();

  const handleExit = () => {
    backToAccounts();
    navigate('/');
  };

  return (
    <header className="h-14 border-b border-border bg-card/80 backdrop-blur-md flex items-center justify-between px-4 z-50 sticky top-0">
      <div className="flex items-center gap-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
            <Eye className="w-5 h-5 text-primary" />
          </div>
          <span className="text-lg font-bold tracking-tight">
            Fin<span className="text-primary">Lens</span>
          </span>
        </Link>

        {/* Nav Tabs */}
        <nav className="flex items-center gap-1">
          {navTabs.map((tab) => {
            const isActive = location.pathname === tab.path;
            return (
              <Link
                key={tab.path}
                to={tab.path}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {/* Profile Context */}
        {selectedAccount && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-secondary text-sm">
            <span className="text-muted-foreground">{selectedAccount.name}</span>
            {selectedRegion && (
              <>
                <span className="text-muted-foreground/50">/</span>
                <span className="text-accent">{selectedRegion.code}</span>
              </>
            )}
            <ChevronDown className="w-3 h-3 text-muted-foreground" />
          </div>
        )}

        <ThemeToggle />
        <button 
          onClick={handleExit}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Exit</span>
        </button>
      </div>
    </header>
  );
}
