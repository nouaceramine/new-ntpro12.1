import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
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
  Store, Users, Package, ShoppingCart, LogOut, 
  Calendar, TrendingUp, Settings, Plus, BarChart3,
  Search, Edit, Trash2, Eye, DollarSign, CreditCard,
  Truck, UserPlus, AlertTriangle, Check, X, RefreshCw,
  Wallet, Calculator, FileText, ArrowUpRight, ArrowDownRight,
  Building, Phone, Mail, MapPin, Clock, Shield
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Stats Card Component
const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
  <Card className={`bg-gradient-to-br ${color} text-white`}>
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm opacity-80">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtitle && <p className="text-xs opacity-70 mt-1">{subtitle}</p>}
        </div>
        <Icon className="h-8 w-8 opacity-80" />
      </div>
    </CardContent>
  </Card>
);

export default function TenantDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Data states
  const [stats, setStats] = useState({
    products: 0,
    sales: 0,
    customers: 0,
    lowStock: 0,
    suppliers: 0,
    employees: 0,
    totalRevenue: 0,
    monthlyRevenue: 0
  });
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [sales, setSales] = useState([]);
  const [settings, setSettings] = useState({});
  
  // Dialog states
  const [showProductDialog, setShowProductDialog] = useState(false);
  const [showCustomerDialog, setShowCustomerDialog] = useState(false);
  const [showSupplierDialog, setShowSupplierDialog] = useState(false);
  const [showEmployeeDialog, setShowEmployeeDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  const tenantData = JSON.parse(localStorage.getItem('tenantData') || '{}');
  const token = localStorage.getItem('tenantToken') || localStorage.getItem('token');

  const fetchData = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      // Fetch all data in parallel
      const [productsRes, customersRes, suppliersRes, employeesRes, salesRes, settingsRes] = await Promise.allSettled([
        axios.get(`${API}/products?limit=100`, { headers }),
        axios.get(`${API}/customers?limit=100`, { headers }),
        axios.get(`${API}/suppliers?limit=100`, { headers }),
        axios.get(`${API}/employees?limit=100`, { headers }),
        axios.get(`${API}/sales?limit=50`, { headers }),
        axios.get(`${API}/system-settings`, { headers })
      ]);
      
      const productsData = productsRes.status === 'fulfilled' ? productsRes.value.data.products || productsRes.value.data || [] : [];
      const customersData = customersRes.status === 'fulfilled' ? customersRes.value.data.customers || customersRes.value.data || [] : [];
      const suppliersData = suppliersRes.status === 'fulfilled' ? suppliersRes.value.data.suppliers || suppliersRes.value.data || [] : [];
      const employeesData = employeesRes.status === 'fulfilled' ? employeesRes.value.data.employees || employeesRes.value.data || [] : [];
      const salesData = salesRes.status === 'fulfilled' ? salesRes.value.data.sales || salesRes.value.data || [] : [];
      
      setProducts(productsData);
      setCustomers(customersData);
      setSuppliers(suppliersData);
      setEmployees(employeesData);
      setSales(salesData);
      
      if (settingsRes.status === 'fulfilled') {
        setSettings(settingsRes.value.data);
      }
      
      // Calculate stats
      const lowStockCount = productsData.filter(p => p.stock <= (p.min_stock || 10)).length;
      const totalRevenue = salesData.reduce((sum, s) => sum + (s.total || 0), 0);
      
      setStats({
        products: productsData.length,
        sales: salesData.length,
        customers: customersData.length,
        lowStock: lowStockCount,
        suppliers: suppliersData.length,
        employees: employeesData.length,
        totalRevenue,
        monthlyRevenue: totalRevenue
      });
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      navigate('/portal');
      return;
    }
    fetchData();
  }, [token, navigate, fetchData]);

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
      localStorage.setItem('user', JSON.stringify({
        ...tenantData,
        role: 'admin'
      }));
    }
    navigate('/');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-DZ', { 
      minimumFractionDigits: 2,
      maximumFractionDigits: 2 
    }).format(amount || 0) + ' دج';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-green-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">جاري تحميل البيانات...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-green-600 to-emerald-700 flex items-center justify-center">
              <Store className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg">NT Commerce</h1>
              <p className="text-xs text-muted-foreground">لوحة تحكم المشترك</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Button variant="default" size="sm" onClick={goToMainApp} className="gap-2 bg-green-600 hover:bg-green-700">
              <ShoppingCart className="h-4 w-4" />
              نقطة البيع
            </Button>
            <div className="text-left hidden md:block">
              <p className="font-medium text-sm">{tenantData.name}</p>
              <p className="text-xs text-muted-foreground">{tenantData.company_name}</p>
            </div>
            <Button variant="outline" size="sm" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" />
              خروج
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Welcome Card */}
        <Card className="bg-gradient-to-br from-green-600 to-emerald-700 text-white">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-green-100 mb-1">مرحباً بك</p>
                <h2 className="text-2xl font-bold mb-2">{tenantData.name}</h2>
                <p className="text-green-100 text-sm">{tenantData.company_name}</p>
                
                <div className="flex items-center gap-4 mt-4">
                  <Badge className="bg-white/20 hover:bg-white/30">
                    {tenantData.plan_name || 'الخطة المبدئية'}
                  </Badge>
                  {tenantData.subscription_ends_at && (
                    <div className="flex items-center gap-1 text-sm text-green-100">
                      <Calendar className="h-4 w-4" />
                      ينتهي: {new Date(tenantData.subscription_ends_at).toLocaleDateString('ar-DZ')}
                    </div>
                  )}
                </div>
              </div>
              <div className="h-16 w-16 rounded-full bg-white/20 flex items-center justify-center">
                <Store className="h-8 w-8" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard 
            title="المنتجات" 
            value={stats.products} 
            icon={Package} 
            color="from-blue-500 to-blue-600"
          />
          <StatCard 
            title="المبيعات" 
            value={stats.sales} 
            icon={ShoppingCart} 
            color="from-green-500 to-green-600"
          />
          <StatCard 
            title="الزبائن" 
            value={stats.customers} 
            icon={Users} 
            color="from-purple-500 to-purple-600"
          />
          <StatCard 
            title="مخزون منخفض" 
            value={stats.lowStock} 
            icon={AlertTriangle} 
            color="from-red-500 to-red-600"
          />
          <StatCard 
            title="الموردين" 
            value={stats.suppliers} 
            icon={Truck} 
            color="from-orange-500 to-orange-600"
          />
          <StatCard 
            title="الموظفين" 
            value={stats.employees} 
            icon={UserPlus} 
            color="from-teal-500 to-teal-600"
          />
        </div>

        {/* Revenue Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-emerald-100 text-sm">إجمالي الإيرادات</p>
                  <p className="text-3xl font-bold mt-1">{formatCurrency(stats.totalRevenue)}</p>
                </div>
                <div className="h-14 w-14 rounded-full bg-white/20 flex items-center justify-center">
                  <DollarSign className="h-7 w-7" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-amber-100 text-sm">إيرادات هذا الشهر</p>
                  <p className="text-3xl font-bold mt-1">{formatCurrency(stats.monthlyRevenue)}</p>
                </div>
                <div className="h-14 w-14 rounded-full bg-white/20 flex items-center justify-center">
                  <TrendingUp className="h-7 w-7" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid grid-cols-4 lg:grid-cols-7 gap-2 h-auto p-1">
            <TabsTrigger value="overview" className="gap-2 py-2">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">نظرة عامة</span>
            </TabsTrigger>
            <TabsTrigger value="products" className="gap-2 py-2">
              <Package className="h-4 w-4" />
              <span className="hidden sm:inline">المنتجات</span>
            </TabsTrigger>
            <TabsTrigger value="sales" className="gap-2 py-2">
              <ShoppingCart className="h-4 w-4" />
              <span className="hidden sm:inline">المبيعات</span>
            </TabsTrigger>
            <TabsTrigger value="customers" className="gap-2 py-2">
              <Users className="h-4 w-4" />
              <span className="hidden sm:inline">الزبائن</span>
            </TabsTrigger>
            <TabsTrigger value="suppliers" className="gap-2 py-2">
              <Truck className="h-4 w-4" />
              <span className="hidden sm:inline">الموردين</span>
            </TabsTrigger>
            <TabsTrigger value="employees" className="gap-2 py-2">
              <UserPlus className="h-4 w-4" />
              <span className="hidden sm:inline">الموظفين</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2 py-2">
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">الإعدادات</span>
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Recent Sales */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ShoppingCart className="h-5 w-5 text-green-600" />
                    آخر المبيعات
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {sales.length > 0 ? (
                    <div className="space-y-3">
                      {sales.slice(0, 5).map((sale, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                          <div>
                            <p className="font-medium text-sm">فاتورة #{sale.invoice_number || sale.id?.slice(-6)}</p>
                            <p className="text-xs text-muted-foreground">{sale.customer_name || 'عميل نقدي'}</p>
                          </div>
                          <div className="text-left">
                            <p className="font-bold text-green-600">{formatCurrency(sale.total)}</p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(sale.created_at).toLocaleDateString('ar-DZ')}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8">لا توجد مبيعات بعد</p>
                  )}
                </CardContent>
              </Card>

              {/* Low Stock Products */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                    منتجات المخزون المنخفض
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {products.filter(p => p.stock <= (p.min_stock || 10)).length > 0 ? (
                    <div className="space-y-3">
                      {products.filter(p => p.stock <= (p.min_stock || 10)).slice(0, 5).map((product, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-red-50">
                          <div>
                            <p className="font-medium text-sm">{product.name}</p>
                            <p className="text-xs text-muted-foreground">{product.category || 'بدون تصنيف'}</p>
                          </div>
                          <Badge variant="destructive">{product.stock} قطعة</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8">لا توجد منتجات بمخزون منخفض</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>إجراءات سريعة</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={goToMainApp}>
                    <ShoppingCart className="h-6 w-6 text-green-600" />
                    <span>بيع جديد</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => setActiveTab('products')}>
                    <Plus className="h-6 w-6 text-blue-600" />
                    <span>إضافة منتج</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => setActiveTab('customers')}>
                    <UserPlus className="h-6 w-6 text-purple-600" />
                    <span>إضافة زبون</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={goToMainApp}>
                    <BarChart3 className="h-6 w-6 text-orange-600" />
                    <span>التقارير</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  إدارة المنتجات ({products.length})
                </CardTitle>
                <div className="flex gap-2">
                  <div className="relative">
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input 
                      placeholder="بحث..." 
                      className="pr-9 w-48"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Button onClick={goToMainApp} className="gap-2">
                    <Plus className="h-4 w-4" />
                    إضافة منتج
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>المنتج</TableHead>
                      <TableHead>السعر</TableHead>
                      <TableHead>المخزون</TableHead>
                      <TableHead>التصنيف</TableHead>
                      <TableHead>الحالة</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {products
                      .filter(p => p.name?.toLowerCase().includes(searchQuery.toLowerCase()))
                      .slice(0, 10)
                      .map((product) => (
                      <TableRow key={product.id}>
                        <TableCell className="font-medium">{product.name}</TableCell>
                        <TableCell>{formatCurrency(product.price)}</TableCell>
                        <TableCell>
                          <Badge variant={product.stock <= (product.min_stock || 10) ? "destructive" : "default"}>
                            {product.stock}
                          </Badge>
                        </TableCell>
                        <TableCell>{product.category || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={product.is_active !== false ? "default" : "secondary"}>
                            {product.is_active !== false ? 'نشط' : 'معطل'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {products.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا توجد منتجات. أضف منتجك الأول!</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sales Tab */}
          <TabsContent value="sales" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <ShoppingCart className="h-5 w-5" />
                  سجل المبيعات ({sales.length})
                </CardTitle>
                <Button onClick={goToMainApp} className="gap-2">
                  <Plus className="h-4 w-4" />
                  بيع جديد
                </Button>
              </CardHeader>
              <CardContent>
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
                    {sales.slice(0, 10).map((sale) => (
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
                  <p className="text-center text-muted-foreground py-8">لا توجد مبيعات بعد</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Customers Tab */}
          <TabsContent value="customers" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  إدارة الزبائن ({customers.length})
                </CardTitle>
                <Button onClick={goToMainApp} className="gap-2">
                  <Plus className="h-4 w-4" />
                  إضافة زبون
                </Button>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الاسم</TableHead>
                      <TableHead>الهاتف</TableHead>
                      <TableHead>الرصيد</TableHead>
                      <TableHead>إجمالي المشتريات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {customers.slice(0, 10).map((customer) => (
                      <TableRow key={customer.id}>
                        <TableCell className="font-medium">{customer.name}</TableCell>
                        <TableCell>{customer.phone || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={customer.balance > 0 ? "destructive" : "default"}>
                            {formatCurrency(customer.balance || 0)}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatCurrency(customer.total_purchases || 0)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {customers.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا يوجد زبائن بعد</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Suppliers Tab */}
          <TabsContent value="suppliers" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  إدارة الموردين ({suppliers.length})
                </CardTitle>
                <Button onClick={goToMainApp} className="gap-2">
                  <Plus className="h-4 w-4" />
                  إضافة مورد
                </Button>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الاسم</TableHead>
                      <TableHead>الهاتف</TableHead>
                      <TableHead>الرصيد المستحق</TableHead>
                      <TableHead>إجمالي المشتريات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {suppliers.slice(0, 10).map((supplier) => (
                      <TableRow key={supplier.id}>
                        <TableCell className="font-medium">{supplier.name}</TableCell>
                        <TableCell>{supplier.phone || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={supplier.balance > 0 ? "destructive" : "default"}>
                            {formatCurrency(supplier.balance || 0)}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatCurrency(supplier.total_purchases || 0)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {suppliers.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا يوجد موردين بعد</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Employees Tab */}
          <TabsContent value="employees" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <UserPlus className="h-5 w-5" />
                  إدارة الموظفين ({employees.length})
                </CardTitle>
                <Button onClick={goToMainApp} className="gap-2">
                  <Plus className="h-4 w-4" />
                  إضافة موظف
                </Button>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الاسم</TableHead>
                      <TableHead>البريد</TableHead>
                      <TableHead>الدور</TableHead>
                      <TableHead>الحالة</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {employees.slice(0, 10).map((employee) => (
                      <TableRow key={employee.id}>
                        <TableCell className="font-medium">{employee.name}</TableCell>
                        <TableCell>{employee.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {employee.role === 'admin' ? 'مدير' : 
                             employee.role === 'seller' ? 'بائع' : 
                             employee.role === 'manager' ? 'مشرف' : employee.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={employee.is_active !== false ? "default" : "secondary"}>
                            {employee.is_active !== false ? 'نشط' : 'معطل'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {employees.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">لا يوجد موظفين بعد</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Subscription Info */}
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

              {/* Account Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building className="h-5 w-5" />
                    معلومات الحساب
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                      <Mail className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">البريد الإلكتروني</p>
                        <p className="font-medium">{tenantData.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                      <Store className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">اسم المتجر</p>
                        <p className="font-medium">{tenantData.company_name || tenantData.name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                      <Shield className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">معرف المشترك</p>
                        <p className="font-medium text-xs">{tenantData.id || tenantData.tenant_id}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Go to Full Settings */}
            <Card>
              <CardContent className="p-6 text-center">
                <Settings className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="font-semibold mb-2">إعدادات متقدمة</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  للوصول لجميع الإعدادات المتقدمة، انتقل للنظام الرئيسي
                </p>
                <Button onClick={goToMainApp} className="gap-2">
                  <Settings className="h-4 w-4" />
                  فتح الإعدادات
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
