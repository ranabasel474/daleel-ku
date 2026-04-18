import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Database,
  MessageSquare,
  LogOut,
  Menu,
  X,
  Settings,
  ChevronUp,
  LayoutDashboard,
} from 'lucide-react';
import AcademicBotLogo from '@/components/AcademicBotLogo';

const navItems = [
  { title: 'Dashboard', path: '/admin', icon: LayoutDashboard },
  { title: 'Content Management', path: '/admin/knowledge', icon: Database },
  { title: 'Query Logs', path: '/admin/queries', icon: MessageSquare },
];

//Props for AdminLayout
interface AdminLayoutProps {
  children: React.ReactNode;
}

//Persistent layout for all admin pages
const AdminLayout = ({ children }: AdminLayoutProps) => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  //Close profile menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="h-dvh flex bg-background" dir="ltr">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-foreground/20 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        dir="ltr"
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-primary text-primary-foreground flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-primary-foreground/10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary-foreground/15 flex items-center justify-center">
              <AcademicBotLogo size={20} animated={false} />
            </div>
            <div>
              <h1 className="text-sm font-bold leading-tight">Daleel KU</h1>
              <p className="text-[11px] text-primary-foreground/60">Admin Panel</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 hover:bg-primary-foreground/10 rounded"
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-foreground/15 font-semibold'
                    : 'text-primary-foreground/70 hover:bg-primary-foreground/10 hover:text-primary-foreground'
                }`}
              >
                <item.icon size={18} />
                <span>{item.title}</span>
              </Link>
            );
          })}
        </nav>

        {/* Profile section */}
        <div className="p-3 border-t border-primary-foreground/10" ref={profileRef}>
          {/* Popover menu */}
          {profileOpen && (
            <div className="mb-2 bg-card text-card-foreground rounded-lg shadow-lg border border-border overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-150">
              <Link
                to="/admin/settings"
                onClick={() => { setProfileOpen(false); setSidebarOpen(false); }}
                className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-secondary transition-colors"
              >
                <Settings size={16} className="text-muted-foreground" />
                <span>Settings</span>
              </Link>
              <Link
                to="/admin/login"
                onClick={() => { setProfileOpen(false); setSidebarOpen(false); }}
                className="flex items-center gap-3 px-4 py-2.5 text-sm text-destructive hover:bg-destructive/10 transition-colors"
              >
                <LogOut size={16} />
                <span>Logout</span>
              </Link>
            </div>
          )}

          {/* Profile button */}
          <button
            onClick={() => setProfileOpen((prev) => !prev)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-primary-foreground/10 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-accent text-accent-foreground flex items-center justify-center text-xs font-bold shrink-0">
              AD
            </div>
            <span className="text-sm font-medium flex-1 text-left">admin</span>
            <ChevronUp
              size={16}
              className={`text-primary-foreground/50 transition-transform duration-200 ${profileOpen ? '' : 'rotate-180'}`}
            />
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-14 bg-card border-b border-border flex items-center justify-between px-4 lg:px-6 shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 -ml-2 text-muted-foreground hover:text-foreground"
            >
              <Menu size={20} />
            </button>
            <div className="text-sm font-medium text-foreground">
              Daleel KU Admin Panel
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
};

export default AdminLayout;
