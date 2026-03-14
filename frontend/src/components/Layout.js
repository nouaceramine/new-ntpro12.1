import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { NotificationBell } from './NotificationBell';
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
  ChevronDown,
  ChevronUp,
  PanelLeftClose,
  PanelLeft,
  DollarSign,
  ShoppingBag,
  BarChart3,
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
  Download,
  Sparkles,
  History,
  Building,
  Mail,
  MessageSquare,
  Coins,
  FileText,
  Landmark,
  Bot,
  PackageX,
  Database,
  CheckSquare,
  MessageCircle
} from 'lucide-react';
import { UnifiedSearch } from './UnifiedSearch';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Helper function to determine AI context based on current page
const getAIContext = (pathname) => {
  if (pathname.includes('/pos') || pathname.includes('/sales')) return 'sales';
  if (pathname.includes('/products') || pathname.includes('/inventory') || pathname.includes('/warehouses')) return 'inventory';
  if (pathname.includes('/customers')) return 'customers';
  if (pathname.includes('/reports') || pathname.includes('/analytics')) return 'reports';
  if (pathname.includes('/suppliers') || pathname.includes('/purchases')) return 'suppliers';
  return 'general';
};

// Icon mapping for dynamic sidebar
const iconMap = {
  LayoutDashboard, Package, ShoppingCart, Truck, Users, CreditCard, Wallet,
  BarChart3, Settings, Bell, Wrench, Receipt, FolderTree, Warehouse,
  ClipboardList, QrCode, DollarSign, ShoppingBag, Clock, Smartphone, Store, Shield, Key, Award, Zap, Mail, Bot,
  PackageX, Database, CheckSquare, MessageCircle, Download
};

