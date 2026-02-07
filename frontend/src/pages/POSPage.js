import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
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
  Trash2, 
  Printer,
  CreditCard,
  Banknote,
  Wallet,
  User,
  Truck,
  AlertCircle,
  FolderTree,
  Clock,
  Package,
  Receipt,
  X,
  Check,
  RotateCcw,
  FileText
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function POSPage() {
  const { t, language, isRTL } = useLanguage();
  const searchInputRef = useRef(null);
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [families, setFamilies] = useState([]);
  const [wilayas, setWilayas] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
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
  
  // Debt dialog
  const [showDebtDialog, setShowDebtDialog] = useState(false);
  const [debtPaymentAmount, setDebtPaymentAmount] = useState(0);
  
  // Delivery dialog
  const [showDeliveryDialog, setShowDeliveryDialog] = useState(false);

  // Active tab in left panel
  const [activeTab, setActiveTab] = useState('products');

  useEffect(() => {
    checkOpenSession();
    fetchProducts();
    fetchCustomers();
    fetchFamilies();
    fetchWilayas();
  }, []);

  const checkOpenSession = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/sessions/my-open`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHasOpenSession(!!response.data);
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

  const fetchWilayas = async () => {
    try {
      const response = await axios.get(`${API}/delivery/wilayas`);
      setWilayas(response.data);
    } catch (error) {
      console.error('Error fetching wilayas:', error);
    }
  };

  const fetchCustomerDebt = async (customerId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/customers/${customerId}/debt`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomerDebt(response.data.total_debt || 0);
    } catch (error) {
      console.error('Error fetching customer debt:', error);
      setCustomerDebt(0);
    }
  };

  const filteredProducts = products.filter(p => {
    if (selectedFamily !== 'all' && p.family_id !== selectedFamily) {
      return false;
    }
    if (!searchQuery) return true;
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
    searchInputRef.current?.focus();
  };

  const updateCartItemQuantity = (productId, newQty) => {
    const product = products.find(p => p.id === productId);
    if (newQty <= 0) {
      removeFromCart(productId);
      return;
    }
    if (newQty > product.quantity) {
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

  const updateCartItemDiscount = (productId, discountPercent) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const disc = (parseFloat(discountPercent) || 0) / 100 * item.quantity * item.unit_price;
        return { ...item, discount: disc, discount_percent: discountPercent, total: item.quantity * item.unit_price - disc };
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
  };

  const subtotal = cart.reduce((sum, item) => sum + item.total, 0);
  const taxAmount = subtotal * 0; // No TVA for now, can be configured
  const total = subtotal - discount + taxAmount + (deliveryEnabled ? deliveryFee : 0);
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

  const completeSale = async () => {
    if (!hasOpenSession) {
      toast.error(language === 'ar' 
        ? 'يجب فتح حصة جديدة قبل البيع'
        : 'Vous devez ouvrir une session avant de vendre');
      return;
    }
    
    if (cart.length === 0) {
      toast.error(t.emptyCart);
      return;
    }

    if (paymentType !== 'cash' && !selectedCustomer) {
      toast.error(t.customerRequired);
      return;
    }

    setLoading(true);
    try {
      const wilaya = wilayas.find(w => w.code === selectedWilaya);
      
      const saleData = {
        customer_id: selectedCustomer,
        items: cart,
        subtotal,
        discount,
        total: subtotal - discount,
        paid_amount: paymentType === 'credit' ? 0 : paidAmount,
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

      const response = await axios.post(`${API}/sales`, saleData);
      toast.success(t.saleCompleted);
      
      try {
        const invoiceResponse = await axios.get(`${API}/sales/${response.data.id}/invoice-pdf`);
        const printWindow = window.open('', '_blank');
        printWindow.document.write(invoiceResponse.data);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
          printWindow.print();
        }, 500);
      } catch (printError) {
        console.error('Print error:', printError);
      }
      
      clearCart();
      fetchProducts();
    } catch (error) {
      console.error('Error completing sale:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
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

  return (
    <Layout>
      <div className="h-[calc(100vh-6rem)] flex flex-col bg-slate-900 text-white rounded-lg overflow-hidden" data-testid="pos-page">
        
        {/* No Session Warning */}
        {!checkingSession && !hasOpenSession && (
          <div className="bg-amber-600 text-white px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">
                {language === 'ar' ? 'لا توجد حصة مفتوحة - يجب فتح حصة جديدة قبل البيع' : 'Aucune session ouverte - Ouvrez une session pour vendre'}
              </span>
            </div>
            <Link to="/daily-sessions">
              <Button size="sm" variant="secondary" className="gap-2">
                <Clock className="h-4 w-4" />
                {language === 'ar' ? 'فتح حصة' : 'Ouvrir session'}
              </Button>
            </Link>
          </div>
        )}

        {/* Top Header Bar */}
        <div className="bg-slate-800 border-b border-slate-700 px-4 py-2">
          <div className="flex items-center justify-between gap-4">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search className={`absolute top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 ${isRTL ? 'right-3' : 'left-3'}`} />
              <Input
                ref={searchInputRef}
                type="text"
                placeholder={language === 'ar' ? 'البحث عن منتج بالاسم أو الباركود...' : 'Rechercher un article...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`h-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 ${isRTL ? 'pr-10' : 'pl-10'}`}
                data-testid="pos-search-input"
              />
            </div>

            {/* Quick Filters */}
            <div className="flex items-center gap-2">
              <Select value={selectedFamily} onValueChange={setSelectedFamily}>
                <SelectTrigger className="w-44 h-10 bg-slate-700 border-slate-600 text-white">
                  <FolderTree className="h-4 w-4 me-2 text-slate-400" />
                  <SelectValue placeholder={t.allFamilies} />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="all" className="text-white hover:bg-slate-700">{t.allFamilies}</SelectItem>
                  {families.map(f => (
                    <SelectItem key={f.id} value={f.id} className="text-white hover:bg-slate-700">
                      {language === 'ar' ? f.name_ar : f.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={priceType} onValueChange={setPriceType}>
                <SelectTrigger className="w-36 h-10 bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="retail" className="text-white hover:bg-slate-700">{t.retailPrice}</SelectItem>
                  <SelectItem value="wholesale" className="text-white hover:bg-slate-700">{t.wholesalePrice}</SelectItem>
                </SelectContent>
              </Select>

              {/* Customer Selection */}
              <Select value={selectedCustomer || 'walk-in'} onValueChange={(v) => setSelectedCustomer(v === 'walk-in' ? null : v)}>
                <SelectTrigger className="w-48 h-10 bg-slate-700 border-slate-600 text-white" data-testid="customer-select">
                  <User className="h-4 w-4 me-2 text-slate-400" />
                  <SelectValue placeholder={t.selectCustomer} />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="walk-in" className="text-white hover:bg-slate-700">{t.walkInCustomer}</SelectItem>
                  {customers.map(c => (
                    <SelectItem key={c.id} value={c.id} className="text-white hover:bg-slate-700">{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Customer Debt Badge */}
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
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          
          {/* Cart/Order Table - Left Side */}
          <div className="w-[55%] flex flex-col border-e border-slate-700 bg-slate-850">
            {/* Cart Header */}
            <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShoppingCart className="h-5 w-5 text-blue-400" />
                <span className="font-semibold text-lg">
                  {language === 'ar' ? 'سلة المشتريات' : 'Panier'}
                </span>
                <Badge className="bg-blue-600 text-white">{cart.length}</Badge>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearCart}
                  className="text-slate-400 hover:text-white hover:bg-slate-700"
                >
                  <RotateCcw className="h-4 w-4 me-1" />
                  {language === 'ar' ? 'مسح' : 'Effacer'}
                </Button>
              </div>
            </div>

            {/* Cart Table */}
            <div className="flex-1 overflow-auto">
              <Table>
                <TableHeader className="bg-slate-800 sticky top-0">
                  <TableRow className="border-slate-700 hover:bg-slate-800">
                    <TableHead className="text-slate-300 w-[80px]">{language === 'ar' ? 'الكود' : 'Code'}</TableHead>
                    <TableHead className="text-slate-300">{language === 'ar' ? 'المنتج' : 'Article'}</TableHead>
                    <TableHead className="text-slate-300 w-[100px] text-center">{language === 'ar' ? 'الكمية' : 'Qté'}</TableHead>
                    <TableHead className="text-slate-300 w-[100px] text-center">{language === 'ar' ? 'السعر' : 'Prix'}</TableHead>
                    <TableHead className="text-slate-300 w-[80px] text-center">{language === 'ar' ? 'خصم %' : 'R. %'}</TableHead>
                    <TableHead className="text-slate-300 w-[120px] text-center">{language === 'ar' ? 'المجموع' : 'Montant'}</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cart.length === 0 ? (
                    <TableRow className="border-slate-700">
                      <TableCell colSpan={7} className="text-center py-12 text-slate-500">
                        <ShoppingCart className="h-12 w-12 mx-auto mb-3 opacity-30" />
                        <p>{language === 'ar' ? 'السلة فارغة - قم باختيار منتجات' : 'Panier vide - Sélectionnez des articles'}</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    cart.map((item, index) => (
                      <TableRow key={item.product_id} className="border-slate-700 hover:bg-slate-800/50">
                        <TableCell className="font-mono text-xs text-slate-400">
                          {item.barcode?.slice(-6) || '---'}
                        </TableCell>
                        <TableCell className="font-medium">{item.product_name}</TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <button
                              onClick={() => updateCartItemQuantity(item.product_id, item.quantity - 1)}
                              className="p-1 rounded bg-slate-700 hover:bg-slate-600 text-white"
                            >
                              <Minus className="h-3 w-3" />
                            </button>
                            <Input
                              type="number"
                              min="1"
                              value={item.quantity}
                              onChange={(e) => updateCartItemQuantity(item.product_id, parseInt(e.target.value) || 1)}
                              className="w-14 h-8 text-center bg-slate-700 border-slate-600 text-white p-1"
                            />
                            <button
                              onClick={() => updateCartItemQuantity(item.product_id, item.quantity + 1)}
                              className="p-1 rounded bg-slate-700 hover:bg-slate-600 text-white"
                            >
                              <Plus className="h-3 w-3" />
                            </button>
                          </div>
                        </TableCell>
                        <TableCell className="text-center text-slate-300">
                          {formatCurrency(item.unit_price)}
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            max="100"
                            placeholder="0"
                            value={item.discount_percent || ''}
                            onChange={(e) => updateCartItemDiscount(item.product_id, e.target.value)}
                            className="w-16 h-8 text-center bg-slate-700 border-slate-600 text-white p-1"
                          />
                        </TableCell>
                        <TableCell className="text-center font-bold text-green-400">
                          {formatCurrency(item.total)}
                        </TableCell>
                        <TableCell>
                          <button
                            onClick={() => removeFromCart(item.product_id)}
                            className="p-1 rounded text-red-400 hover:bg-red-500/20"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </div>

          {/* Products List - Right Side */}
          <div className="flex-1 flex flex-col bg-slate-900">
            {/* Products Header */}
            <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex items-center gap-3">
              <Package className="h-5 w-5 text-green-400" />
              <span className="font-semibold text-lg">
                {language === 'ar' ? 'قائمة المنتجات' : 'Liste des articles'}
              </span>
              <Badge variant="outline" className="text-slate-300 border-slate-600">{filteredProducts.length}</Badge>
            </div>

            {/* Products Table */}
            <div className="flex-1 overflow-auto">
              <Table>
                <TableHeader className="bg-slate-800 sticky top-0">
                  <TableRow className="border-slate-700 hover:bg-slate-800">
                    <TableHead className="text-slate-300 w-[80px]">{language === 'ar' ? 'الكود' : 'Code'}</TableHead>
                    <TableHead className="text-slate-300">{language === 'ar' ? 'اسم المنتج' : 'Nom d\'article'}</TableHead>
                    <TableHead className="text-slate-300 w-[80px] text-center">{language === 'ar' ? 'المخزون' : 'Stock'}</TableHead>
                    <TableHead className="text-slate-300 w-[100px] text-center">{language === 'ar' ? 'السعر' : 'Prix'}</TableHead>
                    <TableHead className="w-[60px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProducts.map(product => (
                    <TableRow 
                      key={product.id} 
                      className={`border-slate-700 cursor-pointer transition-colors ${
                        product.quantity <= 0 
                          ? 'opacity-50 bg-red-900/10' 
                          : 'hover:bg-blue-900/20'
                      }`}
                      onClick={() => product.quantity > 0 && addToCart(product)}
                      data-testid={`pos-product-${product.id}`}
                    >
                      <TableCell className="font-mono text-xs text-slate-400">
                        {product.barcode?.slice(-6) || product.id.slice(-6)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{language === 'ar' ? product.name_ar : product.name_en}</span>
                          {product.quantity <= 5 && product.quantity > 0 && (
                            <Badge variant="outline" className="text-amber-400 border-amber-600 text-xs">
                              {language === 'ar' ? 'منخفض' : 'Bas'}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge className={`${
                          product.quantity <= 0 
                            ? 'bg-red-600' 
                            : product.quantity <= 5 
                              ? 'bg-amber-600' 
                              : 'bg-green-600'
                        } text-white`}>
                          {product.quantity}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center font-bold text-blue-400">
                        {formatCurrency(priceType === 'wholesale' ? product.wholesale_price : product.retail_price)}
                      </TableCell>
                      <TableCell>
                        {product.quantity > 0 && (
                          <button className="p-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white">
                            <Plus className="h-4 w-4" />
                          </button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>

        {/* Bottom Footer Bar - Totals & Actions */}
        <div className="bg-slate-800 border-t border-slate-700">
          {/* Payment Type & Delivery Row */}
          <div className="px-4 py-2 border-b border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Payment Type */}
              <div className="flex items-center gap-2">
                <Label className="text-slate-400 text-sm">{language === 'ar' ? 'نوع الدفع:' : 'Type:'}</Label>
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant={paymentType === 'cash' ? 'default' : 'outline'}
                    onClick={() => setPaymentType('cash')}
                    className={paymentType === 'cash' ? 'bg-green-600 hover:bg-green-700' : 'border-slate-600 text-slate-300'}
                  >
                    {language === 'ar' ? 'نقدي' : 'Comptant'}
                  </Button>
                  <Button
                    size="sm"
                    variant={paymentType === 'credit' ? 'default' : 'outline'}
                    onClick={() => setPaymentType('credit')}
                    className={paymentType === 'credit' ? 'bg-amber-600 hover:bg-amber-700' : 'border-slate-600 text-slate-300'}
                  >
                    {language === 'ar' ? 'دين' : 'Crédit'}
                  </Button>
                  <Button
                    size="sm"
                    variant={paymentType === 'partial' ? 'default' : 'outline'}
                    onClick={() => setPaymentType('partial')}
                    className={paymentType === 'partial' ? 'bg-blue-600 hover:bg-blue-700' : 'border-slate-600 text-slate-300'}
                  >
                    {language === 'ar' ? 'جزئي' : 'Partiel'}
                  </Button>
                </div>
              </div>

              {/* Payment Method */}
              {paymentType !== 'credit' && (
                <div className="flex items-center gap-2">
                  <Label className="text-slate-400 text-sm">{language === 'ar' ? 'الوسيلة:' : 'Mode:'}</Label>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                      onClick={() => setPaymentMethod('cash')}
                      className={paymentMethod === 'cash' ? 'bg-slate-600' : 'border-slate-600 text-slate-300'}
                    >
                      <Banknote className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant={paymentMethod === 'bank' ? 'default' : 'outline'}
                      onClick={() => setPaymentMethod('bank')}
                      className={paymentMethod === 'bank' ? 'bg-slate-600' : 'border-slate-600 text-slate-300'}
                    >
                      <CreditCard className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant={paymentMethod === 'wallet' ? 'default' : 'outline'}
                      onClick={() => setPaymentMethod('wallet')}
                      className={paymentMethod === 'wallet' ? 'bg-slate-600' : 'border-slate-600 text-slate-300'}
                    >
                      <Wallet className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}

              {/* Delivery Toggle */}
              <div className="flex items-center gap-2">
                <Truck className="h-4 w-4 text-slate-400" />
                <Label className="text-slate-400 text-sm">{language === 'ar' ? 'توصيل' : 'Livraison'}</Label>
                <Switch
                  checked={deliveryEnabled}
                  onCheckedChange={setDeliveryEnabled}
                  className="data-[state=checked]:bg-blue-600"
                />
                {deliveryEnabled && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowDeliveryDialog(true)}
                    className="border-slate-600 text-slate-300"
                  >
                    {selectedWilaya || (language === 'ar' ? 'إعداد' : 'Config')}
                  </Button>
                )}
              </div>
            </div>

            {/* Paid Amount Input */}
            {paymentType !== 'credit' && (
              <div className="flex items-center gap-2">
                <Label className="text-slate-400 text-sm">{language === 'ar' ? 'المدفوع:' : 'Payé:'}</Label>
                <Input
                  type="number"
                  min="0"
                  value={paidAmount || ''}
                  onChange={(e) => setPaidAmount(parseFloat(e.target.value) || 0)}
                  className="w-32 h-9 bg-slate-700 border-slate-600 text-white"
                  data-testid="paid-amount-input"
                />
              </div>
            )}
          </div>

          {/* Totals Row */}
          <div className="px-4 py-3 flex items-center justify-between">
            {/* Left - Totals Display */}
            <div className="flex items-center gap-6">
              {/* Subtotal */}
              <div className="text-center">
                <p className="text-xs text-slate-400 mb-1">{language === 'ar' ? 'المجموع الفرعي' : 'Sous total'}</p>
                <p className="text-xl font-bold text-white">{formatCurrency(subtotal)}</p>
              </div>

              {/* Discount */}
              <div className="text-center">
                <p className="text-xs text-slate-400 mb-1">{language === 'ar' ? 'الخصم' : 'Remise'}</p>
                <div className="flex items-center gap-1">
                  <Input
                    type="number"
                    min="0"
                    value={discount || ''}
                    onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                    className="w-24 h-8 bg-slate-700 border-slate-600 text-white text-center"
                    data-testid="total-discount-input"
                  />
                </div>
              </div>

              {/* Delivery Fee */}
              {deliveryEnabled && deliveryFee > 0 && (
                <div className="text-center">
                  <p className="text-xs text-slate-400 mb-1">{language === 'ar' ? 'التوصيل' : 'Livraison'}</p>
                  <p className="text-xl font-bold text-blue-400">+{formatCurrency(deliveryFee)}</p>
                </div>
              )}

              {/* Debt Amount */}
              {(paymentType === 'credit' || (paymentType === 'partial' && remaining > 0)) && (
                <div className="text-center">
                  <p className="text-xs text-slate-400 mb-1">{language === 'ar' ? 'الدين' : 'Crédit'}</p>
                  <p className="text-xl font-bold text-amber-400">
                    {formatCurrency(paymentType === 'credit' ? total : remaining)}
                  </p>
                </div>
              )}

              {/* Total */}
              <div className="text-center px-4 py-2 bg-blue-600 rounded-lg">
                <p className="text-xs text-blue-200 mb-1">{language === 'ar' ? 'الإجمالي' : 'Total'}</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(total)} <span className="text-sm">{t.currency}</span></p>
              </div>
            </div>

            {/* Right - Action Buttons */}
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={clearCart}
                className="h-12 px-6 border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                <RotateCcw className="h-5 w-5 me-2" />
                {language === 'ar' ? 'إلغاء' : 'Annuler'}
              </Button>

              <Button
                onClick={completeSale}
                disabled={loading || cart.length === 0 || !hasOpenSession}
                className="h-12 px-8 bg-green-600 hover:bg-green-700 text-white text-lg gap-2"
                data-testid="complete-sale-btn"
              >
                <Check className="h-5 w-5" />
                {loading ? (language === 'ar' ? 'جاري...' : 'Chargement...') : (language === 'ar' ? 'تأكيد البيع' : 'Valider')}
                <span className="text-xs opacity-70">(Ctrl+Enter)</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Debt Payment Dialog */}
      <Dialog open={showDebtDialog} onOpenChange={setShowDebtDialog}>
        <DialogContent className="max-w-sm bg-slate-800 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle className="text-white">{t.payDebt}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-slate-300">{t.totalDebt}</Label>
              <p className="text-xl font-bold text-amber-400">{formatCurrency(customerDebt)} {t.currency}</p>
            </div>
            <div>
              <Label className="text-slate-300">{t.amount}</Label>
              <Input
                type="number"
                min="0"
                max={customerDebt}
                value={debtPaymentAmount}
                onChange={(e) => setDebtPaymentAmount(parseFloat(e.target.value) || 0)}
                className="bg-slate-700 border-slate-600 text-white"
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
              <Button variant="outline" onClick={() => setShowDebtDialog(false)} className="flex-1 border-slate-600">
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
        <DialogContent className="max-w-md bg-slate-800 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Truck className="h-5 w-5" />
              {language === 'ar' ? 'إعدادات التوصيل' : 'Paramètres de livraison'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-slate-300">{t.selectWilaya}</Label>
              <Select value={selectedWilaya} onValueChange={setSelectedWilaya}>
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="wilaya-select">
                  <SelectValue placeholder={t.selectWilaya} />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700 max-h-60">
                  {wilayas.map(w => (
                    <SelectItem key={w.code} value={w.code} className="text-white hover:bg-slate-700">
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
                className={`flex-1 ${deliveryType === 'desk' ? 'bg-blue-600' : 'border-slate-600 text-slate-300'}`}
              >
                {t.officeDelivery}
              </Button>
              <Button
                variant={deliveryType === 'home' ? 'default' : 'outline'}
                onClick={() => setDeliveryType('home')}
                className={`flex-1 ${deliveryType === 'home' ? 'bg-blue-600' : 'border-slate-600 text-slate-300'}`}
              >
                {t.homeDelivery}
              </Button>
            </div>

            <div>
              <Label className="text-slate-300">{t.deliveryCity}</Label>
              <Input
                value={deliveryCity}
                onChange={(e) => setDeliveryCity(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            <div>
              <Label className="text-slate-300">{t.deliveryAddress}</Label>
              <Input
                value={deliveryAddress}
                onChange={(e) => setDeliveryAddress(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            {deliveryFee > 0 && (
              <div className="p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                <div className="flex justify-between text-lg font-bold">
                  <span className="text-slate-300">{t.deliveryFee}</span>
                  <span className="text-blue-400">{formatCurrency(deliveryFee)} {t.currency}</span>
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowDeliveryDialog(false)} className="flex-1 border-slate-600">
                {t.cancel}
              </Button>
              <Button onClick={() => setShowDeliveryDialog(false)} className="flex-1 bg-blue-600 hover:bg-blue-700">
                {t.confirm}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
