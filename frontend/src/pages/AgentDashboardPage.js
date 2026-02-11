import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import { 
  Truck, Users, DollarSign, TrendingUp, Plus, LogOut, 
  Wallet, CreditCard, Clock, CheckCircle, AlertTriangle,
  Building, Phone, Mail, Calendar, FileText, Eye
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AgentDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [plans, setPlans] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [transactions, setTransactions] = useState([]);
  
  const [addTenantDialogOpen, setAddTenantDialogOpen] = useState(false);
  const [viewTransactionsDialogOpen, setViewTransactionsDialogOpen] = useState(false);
  
  const [tenantForm, setTenantForm] = useState({
    name: '', email: '', password: '', phone: '', company_name: '',
    plan_id: '', subscription_type: 'monthly', business_type: 'retailer', notes: ''
  });

  const agentData = JSON.parse(localStorage.getItem('agentData') || '{}');

  useEffect(() => {
    const token = localStorage.getItem('agentToken');
    if (!token) {
      navigate('/agent-login');
      return;
    }
    fetchDashboard();
    fetchPlans();
  }, [navigate]);

  const getHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem('agentToken')}`
  });

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/agent/dashboard`, { headers: getHeaders() });
      setDashboard(response.data);
      setTenants(response.data.tenants || []);
      setTransactions(response.data.recent_transactions || []);
    } catch (error) {
      if (error.response?.status === 401) {
        localStorage.removeItem('agentToken');
        localStorage.removeItem('agentData');
        navigate('/agent-login');
      }
      toast.error('خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/saas/plans`, { headers: getHeaders() });
      setPlans(response.data.filter(p => p.is_active));
    } catch (error) {
      console.error('Error fetching plans:', error);
    }
  };

  const fetchAllTenants = async () => {
    try {
      const response = await axios.get(`${API}/agent/tenants`, { headers: getHeaders() });
      setTenants(response.data);
    } catch (error) {
      toast.error('خطأ في تحميل المشتركين');
    }
  };

  const fetchAllTransactions = async () => {
    try {
      const response = await axios.get(`${API}/agent/transactions`, { headers: getHeaders() });
      setTransactions(response.data);
      setViewTransactionsDialogOpen(true);
    } catch (error) {
      toast.error('خطأ في تحميل المعاملات');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('agentToken');
    localStorage.removeItem('agentData');
    navigate('/agent-login');
    toast.success('تم تسجيل الخروج');
  };

  const openAddTenant = () => {
    setTenantForm({
      name: '', email: '', password: '', phone: '', company_name: '',
      plan_id: plans[0]?.id || '', subscription_type: 'monthly', business_type: 'retailer', notes: ''
    });
    setAddTenantDialogOpen(true);
  };

  const saveTenant = async () => {
    try {
      await axios.post(`${API}/agent/tenants`, tenantForm, { headers: getHeaders() });
      toast.success('تم إضافة المشترك بنجاح');
      setAddTenantDialogOpen(false);
      fetchDashboard();
      fetchAllTenants();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'حدث خطأ');
    }
  };

  const getPlanPrice = (planId, subType) => {
    const plan = plans.find(p => p.id === planId);
    if (!plan) return 0;
    if (subType === 'monthly') return plan.price_monthly;
    if (subType === '6months') return plan.price_6months;
    return plan.price_yearly;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  const agent = dashboard?.agent || agentData;
  const stats = dashboard?.stats || {};

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary flex items-center justify-center">
              <Truck className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg">NT Commerce</h1>
              <p className="text-xs text-muted-foreground">بوابة الوكلاء</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-left">
              <p className="font-medium text-sm">{agent.name}</p>
              <p className="text-xs text-muted-foreground">{agent.email}</p>
            </div>
            <Button variant="outline" size="sm" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" />
              خروج
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Welcome & Balance Card */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 bg-gradient-to-br from-primary to-blue-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-blue-100 mb-1">مرحباً بك</p>
                  <h2 className="text-2xl font-bold mb-4">{agent.name}</h2>
                  <p className="text-blue-100 text-sm">{agent.company_name || 'وكيل معتمد'}</p>
                </div>
                <div className="h-16 w-16 rounded-full bg-white/20 flex items-center justify-center">
                  <Truck className="h-8 w-8" />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/20">
                <div>
                  <p className="text-blue-100 text-sm">نسبة العمولة</p>
                  <p className="text-xl font-bold">{agent.commission_percent}%</p>
                </div>
                <div>
                  <p className="text-blue-100 text-sm">عمولة ثابتة</p>
                  <p className="text-xl font-bold">{agent.commission_fixed?.toLocaleString()} دج</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Wallet className="h-5 w-5 text-primary" />
                الرصيد المالي
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center p-4 rounded-lg bg-muted">
                  <p className="text-sm text-muted-foreground mb-1">الرصيد الحالي</p>
                  <p className={`text-3xl font-bold ${agent.current_balance < 0 ? 'text-red-500' : 'text-green-500'}`}>
                    {agent.current_balance?.toLocaleString()} دج
                  </p>
                  {agent.current_balance < 0 && (
                    <Badge variant="destructive" className="mt-2">
                      <AlertTriangle className="h-3 w-3 me-1" />
                      دين
                    </Badge>
                  )}
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">حد الدين</span>
                  <span className="font-medium">{agent.credit_limit?.toLocaleString()} دج</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">إجمالي العمولات</span>
                  <span className="font-medium text-green-600">{agent.total_earnings?.toLocaleString()} دج</span>
                </div>
                <Button variant="outline" className="w-full gap-2" onClick={fetchAllTransactions}>
                  <FileText className="h-4 w-4" />
                  عرض كل المعاملات
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total_tenants || 0}</p>
                <p className="text-sm text-muted-foreground">إجمالي المشتركين</p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.active_tenants || 0}</p>
                <p className="text-sm text-muted-foreground">نشط</p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-yellow-100 flex items-center justify-center">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.trial_tenants || 0}</p>
                <p className="text-sm text-muted-foreground">تجريبي</p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total_subscription_value?.toLocaleString() || 0}</p>
                <p className="text-sm text-muted-foreground">قيمة الاشتراكات (دج)</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tenants Section */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>المشتركين</CardTitle>
              <CardDescription>قائمة المشتركين التابعين لك</CardDescription>
            </div>
            <Button onClick={openAddTenant} className="gap-2">
              <Plus className="h-4 w-4" />
              إضافة مشترك
            </Button>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>المشترك</TableHead>
                  <TableHead>البريد / الهاتف</TableHead>
                  <TableHead>الخطة</TableHead>
                  <TableHead>نوع الاشتراك</TableHead>
                  <TableHead>انتهاء الاشتراك</TableHead>
                  <TableHead>الحالة</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tenants.map(tenant => (
                  <TableRow key={tenant.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <Building className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{tenant.name}</p>
                          <p className="text-xs text-muted-foreground">{tenant.company_name}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <p className="flex items-center gap-1"><Mail className="h-3 w-3" /> {tenant.email}</p>
                        <p className="flex items-center gap-1 text-muted-foreground"><Phone className="h-3 w-3" /> {tenant.phone}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{tenant.plan_name || 'غير محدد'}</Badge>
                    </TableCell>
                    <TableCell>
                      {tenant.subscription_type === 'monthly' ? 'شهري' : tenant.subscription_type === '6months' ? '6 أشهر' : 'سنوي'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3" />
                        {tenant.subscription_ends_at ? new Date(tenant.subscription_ends_at).toLocaleDateString('ar-DZ') : '-'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={tenant.is_active ? "default" : "secondary"}>
                        {tenant.is_active ? 'نشط' : 'معطل'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
                {tenants.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      لا يوجد مشتركين حالياً - أضف أول مشترك!
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>آخر المعاملات</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>التاريخ</TableHead>
                  <TableHead>النوع</TableHead>
                  <TableHead>الوصف</TableHead>
                  <TableHead>المبلغ</TableHead>
                  <TableHead>الرصيد بعد</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.slice(0, 5).map(tx => (
                  <TableRow key={tx.id}>
                    <TableCell className="text-sm">
                      {new Date(tx.created_at).toLocaleDateString('ar-DZ')}
                    </TableCell>
                    <TableCell>
                      <Badge variant={tx.transaction_type === 'payment' ? 'default' : tx.transaction_type === 'commission' ? 'secondary' : 'outline'}>
                        {tx.transaction_type === 'payment' ? 'دفعة' : tx.transaction_type === 'commission' ? 'عمولة' : 'بيع اشتراك'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{tx.description}</TableCell>
                    <TableCell className={`font-medium ${tx.transaction_type === 'subscription_sale' ? 'text-red-500' : 'text-green-500'}`}>
                      {tx.transaction_type === 'subscription_sale' ? '-' : '+'}{tx.amount?.toLocaleString()} دج
                    </TableCell>
                    <TableCell className="font-medium">{tx.balance_after?.toLocaleString()} دج</TableCell>
                  </TableRow>
                ))}
                {transactions.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      لا توجد معاملات
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>

      {/* Add Tenant Dialog */}
      <Dialog open={addTenantDialogOpen} onOpenChange={setAddTenantDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>إضافة مشترك جديد</DialogTitle>
            <DialogDescription>سيتم خصم قيمة الاشتراك من رصيدك</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3 py-2">
            <div className="space-y-1">
              <Label className="text-xs">الاسم *</Label>
              <Input className="h-8 text-sm" value={tenantForm.name} onChange={e => setTenantForm({...tenantForm, name: e.target.value})} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">البريد الإلكتروني *</Label>
              <Input className="h-8 text-sm" type="email" value={tenantForm.email} onChange={e => setTenantForm({...tenantForm, email: e.target.value})} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">الهاتف</Label>
              <Input className="h-8 text-sm" value={tenantForm.phone} onChange={e => setTenantForm({...tenantForm, phone: e.target.value})} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">اسم الشركة</Label>
              <Input className="h-8 text-sm" value={tenantForm.company_name} onChange={e => setTenantForm({...tenantForm, company_name: e.target.value})} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">كلمة المرور *</Label>
              <Input className="h-8 text-sm" type="password" value={tenantForm.password} onChange={e => setTenantForm({...tenantForm, password: e.target.value})} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">نوع النشاط</Label>
              <Select value={tenantForm.business_type} onValueChange={v => setTenantForm({...tenantForm, business_type: v})}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="retailer">تاجر تجزئة</SelectItem>
                  <SelectItem value="wholesaler">تاجر جملة</SelectItem>
                  <SelectItem value="distributor">موزع</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">الخطة *</Label>
              <Select value={tenantForm.plan_id} onValueChange={v => setTenantForm({...tenantForm, plan_id: v})}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder="اختر خطة" />
                </SelectTrigger>
                <SelectContent>
                  {plans.map(plan => (
                    <SelectItem key={plan.id} value={plan.id}>{plan.name_ar}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">نوع الاشتراك</Label>
              <Select value={tenantForm.subscription_type} onValueChange={v => setTenantForm({...tenantForm, subscription_type: v})}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="monthly">شهري</SelectItem>
                  <SelectItem value="6months">6 أشهر</SelectItem>
                  <SelectItem value="yearly">سنوي</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2 space-y-1">
              <Label className="text-xs">ملاحظات</Label>
              <Textarea className="text-sm" rows={2} value={tenantForm.notes} onChange={e => setTenantForm({...tenantForm, notes: e.target.value})} />
            </div>
          </div>
          
          {/* Price Summary */}
          <div className="bg-muted p-3 rounded-lg text-sm">
            <div className="flex justify-between mb-2">
              <span>قيمة الاشتراك:</span>
              <span className="font-bold">{getPlanPrice(tenantForm.plan_id, tenantForm.subscription_type).toLocaleString()} دج</span>
            </div>
            <div className="flex justify-between text-muted-foreground">
              <span>رصيدك الحالي:</span>
              <span>{agent.current_balance?.toLocaleString()} دج</span>
            </div>
          </div>
          
          <DialogFooter className="pt-2">
            <Button variant="outline" size="sm" onClick={() => setAddTenantDialogOpen(false)}>إلغاء</Button>
            <Button size="sm" onClick={saveTenant}>إضافة المشترك</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* All Transactions Dialog */}
      <Dialog open={viewTransactionsDialogOpen} onOpenChange={setViewTransactionsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>جميع المعاملات</DialogTitle>
            <DialogDescription>
              الرصيد الحالي: <span className={`font-bold ${agent.current_balance < 0 ? 'text-red-500' : 'text-green-500'}`}>
                {agent.current_balance?.toLocaleString()} دج
              </span>
            </DialogDescription>
          </DialogHeader>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>التاريخ</TableHead>
                <TableHead>النوع</TableHead>
                <TableHead>الوصف</TableHead>
                <TableHead>المبلغ</TableHead>
                <TableHead>الرصيد بعد</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map(tx => (
                <TableRow key={tx.id}>
                  <TableCell className="text-sm">{new Date(tx.created_at).toLocaleDateString('ar-DZ')}</TableCell>
                  <TableCell>
                    <Badge variant={tx.transaction_type === 'payment' ? 'default' : tx.transaction_type === 'commission' ? 'secondary' : 'outline'}>
                      {tx.transaction_type === 'payment' ? 'دفعة' : tx.transaction_type === 'commission' ? 'عمولة' : 'بيع اشتراك'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{tx.description}</TableCell>
                  <TableCell className={`font-medium ${tx.transaction_type === 'subscription_sale' ? 'text-red-500' : 'text-green-500'}`}>
                    {tx.transaction_type === 'subscription_sale' ? '-' : '+'}{tx.amount?.toLocaleString()} دج
                  </TableCell>
                  <TableCell className="font-medium">{tx.balance_after?.toLocaleString()} دج</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </DialogContent>
      </Dialog>
    </div>
  );
}
