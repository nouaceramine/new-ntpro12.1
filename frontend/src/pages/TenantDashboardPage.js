import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  Store, Users, Package, ShoppingCart, LogOut, 
  Calendar, TrendingUp, Settings, Plus, BarChart3
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function TenantDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  
  const tenantData = JSON.parse(localStorage.getItem('tenantData') || '{}');

  useEffect(() => {
    const token = localStorage.getItem('tenantToken');
    if (!token) {
      navigate('/portal');
      return;
    }
    setLoading(false);
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('tenantToken');
    localStorage.removeItem('tenantData');
    navigate('/portal');
    toast.success('تم تسجيل الخروج');
  };

  const goToMainApp = () => {
    // Transfer tenant token to main app token
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-green-600 flex items-center justify-center">
              <Store className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg">NT Commerce</h1>
              <p className="text-xs text-muted-foreground">لوحة تحكم المشترك</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-left">
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
                    {tenantData.plan_name || 'خطة أساسية'}
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

        {/* Quick Actions */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={goToMainApp}>
            <CardContent className="p-6 text-center">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center mx-auto mb-3">
                <ShoppingCart className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="font-semibold">نقطة البيع</h3>
              <p className="text-xs text-muted-foreground mt-1">إدارة المبيعات</p>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={goToMainApp}>
            <CardContent className="p-6 text-center">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center mx-auto mb-3">
                <Package className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="font-semibold">المنتجات</h3>
              <p className="text-xs text-muted-foreground mt-1">إدارة المخزون</p>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={goToMainApp}>
            <CardContent className="p-6 text-center">
              <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center mx-auto mb-3">
                <Users className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="font-semibold">العملاء</h3>
              <p className="text-xs text-muted-foreground mt-1">إدارة الزبائن</p>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={goToMainApp}>
            <CardContent className="p-6 text-center">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center mx-auto mb-3">
                <BarChart3 className="h-6 w-6 text-orange-600" />
              </div>
              <h3 className="font-semibold">التقارير</h3>
              <p className="text-xs text-muted-foreground mt-1">إحصائيات وتقارير</p>
            </CardContent>
          </Card>
        </div>

        {/* Main CTA */}
        <Card>
          <CardContent className="p-8 text-center">
            <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <TrendingUp className="h-10 w-10 text-primary" />
            </div>
            <h2 className="text-xl font-bold mb-2">ابدأ إدارة متجرك الآن</h2>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              انتقل إلى النظام الكامل لإدارة المبيعات والمخزون والعملاء والتقارير
            </p>
            <Button size="lg" onClick={goToMainApp} className="gap-2">
              <ShoppingCart className="h-5 w-5" />
              الدخول للنظام
            </Button>
          </CardContent>
        </Card>

        {/* Subscription Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              معلومات الاشتراك
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                <p className="text-sm text-muted-foreground">البريد</p>
                <p className="font-semibold text-sm truncate">{tenantData.email}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
