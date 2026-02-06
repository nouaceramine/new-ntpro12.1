import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
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
  Barcode
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function POSPage() {
  const { t, language, isRTL } = useLanguage();
  const searchInputRef = useRef(null);
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [discount, setDiscount] = useState(0);
  const [paidAmount, setPaidAmount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [loading, setLoading] = useState(false);
  const [priceType, setPriceType] = useState('retail'); // retail, wholesale

  useEffect(() => {
    fetchProducts();
    fetchCustomers();
  }, []);

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

  const filteredProducts = products.filter(p => {
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
  const total = subtotal - discount;
  const remaining = total - paidAmount;

  const completeSale = async () => {
    if (cart.length === 0) {
      toast.error(t.emptyCart);
      return;
    }

    setLoading(true);
    try {
      const saleData = {
        customer_id: selectedCustomer,
        items: cart,
        subtotal,
        discount,
        total,
        paid_amount: paidAmount,
        payment_method: paymentMethod,
        notes: ''
      };

      const response = await axios.post(`${API}/sales`, saleData);
      toast.success(t.saleCompleted);
      
      // Open invoice in new tab
      window.open(`${API}/sales/${response.data.id}/invoice-pdf`, '_blank');
      
      // Reset
      setCart([]);
      setDiscount(0);
      setPaidAmount(0);
      setSelectedCustomer(null);
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
          {/* Search */}
          <div className="mb-4 flex gap-4">
            <div className="relative flex-1">
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
        <Card className="w-96 flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5" />
              {t.cart}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            {/* Customer Selection */}
            <div className="mb-4">
              <Select value={selectedCustomer || ''} onValueChange={setSelectedCustomer}>
                <SelectTrigger data-testid="customer-select">
                  <User className="h-4 w-4 me-2" />
                  <SelectValue placeholder={t.selectCustomer} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t.walkInCustomer}</SelectItem>
                  {customers.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
              <div className="flex justify-between font-bold text-lg">
                <span>{t.total}</span>
                <span className="text-primary">{total.toFixed(2)} {t.currency}</span>
              </div>
              
              {/* Payment */}
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
              
              {remaining > 0 && (
                <div className="flex justify-between text-sm text-amber-600">
                  <span>{t.remaining}</span>
                  <span>{remaining.toFixed(2)} {t.currency}</span>
                </div>
              )}

              {/* Payment Method */}
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
    </Layout>
  );
}
