import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  Receipt, 
  Printer,
  RotateCcw,
  Eye
} from 'lucide-react';
import { ExportPrintButtons } from '../components/ExportPrintButtons';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SalesHistoryPage() {
  const { t, language } = useLanguage();
  
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [returnDialogOpen, setReturnDialogOpen] = useState(false);
  const [selectedSale, setSelectedSale] = useState(null);

  const fetchSales = async () => {
    try {
      const response = await axios.get(`${API}/sales`);
      setSales(response.data);
    } catch (error) {
      console.error('Error fetching sales:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSales();
  }, []);

  const handleReturn = async () => {
    try {
      await axios.post(`${API}/sales/${selectedSale.id}/return`);
      toast.success(t.saleReturned);
      setReturnDialogOpen(false);
      fetchSales();
    } catch (error) {
      toast.error(t.somethingWentWrong);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'paid':
        return <Badge className="bg-emerald-100 text-emerald-700">{t.paid}</Badge>;
      case 'partial':
        return <Badge className="bg-amber-100 text-amber-700">{t.partial}</Badge>;
      case 'unpaid':
        return <Badge className="bg-red-100 text-red-700">{t.unpaid}</Badge>;
      case 'returned':
        return <Badge variant="outline">{t.returned}</Badge>;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="spinner" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="sales-history-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.sales}</h1>
            <p className="text-muted-foreground mt-1">{sales.length} {t.sales}</p>
          </div>
          <div className="flex gap-2 items-center">
            <ExportPrintButtons
              data={sales.map(s => ({
                invoice: s.invoice_number || '-',
                customer: s.customer_name || (language === 'ar' ? 'زبون مجهول' : 'Client anonyme'),
                total: s.total?.toFixed(2) || '0',
                paid: s.paid_amount?.toFixed(2) || '0',
                remaining: s.remaining?.toFixed(2) || '0',
                payment: s.payment_method === 'cash' ? (language === 'ar' ? 'نقدي' : 'Espèces') : 
                         s.payment_method === 'bank' ? (language === 'ar' ? 'بنكي' : 'Banque') : 
                         (language === 'ar' ? 'محفظة' : 'Portefeuille'),
                date: formatDate(s.created_at)
              }))}
              columns={[
                { key: 'invoice', label: language === 'ar' ? 'رقم الفاتورة' : 'N° Facture' },
                { key: 'customer', label: language === 'ar' ? 'الزبون' : 'Client' },
                { key: 'total', label: language === 'ar' ? 'الإجمالي' : 'Total' },
                { key: 'paid', label: language === 'ar' ? 'المدفوع' : 'Payé' },
                { key: 'remaining', label: language === 'ar' ? 'الباقي' : 'Restant' },
                { key: 'payment', label: language === 'ar' ? 'طريقة الدفع' : 'Paiement' },
                { key: 'date', label: language === 'ar' ? 'التاريخ' : 'Date' }
              ]}
              filename={`sales_${new Date().toISOString().split('T')[0]}`}
              title={language === 'ar' ? 'سجل المبيعات' : 'Historique des Ventes'}
              language={language}
            />
            <Link to="/pos">
              <Button className="gap-2" data-testid="new-sale-btn">
                {t.newSale}
              </Button>
            </Link>
          </div>
        </div>

        {/* Sales List */}
        <Card>
          <CardContent className="p-0">
            {sales.length === 0 ? (
              <div className="empty-state py-16">
                <Receipt className="h-20 w-20 text-muted-foreground mb-4" />
                <h3 className="text-xl font-medium">{t.noProducts}</h3>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t.invoiceNumber}</th>
                      <th>{t.customerName}</th>
                      <th>{t.total}</th>
                      <th>{t.paidAmount}</th>
                      <th>{t.remaining}</th>
                      <th>{t.paymentMethod}</th>
                      <th>{t.createdAt}</th>
                      <th>{t.actions}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sales.map(sale => (
                      <tr key={sale.id}>
                        <td className="font-medium">{sale.invoice_number}</td>
                        <td>{sale.customer_name}</td>
                        <td className="font-semibold">{sale.total.toFixed(2)} {t.currency}</td>
                        <td>{sale.paid_amount.toFixed(2)} {t.currency}</td>
                        <td className={sale.remaining > 0 ? 'text-amber-600' : ''}>
                          {sale.remaining.toFixed(2)} {t.currency}
                        </td>
                        <td>
                          <Badge variant="outline">
                            {sale.payment_method === 'cash' ? t.cash : sale.payment_method === 'bank' ? t.bank : t.wallet}
                          </Badge>
                        </td>
                        <td className="text-muted-foreground text-sm">{formatDate(sale.created_at)}</td>
                        <td>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => window.open(`${API}/sales/${sale.id}/invoice-pdf`, '_blank')}
                            >
                              <Printer className="h-4 w-4" />
                            </Button>
                            {sale.status !== 'returned' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-destructive"
                                onClick={() => { setSelectedSale(sale); setReturnDialogOpen(true); }}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                          {getStatusBadge(sale.status)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Return Dialog */}
        <AlertDialog open={returnDialogOpen} onOpenChange={setReturnDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{t.returnSale}</AlertDialogTitle>
              <AlertDialogDescription>
                {t.deleteConfirm}
                <br />
                <span className="font-medium">{selectedSale?.invoice_number}</span>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>{t.cancel}</AlertDialogCancel>
              <AlertDialogAction onClick={handleReturn} className="bg-destructive text-destructive-foreground">
                {t.returnSale}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
}
