import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Shield, Globe, Eye, EyeOff } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LoginPage() {
  const { t, language, toggleLanguage, isRTL } = useLanguage();
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [branding, setBranding] = useState({
    business_name: '',
    logo_url: '',
    background_url: '',
    primary_color: ''
  });

  useEffect(() => {
    const fetchBranding = async () => {
      try {
        const response = await axios.get(`${API}/branding/settings`);
        if (response.data) {
          setBranding(response.data);
        }
      } catch (error) {
        console.error('Error fetching branding:', error);
      }
    };
    fetchBranding();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await login(email, password);
      toast.success(t.welcomeBack);
      navigate('/');
    } catch (error) {
      console.error('Login error:', error);
      toast.error(error.response?.data?.detail || t.invalidCredentials);
    } finally {
      setLoading(false);
    }
  };

  const displayName = branding.business_name || t.appName;
  const backgroundImage = branding.background_url || 'https://images.unsplash.com/photo-1758631279366-8e8aeaf94082?crop=entropy&cs=srgb&fm=jpg&q=85';

  return (
    <div className="min-h-screen flex" dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Left Side - Hero Image */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-slate-900">
        <img
          src={backgroundImage}
          alt={displayName}
          className="absolute inset-0 w-full h-full object-cover opacity-60"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/50 to-transparent" />
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <div className="flex items-center gap-3 mb-6">
            {branding.logo_url ? (
              <img src={branding.logo_url} alt={displayName} className="h-12 w-12 object-contain rounded-lg" />
            ) : (
              <Shield className="h-10 w-10 text-primary" />
            )}
            <span className="text-3xl font-bold">{displayName}</span>
          </div>
          <h2 className="text-4xl font-bold mb-4">
            {isRTL ? 'إدارة مخزون زجاج الحماية بسهولة' : 'Manage Your Screen Protectors Inventory Effortlessly'}
          </h2>
          <p className="text-lg text-slate-300">
            {isRTL 
              ? 'نظام متكامل لإدارة منتجات زجاج الحماية والبحث عن الموديلات المتوافقة'
              : 'A complete system to manage screen protector products and find compatible models'}
          </p>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md">
          {/* Language Toggle */}
          <div className="flex justify-end mb-8">
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted hover:bg-muted/80 transition-colors"
              data-testid="login-lang-toggle"
            >
              <Globe className="h-4 w-4" />
              <span className="text-sm font-medium">
                {language === 'fr' ? 'عربي' : 'Français'}
              </span>
            </button>
          </div>

          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            {branding.logo_url ? (
              <img src={branding.logo_url} alt={displayName} className="h-10 w-10 object-contain rounded-lg" />
            ) : (
              <Shield className="h-10 w-10 text-primary" />
            )}
            <span className="text-2xl font-bold">{displayName}</span>
          </div>

          <Card className="border-0 shadow-xl">
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-2xl font-bold">{t.welcomeBack}</CardTitle>
              <CardDescription>{t.loginSubtitle}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email">{t.email}</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-12"
                    data-testid="login-email-input"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password">{t.password}</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className={`h-12 ${isRTL ? 'pl-12' : 'pr-12'}`}
                      data-testid="login-password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className={`absolute top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground ${isRTL ? 'left-2' : 'right-2'}`}
                      data-testid="toggle-password-visibility"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 text-base font-semibold"
                  disabled={loading}
                  data-testid="login-submit-btn"
                >
                  {loading ? t.loading : t.login}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <p className="text-sm text-muted-foreground">
                  {t.noAccount}{' '}
                  <Link 
                    to="/register" 
                    className="text-primary font-medium hover:underline"
                    data-testid="go-to-register"
                  >
                    {t.register}
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
