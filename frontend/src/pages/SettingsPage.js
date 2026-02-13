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
import { BackupSystem } from '../components/BackupSystem';
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
  EyeOff,
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
  Database,
  Key,
  ImageIcon,
  MessageCircle,
  Mail,
  Send,
  Download,
  Upload,
  HardDrive,
  GripVertical,
  ChevronRight,
  Volume2,
  VolumeX
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
  
  // Selective Delete
  const [showSelectiveDeleteDialog, setShowSelectiveDeleteDialog] = useState(false);
  const [selectedDataTypes, setSelectedDataTypes] = useState([]);
  const [selectiveDeleteCode, setSelectiveDeleteCode] = useState('');
  const [deleting, setDeleting] = useState(false);
  
  // Backup
  const [backupLoading, setBackupLoading] = useState(false);
  const [backupList, setBackupList] = useState([]);
  
  // Permissions
  const [selectedUser, setSelectedUser] = useState(null);
  const [showPermissionsDialog, setShowPermissionsDialog] = useState(false);
  
  // Add New User
  const [showAddUserDialog, setShowAddUserDialog] = useState(false);
  const [newUserData, setNewUserData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'seller'
  });
  const [addingUser, setAddingUser] = useState(false);
  const [showNewUserPassword, setShowNewUserPassword] = useState(false);
  
  // Password Change
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [passwordUser, setPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);
  const [userPermissions, setUserPermissions] = useState({});
  const [savingPermissions, setSavingPermissions] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  
  // Edit User
  const [showEditUserDialog, setShowEditUserDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editUserData, setEditUserData] = useState({
    name: '',
    email: '',
    role: ''
  });
  const [savingEditUser, setSavingEditUser] = useState(false);
  
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

  // Receipt Settings
  const [receiptSettings, setReceiptSettings] = useState({
    auto_print: false,
    show_print_dialog: true,
    default_template_id: 'default_80mm',
    templates: [
      { id: 'default_58mm', name: 'Thermal 58mm', name_ar: 'حراري 58 مم', width: '58mm', show_logo: false, show_header: true, show_footer: true, header_text: '', footer_text: 'شكراً لزيارتكم', font_size: 'small', is_default: false },
      { id: 'default_80mm', name: 'Thermal 80mm', name_ar: 'حراري 80 مم', width: '80mm', show_logo: true, show_header: true, show_footer: true, header_text: '', footer_text: 'شكراً لزيارتكم', font_size: 'normal', is_default: true },
      { id: 'default_a4', name: 'A4 Full Page', name_ar: 'صفحة A4 كاملة', width: 'A4', show_logo: true, show_header: true, show_footer: true, header_text: '', footer_text: 'شكراً لزيارتكم', font_size: 'normal', is_default: false }
    ]
  });
  const [savingReceipt, setSavingReceipt] = useState(false);

  // WhatsApp Settings
  const [whatsappSettings, setWhatsappSettings] = useState({
    enabled: false,
    phone_number_id: '',
    access_token: '',
    business_account_id: ''
  });
  const [savingWhatsapp, setSavingWhatsapp] = useState(false);

  // Sound Settings
  const [soundSettings, setSoundSettings] = useState({
    enabled: true,
    sale_success: true,
    error_sound: true,
    notification_sound: true,
    scan_beep: true,
    volume: 50
  });
  const [savingSoundSettings, setSavingSoundSettings] = useState(false);

  // Email Settings
  const [emailSettings, setEmailSettings] = useState({
    enabled: false,
    resend_api_key: '',
    sender_email: 'onboarding@resend.dev',
    sender_name: 'NT POS System'
  });
  const [savingEmail, setSavingEmail] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);

  useEffect(() => {
    fetchData();
    fetchBackupList();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [usersRes, statsRes, rolesRes, sysSettingsRes, brandingRes, whatsappRes, emailRes, receiptRes] = await Promise.all([
        axios.get(`${API}/users`, { headers }),
        axios.get(`${API}/system/stats`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/permissions/roles`, { headers }),
        axios.get(`${API}/system/settings`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/branding/settings`).catch(() => ({ data: null })),
        axios.get(`${API}/whatsapp/settings`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/email/settings`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/settings/receipt`, { headers }).catch(() => ({ data: null }))
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
      
      if (whatsappRes.data) {
        setWhatsappSettings(prev => ({
          ...prev,
          enabled: whatsappRes.data.enabled || false,
          phone_number_id: whatsappRes.data.phone_number_id || '',
          business_account_id: whatsappRes.data.business_account_id || ''
        }));
      }
      
      if (emailRes.data) {
        setEmailSettings(prev => ({
          ...prev,
          enabled: emailRes.data.enabled || false,
          resend_api_key: emailRes.data.resend_api_key || '',
          sender_email: emailRes.data.sender_email || 'onboarding@resend.dev',
          sender_name: emailRes.data.sender_name || 'NT POS System'
        }));
      }

      if (receiptRes.data) {
        setReceiptSettings(receiptRes.data);
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

  // Backup functions
  const handleDownloadBackup = async () => {
    setBackupLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/backup/create`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backup_${new Date().toISOString().split('T')[0]}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(language === 'ar' ? 'تم تحميل النسخة الاحتياطية' : 'Backup downloaded');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل في تحميل النسخة' : 'Failed to download backup');
    } finally {
      setBackupLoading(false);
    }
  };

  const handleSaveBackupToServer = async () => {
    setBackupLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/backup/save-to-server`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حفظ النسخة على السيرفر' : 'Backup saved to server');
      fetchBackupList();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل في حفظ النسخة' : 'Failed to save backup');
    } finally {
      setBackupLoading(false);
    }
  };

  const handleRestoreBackup = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!window.confirm(language === 'ar' 
      ? 'هل أنت متأكد؟ سيتم استبدال كل البيانات الحالية!' 
      : 'Are you sure? All current data will be replaced!')) {
      e.target.value = '';
      return;
    }
    
    setBackupLoading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);
      
      await axios.post(`${API}/backup/restore`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      toast.success(language === 'ar' ? 'تم استعادة البيانات بنجاح' : 'Data restored successfully');
      window.location.reload();
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل في استعادة البيانات' : 'Failed to restore data');
    } finally {
      setBackupLoading(false);
      e.target.value = '';
    }
  };

  // Edit User
  const openEditUserDialog = (user) => {
    setEditingUser(user);
    setEditUserData({
      name: user.name,
      email: user.email,
      role: user.role
    });
    setShowEditUserDialog(true);
  };

  const saveEditUser = async () => {
    if (!editUserData.name || !editUserData.email) {
      toast.error(language === 'ar' ? 'جميع الحقول مطلوبة' : 'All fields are required');
      return;
    }
    
    setSavingEditUser(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/users/${editingUser.id}`, editUserData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم تحديث المستخدم بنجاح' : 'User updated successfully');
      setShowEditUserDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSavingEditUser(false);
    }
  };

  // Delete User
  const deleteUser = async (userId) => {
    if (!window.confirm(language === 'ar' ? 'هل أنت متأكد من حذف هذا المستخدم؟' : 'Are you sure you want to delete this user?')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حذف المستخدم بنجاح' : 'User deleted successfully');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    }
  };

  const fetchBackupList = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/backup/list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBackupList(response.data);
    } catch (error) {
      console.error('Error fetching backup list:', error);
    }
  };

  // Selective Delete
  const dataTypeOptions = [
    { value: 'sales', label: language === 'ar' ? 'المبيعات' : 'Sales' },
    { value: 'purchases', label: language === 'ar' ? 'المشتريات' : 'Purchases' },
    { value: 'customers', label: language === 'ar' ? 'الزبائن' : 'Customers' },
    { value: 'suppliers', label: language === 'ar' ? 'الموردين' : 'Suppliers' },
    { value: 'products', label: language === 'ar' ? 'المنتجات' : 'Products' },
    { value: 'employees', label: language === 'ar' ? 'الموظفين' : 'Employees' },
    { value: 'debts', label: language === 'ar' ? 'الديون' : 'Debts' },
    { value: 'expenses', label: language === 'ar' ? 'المصاريف' : 'Expenses' },
    { value: 'repairs', label: language === 'ar' ? 'الإصلاحات' : 'Repairs' },
    { value: 'daily_sessions', label: language === 'ar' ? 'الحصص اليومية' : 'Daily Sessions' },
    { value: 'notifications', label: language === 'ar' ? 'الإشعارات' : 'Notifications' },
  ];

  const handleSelectiveDelete = async () => {
    if (selectedDataTypes.length === 0) {
      toast.error(language === 'ar' ? 'اختر نوع بيانات واحد على الأقل' : 'Select at least one data type');
      return;
    }
    if (selectiveDeleteCode !== 'DELETE-SELECTED') {
      toast.error(language === 'ar' ? 'رمز التأكيد غير صحيح' : 'Invalid confirmation code');
      return;
    }
    
    setDeleting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/system/selective-delete`, {
        data_types: selectedDataTypes,
        confirm_code: selectiveDeleteCode
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(language === 'ar' ? 'تم حذف البيانات المحددة' : 'Selected data deleted');
      setShowSelectiveDeleteDialog(false);
      setSelectedDataTypes([]);
      setSelectiveDeleteCode('');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setDeleting(false);
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

  const saveWhatsappSettings = async () => {
    setSavingWhatsapp(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/whatsapp/settings`, whatsappSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حفظ إعدادات WhatsApp' : 'Paramètres WhatsApp enregistrés');
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSavingWhatsapp(false);
    }
  };

  // Save Email Settings
  const saveEmailSettings = async () => {
    setSavingEmail(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/email/settings`, emailSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حفظ إعدادات البريد الإلكتروني' : 'Paramètres email enregistrés');
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSavingEmail(false);
    }
  };

  // Save Receipt Settings
  const saveReceiptSettings = async () => {
    setSavingReceipt(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/settings/receipt`, receiptSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تم حفظ إعدادات الإيصال' : 'Paramètres reçu enregistrés');
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSavingReceipt(false);
    }
  };

  // Test Email Settings
  const testEmailSettings = async () => {
    setTestingEmail(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/email/test`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message || (language === 'ar' ? 'تم إرسال البريد الاختباري' : 'Email test envoyé'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setTestingEmail(false);
    }
  };

  // Add new user/employee
  const handleAddUser = async () => {
    if (!newUserData.name || !newUserData.email || !newUserData.password) {
      toast.error(language === 'ar' ? 'يرجى ملء جميع الحقول' : 'Veuillez remplir tous les champs');
      return;
    }
    
    setAddingUser(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/auth/register`, newUserData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(language === 'ar' ? 'تمت إضافة العامل بنجاح' : 'Employé ajouté avec succès');
      setShowAddUserDialog(false);
      setNewUserData({ name: '', email: '', password: '', role: 'seller' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setAddingUser(false);
    }
  };

  // Available roles - Note: super_admin is NOT available for tenants (security restriction)
  const availableRoles = [
    { value: 'admin', label_ar: 'مدير', label_fr: 'Admin', color: 'bg-red-500', desc_ar: 'صلاحيات كاملة على المتجر', desc_fr: 'Full store access' },
    { value: 'manager', label_ar: 'مشرف', label_fr: 'Manager', color: 'bg-blue-500', desc_ar: 'إدارة العمليات اليومية', desc_fr: 'Daily operations management' },
    { value: 'sales_supervisor', label_ar: 'مشرف مبيعات', label_fr: 'Sales Supervisor', color: 'bg-teal-500', desc_ar: 'إشراف على المبيعات والعملاء', desc_fr: 'Sales and customer oversight' },
    { value: 'seller', label_ar: 'بائع', label_fr: 'Vendeur', color: 'bg-green-500', desc_ar: 'عمليات البيع الأساسية فقط', desc_fr: 'Basic sales operations only' },
    { value: 'inventory_manager', label_ar: 'مدير مخزون', label_fr: 'Inventory Manager', color: 'bg-orange-500', desc_ar: 'إدارة المخزون والمشتريات', desc_fr: 'Stock and purchase management' },
    { value: 'ecommerce_manager', label_ar: 'مسؤول متجر إلكتروني', label_fr: 'E-commerce Manager', color: 'bg-indigo-500', desc_ar: 'إدارة المتجر الإلكتروني', desc_fr: 'Online store management' },
    { value: 'accountant', label_ar: 'محاسب', label_fr: 'Comptable', color: 'bg-amber-500', desc_ar: 'التقارير المالية والديون والمصاريف', desc_fr: 'Financial reports, debts, and expenses' },
    { value: 'user', label_ar: 'مستخدم عادي', label_fr: 'Utilisateur', color: 'bg-gray-500', desc_ar: 'عرض فقط', desc_fr: 'View only' },
  ];

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
    { key: 'dashboard', label: language === 'ar' ? 'لوحة التحكم' : 'Dashboard', simple: true, group: 'general' },
    { key: 'pos', label: language === 'ar' ? 'نقطة البيع' : 'POS', simple: true, group: 'sales' },
    { key: 'products', label: language === 'ar' ? 'المنتجات' : 'Products', simple: false, actions: ['view', 'add', 'edit', 'delete', 'price_change', 'stock_adjust'], group: 'inventory' },
    { key: 'inventory', label: language === 'ar' ? 'المخزون' : 'Inventory', simple: false, actions: ['view', 'add', 'edit', 'delete', 'transfer', 'count'], group: 'inventory' },
    { key: 'purchases', label: language === 'ar' ? 'المشتريات' : 'Purchases', simple: false, actions: ['view', 'add', 'edit', 'delete', 'approve'], group: 'inventory' },
    { key: 'sales', label: language === 'ar' ? 'المبيعات' : 'Sales', simple: false, actions: ['view', 'add', 'edit', 'delete', 'refund', 'discount'], group: 'sales' },
    { key: 'customers', label: language === 'ar' ? 'الزبائن' : 'Customers', simple: false, actions: ['view', 'add', 'edit', 'delete', 'credit', 'blacklist'], group: 'sales' },
    { key: 'suppliers', label: language === 'ar' ? 'الموردين' : 'Suppliers', simple: false, actions: ['view', 'add', 'edit', 'delete', 'payments'], group: 'inventory' },
    { key: 'employees', label: language === 'ar' ? 'الموظفين' : 'Employees', simple: false, actions: ['view', 'add', 'edit', 'delete', 'salary', 'attendance'], group: 'hr' },
    { key: 'debts', label: language === 'ar' ? 'الديون' : 'Debts', simple: false, actions: ['view', 'add', 'edit', 'delete', 'collect'], group: 'financial' },
    { key: 'expenses', label: language === 'ar' ? 'المصاريف' : 'Expenses', simple: false, actions: ['view', 'add', 'edit', 'delete', 'approve'], group: 'financial' },
    { key: 'reports', label: language === 'ar' ? 'التقارير' : 'Reports', simple: false, actions: ['sales', 'inventory', 'financial', 'customers', 'employees', 'advanced'], group: 'general' },
    { key: 'users', label: language === 'ar' ? 'المستخدمين' : 'Users', simple: false, actions: ['view', 'add', 'edit', 'delete', 'permissions'], group: 'system' },
    { key: 'recharge', label: language === 'ar' ? 'شحن الرصيد' : 'Recharge', simple: true, group: 'services' },
    { key: 'settings', label: language === 'ar' ? 'الإعدادات' : 'Settings', simple: true, group: 'system' },
    { key: 'api_keys', label: language === 'ar' ? 'مفاتيح API' : 'API Keys', simple: true, group: 'system' },
    { key: 'factory_reset', label: language === 'ar' ? 'ضبط المصنع' : 'Factory Reset', simple: true, group: 'system' },
    { key: 'woocommerce', label: 'WooCommerce', simple: true, group: 'services' },
    { key: 'delivery', label: language === 'ar' ? 'التوصيل' : 'Delivery', simple: true, group: 'services' },
    { key: 'loyalty', label: language === 'ar' ? 'برنامج الولاء' : 'Loyalty', simple: true, group: 'services' },
    { key: 'notifications', label: language === 'ar' ? 'الإشعارات' : 'Notifications', simple: true, group: 'services' },
    { key: 'maintenance', label: language === 'ar' ? 'الصيانة' : 'Maintenance', simple: true, group: 'services' },
  ];

  // Group permissions by category
  const permissionGroups = {
    general: { label_ar: 'عام', label_fr: 'Général', icon: '📊' },
    sales: { label_ar: 'عمليات البيع', label_fr: 'Ventes', icon: '🛒' },
    inventory: { label_ar: 'المخزون والمشتريات', label_fr: 'Inventaire', icon: '📦' },
    financial: { label_ar: 'المالية', label_fr: 'Finances', icon: '💰' },
    hr: { label_ar: 'الموارد البشرية', label_fr: 'RH', icon: '👥' },
    services: { label_ar: 'الخدمات', label_fr: 'Services', icon: '⚙️' },
    system: { label_ar: 'إدارة النظام', label_fr: 'Système', icon: '🔧' }
  };

  const actionLabels = {
    view: { ar: 'عرض', fr: 'Voir' },
    add: { ar: 'إضافة', fr: 'Ajouter' },
    edit: { ar: 'تعديل', fr: 'Modifier' },
    delete: { ar: 'حذف', fr: 'Supprimer' },
    price_change: { ar: 'تغيير السعر', fr: 'Changer prix' },
    stock_adjust: { ar: 'تعديل المخزون', fr: 'Ajuster stock' },
    transfer: { ar: 'نقل', fr: 'Transférer' },
    count: { ar: 'جرد', fr: 'Inventaire' },
    approve: { ar: 'موافقة', fr: 'Approuver' },
    refund: { ar: 'استرجاع', fr: 'Remboursement' },
    discount: { ar: 'خصم', fr: 'Remise' },
    credit: { ar: 'آجل', fr: 'Crédit' },
    blacklist: { ar: 'قائمة سوداء', fr: 'Blacklist' },
    payments: { ar: 'مدفوعات', fr: 'Paiements' },
    salary: { ar: 'راتب', fr: 'Salaire' },
    attendance: { ar: 'حضور', fr: 'Présence' },
    collect: { ar: 'تحصيل', fr: 'Collecter' },
    permissions: { ar: 'صلاحيات', fr: 'Permissions' },
    sales: { ar: 'مبيعات', fr: 'Ventes' },
    inventory: { ar: 'مخزون', fr: 'Stock' },
    financial: { ar: 'مالية', fr: 'Finances' },
    customers: { ar: 'زبائن', fr: 'Clients' },
    employees: { ar: 'موظفين', fr: 'Employés' },
    advanced: { ar: 'متقدمة', fr: 'Avancé' }
  };

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
          <TabsList className="grid w-full max-w-4xl grid-cols-7">
            <TabsTrigger value="permissions" className="gap-2">
              <Shield className="h-4 w-4" />
              {t.permissions}
            </TabsTrigger>
            <TabsTrigger value="backup" className="gap-2">
              <Database className="h-4 w-4" />
              {language === 'ar' ? 'النسخ الاحتياطي' : 'Sauvegarde'}
            </TabsTrigger>
            <TabsTrigger value="whatsapp" className="gap-2">
              <MessageCircle className="h-4 w-4" />
              WhatsApp
            </TabsTrigger>
            <TabsTrigger value="printer" className="gap-2">
              <Printer className="h-4 w-4" />
              {language === 'ar' ? 'الطابعة' : 'Imprimante'}
            </TabsTrigger>
            <TabsTrigger value="usb" className="gap-2">
              <Usb className="h-4 w-4" />
              {language === 'ar' ? 'شرائح USB' : 'SIM USB'}
            </TabsTrigger>
            <TabsTrigger value="email" className="gap-2">
              <Mail className="h-4 w-4" />
              {language === 'ar' ? 'البريد' : 'Email'}
            </TabsTrigger>
            <TabsTrigger value="system" className="gap-2">
              <Settings className="h-4 w-4" />
              {language === 'ar' ? 'النظام' : 'Système'}
            </TabsTrigger>
          </TabsList>

          {/* Backup Tab */}
          <TabsContent value="backup" className="space-y-6">
            <BackupSystem />
          </TabsContent>

          {/* Permissions Tab */}
          <TabsContent value="permissions" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      {t.userPermissions}
                    </CardTitle>
                    <CardDescription>
                      {language === 'ar' ? 'إدارة المستخدمين وصلاحياتهم' : 'Gérer les utilisateurs et leurs permissions'}
                    </CardDescription>
                  </div>
                  <Button onClick={() => setShowAddUserDialog(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    {language === 'ar' ? 'إضافة عامل' : 'Ajouter'}
                  </Button>
                </div>
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
                            u.role === 'admin' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                            u.role === 'super_admin' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' :
                            u.role === 'manager' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                            u.role === 'seller' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            u.role === 'sales_supervisor' ? 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400' :
                            u.role === 'inventory_manager' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                            u.role === 'ecommerce_manager' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' :
                            u.role === 'accountant' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                            'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                          }`}>
                            {u.role === 'super_admin' ? (language === 'ar' ? 'سوبر أدمين' : 'Super Admin') :
                             u.role === 'admin' ? (language === 'ar' ? 'مدير' : 'Admin') :
                             u.role === 'manager' ? (language === 'ar' ? 'مشرف' : 'Manager') :
                             u.role === 'seller' ? (language === 'ar' ? 'بائع' : 'Vendeur') :
                             u.role === 'sales_supervisor' ? (language === 'ar' ? 'مشرف مبيعات' : 'Sales Supervisor') :
                             u.role === 'inventory_manager' ? (language === 'ar' ? 'مدير مخزون' : 'Inventory Manager') :
                             u.role === 'ecommerce_manager' ? (language === 'ar' ? 'مسؤول متجر' : 'E-commerce') :
                             u.role === 'accountant' ? (language === 'ar' ? 'محاسب' : 'Comptable') :
                             (language === 'ar' ? 'مستخدم' : 'User')}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => openEditUserDialog(u)}
                              title={language === 'ar' ? 'تعديل' : 'Edit'}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => openPermissionsDialog(u.id)}
                              disabled={u.id === user?.id}
                              title={t.permissions}
                            >
                              <Shield className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => openPasswordDialog(u)}
                              title={language === 'ar' ? 'كلمة المرور' : 'Password'}
                            >
                              <Key className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive"
                              onClick={() => deleteUser(u.id)}
                              disabled={u.id === user?.id || u.role === 'super_admin'}
                              title={language === 'ar' ? 'حذف' : 'Delete'}
                            >
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

          {/* WhatsApp Settings Tab */}
          <TabsContent value="whatsapp" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="h-5 w-5 text-green-600" />
                  {language === 'ar' ? 'إعدادات WhatsApp Business' : 'Paramètres WhatsApp Business'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'قم بربط حسابك في WhatsApp Business لإرسال إشعارات تلقائية للعملاء'
                    : 'Connectez votre compte WhatsApp Business pour envoyer des notifications automatiques'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-full ${whatsappSettings.enabled ? 'bg-green-100' : 'bg-gray-100'}`}>
                      <MessageCircle className={`h-5 w-5 ${whatsappSettings.enabled ? 'text-green-600' : 'text-gray-400'}`} />
                    </div>
                    <div>
                      <p className="font-medium">
                        {language === 'ar' ? 'تفعيل إشعارات WhatsApp' : 'Activer les notifications WhatsApp'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {language === 'ar' ? 'إرسال إشعارات تلقائية عند تغيير حالة الصيانة' : 'Envoyer des notifications automatiques lors du changement de statut'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={whatsappSettings.enabled}
                    onCheckedChange={(checked) => setWhatsappSettings(prev => ({ ...prev, enabled: checked }))}
                  />
                </div>

                {whatsappSettings.enabled && (
                  <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label>{language === 'ar' ? 'Phone Number ID' : 'Phone Number ID'}</Label>
                        <Input
                          placeholder="123456789012345"
                          value={whatsappSettings.phone_number_id}
                          onChange={(e) => setWhatsappSettings(prev => ({ ...prev, phone_number_id: e.target.value }))}
                        />
                        <p className="text-xs text-muted-foreground">
                          {language === 'ar' ? 'تجده في Meta Business Suite' : 'Trouvable dans Meta Business Suite'}
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label>{language === 'ar' ? 'Business Account ID' : 'Business Account ID'}</Label>
                        <Input
                          placeholder="123456789012345"
                          value={whatsappSettings.business_account_id}
                          onChange={(e) => setWhatsappSettings(prev => ({ ...prev, business_account_id: e.target.value }))}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>{language === 'ar' ? 'Access Token' : 'Access Token'}</Label>
                      <Input
                        type="password"
                        placeholder="EAAxxxxxxx..."
                        value={whatsappSettings.access_token}
                        onChange={(e) => setWhatsappSettings(prev => ({ ...prev, access_token: e.target.value }))}
                      />
                      <p className="text-xs text-muted-foreground">
                        {language === 'ar' 
                          ? 'احصل على Access Token من Meta for Developers > WhatsApp > API Setup'
                          : 'Obtenez le Access Token depuis Meta for Developers > WhatsApp > API Setup'}
                      </p>
                    </div>
                    
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                        {language === 'ar' ? '📋 خطوات الإعداد:' : '📋 Étapes de configuration:'}
                      </h4>
                      <ol className="text-sm text-blue-700 dark:text-blue-300 space-y-1 list-decimal list-inside">
                        <li>{language === 'ar' ? 'انتقل إلى developers.facebook.com' : 'Allez sur developers.facebook.com'}</li>
                        <li>{language === 'ar' ? 'أنشئ تطبيق Business جديد' : 'Créez une nouvelle application Business'}</li>
                        <li>{language === 'ar' ? 'أضف WhatsApp product' : 'Ajoutez le produit WhatsApp'}</li>
                        <li>{language === 'ar' ? 'انسخ Phone Number ID و Access Token' : 'Copiez le Phone Number ID et Access Token'}</li>
                      </ol>
                    </div>
                  </div>
                )}

                <div className="flex justify-end">
                  <Button onClick={saveWhatsappSettings} disabled={savingWhatsapp}>
                    {savingWhatsapp ? (
                      <RefreshCw className="h-4 w-4 me-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 me-2" />
                    )}
                    {language === 'ar' ? 'حفظ الإعدادات' : 'Enregistrer'}
                  </Button>
                </div>
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

            {/* Receipt Settings Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Printer className="h-5 w-5 text-purple-600" />
                  {language === 'ar' ? 'إعدادات الإيصال' : 'Paramètres du reçu'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'تخصيص شكل الإيصال وخيارات الطباعة بعد البيع' 
                    : 'Personnaliser le format du reçu et les options d\'impression après vente'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Auto Print After Sale */}
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-green-100">
                      <Printer className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium text-green-800">{language === 'ar' ? 'طباعة تلقائية بعد البيع' : 'Impression auto après vente'}</p>
                      <p className="text-sm text-green-600">
                        {language === 'ar' ? 'طباعة الإيصال مباشرة بدون سؤال' : 'Imprimer le reçu directement sans confirmation'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={receiptSettings.auto_print}
                    onCheckedChange={(checked) => setReceiptSettings(prev => ({ ...prev, auto_print: checked }))}
                  />
                </div>

                {/* Show Print Dialog */}
                <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-blue-100">
                      <Eye className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-blue-800">{language === 'ar' ? 'عرض حوار الطباعة' : 'Afficher dialogue d\'impression'}</p>
                      <p className="text-sm text-blue-600">
                        {language === 'ar' ? 'إظهار خيار طباعة/تخطي بعد كل بيع' : 'Afficher l\'option imprimer/passer après chaque vente'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={receiptSettings.show_print_dialog}
                    onCheckedChange={(checked) => setReceiptSettings(prev => ({ ...prev, show_print_dialog: checked }))}
                    disabled={receiptSettings.auto_print}
                  />
                </div>

                {/* Default Template */}
                <div>
                  <Label>{language === 'ar' ? 'قالب الإيصال الافتراضي' : 'Modèle de reçu par défaut'}</Label>
                  <Select 
                    value={receiptSettings.default_template_id} 
                    onValueChange={(v) => setReceiptSettings(prev => ({ ...prev, default_template_id: v }))}
                  >
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {receiptSettings.templates?.map(template => (
                        <SelectItem key={template.id} value={template.id}>
                          <div className="flex items-center gap-2">
                            <span>{language === 'ar' ? template.name_ar : template.name}</span>
                            <span className="text-xs text-muted-foreground">({template.width})</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Templates List */}
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{language === 'ar' ? 'القالب' : 'Modèle'}</TableHead>
                        <TableHead className="text-center">{language === 'ar' ? 'الحجم' : 'Taille'}</TableHead>
                        <TableHead className="text-center">{language === 'ar' ? 'الشعار' : 'Logo'}</TableHead>
                        <TableHead className="text-center">{language === 'ar' ? 'الترويسة' : 'En-tête'}</TableHead>
                        <TableHead className="text-center">{language === 'ar' ? 'التذييل' : 'Pied'}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {receiptSettings.templates?.map((template, idx) => (
                        <TableRow key={template.id} className={template.id === receiptSettings.default_template_id ? 'bg-primary/5' : ''}>
                          <TableCell className="font-medium">
                            {language === 'ar' ? template.name_ar : template.name}
                            {template.id === receiptSettings.default_template_id && (
                              <span className="ms-2 text-xs text-primary">{language === 'ar' ? '(افتراضي)' : '(défaut)'}</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="px-2 py-1 bg-muted rounded text-xs font-mono">{template.width}</span>
                          </TableCell>
                          <TableCell className="text-center">
                            <Switch
                              checked={template.show_logo}
                              onCheckedChange={(checked) => {
                                const newTemplates = [...receiptSettings.templates];
                                newTemplates[idx].show_logo = checked;
                                setReceiptSettings(prev => ({ ...prev, templates: newTemplates }));
                              }}
                            />
                          </TableCell>
                          <TableCell className="text-center">
                            <Switch
                              checked={template.show_header}
                              onCheckedChange={(checked) => {
                                const newTemplates = [...receiptSettings.templates];
                                newTemplates[idx].show_header = checked;
                                setReceiptSettings(prev => ({ ...prev, templates: newTemplates }));
                              }}
                            />
                          </TableCell>
                          <TableCell className="text-center">
                            <Switch
                              checked={template.show_footer}
                              onCheckedChange={(checked) => {
                                const newTemplates = [...receiptSettings.templates];
                                newTemplates[idx].show_footer = checked;
                                setReceiptSettings(prev => ({ ...prev, templates: newTemplates }));
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {/* Footer Text */}
                <div>
                  <Label>{language === 'ar' ? 'نص التذييل (يظهر في أسفل الإيصال)' : 'Texte de pied (affiché en bas du reçu)'}</Label>
                  <Input
                    value={receiptSettings.templates?.find(t => t.id === receiptSettings.default_template_id)?.footer_text || ''}
                    onChange={(e) => {
                      const newTemplates = receiptSettings.templates.map(t => 
                        t.id === receiptSettings.default_template_id 
                          ? { ...t, footer_text: e.target.value }
                          : t
                      );
                      setReceiptSettings(prev => ({ ...prev, templates: newTemplates }));
                    }}
                    placeholder={language === 'ar' ? 'شكراً لزيارتكم' : 'Merci pour votre visite'}
                    className="mt-2"
                  />
                </div>

                {/* Save Button */}
                <Button onClick={saveReceiptSettings} disabled={savingReceipt} className="gap-2">
                  {savingReceipt ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  {language === 'ar' ? 'حفظ إعدادات الإيصال' : 'Enregistrer paramètres reçu'}
                </Button>
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

          {/* Email Settings Tab */}
          <TabsContent value="email" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-blue-600" />
                  {language === 'ar' ? 'إعدادات البريد الإلكتروني' : 'Paramètres Email'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'إعداد البريد الإلكتروني لإرسال التقارير والإشعارات'
                    : 'Configurer l\'email pour l\'envoi de rapports et notifications'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Enable Email */}
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-full ${emailSettings.enabled ? 'bg-blue-100' : 'bg-gray-100'}`}>
                      <Mail className={`h-5 w-5 ${emailSettings.enabled ? 'text-blue-600' : 'text-gray-400'}`} />
                    </div>
                    <div>
                      <p className="font-medium">
                        {language === 'ar' ? 'تفعيل البريد الإلكتروني' : 'Activer l\'email'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {language === 'ar' ? 'إرسال تقارير الحصص والإشعارات بالبريد' : 'Envoyer les rapports et notifications par email'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={emailSettings.enabled}
                    onCheckedChange={(checked) => setEmailSettings(prev => ({ ...prev, enabled: checked }))}
                  />
                </div>

                {emailSettings.enabled && (
                  <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
                    {/* Resend API Key */}
                    <div className="space-y-2">
                      <Label>{language === 'ar' ? 'مفتاح Resend API' : 'Clé API Resend'}</Label>
                      <Input
                        type="password"
                        placeholder="re_xxxxxxxx..."
                        value={emailSettings.resend_api_key}
                        onChange={(e) => setEmailSettings(prev => ({ ...prev, resend_api_key: e.target.value }))}
                        dir="ltr"
                      />
                      <p className="text-xs text-muted-foreground">
                        {language === 'ar' 
                          ? 'احصل على مفتاح API من resend.com/api-keys'
                          : 'Obtenez votre clé API sur resend.com/api-keys'}
                      </p>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      {/* Sender Email */}
                      <div className="space-y-2">
                        <Label>{language === 'ar' ? 'بريد المرسل' : 'Email expéditeur'}</Label>
                        <Input
                          type="email"
                          placeholder="noreply@yourdomain.com"
                          value={emailSettings.sender_email}
                          onChange={(e) => setEmailSettings(prev => ({ ...prev, sender_email: e.target.value }))}
                          dir="ltr"
                        />
                      </div>

                      {/* Sender Name */}
                      <div className="space-y-2">
                        <Label>{language === 'ar' ? 'اسم المرسل' : 'Nom expéditeur'}</Label>
                        <Input
                          placeholder="NT POS System"
                          value={emailSettings.sender_name}
                          onChange={(e) => setEmailSettings(prev => ({ ...prev, sender_name: e.target.value }))}
                        />
                      </div>
                    </div>

                    {/* Setup Instructions */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                        {language === 'ar' ? '📋 خطوات الإعداد:' : '📋 Étapes de configuration:'}
                      </h4>
                      <ol className="text-sm text-blue-700 dark:text-blue-300 space-y-1 list-decimal list-inside">
                        <li>{language === 'ar' ? 'أنشئ حساب على resend.com' : 'Créez un compte sur resend.com'}</li>
                        <li>{language === 'ar' ? 'انتقل إلى API Keys وأنشئ مفتاح جديد' : 'Allez sur API Keys et créez une nouvelle clé'}</li>
                        <li>{language === 'ar' ? 'انسخ المفتاح والصقه هنا' : 'Copiez la clé et collez-la ici'}</li>
                        <li>{language === 'ar' ? 'أضف نطاقك (Domain) للحصول على بريد مخصص' : 'Ajoutez votre domaine pour un email personnalisé'}</li>
                      </ol>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 justify-end">
                  {emailSettings.enabled && emailSettings.resend_api_key && (
                    <Button variant="outline" onClick={testEmailSettings} disabled={testingEmail}>
                      {testingEmail ? (
                        <RefreshCw className="h-4 w-4 me-2 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4 me-2" />
                      )}
                      {language === 'ar' ? 'إرسال اختباري' : 'Test email'}
                    </Button>
                  )}
                  <Button onClick={saveEmailSettings} disabled={savingEmail}>
                    {savingEmail ? (
                      <RefreshCw className="h-4 w-4 me-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 me-2" />
                    )}
                    {language === 'ar' ? 'حفظ الإعدادات' : 'Enregistrer'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Email Usage Guide */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  {language === 'ar' ? '📧 استخدامات البريد الإلكتروني' : '📧 Utilisations de l\'email'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium flex items-center gap-2 mb-2">
                      📊 {language === 'ar' ? 'تقارير الحصص' : 'Rapports de session'}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {language === 'ar' 
                        ? 'إرسال تقرير مفصل عند إغلاق كل حصة يومية يتضمن المبيعات والديون والفروقات'
                        : 'Envoyer un rapport détaillé à la clôture de chaque session avec ventes, dettes et écarts'}
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium flex items-center gap-2 mb-2">
                      ⏰ {language === 'ar' ? 'تنبيهات المصروفات' : 'Alertes dépenses'}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {language === 'ar' 
                        ? 'تنبيهات تلقائية قبل مواعيد دفع المصروفات المتكررة مثل الإيجار'
                        : 'Alertes automatiques avant les échéances des dépenses récurrentes'}
                    </p>
                  </div>
                </div>
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
                {/* Sidebar Order Link */}
                <div className="p-4 border rounded-lg bg-primary/5 hover:bg-primary/10 transition-colors">
                  <a href="/settings/sidebar" className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-primary/10">
                        <GripVertical className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">
                          {language === 'ar' ? 'ترتيب القائمة الجانبية' : 'Organiser le menu latéral'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {language === 'ar' ? 'اسحب وأفلت لتغيير ترتيب العناصر' : 'Glisser-déposer pour réorganiser'}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </a>
                </div>

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
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button 
                    variant="destructive" 
                    onClick={() => setShowResetDialog(true)}
                    className="gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    {t.factoryReset}
                  </Button>
                  <Button 
                    variant="outline" 
                    className="gap-2 border-amber-500 text-amber-600 hover:bg-amber-50"
                    onClick={() => setShowSelectiveDeleteDialog(true)}
                  >
                    <Trash2 className="h-4 w-4" />
                    {language === 'ar' ? 'حذف انتقائي' : 'Suppression sélective'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Backup & Restore */}
            <Card className="border-blue-200 dark:border-blue-900">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-600">
                  <Database className="h-5 w-5" />
                  {language === 'ar' ? 'النسخ الاحتياطي واستعادة البيانات' : 'Backup & Restore'}
                </CardTitle>
                <CardDescription>
                  {language === 'ar' 
                    ? 'حفظ نسخة احتياطية من قاعدة البيانات أو استعادتها' 
                    : 'Save or restore a backup of the database'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Button 
                    variant="outline" 
                    className="gap-2"
                    onClick={handleDownloadBackup}
                    disabled={backupLoading}
                  >
                    {backupLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                    {language === 'ar' ? 'تحميل نسخة احتياطية' : 'Download Backup'}
                  </Button>
                  <Button 
                    variant="outline" 
                    className="gap-2"
                    onClick={handleSaveBackupToServer}
                    disabled={backupLoading}
                  >
                    {backupLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <HardDrive className="h-4 w-4" />}
                    {language === 'ar' ? 'حفظ على السيرفر' : 'Save to Server'}
                  </Button>
                  <label className="cursor-pointer">
                    <input 
                      type="file" 
                      accept=".json" 
                      className="hidden" 
                      onChange={handleRestoreBackup}
                      disabled={backupLoading}
                    />
                    <Button 
                      variant="outline" 
                      className="gap-2 pointer-events-none"
                      disabled={backupLoading}
                    >
                      <Upload className="h-4 w-4" />
                      {language === 'ar' ? 'استعادة من ملف' : 'Restore from File'}
                    </Button>
                  </label>
                </div>
                
                {/* Backup History */}
                {backupList.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <h4 className="font-medium mb-2">{language === 'ar' ? 'النسخ الاحتياطية المحفوظة' : 'Saved Backups'}</h4>
                    <div className="space-y-2 max-h-40 overflow-auto">
                      {backupList.map((backup) => (
                        <div key={backup.id} className="flex items-center justify-between p-2 bg-muted rounded-lg text-sm">
                          <span>{backup.filename}</span>
                          <span className="text-muted-foreground">{new Date(backup.created_at).toLocaleDateString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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
                <div className="relative mt-1">
                  <Input
                    type={showChangePassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder={language === 'ar' ? '4 أحرف على الأقل' : '4 caractères minimum'}
                    className="pe-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowChangePassword(!showChangePassword)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                  >
                    {showChangePassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
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

        {/* Add User Dialog */}
        <Dialog open={showAddUserDialog} onOpenChange={setShowAddUserDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5 text-primary" />
                {language === 'ar' ? 'إضافة عامل جديد' : 'Ajouter un employé'}
              </DialogTitle>
              <DialogDescription>
                {language === 'ar' ? 'أدخل بيانات العامل الجديد' : 'Entrez les informations du nouvel employé'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'الاسم الكامل *' : 'Nom complet *'}</Label>
                <Input
                  value={newUserData.name}
                  onChange={(e) => setNewUserData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder={language === 'ar' ? 'اسم العامل' : 'Nom de l\'employé'}
                />
              </div>

              <div className="space-y-2">
                <Label>{language === 'ar' ? 'البريد الإلكتروني *' : 'Email *'}</Label>
                <Input
                  type="email"
                  value={newUserData.email}
                  onChange={(e) => setNewUserData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="employee@example.com"
                />
              </div>

              <div className="space-y-2">
                <Label>{language === 'ar' ? 'كلمة المرور *' : 'Mot de passe *'}</Label>
                <div className="relative">
                  <Input
                    type={showNewUserPassword ? 'text' : 'password'}
                    value={newUserData.password}
                    onChange={(e) => setNewUserData(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="••••••••"
                    className="pe-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewUserPassword(!showNewUserPassword)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                  >
                    {showNewUserPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>{language === 'ar' ? 'الدور الوظيفي *' : 'Rôle *'}</Label>
                <Select 
                  value={newUserData.role} 
                  onValueChange={(v) => setNewUserData(prev => ({ ...prev, role: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRoles.map(role => (
                      <SelectItem key={role.value} value={role.value}>
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${role.color}`}></span>
                          {language === 'ar' ? role.label_ar : role.label_fr}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Role description */}
              {newUserData.role && (
                <div className="p-3 bg-muted rounded-lg text-sm">
                  <p className="font-medium mb-1">{language === 'ar' ? 'وصف الدور:' : 'Description du rôle:'}</p>
                  <p className="text-muted-foreground">
                    {availableRoles.find(r => r.value === newUserData.role)?.[language === 'ar' ? 'desc_ar' : 'desc_fr']}
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => {
                    setShowAddUserDialog(false);
                    setNewUserData({ name: '', email: '', password: '', role: 'seller' });
                  }}
                >
                  {language === 'ar' ? 'إلغاء' : 'Annuler'}
                </Button>
                <Button 
                  className="flex-1"
                  onClick={handleAddUser}
                  disabled={addingUser || !newUserData.name || !newUserData.email || !newUserData.password}
                >
                  {addingUser ? (
                    <RefreshCw className="h-4 w-4 animate-spin me-2" />
                  ) : (
                    <Plus className="h-4 w-4 me-2" />
                  )}
                  {language === 'ar' ? 'إضافة' : 'Ajouter'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Edit User Dialog */}
        <Dialog open={showEditUserDialog} onOpenChange={setShowEditUserDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit2 className="h-5 w-5 text-primary" />
                {language === 'ar' ? 'تعديل بيانات المستخدم' : 'Edit User'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'الاسم الكامل' : 'Full Name'}</Label>
                <Input
                  value={editUserData.name}
                  onChange={(e) => setEditUserData(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label>{language === 'ar' ? 'البريد الإلكتروني' : 'Email'}</Label>
                <Input
                  type="email"
                  value={editUserData.email}
                  onChange={(e) => setEditUserData(prev => ({ ...prev, email: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label>{language === 'ar' ? 'الدور الوظيفي' : 'Role'}</Label>
                <Select 
                  value={editUserData.role} 
                  onValueChange={(v) => setEditUserData(prev => ({ ...prev, role: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRoles.map(role => (
                      <SelectItem key={role.value} value={role.value}>
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${role.color}`}></span>
                          {language === 'ar' ? role.label_ar : role.label_fr}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => setShowEditUserDialog(false)}
                >
                  {language === 'ar' ? 'إلغاء' : 'Cancel'}
                </Button>
                <Button 
                  className="flex-1"
                  onClick={saveEditUser}
                  disabled={savingEditUser}
                >
                  {savingEditUser ? (
                    <RefreshCw className="h-4 w-4 animate-spin me-2" />
                  ) : (
                    <Save className="h-4 w-4 me-2" />
                  )}
                  {language === 'ar' ? 'حفظ التغييرات' : 'Save Changes'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Selective Delete Dialog */}
        <Dialog open={showSelectiveDeleteDialog} onOpenChange={setShowSelectiveDeleteDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-amber-600">
                <Trash2 className="h-5 w-5" />
                {language === 'ar' ? 'حذف انتقائي للبيانات' : 'Selective Data Deletion'}
              </DialogTitle>
              <DialogDescription>
                {language === 'ar' 
                  ? 'اختر أنواع البيانات التي تريد حذفها' 
                  : 'Select the data types you want to delete'}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 max-h-64 overflow-auto p-1">
                {dataTypeOptions.map((option) => (
                  <label 
                    key={option.value} 
                    className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                      selectedDataTypes.includes(option.value) 
                        ? 'bg-amber-50 border-amber-500 dark:bg-amber-900/20' 
                        : 'hover:bg-muted'
                    }`}
                  >
                    <Checkbox
                      checked={selectedDataTypes.includes(option.value)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedDataTypes(prev => [...prev, option.value]);
                        } else {
                          setSelectedDataTypes(prev => prev.filter(v => v !== option.value));
                        }
                      }}
                    />
                    <span className="text-sm">{option.label}</span>
                  </label>
                ))}
              </div>
              
              <div>
                <Label>{language === 'ar' ? 'رمز التأكيد' : 'Confirmation Code'}</Label>
                <Input
                  value={selectiveDeleteCode}
                  onChange={(e) => setSelectiveDeleteCode(e.target.value)}
                  placeholder="DELETE-SELECTED"
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {language === 'ar' ? 'اكتب' : 'Type'}: <code className="bg-muted px-1 rounded">DELETE-SELECTED</code>
                </p>
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowSelectiveDeleteDialog(false);
                    setSelectedDataTypes([]);
                    setSelectiveDeleteCode('');
                  }} 
                  className="flex-1"
                >
                  {t.cancel}
                </Button>
                <Button 
                  variant="destructive" 
                  onClick={handleSelectiveDelete}
                  disabled={deleting || selectedDataTypes.length === 0 || selectiveDeleteCode !== 'DELETE-SELECTED'}
                  className="flex-1 gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  {deleting ? t.loading : (language === 'ar' ? 'حذف المحدد' : 'Delete Selected')}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
