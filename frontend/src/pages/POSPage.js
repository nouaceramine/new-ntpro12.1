import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
  Clock
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
  const [paymentType, setPaymentType] = useState('cash'); // cash, credit, partial
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

  useEffect(() => {
    checkOpenSession();
    fetchProducts();
    fetchCustomers();
    fetchFamilies();
    fetchWilayas();
  }, []);

  // Check if user has an open session
  const checkOpenSession = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/sessions/my-open`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHasOpenSession(!!response.data);
    } catch (error) {
      // No open session or error
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
    // Calculate delivery fee when wilaya or type changes
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
    // Filter by family
    if (selectedFamily !== 'all' && p.family_id !== selectedFamily) {
      return false;
    }
    
    // Filter by search
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
        quantity: 1,
        unit_price: price,
        discount: 0,
        total: price
      }]);
    }
    
    setSearchQuery('');
    searchInputRef.current?.focus();
  };

  const updateCartItemQuantity = (productId, delta) => {
    const product = products.find(p => p.id === productId);
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const newQty = item.quantity + delta;
        if (newQty <= 0) return item;
        if (newQty > product.quantity) {
          toast.error(t.outOfStock);
          return item;
        }
        return { ...item, quantity: newQty, total: newQty * item.unit_price - item.discount };
      }
      return item;
    }));
  };

  const updateCartItemDiscount = (productId, discountValue) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const disc = parseFloat(discountValue) || 0;
        return { ...item, discount: disc, total: item.quantity * item.unit_price - disc };
      }
      return item;
    }));
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
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

  const completeSale = async () => {
    // Check for open session first
    if (!hasOpenSession) {
      toast.error(language === 'ar' 
        ? 'يجب فتح حصة جديدة قبل البيع. اذهب إلى صفحة حصص البيع اليومية'
        : 'Vous devez ouvrir une session avant de vendre. Allez à la page des sessions de vente');
      return;
    }
    
    if (cart.length === 0) {
      toast.error(t.emptyCart);
      return;
    }

    // Validate credit sale requires customer
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
        total: subtotal - discount, // Without delivery for backend calculation
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
      
      // Get invoice HTML and open in print dialog
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
      
      // Reset
      setCart([]);
      setDiscount(0);
      setPaidAmount(0);
      setSelectedCustomer(null);
      setDeliveryEnabled(false);
      setSelectedWilaya('');
      setDeliveryAddress('');
      setDeliveryCity('');
      setPaymentType('cash');
      fetchProducts();
    } catch (error) {
      console.error('Error completing sale:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="h-[calc(100vh-8rem)] flex gap-6" data-testid="pos-page">
        {/* Products Section */}
        <div className="flex-1 flex flex-col">
          {/* Search & Filters */}
          <div className="mb-4 flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
              <Input
                ref={searchInputRef}
                type="text"
                placeholder={t.searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`h-12 ${isRTL ? 'pr-10' : 'pl-10'}`}
                data-testid="pos-search-input"
              />
            </div>
            
            {/* Family Filter */}
            <Select value={selectedFamily} onValueChange={setSelectedFamily}>
              <SelectTrigger className="w-48 h-12" data-testid="family-filter">
                <FolderTree className="h-4 w-4 me-2" />
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
              <SelectTrigger className="w-40 h-12" data-testid="price-type-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="retail">{t.retailPrice}</SelectItem>
                <SelectItem value="wholesale">{t.wholesalePrice}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Products Grid */}
          <div className="flex-1 overflow-auto">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {filteredProducts.map(product => (
                <button
                  key={product.id}
                  onClick={() => addToCart(product)}
                  disabled={product.quantity <= 0}
                  className={`p-3 rounded-xl border text-start transition-all hover:shadow-md ${
                    product.quantity <= 0 ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary'
                  }`}
                  data-testid={`pos-product-${product.id}`}
                >
                  <div className="aspect-square rounded-lg bg-muted mb-2 overflow-hidden">
                    <img
                      src={product.image_url || 'https://images.unsplash.com/photo-1634403665443-81dc4d75843a?crop=entropy&cs=srgb&fm=jpg&q=85'}
                      alt={language === 'ar' ? product.name_ar : product.name_en}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <h3 className="font-medium text-sm line-clamp-1">
                    {language === 'ar' ? product.name_ar : product.name_en}
                  </h3>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-primary font-bold">
                      {(priceType === 'wholesale' ? product.wholesale_price : product.retail_price).toFixed(2)} {t.currency}
                    </span>
                    <Badge variant={product.quantity > 0 ? 'secondary' : 'destructive'} className="text-xs">
                      {product.quantity}
                    </Badge>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Cart Section */}
        <Card className="w-[420px] flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5" />
              {t.cart}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col overflow-hidden">
            {/* Customer Selection with Debt Info */}
            <div className="mb-4">
              <Select value={selectedCustomer || 'walk-in'} onValueChange={(v) => setSelectedCustomer(v === 'walk-in' ? null : v)}>
                <SelectTrigger data-testid="customer-select">
                  <User className="h-4 w-4 me-2" />
                  <SelectValue placeholder={t.selectCustomer} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="walk-in">{t.walkInCustomer}</SelectItem>
                  {customers.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {/* Customer Debt Warning */}
              {selectedCustomer && customerDebt > 0 && (
                <div className="mt-2 p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-amber-600">
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">{t.customerDebt}: {customerDebt.toLocaleString()} {t.currency}</span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setDebtPaymentAmount(customerDebt);
                        setShowDebtDialog(true);
                      }}
                      className="text-xs"
                    >
                      {t.payDebt}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Payment Type Selection */}
            <div className="mb-4">
              <Label className="text-sm mb-2 block">{t.paymentType}</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={paymentType === 'cash' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPaymentType('cash')}
                  className="flex-1"
                >
                  {t.cashPayment}
                </Button>
                <Button
                  type="button"
                  variant={paymentType === 'credit' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPaymentType('credit')}
                  className="flex-1"
                >
                  {t.creditPayment}
                </Button>
                <Button
                  type="button"
                  variant={paymentType === 'partial' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPaymentType('partial')}
                  className="flex-1"
                >
                  {t.partialPayment}
                </Button>
              </div>
            </div>

            {/* Cart Items */}
            <div className="flex-1 overflow-auto space-y-2 mb-4">
              {cart.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <ShoppingCart className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>{t.emptyCart}</p>
                </div>
              ) : (
                cart.map(item => (
                  <div key={item.product_id} className="p-3 rounded-lg border bg-muted/30">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{item.product_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {item.unit_price.toFixed(2)} {t.currency}
                        </p>
                      </div>
                      <button
                        onClick={() => removeFromCart(item.product_id)}
                        className="text-destructive hover:bg-destructive/10 p-1 rounded"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => updateCartItemQuantity(item.product_id, -1)}
                          className="p-1 rounded bg-muted hover:bg-muted/80"
                        >
                          <Minus className="h-4 w-4" />
                        </button>
                        <span className="w-8 text-center font-medium">{item.quantity}</span>
                        <button
                          onClick={() => updateCartItemQuantity(item.product_id, 1)}
                          className="p-1 rounded bg-muted hover:bg-muted/80"
                        >
                          <Plus className="h-4 w-4" />
                        </button>
                      </div>
                      <Input
                        type="number"
                        min="0"
                        placeholder={t.discount}
                        value={item.discount || ''}
                        onChange={(e) => updateCartItemDiscount(item.product_id, e.target.value)}
                        className="w-20 h-8 text-sm"
                      />
                      <span className="font-bold text-sm">
                        {item.total.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Delivery Section */}
            <div className="mb-4 p-3 rounded-lg border bg-muted/30">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Truck className="h-4 w-4" />
                  <Label>{t.deliveryService}</Label>
                </div>
                <Switch
                  checked={deliveryEnabled}
                  onCheckedChange={setDeliveryEnabled}
                  data-testid="delivery-toggle"
                />
              </div>
              
              {deliveryEnabled && (
                <div className="space-y-3">
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
                  
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant={deliveryType === 'desk' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setDeliveryType('desk')}
                      className="flex-1"
                    >
                      {t.officeDelivery}
                    </Button>
                    <Button
                      type="button"
                      variant={deliveryType === 'home' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setDeliveryType('home')}
                      className="flex-1"
                    >
                      {t.homeDelivery}
                    </Button>
                  </div>
                  
                  <Input
                    placeholder={t.deliveryCity}
                    value={deliveryCity}
                    onChange={(e) => setDeliveryCity(e.target.value)}
                    className="h-9"
                  />
                  
                  <Input
                    placeholder={t.deliveryAddress}
                    value={deliveryAddress}
                    onChange={(e) => setDeliveryAddress(e.target.value)}
                    className="h-9"
                  />
                  
                  {deliveryFee > 0 && (
                    <div className="flex justify-between text-sm font-medium text-primary">
                      <span>{t.deliveryFee}</span>
                      <span>{deliveryFee.toLocaleString()} {t.currency}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Totals */}
            <div className="space-y-3 border-t pt-4">
              <div className="flex justify-between text-sm">
                <span>{t.subtotal}</span>
                <span>{subtotal.toFixed(2)} {t.currency}</span>
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-sm w-20">{t.discount}</Label>
                <Input
                  type="number"
                  min="0"
                  value={discount || ''}
                  onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                  className="h-9"
                  data-testid="total-discount-input"
                />
              </div>
              {deliveryEnabled && deliveryFee > 0 && (
                <div className="flex justify-between text-sm text-primary">
                  <span>{t.deliveryFee}</span>
                  <span>+{deliveryFee.toLocaleString()} {t.currency}</span>
                </div>
              )}
              <div className="flex justify-between font-bold text-lg">
                <span>{t.total}</span>
                <span className="text-primary">{total.toFixed(2)} {t.currency}</span>
              </div>
              
              {/* Payment - only show for cash or partial */}
              {paymentType !== 'credit' && (
                <div className="flex items-center gap-2">
                  <Label className="text-sm w-20">{t.paidAmount}</Label>
                  <Input
                    type="number"
                    min="0"
                    value={paidAmount || ''}
                    onChange={(e) => setPaidAmount(parseFloat(e.target.value) || 0)}
                    className="h-9"
                    data-testid="paid-amount-input"
                  />
                </div>
              )}
              
              {paymentType === 'credit' && (
                <div className="flex justify-between text-sm text-amber-600 font-medium">
                  <span>{t.debtAmount}</span>
                  <span>{total.toFixed(2)} {t.currency}</span>
                </div>
              )}
              
              {paymentType === 'partial' && remaining > 0 && (
                <div className="flex justify-between text-sm text-amber-600">
                  <span>{t.debtAmount}</span>
                  <span>{remaining.toFixed(2)} {t.currency}</span>
                </div>
              )}

              {/* Payment Method */}
              {paymentType !== 'credit' && (
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setPaymentMethod('cash')}
                    className="flex-1 gap-1"
                  >
                    <Banknote className="h-4 w-4" />
                    {t.cash}
                  </Button>
                  <Button
                    type="button"
                    variant={paymentMethod === 'bank' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setPaymentMethod('bank')}
                    className="flex-1 gap-1"
                  >
                    <CreditCard className="h-4 w-4" />
                    {t.bank}
                  </Button>
                  <Button
                    type="button"
                    variant={paymentMethod === 'wallet' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setPaymentMethod('wallet')}
                    className="flex-1 gap-1"
                  >
                    <Wallet className="h-4 w-4" />
                  </Button>
                </div>
              )}

              {/* Complete Sale Button */}
              <Button
                onClick={completeSale}
                disabled={loading || cart.length === 0}
                className="w-full h-12 text-lg gap-2"
                data-testid="complete-sale-btn"
              >
                <Printer className="h-5 w-5" />
                {loading ? t.loading : t.completeSale}
              </Button>
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
              <p className="text-xl font-bold text-amber-600">{customerDebt.toLocaleString()} {t.currency}</p>
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
                type="button"
                variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setPaymentMethod('cash')}
                className="flex-1"
              >
                <Banknote className="h-4 w-4 me-1" />
                {t.cash}
              </Button>
              <Button
                type="button"
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
              <Button onClick={handlePayDebt} className="flex-1" disabled={debtPaymentAmount <= 0}>
                {t.confirm}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
