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
import { toast } from 'sonner';
import { Users, Plus, Search, Edit, Trash2, Phone, Mail, MapPin, PlusCircle, Save, Ban, Shield, ShieldOff } from 'lucide-react';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CustomersPage() {
  const { t, language, isRTL } = useLanguage();
  
  const [customers, setCustomers] = useState([]);
  const [customerFamilies, setCustomerFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '', 
    phone: '', 
    email: '', 
    address: '', 
    notes: '', 
    family_id: '',
    // New fields
    national_id: '',
    commercial_register: '',
    birthdate: '',
    customer_type: 'regular', // VIP, regular, new
    max_debt_limit: '',
    special_discount: ''
  });
  
  // Family dialog
  const [familyDialogOpen, setFamilyDialogOpen] = useState(false);
  const [newFamilyName, setNewFamilyName] = useState('');
  const [savingFamily, setSavingFamily] = useState(false);
  
  // Blacklist state
  const [blacklist, setBlacklist] = useState([]);
  const [showBlacklistOnly, setShowBlacklistOnly] = useState(false);
  const [blacklistDialogOpen, setBlacklistDialogOpen] = useState(false);
  const [blacklistCustomer, setBlacklistCustomer] = useState(null);
  const [blacklistReason, setBlacklistReason] = useState('');

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

  const handleAddToBlacklist = async () => {
    if (!blacklistCustomer?.phone) {
      toast.error(language === 'ar' ? 'يجب أن يكون للزبون رقم هاتف' : 'Le client doit avoir un numéro de téléphone');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/blacklist`, {
        phone: blacklistCustomer.phone,
        reason: blacklistReason,
        notes: `${language === 'ar' ? 'الزبون:' : 'Client:'} ${blacklistCustomer.name}`
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تمت إضافة الزبون للقائمة السوداء' : 'Client ajouté à la liste noire');
      setBlacklistDialogOpen(false);
      setBlacklistReason('');
      setBlacklistCustomer(null);
      fetchBlacklist();
      fetchCustomers();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'حدث خطأ' : 'Une erreur est survenue'));
    }
  };

  const handleRemoveFromBlacklist = async (phone) => {
    const entry = blacklist.find(b => b.phone === phone);
    if (!entry) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/blacklist/${entry.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تمت إزالة الزبون من القائمة السوداء' : 'Client retiré de la liste noire');
      fetchBlacklist();
      fetchCustomers();
    } catch (error) {
      toast.error(error.response?.data?.detail || (language === 'ar' ? 'حدث خطأ' : 'Une erreur est survenue'));
    }
  };

  const isBlacklisted = (phone) => {
    return phone && blacklist.some(b => b.phone === phone);
  };

  const fetchCustomers = async () => {
    try {
      const params = searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : '';
      const response = await axios.get(`${API}/customers${params}`);
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomerFamilies = async () => {
    try {
      const response = await axios.get(`${API}/customer-families`);
      setCustomerFamilies(response.data);
    } catch (error) {
      console.error('Error fetching customer families:', error);
    }
  };

  const handleAddFamily = async () => {
    if (!newFamilyName.trim()) return;
    setSavingFamily(true);
    try {
      await axios.post(`${API}/customer-families`, { name: newFamilyName });
      toast.success(language === 'ar' ? 'تمت إضافة العائلة' : 'Famille ajoutée');
      setFamilyDialogOpen(false);
      setNewFamilyName('');
      fetchCustomerFamilies();
    } catch (error) {
      toast.error(language === 'ar' ? 'حدث خطأ' : 'Une erreur est survenue');
    } finally {
      setSavingFamily(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
    fetchBlacklist();
    fetchCustomerFamilies();
  }, [searchQuery]);

  const handleSubmit = async (e, createNew = false) => {
    e?.preventDefault();
    setSaving(true);
    try {
      if (selectedCustomer) {
        await axios.put(`${API}/customers/${selectedCustomer.id}`, formData);
        toast.success(t.customerUpdated);
        setDialogOpen(false);
        resetForm();
      } else {
        await axios.post(`${API}/customers`, formData);
        toast.success(t.customerAdded);
        if (createNew) {
          resetForm();
        } else {
          setDialogOpen(false);
          resetForm();
        }
      }
      fetchCustomers();
    } catch (error) {
      toast.error(t.somethingWentWrong);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API}/customers/${selectedCustomer.id}`);
      toast.success(t.customerDeleted);
      setDeleteDialogOpen(false);
      setSelectedCustomer(null);
      fetchCustomers();
    } catch (error) {
      toast.error(t.somethingWentWrong);
    }
  };

  const openEditDialog = (customer) => {
    setSelectedCustomer(customer);
    setFormData({
      name: customer.name,
      phone: customer.phone,
      email: customer.email,
      address: customer.address,
      notes: customer.notes
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setSelectedCustomer(null);
    setFormData({ name: '', phone: '', email: '', address: '', notes: '', family_id: '' });
  };

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="customers-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.customers}</h1>
            <p className="text-muted-foreground mt-1">{customers.length} {t.customers}</p>
          </div>
          <Button onClick={() => { resetForm(); setDialogOpen(true); }} className="gap-2" data-testid="add-customer-btn">
            <Plus className="h-5 w-5" />
            {t.addCustomer}
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
                  data-testid="customer-search-input"
                />
              </div>
              
              {/* Blacklist Filter */}
              <div className="flex items-center gap-2 bg-gray-100 rounded-lg px-3 py-2">
                <Ban className={`h-4 w-4 ${showBlacklistOnly ? 'text-red-600' : 'text-gray-500'}`} />
                <Label className="text-sm cursor-pointer" htmlFor="blacklist-filter">
                  {language === 'ar' ? 'القائمة السوداء فقط' : 'Liste noire uniquement'}
                </Label>
                <Switch
                  id="blacklist-filter"
                  checked={showBlacklistOnly}
                  onCheckedChange={setShowBlacklistOnly}
                  data-testid="blacklist-filter-switch"
                />
              </div>
              
              {blacklist.length > 0 && (
                <Badge variant="destructive" className="gap-1">
                  <Ban className="h-3 w-3" />
                  {blacklist.length} {language === 'ar' ? 'محظور' : 'bloqué(s)'}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Customers Grid */}
        {loading ? (
          <div className="flex items-center justify-center min-h-[40vh]">
            <div className="spinner" />
          </div>
        ) : customers.length === 0 ? (
          <div className="empty-state py-16">
            <Users className="h-20 w-20 text-muted-foreground mb-4" />
            <h3 className="text-xl font-medium">{t.noCustomers}</h3>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {customers
              .filter(customer => !showBlacklistOnly || isBlacklisted(customer.phone))
              .map(customer => {
                const customerIsBlacklisted = isBlacklisted(customer.phone);
                return (
                  <Card 
                    key={customer.id} 
                    className={`hover:shadow-md transition-shadow ${customerIsBlacklisted ? 'border-red-300 bg-red-50/50' : ''}`} 
                    data-testid={`customer-card-${customer.id}`}
                  >
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-lg">{customer.name}</h3>
                            {customerIsBlacklisted && (
                              <Badge variant="destructive" className="text-xs gap-1">
                                <Ban className="h-3 w-3" />
                                {language === 'ar' ? 'محظور' : 'Bloqué'}
                              </Badge>
                            )}
                          </div>
                          {customer.phone && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-2">
                              <Phone className="h-4 w-4" />
                              <span dir="ltr">{customer.phone}</span>
                            </div>
                          )}
                          {customer.email && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                              <Mail className="h-4 w-4" />
                              <span>{customer.email}</span>
                            </div>
                          )}
                          {customer.address && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                              <MapPin className="h-4 w-4" />
                              <span>{customer.address}</span>
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col gap-1">
                          {/* Blacklist Toggle Button */}
                          {customer.phone && (
                            customerIsBlacklisted ? (
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-green-600 border-green-300 hover:bg-green-50 gap-1"
                                onClick={() => handleRemoveFromBlacklist(customer.phone)}
                                title={language === 'ar' ? 'إزالة من القائمة السوداء' : 'Retirer de la liste noire'}
                                data-testid={`unblock-customer-${customer.id}`}
                              >
                                <ShieldOff className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-red-600 border-red-300 hover:bg-red-50 gap-1"
                                onClick={() => { setBlacklistCustomer(customer); setBlacklistDialogOpen(true); }}
                                title={language === 'ar' ? 'إضافة للقائمة السوداء' : 'Ajouter à la liste noire'}
                                data-testid={`block-customer-${customer.id}`}
                              >
                                <Shield className="h-4 w-4" />
                              </Button>
                            )
                          )}
                          <Button variant="ghost" size="sm" onClick={() => openEditDialog(customer)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            onClick={() => { setSelectedCustomer(customer); setDeleteDialogOpen(true); }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="flex gap-4 mt-4 pt-4 border-t">
                        <div>
                          <p className="text-xs text-muted-foreground">{t.totalPurchases}</p>
                          <p className="font-semibold">{customer.total_purchases.toFixed(2)} {t.currency}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">{t.balance}</p>
                          <p className={`font-semibold ${customer.balance > 0 ? 'text-amber-600' : ''}`}>
                            {customer.balance.toFixed(2)} {t.currency}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
          </div>
        )}

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{selectedCustomer ? t.editCustomer : t.addCustomer}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>{t.customerName} *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  data-testid="customer-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t.phone}</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  dir="ltr"
                  data-testid="customer-phone-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t.email}</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  data-testid="customer-email-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t.address}</Label>
                <Input
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  data-testid="customer-address-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t.notes}</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={2}
                />
              </div>
              
              {/* Customer Family */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{language === 'ar' ? 'عائلة الزبون' : 'Famille client'}</Label>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setFamilyDialogOpen(true)}
                    className="gap-1 h-7 text-xs"
                  >
                    <Plus className="h-3 w-3" />
                    {language === 'ar' ? 'إضافة عائلة' : 'Ajouter'}
                  </Button>
                </div>
                <Select
                  value={formData.family_id || "none"}
                  onValueChange={(value) => setFormData({ ...formData, family_id: value === "none" ? "" : value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={language === 'ar' ? 'اختر عائلة' : 'Choisir famille'} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">{language === 'ar' ? 'بدون عائلة' : 'Sans famille'}</SelectItem>
                    {customerFamilies.map(family => (
                      <SelectItem key={family.id} value={family.id}>
                        {family.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  {t.cancel}
                </Button>
                {!selectedCustomer && (
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={() => handleSubmit(null, true)}
                    disabled={saving}
                    className="gap-2"
                    data-testid="save-and-new-customer-btn"
                  >
                    <PlusCircle className="h-4 w-4" />
                    {language === 'ar' ? 'حفظ وإنشاء جديد' : 'Enregistrer et créer nouveau'}
                  </Button>
                )}
                <Button type="submit" disabled={saving} className="gap-2" data-testid="save-customer-btn">
                  <Save className="h-4 w-4" />
                  {saving ? (language === 'ar' ? 'جاري الحفظ...' : 'Enregistrement...') : t.save}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Delete Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{t.deleteConfirm}</AlertDialogTitle>
              <AlertDialogDescription>
                {selectedCustomer?.name}
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

        {/* Blacklist Dialog */}
        <Dialog open={blacklistDialogOpen} onOpenChange={setBlacklistDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-red-600">
                <Ban className="h-5 w-5" />
                {language === 'ar' ? 'إضافة للقائمة السوداء' : 'Ajouter à la liste noire'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="font-medium">{blacklistCustomer?.name}</p>
                <p className="text-sm text-muted-foreground">{blacklistCustomer?.phone}</p>
              </div>
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'سبب الحظر' : 'Raison du blocage'}</Label>
                <Select value={blacklistReason} onValueChange={setBlacklistReason}>
                  <SelectTrigger data-testid="blacklist-reason-select">
                    <SelectValue placeholder={language === 'ar' ? 'اختر السبب' : 'Choisir la raison'} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="عدم الدفع">{language === 'ar' ? 'عدم الدفع' : 'Non-paiement'}</SelectItem>
                    <SelectItem value="سلوك سيء">{language === 'ar' ? 'سلوك سيء' : 'Mauvais comportement'}</SelectItem>
                    <SelectItem value="احتيال">{language === 'ar' ? 'احتيال' : 'Fraude'}</SelectItem>
                    <SelectItem value="إرجاع متكرر">{language === 'ar' ? 'إرجاع متكرر' : 'Retours fréquents'}</SelectItem>
                    <SelectItem value="أخرى">{language === 'ar' ? 'أخرى' : 'Autre'}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => { 
                    setBlacklistDialogOpen(false); 
                    setBlacklistReason(''); 
                    setBlacklistCustomer(null); 
                  }}
                >
                  {t.cancel}
                </Button>
                <Button 
                  onClick={handleAddToBlacklist}
                  className="bg-red-600 hover:bg-red-700 gap-2"
                  disabled={!blacklistReason}
                  data-testid="confirm-blacklist-btn"
                >
                  <Ban className="h-4 w-4" />
                  {language === 'ar' ? 'تأكيد الحظر' : 'Confirmer le blocage'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Add Family Dialog */}
        <Dialog open={familyDialogOpen} onOpenChange={setFamilyDialogOpen}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                {language === 'ar' ? 'إضافة عائلة زبائن جديدة' : 'Ajouter une nouvelle famille'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'اسم العائلة' : 'Nom de la famille'} *</Label>
                <Input
                  value={newFamilyName}
                  onChange={(e) => setNewFamilyName(e.target.value)}
                  placeholder={language === 'ar' ? 'مثال: زبائن VIP' : 'Ex: Clients VIP'}
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
      </div>
    </Layout>
  );
}
