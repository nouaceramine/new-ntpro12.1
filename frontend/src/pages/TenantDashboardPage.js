import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { 
  Users, Building, CreditCard, TrendingUp, Package, 
  Settings, Plus, Edit, Trash2, Check, X, Clock,
  AlertTriangle, DollarSign, Search, MoreHorizontal,
  Star, Eye, EyeOff, Ban, RefreshCw, Calendar, Store, Truck, ShoppingBag,
  Banknote, Wallet, PiggyBank, Receipt, Calculator, FileText, ArrowUpRight, ArrowDownRight,
  LogOut, UserPlus, BarChart3
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Finance Reports Component for Tenant
const FinanceReportsSection = ({ sales, expenses }) => {
  const [financeData, setFinanceData] = useState({
    total_revenue: 0,
    monthly_revenue: 0,
    yearly_revenue: 0,
    total_expenses: 0,
    net_profit: 0,
    payment_methods: {
      cash: { count: 0, amount: 0 },
      card: { count: 0, amount: 0 },
      credit: { count: 0, amount: 0 }
    }
  });
  const [dateRange, setDateRange] = useState('all');

  useEffect(() => {
    calculateFromLocalData();
  }, [sales, expenses, dateRange]);

  const calculateFromLocalData = () => {
    const now = new Date();
    const thisMonth = now.getMonth();
    const thisYear = now.getFullYear();

    let total = 0, monthly = 0, yearly = 0;
    const methods = {
      cash: { count: 0, amount: 0 },
      card: { count: 0, amount: 0 },
      credit: { count: 0, amount: 0 }
    };

    (sales || []).forEach(sale => {
      const saleDate = new Date(sale.created_at);
      const amount = sale.total || 0;
      total += amount;
      
      if (saleDate.getFullYear() === thisYear) {
        yearly += amount;
        if (saleDate.getMonth() === thisMonth) {
          monthly += amount;
        }
      }

      const method = sale.payment_method || 'cash';
      if (methods[method]) {
        methods[method].count++;
        methods[method].amount += amount;
      }
    });

    const totalExpenses = (expenses || []).reduce((sum, e) => sum + (e.amount || 0), 0);

    setFinanceData({
      total_revenue: total,
      monthly_revenue: monthly,
      yearly_revenue: yearly,
      total_expenses: totalExpenses,
      net_profit: total - totalExpenses,
      payment_methods: methods
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-DZ').format(amount || 0) + ' دج';
  };

  return (
    <div className="space-y-6">
      {/* Date Range Filter */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          التقارير المالية الشاملة
        </h3>
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

      {/* Revenue Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">إجمالي الإيرادات</p>
                <p className="text-xl font-bold">{formatCurrency(financeData.total_revenue)}</p>
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
                <p className="text-xl font-bold">{formatCurrency(financeData.monthly_revenue)}</p>
              </div>
              <Calendar className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">إيراد السنة</p>
                <p className="text-xl font-bold">{formatCurrency(financeData.yearly_revenue)}</p>
              </div>
              <TrendingUp className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">إجمالي المصاريف</p>
                <p className="text-xl font-bold">{formatCurrency(financeData.total_expenses)}</p>
              </div>
              <Receipt className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">صافي الربح</p>
                <p className="text-xl font-bold">{formatCurrency(financeData.net_profit)}</p>
              </div>
              <Calculator className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs opacity-80">عدد المبيعات</p>
                <p className="text-xl font-bold">{sales?.length || 0}</p>
              </div>
              <ShoppingBag className="h-8 w-8 opacity-80" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Payment Methods */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            توزيع المبيعات حسب طريقة الدفع
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-green-50 border border-green-200">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                  <Banknote className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">نقدي</p>
                  <p className="text-lg font-bold text-green-600">{formatCurrency(financeData.payment_methods.cash.amount)}</p>
                  <p className="text-xs text-muted-foreground">{financeData.payment_methods.cash.count} عملية</p>
                </div>
              </div>
            </div>
            <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <CreditCard className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">بطاقة</p>
                  <p className="text-lg font-bold text-blue-600">{formatCurrency(financeData.payment_methods.card.amount)}</p>
                  <p className="text-xs text-muted-foreground">{financeData.payment_methods.card.count} عملية</p>
                </div>
              </div>
            </div>
            <div className="p-4 rounded-lg bg-orange-50 border border-orange-200">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-orange-100 flex items-center justify-center">
                  <Wallet className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">آجل</p>
                  <p className="text-lg font-bold text-orange-600">{formatCurrency(financeData.payment_methods.credit.amount)}</p>
                  <p className="text-xs text-muted-foreground">{financeData.payment_methods.credit.count} عملية</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default function TenantDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Data states
  const [stats, setStats] = useState({
    total_products: 0,
    total_sales: 0,
    total_customers: 0,
    low_stock: 0,
    total_suppliers: 0,
    total_employees: 0,
    monthly_revenue: 0,
    total_revenue: 0
  });
  
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [sales, setSales] = useState([]);
  const [expenses, setExpenses] = useState([]);
  
  // Dialog states
  const [productDialogOpen, setProductDialogOpen] = useState(false);
  const [customerDialogOpen, setCustomerDialogOpen] = useState(false);
  const [supplierDialogOpen, setSupplierDialogOpen] = useState(false);
  const [employeeDialogOpen, setEmployeeDialogOpen] = useState(false);
  
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [editingEmployee, setEditingEmployee] = useState(null);
  
  // Form states
  const [productForm, setProductForm] = useState({ name: '', price: 0, stock: 0, category: '' });
  const [customerForm, setCustomerForm] = useState({ name: '', phone: '', email: '' });
  const [supplierForm, setSupplierForm] = useState({ name: '', phone: '', email: '' });
  const [employeeForm, setEmployeeForm] = useState({ name: '', email: '', password: '', role: 'seller' });

  const tenantData = JSON.parse(localStorage.getItem('tenantData') || localStorage.getItem('user') || '{}');
  const token = localStorage.getItem('tenantToken') || localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      navigate('/portal');
      return;
    }
    fetchData();
  }, [token, navigate]);

  const fetchData = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      const [productsRes, customersRes, suppliersRes, employeesRes, salesRes, expensesRes] = await Promise.allSettled([
        axios.get(`${API}/products?limit=200`, { headers }),
        axios.get(`${API}/customers?limit=200`, { headers }),
        axios.get(`${API}/suppliers?limit=200`, { headers }),
        axios.get(`${API}/employees?limit=200`, { headers }),
        axios.get(`${API}/sales?limit=100`, { headers }),
        axios.get(`${API}/expenses?limit=100`, { headers })
      ]);
      
      const productsData = productsRes.status === 'fulfilled' ? (productsRes.value.data.products || productsRes.value.data || []) : [];
      const customersData = customersRes.status === 'fulfilled' ? (customersRes.value.data.customers || customersRes.value.data || []) : [];
      const suppliersData = suppliersRes.status === 'fulfilled' ? (suppliersRes.value.data.suppliers || suppliersRes.value.data || []) : [];
      const employeesData = employeesRes.status === 'fulfilled' ? (employeesRes.value.data.employees || employeesRes.value.data || []) : [];
      const salesData = salesRes.status === 'fulfilled' ? (salesRes.value.data.sales || salesRes.value.data || []) : [];
      const expensesData = expensesRes.status === 'fulfilled' ? (expensesRes.value.data.expenses || expensesRes.value.data || []) : [];
      
      setProducts(productsData);
      setCustomers(customersData);
      setSuppliers(suppliersData);
      setEmployees(employeesData);
      setSales(salesData);
      setExpenses(expensesData);
      
      const lowStock = productsData.filter(p => p.stock <= (p.min_stock || 10)).length;
      const totalRevenue = salesData.reduce((sum, s) => sum + (s.total || 0), 0);
      
      const now = new Date();
      const monthlyRevenue = salesData
        .filter(s => new Date(s.created_at).getMonth() === now.getMonth())
        .reduce((sum, s) => sum + (s.total || 0), 0);
      
      setStats({
        total_products: productsData.length,
        total_sales: salesData.length,
        total_customers: customersData.length,
        low_stock: lowStock,
        total_suppliers: suppliersData.length,
        total_employees: employeesData.length,
        monthly_revenue: monthlyRevenue,
        total_revenue: totalRevenue
      });
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('tenantToken');
    localStorage.removeItem('tenantData');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/portal');
    toast.success('تم تسجيل الخروج');
  };

  const goToMainApp = () => {
    const tenantToken = localStorage.getItem('tenantToken');
    if (tenantToken) {
      localStorage.setItem('token', tenantToken);
      localStorage.setItem('user', JSON.stringify({ ...tenantData, role: 'admin' }));
    }
    navigate('/');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-DZ').format(amount || 0) + ' دج';
  };

  // Product CRUD
  const openProductDialog = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setProductForm({ name: product.name, price: product.price, stock: product.stock, category: product.category || '' });
    } else {
      setEditingProduct(null);
      setProductForm({ name: '', price: 0, stock: 0, category: '' });
    }
    setProductDialogOpen(true);
  };

  const saveProduct = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      if (editingProduct) {
        await axios.put(`${API}/products/${editingProduct.id}`, productForm, { headers });
        toast.success('تم تحديث المنتج');
      } else {
        await axios.post(`${API}/products`, productForm, { headers });
        toast.success('تم إضافة المنتج');
      }
      setProductDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const deleteProduct = async (id) => {
    if (!confirm('هل أنت متأكد من حذف هذا المنتج؟')) return;
    try {
      const headers = { Authorization: `Bearer ${token}` };
      await axios.delete(`${API}/products/${id}`, { headers });
      toast.success('تم حذف المنتج');
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  // Customer CRUD
  const openCustomerDialog = (customer = null) => {
    if (customer) {
      setEditingCustomer(customer);
      setCustomerForm({ name: customer.name, phone: customer.phone || '', email: customer.email || '' });
    } else {
      setEditingCustomer(null);
      setCustomerForm({ name: '', phone: '', email: '' });
    }
    setCustomerDialogOpen(true);
  };

  const saveCustomer = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      if (editingCustomer) {
        await axios.put(`${API}/customers/${editingCustomer.id}`, customerForm, { headers });
        toast.success('تم تحديث الزبون');
      } else {
        await axios.post(`${API}/customers`, customerForm, { headers });
        toast.success('تم إضافة الزبون');
      }
      setCustomerDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const deleteCustomer = async (id) => {
    if (!confirm('هل أنت متأكد من حذف هذا الزبون؟')) return;
    try {
      const headers = { Authorization: `Bearer ${token}` };
      await axios.delete(`${API}/customers/${id}`, { headers });
      toast.success('تم حذف الزبون');
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  // Supplier CRUD
  const openSupplierDialog = (supplier = null) => {
    if (supplier) {
      setEditingSupplier(supplier);
      setSupplierForm({ name: supplier.name, phone: supplier.phone || '', email: supplier.email || '' });
    } else {
      setEditingSupplier(null);
      setSupplierForm({ name: '', phone: '', email: '' });
    }
    setSupplierDialogOpen(true);
  };

  const saveSupplier = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      if (editingSupplier) {
        await axios.put(`${API}/suppliers/${editingSupplier.id}`, supplierForm, { headers });
        toast.success('تم تحديث المورد');
      } else {
        await axios.post(`${API}/suppliers`, supplierForm, { headers });
        toast.success('تم إضافة المورد');
      }
      setSupplierDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const deleteSupplier = async (id) => {
    if (!confirm('هل أنت متأكد من حذف هذا المورد؟')) return;
    try {
      const headers = { Authorization: `Bearer ${token}` };
      await axios.delete(`${API}/suppliers/${id}`, { headers });
      toast.success('تم حذف المورد');
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  // Employee CRUD
  const openEmployeeDialog = (employee = null) => {
    if (employee) {
      setEditingEmployee(employee);
      setEmployeeForm({ name: employee.name, email: employee.email, password: '', role: employee.role || 'seller' });
    } else {
      setEditingEmployee(null);
      setEmployeeForm({ name: '', email: '', password: '', role: 'seller' });
    }
    setEmployeeDialogOpen(true);
  };

  const saveEmployee = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      if (editingEmployee) {
        const data = { ...employeeForm };
        if (!data.password) delete data.password;
        await axios.put(`${API}/employees/${editingEmployee.id}`, data, { headers });
        toast.success('تم تحديث الموظف');
      } else {
        await axios.post(`${API}/employees`, employeeForm, { headers });
        toast.success('تم إضافة الموظف');
      }
      setEmployeeDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const deleteEmployee = async (id) => {
    if (!confirm('هل أنت متأكد من حذف هذا الموظف؟')) return;
    try {
      const headers = { Authorization: `Bearer ${token}` };
      await axios.delete(`${API}/employees/${id}`, { headers });
      toast.success('تم حذف الموظف');
      fetchData();
    } catch (error) {
      toast.error('حدث خطأ');
    }
  };

  const filteredProducts = products.filter(p => {
    const productName = p.name_ar || p.name_en || p.name || '';
    return productName.toLowerCase().includes(searchQuery.toLowerCase()) ||
           (p.barcode || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
           (p.article_code || '').toLowerCase().includes(searchQuery.toLowerCase());
  });
  
  const filteredCustomers = customers.filter(c => 
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.phone?.includes(searchQuery)
  );
  
  const filteredSuppliers = suppliers.filter(s => 
    s.name?.toLowerCase().includes(searchQuery.toLowerCase())
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
      <div className="space-y-6 animate-fade-in" data-testid="tenant-dashboard-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Store className="h-8 w-8 text-primary" />
              لوحة تحكم {tenantData.company_name || tenantData.name || 'المتجر'}
            </h1>
            <p className="text-muted-foreground mt-1">إدارة المنتجات والمبيعات والزبائن والموردين</p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={goToMainApp} className="gap-2">
              <ShoppingBag className="h-4 w-4" />
              نقطة البيع
            </Button>
            <Button variant="outline" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" />
              خروج
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">إجمالي المنتجات</p>
                  <p className="text-2xl font-bold">{stats.total_products}</p>
                </div>
                <Package className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">المبيعات</p>
                  <p className="text-2xl font-bold text-green-600">{stats.total_sales}</p>
                </div>
                <ShoppingBag className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">الزبائن</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.total_customers}</p>
                </div>
                <Users className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">مخزون منخفض</p>
                  <p className="text-2xl font-bold text-amber-600">{stats.low_stock}</p>
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
                  <p className="text-2xl font-bold">{formatCurrency(stats.monthly_revenue)}</p>
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
                  <p className="text-2xl font-bold">{formatCurrency(stats.total_revenue)}</p>
                </div>
                <DollarSign className="h-8 w-8 text-primary" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="products" className="space-y-6">
          <TabsList>
            <TabsTrigger value="products" className="gap-2">
              <Package className="h-4 w-4" />
              المنتجات
            </TabsTrigger>
            <TabsTrigger value="sales" className="gap-2">
              <ShoppingBag className="h-4 w-4" />
              المبيعات
            </TabsTrigger>
            <TabsTrigger value="customers" className="gap-2">
              <Users className="h-4 w-4" />
              الزبائن
            </TabsTrigger>
            <TabsTrigger value="suppliers" className="gap-2">
              <Truck className="h-4 w-4" />
              الموردين
            </TabsTrigger>
            <TabsTrigger value="employees" className="gap-2">
              <UserPlus className="h-4 w-4" />
              الموظفين
            </TabsTrigger>
            <TabsTrigger value="finance" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              التقارير المالية
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2">
              <Settings className="h-4 w-4" />
              الإعدادات
            </TabsTrigger>
          </TabsList>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-4">
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
              <Button onClick={() => openProductDialog()}>
                <Plus className="h-4 w-4 me-2" />
                إضافة منتج
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>المنتج</TableHead>
                      <TableHead>السعر</TableHead>
                      <TableHead>المخزون</TableHead>
                      <TableHead>التصنيف</TableHead>
                      <TableHead className="text-center">الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredProducts.slice(0, 20).map(product => (
                      <TableRow key={product.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{product.name_ar || product.name_en || product.name}</p>
                            {(product.barcode || product.article_code) && (
                              <p className="text-xs text-muted-foreground">{product.barcode || product.article_code}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{formatCurrency(product.retail_price || product.price || 0)}</TableCell>
                        <TableCell>
                          <Badge variant={(product.quantity || product.stock || 0) <= (product.low_stock_threshold || product.min_stock || 10) ? "destructive" : "default"}>
                            {product.quantity || product.stock || 0}
                          </Badge>
                        </TableCell>
                        <TableCell>{product.family_name || product.category || '-'}</TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            <Button size="sm" variant="ghost" onClick={() => openProductDialog(product)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="ghost" className="text-red-600" onClick={() => deleteProduct(product.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {products.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا توجد منتجات</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sales Tab */}
          <TabsContent value="sales" className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">سجل المبيعات ({sales.length})</h3>
              <Button onClick={goToMainApp}>
                <Plus className="h-4 w-4 me-2" />
                بيع جديد
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>رقم الفاتورة</TableHead>
                      <TableHead>العميل</TableHead>
                      <TableHead>المبلغ</TableHead>
                      <TableHead>طريقة الدفع</TableHead>
                      <TableHead>التاريخ</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sales.slice(0, 20).map(sale => (
                      <TableRow key={sale.id}>
                        <TableCell className="font-medium">#{sale.invoice_number || sale.id?.slice(-6)}</TableCell>
                        <TableCell>{sale.customer_name || 'عميل نقدي'}</TableCell>
                        <TableCell className="font-bold text-green-600">{formatCurrency(sale.total)}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{sale.payment_method || 'نقدي'}</Badge>
                        </TableCell>
                        <TableCell>{new Date(sale.created_at).toLocaleDateString('ar-DZ')}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {sales.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا توجد مبيعات</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Customers Tab */}
          <TabsContent value="customers" className="space-y-4">
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
              <Button onClick={() => openCustomerDialog()}>
                <Plus className="h-4 w-4 me-2" />
                إضافة زبون
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الاسم</TableHead>
                      <TableHead>الهاتف</TableHead>
                      <TableHead>البريد</TableHead>
                      <TableHead>الرصيد</TableHead>
                      <TableHead className="text-center">الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredCustomers.slice(0, 20).map(customer => (
                      <TableRow key={customer.id}>
                        <TableCell className="font-medium">{customer.name}</TableCell>
                        <TableCell>{customer.phone || '-'}</TableCell>
                        <TableCell>{customer.email || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={customer.balance > 0 ? "destructive" : "default"}>
                            {formatCurrency(customer.balance || 0)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            <Button size="sm" variant="ghost" onClick={() => openCustomerDialog(customer)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="ghost" className="text-red-600" onClick={() => deleteCustomer(customer.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {customers.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا يوجد زبائن</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Suppliers Tab */}
          <TabsContent value="suppliers" className="space-y-4">
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
              <Button onClick={() => openSupplierDialog()}>
                <Plus className="h-4 w-4 me-2" />
                إضافة مورد
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الاسم</TableHead>
                      <TableHead>الهاتف</TableHead>
                      <TableHead>البريد</TableHead>
                      <TableHead>الرصيد المستحق</TableHead>
                      <TableHead className="text-center">الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredSuppliers.slice(0, 20).map(supplier => (
                      <TableRow key={supplier.id}>
                        <TableCell className="font-medium">{supplier.name}</TableCell>
                        <TableCell>{supplier.phone || '-'}</TableCell>
                        <TableCell>{supplier.email || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={supplier.balance > 0 ? "destructive" : "default"}>
                            {formatCurrency(supplier.balance || 0)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            <Button size="sm" variant="ghost" onClick={() => openSupplierDialog(supplier)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="ghost" className="text-red-600" onClick={() => deleteSupplier(supplier.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {suppliers.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا يوجد موردين</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Employees Tab */}
          <TabsContent value="employees" className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">الموظفين ({employees.length})</h3>
              <Button onClick={() => openEmployeeDialog()}>
                <Plus className="h-4 w-4 me-2" />
                إضافة موظف
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الاسم</TableHead>
                      <TableHead>البريد</TableHead>
                      <TableHead>الدور</TableHead>
                      <TableHead>الحالة</TableHead>
                      <TableHead className="text-center">الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {employees.map(employee => (
                      <TableRow key={employee.id}>
                        <TableCell className="font-medium">{employee.name}</TableCell>
                        <TableCell>{employee.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {employee.role === 'admin' ? 'مدير' : 
                             employee.role === 'seller' ? 'بائع' : 
                             employee.role === 'manager' ? 'مشرف' : 
                             employee.role === 'accountant' ? 'محاسب' : employee.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={employee.is_active !== false ? "default" : "secondary"}>
                            {employee.is_active !== false ? 'نشط' : 'معطل'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            <Button size="sm" variant="ghost" onClick={() => openEmployeeDialog(employee)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button size="sm" variant="ghost" className="text-red-600" onClick={() => deleteEmployee(employee.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {employees.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا يوجد موظفين</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Finance Tab */}
          <TabsContent value="finance" className="space-y-6">
            <FinanceReportsSection sales={sales} expenses={expenses} />
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    معلومات الاشتراك
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm text-muted-foreground">الخطة</p>
                      <p className="font-semibold">{tenantData.plan_name || 'أساسية'}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm text-muted-foreground">الحالة</p>
                      <Badge variant="default">نشط</Badge>
                    </div>
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm text-muted-foreground">تاريخ الانتهاء</p>
                      <p className="font-semibold">
                        {tenantData.subscription_ends_at 
                          ? new Date(tenantData.subscription_ends_at).toLocaleDateString('ar-DZ')
                          : 'غير محدد'}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm text-muted-foreground">قاعدة البيانات</p>
                      <p className="font-semibold text-xs">{tenantData.database_name || 'منفصلة'}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building className="h-5 w-5" />
                    معلومات المتجر
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm text-muted-foreground">اسم المتجر</p>
                      <p className="font-semibold">{tenantData.company_name || tenantData.name}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm text-muted-foreground">البريد الإلكتروني</p>
                      <p className="font-semibold">{tenantData.email}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-sm text-muted-foreground">معرف المشترك</p>
                      <p className="font-semibold text-xs">{tenantData.id || tenantData.tenant_id}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* Product Dialog */}
        <Dialog open={productDialogOpen} onOpenChange={setProductDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingProduct ? 'تعديل المنتج' : 'إضافة منتج جديد'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>اسم المنتج</Label>
                <Input value={productForm.name} onChange={e => setProductForm({...productForm, name: e.target.value})} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>السعر</Label>
                  <Input type="number" value={productForm.price} onChange={e => setProductForm({...productForm, price: parseFloat(e.target.value) || 0})} />
                </div>
                <div className="space-y-2">
                  <Label>المخزون</Label>
                  <Input type="number" value={productForm.stock} onChange={e => setProductForm({...productForm, stock: parseInt(e.target.value) || 0})} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>التصنيف</Label>
                <Input value={productForm.category} onChange={e => setProductForm({...productForm, category: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setProductDialogOpen(false)}>إلغاء</Button>
              <Button onClick={saveProduct}>{editingProduct ? 'حفظ التعديلات' : 'إضافة'}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Customer Dialog */}
        <Dialog open={customerDialogOpen} onOpenChange={setCustomerDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingCustomer ? 'تعديل الزبون' : 'إضافة زبون جديد'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>الاسم</Label>
                <Input value={customerForm.name} onChange={e => setCustomerForm({...customerForm, name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>الهاتف</Label>
                <Input value={customerForm.phone} onChange={e => setCustomerForm({...customerForm, phone: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>البريد الإلكتروني</Label>
                <Input value={customerForm.email} onChange={e => setCustomerForm({...customerForm, email: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCustomerDialogOpen(false)}>إلغاء</Button>
              <Button onClick={saveCustomer}>{editingCustomer ? 'حفظ التعديلات' : 'إضافة'}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Supplier Dialog */}
        <Dialog open={supplierDialogOpen} onOpenChange={setSupplierDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingSupplier ? 'تعديل المورد' : 'إضافة مورد جديد'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>الاسم</Label>
                <Input value={supplierForm.name} onChange={e => setSupplierForm({...supplierForm, name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>الهاتف</Label>
                <Input value={supplierForm.phone} onChange={e => setSupplierForm({...supplierForm, phone: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>البريد الإلكتروني</Label>
                <Input value={supplierForm.email} onChange={e => setSupplierForm({...supplierForm, email: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSupplierDialogOpen(false)}>إلغاء</Button>
              <Button onClick={saveSupplier}>{editingSupplier ? 'حفظ التعديلات' : 'إضافة'}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Employee Dialog */}
        <Dialog open={employeeDialogOpen} onOpenChange={setEmployeeDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingEmployee ? 'تعديل الموظف' : 'إضافة موظف جديد'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>الاسم</Label>
                <Input value={employeeForm.name} onChange={e => setEmployeeForm({...employeeForm, name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>البريد الإلكتروني</Label>
                <Input value={employeeForm.email} onChange={e => setEmployeeForm({...employeeForm, email: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>{editingEmployee ? 'كلمة المرور الجديدة (اتركها فارغة للإبقاء)' : 'كلمة المرور'}</Label>
                <Input type="password" value={employeeForm.password} onChange={e => setEmployeeForm({...employeeForm, password: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>الدور</Label>
                <Select value={employeeForm.role} onValueChange={v => setEmployeeForm({...employeeForm, role: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">مدير</SelectItem>
                    <SelectItem value="manager">مشرف</SelectItem>
                    <SelectItem value="seller">بائع</SelectItem>
                    <SelectItem value="accountant">محاسب</SelectItem>
                    <SelectItem value="inventory_manager">مدير مخزون</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEmployeeDialogOpen(false)}>إلغاء</Button>
              <Button onClick={saveEmployee}>{editingEmployee ? 'حفظ التعديلات' : 'إضافة'}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
