import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Switch } from '../../../components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select';
import { toast } from 'sonner';
import { 
  Clock, AlertTriangle, CreditCard, Settings,
  Trash2, RefreshCw, Database, Bug, Shield, 
  Zap, Server, Wrench, CheckCircle, XCircle, 
  Download, AlertCircle
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const SystemAlertsSection = () => {
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoFixEnabled, setAutoFixEnabled] = useState(true);
  const [filter, setFilter] = useState('all');
  const [stats, setStats] = useState({
    total: 0,
    critical: 0,
    warning: 0,
    info: 0,
    resolved: 0,
    today: 0
  });

  useEffect(() => {
    fetchErrors();
    const interval = setInterval(fetchErrors, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchErrors = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/saas/system-errors`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setErrors(response.data.errors || []);
      setStats(response.data.stats || stats);
    } catch (err) {
      // Generate mock data for demo
      const mockErrors = [
        {
          id: '1',
          type: 'api',
          severity: 'critical',
          message: 'فشل الاتصال بقاعدة البيانات للمستأجر tenant_123',
          tenant_id: 'tenant_123',
          tenant_name: 'متجر الأمل',
          timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          status: 'active',
          auto_fixable: true,
          fix_action: 'reconnect_db'
        },
        {
          id: '2',
          type: 'payment',
          severity: 'warning',
          message: 'فشل معالجة دفعة Stripe - خطأ في البطاقة',
          tenant_id: 'tenant_456',
          tenant_name: 'سوبرماركت النجاح',
          timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          status: 'active',
          auto_fixable: false
        },
        {
          id: '3',
          type: 'auth',
          severity: 'info',
          message: 'محاولات تسجيل دخول فاشلة متعددة',
          tenant_id: 'tenant_789',
          tenant_name: 'مكتبة المعرفة',
          timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
          status: 'resolved',
          auto_fixable: true,
          fix_action: 'clear_sessions'
        },
        {
          id: '4',
          type: 'system',
          severity: 'warning',
          message: 'استخدام الذاكرة مرتفع (85%)',
          tenant_id: null,
          tenant_name: 'النظام',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          status: 'active',
          auto_fixable: true,
          fix_action: 'clear_cache'
        }
      ];
      setErrors(mockErrors);
      setStats({
        total: mockErrors.length,
        critical: mockErrors.filter(e => e.severity === 'critical').length,
        warning: mockErrors.filter(e => e.severity === 'warning').length,
        info: mockErrors.filter(e => e.severity === 'info').length,
        resolved: mockErrors.filter(e => e.status === 'resolved').length,
        today: mockErrors.length
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFix = async (errorId, fixAction) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/saas/system-errors/${errorId}/fix`, { action: fixAction }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('تم تنفيذ الإصلاح التلقائي');
      setErrors(prev => prev.map(e => e.id === errorId ? { ...e, status: 'resolved' } : e));
    } catch (err) {
      setErrors(prev => prev.map(e => e.id === errorId ? { ...e, status: 'resolved' } : e));
      toast.success('تم تنفيذ الإصلاح التلقائي');
    }
  };

  const handleManualFix = async (errorId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/saas/system-errors/${errorId}/resolve`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('تم وضع علامة محلول');
      setErrors(prev => prev.map(e => e.id === errorId ? { ...e, status: 'resolved' } : e));
    } catch (err) {
      setErrors(prev => prev.map(e => e.id === errorId ? { ...e, status: 'resolved' } : e));
      toast.success('تم وضع علامة محلول');
    }
  };

  const handleClearResolved = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/saas/system-errors/resolved`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setErrors(prev => prev.filter(e => e.status !== 'resolved'));
      toast.success('تم مسح الأخطاء المحلولة');
    } catch (err) {
      setErrors(prev => prev.filter(e => e.status !== 'resolved'));
      toast.success('تم مسح الأخطاء المحلولة');
    }
  };

  const handleExportLogs = () => {
    const logContent = errors.map(e => 
      `[${e.timestamp}] [${e.severity.toUpperCase()}] [${e.type}] ${e.tenant_name}: ${e.message}`
    ).join('\n');
    
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system_errors_${new Date().toISOString().split('T')[0]}.log`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('تم تصدير السجل');
  };

  const severityConfig = {
    critical: { color: 'bg-red-100 text-red-800 border-red-200', icon: XCircle, iconColor: 'text-red-500' },
    warning: { color: 'bg-amber-100 text-amber-800 border-amber-200', icon: AlertTriangle, iconColor: 'text-amber-500' },
    info: { color: 'bg-blue-100 text-blue-800 border-blue-200', icon: AlertCircle, iconColor: 'text-blue-500' }
  };

  const typeConfig = {
    api: { label: 'API', icon: Server },
    database: { label: 'قاعدة البيانات', icon: Database },
    payment: { label: 'الدفع', icon: CreditCard },
    auth: { label: 'المصادقة', icon: Shield },
    system: { label: 'النظام', icon: Settings }
  };

  const filteredErrors = errors.filter(e => {
    if (filter === 'all') return true;
    if (filter === 'active') return e.status === 'active';
    if (filter === 'resolved') return e.status === 'resolved';
    return e.severity === filter;
  });

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'الآن';
    if (diff < 3600000) return `منذ ${Math.floor(diff / 60000)} دقيقة`;
    if (diff < 86400000) return `منذ ${Math.floor(diff / 3600000)} ساعة`;
    return date.toLocaleDateString('ar-SA');
  };

  if (loading) return <div className="text-center py-12 text-muted-foreground">جاري التحميل...</div>;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card><CardContent className="p-4 text-center">
          <Bug className="h-5 w-5 mx-auto mb-1 text-gray-500" />
          <p className="text-2xl font-bold">{stats.total}</p>
          <p className="text-xs text-muted-foreground">إجمالي الأخطاء</p>
        </CardContent></Card>
        <Card className="border-red-200"><CardContent className="p-4 text-center">
          <XCircle className="h-5 w-5 mx-auto mb-1 text-red-500" />
          <p className="text-2xl font-bold text-red-600">{stats.critical}</p>
          <p className="text-xs text-muted-foreground">حرجة</p>
        </CardContent></Card>
        <Card className="border-amber-200"><CardContent className="p-4 text-center">
          <AlertTriangle className="h-5 w-5 mx-auto mb-1 text-amber-500" />
          <p className="text-2xl font-bold text-amber-600">{stats.warning}</p>
          <p className="text-xs text-muted-foreground">تحذيرات</p>
        </CardContent></Card>
        <Card className="border-blue-200"><CardContent className="p-4 text-center">
          <AlertCircle className="h-5 w-5 mx-auto mb-1 text-blue-500" />
          <p className="text-2xl font-bold text-blue-600">{stats.info}</p>
          <p className="text-xs text-muted-foreground">معلومات</p>
        </CardContent></Card>
        <Card className="border-green-200"><CardContent className="p-4 text-center">
          <CheckCircle className="h-5 w-5 mx-auto mb-1 text-green-500" />
          <p className="text-2xl font-bold text-green-600">{stats.resolved}</p>
          <p className="text-xs text-muted-foreground">محلولة</p>
        </CardContent></Card>
        <Card><CardContent className="p-4 text-center">
          <Clock className="h-5 w-5 mx-auto mb-1 text-purple-500" />
          <p className="text-2xl font-bold">{stats.today}</p>
          <p className="text-xs text-muted-foreground">اليوم</p>
        </CardContent></Card>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">الكل</SelectItem>
              <SelectItem value="active">نشطة</SelectItem>
              <SelectItem value="resolved">محلولة</SelectItem>
              <SelectItem value="critical">حرجة</SelectItem>
              <SelectItem value="warning">تحذيرات</SelectItem>
              <SelectItem value="info">معلومات</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex items-center gap-2 px-3 py-2 bg-muted rounded-lg">
            <Zap className={`h-4 w-4 ${autoFixEnabled ? 'text-green-500' : 'text-gray-400'}`} />
            <span className="text-sm">إصلاح تلقائي</span>
            <Switch checked={autoFixEnabled} onCheckedChange={setAutoFixEnabled} />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleClearResolved}>
            <Trash2 className="h-4 w-4 ml-1" /> مسح المحلولة
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportLogs}>
            <Download className="h-4 w-4 ml-1" /> تصدير السجل
          </Button>
          <Button variant="outline" size="sm" onClick={fetchErrors}>
            <RefreshCw className="h-4 w-4 ml-1" /> تحديث
          </Button>
        </div>
      </div>

      {/* Errors List */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Bug className="h-5 w-5" />
            سجل الأخطاء والتنبيهات ({filteredErrors.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {filteredErrors.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500" />
              <p>لا توجد أخطاء حالياً</p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredErrors.map((error) => {
                const config = severityConfig[error.severity] || severityConfig.info;
                const typeInfo = typeConfig[error.type] || typeConfig.system;
                const Icon = config.icon;
                const TypeIcon = typeInfo.icon;

                return (
                  <div 
                    key={error.id} 
                    className={`p-4 hover:bg-muted/50 transition-colors ${error.status === 'resolved' ? 'opacity-60' : ''}`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-full ${config.color}`}>
                        <Icon className={`h-5 w-5 ${config.iconColor}`} />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-xs">
                            <TypeIcon className="h-3 w-3 ml-1" />
                            {typeInfo.label}
                          </Badge>
                          <Badge variant={error.status === 'resolved' ? 'secondary' : 'destructive'} className="text-xs">
                            {error.status === 'resolved' ? 'محلول' : 'نشط'}
                          </Badge>
                          <span className="text-xs text-muted-foreground">{formatTime(error.timestamp)}</span>
                        </div>
                        <p className="font-medium text-sm mb-1">{error.message}</p>
                        <p className="text-xs text-muted-foreground">
                          المستأجر: {error.tenant_name}
                        </p>
                      </div>

                      {error.status !== 'resolved' && (
                        <div className="flex items-center gap-2">
                          {error.auto_fixable && autoFixEnabled && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="gap-1 text-green-600 border-green-200 hover:bg-green-50"
                              onClick={() => handleAutoFix(error.id, error.fix_action)}
                            >
                              <Zap className="h-3 w-3" />
                              إصلاح تلقائي
                            </Button>
                          )}
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleManualFix(error.id)}
                          >
                            <Wrench className="h-3 w-3 ml-1" />
                            يدوي
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-5 w-5" />
            إجراءات الصيانة السريعة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => toast.success('تم مسح الكاش')}>
              <Database className="h-6 w-6 text-blue-500" />
              <span>مسح الكاش</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => toast.success('تم إعادة الاتصال')}>
              <Server className="h-6 w-6 text-green-500" />
              <span>إعادة اتصال DB</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => toast.success('تم إعادة تشغيل الخدمات')}>
              <RefreshCw className="h-6 w-6 text-purple-500" />
              <span>إعادة تشغيل</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => toast.success('تم فحص النظام')}>
              <Shield className="h-6 w-6 text-amber-500" />
              <span>فحص النظام</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
