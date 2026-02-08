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
import { Truck, Plus, Search, Edit, Trash2, Phone, Mail, MapPin, Users } from 'lucide-react';

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
    name: '', phone: '', email: '', address: '', notes: '', family_id: ''
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

        {/* Search */}
        <Card>
          <CardContent className="p-4">
            <div className="relative">
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
          </CardContent>
        </Card>

        {/* Suppliers Grid */}
        {loading ? (
          <div className="flex items-center justify-center min-h-[40vh]">
            <div className="spinner" />
          </div>
        ) : suppliers.length === 0 ? (
          <div className="empty-state py-16">
            <Truck className="h-20 w-20 text-muted-foreground mb-4" />
            <h3 className="text-xl font-medium">{t.noSuppliers}</h3>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {suppliers.map(supplier => (
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
                      <p className="font-semibold">{supplier.total_purchases.toFixed(2)} {t.currency}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">{t.balance}</p>
                      <p className={`font-semibold ${supplier.balance > 0 ? 'text-destructive' : ''}`}>
                        {supplier.balance.toFixed(2)} {t.currency}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{selectedSupplier ? t.editSupplier : t.addSupplier}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>{t.supplierName} *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  data-testid="supplier-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t.phone}</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label>{t.email}</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>{t.address}</Label>
                <Input
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
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
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  {t.cancel}
                </Button>
                <Button type="submit" data-testid="save-supplier-btn">{t.save}</Button>
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
      </div>
    </Layout>
  );
}