export const Layout = ({ children }) => {
  const { t, language, toggleLanguage, isRTL } = useLanguage();
  // Get user type and features
  const { user, logout, isAdmin, isSuperAdmin, isTenant, isFeatureEnabled } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    // Default to collapsed (true) if no saved preference
    return saved !== null ? saved === 'true' : true;
  });
  const [expandedSections, setExpandedSections] = useState(() => {
    const saved = localStorage.getItem('expandedSections');
    return saved ? JSON.parse(saved) : ['الرئيسية', 'Principal', 'المالية', 'Finances'];
  });
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallBtn, setShowInstallBtn] = useState(false);
  const [customSidebarOrder, setCustomSidebarOrder] = useState(null);

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

  // Fetch custom sidebar order
  useEffect(() => {
    const fetchSidebarOrder = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await axios.get(`${API}/settings/sidebar-order`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.sidebar_order && Array.isArray(response.data.sidebar_order) && response.data.sidebar_order.length > 0) {
          if (response.data.sidebar_order[0].items) {
            setCustomSidebarOrder(response.data.sidebar_order);
          }
        }
      } catch (error) {
        console.error('Error fetching sidebar order:', error);
      }
    };
    
    fetchSidebarOrder();
    
    // Listen for sidebar order changes from settings page
    const handleSidebarOrderChange = () => fetchSidebarOrder();
    window.addEventListener('sidebarOrderChanged', handleSidebarOrderChange);
    
    return () => window.removeEventListener('sidebarOrderChanged', handleSidebarOrderChange);
  }, []);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // If we have native prompt, use it
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        setShowInstallBtn(false);
      }
      setDeferredPrompt(null);
    } else {
      // Show manual instructions
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const isAndroid = /Android/.test(navigator.userAgent);
      
      if (isIOS) {
        toast.info(language === 'ar' 
          ? 'اضغط على زر المشاركة ثم "إضافة إلى الشاشة الرئيسية"'
          : 'Appuyez sur Partager puis "Ajouter à l\'écran d\'accueil"'
        );
      } else if (isAndroid) {
        toast.info(language === 'ar'
          ? 'اضغط على القائمة ⋮ ثم "إضافة إلى الشاشة الرئيسية"'
          : 'Appuyez sur le menu ⋮ puis "Ajouter à l\'écran d\'accueil"'
        );
      } else {
        toast.info(language === 'ar'
          ? 'يمكنك تثبيت التطبيق من إعدادات المتصفح'
          : 'Vous pouvez installer l\'app depuis les paramètres du navigateur'
        );
      }
    }
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

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Super Admin sees only SaaS management
  const superAdminNavSections = [
    {
      id: 'saas',
      title: 'NT Commerce',
      icon: Building,
      items: [
        { path: '/saas-admin', icon: Building, label: language === 'ar' ? 'لوحة تحكم SaaS' : 'SaaS Dashboard' },
        { path: '/saas-admin/feature-flags', icon: Shield, label: language === 'ar' ? 'إدارة الميزات' : 'Feature Flags' },
        { path: '/system-updates', icon: Bell, label: language === 'ar' ? 'تحديثات النظام' : 'Mises à jour système' },
        { path: '/security-dashboard', icon: Shield, label: language === 'ar' ? 'لوحة الأمان' : 'Sécurité' },
        { path: '/backup-system', icon: Database, label: language === 'ar' ? 'النسخ الاحتياطي' : 'Sauvegardes' },
        { path: '/wallet-management', icon: Wallet, label: language === 'ar' ? 'المحافظ' : 'Portefeuilles' },
      ]
    }
  ];

  // Default nav sections for Tenants and regular users
  // Each section has a featureKey that maps to the feature flags
  const tenantNavSections = [
    {
      id: 'main',
      featureKey: null, // Always visible
      title: language === 'ar' ? 'الرئيسية' : 'Principal',
      icon: LayoutDashboard,
      items: [
        { path: '/', icon: LayoutDashboard, label: t.dashboard },
      ]
    },
    {
      id: 'inventory',
      featureKey: 'inventory',
      title: language === 'ar' ? 'المخزون' : 'Stock',
      icon: Package,
      items: [
        { path: '/products', icon: Package, label: t.products, subFeature: 'products' },
        { path: '/product-families', icon: FolderTree, label: t.productFamilies, subFeature: 'categories' },
        { path: '/warehouses', icon: Warehouse, label: language === 'ar' ? 'المخازن' : 'Entrepôts', subFeature: 'warehouses' },
        { path: '/inventory-count', icon: ClipboardList, label: language === 'ar' ? 'جرد المخزون' : 'Inventaire', subFeature: 'inventory_count' },
        { path: '/barcode-print', icon: QrCode, label: language === 'ar' ? 'طباعة الباركود' : 'Codes-barres', subFeature: 'barcode' },
        { path: '/bulk-price-update', icon: DollarSign, label: t.bulkPriceUpdate },
        { path: '/price-history', icon: History, label: language === 'ar' ? 'سجل الأسعار' : 'Historique prix' },
      ]
    },
    {
      id: 'purchases',
      featureKey: 'purchases',
      title: language === 'ar' ? 'المشتريات' : 'Achats',
      icon: ShoppingBag,
      items: [
        { path: '/purchases', icon: ShoppingBag, label: t.purchases, subFeature: 'purchase_orders' },
        { path: '/suppliers', icon: Truck, label: t.suppliers, subFeature: 'suppliers' },
        { path: '/supplier-families', icon: FolderTree, label: language === 'ar' ? 'عائلات الموردين' : 'Familles fournisseurs' },
      ]
    },
    {
      id: 'customers',
      featureKey: 'customers',
      title: language === 'ar' ? 'الزبائن' : 'Clients',
      icon: Users,
      items: [
        { path: '/customers', icon: Users, label: t.customers, subFeature: 'customer_list' },
        { path: '/customer-families', icon: FolderTree, label: language === 'ar' ? 'عائلات الزبائن' : 'Familles clients', subFeature: 'customer_families' },
        { path: '/customer-debts', icon: CreditCard, label: t.customerDebts, subFeature: 'customer_debts' },
      ]
    },
    {
      id: 'sales',
      featureKey: 'sales',
      title: language === 'ar' ? 'المبيعات' : 'Ventes',
      icon: Receipt,
      items: [
        { path: '/pos', icon: ShoppingCart, label: t.pos, subFeature: 'pos' },
        { path: '/daily-sessions', icon: Clock, label: language === 'ar' ? 'حصص البيع اليومية' : 'Sessions journalières' },
        { path: '/sales', icon: Receipt, label: t.sales, subFeature: 'invoices' },
        { path: '/sales/advanced-report', icon: BarChart3, label: language === 'ar' ? 'تقارير متقدمة' : 'Rapports avancés' },
      ]
    },
    {
      id: 'reports',
      featureKey: 'reports',
      title: language === 'ar' ? 'التقارير' : 'Rapports',
      icon: BarChart3,
      items: [
        { path: '/reports', icon: BarChart3, label: t.reports, subFeature: 'sales_reports' },
        { path: '/analytics', icon: BarChart3, label: language === 'ar' ? 'إحصائيات متقدمة' : 'Analyses avancées', subFeature: 'financial_reports' },
        { path: '/smart-reports', icon: Sparkles, label: language === 'ar' ? 'تقارير ذكية' : 'Rapports intelligents', subFeature: 'smart_reports' },
      ]
    },
    {
      id: 'ai',
      featureKey: null, // Always visible - AI features
      title: language === 'ar' ? 'الذكاء الاصطناعي' : 'Intelligence Artificielle',
      icon: Sparkles,
      items: [
        { path: '/smart-dashboard', icon: LayoutDashboard, label: language === 'ar' ? 'لوحة التحكم الذكية' : 'Dashboard Intelligent' },
        { path: '/ai-chat', icon: Sparkles, label: language === 'ar' ? 'المحاسب الذكي' : 'Comptable IA' },
        { path: '/ai-agents', icon: Zap, label: language === 'ar' ? 'الوكلاء الذكيين' : 'Agents IA' },
        { path: '/robots', icon: Bot, label: language === 'ar' ? 'الروبوتات الذكية' : 'Smart Robots' },
      ]
    },
    {
      id: 'finance',
      featureKey: null,
      title: language === 'ar' ? 'المالية والضرائب' : 'Finance & Taxes',
      icon: FileText,
      items: [
        { path: '/tax-reports', icon: FileText, label: language === 'ar' ? 'التقارير الضريبية' : 'Tax Reports' },
        { path: '/currencies', icon: Coins, label: language === 'ar' ? 'العملات' : 'Currencies' },
        { path: '/banking', icon: Landmark, label: language === 'ar' ? 'التكامل البنكي' : 'Banking' },
      ]
    },
    {
      id: 'integrations',
      featureKey: null,
      title: language === 'ar' ? 'التكاملات' : 'Integrations',
      icon: MessageSquare,
      items: [
        { path: '/whatsapp', icon: MessageSquare, label: language === 'ar' ? 'WhatsApp Business' : 'WhatsApp Business' },
      ]
    },
    {
      id: 'notifications',
      featureKey: 'notifications',
      title: language === 'ar' ? 'الإشعارات' : 'Notifications',
      icon: Bell,
      items: [
        { path: '/notifications', icon: Bell, label: language === 'ar' ? 'الإشعارات' : 'Notifications', subFeature: 'push_notifications' },
        { path: '/smart-notifications', icon: Bell, label: language === 'ar' ? 'الإشعارات الذكية' : 'Smart Notifications' },
        { path: '/email-notifications', icon: Mail, label: language === 'ar' ? 'إشعارات البريد' : 'Email Notifications', subFeature: 'email_notifications' },
      ]
    },
    {
      id: 'payments',
      featureKey: null, // Always visible
      title: language === 'ar' ? 'المدفوعات' : 'Payments',
      icon: CreditCard,
      items: [
        { path: '/payments', icon: CreditCard, label: language === 'ar' ? 'إدارة المدفوعات' : 'Payments Management' },
      ]
    },
    {
      id: 'loyalty',
      featureKey: null, // Always visible
      title: language === 'ar' ? 'الولاء والتسويق' : 'Fidélité & Marketing',
      icon: Award,
      items: [
        { path: '/loyalty', icon: Award, label: language === 'ar' ? 'برنامج الولاء' : 'Programme fidélité' },
      ]
    },
    {
      id: 'ecommerce',
      featureKey: 'ecommerce',
      title: language === 'ar' ? 'المتجر الإلكتروني' : 'E-Commerce',
      icon: Store,
      items: [
        { path: '/store', icon: Store, label: language === 'ar' ? 'إدارة المتجر' : 'Store Management', subFeature: 'online_store' },
      ]
    },
    {
      id: 'administration',
      featureKey: null, // Always visible
      title: language === 'ar' ? 'الإدارة' : 'Administration',
      icon: Settings,
      items: [
        { path: '/cash', icon: Wallet, label: t.cashManagement },
        { path: '/expenses', icon: Receipt, label: language === 'ar' ? 'التكاليف' : 'Dépenses' },
        { path: '/debts', icon: Receipt, label: t.debts },
        { path: '/employees', icon: Users, label: language === 'ar' ? 'الموظفين' : 'Employés' },
        { path: '/employee-alerts', icon: Bell, label: language === 'ar' ? 'تنبيهات الحدود' : 'Alertes limites' },
        { path: '/users', icon: Shield, label: language === 'ar' ? 'المستخدمين' : 'Utilisateurs' },
        { path: '/permissions', icon: Shield, label: language === 'ar' ? 'الصلاحيات' : 'Permissions' },
        { path: '/settings/sales-permissions', icon: Shield, label: language === 'ar' ? 'صلاحيات المبيعات' : 'Permissions ventes' },
      ]
    },
    {
      id: 'repairs',
      featureKey: 'repairs',
      title: language === 'ar' ? 'الصيانة' : 'Réparations',
      icon: Wrench,
      items: [
        { path: '/repairs', icon: ClipboardList, label: language === 'ar' ? 'تتبع الصيانة' : 'Suivi réparations', subFeature: 'repair_tickets' },
        { path: '/repairs/new', icon: Smartphone, label: language === 'ar' ? 'استقبال جهاز' : 'Réception appareil' },
        { path: '/defective-goods', icon: PackageX, label: language === 'ar' ? 'البضائع المعيبة' : 'Produits défectueux' },
      ]
    },
    {
      id: 'supplier-tracking',
      featureKey: null,
      title: language === 'ar' ? 'تتبع الموردين' : 'Suivi Fournisseurs',
      icon: Truck,
      items: [
        { path: '/supplier-tracking', icon: Truck, label: language === 'ar' ? 'تتبع الموردين' : 'Suivi fournisseurs' },
      ]
    },
    {
      id: 'tasks-chat',
      featureKey: null,
      title: language === 'ar' ? 'المهام والتواصل' : 'Tâches & Communication',
      icon: CheckSquare,
      items: [
        { path: '/task-management', icon: CheckSquare, label: language === 'ar' ? 'إدارة المهام' : 'Gestion tâches' },
        { path: '/internal-chat', icon: MessageCircle, label: language === 'ar' ? 'الدردشة الداخلية' : 'Chat interne' },
      ]
    },
    {
      id: 'system-tools',
      featureKey: null,
      title: language === 'ar' ? 'أدوات النظام' : 'Outils Système',
      icon: Database,
      items: [
        { path: '/backup-system', icon: Database, label: language === 'ar' ? 'النسخ الاحتياطي' : 'Sauvegardes' },
        { path: '/wallet-management', icon: Wallet, label: language === 'ar' ? 'المحفظة' : 'Portefeuille' },
        { path: '/two-factor', icon: Shield, label: language === 'ar' ? 'المصادقة الثنائية' : '2FA' },
      ]
    },
    {
      id: 'services',
      featureKey: null, // Always visible
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
      id: 'woocommerce',
      featureKey: 'ecommerce',
      title: 'WooCommerce',
      icon: Store,
      items: [
        { path: '/woocommerce', icon: Store, label: 'WooCommerce', subFeature: 'woocommerce' },
      ]
    }] : []),
    ...(isAdmin ? [{
      id: 'shipping',
      featureKey: 'delivery',
      title: language === 'ar' ? 'التوصيل' : 'Livraison',
      icon: Truck,
      items: [
        { path: '/shipping', icon: Truck, label: language === 'ar' ? 'شركات الشحن' : 'Transporteurs', subFeature: 'shipping_companies' },
      ]
    }] : []),
    ...(isAdmin ? [{
      id: 'settings',
      featureKey: null, // Always visible
      title: language === 'ar' ? 'الإعدادات' : 'Paramètres',
      icon: Settings,
      items: [
        { path: '/api-keys', icon: Key, label: t.apiKeys },
        { path: '/settings', icon: Settings, label: t.settings },
        { path: '/settings/sidebar', icon: LayoutDashboard, label: language === 'ar' ? 'ترتيب القائمة' : 'Ordre menu' },
      ]
    }] : [])
  ];

  // Filter sections based on feature flags
  const filterNavSections = (sections) => {
    return sections
      .filter(section => {
        // If no featureKey, always show
        if (!section.featureKey) return true;
        // Check if feature category is enabled
        return isFeatureEnabled(section.featureKey);
      })
      .map(section => {
        // If no featureKey, return section as-is
        if (!section.featureKey) return section;
        // Filter items based on sub-features
        const filteredItems = section.items.filter(item => {
          if (!item.subFeature) return true;
          return isFeatureEnabled(section.featureKey, item.subFeature);
        });
        return { ...section, items: filteredItems };
      })
      .filter(section => section.items.length > 0); // Remove empty sections
  };

  // Select navigation based on user type
  const defaultNavSections = isSuperAdmin ? superAdminNavSections : filterNavSections(tenantNavSections);

  // Build navSections from customSidebarOrder if available
  const navSections = (() => {
    if (!customSidebarOrder) return defaultNavSections;
    
    // Create a map of default sections for quick lookup
    const defaultMap = {};
    defaultNavSections.forEach(section => {
      defaultMap[section.id] = section;
    });
    
    // Build sections based on custom order
    return customSidebarOrder
      .filter(customSection => customSection.visible !== false)
      .map(customSection => {
        const defaultSection = defaultMap[customSection.id];
        if (defaultSection) {
          // Use default section but apply custom item order and visibility
          const customItemPaths = customSection.items
            .filter(item => item.visible !== false)
            .map(item => item.path);
          
          const orderedItems = customItemPaths
            .map(path => defaultSection.items.find(item => item.path === path))
            .filter(Boolean);
          
          return {
            ...defaultSection,
            title: language === 'ar' ? customSection.titleAr : customSection.titleFr,
            icon: iconMap[customSection.icon] || defaultSection.icon,
            items: orderedItems.length > 0 ? orderedItems : defaultSection.items
          };
        }
        
        // Custom section - convert from saved format
        return {
          id: customSection.id,
          title: language === 'ar' ? customSection.titleAr : customSection.titleFr,
          icon: iconMap[customSection.icon] || Package,
          items: customSection.items
            .filter(item => item.visible !== false)
            .map(item => ({
              path: item.path,
              icon: iconMap[item.icon] || Package,
              label: language === 'ar' ? item.labelAr : item.labelFr
            }))
        };
      })
      .filter(section => section.items.length > 0);
  })();

  // Auto-expand section containing active page
  useEffect(() => {
    const currentPath = location.pathname;
    const activeSection = navSections.find(section => 
      section.items?.some(item => {
        if (item.path === '/') return currentPath === '/';
        return currentPath.startsWith(item.path);
      })
    );
    if (activeSection && !expandedSections.includes(activeSection.title)) {
      setExpandedSections(prev => [...prev, activeSection.title]);
    }
  }, [location.pathname]);

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

          {/* Expand/Collapse All Sections - Only when sidebar is not collapsed */}
          {!sidebarCollapsed && (
            <div className="flex items-center justify-center gap-2 py-2 border-b">
              <button
                onClick={() => setExpandedSections(navSections.map(s => s.title))}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted rounded-md transition-colors"
                title={language === 'ar' ? 'فتح الكل' : 'Tout ouvrir'}
              >
                <ChevronDown className="h-3 w-3" />
                <span>{language === 'ar' ? 'فتح الكل' : 'Ouvrir'}</span>
              </button>
              <button
                onClick={() => setExpandedSections([])}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted rounded-md transition-colors"
                title={language === 'ar' ? 'غلق الكل' : 'Tout fermer'}
              >
                <ChevronUp className="h-3 w-3" />
                <span>{language === 'ar' ? 'غلق الكل' : 'Fermer'}</span>
              </button>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
            {navSections.map((section) => (
              <div key={section.title} className="mb-2">
                {/* Section Header */}
                {!sidebarCollapsed && (
                  <button
                    onClick={() => toggleSection(section.title)}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm font-bold text-foreground uppercase tracking-wider hover:bg-muted/50 rounded-lg transition-colors"
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
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                          isActive(item.path) 
                            ? 'bg-primary text-primary-foreground font-medium shadow-md ring-2 ring-primary/30' 
                            : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                        } ${sidebarCollapsed ? 'justify-center' : ''}`}
                        data-testid={`nav-${item.path.replace(/\//g, '-') || 'home'}`}
                        title={sidebarCollapsed ? item.label : ''}
                      >
                        <item.icon className={`h-5 w-5 flex-shrink-0 ${isActive(item.path) ? '' : 'opacity-70'}`} />
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
          {/* Search Bar - Using UnifiedSearch */}
          <div className="flex-1 max-w-xl">
            <UnifiedSearch mode="header" />
          </div>

          <div className="flex items-center gap-4 ms-6">
            {/* Notifications */}
            <NotificationBell />

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
