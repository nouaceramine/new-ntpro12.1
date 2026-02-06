import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { 
  LayoutDashboard, 
  Package, 
  PlusCircle, 
  LogOut, 
  Menu, 
  X,
  Search,
  Globe,
  Shield
} from 'lucide-react';

export const Layout = ({ children }) => {
  const { t, language, toggleLanguage, isRTL } = useLanguage();
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: t.dashboard },
    { path: '/products', icon: Package, label: t.products },
    ...(isAdmin ? [{ path: '/products/add', icon: PlusCircle, label: t.addProduct }] : [])
  ];

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 inset-x-0 z-50 bg-card/80 backdrop-blur-md border-b">
        <div className="flex items-center justify-between px-4 h-16">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 hover:bg-muted rounded-lg"
            data-testid="mobile-menu-btn"
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <h1 className="font-bold text-lg">{t.appName}</h1>
          
          <button
            onClick={toggleLanguage}
            className="p-2 hover:bg-muted rounded-lg"
            data-testid="mobile-lang-toggle"
          >
            <Globe className="h-5 w-5" />
          </button>
        </div>
      </header>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/50 z-50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`
          fixed top-0 ${isRTL ? 'right-0' : 'left-0'} z-50 h-full w-64 bg-card border-e
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : isRTL ? 'translate-x-full' : '-translate-x-full'}
          md:translate-x-0
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b">
            <div className="flex items-center gap-2">
              <Shield className="h-7 w-7 text-primary" />
              <span className="font-bold text-lg">{t.appName}</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="md:hidden p-1 hover:bg-muted rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                data-testid={`nav-${item.path.replace(/\//g, '-') || 'home'}`}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* User Info & Logout */}
          <div className="p-4 border-t">
            <div className="mb-3 px-2">
              <p className="font-medium truncate">{user?.name}</p>
              <p className="text-sm text-muted-foreground truncate">{user?.email}</p>
              {isAdmin && (
                <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">
                  Admin
                </span>
              )}
            </div>
            <Button
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={handleLogout}
              data-testid="logout-btn"
            >
              <LogOut className="h-4 w-4" />
              {t.logout}
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className={`md:${isRTL ? 'mr-64' : 'ml-64'}`}>
        {/* Desktop Header */}
        <header className="hidden md:flex items-center justify-between h-16 px-8 bg-card/80 backdrop-blur-md border-b sticky top-0 z-40">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex-1 max-w-xl">
            <div className="relative">
              <Search className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
              <input
                type="text"
                placeholder={t.searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`w-full h-11 ${isRTL ? 'pr-10 pl-4' : 'pl-10 pr-4'} rounded-lg border bg-background search-input focus:outline-none focus:ring-2 focus:ring-primary/20`}
                data-testid="search-input"
              />
            </div>
          </form>

          {/* Language Toggle */}
          <div className="flex items-center gap-2 ms-6">
            <button
              onClick={() => toggleLanguage()}
              className={`lang-btn ${language === 'en' ? 'active' : ''}`}
              data-testid="lang-en-btn"
            >
              EN
            </button>
            <button
              onClick={() => toggleLanguage()}
              className={`lang-btn ${language === 'ar' ? 'active' : ''}`}
              data-testid="lang-ar-btn"
            >
              عربي
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6 md:p-8 pt-20 md:pt-8">
          {children}
        </main>
      </div>
    </div>
  );
};
