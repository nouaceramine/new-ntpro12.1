import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { BarChart, TrendingUp, Package, Users, DollarSign, Download } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ReportsPage() {
  const { t } = useLanguage();
  const [salesData, setSalesData] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [profitData, setProfitData] = useState(null);
  const [period, setPeriod] = useState('7');
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const [salesRes, productsRes, customersRes, profitRes] = await Promise.all([
        axios.get(`${API}/reports/sales-chart?days=${period}`),
        axios.get(`${API}/reports/top-products?limit=10`),
        axios.get(`${API}/reports/top-customers?limit=10`),
        axios.get(`${API}/reports/profit?days=${period}`)
      ]);
      setSalesData(salesRes.data);
      setTopProducts(productsRes.data);
      setTopCustomers(customersRes.data);
      setProfitData(profitRes.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchReports(); }, [period]);

  const handleBackup = async () => {
    try {
      window.open(`${API}/backup/create`, '_blank');
    } catch (e) { console.error(e); }
  };

  const handleExportProducts = () => {
    window.open(`${API}/products/export/excel`, '_blank');
  };

  const maxSales = Math.max(...salesData.map(d => d.total), 1);

  if (loading) return <Layout><div className="flex items-center justify-center min-h-[60vh]"><div className="spinner" /></div></Layout>;

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="reports-page">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">{t.reports}</h1>
          </div>
          <div className="flex gap-2">
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="7">{t.last7Days}</SelectItem>
                <SelectItem value="30">{t.last30Days}</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={handleExportProducts} className="gap-2">
              <Download className="h-4 w-4" />{t.exportExcel}
            </Button>
            <Button variant="outline" onClick={handleBackup} className="gap-2">
              <Download className="h-4 w-4" />{t.backup}
            </Button>
          </div>
        </div>

        {/* Profit Summary */}
        {profitData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-4">
                <p className="text-sm text-blue-600">{t.totalRevenue}</p>
                <p className="text-2xl font-bold text-blue-800">{profitData.total_revenue?.toFixed(2)} {t.currency}</p>
              </CardContent>
            </Card>
            <Card className="bg-red-50 border-red-200">
              <CardContent className="p-4">
                <p className="text-sm text-red-600">{t.totalCost}</p>
                <p className="text-2xl font-bold text-red-800">{profitData.total_cost?.toFixed(2)} {t.currency}</p>
              </CardContent>
            </Card>
            <Card className="bg-emerald-50 border-emerald-200">
              <CardContent className="p-4">
                <p className="text-sm text-emerald-600">{t.grossProfit}</p>
                <p className="text-2xl font-bold text-emerald-800">{profitData.gross_profit?.toFixed(2)} {t.currency}</p>
              </CardContent>
            </Card>
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="p-4">
                <p className="text-sm text-purple-600">{t.profitMargin}</p>
                <p className="text-2xl font-bold text-purple-800">{profitData.profit_margin}%</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Sales Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><BarChart className="h-5 w-5" />{t.salesChart}</CardTitle>
          </CardHeader>
          <CardContent>
            {salesData.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">{t.noProducts}</p>
            ) : (
              <div className="space-y-3">
                {salesData.map((day, idx) => (
                  <div key={idx} className="flex items-center gap-4">
                    <span className="w-24 text-sm text-muted-foreground">{day.date}</span>
                    <div className="flex-1 h-8 bg-muted rounded-lg overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-lg transition-all"
                        style={{ width: `${(day.total / maxSales) * 100}%` }}
                      />
                    </div>
                    <span className="w-32 text-sm font-medium text-end">{day.total?.toFixed(2)} {t.currency}</span>
                    <span className="w-16 text-xs text-muted-foreground">({day.count})</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Products */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Package className="h-5 w-5" />{t.topProducts}</CardTitle>
            </CardHeader>
            <CardContent>
              {topProducts.length === 0 ? (
                <p className="text-center text-muted-foreground py-4">{t.noProducts}</p>
              ) : (
                <div className="space-y-3">
                  {topProducts.map((product, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold">{idx + 1}</span>
                        <span className="font-medium">{product.product_name}</span>
                      </div>
                      <div className="text-end">
                        <p className="font-bold">{product.total_revenue?.toFixed(2)} {t.currency}</p>
                        <p className="text-xs text-muted-foreground">{product.total_quantity} {t.quantity}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Customers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Users className="h-5 w-5" />{t.topCustomers}</CardTitle>
            </CardHeader>
            <CardContent>
              {topCustomers.length === 0 ? (
                <p className="text-center text-muted-foreground py-4">{t.noCustomers}</p>
              ) : (
                <div className="space-y-3">
                  {topCustomers.map((customer, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-sm font-bold">{idx + 1}</span>
                        <span className="font-medium">{customer.name}</span>
                      </div>
                      <div className="text-end">
                        <p className="font-bold">{customer.total_purchases?.toFixed(2)} {t.currency}</p>
                        {customer.balance > 0 && <p className="text-xs text-amber-600">{t.balance}: {customer.balance?.toFixed(2)}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
