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
  Monitor,
  Key,
  ImageIcon,
  MessageCircle
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
  
  // Password Change
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [passwordUser, setPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);
  const [userPermissions, setUserPermissions] = useState({});
  const [savingPermissions, setSavingPermissions] = useState(false);
  
  // USB SIM Settings
  const [usbSettings, setUsbSettings] = useState({
    enabled: false,
    port: '',
    baudRate: '9600',
    simSlots: [
      { id: 1, operator: '', phone: '', enabled: false },
      { id: 2, operator: '', phone: '', enabled: false }
    ]
  });
  
  // System Settings
  const [systemSettings, setSystemSettings] = useState({
    cash_difference_threshold: 1000,
    low_stock_threshold: 10,
    currency_symbol: 'دج',
    business_name: 'NT'
  });
  const [savingSystemSettings, setSavingSystemSettings] = useState(false);
  
  // Branding Settings
  const [brandingSettings, setBrandingSettings] = useState({
    logo_url: '',
    business_name: 'NT',
    background_image_url: '',
    tagline_ar: 'إدارة مخزون زجاج الحماية بسهولة',
    tagline_fr: 'Gestion facile de stock de protection'
  });
  const [savingBranding, setSavingBranding] = useState(false);
  
  // Printer Settings
  const [printerSettings, setPrinterSettings] = useState({
    enabled: false,
    type: 'thermal', // thermal, laser, inkjet
    connectionType: 'usb', // usb, network, bluetooth
    name: '',
    ipAddress: '',
    port: '9100',
    paperWidth: '80', // 58, 80
    autoPrint: false,
    printCopies: 1
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [usersRes, statsRes, rolesRes, sysSettingsRes, brandingRes] = await Promise.all([
        axios.get(`${API}/users`, { headers }),
        axios.get(`${API}/system/stats`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/permissions/roles`, { headers }),
        axios.get(`${API}/system/settings`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/branding/settings`).catch(() => ({ data: null }))
      ]);
      
      setUsers(usersRes.data);
      setSystemStats(statsRes.data);
      setRoles(rolesRes.data.roles);
      setDefaultPermissions(rolesRes.data.default_permissions);
      
      if (sysSettingsRes.data) {
        setSystemSettings(sysSettingsRes.data);
      }
      
      if (brandingRes.data) {
        setBrandingSettings(brandingRes.data);
      }
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

  const saveSystemSettings = async () => {
    setSavingSystemSettings(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/system/settings`, systemSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حفظ الإعدادات بنجاح' : 'Paramètres enregistrés');
    } catch (error) {
      toast.error(t.error);
    } finally {
      setSavingSystemSettings(false);
    }
  };

  const saveBrandingSettings = async () => {
    setSavingBranding(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/branding/settings`, brandingSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حفظ إعدادات صفحة الدخول' : 'Paramètres de connexion enregistrés');
    } catch (error) {
      toast.error(t.error);
    } finally {
      setSavingBranding(false);
    }
  };

  const openPasswordDialog = (u) => {
    setPasswordUser(u);
    setNewPassword('');
    setShowPasswordDialog(true);
  };

  const savePassword = async () => {
    if (!passwordUser || newPassword.length < 4) {
      toast.error(language === 'ar' ? 'كلمة المرور يجب أن تكون 4 أحرف على الأقل' : 'Le mot de passe doit contenir au moins 4 caractères');
      return;
    }
    
    setSavingPassword(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/users/${passwordUser.id}/password`, { new_password: newPassword }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم تحديث كلمة المرور بنجاح' : 'Mot de passe mis à jour');
      setShowPasswordDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSavingPassword(false);
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
          <TabsList className="grid w-full max-w-2xl grid-cols-4">
            <TabsTrigger value="permissions" className="gap-2">
              <Shield className="h-4 w-4" />
              {t.permissions}
            </TabsTrigger>
            <TabsTrigger value="printer" className="gap-2">
              <Printer className="h-4 w-4" />
              {language === 'ar' ? 'الطابعة' : 'Imprimante'}
            </TabsTrigger>
            <TabsTrigger value="usb" className="gap-2">
              <Usb className="h-4 w-4" />
              {language === 'ar' ? 'شرائح USB' : 'SIM USB'}
            </TabsTrigger>
            <TabsTrigger value="system" className="gap-2">
              <Settings className="h-4 w-4" />
              {language === 'ar' ? 'النظام' : 'Système'}
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
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => openPermissionsDialog(u.id)}
                              disabled={u.id === user?.id}
                            >
                              <Shield className="h-4 w-4 me-1" />
                              {t.permissions}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => openPasswordDialog(u)}
                              disabled={u.id === user?.id}
                            >
                              <Key className="h-4 w-4 me-1" />
                              {language === 'ar' ? 'كلمة المرور' : 'Mot de passe'}
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

          {/* Printer Settings Tab */}
          <TabsContent value="printer" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Printer className="h-5 w-5" />
                  {language === 'ar' ? 'إعدادات الطابعة' : 'Paramètres de l\'imprimante'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'إعداد الطابعة لطباعة الفواتير والإيصالات' 
                    : 'Configurer l\'imprimante pour les factures et reçus'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Enable Printer */}
                <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-primary/10">
                      <Printer className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{language === 'ar' ? 'تفعيل الطابعة' : 'Activer l\'imprimante'}</p>
                      <p className="text-sm text-muted-foreground">
                        {language === 'ar' ? 'طباعة الفواتير تلقائياً' : 'Impression automatique des factures'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={printerSettings.enabled}
                    onCheckedChange={(checked) => setPrinterSettings(prev => ({ ...prev, enabled: checked }))}
                  />
                </div>

                {printerSettings.enabled && (
                  <>
                    {/* Printer Type */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>{language === 'ar' ? 'نوع الطابعة' : 'Type d\'imprimante'}</Label>
                        <Select 
                          value={printerSettings.type} 
                          onValueChange={(v) => setPrinterSettings(prev => ({ ...prev, type: v }))}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="thermal">
                              {language === 'ar' ? 'طابعة حرارية (إيصالات)' : 'Thermique (reçus)'}
                            </SelectItem>
                            <SelectItem value="laser">
                              {language === 'ar' ? 'طابعة ليزر' : 'Laser'}
                            </SelectItem>
                            <SelectItem value="inkjet">
                              {language === 'ar' ? 'طابعة حبر' : 'Jet d\'encre'}
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>{language === 'ar' ? 'طريقة الاتصال' : 'Type de connexion'}</Label>
                        <Select 
                          value={printerSettings.connectionType} 
                          onValueChange={(v) => setPrinterSettings(prev => ({ ...prev, connectionType: v }))}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="usb">
                              <div className="flex items-center gap-2">
                                <Cable className="h-4 w-4" />
                                USB
                              </div>
                            </SelectItem>
                            <SelectItem value="network">
                              <div className="flex items-center gap-2">
                                <Wifi className="h-4 w-4" />
                                {language === 'ar' ? 'شبكة (IP)' : 'Réseau (IP)'}
                              </div>
                            </SelectItem>
                            <SelectItem value="bluetooth">
                              <div className="flex items-center gap-2">
                                <Monitor className="h-4 w-4" />
                                Bluetooth
                              </div>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Connection Settings */}
                    {printerSettings.connectionType === 'usb' && (
                      <div>
                        <Label>{language === 'ar' ? 'اسم الطابعة' : 'Nom de l\'imprimante'}</Label>
                        <Input
                          value={printerSettings.name}
                          onChange={(e) => setPrinterSettings(prev => ({ ...prev, name: e.target.value }))}
                          placeholder={language === 'ar' ? 'مثال: POS-58' : 'Ex: POS-58'}
                          className="mt-1"
                        />
                      </div>
                    )}

                    {printerSettings.connectionType === 'network' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>{language === 'ar' ? 'عنوان IP' : 'Adresse IP'}</Label>
                          <Input
                            value={printerSettings.ipAddress}
                            onChange={(e) => setPrinterSettings(prev => ({ ...prev, ipAddress: e.target.value }))}
                            placeholder="192.168.1.100"
                            className="mt-1"
                          />
                        </div>
                        <div>
                          <Label>{language === 'ar' ? 'المنفذ' : 'Port'}</Label>
                          <Input
                            value={printerSettings.port}
                            onChange={(e) => setPrinterSettings(prev => ({ ...prev, port: e.target.value }))}
                            placeholder="9100"
                            className="mt-1"
                          />
                        </div>
                      </div>
                    )}

                    {/* Paper & Print Settings */}
                    {printerSettings.type === 'thermal' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>{language === 'ar' ? 'عرض الورق' : 'Largeur du papier'}</Label>
                          <Select 
                            value={printerSettings.paperWidth} 
                            onValueChange={(v) => setPrinterSettings(prev => ({ ...prev, paperWidth: v }))}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="58">58mm</SelectItem>
                              <SelectItem value="80">80mm</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>{language === 'ar' ? 'عدد النسخ' : 'Nombre de copies'}</Label>
                          <Input
                            type="number"
                            min="1"
                            max="5"
                            value={printerSettings.printCopies}
                            onChange={(e) => setPrinterSettings(prev => ({ ...prev, printCopies: parseInt(e.target.value) || 1 }))}
                            className="mt-1"
                          />
                        </div>
                      </div>
                    )}

                    {/* Auto Print */}
                    <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                      <div>
                        <p className="font-medium">{language === 'ar' ? 'طباعة تلقائية' : 'Impression automatique'}</p>
                        <p className="text-sm text-muted-foreground">
                          {language === 'ar' ? 'طباعة الفاتورة تلقائياً بعد كل عملية بيع' : 'Imprimer automatiquement après chaque vente'}
                        </p>
                      </div>
                      <Switch
                        checked={printerSettings.autoPrint}
                        onCheckedChange={(checked) => setPrinterSettings(prev => ({ ...prev, autoPrint: checked }))}
                      />
                    </div>

                    {/* Test Print Button */}
                    <Button variant="outline" className="gap-2">
                      <Printer className="h-4 w-4" />
                      {language === 'ar' ? 'طباعة اختبارية' : 'Test d\'impression'}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* USB SIM Settings Tab */}
          <TabsContent value="usb" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Usb className="h-5 w-5" />
                  {language === 'ar' ? 'إعدادات شرائح USB' : 'Paramètres SIM USB'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'ربط شرائح الهاتف عبر مفتاح USB لعمليات شحن الرصيد' 
                    : 'Connecter les cartes SIM via clé USB pour les recharges'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Enable USB */}
                <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-blue-100">
                      <Usb className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium">{language === 'ar' ? 'تفعيل USB Modem' : 'Activer USB Modem'}</p>
                      <p className="text-sm text-muted-foreground">
                        {language === 'ar' ? 'استخدام شرائح SIM عبر منفذ USB' : 'Utiliser les cartes SIM via port USB'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={usbSettings.enabled}
                    onCheckedChange={(checked) => setUsbSettings(prev => ({ ...prev, enabled: checked }))}
                  />
                </div>

                {usbSettings.enabled && (
                  <>
                    {/* USB Port Settings */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>{language === 'ar' ? 'منفذ USB' : 'Port USB'}</Label>
                        <Select 
                          value={usbSettings.port} 
                          onValueChange={(v) => setUsbSettings(prev => ({ ...prev, port: v }))}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue placeholder={language === 'ar' ? 'اختر المنفذ' : 'Sélectionner port'} />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="COM1">COM1</SelectItem>
                            <SelectItem value="COM2">COM2</SelectItem>
                            <SelectItem value="COM3">COM3</SelectItem>
                            <SelectItem value="COM4">COM4</SelectItem>
                            <SelectItem value="/dev/ttyUSB0">/dev/ttyUSB0</SelectItem>
                            <SelectItem value="/dev/ttyUSB1">/dev/ttyUSB1</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>{language === 'ar' ? 'سرعة الاتصال' : 'Vitesse baud'}</Label>
                        <Select 
                          value={usbSettings.baudRate} 
                          onValueChange={(v) => setUsbSettings(prev => ({ ...prev, baudRate: v }))}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="9600">9600</SelectItem>
                            <SelectItem value="19200">19200</SelectItem>
                            <SelectItem value="38400">38400</SelectItem>
                            <SelectItem value="115200">115200</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* SIM Slots */}
                    <div className="space-y-4">
                      <Label className="text-lg font-semibold">{language === 'ar' ? 'شرائح SIM' : 'Cartes SIM'}</Label>
                      
                      {usbSettings.simSlots.map((slot, index) => (
                        <div key={slot.id} className="p-4 border rounded-lg space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Smartphone className="h-5 w-5 text-muted-foreground" />
                              <span className="font-medium">
                                {language === 'ar' ? `شريحة ${slot.id}` : `SIM ${slot.id}`}
                              </span>
                            </div>
                            <Switch
                              checked={slot.enabled}
                              onCheckedChange={(checked) => {
                                const newSlots = [...usbSettings.simSlots];
                                newSlots[index].enabled = checked;
                                setUsbSettings(prev => ({ ...prev, simSlots: newSlots }));
                              }}
                            />
                          </div>
                          
                          {slot.enabled && (
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label>{language === 'ar' ? 'المشغل' : 'Opérateur'}</Label>
                                <Select 
                                  value={slot.operator}
                                  onValueChange={(v) => {
                                    const newSlots = [...usbSettings.simSlots];
                                    newSlots[index].operator = v;
                                    setUsbSettings(prev => ({ ...prev, simSlots: newSlots }));
                                  }}
                                >
                                  <SelectTrigger className="mt-1">
                                    <SelectValue placeholder={language === 'ar' ? 'اختر' : 'Choisir'} />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="mobilis">Mobilis</SelectItem>
                                    <SelectItem value="djezzy">Djezzy</SelectItem>
                                    <SelectItem value="ooredoo">Ooredoo</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label>{language === 'ar' ? 'رقم الهاتف' : 'Numéro'}</Label>
                                <Input
                                  value={slot.phone}
                                  onChange={(e) => {
                                    const newSlots = [...usbSettings.simSlots];
                                    newSlots[index].phone = e.target.value;
                                    setUsbSettings(prev => ({ ...prev, simSlots: newSlots }));
                                  }}
                                  placeholder="0555123456"
                                  className="mt-1"
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      ))}

                      {/* Add SIM Button */}
                      <Button 
                        variant="outline" 
                        className="w-full gap-2"
                        onClick={() => {
                          setUsbSettings(prev => ({
                            ...prev,
                            simSlots: [...prev.simSlots, {
                              id: prev.simSlots.length + 1,
                              operator: '',
                              phone: '',
                              enabled: false
                            }]
                          }));
                        }}
                      >
                        <Plus className="h-4 w-4" />
                        {language === 'ar' ? 'إضافة شريحة' : 'Ajouter SIM'}
                      </Button>
                    </div>

                    {/* Test Connection Button */}
                    <Button variant="outline" className="gap-2">
                      <RefreshCw className="h-4 w-4" />
                      {language === 'ar' ? 'اختبار الاتصال' : 'Tester la connexion'}
                    </Button>
                  </>
                )}
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

            {/* System Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  {language === 'ar' ? 'إعدادات عامة' : 'Paramètres généraux'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'تخصيص إعدادات النظام والتنبيهات' 
                    : 'Personnaliser les paramètres du système et les alertes'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Cash Difference Threshold */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      {language === 'ar' ? 'حد تنبيه العجز/الفائض' : 'Seuil d\'alerte écart caisse'}
                    </Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={systemSettings.cash_difference_threshold}
                        onChange={(e) => setSystemSettings(prev => ({ 
                          ...prev, 
                          cash_difference_threshold: parseFloat(e.target.value) || 0 
                        }))}
                        className="w-32"
                      />
                      <span className="text-muted-foreground">{systemSettings.currency_symbol}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {language === 'ar' 
                        ? 'سيتم إرسال إشعار عند تجاوز هذا المبلغ' 
                        : 'Une notification sera envoyée si ce montant est dépassé'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      {language === 'ar' ? 'حد المخزون المنخفض' : 'Seuil de stock bas'}
                    </Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={systemSettings.low_stock_threshold}
                        onChange={(e) => setSystemSettings(prev => ({ 
                          ...prev, 
                          low_stock_threshold: parseInt(e.target.value) || 0 
                        }))}
                        className="w-32"
                      />
                      <span className="text-muted-foreground">{language === 'ar' ? 'وحدة' : 'unités'}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {language === 'ar' 
                        ? 'تنبيه عندما يصل المخزون لهذا الحد' 
                        : 'Alerte quand le stock atteint ce niveau'}
                    </p>
                  </div>
                </div>

                {/* Business Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t">
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'اسم المتجر' : 'Nom du magasin'}</Label>
                    <Input
                      value={systemSettings.business_name}
                      onChange={(e) => setSystemSettings(prev => ({ ...prev, business_name: e.target.value }))}
                      placeholder="NT"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'رمز العملة' : 'Symbole de devise'}</Label>
                    <Input
                      value={systemSettings.currency_symbol}
                      onChange={(e) => setSystemSettings(prev => ({ ...prev, currency_symbol: e.target.value }))}
                      placeholder="دج"
                      className="w-24"
                    />
                  </div>
                </div>

                <Button 
                  onClick={saveSystemSettings} 
                  disabled={savingSystemSettings}
                  className="gap-2"
                >
                  {savingSystemSettings ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  {language === 'ar' ? 'حفظ الإعدادات' : 'Enregistrer'}
                </Button>
              </CardContent>
            </Card>

            {/* Login Page Branding */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5" />
                  {language === 'ar' ? 'تخصيص صفحة الدخول' : 'Personnalisation de la page de connexion'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'تغيير الشعار والاسم والصورة في صفحة تسجيل الدخول' 
                    : 'Modifier le logo, le nom et l\'image sur la page de connexion'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'اسم النظام/المتجر' : 'Nom du système/magasin'}</Label>
                    <Input
                      value={brandingSettings.business_name}
                      onChange={(e) => setBrandingSettings(prev => ({ ...prev, business_name: e.target.value }))}
                      placeholder="NT"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'رابط الشعار (Logo URL)' : 'URL du logo'}</Label>
                    <Input
                      value={brandingSettings.logo_url}
                      onChange={(e) => setBrandingSettings(prev => ({ ...prev, logo_url: e.target.value }))}
                      placeholder="https://example.com/logo.png"
                      dir="ltr"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>{language === 'ar' ? 'رابط صورة الخلفية' : 'URL de l\'image de fond'}</Label>
                  <Input
                    value={brandingSettings.background_image_url}
                    onChange={(e) => setBrandingSettings(prev => ({ ...prev, background_image_url: e.target.value }))}
                    placeholder="https://example.com/background.jpg"
                    dir="ltr"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'الشعار النصي (عربي)' : 'Slogan (arabe)'}</Label>
                    <Input
                      value={brandingSettings.tagline_ar}
                      onChange={(e) => setBrandingSettings(prev => ({ ...prev, tagline_ar: e.target.value }))}
                      placeholder="إدارة مخزون زجاج الحماية بسهولة"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'الشعار النصي (فرنسي)' : 'Slogan (français)'}</Label>
                    <Input
                      value={brandingSettings.tagline_fr}
                      onChange={(e) => setBrandingSettings(prev => ({ ...prev, tagline_fr: e.target.value }))}
                      placeholder="Gestion facile de stock de protection"
                      dir="ltr"
                    />
                  </div>
                </div>

                <Button 
                  onClick={saveBrandingSettings} 
                  disabled={savingBranding}
                  className="gap-2"
                >
                  {savingBranding ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  {language === 'ar' ? 'حفظ إعدادات صفحة الدخول' : 'Enregistrer'}
                </Button>
              </CardContent>
            </Card>

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

        {/* Password Change Dialog */}
        <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                {language === 'ar' ? 'تغيير كلمة المرور' : 'Changer le mot de passe'}
              </DialogTitle>
              <DialogDescription>
                {passwordUser?.name} ({passwordUser?.email})
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <Label>{language === 'ar' ? 'كلمة المرور الجديدة' : 'Nouveau mot de passe'}</Label>
                <Input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={language === 'ar' ? '4 أحرف على الأقل' : '4 caractères minimum'}
                  className="mt-1"
                />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowPasswordDialog(false)} className="flex-1">
                  {t.cancel}
                </Button>
                <Button 
                  onClick={savePassword}
                  disabled={savingPassword || newPassword.length < 4}
                  className="flex-1 gap-2"
                >
                  <Save className="h-4 w-4" />
                  {savingPassword ? t.loading : t.save}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
