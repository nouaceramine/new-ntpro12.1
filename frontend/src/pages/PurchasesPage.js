import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
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
  TrendingDown,
  Calculator,
  FileText,
  Calendar,
  Users,
  Receipt,
  DollarSign,
  History,
  AlertCircle,
  PlusCircle,
  Save,
  Edit,
  Image,
  Upload,
  X,
  Check,
  RefreshCw,
  Percent,
  Tag
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PurchasesPage() {
  const { t, language, isRTL } = useLanguage();
  const searchInputRef = useRef(null);
  
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [supplierDebts, setSupplierDebts] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [paidAmount, setPaidAmount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [paymentType, setPaymentType] = useState('cash'); // cash, credit, partial
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [showNewPurchaseDialog, setShowNewPurchaseDialog] = useState(false);
  const [showPayDebtDialog, setShowPayDebtDialog] = useState(false);
  const [selectedDebt, setSelectedDebt] = useState(null);
  const [debtPaymentAmount, setDebtPaymentAmount] = useState(0);
  const [activeTab, setActiveTab] = useState('purchases');
  
  // New supplier dialog
  const [showNewSupplierDialog, setShowNewSupplierDialog] = useState(false);
  const [newSupplierData, setNewSupplierData] = useState({
    name: '',
    phone: '',
    email: '',
    address: ''
  });
  const [addingSupplier, setAddingSupplier] = useState(false);

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
      
      // Calculate supplier debts
      calculateSupplierDebts(purchasesRes.data, suppliersRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const calculateSupplierDebts = (purchasesData, suppliersData) => {
    const debts = {};
    purchasesData.forEach(p => {
      if (p.remaining > 0) {
        if (!debts[p.supplier_id]) {
          const supplier = suppliersData.find(s => s.id === p.supplier_id);
          debts[p.supplier_id] = {
            supplier_id: p.supplier_id,
            supplier_name: supplier?.name || p.supplier_name,
            total_debt: 0,
            purchases: []
          };
        }
        debts[p.supplier_id].total_debt += p.remaining;
        debts[p.supplier_id].purchases.push(p);
      }
    });
    setSupplierDebts(Object.values(debts));
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
  
  // Auto-set paid amount based on payment type
  useEffect(() => {
    if (paymentType === 'cash') {
      setPaidAmount(subtotal);
    } else if (paymentType === 'credit') {
      setPaidAmount(0);
    }
  }, [paymentType, subtotal]);

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
        payment_type: paymentType,
        notes
      };

      await axios.post(`${API}/purchases`, purchaseData);
      
      const msg = paymentType === 'credit' 
        ? (language === 'ar' ? 'تم تسجيل الشراء بالدين' : 'Achat à crédit enregistré')
        : paymentType === 'partial'
        ? (language === 'ar' ? 'تم تسجيل الشراء مع دفعة جزئية' : 'Achat avec paiement partiel enregistré')
        : t.purchaseCompleted;
      
      toast.success(msg);
      
      // Reset
      setCart([]);
      setPaidAmount(0);
      setSelectedSupplier(null);
      setNotes('');
      setPaymentType('cash');
      setShowNewPurchaseDialog(false);
      fetchData();
    } catch (error) {
      console.error('Error completing purchase:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  const openPayDebtDialog = (debt) => {
    setSelectedDebt(debt);
    setDebtPaymentAmount(debt.total_debt);
    setShowPayDebtDialog(true);
  };

  const paySupplierDebt = async () => {
    if (!selectedDebt || debtPaymentAmount <= 0) return;

    setLoading(true);
    try {
      await axios.post(`${API}/supplier-debts/pay`, {
        supplier_id: selectedDebt.supplier_id,
        amount: debtPaymentAmount,
        payment_method: paymentMethod
      });
      
      toast.success(language === 'ar' ? 'تم تسجيل الدفعة بنجاح' : 'Paiement enregistré avec succès');
      setShowPayDebtDialog(false);
      setSelectedDebt(null);
      setDebtPaymentAmount(0);
      fetchData();
    } catch (error) {
      console.error('Error paying debt:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  // Add new supplier
  const handleAddSupplier = async (createNew = false) => {
    if (!newSupplierData.name.trim()) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم المورد' : 'Veuillez entrer le nom du fournisseur');
      return;
    }

    setAddingSupplier(true);
    try {
      const response = await axios.post(`${API}/suppliers`, newSupplierData);
      toast.success(language === 'ar' ? 'تمت إضافة المورد بنجاح' : 'Fournisseur ajouté avec succès');
      
      // Add to suppliers list and select it
      setSuppliers(prev => [...prev, response.data]);
      setSelectedSupplier(response.data.id);
      
      // Reset form
      setNewSupplierData({ name: '', phone: '', email: '', address: '' });
      
      if (!createNew) {
        setShowNewSupplierDialog(false);
      }
    } catch (error) {
      console.error('Error adding supplier:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setAddingSupplier(false);
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

  const selectedSupplierData = suppliers.find(s => s.id === selectedSupplier);
  const supplierPreviousDebt = supplierDebts.find(d => d.supplier_id === selectedSupplier)?.total_debt || 0;

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="purchases-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.purchases}</h1>
            <p className="text-muted-foreground mt-1">
              {language === 'ar' ? 'إدارة المشتريات وحسابات الموردين' : 'Gestion des achats et comptes fournisseurs'}
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

          <Card className={totalRemaining > 0 ? 'border-red-200 bg-red-50/30' : ''}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'ديون الموردين' : 'Dettes fournisseurs'}</p>
                  <p className="text-2xl font-bold mt-1 text-red-600">{totalRemaining.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
                <div className="p-3 rounded-xl bg-red-100 text-red-600">
                  <TrendingDown className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'موردين بديون' : 'Fournisseurs débiteurs'}</p>
                  <p className="text-2xl font-bold mt-1">{supplierDebts.length}</p>
                  <p className="text-xs text-muted-foreground">{language === 'ar' ? 'مورد' : 'fournisseurs'}</p>
                </div>
                <div className="p-3 rounded-xl bg-purple-100 text-purple-600">
                  <Users className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="purchases" className="gap-2">
              <Receipt className="h-4 w-4" />
              {language === 'ar' ? 'سجل المشتريات' : 'Historique'}
            </TabsTrigger>
            <TabsTrigger value="debts" className="gap-2">
              <AlertCircle className="h-4 w-4" />
              {language === 'ar' ? 'حسابات الموردين' : 'Comptes'}
              {totalRemaining > 0 && (
                <Badge variant="destructive" className="ms-1">{supplierDebts.length}</Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Purchases History Tab */}
          <TabsContent value="purchases">
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
                            <TableCell className={purchase.remaining > 0 ? 'text-red-600 font-semibold' : ''}>
                              {purchase.remaining.toFixed(2)} {t.currency}
                            </TableCell>
                            <TableCell>{getStatusBadge(purchase.status)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Supplier Debts Tab */}
          <TabsContent value="debts">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  {language === 'ar' ? 'حسابات الموردين' : 'Comptes fournisseurs'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {supplierDebts.length === 0 ? (
                  <div className="text-center py-12">
                    <DollarSign className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
                    <p className="text-emerald-600 font-medium">
                      {language === 'ar' ? 'لا توجد ديون للموردين' : 'Aucune dette fournisseur'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {supplierDebts.map(debt => (
                      <div key={debt.supplier_id} className="border rounded-lg p-4 hover:bg-muted/30 transition-colors">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-full bg-red-100">
                              <Truck className="h-5 w-5 text-red-600" />
                            </div>
                            <div>
                              <h4 className="font-semibold">{debt.supplier_name}</h4>
                              <p className="text-sm text-muted-foreground">
                                {debt.purchases.length} {language === 'ar' ? 'فاتورة غير مسددة' : 'factures impayées'}
                              </p>
                            </div>
                          </div>
                          <div className="text-end">
                            <p className="text-2xl font-bold text-red-600">{debt.total_debt.toFixed(2)}</p>
                            <p className="text-xs text-muted-foreground">{t.currency}</p>
                          </div>
                        </div>
                        
                        <div className="flex gap-2 mt-3">
                          <Button 
                            size="sm" 
                            onClick={() => openPayDebtDialog(debt)}
                            className="gap-1"
                          >
                            <Banknote className="h-4 w-4" />
                            {language === 'ar' ? 'تسديد الدين' : 'Payer'}
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            className="gap-1"
                          >
                            <History className="h-4 w-4" />
                            {language === 'ar' ? 'السجل' : 'Historique'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

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
                  <div className="flex items-center justify-between mb-1">
                    <Label>{t.selectSupplier}</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setShowNewSupplierDialog(true)}
                      className="gap-1 h-7"
                    >
                      <Plus className="h-3 w-3" />
                      {language === 'ar' ? 'مورد جديد' : 'Nouveau'}
                    </Button>
                  </div>
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
                  {selectedSupplier && supplierPreviousDebt > 0 && (
                    <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {language === 'ar' ? `دين سابق: ${supplierPreviousDebt.toFixed(2)} ${t.currency}` : `Dette précédente: ${supplierPreviousDebt.toFixed(2)} ${t.currency}`}
                    </p>
                  )}
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

                {/* Payment Type Selection */}
                <div className="p-4 bg-muted/30 rounded-lg space-y-4">
                  <div className="flex justify-between text-lg font-bold">
                    <span>{t.total}</span>
                    <span>{subtotal.toFixed(2)} {t.currency}</span>
                  </div>

                  {/* Payment Type */}
                  <div>
                    <Label>{language === 'ar' ? 'نوع الدفع' : 'Type de paiement'}</Label>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      <Button
                        type="button"
                        variant={paymentType === 'cash' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setPaymentType('cash')}
                        className="flex-col h-16 gap-1"
                      >
                        <Banknote className="h-5 w-5" />
                        <span className="text-xs">{language === 'ar' ? 'نقداً' : 'Comptant'}</span>
                      </Button>
                      <Button
                        type="button"
                        variant={paymentType === 'credit' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setPaymentType('credit')}
                        className="flex-col h-16 gap-1 border-red-200 hover:border-red-300"
                      >
                        <CreditCard className="h-5 w-5" />
                        <span className="text-xs">{language === 'ar' ? 'دين' : 'Crédit'}</span>
                      </Button>
                      <Button
                        type="button"
                        variant={paymentType === 'partial' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setPaymentType('partial')}
                        className="flex-col h-16 gap-1 border-amber-200 hover:border-amber-300"
                      >
                        <Calculator className="h-5 w-5" />
                        <span className="text-xs">{language === 'ar' ? 'جزئي' : 'Partiel'}</span>
                      </Button>
                    </div>
                  </div>

                  {/* Paid Amount (for partial payment) */}
                  {paymentType === 'partial' && (
                    <div>
                      <Label>{t.paidAmount}</Label>
                      <Input
                        type="number"
                        value={paidAmount}
                        onChange={(e) => setPaidAmount(Math.min(parseFloat(e.target.value) || 0, subtotal))}
                        className="mt-1"
                        max={subtotal}
                      />
                    </div>
                  )}

                  {/* Remaining */}
                  {paymentType !== 'cash' && (
                    <div className="flex justify-between text-red-600 font-semibold p-2 bg-red-50 rounded">
                      <span>{language === 'ar' ? 'سيُسجل كدين' : 'Sera enregistré comme dette'}</span>
                      <span>{(subtotal - paidAmount).toFixed(2)} {t.currency}</span>
                    </div>
                  )}

                  {/* Payment Method */}
                  {(paymentType === 'cash' || paymentType === 'partial') && (
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
                  )}

                  <div>
                    <Label>{t.notes}</Label>
                    <Textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder={language === 'ar' ? 'ملاحظات...' : 'Notes...'}
                      className="mt-1"
                      rows={2}
                    />
                  </div>
                </div>

                {/* Complete Button */}
                <Button
                  onClick={completePurchase}
                  disabled={loading || cart.length === 0 || !selectedSupplier}
                  className={`w-full h-12 text-lg ${paymentType === 'credit' ? 'bg-red-600 hover:bg-red-700' : ''}`}
                >
                  {loading ? t.loading : (
                    paymentType === 'credit' 
                      ? (language === 'ar' ? 'تسجيل شراء بالدين' : 'Enregistrer achat à crédit')
                      : t.completeSale
                  )}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Pay Debt Dialog */}
        <Dialog open={showPayDebtDialog} onOpenChange={setShowPayDebtDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                {language === 'ar' ? 'تسديد دين المورد' : 'Payer dette fournisseur'}
              </DialogTitle>
            </DialogHeader>

            {selectedDebt && (
              <div className="space-y-4 mt-4">
                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <Truck className="h-6 w-6 text-muted-foreground" />
                    <div>
                      <p className="font-semibold">{selectedDebt.supplier_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedDebt.purchases.length} {language === 'ar' ? 'فاتورة' : 'factures'}
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-between text-lg">
                    <span>{language === 'ar' ? 'إجمالي الدين' : 'Total dette'}</span>
                    <span className="font-bold text-red-600">{selectedDebt.total_debt.toFixed(2)} {t.currency}</span>
                  </div>
                </div>

                <div>
                  <Label>{language === 'ar' ? 'المبلغ المدفوع' : 'Montant à payer'}</Label>
                  <Input
                    type="number"
                    value={debtPaymentAmount}
                    onChange={(e) => setDebtPaymentAmount(Math.min(parseFloat(e.target.value) || 0, selectedDebt.total_debt))}
                    className="mt-1"
                    max={selectedDebt.total_debt}
                  />
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
                  </div>
                </div>

                {debtPaymentAmount < selectedDebt.total_debt && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
                    {language === 'ar' ? 'سيتبقى' : 'Restera'}: {(selectedDebt.total_debt - debtPaymentAmount).toFixed(2)} {t.currency}
                  </div>
                )}

                <Button
                  onClick={paySupplierDebt}
                  disabled={loading || debtPaymentAmount <= 0}
                  className="w-full"
                >
                  {loading ? t.loading : (language === 'ar' ? 'تأكيد الدفع' : 'Confirmer le paiement')}
                </Button>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* New Supplier Dialog */}
        <Dialog open={showNewSupplierDialog} onOpenChange={setShowNewSupplierDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {language === 'ar' ? 'إضافة مورد جديد' : 'Ajouter un fournisseur'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'اسم المورد *' : 'Nom du fournisseur *'}</Label>
                <Input
                  value={newSupplierData.name}
                  onChange={(e) => setNewSupplierData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder={language === 'ar' ? 'اسم المورد' : 'Nom'}
                />
              </div>
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'رقم الهاتف' : 'Téléphone'}</Label>
                <Input
                  value={newSupplierData.phone}
                  onChange={(e) => setNewSupplierData(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="0555 123 456"
                />
              </div>
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'البريد الإلكتروني' : 'Email'}</Label>
                <Input
                  type="email"
                  value={newSupplierData.email}
                  onChange={(e) => setNewSupplierData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="supplier@example.com"
                />
              </div>
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'العنوان' : 'Adresse'}</Label>
                <Input
                  value={newSupplierData.address}
                  onChange={(e) => setNewSupplierData(prev => ({ ...prev, address: e.target.value }))}
                  placeholder={language === 'ar' ? 'عنوان المورد' : 'Adresse'}
                />
              </div>
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowNewSupplierDialog(false);
                    setNewSupplierData({ name: '', phone: '', email: '', address: '' });
                  }}
                >
                  {language === 'ar' ? 'إلغاء' : 'Annuler'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleAddSupplier(true)}
                  disabled={addingSupplier || !newSupplierData.name.trim()}
                  className="gap-2"
                >
                  <PlusCircle className="h-4 w-4" />
                  {language === 'ar' ? 'حفظ وإنشاء جديد' : 'Enregistrer et créer nouveau'}
                </Button>
                <Button
                  onClick={() => handleAddSupplier(false)}
                  disabled={addingSupplier || !newSupplierData.name.trim()}
                  className="gap-2"
                >
                  <Save className="h-4 w-4" />
                  {addingSupplier ? (language === 'ar' ? 'جاري الحفظ...' : 'Enregistrement...') : (language === 'ar' ? 'حفظ' : 'Enregistrer')}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
