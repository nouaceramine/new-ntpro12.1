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
import { 
  ShoppingBag, 
  Search, 
  Plus, 
  Minus, 
  Trash2, 
  Package,
  Truck,
  CreditCard,
  Banknote,
  Wallet,
  TrendingUp,
  Calculator,
  FileText,
  Calendar
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PurchasesPage() {
  const { t, language, isRTL } = useLanguage();
  const searchInputRef = useRef(null);
  
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [paidAmount, setPaidAmount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [showNewPurchaseDialog, setShowNewPurchaseDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('history'); // history, new

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [productsRes, suppliersRes, purchasesRes] = await Promise.all([
        axios.get(`${API}/products`),
        axios.get(`${API}/suppliers`),
        axios.get(`${API}/purchases`)
      ]);
      setProducts(productsRes.data);
      setSuppliers(suppliersRes.data);
      setPurchases(purchasesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const filteredProducts = products.filter(p => {
    const query = searchQuery.toLowerCase();
    return (
      p.name_ar?.toLowerCase().includes(query) ||
      p.name_en?.toLowerCase().includes(query) ||
      p.barcode?.toLowerCase().includes(query)
    );
  });

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.product_id === product.id);
    if (existingItem) {
      setCart(cart.map(item =>
        item.product_id === product.id
          ? { ...item, quantity: item.quantity + 1, total: (item.quantity + 1) * item.unit_price }
          : item
      ));
    } else {
      setCart([...cart, {
        product_id: product.id,
        product_name: language === 'ar' ? product.name_ar : product.name_en,
        quantity: 1,
        unit_price: product.purchase_price || product.price || 0,
        total: product.purchase_price || product.price || 0
      }]);
    }
  };

  const updateQuantity = (productId, delta) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const newQty = Math.max(1, item.quantity + delta);
        return { ...item, quantity: newQty, total: newQty * item.unit_price };
      }
      return item;
    }));
  };

  const updatePrice = (productId, newPrice) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        return { ...item, unit_price: newPrice, total: item.quantity * newPrice };
      }
      return item;
    }));
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
  };

  const subtotal = cart.reduce((sum, item) => sum + item.total, 0);

  const completePurchase = async () => {
    if (cart.length === 0) {
      toast.error(language === 'ar' ? 'السلة فارغة' : 'Le panier est vide');
      return;
    }

    if (!selectedSupplier) {
      toast.error(language === 'ar' ? 'يرجى اختيار المورد' : 'Veuillez sélectionner un fournisseur');
      return;
    }

    setLoading(true);
    try {
      const purchaseData = {
        supplier_id: selectedSupplier,
        items: cart,
        total: subtotal,
        paid_amount: paidAmount,
        payment_method: paymentMethod,
        notes
      };

      await axios.post(`${API}/purchases`, purchaseData);
      toast.success(t.purchaseCompleted);
      
      // Reset
      setCart([]);
      setPaidAmount(0);
      setSelectedSupplier(null);
      setNotes('');
      setShowNewPurchaseDialog(false);
      fetchData();
    } catch (error) {
      console.error('Error completing purchase:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat(language === 'ar' ? 'ar-SA' : 'fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'paid':
        return <Badge className="bg-emerald-100 text-emerald-700">{t.paid}</Badge>;
      case 'partial':
        return <Badge className="bg-amber-100 text-amber-700">{t.partial}</Badge>;
      case 'unpaid':
        return <Badge variant="destructive">{t.unpaid}</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  // Calculate statistics
  const totalPurchases = purchases.reduce((sum, p) => sum + p.total, 0);
  const totalPaid = purchases.reduce((sum, p) => sum + p.paid_amount, 0);
  const totalRemaining = purchases.reduce((sum, p) => sum + p.remaining, 0);
  const purchasesThisMonth = purchases.filter(p => {
    const purchaseDate = new Date(p.created_at);
    const now = new Date();
    return purchaseDate.getMonth() === now.getMonth() && purchaseDate.getFullYear() === now.getFullYear();
  }).length;

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="purchases-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.purchases}</h1>
            <p className="text-muted-foreground mt-1">
              {language === 'ar' ? 'إدارة المشتريات وتتبع المخزون' : 'Gestion des achats et suivi des stocks'}
            </p>
          </div>
          <Button onClick={() => setShowNewPurchaseDialog(true)} className="gap-2" data-testid="new-purchase-btn">
            <Plus className="h-5 w-5" />
            {t.newPurchase}
          </Button>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'إجمالي المشتريات' : 'Total achats'}</p>
                  <p className="text-2xl font-bold mt-1">{totalPurchases.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
                <div className="p-3 rounded-xl bg-blue-100 text-blue-600">
                  <ShoppingBag className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'المدفوع' : 'Payé'}</p>
                  <p className="text-2xl font-bold mt-1 text-emerald-600">{totalPaid.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
                <div className="p-3 rounded-xl bg-emerald-100 text-emerald-600">
                  <TrendingUp className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'المتبقي' : 'Restant'}</p>
                  <p className="text-2xl font-bold mt-1 text-amber-600">{totalRemaining.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
                <div className="p-3 rounded-xl bg-amber-100 text-amber-600">
                  <Calculator className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'هذا الشهر' : 'Ce mois'}</p>
                  <p className="text-2xl font-bold mt-1">{purchasesThisMonth}</p>
                  <p className="text-xs text-muted-foreground">{language === 'ar' ? 'فاتورة' : 'factures'}</p>
                </div>
                <div className="p-3 rounded-xl bg-purple-100 text-purple-600">
                  <Calendar className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Purchases History Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {language === 'ar' ? 'سجل المشتريات' : 'Historique des achats'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {purchases.length === 0 ? (
              <div className="text-center py-12">
                <ShoppingBag className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">{language === 'ar' ? 'لا توجد مشتريات' : 'Aucun achat'}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{language === 'ar' ? 'رقم الفاتورة' : 'N° Facture'}</TableHead>
                      <TableHead>{language === 'ar' ? 'المورد' : 'Fournisseur'}</TableHead>
                      <TableHead>{language === 'ar' ? 'التاريخ' : 'Date'}</TableHead>
                      <TableHead>{language === 'ar' ? 'الإجمالي' : 'Total'}</TableHead>
                      <TableHead>{language === 'ar' ? 'المدفوع' : 'Payé'}</TableHead>
                      <TableHead>{language === 'ar' ? 'المتبقي' : 'Restant'}</TableHead>
                      <TableHead>{language === 'ar' ? 'الحالة' : 'Statut'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {purchases.map(purchase => (
                      <TableRow key={purchase.id}>
                        <TableCell className="font-medium">{purchase.invoice_number}</TableCell>
                        <TableCell>{purchase.supplier_name}</TableCell>
                        <TableCell>{formatDate(purchase.created_at)}</TableCell>
                        <TableCell className="font-semibold">{purchase.total.toFixed(2)} {t.currency}</TableCell>
                        <TableCell className="text-emerald-600">{purchase.paid_amount.toFixed(2)} {t.currency}</TableCell>
                        <TableCell className="text-amber-600">{purchase.remaining.toFixed(2)} {t.currency}</TableCell>
                        <TableCell>{getStatusBadge(purchase.status)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* New Purchase Dialog */}
        <Dialog open={showNewPurchaseDialog} onOpenChange={setShowNewPurchaseDialog}>
          <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <ShoppingBag className="h-5 w-5" />
                {t.newPurchase}
              </DialogTitle>
            </DialogHeader>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
              {/* Products Selection */}
              <div className="space-y-4">
                <div className="relative">
                  <Search className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
                  <Input
                    ref={searchInputRef}
                    type="text"
                    placeholder={t.searchPlaceholder}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className={`h-11 ${isRTL ? 'pr-10' : 'pl-10'}`}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3 max-h-[400px] overflow-y-auto">
                  {filteredProducts.slice(0, 20).map(product => (
                    <div
                      key={product.id}
                      onClick={() => addToCart(product)}
                      className="p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                    >
                      <p className="font-medium text-sm line-clamp-1">
                        {language === 'ar' ? product.name_ar : product.name_en}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {(product.purchase_price || product.price || 0).toFixed(2)} {t.currency}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {t.quantity}: {product.quantity}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cart & Payment */}
              <div className="space-y-4">
                {/* Supplier Selection */}
                <div>
                  <Label>{t.selectSupplier}</Label>
                  <Select value={selectedSupplier || ''} onValueChange={setSelectedSupplier}>
                    <SelectTrigger>
                      <Truck className="h-4 w-4 me-2" />
                      <SelectValue placeholder={t.selectSupplier} />
                    </SelectTrigger>
                    <SelectContent>
                      {suppliers.map(s => (
                        <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Cart Items */}
                <div className="border rounded-lg p-3 max-h-[200px] overflow-y-auto">
                  {cart.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">{t.emptyCart}</p>
                  ) : (
                    <div className="space-y-2">
                      {cart.map(item => (
                        <div key={item.product_id} className="flex items-center justify-between gap-2 p-2 bg-muted/30 rounded">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">{item.product_name}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Input
                              type="number"
                              value={item.unit_price}
                              onChange={(e) => updatePrice(item.product_id, parseFloat(e.target.value) || 0)}
                              className="w-20 h-8 text-center"
                            />
                            <div className="flex items-center gap-1">
                              <Button variant="outline" size="icon" className="h-7 w-7" onClick={() => updateQuantity(item.product_id, -1)}>
                                <Minus className="h-3 w-3" />
                              </Button>
                              <span className="w-8 text-center font-medium">{item.quantity}</span>
                              <Button variant="outline" size="icon" className="h-7 w-7" onClick={() => updateQuantity(item.product_id, 1)}>
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                            <span className="font-semibold w-20 text-end">{item.total.toFixed(2)}</span>
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-red-500" onClick={() => removeFromCart(item.product_id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Total & Payment */}
                <div className="space-y-3 p-4 bg-muted/30 rounded-lg">
                  <div className="flex justify-between text-lg font-bold">
                    <span>{t.total}</span>
                    <span>{subtotal.toFixed(2)} {t.currency}</span>
                  </div>
                  
                  <div>
                    <Label>{t.paidAmount}</Label>
                    <Input
                      type="number"
                      value={paidAmount}
                      onChange={(e) => setPaidAmount(parseFloat(e.target.value) || 0)}
                      className="mt-1"
                    />
                  </div>

                  <div className="flex justify-between text-muted-foreground">
                    <span>{t.remaining}</span>
                    <span className={subtotal - paidAmount > 0 ? 'text-amber-600 font-semibold' : ''}>
                      {(subtotal - paidAmount).toFixed(2)} {t.currency}
                    </span>
                  </div>

                  <div>
                    <Label>{t.paymentMethod}</Label>
                    <div className="flex gap-2 mt-2">
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
                      <Button
                        type="button"
                        variant={paymentMethod === 'wallet' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setPaymentMethod('wallet')}
                        className="flex-1"
                      >
                        <Wallet className="h-4 w-4 me-1" />
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label>{t.notes}</Label>
                    <Input
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder={language === 'ar' ? 'ملاحظات...' : 'Notes...'}
                      className="mt-1"
                    />
                  </div>
                </div>

                {/* Complete Button */}
                <Button
                  onClick={completePurchase}
                  disabled={loading || cart.length === 0 || !selectedSupplier}
                  className="w-full h-12 text-lg"
                >
                  {loading ? t.loading : t.completeSale}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
