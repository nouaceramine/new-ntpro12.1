import { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout } from '../components/Layout';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
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
  Receipt,
  Plus,
  Search,
  Filter,
  Calendar,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Trash2,
  Edit,
  Building,
  Zap,
  Truck,
  Users,
  ShoppingBag,
  MoreHorizontal,
  RefreshCw
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EXPENSE_CATEGORIES = [
  { id: 'rent', name_ar: 'إيجار المحل', name_fr: 'Loyer', icon: Building, color: 'bg-blue-500' },
  { id: 'utilities', name_ar: 'فواتير (كهرباء، ماء، غاز)', name_fr: 'Factures', icon: Zap, color: 'bg-yellow-500' },
  { id: 'transport', name_ar: 'نقل وتوصيل', name_fr: 'Transport', icon: Truck, color: 'bg-green-500' },
  { id: 'salaries', name_ar: 'رواتب الموظفين', name_fr: 'Salaires', icon: Users, color: 'bg-purple-500' },
  { id: 'supplies', name_ar: 'مستلزمات المحل', name_fr: 'Fournitures', icon: ShoppingBag, color: 'bg-pink-500' },
  { id: 'maintenance', name_ar: 'صيانة وإصلاحات', name_fr: 'Maintenance', icon: Receipt, color: 'bg-orange-500' },
  { id: 'other', name_ar: 'أخرى', name_fr: 'Autres', icon: MoreHorizontal, color: 'bg-gray-500' },
];

