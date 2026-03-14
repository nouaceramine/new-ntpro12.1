import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';
import { Wallet, ArrowUpRight, ArrowDownLeft, ArrowLeftRight, DollarSign, TrendingUp } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function WalletPage() {
  const { language } = useLanguage();
  const isAr = language === 'ar';
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('token');
  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = async () => {
    try {
      const [wRes, tRes] = await Promise.all([
        axios.get(`${API}/wallet`, { headers }),
        axios.get(`${API}/wallet/transactions`, { headers }),
      ]);
      setWallet(wRes.data);
      setTransactions(tRes.data);
      // Try stats (super admin only)
      try {
        const sRes = await axios.get(`${API}/wallet/stats`, { headers });
        setStats(sRes.data);
      } catch {}
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const txnIcon = (type) => type === 'credit' ? ArrowDownLeft : ArrowUpRight;
  const txnColor = (type) => type === 'credit' ? 'text-emerald-400' : 'text-red-400';

  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-6" data-testid="wallet-page">
        <h1 className="text-2xl font-bold text-white">{isAr ? 'المحفظة' : 'Portefeuille'}</h1>

        {/* Wallet Balance */}
        {wallet && (
          <Card className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border-blue-500/30">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <Wallet className="w-12 h-12 text-blue-400" />
                <div>
                  <p className="text-sm text-gray-300">{isAr ? 'الرصيد الحالي' : 'Solde actuel'}</p>
                  <p className="text-4xl font-bold text-white">{(wallet.balance || 0).toLocaleString()} <span className="text-lg text-gray-400">{wallet.currency || 'DZD'}</span></p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats (Super Admin) */}
        {stats.total_wallets > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: isAr ? 'إجمالي المحافظ' : 'Total wallets', value: stats.total_wallets, icon: Wallet, color: 'text-blue-400' },
              { label: isAr ? 'الرصيد الكلي' : 'Solde total', value: `${(stats.total_balance || 0).toLocaleString()} DA`, icon: DollarSign, color: 'text-emerald-400' },
              { label: isAr ? 'المعاملات' : 'Transactions', value: stats.total_transactions || 0, icon: TrendingUp, color: 'text-purple-400' },
              { label: isAr ? 'التحويلات' : 'Transferts', value: stats.total_transfers || 0, icon: ArrowLeftRight, color: 'text-amber-400' },
            ].map((s, i) => (
              <Card key={i} className="bg-gray-800/50 border-gray-700"><CardContent className="p-4 flex items-center gap-3">
                <s.icon className={`w-8 h-8 ${s.color}`} />
                <div><p className="text-xs text-gray-400">{s.label}</p><p className="text-xl font-bold text-white">{s.value}</p></div>
              </CardContent></Card>
            ))}
          </div>
        )}

        {/* Transactions */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">{isAr ? 'سجل المعاملات' : 'Historique'}</h2>
          <div className="space-y-2">
            {loading ? <p className="text-gray-400 text-center py-8">{isAr ? 'جاري التحميل...' : 'Chargement...'}</p> :
             transactions.length === 0 ? <p className="text-gray-400 text-center py-8">{isAr ? 'لا توجد معاملات' : 'Aucune transaction'}</p> :
             transactions.map(t => {
               const Icon = txnIcon(t.transaction_type);
               return (
                <Card key={t.id} className="bg-gray-800/50 border-gray-700" data-testid={`txn-${t.id}`}>
                  <CardContent className="p-3 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <Icon className={`w-5 h-5 ${txnColor(t.transaction_type)}`} />
                      <div>
                        <p className="text-white text-sm">{t.description || t.reference_type}</p>
                        <p className="text-xs text-gray-500">{new Date(t.created_at).toLocaleString()}</p>
                      </div>
                    </div>
                    <span className={`font-bold ${txnColor(t.transaction_type)}`}>
                      {t.transaction_type === 'credit' ? '+' : '-'}{t.amount?.toLocaleString()} DA
                    </span>
                  </CardContent>
                </Card>
               );
             })}
          </div>
        </div>
      </div>
    </Layout>
  );
}
