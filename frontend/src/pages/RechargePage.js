import { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout } from '../components/Layout';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import { 
  Smartphone, 
  Copy, 
  TrendingUp,
  Clock,
  Wallet,
  CheckCircle,
  Wifi
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Operator logos/colors
const OPERATOR_STYLES = {
  mobilis: { color: 'bg-green-500', name: 'موبيليس', nameEn: 'Mobilis' },
  djezzy: { color: 'bg-red-500', name: 'جازي', nameEn: 'Djezzy' },
  ooredoo: { color: 'bg-orange-500', name: 'أوريدو', nameEn: 'Ooredoo' },
  idoom: { color: 'bg-blue-500', name: 'إيدوم', nameEn: 'Idoom ADSL' }
};

export default function RechargePage() {
  const { t, language, isRTL } = useLanguage();
  const [config, setConfig] = useState({});
  const [recharges, setRecharges] = useState([]);
  const [stats, setStats] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  const [form, setForm] = useState({
    operator: '',
    phone_number: '',
    amount: '',
    recharge_type: 'credit',
    customer_id: '',
    payment_method: 'cash',
    notes: ''
  });

  const [lastUssd, setLastUssd] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [configRes, rechargesRes, statsRes, customersRes] = await Promise.all([
        axios.get(`${API}/recharge/config`, { headers }),
        axios.get(`${API}/recharge`, { headers }),
        axios.get(`${API}/recharge/stats`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/customers`, { headers })
      ]);
      
      setConfig(configRes.data);
      setRecharges(rechargesRes.data);
      setStats(statsRes.data);
      setCustomers(customersRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!form.operator || !form.phone_number || !form.amount) {
      toast.error(language === 'ar' ? 'يرجى ملء جميع الحقول المطلوبة' : 'Please fill all required fields');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/recharge`, {
        ...form,
        amount: parseFloat(form.amount),
        customer_id: form.customer_id || null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(t.rechargeSuccess);
      setLastUssd(response.data.ussd_code);
      
      // Reset form
      setForm({
        operator: '',
        phone_number: '',
        amount: '',
        recharge_type: 'credit',
        customer_id: '',
        payment_method: 'cash',
        notes: ''
      });
      
      fetchData();
    } catch (error) {
      console.error('Error creating recharge:', error);
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSubmitting(false);
    }
  };

  const copyUssd = (code) => {
    navigator.clipboard.writeText(code);
    toast.success(t.ussdCopied);
  };

  const selectedOperator = config[form.operator];

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
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold">{t.mobileRecharge}</h1>
          <p className="text-muted-foreground">
            {language === 'ar' ? 'شحن رصيد الهاتف المحمول والأنترنت' : 'Mobile credit and internet top-up'}
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{t.todayRecharges}</p>
                    <p className="text-2xl font-bold">{stats.today?.count || 0}</p>
                  </div>
                  <Clock className="h-10 w-10 text-primary/20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{t.total}</p>
                    <p className="text-2xl font-bold">{(stats.today?.total_amount || 0).toLocaleString()} {t.currency}</p>
                  </div>
                  <Wallet className="h-10 w-10 text-green-500/20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{t.totalProfit}</p>
                    <p className="text-2xl font-bold text-green-500">{(stats.today?.total_profit || 0).toLocaleString()} {t.currency}</p>
                  </div>
                  <TrendingUp className="h-10 w-10 text-green-500/20" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recharge Form */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                {t.rechargeNow}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Operator Selection */}
                <div>
                  <Label>{t.operator} *</Label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {Object.entries(config).map(([key, op]) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setForm({ ...form, operator: key, amount: '' })}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          form.operator === key 
                            ? 'border-primary bg-primary/10' 
                            : 'border-muted hover:border-primary/50'
                        }`}
                        data-testid={`operator-${key}`}
                      >
                        <div className={`w-3 h-3 rounded-full ${OPERATOR_STYLES[key]?.color} mx-auto mb-1`} />
                        <p className="text-sm font-medium">
                          {language === 'ar' ? op.name : op.name_en}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Phone Number */}
                <div>
                  <Label>{t.phoneNumber} *</Label>
                  <Input
                    type="tel"
                    value={form.phone_number}
                    onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                    placeholder="0XXX XXX XXX"
                    className="text-lg tracking-wider"
                    data-testid="phone-number-input"
                  />
                </div>

                {/* Recharge Type */}
                <div>
                  <Label>{t.rechargeType}</Label>
                  <Select
                    value={form.recharge_type}
                    onValueChange={(value) => setForm({ ...form, recharge_type: value })}
                  >
                    <SelectTrigger data-testid="recharge-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="credit">{t.credit}</SelectItem>
                      <SelectItem value="internet">{t.internet}</SelectItem>
                      {form.operator === 'djezzy' && (
                        <SelectItem value="flexy">{t.flexy}</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Amount Selection */}
                {selectedOperator && (
                  <div>
                    <Label>{t.rechargeAmount} *</Label>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      {selectedOperator.amounts.map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          onClick={() => setForm({ ...form, amount: amt.toString() })}
                          className={`p-2 rounded-lg border transition-all ${
                            form.amount === amt.toString()
                              ? 'border-primary bg-primary text-primary-foreground'
                              : 'border-muted hover:border-primary/50'
                          }`}
                          data-testid={`amount-${amt}`}
                        >
                          {amt.toLocaleString()}
                        </button>
                      ))}
                    </div>
                    <Input
                      type="number"
                      value={form.amount}
                      onChange={(e) => setForm({ ...form, amount: e.target.value })}
                      placeholder={language === 'ar' ? 'أو أدخل مبلغ آخر' : 'Or enter custom amount'}
                      className="mt-2"
                      data-testid="custom-amount-input"
                    />
                  </div>
                )}

                {/* Customer (Optional) */}
                <div>
                  <Label>{t.selectCustomer}</Label>
                  <Select
                    value={form.customer_id || "walk-in"}
                    onValueChange={(value) => setForm({ ...form, customer_id: value === "walk-in" ? "" : value })}
                  >
                    <SelectTrigger data-testid="customer-select">
                      <SelectValue placeholder={t.walkInCustomer} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="walk-in">{t.walkInCustomer}</SelectItem>
                      {customers.map((c) => (
                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Payment Method */}
                <div>
                  <Label>{t.paymentMethod}</Label>
                  <Select
                    value={form.payment_method}
                    onValueChange={(value) => setForm({ ...form, payment_method: value })}
                  >
                    <SelectTrigger data-testid="payment-method-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">{t.cash}</SelectItem>
                      <SelectItem value="bank">{t.bank}</SelectItem>
                      <SelectItem value="wallet">{t.wallet}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={submitting}
                  data-testid="recharge-submit-btn"
                >
                  {submitting ? t.loading : t.rechargeNow}
                </Button>
              </form>

              {/* Last USSD Code */}
              {lastUssd && (
                <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-green-600 dark:text-green-400 font-medium">
                        {t.ussdCode}
                      </p>
                      <code className="text-lg font-mono">{lastUssd}</code>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyUssd(lastUssd)}
                      data-testid="copy-last-ussd"
                    >
                      <Copy className="h-4 w-4 me-1" />
                      {t.copyUssd}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recharge History */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>{t.rechargeHistory}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.operator}</TableHead>
                      <TableHead>{t.phoneNumber}</TableHead>
                      <TableHead>{t.amount}</TableHead>
                      <TableHead>{t.rechargeType}</TableHead>
                      <TableHead>{t.ussdCode}</TableHead>
                      <TableHead>{language === 'ar' ? 'الربح' : 'Profit'}</TableHead>
                      <TableHead>{t.createdAt}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recharges.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8">
                          <Wifi className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                          <p className="text-muted-foreground">{t.noRecharges}</p>
                        </TableCell>
                      </TableRow>
                    ) : (
                      recharges.slice(0, 20).map((r) => (
                        <TableRow key={r.id} data-testid={`recharge-row-${r.id}`}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full ${OPERATOR_STYLES[r.operator]?.color}`} />
                              {language === 'ar' 
                                ? OPERATOR_STYLES[r.operator]?.name 
                                : OPERATOR_STYLES[r.operator]?.nameEn}
                            </div>
                          </TableCell>
                          <TableCell className="font-mono">{r.phone_number}</TableCell>
                          <TableCell className="font-medium">{r.amount.toLocaleString()} {t.currency}</TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {r.recharge_type === 'credit' ? t.credit : 
                               r.recharge_type === 'internet' ? t.internet : t.flexy}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <code className="text-xs bg-muted px-1 rounded">{r.ussd_code}</code>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => copyUssd(r.ussd_code)}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                            </div>
                          </TableCell>
                          <TableCell className="text-green-500 font-medium">
                            +{r.profit?.toLocaleString() || 0} {t.currency}
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {new Date(r.created_at).toLocaleString(language === 'ar' ? 'ar-DZ' : 'en-US')}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