export default function ExpensesPage() {
  const { language, t } = useLanguage();
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all'); // all, today, week, month
  const [stats, setStats] = useState({ total: 0, thisMonth: 0, lastMonth: 0, byCategory: [] });
  
  const [formData, setFormData] = useState({
    title: '',
    category: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    notes: '',
    recurring: false,
    recurring_period: 'monthly'
  });

  useEffect(() => {
    fetchExpenses();
    fetchStats();
  }, []);

  const fetchExpenses = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/expenses`);
      setExpenses(response.data || []);
    } catch (error) {
      console.error('Error fetching expenses:', error);
      toast.error(language === 'ar' ? 'فشل في تحميل التكاليف' : 'Échec du chargement');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/expenses/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleSubmit = async () => {
    if (!formData.title || !formData.category || !formData.amount) {
      toast.error(language === 'ar' ? 'يرجى ملء جميع الحقول المطلوبة' : 'Veuillez remplir tous les champs requis');
      return;
    }

    try {
      const expenseData = {
        ...formData,
        amount: parseFloat(formData.amount)
      };

      if (editingExpense) {
        await axios.put(`${API}/expenses/${editingExpense.id}`, expenseData);
        toast.success(language === 'ar' ? 'تم تحديث التكلفة' : 'Dépense mise à jour');
      } else {
        await axios.post(`${API}/expenses`, expenseData);
        toast.success(language === 'ar' ? 'تمت إضافة التكلفة' : 'Dépense ajoutée');
      }

      setShowAddDialog(false);
      resetForm();
      fetchExpenses();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(language === 'ar' ? 'هل تريد حذف هذه التكلفة؟' : 'Voulez-vous supprimer cette dépense?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/expenses/${id}`);
      toast.success(language === 'ar' ? 'تم حذف التكلفة' : 'Dépense supprimée');
      fetchExpenses();
      fetchStats();
    } catch (error) {
      toast.error(t.somethingWentWrong);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      category: '',
      amount: '',
      date: new Date().toISOString().split('T')[0],
      notes: '',
      recurring: false,
      recurring_period: 'monthly'
    });
    setEditingExpense(null);
  };

  const openEditDialog = (expense) => {
    setEditingExpense(expense);
    setFormData({
      title: expense.title,
      category: expense.category,
      amount: expense.amount.toString(),
      date: expense.date?.split('T')[0] || new Date().toISOString().split('T')[0],
      notes: expense.notes || '',
      recurring: expense.recurring || false,
      recurring_period: expense.recurring_period || 'monthly'
    });
    setShowAddDialog(true);
  };

  const filteredExpenses = expenses.filter(expense => {
    const matchesSearch = expense.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         expense.notes?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || expense.category === categoryFilter;
    
    let matchesDate = true;
    if (dateFilter !== 'all') {
      const expenseDate = new Date(expense.date);
      const now = new Date();
      if (dateFilter === 'today') {
        matchesDate = expenseDate.toDateString() === now.toDateString();
      } else if (dateFilter === 'week') {
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        matchesDate = expenseDate >= weekAgo;
      } else if (dateFilter === 'month') {
        matchesDate = expenseDate.getMonth() === now.getMonth() && expenseDate.getFullYear() === now.getFullYear();
      }
    }
    
    return matchesSearch && matchesCategory && matchesDate;
  });

  const getCategoryInfo = (categoryId) => {
    return EXPENSE_CATEGORIES.find(c => c.id === categoryId) || EXPENSE_CATEGORIES[EXPENSE_CATEGORIES.length - 1];
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-DZ', { minimumFractionDigits: 2 }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('ar-DZ');
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="expenses-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Receipt className="h-6 w-6 text-red-500" />
              {language === 'ar' ? 'إدارة التكاليف' : 'Gestion des dépenses'}
            </h1>
            <p className="text-muted-foreground">
              {language === 'ar' ? 'تتبع وإدارة مصاريف المحل' : 'Suivre et gérer les dépenses du magasin'}
            </p>
          </div>
          <Button onClick={() => { resetForm(); setShowAddDialog(true); }} data-testid="add-expense-btn">
            <Plus className="h-4 w-4 me-2" />
            {language === 'ar' ? 'إضافة تكلفة' : 'Ajouter'}
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                  <DollarSign className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'إجمالي التكاليف' : 'Total dépenses'}</p>
                  <p className="text-xl font-bold text-red-600">{formatCurrency(stats.total)} {t.currency}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Calendar className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'هذا الشهر' : 'Ce mois'}</p>
                  <p className="text-xl font-bold">{formatCurrency(stats.thisMonth)} {t.currency}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <Calendar className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'الشهر الماضي' : 'Mois dernier'}</p>
                  <p className="text-xl font-bold">{formatCurrency(stats.lastMonth)} {t.currency}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${stats.thisMonth <= stats.lastMonth ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                  {stats.thisMonth <= stats.lastMonth ? (
                    <TrendingDown className="h-5 w-5 text-green-600" />
                  ) : (
                    <TrendingUp className="h-5 w-5 text-red-600" />
                  )}
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'الفرق' : 'Différence'}</p>
                  <p className={`text-xl font-bold ${stats.thisMonth <= stats.lastMonth ? 'text-green-600' : 'text-red-600'}`}>
                    {stats.thisMonth <= stats.lastMonth ? '-' : '+'}
                    {formatCurrency(Math.abs(stats.thisMonth - stats.lastMonth))} {t.currency}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Categories Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{language === 'ar' ? 'التكاليف حسب الفئة' : 'Dépenses par catégorie'}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {EXPENSE_CATEGORIES.map(cat => {
                const catStats = stats.byCategory?.find(c => c.category === cat.id);
                const Icon = cat.icon;
                return (
                  <div key={cat.id} className="p-3 border rounded-lg text-center hover:shadow-md transition-shadow">
                    <div className={`w-10 h-10 ${cat.color} rounded-full flex items-center justify-center mx-auto mb-2`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{language === 'ar' ? cat.name_ar : cat.name_fr}</p>
                    <p className="font-bold text-sm">{formatCurrency(catStats?.total || 0)}</p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Filters & Table */}
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row gap-4 justify-between">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={language === 'ar' ? 'بحث...' : 'Rechercher...'}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pe-10"
                />
              </div>
              <div className="flex gap-2">
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                  <SelectTrigger className="w-[150px]">
                    <Filter className="h-4 w-4 me-2" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{language === 'ar' ? 'كل الفئات' : 'Toutes'}</SelectItem>
                    {EXPENSE_CATEGORIES.map(cat => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {language === 'ar' ? cat.name_ar : cat.name_fr}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={dateFilter} onValueChange={setDateFilter}>
                  <SelectTrigger className="w-[130px]">
                    <Calendar className="h-4 w-4 me-2" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{language === 'ar' ? 'كل الفترات' : 'Toutes'}</SelectItem>
                    <SelectItem value="today">{language === 'ar' ? 'اليوم' : 'Aujourd\'hui'}</SelectItem>
                    <SelectItem value="week">{language === 'ar' ? 'هذا الأسبوع' : 'Cette semaine'}</SelectItem>
                    <SelectItem value="month">{language === 'ar' ? 'هذا الشهر' : 'Ce mois'}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredExpenses.length === 0 ? (
              <div className="text-center py-8">
                <Receipt className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">
                  {language === 'ar' ? 'لا توجد تكاليف' : 'Aucune dépense'}
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{language === 'ar' ? 'الفئة' : 'Catégorie'}</TableHead>
                    <TableHead>{language === 'ar' ? 'الوصف' : 'Description'}</TableHead>
                    <TableHead>{language === 'ar' ? 'المبلغ' : 'Montant'}</TableHead>
                    <TableHead>{language === 'ar' ? 'التاريخ' : 'Date'}</TableHead>
                    <TableHead>{language === 'ar' ? 'إجراءات' : 'Actions'}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredExpenses.map(expense => {
                    const catInfo = getCategoryInfo(expense.category);
                    const Icon = catInfo.icon;
                    return (
                      <TableRow key={expense.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className={`p-1.5 ${catInfo.color} rounded-lg`}>
                              <Icon className="h-4 w-4 text-white" />
                            </div>
                            <span className="text-sm">{language === 'ar' ? catInfo.name_ar : catInfo.name_fr}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{expense.title}</p>
                            {expense.notes && <p className="text-xs text-muted-foreground truncate max-w-[200px]">{expense.notes}</p>}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="font-bold text-red-600">{formatCurrency(expense.amount)} {t.currency}</span>
                        </TableCell>
                        <TableCell>{formatDate(expense.date)}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button variant="ghost" size="icon" onClick={() => openEditDialog(expense)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleDelete(expense.id)} className="text-red-600 hover:text-red-700">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Add/Edit Dialog */}
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {editingExpense 
                  ? (language === 'ar' ? 'تعديل التكلفة' : 'Modifier la dépense')
                  : (language === 'ar' ? 'إضافة تكلفة جديدة' : 'Ajouter une dépense')}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'الفئة *' : 'Catégorie *'}</Label>
                <Select value={formData.category} onValueChange={(v) => setFormData(p => ({ ...p, category: v }))}>
                  <SelectTrigger>
                    <SelectValue placeholder={language === 'ar' ? 'اختر الفئة' : 'Choisir'} />
                  </SelectTrigger>
                  <SelectContent>
                    {EXPENSE_CATEGORIES.map(cat => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {language === 'ar' ? cat.name_ar : cat.name_fr}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>{language === 'ar' ? 'الوصف *' : 'Description *'}</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData(p => ({ ...p, title: e.target.value }))}
                  placeholder={language === 'ar' ? 'وصف التكلفة' : 'Description'}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{language === 'ar' ? 'المبلغ *' : 'Montant *'}</Label>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData(p => ({ ...p, amount: e.target.value }))}
                    placeholder="0.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{language === 'ar' ? 'التاريخ' : 'Date'}</Label>
                  <Input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData(p => ({ ...p, date: e.target.value }))}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>{language === 'ar' ? 'ملاحظات' : 'Notes'}</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData(p => ({ ...p, notes: e.target.value }))}
                  placeholder={language === 'ar' ? 'ملاحظات إضافية...' : 'Notes...'}
                  rows={2}
                />
              </div>

              <div className="flex gap-2 pt-4">
                <Button variant="outline" className="flex-1" onClick={() => setShowAddDialog(false)}>
                  {language === 'ar' ? 'إلغاء' : 'Annuler'}
                </Button>
                <Button className="flex-1" onClick={handleSubmit}>
                  {editingExpense 
                    ? (language === 'ar' ? 'تحديث' : 'Mettre à jour')
                    : (language === 'ar' ? 'إضافة' : 'Ajouter')}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
