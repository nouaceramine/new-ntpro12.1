import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
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
  DialogFooter,
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
  Trash2,
  RotateCcw,
  History
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
  const navigate = useNavigate();
  
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
  
  // Task-related dialogs
  const [showProductsDialog, setShowProductsDialog] = useState(false);
  const [showCustomersDialog, setShowCustomersDialog] = useState(false);
  const [showNoteDialog, setShowNoteDialog] = useState(false);
  const [showCashDialog, setShowCashDialog] = useState(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [saleNote, setSaleNote] = useState('');
  const [returnMode, setReturnMode] = useState(false);
  const [cashOperation, setCashOperation] = useState({ type: 'deposit', amount: 0, note: '' });
  const [salesHistory, setSalesHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  
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

  // Search Results
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchResults, setSearchResults] = useState([]);

  // Sale Code
  const [saleCode, setSaleCode] = useState('');

  // Product Shortcuts (10 quick access boxes - reduced for single page)
  const [productShortcuts, setProductShortcuts] = useState(() => {
    const saved = localStorage.getItem('posProductShortcuts');
    return saved ? JSON.parse(saved) : Array(10).fill({ productId: null, color: '#e5e7eb' });
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

  const fetchSalesHistory = async () => {
    setHistoryLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/sales?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSalesHistory(response.data.sales || response.data || []);
    } catch (error) {
      console.error('Error fetching sales history:', error);
    } finally {
      setHistoryLoading(false);
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
      const newQty = returnMode ? existingItem.quantity - 1 : existingItem.quantity + 1;
      if (newQty <= 0) {
        removeFromCart(product.id);
        return;
      }
      
      const willBeNegative = newQty > product.quantity;
      if (willBeNegative && !returnMode) {
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
      if (product.quantity <= 0 && !returnMode) {
        toast.warning(language === 'ar' 
          ? 'تنبيه: هذا المنتج غير متوفر - سيتم حساب المخزون بالسالب' 
          : 'Attention: Produit non disponible - stock sera negatif');
      }
      
      setCart([...cart, {
        product_id: product.id,
        product_name: language === 'ar' ? (product.name_ar || product.name_en) : (product.name_en || product.name_ar),
        barcode: product.barcode,
        article_code: product.article_code,
        quantity: returnMode ? -1 : 1,
        unit_price: price,
        discount: 0,
        discount_percent: 0,
        total: returnMode ? -price : price,
        available_stock: product.quantity,
        is_return: returnMode
      }]);
    }
    
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      oscillator.frequency.value = returnMode ? 800 : 1200;
      gainNode.gain.value = 0.15;
      oscillator.start();
      setTimeout(() => oscillator.stop(), 80);
    } catch (e) {}
  };

  const updateCartItemQuantity = (productId, newQty) => {
    if (newQty === 0) {
      removeFromCart(productId);
      return;
    }
    
    const product = products.find(p => p.id === productId);
    if (product && Math.abs(newQty) > product.quantity && newQty > 0) {
      toast.warning(language === 'ar' 
        ? `تنبيه: المخزون سيصبح سالب` 
        : `Attention: Stock sera negatif`);
    }
    
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const subtotal = newQty * item.unit_price;
        const discountAmount = (item.discount_percent || 0) / 100 * Math.abs(subtotal);
        return { ...item, quantity: newQty, total: subtotal - (newQty > 0 ? discountAmount : -discountAmount) };
      }
      return item;
    }));
  };

  const updateCartItemPrice = (productId, newPrice) => {
    const price = parseFloat(newPrice) || 0;
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const subtotal = item.quantity * price;
        const discountAmount = (item.discount_percent || 0) / 100 * Math.abs(subtotal);
        return { ...item, unit_price: price, total: subtotal - (item.quantity > 0 ? discountAmount : -discountAmount) };
      }
      return item;
    }));
  };

  const updateCartItemDiscount = (productId, discountPercent) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const subtotal = item.quantity * item.unit_price;
        const discountAmount = (parseFloat(discountPercent) || 0) / 100 * Math.abs(subtotal);
        return { ...item, discount_percent: parseFloat(discountPercent) || 0, discount: discountAmount, total: subtotal - (item.quantity > 0 ? discountAmount : -discountAmount) };
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
    setSaleNote('');
    setReturnMode(false);
    fetchSaleCode();
  };

  const subtotal = cart.reduce((sum, item) => sum + item.total, 0);
  const total = subtotal - discount + (deliveryEnabled ? deliveryFee : 0);
  const remaining = total - paidAmount;

  // Handle cash operation (deposit/withdraw)
  const handleCashOperation = async () => {
    if (!cashOperation.amount || cashOperation.amount <= 0) {
      toast.error(language === 'ar' ? 'يرجى إدخال مبلغ صحيح' : 'Veuillez entrer un montant valide');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const endpoint = cashOperation.type === 'deposit' ? '/cash/deposit' : '/cash/withdraw';
      await axios.post(`${API}${endpoint}`, {
        amount: cashOperation.amount,
        note: cashOperation.note,
        box_id: 'cash'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(language === 'ar' 
        ? (cashOperation.type === 'deposit' ? 'تم الإيداع بنجاح' : 'تم السحب بنجاح')
        : (cashOperation.type === 'deposit' ? 'Depot effectue' : 'Retrait effectue'));
      
      setShowCashDialog(false);
      setCashOperation({ type: 'deposit', amount: 0, note: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error');
    }
  };

  // Handle task menu click
  const handleTaskClick = (taskId) => {
    setActiveTask(taskId);
    
    switch(taskId) {
      case 'articles':
        setShowProductsDialog(true);
        break;
      case 'families':
        setSelectedFamily('all');
        setShowProductsDialog(true);
        break;
      case 'customers':
        setShowCustomersDialog(true);
        break;
      case 'customer-families':
        setShowCustomersDialog(true);
        break;
      case 'note':
        setShowNoteDialog(true);
        break;
      case 'return':
        setReturnMode(!returnMode);
        toast.info(language === 'ar' 
          ? (returnMode ? 'تم إلغاء وضع الإرجاع' : 'تم تفعيل وضع الإرجاع')
          : (returnMode ? 'Mode retour desactive' : 'Mode retour active'));
        break;
      case 'deposit':
        setCashOperation({ type: 'deposit', amount: 0, note: '' });
        setShowCashDialog(true);
        break;
      case 'withdraw':
        setCashOperation({ type: 'withdraw', amount: 0, note: '' });
        setShowCashDialog(true);
        break;
      case 'reports':
        navigate('/reports');
        break;
      case 'history':
        fetchSalesHistory();
        setShowHistoryDialog(true);
        break;
      default:
        break;
    }
  };

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
        notes: saleNote,
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
        // Use the saved printer size from settings
        const printerSize = receiptSettings?.thermal_printer_size || '80mm';
        printThermalReceipt(response.data.id, printerSize);
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

  // Thermal Printer Support - Universal ESC/POS compatible for all models (58mm, 80mm)
  const printThermalReceipt = async (saleId, printerSize = '80mm') => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/sales/${saleId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const sale = response.data;
      
      // Generate thermal receipt HTML
      const receiptHtml = generateThermalReceiptHtml(sale, printerSize);
      
      const printWindow = window.open('', '_blank', 'width=300,height=600');
      if (printWindow) {
        printWindow.document.write(receiptHtml);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
          printWindow.print();
          printWindow.close();
        }, 500);
      }
    } catch (error) {
      console.error('Print error:', error);
      toast.error(language === 'ar' ? 'خطأ في الطباعة' : 'Erreur d\'impression');
    }
  };

  // Generate thermal receipt HTML (ESC/POS compatible for 58mm, 80mm thermal printers)
  const generateThermalReceiptHtml = (sale, printerSize = '80mm') => {
    const storeName = receiptSettings?.store_name || 'NT Commerce';
    const storeAddress = receiptSettings?.store_address || '';
    const storePhone = receiptSettings?.store_phone || '';
    const fontSize = printerSize === '58mm' ? '10px' : '12px';
    const titleSize = printerSize === '58mm' ? '14px' : '16px';
    const totalSize = printerSize === '58mm' ? '12px' : '14px';
    
    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Receipt</title>
  <style>
    @page { size: ${printerSize} auto; margin: 0; }
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Courier New', 'Lucida Console', monospace;
      font-size: ${fontSize};
      width: ${printerSize};
      padding: 3mm;
      direction: ${isRTL ? 'rtl' : 'ltr'};
      line-height: 1.4;
    }
    .center { text-align: center; }
    .bold { font-weight: bold; }
    .line { border-bottom: 1px dashed #000; margin: 4px 0; }
    .double-line { border-bottom: 2px solid #000; margin: 4px 0; }
    .row { display: flex; justify-content: space-between; gap: 4px; }
    .items { margin: 8px 0; }
    .item { margin: 4px 0; padding-bottom: 2px; }
    .total { font-size: ${totalSize}; font-weight: bold; }
    .footer { margin-top: 12px; font-size: 9px; }
    .cashier { font-size: 9px; color: #666; margin-top: 4px; }
    .barcode { font-family: 'Libre Barcode 39', monospace; font-size: 24px; margin: 8px 0; }
  </style>
</head>
<body>
  <div class="center bold" style="font-size: ${titleSize};">${storeName}</div>
  ${storeAddress ? `<div class="center" style="font-size: 10px;">${storeAddress}</div>` : ''}
  ${storePhone ? `<div class="center" style="font-size: 10px;">${storePhone}</div>` : ''}
  
  <div class="double-line"></div>
  
  <div class="row">
    <span>${language === 'ar' ? 'رقم:' : 'N°:'}</span>
    <span class="bold">${sale.invoice_number || sale.code}</span>
  </div>
  <div class="row">
    <span>${language === 'ar' ? 'التاريخ:' : 'Date:'}</span>
    <span>${new Date(sale.created_at).toLocaleString(language === 'ar' ? 'ar-DZ' : 'fr-FR')}</span>
  </div>
  ${sale.customer_name ? `
  <div class="row">
    <span>${language === 'ar' ? 'الزبون:' : 'Client:'}</span>
    <span>${sale.customer_name}</span>
  </div>
  ` : ''}
  
  <div class="line"></div>
  
  <div class="items">
    ${(sale.items || []).map(item => `
      <div class="item">
        <div class="bold">${item.product_name}</div>
        <div class="row">
          <span>${item.quantity} x ${formatCurrency(item.unit_price)}</span>
          <span class="bold">${formatCurrency(item.total)}</span>
        </div>
      </div>
    `).join('')}
  </div>
  
  <div class="line"></div>
  
  <div class="row">
    <span>${language === 'ar' ? 'المجموع الفرعي:' : 'Sous-total:'}</span>
    <span>${formatCurrency(sale.subtotal)}</span>
  </div>
  ${sale.discount > 0 ? `
  <div class="row">
    <span>${language === 'ar' ? 'الخصم:' : 'Remise:'}</span>
    <span>-${formatCurrency(sale.discount)}</span>
  </div>
  ` : ''}
  ${sale.delivery?.fee > 0 ? `
  <div class="row">
    <span>${language === 'ar' ? 'التوصيل:' : 'Livraison:'}</span>
    <span>${formatCurrency(sale.delivery.fee)}</span>
  </div>
  ` : ''}
  
  <div class="double-line"></div>
  
  <div class="row total">
    <span>${language === 'ar' ? 'الإجمالي:' : 'TOTAL:'}</span>
    <span>${formatCurrency(sale.total)} ${t.currency}</span>
  </div>
  
  ${sale.paid_amount ? `
  <div class="row" style="margin-top: 4px;">
    <span>${language === 'ar' ? 'المدفوع:' : 'Payé:'}</span>
    <span>${formatCurrency(sale.paid_amount)}</span>
  </div>
  ${sale.total - sale.paid_amount > 0 ? `
  <div class="row">
    <span>${language === 'ar' ? 'الباقي:' : 'Reste:'}</span>
    <span>${formatCurrency(sale.total - sale.paid_amount)}</span>
  </div>
  ` : ''}
  ` : ''}
  
  <div class="footer center">
    <div class="line"></div>
    <div style="margin-top: 6px;">${language === 'ar' ? 'شكراً لزيارتكم' : 'Merci de votre visite'}</div>
    <div class="cashier">${language === 'ar' ? 'البائع:' : 'Caissier:'} ${currentCashier}</div>
  </div>
</body>
</html>
    `;
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
          handleTaskClick(tasks[index]);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cart, hasOpenSession, returnMode]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-DZ', { minimumFractionDigits: 2 }).format(amount || 0);
  };

  // Left sidebar menu items
  const taskMenuItems = [
    { id: 'articles', icon: List, label: language === 'ar' ? 'قائمة المنتجات' : 'Liste articles', shortcut: '0' },
    { id: 'families', icon: FolderTree, label: language === 'ar' ? 'بالعائلة' : 'Par famille', shortcut: '1' },
    { id: 'customers', icon: Users, label: language === 'ar' ? 'الزبائن' : 'Clients', shortcut: '2' },
    { id: 'customer-families', icon: FolderTree, label: language === 'ar' ? 'عائلات الزبائن' : 'Fam. clients', shortcut: '3' },
    { id: 'note', icon: FileText, label: language === 'ar' ? 'ملاحظة' : 'Note', shortcut: '4' },
    { id: 'return', icon: Undo2, label: language === 'ar' ? 'إرجاع' : 'Retour', shortcut: '5' },
    { id: 'deposit', icon: ArrowDownToLine, label: language === 'ar' ? 'إيداع' : 'Depot', shortcut: '6' },
    { id: 'withdraw', icon: ArrowUpFromLine, label: language === 'ar' ? 'سحب' : 'Retrait', shortcut: '7' },
    { id: 'reports', icon: BarChart3, label: language === 'ar' ? 'تقارير' : 'Rapports', shortcut: '8' },
    { id: 'history', icon: ScrollText, label: language === 'ar' ? 'السجل' : 'Historique', shortcut: '9' },
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
    if (!shortcut.productId) return '+';
    const product = products.find(p => p.id === shortcut.productId);
    if (!product) return '---';
    const name = language === 'ar' ? (product.name_ar || product.name_en) : (product.name_en || product.name_ar);
    return name?.substring(0, 8) || '---';
  };

  return (
    <Layout>
      <div className="h-[calc(100vh-120px)] md:h-[calc(100vh-120px)] flex flex-col" data-testid="pos-page">
        {/* Header with title and total - Mobile Responsive */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-2">
          <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
            <h1 className="text-base sm:text-xl font-bold">
              {language === 'ar' ? 'نقطة البيع' : 'Point de Vente'}
            </h1>
            {returnMode && (
              <Badge variant="destructive" className="animate-pulse text-xs sm:text-sm">
                {language === 'ar' ? 'إرجاع' : 'Retour'}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto justify-between sm:justify-end">
            {saleCode && (
              <Badge variant="outline" className="font-mono text-xs sm:text-sm px-2 py-1">
                {saleCode}
              </Badge>
            )}
            <div className="bg-primary text-primary-foreground text-base sm:text-xl font-bold px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg shadow">
              {formatCurrency(total)} {t.currency}
            </div>
          </div>
        </div>

        {/* Session Warning */}
        {!checkingSession && !hasOpenSession && (
          <Card className="border-amber-500 bg-amber-50 dark:bg-amber-950/20 mb-2">
            <CardContent className="flex items-center justify-between p-3">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <span className="font-medium text-amber-800 dark:text-amber-200 text-sm">
                  {language === 'ar' ? 'لا توجد حصة مفتوحة' : 'Aucune session ouverte'}
                </span>
              </div>
              <Link to="/daily-sessions">
                <Button size="sm" variant="outline" className="gap-1 border-amber-500 text-amber-700">
                  <Clock className="h-4 w-4" />
                  {language === 'ar' ? 'فتح حصة' : 'Ouvrir'}
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Main Content Grid - Mobile Responsive */}
        <div className={`flex-1 grid grid-cols-1 md:grid-cols-12 gap-2 min-h-0 ${isRTL ? 'direction-ltr' : ''}`} style={{ direction: 'ltr' }}>
          {/* Left Sidebar - Search, Add Product & Task Menu - Hidden on mobile, shown as floating menu */}
          <div className="hidden md:flex md:col-span-2 flex-col gap-2" style={{ direction: isRTL ? 'rtl' : 'ltr' }}>
            {/* Search & Add Product */}
            <Card className="p-2">
              <div className="relative mb-2">
                <Search className="absolute top-1/2 -translate-y-1/2 start-2 h-4 w-4 text-muted-foreground z-10" />
                <Input
                  ref={searchInputRef}
                  placeholder={language === 'ar' ? 'بحث...' : 'Rechercher...'}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setShowSearchResults(true)}
                  className="ps-8 h-9 text-sm"
                  data-testid="pos-search-input"
                />
                {/* Search Results Dropdown */}
                {showSearchResults && searchQuery.length >= 1 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-background border rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
                    {searchResults.length === 0 ? (
                      <div className="p-3 text-center text-muted-foreground text-sm">
                        {language === 'ar' ? 'لا توجد نتائج' : 'Aucun résultat'}
                      </div>
                    ) : (
                      searchResults.slice(0, 8).map((product) => (
                        <button
                          key={product.id}
                          onClick={() => {
                            addToCart(product);
                            setSearchQuery('');
                            setShowSearchResults(false);
                          }}
                          className="w-full flex items-center gap-2 p-2 hover:bg-muted text-start transition-colors border-b last:border-b-0"
                        >
                          <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center shrink-0">
                            <Package className="h-4 w-4 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{product.name}</p>
                            <p className="text-xs text-muted-foreground">{product.code} • {formatCurrency(product.price)}</p>
                          </div>
                          <Badge variant="outline" className="text-xs shrink-0">
                            {product.quantity || 0}
                          </Badge>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
              <Button 
                size="sm" 
                className="w-full gap-1"
                onClick={() => setShowProductsDialog(true)}
                data-testid="add-product-btn"
              >
                <Plus className="h-4 w-4" />
                {language === 'ar' ? 'إضافة منتج' : 'Ajouter'}
              </Button>
            </Card>

            {/* Task Menu */}
            <Card className="flex-1 overflow-hidden">
              <CardHeader className="p-2 pb-1">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  {language === 'ar' ? 'مهام البيع' : 'Taches'}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-1 pt-0 overflow-y-auto" style={{ maxHeight: 'calc(100% - 40px)' }}>
                <div className="space-y-0.5">
                  {taskMenuItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleTaskClick(item.id)}
                      className={`w-full flex items-center gap-1.5 px-2 py-1.5 rounded text-xs transition-colors ${
                        activeTask === item.id 
                          ? 'bg-primary text-primary-foreground' 
                          : item.id === 'return' && returnMode
                            ? 'bg-destructive text-destructive-foreground'
                            : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                      }`}
                      title={item.label}
                      data-testid={`task-${item.id}`}
                    >
                      <item.icon className="h-3.5 w-3.5 flex-shrink-0" />
                      <span className="flex-1 text-start truncate">{item.label}</span>
                      <span className="text-[10px] opacity-60">{item.shortcut}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Mobile Quick Actions Bar */}
          <div className="md:hidden flex items-center gap-2 mb-2 overflow-x-auto pb-2" style={{ direction: isRTL ? 'rtl' : 'ltr' }}>
            <Button 
              size="sm" 
              variant="outline"
              className="gap-1 shrink-0"
              onClick={() => setShowProductsDialog(true)}
            >
              <Plus className="h-4 w-4" />
              {language === 'ar' ? 'منتج' : 'Produit'}
            </Button>
            <Button 
              size="sm" 
              variant={returnMode ? "destructive" : "outline"}
              className="gap-1 shrink-0"
              onClick={() => handleTaskClick('return')}
            >
              <Undo2 className="h-4 w-4" />
              {language === 'ar' ? 'إرجاع' : 'Retour'}
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              className="gap-1 shrink-0"
              onClick={() => setShowCustomersDialog(true)}
            >
              <Users className="h-4 w-4" />
              {language === 'ar' ? 'زبون' : 'Client'}
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              className="gap-1 shrink-0"
              onClick={() => setShowHistoryDialog(true)}
            >
              <History className="h-4 w-4" />
            </Button>
          </div>

          {/* Main Area - Products Table */}
          <div className="col-span-1 md:col-span-8 flex flex-col min-h-0" style={{ direction: isRTL ? 'rtl' : 'ltr' }}>
            <Card className="flex-1 flex flex-col overflow-hidden">
              {/* Customer & Warehouse Selection */}
              <div className="p-2 border-b flex flex-wrap items-center gap-2">
                <Select value={selectedCustomer || 'walk-in'} onValueChange={(v) => setSelectedCustomer(v === 'walk-in' ? null : v)}>
                  <SelectTrigger className="w-40 h-8 text-sm" data-testid="customer-select">
                    <User className="h-3.5 w-3.5 me-1.5 opacity-50" />
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
                  className="h-8 gap-1 text-xs"
                  data-testid="add-customer-btn"
                >
                  <UserPlus className="h-3.5 w-3.5" />
                </Button>

                {warehouses.length > 0 && (
                  <Select value={selectedWarehouse} onValueChange={setSelectedWarehouse}>
                    <SelectTrigger className="w-32 h-8 text-sm" data-testid="warehouse-select">
                      <Warehouse className="h-3.5 w-3.5 me-1.5 opacity-50" />
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
                  <SelectTrigger className="w-24 h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="retail">{language === 'ar' ? 'تجزئة' : 'Detail'}</SelectItem>
                    <SelectItem value="wholesale">{language === 'ar' ? 'جملة' : 'Gros'}</SelectItem>
                  </SelectContent>
                </Select>

                {selectedCustomer && customerDebt > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    {language === 'ar' ? 'دين:' : 'Dette:'} {formatCurrency(customerDebt)}
                  </Badge>
                )}
              </div>

              {/* Products Table - Responsive */}
              <div className="flex-1 overflow-auto">
                {/* Desktop Table */}
                <Table className="hidden sm:table">
                  <TableHeader>
                    <TableRow className="bg-muted/50">
                      <TableHead className="w-20 text-xs">{language === 'ar' ? 'الكود' : 'Code'}</TableHead>
                      <TableHead className="text-xs">{language === 'ar' ? 'المنتج' : 'Article'}</TableHead>
                      <TableHead className="w-24 text-center text-xs">{language === 'ar' ? 'الكمية' : 'Qte'}</TableHead>
                      <TableHead className="w-24 text-center text-xs">{language === 'ar' ? 'السعر' : 'Prix'}</TableHead>
                      <TableHead className="w-16 text-center text-xs">%</TableHead>
                      <TableHead className="w-24 text-center text-xs">{language === 'ar' ? 'المبلغ' : 'Total'}</TableHead>
                      <TableHead className="w-10"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cart.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          <ShoppingCart className="h-8 w-8 mx-auto mb-2 opacity-30" />
                          <p className="text-sm">{language === 'ar' ? 'أضف منتجات' : 'Ajoutez des articles'}</p>
                        </TableCell>
                      </TableRow>
                    ) : (
                      cart.map((item, index) => (
                        <TableRow key={item.product_id} className={`${index % 2 === 0 ? 'bg-muted/20' : ''} ${item.is_return ? 'bg-red-50 dark:bg-red-950/20' : ''}`}>
                          <TableCell className="font-mono text-xs py-1">{item.article_code || item.barcode || '---'}</TableCell>
                          <TableCell className="font-medium text-sm py-1">{item.product_name}</TableCell>
                          <TableCell className="text-center py-1">
                            <div className="flex items-center justify-center gap-0.5">
                              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => updateCartItemQuantity(item.product_id, item.quantity - 1)}>
                                <Minus className="h-3 w-3" />
                              </Button>
                              <Input
                                type="number"
                                value={item.quantity}
                                onChange={(e) => updateCartItemQuantity(item.product_id, parseInt(e.target.value) || 0)}
                                className="w-12 h-6 text-center text-sm p-0"
                              />
                              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => updateCartItemQuantity(item.product_id, item.quantity + 1)}>
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                          </TableCell>
                          <TableCell className="text-center py-1">
                            <Input
                              type="number"
                              value={item.unit_price}
                              onChange={(e) => updateCartItemPrice(item.product_id, e.target.value)}
                              className="w-20 h-6 text-center text-sm p-0"
                            />
                          </TableCell>
                          <TableCell className="text-center py-1">
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={item.discount_percent || ''}
                              onChange={(e) => updateCartItemDiscount(item.product_id, e.target.value)}
                              className="w-12 h-6 text-center text-sm p-0"
                            />
                          </TableCell>
                          <TableCell className="text-center font-semibold text-sm py-1">{formatCurrency(item.total)}</TableCell>
                          <TableCell className="py-1">
                            <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive hover:bg-destructive/10" onClick={() => removeFromCart(item.product_id)}>
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>

                {/* Mobile Cards View */}
                <div className="sm:hidden space-y-2 p-2">
                  {cart.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <ShoppingCart className="h-8 w-8 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">{language === 'ar' ? 'أضف منتجات' : 'Ajoutez des articles'}</p>
                    </div>
                  ) : (
                    cart.map((item, index) => (
                      <div 
                        key={item.product_id} 
                        className={`p-3 rounded-lg border ${item.is_return ? 'bg-red-50 border-red-200 dark:bg-red-950/20' : 'bg-muted/20'}`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">{item.name}</p>
                            <p className="text-xs text-muted-foreground">{item.code}</p>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 text-destructive shrink-0"
                            onClick={() => removeFromCart(item.product_id)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                        <div className="flex items-center justify-between mt-2 gap-2">
                          <div className="flex items-center gap-1">
                            <Button variant="outline" size="icon" className="h-7 w-7" onClick={() => updateQuantity(item.product_id, item.quantity - 1)}>
                              <Minus className="h-3 w-3" />
                            </Button>
                            <Input
                              type="number"
                              value={item.quantity}
                              onChange={(e) => updateQuantity(item.product_id, parseInt(e.target.value) || 1)}
                              className="w-12 h-7 text-center text-sm"
                            />
                            <Button variant="outline" size="icon" className="h-7 w-7" onClick={() => updateQuantity(item.product_id, item.quantity + 1)}>
                              <Plus className="h-3 w-3" />
                            </Button>
                          </div>
                          <div className="text-end">
                            <p className="text-xs text-muted-foreground">{formatCurrency(item.unit_price)} × {item.quantity}</p>
                            <p className="font-bold text-sm">{formatCurrency(item.total)}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Totals & Action Buttons - Responsive */}
              <div className="border-t p-2">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                  {/* Totals */}
                  <div className="flex items-center gap-3 sm:gap-4 w-full sm:w-auto justify-center sm:justify-start">
                    <div className="text-center">
                      <p className="text-[10px] text-muted-foreground">{language === 'ar' ? 'الفرعي' : 'Sous-total'}</p>
                      <p className="text-sm font-bold">{formatCurrency(subtotal)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] text-muted-foreground">{language === 'ar' ? 'خصم' : 'Remise'}</p>
                      <Input
                        type="number"
                        value={discount || ''}
                        onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                        className="w-14 sm:w-16 h-6 text-center text-sm"
                      />
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] text-muted-foreground">{language === 'ar' ? 'الإجمالي' : 'Total'}</p>
                      <p className="text-base sm:text-lg font-bold text-primary">{formatCurrency(total)}</p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <Button 
                      variant="outline"
                      onClick={clearCart}
                      className="h-9 px-3 gap-1 flex-1 sm:flex-none"
                      data-testid="annuler-btn"
                    >
                      <X className="h-4 w-4" />
                      {language === 'ar' ? 'إلغاء' : 'Annuler'}
                    </Button>
                    <Button
                      onClick={completeSale}
                      disabled={loading || cart.length === 0 || !hasOpenSession}
                      className="h-9 px-4 gap-1 flex-1 sm:flex-none"
                      data-testid="vente-btn"
                    >
                      <Check className="h-4 w-4" />
                      {language === 'ar' ? 'تأكيد' : 'Valider'}
                      <Badge variant="secondary" className="text-[10px] ms-1 hidden sm:inline">F10</Badge>
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right Sidebar - Product Shortcuts (Compact) - Hidden on mobile */}
          <div className="hidden md:block md:col-span-2" style={{ direction: isRTL ? 'rtl' : 'ltr' }}>
            <Card className="h-full">
              <CardHeader className="p-2 pb-1">
                <CardTitle className="text-xs text-center text-muted-foreground">
                  {language === 'ar' ? 'اختصارات' : 'Raccourcis'}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-1.5 pt-0">
                <div className="grid grid-cols-2 gap-1">
                  {productShortcuts.slice(0, 10).map((shortcut, index) => {
                    const productName = getShortcutProductName(shortcut);
                    const bgColor = shortcut.productId ? shortcut.color : undefined;
                    
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
                        style={{ backgroundColor: bgColor }}
                        className={`py-2 px-1 rounded text-[10px] font-medium text-center leading-tight transition-all h-10 flex items-center justify-center ${
                          shortcut.productId 
                            ? 'text-white hover:opacity-90 shadow-sm' 
                            : 'bg-muted text-muted-foreground hover:bg-muted/80 border border-dashed'
                        }`}
                        title={productName}
                        data-testid={`shortcut-${index}`}
                      >
                        <span className="line-clamp-2">{productName}</span>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Products Dialog */}
        <Dialog open={showProductsDialog} onOpenChange={setShowProductsDialog}>
          <DialogContent className="max-w-3xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>{language === 'ar' ? 'اختر منتج' : 'Choisir un produit'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute top-1/2 -translate-y-1/2 start-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder={language === 'ar' ? 'بحث بالاسم أو الباركود...' : 'Rechercher par nom ou code-barres...'}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="ps-9"
                  />
                </div>
                <Select value={selectedFamily} onValueChange={setSelectedFamily}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder={language === 'ar' ? 'العائلة' : 'Famille'} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{language === 'ar' ? 'الكل' : 'Tous'}</SelectItem>
                    {families.map(f => (
                      <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="max-h-96 overflow-y-auto border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{language === 'ar' ? 'المنتج' : 'Produit'}</TableHead>
                      <TableHead className="w-24 text-center">{language === 'ar' ? 'السعر' : 'Prix'}</TableHead>
                      <TableHead className="w-20 text-center">{language === 'ar' ? 'المخزون' : 'Stock'}</TableHead>
                      <TableHead className="w-20"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredProducts.slice(0, 50).map(product => (
                      <TableRow key={product.id} className="cursor-pointer hover:bg-muted/50" onClick={() => { addToCart(product); setShowProductsDialog(false); }}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{language === 'ar' ? product.name_ar : product.name_en}</p>
                            <p className="text-xs text-muted-foreground">{product.barcode || product.article_code}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">{formatCurrency(priceType === 'wholesale' ? product.wholesale_price : product.retail_price)}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant={product.quantity > 10 ? 'default' : product.quantity > 0 ? 'secondary' : 'destructive'}>
                            {product.quantity}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button size="sm" variant="ghost" className="h-8">
                            <Plus className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Customers Dialog */}
        <Dialog open={showCustomersDialog} onOpenChange={setShowCustomersDialog}>
          <DialogContent className="max-w-md max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>{language === 'ar' ? 'اختر زبون' : 'Choisir un client'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div className="max-h-80 overflow-y-auto border rounded-lg">
                {customers.map(customer => (
                  <div 
                    key={customer.id} 
                    className="p-3 border-b cursor-pointer hover:bg-muted/50"
                    onClick={() => { setSelectedCustomer(customer.id); setShowCustomersDialog(false); }}
                  >
                    <p className="font-medium">{customer.name}</p>
                    <p className="text-sm text-muted-foreground">{customer.phone}</p>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full gap-2" onClick={() => { setShowCustomersDialog(false); setShowNewCustomerDialog(true); }}>
                <UserPlus className="h-4 w-4" />
                {language === 'ar' ? 'إضافة زبون جديد' : 'Nouveau client'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Note Dialog */}
        <Dialog open={showNoteDialog} onOpenChange={setShowNoteDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>{language === 'ar' ? 'إضافة ملاحظة' : 'Ajouter une note'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Textarea
                value={saleNote}
                onChange={(e) => setSaleNote(e.target.value)}
                placeholder={language === 'ar' ? 'اكتب ملاحظة للفاتورة...' : 'Ecrivez une note pour la facture...'}
                rows={4}
              />
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowNoteDialog(false)} className="flex-1">
                  {language === 'ar' ? 'إلغاء' : 'Annuler'}
                </Button>
                <Button onClick={() => { toast.success(language === 'ar' ? 'تم حفظ الملاحظة' : 'Note enregistree'); setShowNoteDialog(false); }} className="flex-1">
                  {language === 'ar' ? 'حفظ' : 'Enregistrer'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Cash Operation Dialog */}
        <Dialog open={showCashDialog} onOpenChange={setShowCashDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {cashOperation.type === 'deposit' 
                  ? (language === 'ar' ? 'إيداع في الصندوق' : 'Depot en caisse')
                  : (language === 'ar' ? 'سحب من الصندوق' : 'Retrait de caisse')}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>{language === 'ar' ? 'المبلغ' : 'Montant'}</Label>
                <Input
                  type="number"
                  value={cashOperation.amount || ''}
                  onChange={(e) => setCashOperation(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                  placeholder="0.00"
                />
              </div>
              <div>
                <Label>{language === 'ar' ? 'ملاحظة' : 'Note'}</Label>
                <Input
                  value={cashOperation.note}
                  onChange={(e) => setCashOperation(prev => ({ ...prev, note: e.target.value }))}
                  placeholder={language === 'ar' ? 'سبب العملية...' : 'Raison de l\'operation...'}
                />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowCashDialog(false)} className="flex-1">
                  {language === 'ar' ? 'إلغاء' : 'Annuler'}
                </Button>
                <Button onClick={handleCashOperation} className="flex-1">
                  {language === 'ar' ? 'تأكيد' : 'Confirmer'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Sales History Dialog */}
        <Dialog open={showHistoryDialog} onOpenChange={setShowHistoryDialog}>
          <DialogContent className="max-w-3xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>{language === 'ar' ? 'سجل المبيعات' : 'Historique des ventes'}</DialogTitle>
            </DialogHeader>
            <div className="max-h-96 overflow-y-auto border rounded-lg">
              {historyLoading ? (
                <div className="p-8 text-center text-muted-foreground">
                  {language === 'ar' ? 'جاري التحميل...' : 'Chargement...'}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{language === 'ar' ? 'الرقم' : 'N°'}</TableHead>
                      <TableHead>{language === 'ar' ? 'التاريخ' : 'Date'}</TableHead>
                      <TableHead>{language === 'ar' ? 'الزبون' : 'Client'}</TableHead>
                      <TableHead className="text-center">{language === 'ar' ? 'المبلغ' : 'Montant'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {salesHistory.map(sale => (
                      <TableRow key={sale.id}>
                        <TableCell className="font-mono">{sale.invoice_number || sale.code}</TableCell>
                        <TableCell>{new Date(sale.created_at).toLocaleDateString()}</TableCell>
                        <TableCell>{sale.customer_name || (language === 'ar' ? 'زبون عابر' : 'Client passant')}</TableCell>
                        <TableCell className="text-center font-semibold">{formatCurrency(sale.total)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </DialogContent>
        </Dialog>

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
                  onClick={() => {
                    if (lastSaleId) {
                      const printerSize = receiptSettings?.thermal_printer_size || '80mm';
                      printThermalReceipt(lastSaleId, printerSize);
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
