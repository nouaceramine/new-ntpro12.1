import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../../contexts/LanguageContext';
import { Layout } from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { Textarea } from '../../components/ui/textarea';
import { toast } from 'sonner';
import { 
  Users, Building, CreditCard, TrendingUp, Package, 
  Settings, Plus, Edit, Trash2, Check, X, Clock,
  AlertTriangle, DollarSign, Search, MoreHorizontal,
  Star, Eye, EyeOff, Ban, RefreshCw, Calendar, Store, Truck, ShoppingBag
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SaasAdminPage() {
  const { t, language } = useLanguage();
  
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [tenants, setTenants] = useState([]);
  const [plans, setPlans] = useState([]);
  const [payments, setPayments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialogs
  const [planDialogOpen, setPlanDialogOpen] = useState(false);
  const [tenantDialogOpen, setTenantDialogOpen] = useState(false);
  const [extendDialogOpen, setExtendDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [editingTenant, setEditingTenant] = useState(null);
  const [selectedTenantForExtend, setSelectedTenantForExtend] = useState(null);
  
  // Forms
  const [planForm, setPlanForm] = useState({
    name: '', name_ar: '', description: '', description_ar: '',
    price_monthly: 0, price_6months: 0, price_yearly: 0,
    features: {}, limits: {}, is_active: true, is_popular: false, sort_order: 0
  });
  
  const [tenantForm, setTenantForm] = useState({
    name: '', email: '', phone: '', company_name: '', password: '',
    plan_id: '', subscription_type: 'monthly', business_type: 'retailer'
  });

  const [showPassword, setShowPassword] = useState(false);

  const [extendForm, setExtendForm] = useState({
    amount: 0, payment_method: 'manual', subscription_type: 'monthly', notes: '', transaction_id: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [statsRes, tenantsRes, plansRes, paymentsRes] = await Promise.all([
        axios.get(`${API}/saas/stats`, { headers }),
        axios.get(`${API}/saas/tenants`, { headers }),
        axios.get(`${API}/saas/plans?include_inactive=true`, { headers }),
        axios.get(`${API}/saas/payments`, { headers })
      ]);
      
      setStats(statsRes.data);
      setTenants(tenantsRes.data);
      setPlans(plansRes.data);
      setPayments(paymentsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  // Plan Functions
  const openPlanDialog = (plan = null) => {
    if (plan) {
      setEditingPlan(plan);
      setPlanForm({
        name: plan.name, name_ar: plan.name_ar,
        description: plan.description, description_ar: plan.description_ar,
        price_monthly: plan.price_monthly, price_6months: plan.price_6months, price_yearly: plan.price_yearly,
        features: plan.features || {}, limits: plan.limits || {},
        is_active: plan.is_active, is_popular: plan.is_popular, sort_order: plan.sort_order
      });
    } else {
      setEditingPlan(null);
      setPlanForm({
        name: '', name_ar: '', description: '', description_ar: '',
        price_monthly: 0, price_6months: 0, price_yearly: 0,
        features: { pos: true, reports: true, ai_tips: false, multi_warehouse: false },
        limits: { max_products: 100, max_users: 3, max_sales_per_month: 500 },
        is_active: true, is_popular: false, sort_order: plans.length
      });
    }
    setPlanDialogOpen(true);
  };

  const savePlan = async () => {
    try {
      const token = localStorage.getItem('token');
      if (editingPlan) {
        await axios.put(`${API}/saas/plans/${editingPlan.id}`, planForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('تم تحديث الخطة بنجاح');
      } else {
        await axios.post(`${API}/saas/plans`, planForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('تم إنشاء الخطة بنجاح');
      }
      setPlanDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'حدث خطأ');
    }
  };

  const deletePlan = async (planId) => {
    if (!window.confirm('هل أنت متأكد من حذف هذه الخطة؟')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/saas/plans/${planId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('تم حذف الخطة');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'حدث خطأ');
    }
  };

  // Tenant Functions
  const openTenantDialog = (tenant = null) => {
    if (tenant) {
      setEditingTenant(tenant);
      setTenantForm({
        name: tenant.name, email: tenant.email, phone: tenant.phone,
        company_name: tenant.company_name, password: '',
        plan_id: tenant.plan_id, subscription_type: tenant.subscription_type
      });
    } else {
      setEditingTenant(null);
      setTenantForm({
        name: '', email: '', phone: '', company_name: '', password: '',
        plan_id: plans[0]?.id || '', subscription_type: 'monthly'
      });
    }
    setTenantDialogOpen(true);
  };

  const saveTenant = async () => {
    try {
      const token = localStorage.getItem('token');
      if (editingTenant) {
        const updateData = { ...tenantForm };
        delete updateData.password;
        await axios.put(`${API}/saas/tenants/${editingTenant.id}`, updateData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('تم تحديث المشترك');
      } else {
        await axios.post(`${API}/saas/tenants`, tenantForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('تم إنشاء المشترك');
      }
      setTenantDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'حدث خطأ');
    }
  };

  const toggleTenantStatus = async (tenantId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API}/saas/tenants/${tenantId}/toggle-status`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(res.data.is_active ? 'تم تفعيل المشترك' : 'تم تعطيل المشترك');
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const deleteTenant = async (tenantId) => {
    if (!window.confirm('هل أنت متأكد؟ سيتم حذف جميع بيانات هذا المشترك نهائياً!')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/saas/tenants/${tenantId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('تم حذف المشترك');
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const openExtendDialog = (tenant) => {
    setSelectedTenantForExtend(tenant);
    const plan = plans.find(p => p.id === tenant.plan_id);
    setExtendForm({
      amount: plan?.price_monthly || 0,
      payment_method: 'manual',
      subscription_type: 'monthly',
      notes: '',
      transaction_id: ''
    });
    setExtendDialogOpen(true);
  };

  const extendSubscription = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/saas/tenants/${selectedTenantForExtend.id}/extend-subscription`, {
        tenant_id: selectedTenantForExtend.id,
        ...extendForm
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('تم تمديد الاشتراك بنجاح');
      setExtendDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const isExpiringSoon = (endDate) => {
    const end = new Date(endDate);
    const now = new Date();
    const diff = (end - now) / (1000 * 60 * 60 * 24);
    return diff <= 7 && diff > 0;
  };

  const isExpired = (endDate) => {
    return new Date(endDate) < new Date();
  };

  const filteredTenants = tenants.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.company_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="spinner" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="saas-admin-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Building className="h-8 w-8 text-primary" />
              لوحة تحكم NT Commerce
            </h1>
            <p className="text-muted-foreground mt-1">إدارة المشتركين والخطط والاشتراكات</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">إجمالي المشتركين</p>
                  <p className="text-2xl font-bold">{stats.total_tenants}</p>
                </div>
                <Users className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">نشط</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active_tenants}</p>
                </div>
                <Check className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">تجريبي</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.trial_tenants}</p>
                </div>
                <Clock className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">ينتهي قريباً</p>
                  <p className="text-2xl font-bold text-amber-600">{stats.expiring_soon}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">إيراد الشهر</p>
                  <p className="text-2xl font-bold">{stats.monthly_revenue?.toLocaleString()}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">إجمالي الإيراد</p>
                  <p className="text-2xl font-bold">{stats.total_revenue?.toLocaleString()}</p>
                </div>
                <DollarSign className="h-8 w-8 text-primary" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="tenants" className="space-y-6">
          <TabsList>
            <TabsTrigger value="tenants" className="gap-2">
              <Users className="h-4 w-4" />
              المشتركين
            </TabsTrigger>
            <TabsTrigger value="plans" className="gap-2">
              <Package className="h-4 w-4" />
              الخطط
            </TabsTrigger>
            <TabsTrigger value="payments" className="gap-2">
              <CreditCard className="h-4 w-4" />
              المدفوعات
            </TabsTrigger>
            <TabsTrigger value="finance" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              التقارير المالية
            </TabsTrigger>
          </TabsList>

          {/* Tenants Tab */}
          <TabsContent value="tenants" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="relative w-64">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="بحث..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pr-9"
                />
              </div>
              <Button onClick={() => openTenantDialog()}>
                <Plus className="h-4 w-4 me-2" />
                إضافة مشترك
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>المشترك</TableHead>
                      <TableHead>التصنيف</TableHead>
                      <TableHead>الخطة</TableHead>
                      <TableHead className="text-center">الإحصائيات</TableHead>
                      <TableHead className="text-center">الحالة</TableHead>
                      <TableHead className="text-center">انتهاء الاشتراك</TableHead>
                      <TableHead className="text-center">الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTenants.map(tenant => (
                      <TableRow key={tenant.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{tenant.name}</p>
                            <p className="text-sm text-muted-foreground">{tenant.email}</p>
                            {tenant.company_name && (
                              <p className="text-xs text-muted-foreground">{tenant.company_name}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={
                            tenant.business_type === 'wholesaler' ? 'bg-green-50 text-green-700 border-green-200' :
                            tenant.business_type === 'distributor' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                            'bg-blue-50 text-blue-700 border-blue-200'
                          }>
                            {tenant.business_type === 'wholesaler' ? (
                              <><ShoppingBag className="h-3 w-3 me-1" />تاجر جملة</>
                            ) : tenant.business_type === 'distributor' ? (
                              <><Truck className="h-3 w-3 me-1" />موزع</>
                            ) : (
                              <><Store className="h-3 w-3 me-1" />تاجر تجزئة</>
                            )}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{tenant.plan_name}</Badge>
                          {tenant.is_trial && (
                            <Badge variant="secondary" className="mr-1">تجريبي</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-3 text-sm">
                            <span title="المنتجات">📦 {tenant.stats?.products || 0}</span>
                            <span title="المستخدمين">👥 {tenant.stats?.users || 0}</span>
                            <span title="المبيعات">🛒 {tenant.stats?.sales || 0}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          {tenant.is_active ? (
                            <Badge className="bg-green-100 text-green-700">نشط</Badge>
                          ) : (
                            <Badge variant="destructive">معطل</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <div className={`text-sm ${
                            isExpired(tenant.subscription_ends_at) ? 'text-red-600' :
                            isExpiringSoon(tenant.subscription_ends_at) ? 'text-amber-600' : ''
                          }`}>
                            {new Date(tenant.subscription_ends_at).toLocaleDateString('ar-SA')}
                            {isExpired(tenant.subscription_ends_at) && (
                              <Badge variant="destructive" className="mr-1 text-xs">منتهي</Badge>
                            )}
                            {isExpiringSoon(tenant.subscription_ends_at) && (
                              <Badge variant="outline" className="mr-1 text-xs text-amber-600">قريباً</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Button variant="ghost" size="sm" onClick={() => openExtendDialog(tenant)} title="تمديد">
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => openTenantDialog(tenant)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => toggleTenantStatus(tenant.id)}>
                              {tenant.is_active ? <Ban className="h-4 w-4 text-amber-500" /> : <Check className="h-4 w-4 text-green-500" />}
                            </Button>
                            <Button variant="ghost" size="sm" className="text-destructive" onClick={() => deleteTenant(tenant.id)}>
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
          </TabsContent>

          {/* Plans Tab */}
          <TabsContent value="plans" className="space-y-4">
            <div className="flex justify-end">
              <Button onClick={() => openPlanDialog()}>
                <Plus className="h-4 w-4 me-2" />
                إضافة خطة
              </Button>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {plans.map(plan => (
                <Card key={plan.id} className={!plan.is_active ? 'opacity-60' : ''}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        {plan.name_ar}
                        {plan.is_popular && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />}
                      </CardTitle>
                      <Badge variant={plan.is_active ? 'default' : 'secondary'}>
                        {plan.is_active ? 'نشط' : 'معطل'}
                      </Badge>
                    </div>
                    <CardDescription>{plan.description_ar}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span>شهري:</span>
                        <span className="font-semibold">{plan.price_monthly.toLocaleString()} دج</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>6 أشهر:</span>
                        <span className="font-semibold">{plan.price_6months.toLocaleString()} دج</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>سنوي:</span>
                        <span className="font-semibold">{plan.price_yearly.toLocaleString()} دج</span>
                      </div>
                      <div className="border-t pt-3 mt-3">
                        <p className="text-xs text-muted-foreground mb-2">الحدود:</p>
                        <div className="flex flex-wrap gap-2">
                          {plan.limits?.max_products && (
                            <Badge variant="outline" className="text-xs">{plan.limits.max_products} منتج</Badge>
                          )}
                          {plan.limits?.max_users && (
                            <Badge variant="outline" className="text-xs">{plan.limits.max_users} مستخدم</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2 mt-4">
                      <Button variant="outline" size="sm" className="flex-1" onClick={() => openPlanDialog(plan)}>
                        <Edit className="h-4 w-4 me-1" />
                        تعديل
                      </Button>
                      <Button variant="outline" size="sm" className="text-destructive" onClick={() => deletePlan(plan.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Payments Tab */}
          <TabsContent value="payments">
            <Card>
              <CardHeader>
                <CardTitle>سجل المدفوعات</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>المشترك</TableHead>
                      <TableHead>المبلغ</TableHead>
                      <TableHead>نوع الاشتراك</TableHead>
                      <TableHead>طريقة الدفع</TableHead>
                      <TableHead>الفترة</TableHead>
                      <TableHead>التاريخ</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payments.map(payment => (
                      <TableRow key={payment.id}>
                        <TableCell className="font-medium">{payment.tenant_name}</TableCell>
                        <TableCell>{payment.amount.toLocaleString()} دج</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {payment.subscription_type === 'monthly' ? 'شهري' :
                             payment.subscription_type === '6months' ? '6 أشهر' : 'سنوي'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {payment.payment_method === 'manual' ? 'يدوي' :
                           payment.payment_method === 'stripe' ? 'Stripe' : payment.payment_method}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(payment.period_start).toLocaleDateString('ar-SA')} - {new Date(payment.period_end).toLocaleDateString('ar-SA')}
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(payment.created_at).toLocaleDateString('ar-SA')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Plan Dialog */}
        <Dialog open={planDialogOpen} onOpenChange={setPlanDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingPlan ? 'تعديل الخطة' : 'إضافة خطة جديدة'}</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 py-4">
              <div className="space-y-2">
                <Label>الاسم (إنجليزي)</Label>
                <Input value={planForm.name} onChange={e => setPlanForm({...planForm, name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>الاسم (عربي)</Label>
                <Input value={planForm.name_ar} onChange={e => setPlanForm({...planForm, name_ar: e.target.value})} />
              </div>
              <div className="space-y-2 col-span-2">
                <Label>الوصف (عربي)</Label>
                <Textarea value={planForm.description_ar} onChange={e => setPlanForm({...planForm, description_ar: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>السعر الشهري (دج)</Label>
                <Input type="number" value={planForm.price_monthly} onChange={e => setPlanForm({...planForm, price_monthly: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-2">
                <Label>سعر 6 أشهر (دج)</Label>
                <Input type="number" value={planForm.price_6months} onChange={e => setPlanForm({...planForm, price_6months: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-2">
                <Label>السعر السنوي (دج)</Label>
                <Input type="number" value={planForm.price_yearly} onChange={e => setPlanForm({...planForm, price_yearly: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-2">
                <Label>ترتيب العرض</Label>
                <Input type="number" value={planForm.sort_order} onChange={e => setPlanForm({...planForm, sort_order: parseInt(e.target.value) || 0})} />
              </div>
              <div className="space-y-2">
                <Label>حد المنتجات</Label>
                <Input type="number" value={planForm.limits?.max_products || 0} onChange={e => setPlanForm({...planForm, limits: {...planForm.limits, max_products: parseInt(e.target.value) || 0}})} />
              </div>
              <div className="space-y-2">
                <Label>حد المستخدمين</Label>
                <Input type="number" value={planForm.limits?.max_users || 0} onChange={e => setPlanForm({...planForm, limits: {...planForm.limits, max_users: parseInt(e.target.value) || 0}})} />
              </div>
              <div className="flex items-center gap-4 col-span-2">
                <div className="flex items-center gap-2">
                  <Switch checked={planForm.is_active} onCheckedChange={v => setPlanForm({...planForm, is_active: v})} />
                  <Label>نشط</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={planForm.is_popular} onCheckedChange={v => setPlanForm({...planForm, is_popular: v})} />
                  <Label>الأكثر شعبية</Label>
                </div>
              </div>
              <div className="col-span-2">
                <Label className="mb-2 block">الميزات</Label>
                <div className="grid grid-cols-2 gap-2">
                  {['pos', 'reports', 'ai_tips', 'multi_warehouse', 'smart_reports', 'employee_alerts'].map(f => (
                    <div key={f} className="flex items-center gap-2">
                      <Switch 
                        checked={planForm.features?.[f] || false} 
                        onCheckedChange={v => setPlanForm({...planForm, features: {...planForm.features, [f]: v}})} 
                      />
                      <Label className="text-sm">
                        {f === 'pos' ? 'نقطة البيع' :
                         f === 'reports' ? 'التقارير' :
                         f === 'ai_tips' ? 'نصائح AI' :
                         f === 'multi_warehouse' ? 'تعدد المخازن' :
                         f === 'smart_reports' ? 'تقارير ذكية' :
                         f === 'employee_alerts' ? 'تنبيهات الموظفين' : f}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPlanDialogOpen(false)}>إلغاء</Button>
              <Button onClick={savePlan}>حفظ</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Tenant Dialog */}
        <Dialog open={tenantDialogOpen} onOpenChange={setTenantDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingTenant ? 'تعديل المشترك' : 'إضافة مشترك جديد'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>الاسم</Label>
                <Input value={tenantForm.name} onChange={e => setTenantForm({...tenantForm, name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>البريد الإلكتروني</Label>
                <Input type="email" value={tenantForm.email} onChange={e => setTenantForm({...tenantForm, email: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>الهاتف</Label>
                <Input value={tenantForm.phone} onChange={e => setTenantForm({...tenantForm, phone: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>اسم الشركة</Label>
                <Input value={tenantForm.company_name} onChange={e => setTenantForm({...tenantForm, company_name: e.target.value})} />
              </div>
              {!editingTenant && (
                <div className="space-y-2">
                  <Label>كلمة المرور</Label>
                  <div className="relative">
                    <Input 
                      type={showPassword ? 'text' : 'password'} 
                      value={tenantForm.password} 
                      onChange={e => setTenantForm({...tenantForm, password: e.target.value})}
                      className="pe-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute left-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              )}
              <div className="space-y-2">
                <Label>تصنيف المشترك</Label>
                <Select value={tenantForm.business_type} onValueChange={v => setTenantForm({...tenantForm, business_type: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="اختر التصنيف" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="retailer">
                      <div className="flex items-center gap-2">
                        <Store className="h-4 w-4 text-blue-500" />
                        <span>تاجر تجزئة</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="wholesaler">
                      <div className="flex items-center gap-2">
                        <ShoppingBag className="h-4 w-4 text-green-500" />
                        <span>تاجر جملة</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="distributor">
                      <div className="flex items-center gap-2">
                        <Truck className="h-4 w-4 text-orange-500" />
                        <span>موزع</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>الخطة</Label>
                <Select value={tenantForm.plan_id} onValueChange={v => setTenantForm({...tenantForm, plan_id: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {plans.map(p => (
                      <SelectItem key={p.id} value={p.id}>{p.name_ar}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>نوع الاشتراك</Label>
                <Select value={tenantForm.subscription_type} onValueChange={v => setTenantForm({...tenantForm, subscription_type: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="monthly">شهري</SelectItem>
                    <SelectItem value="6months">6 أشهر</SelectItem>
                    <SelectItem value="yearly">سنوي</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setTenantDialogOpen(false)}>إلغاء</Button>
              <Button onClick={saveTenant}>حفظ</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Extend Subscription Dialog */}
        <Dialog open={extendDialogOpen} onOpenChange={setExtendDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>تمديد الاشتراك</DialogTitle>
              <DialogDescription>{selectedTenantForExtend?.name}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>نوع الاشتراك</Label>
                <Select value={extendForm.subscription_type} onValueChange={v => {
                  const plan = plans.find(p => p.id === selectedTenantForExtend?.plan_id);
                  const price = v === 'monthly' ? plan?.price_monthly : v === '6months' ? plan?.price_6months : plan?.price_yearly;
                  setExtendForm({...extendForm, subscription_type: v, amount: price || 0});
                }}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="monthly">شهري</SelectItem>
                    <SelectItem value="6months">6 أشهر</SelectItem>
                    <SelectItem value="yearly">سنوي</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>المبلغ (دج)</Label>
                <Input type="number" value={extendForm.amount} onChange={e => setExtendForm({...extendForm, amount: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-2">
                <Label>طريقة الدفع</Label>
                <Select value={extendForm.payment_method} onValueChange={v => setExtendForm({...extendForm, payment_method: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="manual">يدوي (نقدي/تحويل)</SelectItem>
                    <SelectItem value="stripe">Stripe</SelectItem>
                    <SelectItem value="paypal">PayPal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>رقم المعاملة (اختياري)</Label>
                <Input value={extendForm.transaction_id} onChange={e => setExtendForm({...extendForm, transaction_id: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>ملاحظات</Label>
                <Textarea value={extendForm.notes} onChange={e => setExtendForm({...extendForm, notes: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setExtendDialogOpen(false)}>إلغاء</Button>
              <Button onClick={extendSubscription}>تمديد الاشتراك</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
