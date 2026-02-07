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
  RotateCcw
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function POSPage() {
  const { t, language, isRTL } = useLanguage();
  const searchInputRef = useRef(null);
  const searchDropdownRef = useRef(null);
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [families, setFamilies] = useState([]);
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
  const [newCustomerData, setNewCustomerData] = useState({ name: '', phone: '', email: '', address: '' });
  const [savingCustomer, setSavingCustomer] = useState(false);

  useEffect(() => {
    checkOpenSession();
    fetchProducts();
    fetchCustomers();
    fetchFamilies();
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

  // Add new customer
  const handleAddCustomer = async () => {
    if (!newCustomerData.name) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم الزبون' : 'Veuillez entrer le nom du client');
      return;
    }

    setSavingCustomer(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/customers`, newCustomerData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تمت إضافة الزبون بنجاح' : 'Client ajouté avec succès');
      setShowNewCustomerDialog(false);
      setNewCustomerData({ name: '', phone: '', email: '', address: '' });
      fetchCustomers();
      // Auto-select the new customer
      if (response.data?.id) {
        setSelectedCustomer(response.data.id);
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
        setTimeout(() => printWindow.print(), 500);
      } catch (printError) {
        console.error('Print error:', printError);
      }
      
      clearCart();
      fetchProducts();
    } catch (error) {
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
              <Select value={selectedCustomer || 'walk-in'} onValueChange={(v) => setSelectedCustomer(v === 'walk-in' ? null : v)}>
                <SelectTrigger className="w-48 h-11" data-testid="customer-select">
                  <User className="h-4 w-4 me-2 text-muted-foreground" />
                  <SelectValue placeholder={t.selectCustomer} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="walk-in">{t.walkInCustomer}</SelectItem>
                  {customers.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

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

        {/* Main Content - Cart */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <ShoppingCart className="h-5 w-5 text-primary" />
                {language === 'ar' ? 'سلة المشتريات' : 'Panier'}
                <Badge className="ms-2">{cart.length}</Badge>
              </CardTitle>
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
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead className="w-[100px]">{language === 'ar' ? 'الكود' : 'Code'}</TableHead>
                    <TableHead>{language === 'ar' ? 'المنتج' : 'Article'}</TableHead>
                    <TableHead className="w-[140px] text-center">{language === 'ar' ? 'الكمية' : 'Qté'}</TableHead>
                    <TableHead className="w-[100px] text-center">{language === 'ar' ? 'السعر' : 'Prix'}</TableHead>
                    <TableHead className="w-[100px] text-center">{language === 'ar' ? 'خصم %' : 'R. %'}</TableHead>
                    <TableHead className="w-[120px] text-center">{language === 'ar' ? 'المجموع' : 'Total'}</TableHead>
                    <TableHead className="w-[60px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cart.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                        <ShoppingCart className="h-12 w-12 mx-auto mb-3 opacity-30" />
                        <p>{language === 'ar' ? 'السلة فارغة - ابحث عن منتج لإضافته' : 'Panier vide - Recherchez un article'}</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    cart.map((item) => (
                      <TableRow key={item.product_id}>
                        <TableCell className="font-mono text-sm text-muted-foreground">
                          {item.barcode?.slice(-6) || '---'}
                        </TableCell>
                        <TableCell className="font-medium">{item.product_name}</TableCell>
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
                        <TableCell className="text-center">{formatCurrency(item.unit_price)}</TableCell>
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
                            onClick={() => removeFromCart(item.product_id)}
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
    </Layout>
  );
}
