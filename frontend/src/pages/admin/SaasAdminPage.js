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
  Star, Eye, EyeOff, Ban, RefreshCw, Calendar, Store, Truck, ShoppingBag,
  Banknote, Wallet, PiggyBank, Receipt, Calculator, FileText, ArrowUpRight, ArrowDownRight,
  Send, Database
} from 'lucide-react';
import { DatabaseManager } from '../../components/DatabaseManager';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Finance Reports Component
const FinanceReportsSection = ({ tenants, payments }) => {
  const [financeData, setFinanceData] = useState({
    total_revenue: 0,
    monthly_revenue: 0,
    yearly_revenue: 0,
    pending_payments: 0,
    net_profit: 0,
    expenses: 0,
    payment_methods: {
      cash: { count: 0, amount: 0 },
      ccp: { count: 0, amount: 0 },
      bank_transfer: { count: 0, amount: 0 },
      stripe: { count: 0, amount: 0 }
    },
    monthly_breakdown: []
  });
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('all');

  useEffect(() => {
    fetchFinanceData();
  }, [dateRange]);

  const fetchFinanceData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/saas/finance-reports?range=${dateRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFinanceData(response.data);
    } catch (error) {
      console.error('Error fetching finance data:', error);
      // Calculate from local data
      calculateFromLocalData();
    } finally {
      setLoading(false);
    }
  };

  const calculateFromLocalData = () => {
    const now = new Date();
    const thisMonth = now.getMonth();
    const thisYear = now.getFullYear();

    let total = 0, monthly = 0, yearly = 0;
    const methods = {
      cash: { count: 0, amount: 0 },
      ccp: { count: 0, amount: 0 },
      bank_transfer: { count: 0, amount: 0 },
      stripe: { count: 0, amount: 0 },
      manual: { count: 0, amount: 0 }
    };

    payments.forEach(p => {
      total += p.amount;
      const pDate = new Date(p.created_at);
      if (pDate.getMonth() === thisMonth && pDate.getFullYear() === thisYear) {
        monthly += p.amount;
      }
      if (pDate.getFullYear() === thisYear) {
        yearly += p.amount;
      }
      const method = p.payment_method || 'manual';
      if (methods[method]) {
        methods[method].count++;
        methods[method].amount += p.amount;
      }
    });

    // Estimate expenses as 30% of revenue
    const expenses = total * 0.3;
    const net_profit = total - expenses;

    setFinanceData({
      total_revenue: total,
      monthly_revenue: monthly,
      yearly_revenue: yearly,
      pending_payments: 0,
      net_profit: net_profit,
      expenses: expenses,
      payment_methods: methods,
      monthly_breakdown: []
    });
  };

  return (
    <div className="space-y-6">
      {/* Date Range Filter */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Calculator className="h-5 w-5 text-primary" />
          التقارير المالية الشاملة
        </h2>
        <Select value={dateRange} onValueChange={setDateRange}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">كل الوقت</SelectItem>
            <SelectItem value="today">اليوم</SelectItem>
            <SelectItem value="week">هذا الأسبوع</SelectItem>
            <SelectItem value="month">هذا الشهر</SelectItem>
            <SelectItem value="year">هذه السنة</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">إجمالي الإيرادات</p>
                <p className="text-xl font-bold">{financeData.total_revenue?.toLocaleString()} دج</p>
              </div>
              <DollarSign className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">إيراد الشهر</p>
                <p className="text-xl font-bold">{financeData.monthly_revenue?.toLocaleString()} دج</p>
              </div>
              <TrendingUp className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">إيراد السنة</p>
                <p className="text-xl font-bold">{financeData.yearly_revenue?.toLocaleString()} دج</p>
              </div>
              <Calendar className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">المصاريف</p>
                <p className="text-xl font-bold">{financeData.expenses?.toLocaleString()} دج</p>
              </div>
              <ArrowDownRight className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">صافي الربح</p>
                <p className="text-xl font-bold">{financeData.net_profit?.toLocaleString()} دج</p>
              </div>
              <PiggyBank className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">مدفوعات معلقة</p>
                <p className="text-xl font-bold">{financeData.pending_payments?.toLocaleString()} دج</p>
              </div>
              <Clock className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Payment Methods Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            طرق الدفع
          </CardTitle>
          <CardDescription>توزيع المدفوعات حسب طريقة الدفع</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border bg-muted/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900">
                  <Banknote className="h-5 w-5 text-green-600" />
                </div>
                <span className="font-medium">نقدي (CCP)</span>
              </div>
              <p className="text-2xl font-bold">{financeData.payment_methods?.ccp?.amount?.toLocaleString() || 0} دج</p>
              <p className="text-sm text-muted-foreground">{financeData.payment_methods?.ccp?.count || 0} عملية</p>
            </div>
            <div className="p-4 rounded-xl border bg-muted/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Building className="h-5 w-5 text-blue-600" />
                </div>
                <span className="font-medium">تحويل بنكي</span>
              </div>
              <p className="text-2xl font-bold">{financeData.payment_methods?.bank_transfer?.amount?.toLocaleString() || 0} دج</p>
              <p className="text-sm text-muted-foreground">{financeData.payment_methods?.bank_transfer?.count || 0} عملية</p>
            </div>
            <div className="p-4 rounded-xl border bg-muted/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                  <CreditCard className="h-5 w-5 text-purple-600" />
                </div>
                <span className="font-medium">Stripe</span>
              </div>
              <p className="text-2xl font-bold">{financeData.payment_methods?.stripe?.amount?.toLocaleString() || 0} دج</p>
              <p className="text-sm text-muted-foreground">{financeData.payment_methods?.stripe?.count || 0} عملية</p>
            </div>
            <div className="p-4 rounded-xl border bg-muted/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900">
                  <Wallet className="h-5 w-5 text-amber-600" />
                </div>
                <span className="font-medium">نقدي / يدوي</span>
              </div>
              <p className="text-2xl font-bold">{(financeData.payment_methods?.cash?.amount || 0) + (financeData.payment_methods?.manual?.amount || 0)} دج</p>
              <p className="text-sm text-muted-foreground">{(financeData.payment_methods?.cash?.count || 0) + (financeData.payment_methods?.manual?.count || 0)} عملية</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Profit Calculation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PiggyBank className="h-5 w-5" />
            حساب الأرباح الصافية
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-lg bg-green-50 dark:bg-green-950/30">
              <div className="flex items-center gap-3">
                <ArrowUpRight className="h-6 w-6 text-green-500" />
                <span className="font-medium">إجمالي الإيرادات</span>
              </div>
              <span className="text-xl font-bold text-green-600">+{financeData.total_revenue?.toLocaleString()} دج</span>
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-red-50 dark:bg-red-950/30">
              <div className="flex items-center gap-3">
                <ArrowDownRight className="h-6 w-6 text-red-500" />
                <span className="font-medium">إجمالي المصاريف (تقديري 30%)</span>
              </div>
              <span className="text-xl font-bold text-red-600">-{financeData.expenses?.toLocaleString()} دج</span>
            </div>
            <div className="border-t pt-4">
              <div className="flex items-center justify-between p-4 rounded-lg bg-primary/10">
                <div className="flex items-center gap-3">
                  <PiggyBank className="h-6 w-6 text-primary" />
                  <span className="font-bold text-lg">صافي الربح</span>
                </div>
                <span className="text-2xl font-bold text-primary">{financeData.net_profit?.toLocaleString()} دج</span>
              </div>
            </div>
            <p className="text-sm text-muted-foreground text-center">
              * المصاريف تقديرية، يمكنك إدخال المصاريف الفعلية للحصول على نتائج أدق
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Tenants Revenue Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            تفاصيل الإيرادات حسب المشترك
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>المشترك</TableHead>
                <TableHead>الخطة</TableHead>
                <TableHead>طريقة الدفع</TableHead>
                <TableHead>إجمالي المدفوعات</TableHead>
                <TableHead>آخر دفعة</TableHead>
                <TableHead>الحالة</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tenants.slice(0, 10).map(tenant => {
                const tenantPayments = payments.filter(p => p.tenant_id === tenant.id);
                const totalPaid = tenantPayments.reduce((sum, p) => sum + p.amount, 0);
                const lastPayment = tenantPayments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];
                
                return (
                  <TableRow key={tenant.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{tenant.company_name || tenant.name}</p>
                        <p className="text-sm text-muted-foreground">{tenant.email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{tenant.plan_name || 'غير محدد'}</Badge>
                    </TableCell>
                    <TableCell>
                      {lastPayment?.payment_method === 'ccp' && 'CCP'}
                      {lastPayment?.payment_method === 'bank_transfer' && 'تحويل بنكي'}
                      {lastPayment?.payment_method === 'stripe' && 'Stripe'}
                      {lastPayment?.payment_method === 'manual' && 'يدوي'}
                      {!lastPayment && '-'}
                    </TableCell>
                    <TableCell className="font-semibold">{totalPaid.toLocaleString()} دج</TableCell>
                    <TableCell className="text-sm">
                      {lastPayment ? new Date(lastPayment.created_at).toLocaleDateString('ar-SA') : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={tenant.status === 'active' ? 'default' : 'secondary'}>
                        {tenant.status === 'active' ? 'نشط' : tenant.status === 'trial' ? 'تجريبي' : 'معلق'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

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
    plan_id: '', subscription_type: 'monthly', business_type: 'retailer', role: 'admin'
  });

  const [showPassword, setShowPassword] = useState(false);

  const [extendForm, setExtendForm] = useState({
    amount: 0, payment_method: 'manual', subscription_type: 'monthly', notes: '', transaction_id: ''
  });

  // Agents State
  const [agents, setAgents] = useState([]);
  const [agentDialogOpen, setAgentDialogOpen] = useState(false);
  const [agentTransactionsDialogOpen, setAgentTransactionsDialogOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentTransactions, setAgentTransactions] = useState([]);
  const [addPaymentDialogOpen, setAddPaymentDialogOpen] = useState(false);
  
  const [agentForm, setAgentForm] = useState({
    name: '', email: '', password: '', phone: '', company_name: '', address: '',
    commission_percent: 10, commission_fixed: 0, credit_limit: 100000, notes: ''
  });
  
  const [paymentForm, setPaymentForm] = useState({
    amount: 0, transaction_type: 'payment', description: '', notes: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [statsRes, tenantsRes, plansRes, paymentsRes, agentsRes] = await Promise.all([
        axios.get(`${API}/saas/stats`, { headers }),
        axios.get(`${API}/saas/tenants`, { headers }),
        axios.get(`${API}/saas/plans?include_inactive=true`, { headers }),
        axios.get(`${API}/saas/payments`, { headers }),
        axios.get(`${API}/saas/agents`, { headers })
      ]);
      
      setStats(statsRes.data);
      setTenants(tenantsRes.data);
      setPlans(plansRes.data);
      setPayments(paymentsRes.data);
      setAgents(agentsRes.data);
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

  // Agent Functions
  const openAgentDialog = (agent = null) => {
    if (agent) {
      setEditingAgent(agent);
      setAgentForm({
        name: agent.name, email: agent.email, password: '', phone: agent.phone,
        company_name: agent.company_name || '', address: agent.address || '',
        commission_percent: agent.commission_percent || 10,
        commission_fixed: agent.commission_fixed || 0,
        credit_limit: agent.credit_limit || 100000,
        notes: agent.notes || ''
      });
    } else {
      setEditingAgent(null);
      setAgentForm({
        name: '', email: '', password: '', phone: '', company_name: '', address: '',
        commission_percent: 10, commission_fixed: 0, credit_limit: 100000, notes: ''
      });
    }
    setAgentDialogOpen(true);
  };

  const saveAgent = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      if (editingAgent) {
        const updateData = { ...agentForm };
        if (!updateData.password) delete updateData.password;
        await axios.put(`${API}/saas/agents/${editingAgent.id}`, updateData, { headers });
        toast.success('تم تحديث الوكيل بنجاح');
      } else {
        await axios.post(`${API}/saas/agents`, agentForm, { headers });
        toast.success('تم إنشاء الوكيل بنجاح');
      }
      setAgentDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'حدث خطأ');
    }
  };

  const deleteAgent = async (agentId) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا الوكيل؟')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/saas/agents/${agentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('تم حذف الوكيل');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'حدث خطأ');
    }
  };

  const openAgentTransactions = async (agent) => {
    setSelectedAgent(agent);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/saas/agents/${agent.id}/transactions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAgentTransactions(response.data);
      setAgentTransactionsDialogOpen(true);
    } catch (error) {
      toast.error('خطأ في تحميل المعاملات');
    }
  };

  const openAddPayment = (agent) => {
    setSelectedAgent(agent);
    setPaymentForm({ amount: 0, transaction_type: 'payment', description: 'دفعة نقدية', notes: '' });
    setAddPaymentDialogOpen(true);
  };

  const saveAgentPayment = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/saas/agents/${selectedAgent.id}/transactions`, paymentForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('تم تسجيل الدفعة بنجاح');
      setAddPaymentDialogOpen(false);
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
        plan_id: tenant.plan_id, subscription_type: tenant.subscription_type,
        business_type: tenant.business_type || 'retailer', role: tenant.role || 'admin'
      });
    } else {
      setEditingTenant(null);
      setTenantForm({
        name: '', email: '', phone: '', company_name: '', password: '',
        plan_id: plans[0]?.id || '', subscription_type: 'monthly',
        business_type: 'retailer', role: 'admin'
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
            <TabsTrigger value="agents" className="gap-2">
              <Truck className="h-4 w-4" />
              الوكلاء
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
            <TabsTrigger value="databases" className="gap-2">
              <Database className="h-4 w-4" />
              قواعد البيانات
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

          {/* Agents Tab */}
          <TabsContent value="agents" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-sm text-muted-foreground">
                  إجمالي الوكلاء: <span className="font-bold text-foreground">{agents.length}</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  إجمالي الدين: <span className="font-bold text-red-500">
                    {agents.reduce((sum, a) => sum + (a.current_balance < 0 ? Math.abs(a.current_balance) : 0), 0).toLocaleString()} دج
                  </span>
                </div>
              </div>
              <Button onClick={() => openAgentDialog()}>
                <Plus className="h-4 w-4 me-2" />
                إضافة وكيل
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الوكيل</TableHead>
                      <TableHead>البريد / الهاتف</TableHead>
                      <TableHead>المشتركين</TableHead>
                      <TableHead>العمولة</TableHead>
                      <TableHead>الرصيد</TableHead>
                      <TableHead>حد الدين</TableHead>
                      <TableHead>الحالة</TableHead>
                      <TableHead className="text-center">الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agents.map(agent => (
                      <TableRow key={agent.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                              <Truck className="h-4 w-4 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium">{agent.name}</p>
                              <p className="text-xs text-muted-foreground">{agent.company_name}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p>{agent.email}</p>
                            <p className="text-muted-foreground">{agent.phone}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{agent.tenants_count || 0}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p>{agent.commission_percent}%</p>
                            {agent.commission_fixed > 0 && (
                              <p className="text-muted-foreground">+ {agent.commission_fixed} دج</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className={`font-bold ${agent.current_balance < 0 ? 'text-red-500' : 'text-green-500'}`}>
                            {agent.current_balance?.toLocaleString()} دج
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-muted-foreground">{agent.credit_limit?.toLocaleString()} دج</span>
                        </TableCell>
                        <TableCell>
                          <Badge variant={agent.is_active ? "default" : "secondary"}>
                            {agent.is_active ? 'نشط' : 'معطل'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Button variant="ghost" size="sm" onClick={() => openAddPayment(agent)} title="إضافة دفعة">
                              <DollarSign className="h-4 w-4 text-green-500" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => openAgentTransactions(agent)} title="المعاملات">
                              <FileText className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => openAgentDialog(agent)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" className="text-destructive" onClick={() => deleteAgent(agent.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {agents.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                          لا يوجد وكلاء حالياً
                        </TableCell>
                      </TableRow>
                    )}
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

          {/* Finance Reports Tab */}
          <TabsContent value="finance" className="space-y-6">
            <FinanceReportsSection tenants={tenants} payments={payments} />
          </TabsContent>

          {/* Databases Tab */}
          <TabsContent value="databases" className="space-y-6">
            <DatabaseManager tenants={tenants} agents={agents} />
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

        {/* Tenant Dialog - Compact */}
        <Dialog open={tenantDialogOpen} onOpenChange={setTenantDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader className="pb-2">
              <DialogTitle className="text-lg">{editingTenant ? 'تعديل المشترك' : 'إضافة مشترك جديد'}</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-3 py-2">
              <div className="space-y-1">
                <Label className="text-xs">الاسم</Label>
                <Input className="h-8 text-sm" value={tenantForm.name} onChange={e => setTenantForm({...tenantForm, name: e.target.value})} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">البريد الإلكتروني</Label>
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
              {!editingTenant && (
                <div className="space-y-1 col-span-2">
                  <Label className="text-xs">كلمة المرور</Label>
                  <div className="relative">
                    <Input 
                      className="h-8 text-sm pe-8"
                      type={showPassword ? 'text' : 'password'} 
                      value={tenantForm.password} 
                      onChange={e => setTenantForm({...tenantForm, password: e.target.value})}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
              )}
              <div className="space-y-1">
                <Label className="text-xs">التصنيف</Label>
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
                <Label className="text-xs">الصلاحية</Label>
                <Select value={tenantForm.role} onValueChange={v => setTenantForm({...tenantForm, role: v})}>
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">مدير (صلاحيات كاملة)</SelectItem>
                    <SelectItem value="manager">مشرف (عمليات يومية)</SelectItem>
                    <SelectItem value="sales_supervisor">مشرف مبيعات</SelectItem>
                    <SelectItem value="seller">بائع</SelectItem>
                    <SelectItem value="inventory_manager">مدير مخزون</SelectItem>
                    <SelectItem value="accountant">محاسب</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">الخطة</Label>
                <Select value={tenantForm.plan_id} onValueChange={v => setTenantForm({...tenantForm, plan_id: v})}>
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {plans.map(p => (
                      <SelectItem key={p.id} value={p.id}>{p.name_ar}</SelectItem>
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
            </div>
            <DialogFooter className="pt-2">
              <Button variant="outline" size="sm" onClick={() => setTenantDialogOpen(false)}>إلغاء</Button>
              <Button size="sm" onClick={saveTenant}>حفظ</Button>
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

        {/* Agent Dialog */}
        <Dialog open={agentDialogOpen} onOpenChange={setAgentDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{editingAgent ? 'تعديل الوكيل' : 'إضافة وكيل جديد'}</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-3 py-2">
              <div className="space-y-1">
                <Label className="text-xs">الاسم *</Label>
                <Input className="h-8 text-sm" value={agentForm.name} onChange={e => setAgentForm({...agentForm, name: e.target.value})} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">البريد الإلكتروني *</Label>
                <Input className="h-8 text-sm" type="email" value={agentForm.email} onChange={e => setAgentForm({...agentForm, email: e.target.value})} disabled={!!editingAgent} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">الهاتف</Label>
                <Input className="h-8 text-sm" value={agentForm.phone} onChange={e => setAgentForm({...agentForm, phone: e.target.value})} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">اسم الشركة</Label>
                <Input className="h-8 text-sm" value={agentForm.company_name} onChange={e => setAgentForm({...agentForm, company_name: e.target.value})} />
              </div>
              <div className="col-span-2 space-y-1">
                <Label className="text-xs">العنوان</Label>
                <Input className="h-8 text-sm" value={agentForm.address} onChange={e => setAgentForm({...agentForm, address: e.target.value})} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">كلمة المرور {editingAgent ? '(اتركها فارغة للإبقاء)' : '*'}</Label>
                <Input className="h-8 text-sm" type="password" value={agentForm.password} onChange={e => setAgentForm({...agentForm, password: e.target.value})} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">نسبة العمولة (%)</Label>
                <Input className="h-8 text-sm" type="number" value={agentForm.commission_percent} onChange={e => setAgentForm({...agentForm, commission_percent: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">عمولة ثابتة (دج)</Label>
                <Input className="h-8 text-sm" type="number" value={agentForm.commission_fixed} onChange={e => setAgentForm({...agentForm, commission_fixed: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">حد الدين (دج)</Label>
                <Input className="h-8 text-sm" type="number" value={agentForm.credit_limit} onChange={e => setAgentForm({...agentForm, credit_limit: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="col-span-2 space-y-1">
                <Label className="text-xs">ملاحظات</Label>
                <Textarea className="text-sm" rows={2} value={agentForm.notes} onChange={e => setAgentForm({...agentForm, notes: e.target.value})} />
              </div>
            </div>
            <DialogFooter className="pt-2">
              <Button variant="outline" size="sm" onClick={() => setAgentDialogOpen(false)}>إلغاء</Button>
              <Button size="sm" onClick={saveAgent}>حفظ</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Agent Transactions Dialog */}
        <Dialog open={agentTransactionsDialogOpen} onOpenChange={setAgentTransactionsDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>معاملات الوكيل: {selectedAgent?.name}</DialogTitle>
              <DialogDescription>
                الرصيد الحالي: <span className={`font-bold ${selectedAgent?.current_balance < 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {selectedAgent?.current_balance?.toLocaleString()} دج
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
                {agentTransactions.map(tx => (
                  <TableRow key={tx.id}>
                    <TableCell className="text-sm">{new Date(tx.created_at).toLocaleDateString('ar-DZ')}</TableCell>
                    <TableCell>
                      <Badge variant={tx.transaction_type === 'payment' ? 'default' : tx.transaction_type === 'commission' ? 'secondary' : 'outline'}>
                        {tx.transaction_type === 'payment' ? 'دفعة' : tx.transaction_type === 'commission' ? 'عمولة' : tx.transaction_type === 'subscription_sale' ? 'بيع' : tx.transaction_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{tx.description}</TableCell>
                    <TableCell className={`font-medium ${tx.transaction_type === 'subscription_sale' ? 'text-red-500' : 'text-green-500'}`}>
                      {tx.transaction_type === 'subscription_sale' ? '-' : '+'}{tx.amount?.toLocaleString()} دج
                    </TableCell>
                    <TableCell className="font-medium">{tx.balance_after?.toLocaleString()} دج</TableCell>
                  </TableRow>
                ))}
                {agentTransactions.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">لا توجد معاملات</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </DialogContent>
        </Dialog>

        {/* Add Payment Dialog */}
        <Dialog open={addPaymentDialogOpen} onOpenChange={setAddPaymentDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>إضافة دفعة للوكيل</DialogTitle>
              <DialogDescription>{selectedAgent?.name} - الرصيد الحالي: {selectedAgent?.current_balance?.toLocaleString()} دج</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>نوع المعاملة</Label>
                <Select value={paymentForm.transaction_type} onValueChange={v => setPaymentForm({...paymentForm, transaction_type: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="payment">دفعة نقدية (إضافة للرصيد)</SelectItem>
                    <SelectItem value="refund">استرداد (خصم من الرصيد)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>المبلغ (دج)</Label>
                <Input type="number" value={paymentForm.amount} onChange={e => setPaymentForm({...paymentForm, amount: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-2">
                <Label>الوصف</Label>
                <Input value={paymentForm.description} onChange={e => setPaymentForm({...paymentForm, description: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>ملاحظات</Label>
                <Textarea value={paymentForm.notes} onChange={e => setPaymentForm({...paymentForm, notes: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAddPaymentDialogOpen(false)}>إلغاء</Button>
              <Button onClick={saveAgentPayment}>تسجيل الدفعة</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
