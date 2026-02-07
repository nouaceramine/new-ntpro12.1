import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
  CreditCard,
  Banknote,
  Wallet,
  User,
  Truck,
  AlertCircle,
  Clock,
  Package,
  X,
  Check,
  RotateCcw,
  Ban,
  Bell,
  Users,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function POSPage() {
  const { t, language, isRTL } = useLanguage();
  const searchInputRef = useRef(null);
  const searchDropdownRef = useRef(null);
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [families, setFamilies] = useState([]);
  const [customerFamilies, setCustomerFamilies] = useState([]);
  const [wilayas, setWilayas] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [selectedFamily, setSelectedFamily] = useState('all');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDebt, setCustomerDebt] = useState(0);
  const [discount, setDiscount] = useState(0);
  const [paidAmount, setPaidAmount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [paymentType, setPaymentType] = useState('cash');
  const [loading, setLoading] = useState(false);
  const [priceType, setPriceType] = useState('retail');
  
  // Session state
  const [hasOpenSession, setHasOpenSession] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  
  // Delivery state
  const [deliveryEnabled, setDeliveryEnabled] = useState(false);
  const [selectedWilaya, setSelectedWilaya] = useState('');
  const [deliveryType, setDeliveryType] = useState('desk');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [deliveryCity, setDeliveryCity] = useState('');
  const [deliveryFee, setDeliveryFee] = useState(0);
  
  // Dialogs
  const [showDebtDialog, setShowDebtDialog] = useState(false);
  const [debtPaymentAmount, setDebtPaymentAmount] = useState(0);
  const [showDeliveryDialog, setShowDeliveryDialog] = useState(false);
  const [showNewCustomerDialog, setShowNewCustomerDialog] = useState(false);
  const [newCustomerData, setNewCustomerData] = useState({ name: '', phone: '', email: '', address: '', family_id: '' });
  const [savingCustomer, setSavingCustomer] = useState(false);
  const [showNewFamilyInput, setShowNewFamilyInput] = useState(false);
  const [newFamilyName, setNewFamilyName] = useState('');
  
  // Blacklist state
  const [blacklist, setBlacklist] = useState([]);
  const [selectedCustomerBlacklisted, setSelectedCustomerBlacklisted] = useState(false);
  const [blacklistReason, setBlacklistReason] = useState('');
  
  // Debt reminders
  const [debtReminders, setDebtReminders] = useState([]);
  const [showDebtRemindersPanel, setShowDebtRemindersPanel] = useState(false);

  useEffect(() => {
    checkOpenSession();
    fetchProducts();
    fetchCustomers();
    fetchFamilies();
    fetchCustomerFamilies();
    fetchBlacklist();
    fetchDebtReminders();
    fetchWilayas();
  }, []);

  // Close search dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchDropdownRef.current && !searchDropdownRef.current.contains(event.target)) {
        setShowSearchResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
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

  const fetchDebtReminders = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/debt-reminders/pending`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDebtReminders(response.data);
    } catch (error) {
      console.error('Error fetching debt reminders:', error);
    }
  };

  const fetchCustomerDebt = async (customerId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/customers/${customerId}/debt`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomerDebt(response.data.total_debt || 0);
      
      // Check if customer is blacklisted
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

  // Filter products based on search query
  const filteredProducts = products.filter(p => {
    if (selectedFamily !== 'all' && p.family_id !== selectedFamily) {
      return false;
    }
    if (!searchQuery) return false; // Only show when there's a search query
    const query = searchQuery.toLowerCase();
    return (
      p.name_en.toLowerCase().includes(query) ||
      p.name_ar.toLowerCase().includes(query) ||
      p.barcode?.toLowerCase().includes(query) ||
      p.compatible_models.some(m => m.toLowerCase().includes(query))
    );
  });

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.product_id === product.id);
    const price = priceType === 'wholesale' ? product.wholesale_price : product.retail_price;
    
    if (existingItem) {
      if (existingItem.quantity >= product.quantity) {
        toast.error(t.outOfStock);
        return;
      }
      setCart(cart.map(item => 
        item.product_id === product.id
          ? { ...item, quantity: item.quantity + 1, total: (item.quantity + 1) * item.unit_price }
          : item
      ));
    } else {
      if (product.quantity <= 0) {
        toast.error(t.outOfStock);
        return;
      }
      setCart([...cart, {
        product_id: product.id,
        product_name: language === 'ar' ? product.name_ar : product.name_en,
        barcode: product.barcode,
        quantity: 1,
        unit_price: price,
        discount: 0,
        total: price
      }]);
    }
    
    setSearchQuery('');
    setShowSearchResults(false);
    searchInputRef.current?.focus();
  };

  const updateCartItemQuantity = (productId, newQty) => {
    const product = products.find(p => p.id === productId);
    if (newQty <= 0) {
      removeFromCart(productId);
      return;
    }
    // Only check stock for existing products, not custom items
    if (product && newQty > product.quantity) {
      toast.error(t.outOfStock);
      return;
    }
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        return { ...item, quantity: newQty, total: newQty * item.unit_price - item.discount };
      }
      return item;
    }));
  };

  const updateCartItemName = (productId, newName) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        return { ...item, product_name: newName };
      }
      return item;
    }));
  };

  const updateCartItemPrice = (productId, newPrice) => {
    const price = parseFloat(newPrice) || 0;
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const newTotal = item.quantity * price - item.discount;
        return { ...item, unit_price: price, total: newTotal };
      }
      return item;
    }));
  };

  const updateCartItemDiscount = (productId, discountPercent) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const disc = (parseFloat(discountPercent) || 0) / 100 * item.quantity * item.unit_price;
        return { ...item, discount: disc, discount_percent: discountPercent, total: item.quantity * item.unit_price - disc };
      }
      return item;
    }));
  };

  // Add custom product to cart
  const addCustomProduct = () => {
    const customId = `custom-${Date.now()}`;
    setCart([...cart, {
      product_id: customId,
      product_name: language === 'ar' ? 'منتج مخصص' : 'Article personnalisé',
      barcode: '',
      quantity: 1,
      unit_price: 0,
      discount: 0,
      total: 0,
      is_custom: true
    }]);
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
  };

  const subtotal = cart.reduce((sum, item) => sum + item.total, 0);
  const total = subtotal - discount + (deliveryEnabled ? deliveryFee : 0);
  const remaining = total - paidAmount;

  const handlePayDebt = async () => {
    if (!selectedCustomer || debtPaymentAmount <= 0) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/customers/${selectedCustomer}/debt/pay`, {
        customer_id: selectedCustomer,
        amount: debtPaymentAmount,
        payment_method: paymentMethod
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t.debtPaid);
      setShowDebtDialog(false);
      setDebtPaymentAmount(0);
      fetchCustomerDebt(selectedCustomer);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    }
  };

  // Add new customer family
  const handleAddCustomerFamily = async () => {
    if (!newFamilyName.trim()) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/customer-families`, 
        { name: newFamilyName.trim() },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      setCustomerFamilies([...customerFamilies, response.data]);
      setNewCustomerData(prev => ({ ...prev, family_id: response.data.id }));
      setNewFamilyName('');
      setShowNewFamilyInput(false);
      toast.success(language === 'ar' ? 'تمت إضافة العائلة' : 'Famille ajoutée');
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    }
  };

  // Add new customer
  const handleAddCustomer = async (createNew = false) => {
    if (!newCustomerData.name) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم الزبون' : 'Veuillez entrer le nom du client');
      return;
    }

    // Check if phone is blacklisted
    if (newCustomerData.phone) {
      const isBlacklisted = blacklist.some(b => b.phone === newCustomerData.phone);
      if (isBlacklisted) {
        toast.error(language === 'ar' ? 'هذا الرقم في القائمة السوداء!' : 'Ce numéro est sur liste noire!');
        return;
      }
    }

    setSavingCustomer(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/customers`, newCustomerData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تمت إضافة الزبون بنجاح' : 'Client ajouté avec succès');
      
      // Reset form
      setNewCustomerData({ name: '', phone: '', email: '', address: '', family_id: '' });
      fetchCustomers();
      
      if (createNew) {
        // Keep dialog open for new entry
      } else {
        setShowNewCustomerDialog(false);
        // Auto-select the new customer
        if (response.data?.id) {
          setSelectedCustomer(response.data.id);
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSavingCustomer(false);
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
      toast.error(language === 'ar' ? 'يجب اختيار زبون للبيع بالدين' : 'Sélectionnez un client pour le crédit');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const wilaya = wilayas.find(w => w.code === selectedWilaya);
      
      const saleData = {
        customer_id: selectedCustomer,
        items: cart.map(item => ({
          product_id: item.is_custom ? null : item.product_id,
          product_name: item.product_name,
          quantity: item.quantity,
          unit_price: item.unit_price,
          discount: item.discount || 0,
          total: item.total
        })),
        subtotal,
        discount,
        total: subtotal - discount,
        paid_amount: paymentType === 'credit' ? 0 : (paidAmount || total),
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
      toast.success(language === 'ar' ? 'تمت عملية البيع بنجاح' : 'Vente effectuée avec succès');
      
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
      
      clearCart();
      fetchProducts();
    } catch (error) {
      console.error('Sale error:', error);
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'حدث خطأ أثناء البيع' : 'Erreur lors de la vente'));
    } finally {
      setLoading(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        completeSale();
      }
      if (e.key === 'Escape') {
        setSearchQuery('');
        setShowSearchResults(false);
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart, hasOpenSession]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-DZ', { minimumFractionDigits: 2 }).format(amount || 0);
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    setShowSearchResults(value.length > 0);
  };

  return (
    <Layout>
      <div className="space-y-4" data-testid="pos-page">
        
        {/* No Session Warning */}
        {!checkingSession && !hasOpenSession && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">
                {language === 'ar' ? 'لا توجد حصة مفتوحة - يجب فتح حصة جديدة قبل البيع' : 'Aucune session ouverte - Ouvrez une session pour vendre'}
              </span>
            </div>
            <Link to="/daily-sessions">
              <Button size="sm" className="gap-2 bg-amber-600 hover:bg-amber-700">
                <Clock className="h-4 w-4" />
                {language === 'ar' ? 'فتح حصة' : 'Ouvrir session'}
              </Button>
            </Link>
          </div>
        )}

        {/* Top Section - Search & Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4 flex-wrap">
              {/* Search with Dropdown */}
              <div className="relative flex-1 min-w-[300px]" ref={searchDropdownRef}>
                <Search className={`absolute top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
                <Input
                  ref={searchInputRef}
                  type="text"
                  placeholder={language === 'ar' ? 'البحث عن منتج بالاسم أو الباركود...' : 'Rechercher un article...'}
                  value={searchQuery}
                  onChange={handleSearchChange}
                  onFocus={() => searchQuery && setShowSearchResults(true)}
                  className={`h-11 ${isRTL ? 'pr-10' : 'pl-10'}`}
                  data-testid="pos-search-input"
                />
                
                {/* Search Results Dropdown */}
                {showSearchResults && filteredProducts.length > 0 && (
                  <div className="absolute z-50 top-full mt-1 w-full bg-white border rounded-lg shadow-lg max-h-80 overflow-auto">
                    {filteredProducts.slice(0, 10).map((product) => (
                      <div
                        key={product.id}
                        onClick={() => addToCart(product)}
                        className={`px-4 py-3 cursor-pointer hover:bg-blue-50 border-b last:border-b-0 flex items-center justify-between ${
                          product.quantity <= 0 ? 'opacity-50 bg-red-50' : ''
                        }`}
                        data-testid={`search-result-${product.id}`}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
                            <Package className="h-5 w-5 text-gray-400" />
                          </div>
                          <div>
                            <p className="font-medium">{language === 'ar' ? product.name_ar : product.name_en}</p>
                            <p className="text-sm text-muted-foreground">
                              {product.barcode || '---'} • {language === 'ar' ? 'المخزون:' : 'Stock:'} {product.quantity}
                            </p>
                          </div>
                        </div>
                        <div className="text-end">
                          <p className="font-bold text-blue-600">
                            {formatCurrency(priceType === 'wholesale' ? product.wholesale_price : product.retail_price)} {t.currency}
                          </p>
                          {product.quantity <= 0 && (
                            <Badge variant="destructive" className="text-xs">{t.outOfStock}</Badge>
                          )}
                        </div>
                      </div>
                    ))}
                    {filteredProducts.length > 10 && (
                      <div className="px-4 py-2 text-center text-sm text-muted-foreground bg-gray-50">
                        {language === 'ar' ? `+${filteredProducts.length - 10} منتج آخر...` : `+${filteredProducts.length - 10} autres articles...`}
                      </div>
                    )}
                  </div>
                )}

                {showSearchResults && searchQuery && filteredProducts.length === 0 && (
                  <div className="absolute z-50 top-full mt-1 w-full bg-white border rounded-lg shadow-lg p-4 text-center text-muted-foreground">
                    <Package className="h-8 w-8 mx-auto mb-2 opacity-30" />
                    {language === 'ar' ? 'لا توجد منتجات مطابقة' : 'Aucun article trouvé'}
                  </div>
                )}
              </div>

              {/* Filters */}
              <Select value={selectedFamily} onValueChange={setSelectedFamily}>
                <SelectTrigger className="w-44 h-11">
                  <SelectValue placeholder={t.allFamilies} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.allFamilies}</SelectItem>
                  {families.map(f => (
                    <SelectItem key={f.id} value={f.id}>
                      {language === 'ar' ? f.name_ar : f.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={priceType} onValueChange={setPriceType}>
                <SelectTrigger className="w-36 h-11">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="retail">{t.retailPrice}</SelectItem>
                  <SelectItem value="wholesale">{t.wholesalePrice}</SelectItem>
                </SelectContent>
              </Select>

              {/* Customer Selection */}
              <div className="flex items-center gap-2">
                <Select value={selectedCustomer || 'walk-in'} onValueChange={(v) => setSelectedCustomer(v === 'walk-in' ? null : v)}>
                  <SelectTrigger className={`w-48 h-11 ${selectedCustomerBlacklisted ? 'border-red-500 bg-red-50' : ''}`} data-testid="customer-select">
                    {selectedCustomerBlacklisted ? (
                      <Ban className="h-4 w-4 me-2 text-red-500" />
                    ) : (
                      <User className="h-4 w-4 me-2 text-muted-foreground" />
                    )}
                    <SelectValue placeholder={t.selectCustomer} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="walk-in">{t.walkInCustomer}</SelectItem>
                    {customers.map(c => {
                      const isBlacklisted = blacklist.some(b => b.phone === c.phone);
                      return (
                        <SelectItem key={c.id} value={c.id} className={isBlacklisted ? 'text-red-500 bg-red-50' : ''}>
                          {isBlacklisted && <Ban className="h-3 w-3 inline me-1" />}
                          {c.name}
                          {c.total_debt > 0 && <span className="text-amber-600 ms-1">({formatCurrency(c.total_debt)})</span>}
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
                
                {/* Add New Customer Button */}
                <Button
                  variant="outline"
                  size="icon"
                  className="h-11 w-11"
                  onClick={() => setShowNewCustomerDialog(true)}
                  title={language === 'ar' ? 'إضافة زبون جديد' : 'Ajouter client'}
                  data-testid="add-customer-btn"
                >
                  <Plus className="h-4 w-4" />
                </Button>

                {/* Debt Reminders Button */}
                {debtReminders.length > 0 && (
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-11 w-11 relative"
                    onClick={() => setShowDebtRemindersPanel(!showDebtRemindersPanel)}
                    title={language === 'ar' ? 'تذكيرات الديون' : 'Rappels de dettes'}
                  >
                    <Bell className="h-4 w-4 text-amber-600" />
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {debtReminders.length}
                    </span>
                  </Button>
                )}
              </div>

              {/* Blacklist Warning */}
              {selectedCustomerBlacklisted && (
                <div className="flex items-center gap-2 px-3 py-2 bg-red-100 border border-red-300 rounded-lg">
                  <Ban className="h-5 w-5 text-red-600" />
                  <span className="text-red-700 text-sm font-medium">
                    {language === 'ar' ? 'تحذير: هذا الزبون في القائمة السوداء!' : 'Attention: Client sur liste noire!'}
                    {blacklistReason && ` (${blacklistReason})`}
                  </span>
                </div>
              )}

              {selectedCustomer && customerDebt > 0 && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    setDebtPaymentAmount(customerDebt);
                    setShowDebtDialog(true);
                  }}
                  className="gap-1"
                >
                  <AlertCircle className="h-4 w-4" />
                  {formatCurrency(customerDebt)} {t.currency}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Debt Reminders Panel */}
        {showDebtRemindersPanel && debtReminders.length > 0 && (
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-amber-800 flex items-center gap-2 text-base">
                  <Bell className="h-5 w-5" />
                  {language === 'ar' ? 'تذكيرات ديون الزبائن' : 'Rappels de dettes clients'}
                  <Badge className="bg-amber-600">{debtReminders.length}</Badge>
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDebtRemindersPanel(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2 max-h-40 overflow-auto">
                {debtReminders.slice(0, 5).map((reminder) => (
                  <div 
                    key={reminder.customer_id}
                    className={`flex items-center justify-between p-2 rounded-lg cursor-pointer hover:bg-amber-100 ${
                      reminder.is_urgent ? 'bg-red-100 border border-red-200' : 'bg-white'
                    }`}
                    onClick={() => {
                      setSelectedCustomer(reminder.customer_id);
                      setShowDebtRemindersPanel(false);
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <User className={`h-4 w-4 ${reminder.is_urgent ? 'text-red-600' : 'text-amber-600'}`} />
                      <div>
                        <p className="font-medium text-sm">{reminder.customer_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {reminder.phone || '---'} • {language === 'ar' ? `منذ ${reminder.days_since_last_purchase} يوم` : `Il y a ${reminder.days_since_last_purchase} jours`}
                        </p>
                      </div>
                    </div>
                    <div className="text-end">
                      <p className={`font-bold ${reminder.is_urgent ? 'text-red-600' : 'text-amber-700'}`}>
                        {formatCurrency(reminder.total_debt)} {t.currency}
                      </p>
                      {reminder.is_urgent && (
                        <Badge variant="destructive" className="text-xs">
                          {language === 'ar' ? 'عاجل' : 'Urgent'}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content - Cart */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <ShoppingCart className="h-5 w-5 text-primary" />
                {language === 'ar' ? 'سلة المشتريات' : 'Panier'}
                <Badge className="ms-2">{cart.length}</Badge>
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={addCustomProduct}
                  className="gap-1"
                >
                  <Plus className="h-4 w-4" />
                  {language === 'ar' ? 'منتج مخصص' : 'Article libre'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearCart}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <RotateCcw className="h-4 w-4 me-1" />
                  {language === 'ar' ? 'مسح الكل' : 'Effacer'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead>{language === 'ar' ? 'المنتج' : 'Article'}</TableHead>
                    <TableHead className="w-[120px] text-center">{language === 'ar' ? 'الكمية' : 'Qté'}</TableHead>
                    <TableHead className="w-[120px] text-center">{language === 'ar' ? 'السعر' : 'Prix'}</TableHead>
                    <TableHead className="w-[80px] text-center">{language === 'ar' ? 'خصم %' : 'R. %'}</TableHead>
                    <TableHead className="w-[120px] text-center">{language === 'ar' ? 'المجموع' : 'Total'}</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cart.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                        <ShoppingCart className="h-12 w-12 mx-auto mb-3 opacity-30" />
                        <p>{language === 'ar' ? 'السلة فارغة - ابحث عن منتج لإضافته' : 'Panier vide - Recherchez un article'}</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    cart.map((item) => (
                      <TableRow key={item.product_id}>
                        <TableCell>
                          <Input
                            type="text"
                            value={item.product_name}
                            onChange={(e) => updateCartItemName(item.product_id, e.target.value)}
                            className="h-8 font-medium"
                            placeholder={language === 'ar' ? 'اسم المنتج' : 'Nom article'}
                          />
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => updateCartItemQuantity(item.product_id, item.quantity - 1)}
                            >
                              <Minus className="h-3 w-3" />
                            </Button>
                            <Input
                              type="number"
                              min="1"
                              value={item.quantity}
                              onChange={(e) => updateCartItemQuantity(item.product_id, parseInt(e.target.value) || 1)}
                              className="w-14 h-8 text-center"
                            />
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => updateCartItemQuantity(item.product_id, item.quantity + 1)}
                            >
                              <Plus className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            value={item.unit_price}
                            onChange={(e) => updateCartItemPrice(item.product_id, e.target.value)}
                            className="w-24 h-8 text-center"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            max="100"
                            placeholder="0"
                            value={item.discount_percent || ''}
                            onChange={(e) => updateCartItemDiscount(item.product_id, e.target.value)}
                            className="w-16 h-8 text-center"
                          />
                        </TableCell>
                        <TableCell className="text-center font-bold text-green-600">
                          {formatCurrency(item.total)}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:bg-destructive/10"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Footer - Payment & Totals */}
        <Card>
          <CardContent className="p-4">
            {/* Payment Options Row */}
            <div className="flex items-center justify-between gap-4 pb-4 border-b mb-4 flex-wrap">
              <div className="flex items-center gap-4 flex-wrap">
                {/* Payment Type */}
                <div className="flex items-center gap-2">
                  <Label className="text-muted-foreground">{language === 'ar' ? 'نوع الدفع:' : 'Type:'}</Label>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant={paymentType === 'cash' ? 'default' : 'outline'}
                      onClick={() => setPaymentType('cash')}
                      className={paymentType === 'cash' ? 'bg-green-600 hover:bg-green-700' : ''}
                    >
                      {language === 'ar' ? 'نقدي' : 'Comptant'}
                    </Button>
                    <Button
                      size="sm"
                      variant={paymentType === 'credit' ? 'default' : 'outline'}
                      onClick={() => setPaymentType('credit')}
                      className={paymentType === 'credit' ? 'bg-amber-600 hover:bg-amber-700' : ''}
                    >
                      {language === 'ar' ? 'دين' : 'Crédit'}
                    </Button>
                    <Button
                      size="sm"
                      variant={paymentType === 'partial' ? 'default' : 'outline'}
                      onClick={() => setPaymentType('partial')}
                      className={paymentType === 'partial' ? 'bg-blue-600 hover:bg-blue-700' : ''}
                    >
                      {language === 'ar' ? 'جزئي' : 'Partiel'}
                    </Button>
                  </div>
                </div>

                {/* Payment Method */}
                {paymentType !== 'credit' && (
                  <div className="flex items-center gap-2">
                    <Label className="text-muted-foreground">{language === 'ar' ? 'الوسيلة:' : 'Mode:'}</Label>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                        onClick={() => setPaymentMethod('cash')}
                      >
                        <Banknote className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant={paymentMethod === 'bank' ? 'default' : 'outline'}
                        onClick={() => setPaymentMethod('bank')}
                      >
                        <CreditCard className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant={paymentMethod === 'wallet' ? 'default' : 'outline'}
                        onClick={() => setPaymentMethod('wallet')}
                      >
                        <Wallet className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* Delivery */}
                <div className="flex items-center gap-2">
                  <Truck className="h-4 w-4 text-muted-foreground" />
                  <Label className="text-muted-foreground">{language === 'ar' ? 'توصيل' : 'Livraison'}</Label>
                  <Switch
                    checked={deliveryEnabled}
                    onCheckedChange={setDeliveryEnabled}
                  />
                  {deliveryEnabled && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowDeliveryDialog(true)}
                    >
                      {selectedWilaya || (language === 'ar' ? 'إعداد' : 'Config')}
                    </Button>
                  )}
                </div>
              </div>

              {/* Paid Amount */}
              {paymentType !== 'credit' && (
                <div className="flex items-center gap-2">
                  <Label className="text-muted-foreground">{language === 'ar' ? 'المدفوع:' : 'Payé:'}</Label>
                  <Input
                    type="number"
                    min="0"
                    value={paidAmount || ''}
                    onChange={(e) => setPaidAmount(parseFloat(e.target.value) || 0)}
                    className="w-32 h-9"
                    data-testid="paid-amount-input"
                  />
                </div>
              )}
            </div>

            {/* Totals & Actions Row */}
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">{language === 'ar' ? 'المجموع الفرعي' : 'Sous total'}</p>
                  <p className="text-xl font-bold">{formatCurrency(subtotal)}</p>
                </div>

                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">{language === 'ar' ? 'الخصم' : 'Remise'}</p>
                  <Input
                    type="number"
                    min="0"
                    value={discount || ''}
                    onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                    className="w-24 h-8 text-center"
                    data-testid="total-discount-input"
                  />
                </div>

                {deliveryEnabled && deliveryFee > 0 && (
                  <div className="text-center">
                    <p className="text-xs text-muted-foreground mb-1">{language === 'ar' ? 'التوصيل' : 'Livraison'}</p>
                    <p className="text-xl font-bold text-blue-600">+{formatCurrency(deliveryFee)}</p>
                  </div>
                )}

                {(paymentType === 'credit' || (paymentType === 'partial' && remaining > 0)) && (
                  <div className="text-center">
                    <p className="text-xs text-muted-foreground mb-1">{language === 'ar' ? 'الدين' : 'Crédit'}</p>
                    <p className="text-xl font-bold text-amber-600">
                      {formatCurrency(paymentType === 'credit' ? total : remaining)}
                    </p>
                  </div>
                )}

                <div className="text-center px-6 py-3 bg-primary text-primary-foreground rounded-lg">
                  <p className="text-xs opacity-80 mb-1">{language === 'ar' ? 'الإجمالي' : 'Total'}</p>
                  <p className="text-2xl font-bold">{formatCurrency(total)} <span className="text-sm">{t.currency}</span></p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  onClick={clearCart}
                  className="h-12 px-6"
                >
                  <RotateCcw className="h-5 w-5 me-2" />
                  {language === 'ar' ? 'إلغاء' : 'Annuler'}
                </Button>

                <Button
                  onClick={completeSale}
                  disabled={loading || cart.length === 0 || !hasOpenSession}
                  className="h-12 px-8 bg-green-600 hover:bg-green-700 text-lg gap-2"
                  data-testid="complete-sale-btn"
                >
                  <Check className="h-5 w-5" />
                  {loading ? (language === 'ar' ? 'جاري...' : 'Chargement...') : (language === 'ar' ? 'تأكيد البيع' : 'Valider')}
                  <span className="text-xs opacity-70">(Ctrl+Enter)</span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Debt Payment Dialog */}
      <Dialog open={showDebtDialog} onOpenChange={setShowDebtDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{t.payDebt}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t.totalDebt}</Label>
              <p className="text-xl font-bold text-amber-600">{formatCurrency(customerDebt)} {t.currency}</p>
            </div>
            <div>
              <Label>{t.amount}</Label>
              <Input
                type="number"
                min="0"
                max={customerDebt}
                value={debtPaymentAmount}
                onChange={(e) => setDebtPaymentAmount(parseFloat(e.target.value) || 0)}
                data-testid="debt-payment-input"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setPaymentMethod('cash')}
                className="flex-1"
              >
                <Banknote className="h-4 w-4 me-1" />
                {t.cash}
              </Button>
              <Button
                variant={paymentMethod === 'bank' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setPaymentMethod('bank')}
                className="flex-1"
              >
                <CreditCard className="h-4 w-4 me-1" />
                {t.bank}
              </Button>
            </div>
            <div className="flex gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowDebtDialog(false)} className="flex-1">
                {t.cancel}
              </Button>
              <Button onClick={handlePayDebt} className="flex-1 bg-green-600 hover:bg-green-700" disabled={debtPaymentAmount <= 0}>
                {t.confirm}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delivery Settings Dialog */}
      <Dialog open={showDeliveryDialog} onOpenChange={setShowDeliveryDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Truck className="h-5 w-5" />
              {language === 'ar' ? 'إعدادات التوصيل' : 'Paramètres de livraison'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t.selectWilaya}</Label>
              <Select value={selectedWilaya} onValueChange={setSelectedWilaya}>
                <SelectTrigger data-testid="wilaya-select">
                  <SelectValue placeholder={t.selectWilaya} />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  {wilayas.map(w => (
                    <SelectItem key={w.code} value={w.code}>
                      {w.code} - {language === 'ar' ? w.name_ar : w.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2">
              <Button
                variant={deliveryType === 'desk' ? 'default' : 'outline'}
                onClick={() => setDeliveryType('desk')}
                className="flex-1"
              >
                {t.officeDelivery}
              </Button>
              <Button
                variant={deliveryType === 'home' ? 'default' : 'outline'}
                onClick={() => setDeliveryType('home')}
                className="flex-1"
              >
                {t.homeDelivery}
              </Button>
            </div>

            <div>
              <Label>{t.deliveryCity}</Label>
              <Input
                value={deliveryCity}
                onChange={(e) => setDeliveryCity(e.target.value)}
              />
            </div>

            <div>
              <Label>{t.deliveryAddress}</Label>
              <Input
                value={deliveryAddress}
                onChange={(e) => setDeliveryAddress(e.target.value)}
              />
            </div>

            {deliveryFee > 0 && (
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex justify-between text-lg font-bold">
                  <span>{t.deliveryFee}</span>
                  <span className="text-blue-600">{formatCurrency(deliveryFee)} {t.currency}</span>
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowDeliveryDialog(false)} className="flex-1">
                {t.cancel}
              </Button>
              <Button onClick={() => setShowDeliveryDialog(false)} className="flex-1 bg-blue-600 hover:bg-blue-700">
                {t.confirm}
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
              <User className="h-5 w-5" />
              {language === 'ar' ? 'إضافة زبون جديد' : 'Ajouter un client'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{language === 'ar' ? 'الاسم' : 'Nom'} *</Label>
              <Input
                value={newCustomerData.name}
                onChange={(e) => setNewCustomerData(prev => ({ ...prev, name: e.target.value }))}
                placeholder={language === 'ar' ? 'اسم الزبون' : 'Nom du client'}
                data-testid="new-customer-name"
              />
            </div>

            <div>
              <Label>{language === 'ar' ? 'رقم الهاتف' : 'Téléphone'}</Label>
              <Input
                type="tel"
                value={newCustomerData.phone}
                onChange={(e) => setNewCustomerData(prev => ({ ...prev, phone: e.target.value }))}
                placeholder="05XX XXX XXX"
                dir="ltr"
              />
              {newCustomerData.phone && blacklist.some(b => b.phone === newCustomerData.phone) && (
                <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                  <Ban className="h-3 w-3" />
                  {language === 'ar' ? 'هذا الرقم في القائمة السوداء!' : 'Ce numéro est sur liste noire!'}
                </p>
              )}
            </div>

            {/* Customer Family Selection */}
            <div>
              <Label className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                {language === 'ar' ? 'عائلة الزبون' : 'Famille du client'}
              </Label>
              {!showNewFamilyInput ? (
                <div className="flex gap-2">
                  <Select 
                    value={newCustomerData.family_id || 'none'} 
                    onValueChange={(v) => setNewCustomerData(prev => ({ ...prev, family_id: v === 'none' ? '' : v }))}
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder={language === 'ar' ? 'اختر العائلة' : 'Choisir famille'} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">{language === 'ar' ? 'بدون عائلة' : 'Sans famille'}</SelectItem>
                      {customerFamilies.map(f => (
                        <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => setShowNewFamilyInput(true)}
                    title={language === 'ar' ? 'إضافة عائلة جديدة' : 'Ajouter nouvelle famille'}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Input
                    value={newFamilyName}
                    onChange={(e) => setNewFamilyName(e.target.value)}
                    placeholder={language === 'ar' ? 'اسم العائلة الجديدة' : 'Nom de la nouvelle famille'}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    size="icon"
                    onClick={handleAddCustomerFamily}
                    disabled={!newFamilyName.trim()}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => {
                      setShowNewFamilyInput(false);
                      setNewFamilyName('');
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            <div>
              <Label>{language === 'ar' ? 'البريد الإلكتروني' : 'Email'}</Label>
              <Input
                type="email"
                value={newCustomerData.email}
                onChange={(e) => setNewCustomerData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="email@example.com"
                dir="ltr"
              />
            </div>

            <div>
              <Label>{language === 'ar' ? 'العنوان' : 'Adresse'}</Label>
              <Input
                value={newCustomerData.address}
                onChange={(e) => setNewCustomerData(prev => ({ ...prev, address: e.target.value }))}
                placeholder={language === 'ar' ? 'عنوان الزبون' : 'Adresse du client'}
              />
            </div>

            <div className="flex gap-2 pt-4">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowNewCustomerDialog(false);
                  setNewCustomerData({ name: '', phone: '', email: '', address: '', family_id: '' });
                  setShowNewFamilyInput(false);
                  setNewFamilyName('');
                }} 
                className="flex-1"
              >
                {t.cancel}
              </Button>
              <Button 
                onClick={handleAddCustomer} 
                disabled={savingCustomer || !newCustomerData.name || (newCustomerData.phone && blacklist.some(b => b.phone === newCustomerData.phone))}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                {savingCustomer ? (language === 'ar' ? 'جاري الحفظ...' : 'Enregistrement...') : (language === 'ar' ? 'حفظ' : 'Enregistrer')}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
