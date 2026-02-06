import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  LayoutDashboard, 
  Package, 
  PlusCircle, 
  LogOut, 
  Menu, 
  X,
  Search,
  Globe,
  Shield,
  Users,
  ShoppingCart,
  Truck,
  Receipt,
  Wallet,
  Bell,
  Key,
  Smartphone,
  FolderTree,
  CreditCard,
  Settings,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  DollarSign
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Layout = ({ children }) => {
  const { t, language, toggleLanguage, isRTL } = useLanguage();
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed);
  }, [sidebarCollapsed]);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAllRead = async () => {
    try {
      await axios.put(`${API}/notifications/read-all`);
      setNotifications([]);
    } catch (error) {
      console.error('Error marking notifications:', error);
    }
  };

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
    { path: '/pos', icon: ShoppingCart, label: t.pos },
    { path: '/products', icon: Package, label: t.products },
    { path: '/sales', icon: Receipt, label: t.sales },
    { path: '/recharge', icon: Smartphone, label: t.recharge },
    { path: '/customers', icon: Users, label: t.customers },
    { path: '/customer-debts', icon: CreditCard, label: t.customerDebts },
    ...(isAdmin ? [
      { path: '/product-families', icon: FolderTree, label: t.productFamilies },
      { path: '/bulk-price-update', icon: DollarSign, label: t.bulkPriceUpdate },
      { path: '/suppliers', icon: Truck, label: t.suppliers },
      { path: '/employees', icon: Users, label: t.employees },
      { path: '/debts', icon: Receipt, label: t.debts },
      { path: '/cash', icon: Wallet, label: t.cashManagement },
      { path: '/reports', icon: LayoutDashboard, label: t.reports },
      { path: '/api-keys', icon: Key, label: t.apiKeys },
      { path: '/users', icon: Shield, label: t.users },
      { path: '/settings', icon: Settings, label: t.settings }
    ] : [])
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
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
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

          <div className="flex items-center gap-4 ms-6">
            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2 hover:bg-muted rounded-lg relative"
                data-testid="notifications-btn"
              >
                <Bell className="h-5 w-5" />
                {notifications.length > 0 && (
                  <span className="absolute top-0 right-0 h-5 w-5 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center">
                    {notifications.length}
                  </span>
                )}
              </button>
              
              {showNotifications && (
                <div className={`absolute top-12 ${isRTL ? 'left-0' : 'right-0'} w-80 bg-card border rounded-xl shadow-lg z-50`}>
                  <div className="p-4 border-b flex items-center justify-between">
                    <h3 className="font-semibold">{t.notifications}</h3>
                    {notifications.length > 0 && (
                      <button
                        onClick={markAllRead}
                        className="text-sm text-primary hover:underline"
                      >
                        {t.markAllRead}
                      </button>
                    )}
                  </div>
                  <div className="max-h-80 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <p className="p-4 text-center text-muted-foreground">{t.noNotifications}</p>
                    ) : (
                      notifications.map(notif => (
                        <div key={notif.id} className="p-4 border-b hover:bg-muted/50">
                          <p className="text-sm">
                            {language === 'ar' ? notif.message_ar : notif.message_en}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(notif.created_at).toLocaleString()}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Language Toggle */}
            <div className="flex items-center gap-2">
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
