import { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout } from '../components/Layout';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';
import { 
  Settings,
  Shield,
  Users,
  RefreshCw,
  AlertTriangle,
  Trash2,
  Save,
  Eye,
  Edit2,
  Plus,
  Check,
  X,
  Printer,
  Usb,
  Smartphone,
  Wifi,
  Cable,
  Monitor
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SettingsPage() {
  const { t, language } = useLanguage();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [roles, setRoles] = useState([]);
  const [defaultPermissions, setDefaultPermissions] = useState({});
  
  // Factory Reset
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [resetCode, setResetCode] = useState('');
  const [resetting, setResetting] = useState(false);
  
  // Permissions
  const [selectedUser, setSelectedUser] = useState(null);
  const [showPermissionsDialog, setShowPermissionsDialog] = useState(false);
  const [userPermissions, setUserPermissions] = useState({});
  const [savingPermissions, setSavingPermissions] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [usersRes, statsRes, rolesRes] = await Promise.all([
        axios.get(`${API}/users`, { headers }),
        axios.get(`${API}/system/stats`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/permissions/roles`, { headers })
      ]);
      
      setUsers(usersRes.data);
      setSystemStats(statsRes.data);
      setRoles(rolesRes.data.roles);
      setDefaultPermissions(rolesRes.data.default_permissions);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  const openPermissionsDialog = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/users/${userId}/permissions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSelectedUser(users.find(u => u.id === userId));
      setUserPermissions(response.data.permissions);
      setShowPermissionsDialog(true);
    } catch (error) {
      toast.error(t.error);
    }
  };

  const savePermissions = async () => {
    if (!selectedUser) return;
    
    setSavingPermissions(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/users/${selectedUser.id}/permissions`, userPermissions, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حفظ الصلاحيات' : 'Permissions saved');
      setShowPermissionsDialog(false);
    } catch (error) {
      toast.error(t.error);
    } finally {
      setSavingPermissions(false);
    }
  };

  const resetPermissions = async () => {
    if (!selectedUser) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/users/${selectedUser.id}/reset-permissions`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserPermissions(defaultPermissions[selectedUser.role] || {});
      toast.success(language === 'ar' ? 'تم إعادة الصلاحيات للافتراضي' : 'Permissions reset');
    } catch (error) {
      toast.error(t.error);
    }
  };

  const handleFactoryReset = async () => {
    if (resetCode !== 'RESET-ALL-DATA') {
      toast.error(language === 'ar' ? 'كود التأكيد غير صحيح' : 'Invalid confirmation code');
      return;
    }
    
    setResetting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/system/factory-reset`, null, {
        headers: { Authorization: `Bearer ${token}` },
        params: { confirm_code: resetCode }
      });
      toast.success(t.factoryResetSuccess);
      setShowResetDialog(false);
      setResetCode('');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setResetting(false);
    }
  };

  const updatePermission = (category, action, value) => {
    setUserPermissions(prev => {
      const updated = { ...prev };
      if (typeof updated[category] === 'object') {
        updated[category] = { ...updated[category], [action]: value };
      } else {
        updated[category] = value;
      }
      return updated;
    });
  };

  const permissionCategories = [
    { key: 'dashboard', label: language === 'ar' ? 'لوحة التحكم' : 'Dashboard', simple: true },
    { key: 'pos', label: language === 'ar' ? 'نقطة البيع' : 'POS', simple: true },
    { key: 'products', label: language === 'ar' ? 'المنتجات' : 'Products', simple: false },
    { key: 'sales', label: language === 'ar' ? 'المبيعات' : 'Sales', simple: false },
    { key: 'customers', label: language === 'ar' ? 'الزبائن' : 'Customers', simple: false },
    { key: 'suppliers', label: language === 'ar' ? 'الموردين' : 'Suppliers', simple: false },
    { key: 'employees', label: language === 'ar' ? 'الموظفين' : 'Employees', simple: false },
    { key: 'debts', label: language === 'ar' ? 'الديون' : 'Debts', simple: false },
    { key: 'reports', label: language === 'ar' ? 'التقارير' : 'Reports', simple: true },
    { key: 'users', label: language === 'ar' ? 'المستخدمين' : 'Users', simple: false },
    { key: 'recharge', label: language === 'ar' ? 'شحن الرصيد' : 'Recharge', simple: true },
    { key: 'settings', label: language === 'ar' ? 'الإعدادات' : 'Settings', simple: true },
    { key: 'api_keys', label: language === 'ar' ? 'مفاتيح API' : 'API Keys', simple: true },
    { key: 'factory_reset', label: language === 'ar' ? 'ضبط المصنع' : 'Factory Reset', simple: true },
  ];

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{t.systemSettings}</h1>
          <p className="text-muted-foreground">
            {language === 'ar' ? 'إدارة صلاحيات المستخدمين وإعدادات النظام' : 'Manage user permissions and system settings'}
          </p>
        </div>

        <Tabs defaultValue="permissions" className="space-y-6">
          <TabsList>
            <TabsTrigger value="permissions" className="gap-2">
              <Shield className="h-4 w-4" />
              {t.permissions}
            </TabsTrigger>
            <TabsTrigger value="system" className="gap-2">
              <Settings className="h-4 w-4" />
              {language === 'ar' ? 'النظام' : 'System'}
            </TabsTrigger>
          </TabsList>

          {/* Permissions Tab */}
          <TabsContent value="permissions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  {t.userPermissions}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' ? 'انقر على مستخدم لتعديل صلاحياته' : 'Click on a user to edit their permissions'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.name}</TableHead>
                      <TableHead>{t.email}</TableHead>
                      <TableHead>{language === 'ar' ? 'الدور' : 'Role'}</TableHead>
                      <TableHead>{t.actions}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">{u.name}</TableCell>
                        <TableCell>{u.email}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            u.role === 'admin' ? 'bg-red-100 text-red-700' :
                            u.role === 'manager' ? 'bg-blue-100 text-blue-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {u.role === 'admin' ? (language === 'ar' ? 'مدير' : 'Admin') :
                             u.role === 'manager' ? (language === 'ar' ? 'مشرف' : 'Manager') :
                             (language === 'ar' ? 'مستخدم' : 'User')}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openPermissionsDialog(u.id)}
                            disabled={u.id === user?.id}
                          >
                            <Shield className="h-4 w-4 me-1" />
                            {t.permissions}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Tab */}
          <TabsContent value="system" className="space-y-6">
            {/* System Stats */}
            {systemStats && (
              <Card>
                <CardHeader>
                  <CardTitle>{language === 'ar' ? 'إحصائيات النظام' : 'System Statistics'}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{systemStats.products}</p>
                      <p className="text-sm text-muted-foreground">{language === 'ar' ? 'منتج' : 'Products'}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{systemStats.customers}</p>
                      <p className="text-sm text-muted-foreground">{language === 'ar' ? 'زبون' : 'Customers'}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{systemStats.sales}</p>
                      <p className="text-sm text-muted-foreground">{language === 'ar' ? 'مبيعات' : 'Sales'}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{systemStats.users}</p>
                      <p className="text-sm text-muted-foreground">{language === 'ar' ? 'مستخدم' : 'Users'}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Factory Reset */}
            <Card className="border-red-200 dark:border-red-900">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                  {t.factoryReset}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'احذر! سيتم حذف جميع البيانات نهائياً ولا يمكن استرجاعها' 
                    : 'Warning! All data will be permanently deleted and cannot be recovered'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  variant="destructive" 
                  onClick={() => setShowResetDialog(true)}
                  className="gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  {t.factoryReset}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Permissions Dialog */}
        <Dialog open={showPermissionsDialog} onOpenChange={setShowPermissionsDialog}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
            <DialogHeader>
              <DialogTitle>{t.userPermissions}: {selectedUser?.name}</DialogTitle>
              <DialogDescription>
                {language === 'ar' ? 'الدور' : 'Role'}: {selectedUser?.role}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid gap-4">
                {permissionCategories.map((cat) => (
                  <div key={cat.key} className="flex items-center justify-between p-3 border rounded-lg">
                    <span className="font-medium">{cat.label}</span>
                    {cat.simple ? (
                      <Switch
                        checked={!!userPermissions[cat.key]}
                        onCheckedChange={(checked) => updatePermission(cat.key, null, checked)}
                      />
                    ) : (
                      <div className="flex gap-4">
                        {['view', 'add', 'edit', 'delete'].map((action) => (
                          <label key={action} className="flex items-center gap-1 text-sm">
                            <Checkbox
                              checked={userPermissions[cat.key]?.[action] || false}
                              onCheckedChange={(checked) => updatePermission(cat.key, action, checked)}
                            />
                            {action === 'view' ? t.viewPermission :
                             action === 'add' ? t.addPermission :
                             action === 'edit' ? t.editPermission : t.deletePermission}
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              <div className="flex gap-2 pt-4 border-t">
                <Button variant="outline" onClick={resetPermissions} className="gap-2">
                  <RefreshCw className="h-4 w-4" />
                  {t.resetToDefault}
                </Button>
                <div className="flex-1" />
                <Button variant="outline" onClick={() => setShowPermissionsDialog(false)}>
                  {t.cancel}
                </Button>
                <Button onClick={savePermissions} disabled={savingPermissions} className="gap-2">
                  <Save className="h-4 w-4" />
                  {t.save}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Factory Reset Dialog */}
        <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-red-600">
                <AlertTriangle className="h-5 w-5" />
                {t.factoryReset}
              </DialogTitle>
              <DialogDescription>
                {t.factoryResetConfirm}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200">
                <p className="font-medium text-red-700 dark:text-red-400 mb-2">{t.dataWillBeDeleted}</p>
                <ul className="text-sm text-red-600 dark:text-red-300 space-y-1 list-disc list-inside">
                  <li>{language === 'ar' ? 'جميع المنتجات' : 'All products'}</li>
                  <li>{language === 'ar' ? 'جميع الزبائن والموردين' : 'All customers and suppliers'}</li>
                  <li>{language === 'ar' ? 'جميع المبيعات والمشتريات' : 'All sales and purchases'}</li>
                  <li>{language === 'ar' ? 'جميع الموظفين' : 'All employees'}</li>
                  <li>{language === 'ar' ? 'سيتم الاحتفاظ بحساب المدير فقط' : 'Only admin account will be kept'}</li>
                </ul>
              </div>
              
              <div>
                <Label>{t.factoryResetCode}</Label>
                <Input
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value)}
                  placeholder="RESET-ALL-DATA"
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {language === 'ar' ? 'اكتب' : 'Type'}: <code className="bg-muted px-1 rounded">RESET-ALL-DATA</code>
                </p>
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowResetDialog(false)} className="flex-1">
                  {t.cancel}
                </Button>
                <Button 
                  variant="destructive" 
                  onClick={handleFactoryReset}
                  disabled={resetting || resetCode !== 'RESET-ALL-DATA'}
                  className="flex-1 gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  {resetting ? t.loading : t.factoryReset}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
