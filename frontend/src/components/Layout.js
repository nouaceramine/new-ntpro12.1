import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
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
  DollarSign,
  ShoppingBag,
  BarChart3,
  ChevronDown,
  Warehouse,
  ClipboardList,
  QrCode,
  Clock,
  Store,
  Zap,
  Award,
  Moon,
  Sun,
  Wrench,
  Download
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Layout = ({ children }) => {
  const { t, language, toggleLanguage, isRTL } = useLanguage();
  const { user, logout, isAdmin } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  });
  const [expandedSections, setExpandedSections] = useState(() => {
    const saved = localStorage.getItem('expandedSections');
    return saved ? JSON.parse(saved) : ['الرئيسية', 'Principal', 'المالية', 'Finances'];
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallBtn, setShowInstallBtn] = useState(false);

  // Listen for PWA install prompt
  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallBtn(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    
    // Check if app is already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setShowInstallBtn(false);
    }
    
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setShowInstallBtn(false);
    }
    setDeferredPrompt(null);
  };


  const toggleSection = (sectionTitle) => {
    setExpandedSections(prev => {
      const newExpanded = prev.includes(sectionTitle)
        ? prev.filter(s => s !== sectionTitle)
        : [...prev, sectionTitle];
      localStorage.setItem('expandedSections', JSON.stringify(newExpanded));
      return newExpanded;
    });
  };

  const fetchNotifications = async () => {
    try {
      // Generate automatic notifications first
      await axios.post(`${API}/notifications/generate`).catch(() => {});
      // Then fetch all notifications
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed);
  }, [sidebarCollapsed]);

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

  const navSections = [
    {
      title: language === 'ar' ? 'الرئيسية' : 'Principal',
      icon: LayoutDashboard,
      items: [
        { path: '/', icon: LayoutDashboard, label: t.dashboard },
      ]
    },
    {
      title: language === 'ar' ? 'المخزون' : 'Stock',
      icon: Package,
      items: [
        { path: '/products', icon: Package, label: t.products },
        ...(isAdmin ? [
          { path: '/product-families', icon: FolderTree, label: t.productFamilies },
          { path: '/warehouses', icon: Warehouse, label: language === 'ar' ? 'المخازن' : 'Entrepôts' },
          { path: '/inventory-count', icon: ClipboardList, label: language === 'ar' ? 'جرد المخزون' : 'Inventaire' },
          { path: '/barcode-print', icon: QrCode, label: language === 'ar' ? 'طباعة الباركود' : 'Codes-barres' },
          { path: '/bulk-price-update', icon: DollarSign, label: t.bulkPriceUpdate },
        ] : [])
      ]
    },
    {
      title: language === 'ar' ? 'المالية' : 'Finances',
      icon: Wallet,
      items: [
        { path: '/pos', icon: ShoppingCart, label: t.pos },
        { path: '/daily-sessions', icon: Clock, label: language === 'ar' ? 'حصص البيع اليومية' : 'Sessions journalières' },
        { path: '/sales', icon: Receipt, label: t.sales },
        { path: '/purchases', icon: ShoppingBag, label: t.purchases },
        ...(isAdmin ? [
          { path: '/cash', icon: Wallet, label: t.cashManagement },
          { path: '/customer-debts', icon: CreditCard, label: t.customerDebts },
          { path: '/debts', icon: Receipt, label: t.debts },
        ] : [
          { path: '/customer-debts', icon: CreditCard, label: t.customerDebts },
        ])
      ]
    },
    {
      title: language === 'ar' ? 'العلاقات' : 'Relations',
      icon: Users,
      items: [
        { path: '/customers', icon: Users, label: t.customers },
        ...(isAdmin ? [
          { path: '/customer-families', icon: FolderTree, label: language === 'ar' ? 'عائلات الزبائن' : 'Familles clients' },
          { path: '/suppliers', icon: Truck, label: t.suppliers },
          { path: '/supplier-families', icon: FolderTree, label: language === 'ar' ? 'عائلات الموردين' : 'Familles fournisseurs' },
          { path: '/employees', icon: Users, label: t.employees },
        ] : [])
      ]
    },
    {
      title: language === 'ar' ? 'الصيانة' : 'Réparations',
      icon: Wrench,
      items: [
        { path: '/repairs', icon: ClipboardList, label: language === 'ar' ? 'تتبع الصيانة' : 'Suivi réparations' },
        { path: '/repairs/new', icon: Smartphone, label: language === 'ar' ? 'استقبال جهاز' : 'Réception appareil' },
        { path: '/repairs/parts', icon: Package, label: language === 'ar' ? 'قطع الغيار' : 'Pièces de rechange' },
      ]
    },
    {
      title: language === 'ar' ? 'الخدمات' : 'Services',
      icon: Smartphone,
      items: [
        { path: '/services', icon: Store, label: language === 'ar' ? 'الصفحة الرئيسية' : 'Accueil services' },
        { path: '/services/flexy', icon: Smartphone, label: language === 'ar' ? 'فليكسي' : 'Flexy' },
        { path: '/services/idoom', icon: Zap, label: language === 'ar' ? 'تعبئة أيدوم' : 'Recharge Idoom' },
        { path: '/services/cards', icon: CreditCard, label: language === 'ar' ? 'بطاقات' : 'Cartes' },
        { path: '/services/operations', icon: Clock, label: language === 'ar' ? 'كل العمليات' : 'Opérations' },
        { path: '/services/profits', icon: DollarSign, label: language === 'ar' ? 'نسب الأرباح' : 'Taux profits' },
        { path: '/services/transfers', icon: Receipt, label: language === 'ar' ? 'التحويلات' : 'Transferts' },
        { path: '/services/directory', icon: Users, label: language === 'ar' ? 'دليل الهاتف' : 'Annuaire' },
        { path: '/recharge', icon: Smartphone, label: t.recharge },
        ...(isAdmin ? [
          { path: '/sim-management', icon: Zap, label: language === 'ar' ? 'إدارة الشرائح' : 'Gestion SIM' },
        ] : [])
      ]
    },
    ...(isAdmin ? [{
      title: 'WooCommerce',
      icon: Store,
      items: [
        { path: '/woocommerce', icon: Store, label: 'WooCommerce' },
      ]
    }] : []),
    ...(isAdmin ? [{
      title: language === 'ar' ? 'التوصيل' : 'Livraison',
      icon: Truck,
      items: [
        { path: '/shipping', icon: Truck, label: language === 'ar' ? 'شركات الشحن' : 'Transporteurs' },
      ]
    }] : []),
    ...(isAdmin ? [{
      title: language === 'ar' ? 'الإدارة' : 'Administration',
      icon: Settings,
      items: [
        { path: '/reports', icon: BarChart3, label: t.reports },
        { path: '/analytics', icon: BarChart3, label: language === 'ar' ? 'إحصائيات متقدمة' : 'Analyses avancées' },
        { path: '/loyalty', icon: Award, label: language === 'ar' ? 'الولاء والتسويق' : 'Fidélité' },
        { path: '/users', icon: Shield, label: t.users },
        { path: '/api-keys', icon: Key, label: t.apiKeys },
        { path: '/settings', icon: Settings, label: t.settings },
      ]
    }] : [])
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
          
          <div className="flex items-center gap-1">
            <button
              onClick={toggleTheme}
              className="p-2 hover:bg-muted rounded-lg"
              data-testid="mobile-theme-toggle"
            >
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            <button
              onClick={toggleLanguage}
              className="p-2 hover:bg-muted rounded-lg"
              data-testid="mobile-lang-toggle"
            >
              <Globe className="h-5 w-5" />
            </button>
          </div>
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
          fixed top-0 ${isRTL ? 'right-0' : 'left-0'} z-50 h-full bg-card border-e
          transform transition-all duration-300 ease-in-out
          ${sidebarCollapsed ? 'w-16' : 'w-64'}
          ${sidebarOpen ? 'translate-x-0' : isRTL ? 'translate-x-full' : '-translate-x-full'}
          md:translate-x-0
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className={`flex items-center justify-between h-16 border-b ${sidebarCollapsed ? 'px-2' : 'px-6'}`}>
            <div className="flex items-center gap-2">
              <Shield className="h-7 w-7 text-primary flex-shrink-0" />
              {!sidebarCollapsed && <span className="font-bold text-lg">{t.appName}</span>}
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="md:hidden p-1 hover:bg-muted rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Collapse Toggle - Desktop Only */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden md:flex items-center justify-center h-10 border-b hover:bg-muted transition-colors"
            title={sidebarCollapsed ? t.expandSidebar : t.collapseSidebar}
          >
            {sidebarCollapsed ? (
              isRTL ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />
            ) : (
              isRTL ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />
            )}
            {!sidebarCollapsed && (
              <span className="text-sm text-muted-foreground ms-2">{t.collapseSidebar}</span>
            )}
          </button>

          {/* Navigation */}
          <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
            {navSections.map((section) => (
              <div key={section.title} className="mb-2">
                {/* Section Header */}
                {!sidebarCollapsed && (
                  <button
                    onClick={() => toggleSection(section.title)}
                    className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider hover:bg-muted/50 rounded-lg transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <section.icon className="h-4 w-4" />
                      <span>{section.title}</span>
                    </div>
                    <ChevronDown className={`h-4 w-4 transition-transform ${expandedSections.includes(section.title) ? 'rotate-180' : ''}`} />
                  </button>
                )}
                
                {/* Section Items */}
                {(sidebarCollapsed || expandedSections.includes(section.title)) && (
                  <div className={`space-y-1 ${!sidebarCollapsed ? 'mt-1 ms-2' : ''}`}>
                    {section.items.map((item) => (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                          isActive(item.path) 
                            ? 'bg-primary text-primary-foreground' 
                            : 'hover:bg-muted'
                        } ${sidebarCollapsed ? 'justify-center' : ''}`}
                        data-testid={`nav-${item.path.replace(/\//g, '-') || 'home'}`}
                        title={sidebarCollapsed ? item.label : ''}
                      >
                        <item.icon className="h-5 w-5 flex-shrink-0" />
                        {!sidebarCollapsed && <span className="truncate text-sm">{item.label}</span>}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* User Info & Logout */}
          <div className={`p-2 border-t ${sidebarCollapsed ? 'px-2' : 'p-4'}`}>
            {!sidebarCollapsed && (
              <div className="mb-3 px-2">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-sm text-muted-foreground truncate">{user?.email}</p>
                {isAdmin && (
                  <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">
                    Admin
                  </span>
                )}
              </div>
            )}
            <Button
              variant="outline"
              className={`w-full gap-2 ${sidebarCollapsed ? 'justify-center px-2' : 'justify-start'}`}
              onClick={handleLogout}
              data-testid="logout-btn"
              title={sidebarCollapsed ? t.logout : ''}
            >
              <LogOut className="h-4 w-4 flex-shrink-0" />
              {!sidebarCollapsed && t.logout}
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'md:ms-16' : 'md:ms-64'}`}>
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
                          <p className="font-medium text-sm mb-1">
                            {language === 'ar' ? (notif.title || notif.title_ar) : (notif.title_fr || notif.title_en || notif.title)}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {language === 'ar' ? (notif.message || notif.message_ar) : (notif.message_fr || notif.message_en || notif.message)}
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
                className={`lang-btn ${language === 'fr' ? 'active' : ''}`}
                data-testid="lang-fr-btn"
              >
                FR
              </button>
              <button
                onClick={() => toggleLanguage()}
                className={`lang-btn ${language === 'ar' ? 'active' : ''}`}
                data-testid="lang-ar-btn"
              >
                عربي
              </button>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
              data-testid="theme-toggle-btn"
              title={isDark ? (language === 'ar' ? 'الوضع الفاتح' : 'Mode clair') : (language === 'ar' ? 'الوضع المظلم' : 'Mode sombre')}
            >
              {isDark ? (
                <Sun className="h-5 w-5 text-amber-500" />
              ) : (
                <Moon className="h-5 w-5 text-slate-600" />
              )}
            </button>

            {/* Install App Button */}
            {showInstallBtn && (
              <button
                onClick={handleInstallClick}
                className="p-2 hover:bg-muted rounded-lg transition-colors flex items-center gap-2 bg-primary/10 text-primary"
                data-testid="install-app-btn"
                title={language === 'ar' ? 'تثبيت التطبيق' : 'Installer l\'app'}
              >
                <Download className="h-5 w-5" />
                <span className="hidden lg:inline text-sm font-medium">
                  {language === 'ar' ? 'تثبيت' : 'Installer'}
                </span>
              </button>
            )}
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
