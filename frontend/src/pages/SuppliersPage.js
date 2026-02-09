import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import { 
  Truck, Plus, Search, Edit, Trash2, Phone, Mail, MapPin, Users, DollarSign,
  Grid3X3, List, ArrowUpDown, SortAsc, SortDesc
} from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Badge } from '../components/ui/badge';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SuppliersPage() {
  const { t, language, isRTL } = useLanguage();
  
  const [suppliers, setSuppliers] = useState([]);
  const [supplierFamilies, setSupplierFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [formData, setFormData] = useState({
    name: '', phone: '', email: '', address: '', notes: '', family_id: '', code: ''
  });

  // View mode and sorting
  const [viewMode, setViewMode] = useState(localStorage.getItem('suppliersViewMode') || 'grid');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  const changeViewMode = (mode) => {
    setViewMode(mode);
    localStorage.setItem('suppliersViewMode', mode);
  };

  // Sort suppliers
  const sortedSuppliers = [...suppliers].sort((a, b) => {
    let comparison = 0;
    switch (sortBy) {
      case 'name':
        comparison = a.name.localeCompare(b.name);
        break;
      case 'balance':
        comparison = (a.balance || 0) - (b.balance || 0);
        break;
      case 'total_purchases':
        comparison = (a.total_purchases || 0) - (b.total_purchases || 0);
        break;
      case 'advance_balance':
        comparison = (a.advance_balance || 0) - (b.advance_balance || 0);
        break;
      default:
        comparison = 0;
    }
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  // Advance Payment Dialog
  const [advancePaymentDialogOpen, setAdvancePaymentDialogOpen] = useState(false);
  const [advancePaymentData, setAdvancePaymentData] = useState({
    supplier_id: '',
    amount: '',
    payment_method: 'cash',
    notes: ''
  });

  // Family dialog
  const [familyDialogOpen, setFamilyDialogOpen] = useState(false);
  const [newFamilyName, setNewFamilyName] = useState('');
  const [savingFamily, setSavingFamily] = useState(false);

  const fetchSuppliers = async () => {
    try {
      const params = searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : '';
      const response = await axios.get(`${API}/suppliers${params}`);
      setSuppliers(response.data);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSupplierFamilies = async () => {
    try {
      const response = await axios.get(`${API}/supplier-families`);
      setSupplierFamilies(response.data);
    } catch (error) {
      console.error('Error fetching supplier families:', error);
    }
  };

  const handleAddFamily = async () => {
    if (!newFamilyName.trim()) return;
    setSavingFamily(true);
    try {
      await axios.post(`${API}/supplier-families`, { name: newFamilyName });
      toast.success(language === 'ar' ? 'تمت إضافة العائلة' : 'Famille ajoutée');
      setFamilyDialogOpen(false);
      setNewFamilyName('');
      fetchSupplierFamilies();
    } catch (error) {
      toast.error(language === 'ar' ? 'حدث خطأ' : 'Une erreur est survenue');
    } finally {
      setSavingFamily(false);
    }
  };

  // Handle Advance Payment
  const handleAdvancePayment = async () => {
    if (!advancePaymentData.amount || parseFloat(advancePaymentData.amount) <= 0) {
      toast.error(language === 'ar' ? 'يرجى إدخال مبلغ صحيح' : 'Veuillez entrer un montant valide');
      return;
    }
    try {
      await axios.post(`${API}/suppliers/${advancePaymentData.supplier_id}/advance-payment`, {
        amount: parseFloat(advancePaymentData.amount),
        payment_method: advancePaymentData.payment_method,
        notes: advancePaymentData.notes
      });
      toast.success(language === 'ar' ? 'تم تسجيل الدفع المتقدم بنجاح' : 'Paiement avancé enregistré');
      setAdvancePaymentDialogOpen(false);
      setAdvancePaymentData({ supplier_id: '', amount: '', payment_method: 'cash', notes: '' });
      fetchSuppliers();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'حدث خطأ' : 'Une erreur est survenue'));
    }
  };

  const openAdvancePaymentDialog = (supplier) => {
    setAdvancePaymentData({
      supplier_id: supplier.id,
      amount: '',
      payment_method: 'cash',
      notes: ''
    });
    setAdvancePaymentDialogOpen(true);
  };

  useEffect(() => {
    fetchSuppliers();
    fetchSupplierFamilies();
  }, [searchQuery]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedSupplier) {
        await axios.put(`${API}/suppliers/${selectedSupplier.id}`, formData);
        toast.success(t.supplierUpdated);
      } else {
        await axios.post(`${API}/suppliers`, formData);
        toast.success(t.supplierAdded);
      }
      setDialogOpen(false);
      resetForm();
      fetchSuppliers();
    } catch (error) {
      toast.error(t.somethingWentWrong);
    }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API}/suppliers/${selectedSupplier.id}`);
      toast.success(t.supplierDeleted);
      setDeleteDialogOpen(false);
      setSelectedSupplier(null);
      fetchSuppliers();
    } catch (error) {
      toast.error(t.somethingWentWrong);
    }
  };

  const openEditDialog = (supplier) => {
    setSelectedSupplier(supplier);
    setFormData({
      name: supplier.name,
      phone: supplier.phone,
      email: supplier.email,
      address: supplier.address,
      notes: supplier.notes,
      family_id: supplier.family_id || ''
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setSelectedSupplier(null);
    setFormData({ name: '', phone: '', email: '', address: '', notes: '', family_id: '' });
  };

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="suppliers-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.suppliers}</h1>
            <p className="text-muted-foreground mt-1">{suppliers.length} {t.suppliers}</p>
          </div>
          <Button onClick={() => { resetForm(); setDialogOpen(true); }} className="gap-2" data-testid="add-supplier-btn">
            <Plus className="h-5 w-5" />
            {t.addSupplier}
          </Button>
        </div>

        {/* Search & Filter */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4 flex-wrap">
              <div className="relative flex-1 min-w-[200px]">
                <Search className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
                <Input
                  type="text"
                  placeholder={t.search}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`h-11 ${isRTL ? 'pr-10' : 'pl-10'}`}
                  data-testid="supplier-search-input"
                />
              </div>
              
              {/* Sort By */}
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[150px]">
                  <ArrowUpDown className="h-4 w-4 me-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">{language === 'ar' ? 'الاسم' : 'Nom'}</SelectItem>
                  <SelectItem value="balance">{language === 'ar' ? 'الرصيد' : 'Solde'}</SelectItem>
                  <SelectItem value="total_purchases">{language === 'ar' ? 'المشتريات' : 'Achats'}</SelectItem>
                  <SelectItem value="advance_balance">{language === 'ar' ? 'الرصيد المتقدم' : 'Avance'}</SelectItem>
                </SelectContent>
              </Select>
              
              {/* Sort Order */}
              <Button
                variant="outline"
                size="icon"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                title={sortOrder === 'asc' ? 'تصاعدي' : 'تنازلي'}
              >
                {sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
              </Button>
              
              {/* View Mode */}
              <div className="flex border rounded-lg">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="icon"
                  onClick={() => changeViewMode('grid')}
                  className="rounded-e-none"
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="icon"
                  onClick={() => changeViewMode('list')}
                  className="rounded-s-none"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Suppliers Display */}
        {loading ? (
          <div className="flex items-center justify-center min-h-[40vh]">
            <div className="spinner" />
          </div>
        ) : sortedSuppliers.length === 0 ? (
          <div className="empty-state py-16">
            <Truck className="h-20 w-20 text-muted-foreground mb-4" />
            <h3 className="text-xl font-medium">{t.noSuppliers}</h3>
          </div>
        ) : viewMode === 'list' ? (
          /* List View - Table Format */
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{language === 'ar' ? 'الاسم' : 'Nom'}</TableHead>
                    <TableHead>{language === 'ar' ? 'الهاتف' : 'Téléphone'}</TableHead>
                    <TableHead>{language === 'ar' ? 'البريد' : 'Email'}</TableHead>
                    <TableHead className="text-center">{t.totalPurchases}</TableHead>
                    <TableHead className="text-center">{t.balance}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'رصيد متقدم' : 'Avance'}</TableHead>
                    <TableHead className="text-center">{language === 'ar' ? 'الإجراءات' : 'Actions'}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedSuppliers.map(supplier => (
                    <TableRow key={supplier.id} data-testid={`supplier-row-${supplier.id}`}>
                      <TableCell className="font-medium">{supplier.name}</TableCell>
                      <TableCell dir="ltr" className="text-muted-foreground">
                        {supplier.phone || '-'}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {supplier.email || '-'}
                      </TableCell>
                      <TableCell className="text-center font-medium">
                        {(supplier.total_purchases || 0).toFixed(2)} {t.currency}
                      </TableCell>
                      <TableCell className={`text-center font-medium ${supplier.balance > 0 ? 'text-destructive' : ''}`}>
                        {(supplier.balance || 0).toFixed(2)} {t.currency}
                      </TableCell>
                      <TableCell className="text-center font-medium text-green-600">
                        {(supplier.advance_balance || 0).toFixed(2)} {t.currency}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-green-600"
                            onClick={() => openAdvancePaymentDialog(supplier)}
                            title={language === 'ar' ? 'دفع متقدم' : 'Paiement avancé'}
                          >
                            <DollarSign className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => openEditDialog(supplier)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-destructive"
                            onClick={() => { setSelectedSupplier(supplier); setDeleteDialogOpen(true); }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        ) : (
          /* Grid View - Cards */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedSuppliers.map(supplier => (
              <Card key={supplier.id} className="hover:shadow-md transition-shadow" data-testid={`supplier-card-${supplier.id}`}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{supplier.name}</h3>
                      {supplier.phone && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-2">
                          <Phone className="h-4 w-4" />
                          <span dir="ltr">{supplier.phone}</span>
                        </div>
                      )}
                      {supplier.email && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                          <Mail className="h-4 w-4" />
                          <span>{supplier.email}</span>
                        </div>
                      )}
                      {supplier.address && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                          <MapPin className="h-4 w-4" />
                          <span>{supplier.address}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openEditDialog(supplier)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive"
                        onClick={() => { setSelectedSupplier(supplier); setDeleteDialogOpen(true); }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex gap-4 mt-4 pt-4 border-t">
                    <div>
                      <p className="text-xs text-muted-foreground">{t.totalPurchases}</p>
                      <p className="font-semibold">{(supplier.total_purchases || 0).toFixed(2)} {t.currency}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">{t.balance}</p>
                      <p className={`font-semibold ${supplier.balance > 0 ? 'text-destructive' : ''}`}>
                        {(supplier.balance || 0).toFixed(2)} {t.currency}
                      </p>
                    </div>
                    {supplier.advance_balance > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground">{language === 'ar' ? 'رصيد متقدم' : 'Avance'}</p>
                        <p className="font-semibold text-green-600">{supplier.advance_balance?.toFixed(2) || '0.00'} {t.currency}</p>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 pt-3 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full gap-2 text-green-600 border-green-300 hover:bg-green-50"
                      onClick={() => openAdvancePaymentDialog(supplier)}
                    >
                      <DollarSign className="h-4 w-4" />
                      {language === 'ar' ? 'دفع متقدم' : 'Paiement avancé'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Add/Edit Dialog - Compact Design */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader className="pb-2">
              <DialogTitle className="text-lg">{selectedSupplier ? t.editSupplier : t.addSupplier}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-3">
              {/* Name & Phone */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{t.supplierName} *</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="h-9"
                    data-testid="supplier-name-input"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.phone}</Label>
                  <Input
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    dir="ltr"
                    className="h-9"
                  />
                </div>
              </div>
              
              {/* Email & Family */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{t.email}</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">{language === 'ar' ? 'العائلة' : 'Famille'}</Label>
                    <Button 
                      type="button" 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => setFamilyDialogOpen(true)}
                      className="h-5 px-1 text-xs"
                    >
                      <Plus className="h-3 w-3" />
                    </Button>
                  </div>
                  <Select
                    value={formData.family_id || "none"}
                    onValueChange={(value) => setFormData({ ...formData, family_id: value === "none" ? "" : value })}
                  >
                    <SelectTrigger className="h-9">
                      <SelectValue placeholder={language === 'ar' ? 'اختر' : 'Choisir'} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">{language === 'ar' ? 'بدون' : 'Sans'}</SelectItem>
                      {supplierFamilies.map(family => (
                        <SelectItem key={family.id} value={family.id}>
                          {family.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {/* Address */}
              <div className="space-y-1">
                <Label className="text-xs">{t.address}</Label>
                <Input
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="h-9"
                />
              </div>
              
              {/* Notes */}
              <div className="space-y-1">
                <Label className="text-xs">{t.notes}</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={2}
                  className="text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setDialogOpen(false)}>
                  {t.cancel}
                </Button>
                <Button type="submit" size="sm" data-testid="save-supplier-btn">{t.save}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Add Family Dialog */}
        <Dialog open={familyDialogOpen} onOpenChange={setFamilyDialogOpen}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                {language === 'ar' ? 'إضافة عائلة موردين جديدة' : 'Ajouter une nouvelle famille'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'اسم العائلة' : 'Nom de la famille'} *</Label>
                <Input
                  value={newFamilyName}
                  onChange={(e) => setNewFamilyName(e.target.value)}
                  placeholder={language === 'ar' ? 'مثال: موردي الهواتف' : 'Ex: Fournisseurs téléphones'}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => { setFamilyDialogOpen(false); setNewFamilyName(''); }}>
                  {t.cancel}
                </Button>
                <Button onClick={handleAddFamily} disabled={savingFamily || !newFamilyName.trim()}>
                  <Plus className="h-4 w-4 me-1" />
                  {language === 'ar' ? 'إضافة' : 'Ajouter'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Delete Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{t.deleteConfirm}</AlertDialogTitle>
              <AlertDialogDescription>
                {selectedSupplier?.name}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>{t.cancel}</AlertDialogCancel>
              <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
                {t.delete}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Advance Payment Dialog */}
        <Dialog open={advancePaymentDialogOpen} onOpenChange={setAdvancePaymentDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                {language === 'ar' ? 'دفع متقدم للمورد' : 'Paiement Avancé au Fournisseur'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'المبلغ' : 'Montant'} *</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={advancePaymentData.amount}
                  onChange={(e) => setAdvancePaymentData({ ...advancePaymentData, amount: e.target.value })}
                  placeholder={language === 'ar' ? 'أدخل المبلغ' : 'Entrez le montant'}
                />
              </div>
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'طريقة الدفع' : 'Mode de paiement'}</Label>
                <Select 
                  value={advancePaymentData.payment_method} 
                  onValueChange={(v) => setAdvancePaymentData({ ...advancePaymentData, payment_method: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cash">{language === 'ar' ? 'نقدي' : 'Cash'}</SelectItem>
                    <SelectItem value="bank">{language === 'ar' ? 'تحويل بنكي' : 'Virement'}</SelectItem>
                    <SelectItem value="check">{language === 'ar' ? 'شيك' : 'Chèque'}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'ملاحظات' : 'Notes'}</Label>
                <Textarea
                  value={advancePaymentData.notes}
                  onChange={(e) => setAdvancePaymentData({ ...advancePaymentData, notes: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setAdvancePaymentDialogOpen(false)}>
                  {t.cancel}
                </Button>
                <Button onClick={handleAdvancePayment} className="bg-green-600 hover:bg-green-700">
                  {language === 'ar' ? 'تأكيد الدفع' : 'Confirmer'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
