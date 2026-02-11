import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Truck, Eye, EyeOff, ArrowLeft } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AgentLoginPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/saas/agent-login`, formData);
      
      // Store agent token and data
      localStorage.setItem('agentToken', response.data.access_token);
      localStorage.setItem('agentData', JSON.stringify(response.data.agent));
      
      toast.success('مرحباً بك!');
      navigate('/agent/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'بيانات الدخول غير صحيحة');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-2">
            <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center">
              <Truck className="h-7 w-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-primary">NT Commerce</span>
          </div>
          <p className="text-muted-foreground">بوابة الوكلاء</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-xl">تسجيل دخول الوكيل</CardTitle>
            <CardDescription>أدخل بياناتك للوصول إلى لوحة التحكم</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>البريد الإلكتروني</Label>
                <Input
                  type="email"
                  placeholder="agent@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                  className="h-11"
                  data-testid="agent-email-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label>كلمة المرور</Label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    required
                    className="h-11 pe-10"
                    data-testid="agent-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full h-11 text-base gap-2" 
                disabled={loading}
                data-testid="agent-login-btn"
              >
                {loading ? (
                  <>جاري التحميل...</>
                ) : (
                  <>
                    <Truck className="h-5 w-5" />
                    تسجيل الدخول
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <Button 
                variant="ghost" 
                className="text-sm text-muted-foreground gap-2"
                onClick={() => navigate('/login')}
              >
                <ArrowLeft className="h-4 w-4" />
                العودة لتسجيل الدخول الرئيسي
              </Button>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground mt-6">
          © 2024 NT Commerce - جميع الحقوق محفوظة
        </p>
      </div>
    </div>
  );
}
