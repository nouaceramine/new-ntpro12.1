import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { playSuccessBeep, playErrorBeep } from '../utils/beep';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import { 
  ShoppingCart, 
  Search, 
  Plus, 
  Minus, 
  User,
  AlertCircle,
  Clock,
  Package,
  X,
  Check,
  UserPlus,
  Warehouse,
  Printer,
  List,
  FolderTree,
  Users,
  FileText,
  Undo2,
  ArrowDownToLine,
  ArrowUpFromLine,
  BarChart3,
  ScrollText,
  ChevronLeft,
  ChevronRight,
  DollarSign,
  Trash2
} from 'lucide-react';
import { Calculator } from '../components/Calculator';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Color palette for product shortcuts
const SHORTCUT_COLORS = [
  '#dc2626', '#ea580c', '#d97706', '#ca8a04', '#65a30d',
  '#16a34a', '#059669', '#0d9488', '#0891b2', '#0284c7',
  '#2563eb', '#4f46e5', '#7c3aed', '#9333ea', '#c026d3',
  '#db2777', '#e11d48', '#64748b', '#78716c', '#71717a'
];

export default function POSPage() {
  const { t, language, isRTL } = useLanguage();
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [families, setFamilies] = useState([]);
  const [customerFamilies, setCustomerFamilies] = useState([]);
  const [wilayas, setWilayas] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState('');
  const [cart, setCart] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState('all');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDebt, setCustomerDebt] = useState(0);
  const [discount, setDiscount] = useState(0);
  const [paidAmount, setPaidAmount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [paymentType, setPaymentType] = useState('cash');
  const [loading, setLoading] = useState(false);
  const [priceType, setPriceType] = useState('retail');
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef(null);
  
  // Session state
  const [hasOpenSession, setHasOpenSession] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  
  // Left sidebar state
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false);
  const [activeTask, setActiveTask] = useState('articles');
  
  // Delivery state
  const [deliveryEnabled, setDeliveryEnabled] = useState(false);
  const [selectedWilaya, setSelectedWilaya] = useState('');
  const [deliveryType, setDeliveryType] = useState('desk');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [deliveryCity, setDeliveryCity] = useState('');
  const [deliveryFee, setDeliveryFee] = useState(0);
  
  // Dialogs
  const [showNewCustomerDialog, setShowNewCustomerDialog] = useState(false);
  const [newCustomerData, setNewCustomerData] = useState({ name: '', phone: '', email: '', address: '', family_id: '' });
  const [savingCustomer, setSavingCustomer] = useState(false);
  
  // Blacklist state
  const [blacklist, setBlacklist] = useState([]);
  const [selectedCustomerBlacklisted, setSelectedCustomerBlacklisted] = useState(false);
  const [blacklistReason, setBlacklistReason] = useState('');

  // Print Receipt Dialog
  const [showPrintDialog, setShowPrintDialog] = useState(false);
  const [lastSaleId, setLastSaleId] = useState(null);
  const [lastSaleInvoice, setLastSaleInvoice] = useState(null);
  const [receiptSettings, setReceiptSettings] = useState(null);
  
  // Calculator
  const [showCalculator, setShowCalculator] = useState(false);

  // Sale Code
  const [saleCode, setSaleCode] = useState('');

  // Product Shortcuts (20 quick access boxes)
  const [productShortcuts, setProductShortcuts] = useState(() => {
    const saved = localStorage.getItem('posProductShortcuts');
    return saved ? JSON.parse(saved) : Array(20).fill({ productId: null, color: '#e5e7eb' });
  });
  const [showShortcutDialog, setShowShortcutDialog] = useState(false);
  const [editingShortcutIndex, setEditingShortcutIndex] = useState(null);
  const [shortcutColor, setShortcutColor] = useState('#e5e7eb');
  const [shortcutProductId, setShortcutProductId] = useState('');

  // Current cashier info
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const currentCashier = currentUser?.full_name || currentUser?.username || 'Cashier';

  // Save shortcuts to localStorage
  const saveShortcuts = (shortcuts) => {
    setProductShortcuts(shortcuts);
    localStorage.setItem('posProductShortcuts', JSON.stringify(shortcuts));
  };

  useEffect(() => {
    checkOpenSession();
    fetchProducts();
    fetchCustomers();
    fetchFamilies();
    fetchCustomerFamilies();
    fetchBlacklist();
    fetchWilayas();
    fetchWarehouses();
    fetchReceiptSettings();
    fetchSaleCode();
  }, []);

  const checkOpenSession = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/daily-sessions/current`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHasOpenSession(!!response.data && response.data.status === 'open');
    } catch (error) {
      setHasOpenSession(false);
    } finally {
      setCheckingSession(false);
    }
  };

  useEffect(() => {
    if (selectedCustomer) {
      fetchCustomerDebt(selectedCustomer);
    } else {
      setCustomerDebt(0);
    }
  }, [selectedCustomer]);

  useEffect(() => {
    if (selectedWilaya && deliveryEnabled) {
      const wilaya = wilayas.find(w => w.code === selectedWilaya);
      if (wilaya) {
        setDeliveryFee(deliveryType === 'home' ? wilaya.home_fee : wilaya.desk_fee);
      }
    } else {
      setDeliveryFee(0);
    }
  }, [selectedWilaya, deliveryType, deliveryEnabled, wilayas]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchSaleCode = async () => {
    try {
      const response = await axios.get(`${API}/sales/generate-code`);
      setSaleCode(response.data.code);
    } catch (error) {
      console.error('Error fetching sale code:', error);
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const fetchFamilies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/product-families`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFamilies(response.data);
    } catch (error) {
      console.error('Error fetching families:', error);
    }
  };

  const fetchCustomerFamilies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/customer-families`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomerFamilies(response.data);
    } catch (error) {
      console.error('Error fetching customer families:', error);
    }
  };

  const fetchWilayas = async () => {
    try {
      const response = await axios.get(`${API}/delivery/wilayas`);
      setWilayas(response.data);
    } catch (error) {
      console.error('Error fetching wilayas:', error);
    }
  };

  const fetchWarehouses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/warehouses`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setWarehouses(response.data);
      const mainWarehouse = response.data.find(w => w.is_main);
      if (mainWarehouse && !selectedWarehouse) {
        setSelectedWarehouse(mainWarehouse.id);
      }
    } catch (error) {
      console.error('Error fetching warehouses:', error);
    }
  };

  const fetchBlacklist = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/blacklist`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBlacklist(response.data);
    } catch (error) {
      console.error('Error fetching blacklist:', error);
    }
  };

  const fetchReceiptSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/settings/receipt`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setReceiptSettings(response.data);
    } catch (error) {
      console.error('Error fetching receipt settings:', error);
    }
  };

  const fetchCustomerDebt = async (customerId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/customers/${customerId}/debt`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomerDebt(response.data.total_debt || 0);
      
      const customer = customers.find(c => c.id === customerId);
      if (customer?.phone) {
        const isBlacklisted = blacklist.some(b => b.phone === customer.phone);
        setSelectedCustomerBlacklisted(isBlacklisted);
        if (isBlacklisted) {
          const entry = blacklist.find(b => b.phone === customer.phone);
          setBlacklistReason(entry?.reason || '');
        } else {
          setBlacklistReason('');
        }
      }
    } catch (error) {
      setCustomerDebt(0);
    }
  };

  // Filtered products based on search and family
  const filteredProducts = products.filter(p => {
    const matchesSearch = !searchQuery || 
      p.name_ar?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.name_en?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.barcode?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.article_code?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesFamily = selectedFamily === 'all' || p.family_id === selectedFamily;
    
    return matchesSearch && matchesFamily;
  });

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.product_id === product.id);
    const price = priceType === 'wholesale' ? product.wholesale_price : product.retail_price;
    
    if (existingItem) {
      const newQty = existingItem.quantity + 1;
      const willBeNegative = newQty > product.quantity;
      
      if (willBeNegative) {
        toast.warning(language === 'ar' 
          ? `تنبيه: المخزون سيصبح سالب (${product.quantity - newQty})` 
          : `Attention: Stock sera negatif (${product.quantity - newQty})`);
      }
      
      setCart(cart.map(item => 
        item.product_id === product.id
          ? { ...item, quantity: newQty, total: newQty * item.unit_price }
          : item
      ));
    } else {
      if (product.quantity <= 0) {
        toast.warning(language === 'ar' 
          ? 'تنبيه: هذا المنتج غير متوفر - سيتم حساب المخزون بالسالب' 
          : 'Attention: Produit non disponible - stock sera negatif');
      }
      
      setCart([...cart, {
        product_id: product.id,
        product_name: language === 'ar' ? (product.name_ar || product.name_en) : (product.name_en || product.name_ar),
        barcode: product.barcode,
        article_code: product.article_code,
        quantity: 1,
        unit_price: price,
        discount: 0,
        discount_percent: 0,
        total: price,
        available_stock: product.quantity
      }]);
    }
    
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      oscillator.frequency.value = 1200;
      gainNode.gain.value = 0.15;
      oscillator.start();
      setTimeout(() => oscillator.stop(), 80);
    } catch (e) {}
  };

  const updateCartItemQuantity = (productId, newQty) => {
    if (newQty <= 0) {
      removeFromCart(productId);
      return;
    }
    
    const product = products.find(p => p.id === productId);
    if (product && newQty > product.quantity) {
      toast.warning(language === 'ar' 
        ? `تنبيه: المخزون سيصبح سالب` 
        : `Attention: Stock sera negatif`);
    }
    
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const subtotal = newQty * item.unit_price;
        const discountAmount = (item.discount_percent || 0) / 100 * subtotal;
        return { ...item, quantity: newQty, total: subtotal - discountAmount };
      }
      return item;
    }));
  };

  const updateCartItemPrice = (productId, newPrice) => {
    const price = parseFloat(newPrice) || 0;
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const subtotal = item.quantity * price;
        const discountAmount = (item.discount_percent || 0) / 100 * subtotal;
        return { ...item, unit_price: price, total: subtotal - discountAmount };
      }
      return item;
    }));
  };

  const updateCartItemDiscount = (productId, discountPercent) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const subtotal = item.quantity * item.unit_price;
        const discountAmount = (parseFloat(discountPercent) || 0) / 100 * subtotal;
        return { ...item, discount_percent: parseFloat(discountPercent) || 0, discount: discountAmount, total: subtotal - discountAmount };
      }
      return item;
    }));
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
  };

  const clearCart = () => {
    setCart([]);
    setDiscount(0);
    setPaidAmount(0);
    setSelectedCustomer(null);
    setDeliveryEnabled(false);
    setSelectedWilaya('');
    setDeliveryAddress('');
    setDeliveryCity('');
    setPaymentType('cash');
    fetchSaleCode();
  };

  const subtotal = cart.reduce((sum, item) => sum + item.total, 0);
  const total = subtotal - discount + (deliveryEnabled ? deliveryFee : 0);
  const remaining = total - paidAmount;

  const completeSale = async () => {
    if (!hasOpenSession) {
      toast.error(language === 'ar' 
        ? 'يجب فتح حصة جديدة قبل البيع'
        : 'Vous devez ouvrir une session avant de vendre');
      return;
    }
    
    if (cart.length === 0) {
      toast.error(language === 'ar' ? 'السلة فارغة' : 'Le panier est vide');
      return;
    }

    if (paymentType !== 'cash' && !selectedCustomer) {
      toast.error(language === 'ar' ? 'يجب اختيار زبون للبيع بالدين' : 'Selectionnez un client pour le credit');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const wilaya = wilayas.find(w => w.code === selectedWilaya);
      
      const saleData = {
        code: saleCode,
        customer_id: selectedCustomer,
        warehouse_id: selectedWarehouse || null,
        items: cart.map(item => ({
          product_id: item.is_custom ? null : item.product_id,
          product_name: item.product_name,
          barcode: item.barcode || '',
          quantity: item.quantity,
          unit_price: item.unit_price,
          discount: item.discount || 0,
          total: item.total
        })),
        subtotal,
        discount,
        total: subtotal - discount,
        paid_amount: paymentType === 'credit' ? 0 : paidAmount || total,
        payment_method: paymentMethod,
        payment_type: paymentType,
        notes: '',
        delivery: deliveryEnabled ? {
          enabled: true,
          wilaya_code: selectedWilaya,
          wilaya_name: wilaya ? (language === 'ar' ? wilaya.name_ar : wilaya.name_en) : '',
          city: deliveryCity,
          address: deliveryAddress,
          delivery_type: deliveryType,
          fee: deliveryFee
        } : null
      };

      const response = await axios.post(`${API}/sales`, saleData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(language === 'ar' ? 'تمت عملية البيع بنجاح' : 'Vente effectuee avec succes');
      
      setLastSaleId(response.data.id);
      setLastSaleInvoice(response.data.invoice_number);
      
      if (receiptSettings?.auto_print) {
        try {
          const invoiceResponse = await axios.get(`${API}/sales/${response.data.id}/invoice-pdf`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          const printWindow = window.open('', '_blank');
          if (printWindow) {
            printWindow.document.write(invoiceResponse.data);
            printWindow.document.close();
            printWindow.focus();
            setTimeout(() => printWindow.print(), 500);
          }
        } catch (printError) {
          console.error('Print error:', printError);
        }
      } else if (receiptSettings?.show_print_dialog !== false) {
        setShowPrintDialog(true);
      }
      
      clearCart();
      fetchProducts();
    } catch (error) {
      console.error('Sale error:', error);
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'حدث خطا اثناء البيع' : 'Erreur lors de la vente'));
    } finally {
      setLoading(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'F10' || (e.ctrlKey && e.key === 'Enter')) {
        e.preventDefault();
        completeSale();
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        clearCart();
      }
      // Ctrl+0-9 shortcuts
      if (e.ctrlKey && e.key >= '0' && e.key <= '9') {
        e.preventDefault();
        const index = parseInt(e.key);
        const tasks = ['articles', 'families', 'customers', 'customer-families', 'note', 'return', 'deposit', 'withdraw', 'reports', 'history'];
        if (tasks[index]) {
          setActiveTask(tasks[index]);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cart, hasOpenSession]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-DZ', { minimumFractionDigits: 2 }).format(amount || 0);
  };

  // Left sidebar menu items
  const taskMenuItems = [
    { id: 'articles', icon: List, label: language === 'ar' ? 'قائمة المنتجات' : 'Liste des articles', shortcut: 'Ctrl+0' },
    { id: 'families', icon: FolderTree, label: language === 'ar' ? 'المنتجات بالعائلة' : 'Articles par famille', shortcut: 'Ctrl+1' },
    { id: 'customers', icon: Users, label: language === 'ar' ? 'قائمة الزبائن' : 'Liste des clients', shortcut: 'Ctrl+2' },
    { id: 'customer-families', icon: FolderTree, label: language === 'ar' ? 'الزبائن بالعائلة' : 'Clients par famille', shortcut: 'Ctrl+3' },
    { id: 'note', icon: FileText, label: language === 'ar' ? 'إدراج ملاحظة' : 'Inserer une note libre', shortcut: 'Ctrl+4' },
    { id: 'return', icon: Undo2, label: language === 'ar' ? 'وضع الإرجاع' : 'Mode de retour', shortcut: 'Ctrl+5' },
    { id: 'deposit', icon: ArrowDownToLine, label: language === 'ar' ? 'إيداع - الصندوق' : 'Depot - Caisse', shortcut: 'Ctrl+6' },
    { id: 'withdraw', icon: ArrowUpFromLine, label: language === 'ar' ? 'سحب - الصندوق' : 'Retrait - Caisse', shortcut: 'Ctrl+7' },
    { id: 'reports', icon: BarChart3, label: language === 'ar' ? 'التقارير' : 'Rapports', shortcut: 'Ctrl+8' },
    { id: 'history', icon: ScrollText, label: language === 'ar' ? 'السجل' : 'Historiques', shortcut: 'Ctrl+9' },
  ];

  // Handle shortcut click
  const handleShortcutClick = (shortcut, index) => {
    if (shortcut.productId) {
      const product = products.find(p => p.id === shortcut.productId);
      if (product) {
        addToCart(product);
      }
    } else {
      setEditingShortcutIndex(index);
      setShortcutColor(shortcut.color || SHORTCUT_COLORS[index % SHORTCUT_COLORS.length]);
      setShortcutProductId('');
      setShowShortcutDialog(true);
    }
  };

  // Save shortcut
  const saveShortcut = () => {
    if (editingShortcutIndex !== null && shortcutProductId) {
      const newShortcuts = [...productShortcuts];
      newShortcuts[editingShortcutIndex] = {
        productId: shortcutProductId,
        color: shortcutColor
      };
      saveShortcuts(newShortcuts);
      setShowShortcutDialog(false);
    }
  };

  // Get shortcut product name
  const getShortcutProductName = (shortcut) => {
    if (!shortcut.productId) return language === 'ar' ? 'فارغ' : 'Vide';
    const product = products.find(p => p.id === shortcut.productId);
    if (!product) return '---';
    return language === 'ar' ? (product.name_ar || product.name_en) : (product.name_en || product.name_ar);
  };

  return (
    <Layout>
      <div className="space-y-4" data-testid="pos-page">
        {/* Header with title and total */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">
              {language === 'ar' ? 'نقطة البيع' : 'Point de Vente'} - NT Commerce
            </h1>
            <p className="text-muted-foreground">
              {language === 'ar' ? 'إدارة المبيعات والفواتير' : 'Gestion des ventes et factures'}
            </p>
          </div>
          <div className="flex items-center gap-4">
            {saleCode && (
              <Badge variant="outline" className="font-mono text-lg px-4 py-2">
                {saleCode}
              </Badge>
            )}
            <div className="bg-primary text-primary-foreground text-2xl font-bold px-6 py-3 rounded-xl shadow-lg">
              {formatCurrency(total)} {t.currency}
            </div>
          </div>
        </div>

        {/* Session Warning */}
        {!checkingSession && !hasOpenSession && (
          <Card className="border-amber-500 bg-amber-50 dark:bg-amber-950/20">
            <CardContent className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-6 w-6 text-amber-600" />
                <span className="font-medium text-amber-800 dark:text-amber-200">
                  {language === 'ar' ? 'لا توجد حصة مفتوحة - يجب فتح حصة جديدة قبل البيع' : 'Aucune session ouverte - Ouvrez une session'}
                </span>
              </div>
              <Link to="/daily-sessions">
                <Button variant="outline" className="gap-2 border-amber-500 text-amber-700 hover:bg-amber-100">
                  <Clock className="h-4 w-4" />
                  {language === 'ar' ? 'فتح حصة' : 'Ouvrir session'}
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-12 gap-4">
          {/* Left Sidebar - Task Menu */}
          <div className={`${leftSidebarCollapsed ? 'col-span-1' : 'col-span-2'} transition-all duration-300`}>
            <Card className="h-full">
              <CardHeader className="p-3 pb-2">
                <div className="flex items-center justify-between">
                  {!leftSidebarCollapsed && (
                    <CardTitle className="text-sm">
                      {language === 'ar' ? 'مهام البيع' : 'Taches de vente'}
                    </CardTitle>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setLeftSidebarCollapsed(!leftSidebarCollapsed)}
                    className="h-7 w-7"
                  >
                    {leftSidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-2 pt-0">
                <div className="space-y-1">
                  {taskMenuItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveTask(item.id)}
                      className={`w-full flex items-center gap-2 px-2 py-2 rounded-lg text-sm transition-colors ${
                        activeTask === item.id 
                          ? 'bg-primary text-primary-foreground' 
                          : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                      }`}
                      title={leftSidebarCollapsed ? item.label : undefined}
                    >
                      <item.icon className="h-4 w-4 flex-shrink-0" />
                      {!leftSidebarCollapsed && (
                        <>
                          <span className="flex-1 text-start truncate">{item.label}</span>
                          <span className="text-xs opacity-60">{item.shortcut}</span>
                        </>
                      )}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Area - Products Table */}
          <div className={`${leftSidebarCollapsed ? 'col-span-9' : 'col-span-8'} transition-all duration-300`}>
            <Card className="h-full flex flex-col">
              {/* Customer & Warehouse Selection */}
              <CardHeader className="p-4 pb-3 border-b">
                <div className="flex flex-wrap items-center gap-3">
                  <Select value={selectedCustomer || 'walk-in'} onValueChange={(v) => setSelectedCustomer(v === 'walk-in' ? null : v)}>
                    <SelectTrigger className="w-48" data-testid="customer-select">
                      <User className="h-4 w-4 me-2 opacity-50" />
                      <SelectValue placeholder={t.selectCustomer} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="walk-in">{t.walkInCustomer}</SelectItem>
                      {customers.map(c => (
                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowNewCustomerDialog(true)}
                    className="gap-1"
                    data-testid="add-customer-btn"
                  >
                    <UserPlus className="h-4 w-4" />
                    {language === 'ar' ? 'زبون جديد' : 'Nouveau client'}
                  </Button>

                  {warehouses.length > 0 && (
                    <Select value={selectedWarehouse} onValueChange={setSelectedWarehouse}>
                      <SelectTrigger className="w-40" data-testid="warehouse-select">
                        <Warehouse className="h-4 w-4 me-2 opacity-50" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses.map(w => (
                          <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}

                  <Select value={priceType} onValueChange={setPriceType}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="retail">{t.retailPrice}</SelectItem>
                      <SelectItem value="wholesale">{t.wholesalePrice}</SelectItem>
                    </SelectContent>
                  </Select>

                  {selectedCustomer && customerDebt > 0 && (
                    <Badge variant="destructive" className="px-3 py-1">
                      {language === 'ar' ? 'دين:' : 'Dette:'} {formatCurrency(customerDebt)} {t.currency}
                    </Badge>
                  )}
                </div>
              </CardHeader>

              {/* Products Table */}
              <CardContent className="flex-1 p-0 overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/50">
                      <TableHead className="w-24">{language === 'ar' ? 'الكود' : 'Code'}</TableHead>
                      <TableHead>{language === 'ar' ? 'اسم المنتج' : 'Nom d\'article'}</TableHead>
                      <TableHead className="w-24 text-center">{language === 'ar' ? 'الكمية' : 'Qte'}</TableHead>
                      <TableHead className="w-28 text-center">{language === 'ar' ? 'السعر' : 'Prix'}</TableHead>
                      <TableHead className="w-20 text-center">{language === 'ar' ? 'خصم %' : 'R. %'}</TableHead>
                      <TableHead className="w-28 text-center">{language === 'ar' ? 'المبلغ' : 'Montant'}</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cart.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-16 text-muted-foreground">
                          <ShoppingCart className="h-12 w-12 mx-auto mb-3 opacity-30" />
                          <p>{language === 'ar' ? 'اضف منتجات من الشريط الجانبي او ابحث' : 'Ajoutez des articles depuis la barre laterale'}</p>
                        </TableCell>
                      </TableRow>
                    ) : (
                      cart.map((item, index) => (
                        <TableRow key={item.product_id} className={index % 2 === 0 ? 'bg-muted/20' : ''}>
                          <TableCell className="font-mono text-sm">{item.article_code || item.barcode || '---'}</TableCell>
                          <TableCell className="font-medium">{item.product_name}</TableCell>
                          <TableCell className="text-center">
                            <div className="flex items-center justify-center gap-1">
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => updateCartItemQuantity(item.product_id, item.quantity - 1)}>
                                <Minus className="h-3 w-3" />
                              </Button>
                              <Input
                                type="number"
                                min="1"
                                value={item.quantity}
                                onChange={(e) => updateCartItemQuantity(item.product_id, parseInt(e.target.value) || 1)}
                                className="w-14 h-8 text-center"
                              />
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => updateCartItemQuantity(item.product_id, item.quantity + 1)}>
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <Input
                              type="number"
                              value={item.unit_price}
                              onChange={(e) => updateCartItemPrice(item.product_id, e.target.value)}
                              className="w-24 h-8 text-center"
                            />
                          </TableCell>
                          <TableCell className="text-center">
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={item.discount_percent || ''}
                              onChange={(e) => updateCartItemDiscount(item.product_id, e.target.value)}
                              className="w-16 h-8 text-center"
                            />
                          </TableCell>
                          <TableCell className="text-center font-semibold">{formatCurrency(item.total)}</TableCell>
                          <TableCell>
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:bg-destructive/10" onClick={() => removeFromCart(item.product_id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>

              {/* Totals & Action Buttons */}
              <div className="border-t p-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  {/* Totals */}
                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">{language === 'ar' ? 'المجموع الفرعي' : 'Sous total'}</p>
                      <p className="text-lg font-bold">{formatCurrency(subtotal)} {t.currency}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">{language === 'ar' ? 'الخصم' : 'Remise'}</p>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          value={discount || ''}
                          onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                          className="w-20 h-8 text-center"
                        />
                        <span className="font-semibold">{formatCurrency(discount)} {t.currency}</span>
                      </div>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">{language === 'ar' ? 'الإجمالي' : 'Total'}</p>
                      <p className="text-2xl font-bold text-primary">{formatCurrency(total)} {t.currency}</p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={completeSale}
                      disabled={loading || cart.length === 0 || !hasOpenSession}
                      className="h-11 px-6 gap-2"
                      data-testid="vente-btn"
                    >
                      <Check className="h-5 w-5" />
                      {language === 'ar' ? 'تاكيد البيع' : 'Valider'}
                      <Badge variant="secondary" className="text-xs ms-1">F10</Badge>
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={clearCart}
                      className="h-11 px-4 gap-2"
                      data-testid="annuler-btn"
                    >
                      <X className="h-4 w-4" />
                      {language === 'ar' ? 'الغاء' : 'Annuler'}
                    </Button>
                  </div>
                </div>

                {/* Bottom Info Bar */}
                <div className="flex items-center justify-between mt-4 pt-3 border-t text-xs text-muted-foreground">
                  <div className="flex items-center gap-4">
                    <span>{language === 'ar' ? 'الصندوق:' : 'Caisse:'} 1</span>
                    <span>{language === 'ar' ? 'البائع:' : 'Caissier:'} {currentCashier}</span>
                  </div>
                  <div>
                    {new Date().toLocaleDateString(language === 'ar' ? 'ar-SA' : 'fr-FR', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right Sidebar - Product Shortcuts */}
          <div className="col-span-2">
            <Card className="h-full">
              <CardHeader className="p-3 pb-2">
                <CardTitle className="text-sm text-center">
                  {language === 'ar' ? 'اختصارات المنتجات' : 'Raccourcis'}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-2 pt-0">
                <div className="grid grid-cols-2 gap-1">
                  {productShortcuts.slice(0, 20).map((shortcut, index) => {
                    const productName = getShortcutProductName(shortcut);
                    const bgColor = shortcut.productId ? shortcut.color : 'hsl(var(--muted))';
                    
                    return (
                      <button
                        key={index}
                        onClick={() => handleShortcutClick(shortcut, index)}
                        onContextMenu={(e) => {
                          e.preventDefault();
                          setEditingShortcutIndex(index);
                          setShortcutColor(shortcut.color || SHORTCUT_COLORS[index % SHORTCUT_COLORS.length]);
                          setShortcutProductId(shortcut.productId || '');
                          setShowShortcutDialog(true);
                        }}
                        style={{ backgroundColor: shortcut.productId ? bgColor : undefined }}
                        className={`py-3 px-1 rounded-lg text-xs font-medium text-center leading-tight transition-all min-h-[56px] flex items-center justify-center ${
                          shortcut.productId 
                            ? 'text-white hover:opacity-90 shadow-sm' 
                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                        }`}
                        title={productName}
                      >
                        <span className="line-clamp-3">{productName}</span>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Shortcut Edit Dialog */}
        <Dialog open={showShortcutDialog} onOpenChange={setShowShortcutDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {language === 'ar' ? 'تعديل الاختصار' : 'Modifier le raccourci'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>{language === 'ar' ? 'اختر المنتج' : 'Choisir le produit'}</Label>
                <Select value={shortcutProductId} onValueChange={setShortcutProductId}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder={language === 'ar' ? 'اختر منتج...' : 'Selectionner...'} />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {products.map(p => (
                      <SelectItem key={p.id} value={p.id}>
                        {language === 'ar' ? p.name_ar : p.name_en}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>{language === 'ar' ? 'اختر اللون' : 'Choisir la couleur'}</Label>
                <div className="grid grid-cols-5 gap-2 mt-2">
                  {SHORTCUT_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setShortcutColor(color)}
                      style={{ backgroundColor: color }}
                      className={`h-8 w-full rounded ${shortcutColor === color ? 'ring-2 ring-primary ring-offset-2' : ''}`}
                    />
                  ))}
                </div>
              </div>
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    if (editingShortcutIndex !== null) {
                      const newShortcuts = [...productShortcuts];
                      newShortcuts[editingShortcutIndex] = { productId: null, color: '#e5e7eb' };
                      saveShortcuts(newShortcuts);
                    }
                    setShowShortcutDialog(false);
                  }}
                  className="flex-1"
                >
                  {language === 'ar' ? 'مسح' : 'Effacer'}
                </Button>
                <Button onClick={saveShortcut} disabled={!shortcutProductId} className="flex-1">
                  {language === 'ar' ? 'حفظ' : 'Enregistrer'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* New Customer Dialog */}
        <Dialog open={showNewCustomerDialog} onOpenChange={setShowNewCustomerDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                {language === 'ar' ? 'اضافة زبون جديد' : 'Ajouter un client'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>{language === 'ar' ? 'الاسم *' : 'Nom *'}</Label>
                <Input
                  value={newCustomerData.name}
                  onChange={(e) => setNewCustomerData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder={language === 'ar' ? 'اسم الزبون' : 'Nom du client'}
                />
              </div>
              <div>
                <Label>{language === 'ar' ? 'الهاتف' : 'Telephone'}</Label>
                <Input
                  value={newCustomerData.phone}
                  onChange={(e) => setNewCustomerData(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="0555 123 456"
                />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowNewCustomerDialog(false)} className="flex-1">
                  {language === 'ar' ? 'الغاء' : 'Annuler'}
                </Button>
                <Button
                  onClick={async () => {
                    if (!newCustomerData.name) {
                      toast.error(language === 'ar' ? 'يرجى ادخال الاسم' : 'Veuillez entrer le nom');
                      return;
                    }
                    setSavingCustomer(true);
                    try {
                      const token = localStorage.getItem('token');
                      const response = await axios.post(`${API}/customers`, newCustomerData, {
                        headers: { Authorization: `Bearer ${token}` }
                      });
                      toast.success(language === 'ar' ? 'تمت الاضافة' : 'Client ajoute');
                      setNewCustomerData({ name: '', phone: '', email: '', address: '', family_id: '' });
                      fetchCustomers();
                      setSelectedCustomer(response.data.id);
                      setShowNewCustomerDialog(false);
                    } catch (error) {
                      toast.error(error.response?.data?.detail || 'Error');
                    } finally {
                      setSavingCustomer(false);
                    }
                  }}
                  disabled={savingCustomer}
                  className="flex-1"
                >
                  {savingCustomer ? '...' : (language === 'ar' ? 'حفظ' : 'Enregistrer')}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Print Receipt Dialog */}
        <Dialog open={showPrintDialog} onOpenChange={setShowPrintDialog}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Printer className="h-5 w-5" />
                {language === 'ar' ? 'طباعة الوصل' : 'Imprimer le recu'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <p className="text-center text-muted-foreground">
                {language === 'ar' ? 'تمت عملية البيع بنجاح' : 'Vente effectuee avec succes'}
              </p>
              {lastSaleInvoice && (
                <p className="text-center font-mono text-lg">{lastSaleInvoice}</p>
              )}
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowPrintDialog(false)} className="flex-1">
                  {language === 'ar' ? 'اغلاق' : 'Fermer'}
                </Button>
                <Button
                  onClick={async () => {
                    if (lastSaleId) {
                      const token = localStorage.getItem('token');
                      try {
                        const invoiceResponse = await axios.get(`${API}/sales/${lastSaleId}/invoice-pdf`, {
                          headers: { Authorization: `Bearer ${token}` }
                        });
                        const printWindow = window.open('', '_blank');
                        if (printWindow) {
                          printWindow.document.write(invoiceResponse.data);
                          printWindow.document.close();
                          printWindow.focus();
                          setTimeout(() => printWindow.print(), 500);
                        }
                      } catch (error) {
                        toast.error('Error printing');
                      }
                    }
                    setShowPrintDialog(false);
                  }}
                  className="flex-1 gap-2"
                >
                  <Printer className="h-4 w-4" />
                  {language === 'ar' ? 'طباعة' : 'Imprimer'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
