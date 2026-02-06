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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
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
  Users, 
  DollarSign, 
  Search,
  Download,
  CreditCard,
  Banknote,
  Phone,
  Calendar,
  AlertCircle,
  CheckCircle,
  FileSpreadsheet,
  Eye,
  Wallet
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CustomerDebtsPage() {
  const { t, language, isRTL } = useLanguage();
  const [debtsSummary, setDebtsSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('debt_desc');
  
  // Payment dialog
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  // Debt details dialog
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [customerDebtDetails, setCustomerDebtDetails] = useState(null);

  useEffect(() => {
    fetchDebtsSummary();
  }, []);

  const fetchDebtsSummary = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/debts/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDebtsSummary(response.data);
    } catch (error) {
      console.error('Error fetching debts summary:', error);
      toast.error(t.error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomerDebtDetails = async (customerId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/customers/${customerId}/debt`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomerDebtDetails(response.data);
      setShowDetailsDialog(true);
    } catch (error) {
      console.error('Error fetching customer debt details:', error);
      toast.error(t.error);
    }
  };

  const handlePayDebt = async () => {
    if (!selectedCustomer || paymentAmount <= 0) {
      toast.error(language === 'ar' ? 'يرجى إدخال مبلغ صحيح' : 'Please enter a valid amount');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/customers/${selectedCustomer.customer_id}/debt/pay`, {
        customer_id: selectedCustomer.customer_id,
        amount: paymentAmount,
        payment_method: paymentMethod,
        notes: paymentNotes
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(t.debtPaid);
      setShowPaymentDialog(false);
      setSelectedCustomer(null);
      setPaymentAmount(0);
      setPaymentNotes('');
      fetchDebtsSummary();
    } catch (error) {
      console.error('Error paying debt:', error);
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setSubmitting(false);
    }
  };

  const openPaymentDialog = (customer) => {
    setSelectedCustomer(customer);
    setPaymentAmount(customer.total_debt);
    setShowPaymentDialog(true);
  };

  const exportToExcel = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/debts/export`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `debts_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(language === 'ar' ? 'تم تصدير الملف بنجاح' : 'File exported successfully');
    } catch (error) {
      console.error('Error exporting:', error);
      toast.error(t.error);
    }
  };

  // Filter and sort debts
  const filteredDebts = debtsSummary?.debts?.filter(debt => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      debt.customer_name.toLowerCase().includes(query) ||
      debt.customer_phone?.toLowerCase().includes(query)
    );
  }) || [];

  const sortedDebts = [...filteredDebts].sort((a, b) => {
    switch (sortBy) {
      case 'debt_desc':
        return b.total_debt - a.total_debt;
      case 'debt_asc':
        return a.total_debt - b.total_debt;
      case 'name_asc':
        return a.customer_name.localeCompare(b.customer_name);
      case 'name_desc':
        return b.customer_name.localeCompare(a.customer_name);
      case 'sales_desc':
        return b.sales_count - a.sales_count;
      default:
        return 0;
    }
  });

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
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold">{t.customerDebts}</h1>
            <p className="text-muted-foreground">
              {language === 'ar' ? 'متابعة وتحصيل ديون الزبائن' : 'Track and collect customer debts'}
            </p>
          </div>
          <Button onClick={exportToExcel} variant="outline" data-testid="export-debts-btn">
            <FileSpreadsheet className="h-4 w-4 me-2" />
            {t.exportExcel}
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-200 dark:border-red-900">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{t.totalDebt}</p>
                  <p className="text-3xl font-bold text-red-600">
                    {(debtsSummary?.total_outstanding || 0).toLocaleString()} {t.currency}
                  </p>
                </div>
                <div className="p-3 bg-red-500/10 rounded-full">
                  <DollarSign className="h-8 w-8 text-red-500" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {language === 'ar' ? 'عدد الزبائن المدينين' : 'Customers with Debt'}
                  </p>
                  <p className="text-3xl font-bold">{debtsSummary?.customers_with_debt || 0}</p>
                </div>
                <div className="p-3 bg-primary/10 rounded-full">
                  <Users className="h-8 w-8 text-primary" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {language === 'ar' ? 'متوسط الدين' : 'Average Debt'}
                  </p>
                  <p className="text-3xl font-bold">
                    {debtsSummary?.customers_with_debt > 0 
                      ? Math.round(debtsSummary.total_outstanding / debtsSummary.customers_with_debt).toLocaleString()
                      : 0} {t.currency}
                  </p>
                </div>
                <div className="p-3 bg-amber-500/10 rounded-full">
                  <AlertCircle className="h-8 w-8 text-amber-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex gap-4 flex-wrap">
          <div className="relative flex-1 min-w-[250px]">
            <Search className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
            <Input
              placeholder={language === 'ar' ? 'بحث باسم الزبون أو رقم الهاتف...' : 'Search by name or phone...'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`h-11 ${isRTL ? 'pr-10' : 'pl-10'}`}
              data-testid="search-debts-input"
            />
          </div>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-48" data-testid="sort-select">
              <SelectValue placeholder={language === 'ar' ? 'ترتيب حسب' : 'Sort by'} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="debt_desc">{language === 'ar' ? 'الدين (الأعلى)' : 'Debt (Highest)'}</SelectItem>
              <SelectItem value="debt_asc">{language === 'ar' ? 'الدين (الأقل)' : 'Debt (Lowest)'}</SelectItem>
              <SelectItem value="name_asc">{language === 'ar' ? 'الاسم (أ-ي)' : 'Name (A-Z)'}</SelectItem>
              <SelectItem value="name_desc">{language === 'ar' ? 'الاسم (ي-أ)' : 'Name (Z-A)'}</SelectItem>
              <SelectItem value="sales_desc">{language === 'ar' ? 'عدد الفواتير' : 'Invoice Count'}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Debts Table */}
        <div className="bg-card rounded-xl border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{language === 'ar' ? 'الزبون' : 'Customer'}</TableHead>
                <TableHead>{t.phone}</TableHead>
                <TableHead>{language === 'ar' ? 'عدد الفواتير' : 'Invoices'}</TableHead>
                <TableHead>{t.totalDebt}</TableHead>
                <TableHead>{t.actions}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedDebts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12">
                    <CheckCircle className="h-16 w-16 mx-auto text-green-500 mb-4" />
                    <p className="text-lg font-medium text-green-600">
                      {language === 'ar' ? 'لا توجد ديون مستحقة!' : 'No outstanding debts!'}
                    </p>
                    <p className="text-muted-foreground">
                      {language === 'ar' ? 'جميع الزبائن سددوا مستحقاتهم' : 'All customers have paid their dues'}
                    </p>
                  </TableCell>
                </TableRow>
              ) : (
                sortedDebts.map((debt) => (
                  <TableRow key={debt.customer_id} data-testid={`debt-row-${debt.customer_id}`}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <Users className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{debt.customer_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {debt.sales_count} {language === 'ar' ? 'فاتورة' : 'invoices'}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {debt.customer_phone ? (
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-muted-foreground" />
                          <span dir="ltr">{debt.customer_phone}</span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{debt.sales_count}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-lg font-bold text-red-600">
                        {debt.total_debt.toLocaleString()} {t.currency}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => fetchCustomerDebtDetails(debt.customer_id)}
                          data-testid={`view-debt-${debt.customer_id}`}
                        >
                          <Eye className="h-4 w-4 me-1" />
                          {language === 'ar' ? 'تفاصيل' : 'Details'}
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => openPaymentDialog(debt)}
                          data-testid={`pay-debt-${debt.customer_id}`}
                        >
                          <CreditCard className="h-4 w-4 me-1" />
                          {t.payDebt}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Payment Dialog */}
        <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>{t.payDebt}</DialogTitle>
            </DialogHeader>
            {selectedCustomer && (
              <div className="space-y-4">
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'الزبون' : 'Customer'}</p>
                  <p className="font-bold text-lg">{selectedCustomer.customer_name}</p>
                </div>
                
                <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                  <p className="text-sm text-red-600">{t.totalDebt}</p>
                  <p className="text-2xl font-bold text-red-600">
                    {selectedCustomer.total_debt.toLocaleString()} {t.currency}
                  </p>
                </div>

                <div>
                  <Label>{t.amount}</Label>
                  <Input
                    type="number"
                    min="0"
                    max={selectedCustomer.total_debt}
                    value={paymentAmount}
                    onChange={(e) => setPaymentAmount(parseFloat(e.target.value) || 0)}
                    data-testid="payment-amount-input"
                  />
                </div>

                <div>
                  <Label>{t.paymentMethod}</Label>
                  <div className="flex gap-2 mt-2">
                    <Button
                      type="button"
                      variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setPaymentMethod('cash')}
                      className="flex-1"
                    >
                      <Banknote className="h-4 w-4 me-1" />
                      {t.cash}
                    </Button>
                    <Button
                      type="button"
                      variant={paymentMethod === 'bank' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setPaymentMethod('bank')}
                      className="flex-1"
                    >
                      <CreditCard className="h-4 w-4 me-1" />
                      {t.bank}
                    </Button>
                    <Button
                      type="button"
                      variant={paymentMethod === 'wallet' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setPaymentMethod('wallet')}
                      className="flex-1"
                    >
                      <Wallet className="h-4 w-4 me-1" />
                    </Button>
                  </div>
                </div>

                <div>
                  <Label>{t.notes}</Label>
                  <Input
                    value={paymentNotes}
                    onChange={(e) => setPaymentNotes(e.target.value)}
                    placeholder={language === 'ar' ? 'ملاحظات اختيارية...' : 'Optional notes...'}
                  />
                </div>

                <div className="flex gap-2 pt-4">
                  <Button variant="outline" onClick={() => setShowPaymentDialog(false)} className="flex-1">
                    {t.cancel}
                  </Button>
                  <Button 
                    onClick={handlePayDebt} 
                    className="flex-1" 
                    disabled={submitting || paymentAmount <= 0}
                  >
                    {submitting ? t.loading : t.confirm}
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Debt Details Dialog */}
        <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
            <DialogHeader>
              <DialogTitle>{language === 'ar' ? 'تفاصيل الدين' : 'Debt Details'}</DialogTitle>
            </DialogHeader>
            {customerDebtDetails && (
              <div className="space-y-6">
                {/* Customer Info */}
                <div className="p-4 bg-muted rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{language === 'ar' ? 'الزبون' : 'Customer'}</p>
                      <p className="font-bold text-lg">{customerDebtDetails.customer_name}</p>
                    </div>
                    <div className="text-end">
                      <p className="text-sm text-muted-foreground">{t.totalDebt}</p>
                      <p className="text-2xl font-bold text-red-600">
                        {customerDebtDetails.total_debt.toLocaleString()} {t.currency}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Unpaid Sales */}
                {customerDebtDetails.unpaid_sales?.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">{language === 'ar' ? 'الفواتير غير المسددة' : 'Unpaid Invoices'}</h3>
                    <div className="space-y-2">
                      {customerDebtDetails.unpaid_sales.map((sale) => (
                        <div key={sale.id} className="p-3 border rounded-lg flex items-center justify-between">
                          <div>
                            <p className="font-medium">{sale.invoice_number}</p>
                            <p className="text-sm text-muted-foreground">
                              {new Date(sale.created_at).toLocaleDateString(language === 'ar' ? 'ar-DZ' : 'en-US')}
                            </p>
                          </div>
                          <div className="text-end">
                            <p className="text-sm text-muted-foreground">{language === 'ar' ? 'المتبقي' : 'Remaining'}</p>
                            <p className="font-bold text-red-600">{sale.debt_amount?.toLocaleString()} {t.currency}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Payment History */}
                {customerDebtDetails.payment_history?.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">{language === 'ar' ? 'سجل المدفوعات' : 'Payment History'}</h3>
                    <div className="space-y-2">
                      {customerDebtDetails.payment_history.map((payment) => (
                        <div key={payment.id} className="p-3 border rounded-lg bg-green-50 dark:bg-green-900/20 flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              <p className="font-medium text-green-700">
                                {payment.payment_method === 'cash' ? t.cash : payment.payment_method === 'bank' ? t.bank : t.wallet}
                              </p>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {new Date(payment.created_at).toLocaleDateString(language === 'ar' ? 'ar-DZ' : 'en-US')}
                            </p>
                          </div>
                          <p className="font-bold text-green-600">+{payment.amount?.toLocaleString()} {t.currency}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Button onClick={() => setShowDetailsDialog(false)} className="w-full">
                  {t.cancel}
                </Button>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
