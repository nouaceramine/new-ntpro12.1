import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
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
import { toast } from 'sonner';
import { 
  Clock, 
  Play,
  StopCircle,
  DollarSign,
  TrendingUp,
  TrendingDown,
  ShoppingCart,
  Users,
  Calendar,
  FileText,
  Banknote,
  CreditCard,
  Receipt,
  Calculator,
  CheckCircle2,
  XCircle,
  History,
  Lock
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DailySessionsPage() {
  const { t, language } = useLanguage();
  
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [todaySales, setTodaySales] = useState([]);
  const [cashBoxes, setCashBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Dialogs
  const [showStartDialog, setShowStartDialog] = useState(false);
  const [showCloseDialog, setShowCloseDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);
  
  // Form
  const [openingCash, setOpeningCash] = useState(0);
  const [closingNotes, setClosingNotes] = useState('');
  const [actualCash, setActualCash] = useState(0);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sessionsRes, salesRes, cashRes] = await Promise.all([
        axios.get(`${API}/daily-sessions`).catch(() => ({ data: [] })),
        axios.get(`${API}/sales`),
        axios.get(`${API}/cash-boxes`)
      ]);
      
      setSessions(sessionsRes.data);
      setCashBoxes(cashRes.data);
      
      // Find active session
      const active = sessionsRes.data.find(s => s.status === 'open');
      setCurrentSession(active || null);
      
      // Filter today's sales
      const today = new Date().toISOString().split('T')[0];
      const todaySalesData = salesRes.data.filter(s => s.created_at?.startsWith(today));
      setTodaySales(todaySalesData);
      
      // Set actual cash from cash box
      const cashBox = cashRes.data.find(b => b.id === 'cash');
      if (cashBox) {
        setActualCash(cashBox.balance || 0);
        if (!active) {
          setOpeningCash(cashBox.balance || 0);
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const startSession = async () => {
    try {
      const session = {
        opening_cash: openingCash,
        opened_at: new Date().toISOString(),
        status: 'open'
      };
      
      const response = await axios.post(`${API}/daily-sessions`, session);
      setCurrentSession(response.data);
      setShowStartDialog(false);
      toast.success(language === 'ar' ? 'تم فتح الحصة بنجاح' : 'Session ouverte avec succès');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    }
  };

  const closeSession = async () => {
    if (!currentSession) return;
    
    try {
      const closingData = {
        closing_cash: actualCash,
        closed_at: new Date().toISOString(),
        notes: closingNotes,
        status: 'closed'
      };
      
      await axios.put(`${API}/daily-sessions/${currentSession.id}/close`, closingData);
      setCurrentSession(null);
      setShowCloseDialog(false);
      setClosingNotes('');
      toast.success(language === 'ar' ? 'تم غلق الحصة بنجاح' : 'Session fermée avec succès');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    }
  };

  const viewSessionDetails = (session) => {
    setSelectedSession(session);
    setShowDetailsDialog(true);
  };

  // Calculate session stats
  const calculateSessionStats = (session) => {
    const salesTotal = session.total_sales || 0;
    const cashSales = session.cash_sales || 0;
    const creditSales = session.credit_sales || 0;
    const expectedCash = (session.opening_cash || 0) + cashSales;
    const difference = (session.closing_cash || 0) - expectedCash;
    
    return { salesTotal, cashSales, creditSales, expectedCash, difference };
  };

  // Current session stats
  const currentStats = currentSession ? {
    totalSales: todaySales.reduce((sum, s) => sum + s.total, 0),
    cashSales: todaySales.filter(s => s.payment_type === 'cash').reduce((sum, s) => sum + s.total, 0),
    creditSales: todaySales.filter(s => s.payment_type === 'credit').reduce((sum, s) => sum + s.remaining, 0),
    salesCount: todaySales.length,
    expectedCash: (currentSession.opening_cash || 0) + todaySales.filter(s => s.payment_type === 'cash').reduce((sum, s) => sum + s.total, 0)
  } : null;

  const formatDate = (dateString) => {
    return new Intl.DateTimeFormat(language === 'ar' ? 'ar-SA' : 'fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  const formatTime = (dateString) => {
    return new Intl.DateTimeFormat(language === 'ar' ? 'ar-SA' : 'fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  if (loading) {
    return <Layout><div className="flex items-center justify-center min-h-[60vh]"><div className="spinner" /></div></Layout>;
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="daily-sessions-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {language === 'ar' ? 'حصص البيع اليومية' : 'Sessions de vente'}
            </h1>
            <p className="text-muted-foreground mt-1">
              {language === 'ar' ? 'تتبع الصندوق النقدي والمبيعات اليومية' : 'Suivi de la caisse et des ventes quotidiennes'}
            </p>
          </div>
          {!currentSession ? (
            <Button onClick={() => setShowStartDialog(true)} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
              <Play className="h-4 w-4" />
              {language === 'ar' ? 'فتح حصة جديدة' : 'Ouvrir une session'}
            </Button>
          ) : (
            <Button onClick={() => setShowCloseDialog(true)} variant="destructive" className="gap-2">
              <StopCircle className="h-4 w-4" />
              {language === 'ar' ? 'غلق الحصة' : 'Fermer la session'}
            </Button>
          )}
        </div>

        {/* Current Session Card */}
        {currentSession ? (
          <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-emerald-500 text-white">
                    <Clock className="h-6 w-6" />
                  </div>
                  <div>
                    <CardTitle className="text-emerald-800">
                      {language === 'ar' ? 'الحصة الحالية' : 'Session en cours'}
                    </CardTitle>
                    <CardDescription>
                      {language === 'ar' ? 'بدأت في' : 'Ouverte à'}: {formatTime(currentSession.opened_at)}
                    </CardDescription>
                  </div>
                </div>
                <Badge className="bg-emerald-500 text-white text-lg px-4 py-1">
                  {language === 'ar' ? 'مفتوحة' : 'Ouverte'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="p-4 bg-white/60 rounded-xl">
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'رصيد الافتتاح' : 'Ouverture'}</p>
                  <p className="text-2xl font-bold text-emerald-700">{currentSession.opening_cash?.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
                <div className="p-4 bg-white/60 rounded-xl">
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'المبيعات النقدية' : 'Ventes espèces'}</p>
                  <p className="text-2xl font-bold text-blue-600">{currentStats?.cashSales.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
                <div className="p-4 bg-white/60 rounded-xl">
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'البيع بالدين' : 'Ventes crédit'}</p>
                  <p className="text-2xl font-bold text-amber-600">{currentStats?.creditSales.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
                <div className="p-4 bg-white/60 rounded-xl">
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'عدد المبيعات' : 'Nb ventes'}</p>
                  <p className="text-2xl font-bold">{currentStats?.salesCount}</p>
                  <p className="text-xs text-muted-foreground">{language === 'ar' ? 'عملية' : 'ventes'}</p>
                </div>
                <div className="p-4 bg-white/60 rounded-xl border-2 border-emerald-300">
                  <p className="text-sm text-muted-foreground">{language === 'ar' ? 'المتوقع في الصندوق' : 'Attendu caisse'}</p>
                  <p className="text-2xl font-bold text-emerald-700">{currentStats?.expectedCash.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">{t.currency}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-muted/30 border-dashed">
            <CardContent className="p-8 text-center">
              <Lock className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">
                {language === 'ar' ? 'لا توجد حصة مفتوحة' : 'Aucune session ouverte'}
              </h3>
              <p className="text-muted-foreground mb-4">
                {language === 'ar' ? 'افتح حصة جديدة لبدء تتبع المبيعات' : 'Ouvrez une session pour commencer le suivi'}
              </p>
              <Button onClick={() => setShowStartDialog(true)} className="gap-2">
                <Play className="h-4 w-4" />
                {language === 'ar' ? 'فتح حصة' : 'Ouvrir session'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Sessions History */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              {language === 'ar' ? 'سجل الحصص' : 'Historique des sessions'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sessions.filter(s => s.status === 'closed').length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>{language === 'ar' ? 'لا يوجد سجل حصص سابقة' : 'Aucun historique'}</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{language === 'ar' ? 'التاريخ' : 'Date'}</TableHead>
                    <TableHead>{language === 'ar' ? 'الافتتاح' : 'Ouverture'}</TableHead>
                    <TableHead>{language === 'ar' ? 'الإغلاق' : 'Fermeture'}</TableHead>
                    <TableHead>{language === 'ar' ? 'المبيعات' : 'Ventes'}</TableHead>
                    <TableHead>{language === 'ar' ? 'الفرق' : 'Différence'}</TableHead>
                    <TableHead>{language === 'ar' ? 'الحالة' : 'Statut'}</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions.filter(s => s.status === 'closed').slice(0, 10).map(session => {
                    const stats = calculateSessionStats(session);
                    return (
                      <TableRow key={session.id}>
                        <TableCell className="font-medium">{formatDate(session.opened_at)}</TableCell>
                        <TableCell>{session.opening_cash?.toFixed(2)} {t.currency}</TableCell>
                        <TableCell>{session.closing_cash?.toFixed(2)} {t.currency}</TableCell>
                        <TableCell className="text-emerald-600 font-semibold">
                          {stats.salesTotal.toFixed(2)} {t.currency}
                        </TableCell>
                        <TableCell>
                          <Badge className={stats.difference === 0 ? 'bg-emerald-100 text-emerald-700' : stats.difference > 0 ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}>
                            {stats.difference > 0 ? '+' : ''}{stats.difference.toFixed(2)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className="bg-gray-100 text-gray-700">
                            {language === 'ar' ? 'مغلقة' : 'Fermée'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm" onClick={() => viewSessionDetails(session)}>
                            <FileText className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Start Session Dialog */}
        <Dialog open={showStartDialog} onOpenChange={setShowStartDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Play className="h-5 w-5 text-emerald-600" />
                {language === 'ar' ? 'فتح حصة جديدة' : 'Ouvrir une session'}
              </DialogTitle>
              <DialogDescription>
                {language === 'ar' ? 'أدخل رصيد الصندوق الافتتاحي' : 'Entrez le solde d\'ouverture de la caisse'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label>{language === 'ar' ? 'رصيد الافتتاح' : 'Solde d\'ouverture'}</Label>
                <div className="relative mt-1">
                  <Banknote className="absolute start-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="number"
                    value={openingCash}
                    onChange={(e) => setOpeningCash(parseFloat(e.target.value) || 0)}
                    className="ps-10 text-lg"
                    placeholder="0.00"
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {language === 'ar' ? 'الرصيد الحالي في الصندوق' : 'Solde actuel de la caisse'}: {actualCash.toFixed(2)} {t.currency}
                </p>
              </div>
              <Button onClick={startSession} className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700">
                <Play className="h-4 w-4" />
                {language === 'ar' ? 'بدء الحصة' : 'Démarrer la session'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Close Session Dialog */}
        <AlertDialog open={showCloseDialog} onOpenChange={setShowCloseDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2">
                <StopCircle className="h-5 w-5 text-red-600" />
                {language === 'ar' ? 'غلق الحصة' : 'Fermer la session'}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {language === 'ar' ? 'تأكد من عد الصندوق قبل الغلق' : 'Vérifiez le comptage de la caisse avant de fermer'}
              </AlertDialogDescription>
            </AlertDialogHeader>
            
            {currentSession && currentStats && (
              <div className="space-y-4 my-4">
                <div className="p-4 bg-muted/50 rounded-lg space-y-2">
                  <div className="flex justify-between">
                    <span>{language === 'ar' ? 'رصيد الافتتاح' : 'Solde ouverture'}</span>
                    <span className="font-semibold">{currentSession.opening_cash?.toFixed(2)} {t.currency}</span>
                  </div>
                  <div className="flex justify-between text-emerald-600">
                    <span>{language === 'ar' ? '+ المبيعات النقدية' : '+ Ventes espèces'}</span>
                    <span className="font-semibold">{currentStats.cashSales.toFixed(2)} {t.currency}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t font-bold">
                    <span>{language === 'ar' ? 'المتوقع في الصندوق' : 'Attendu en caisse'}</span>
                    <span>{currentStats.expectedCash.toFixed(2)} {t.currency}</span>
                  </div>
                </div>

                <div>
                  <Label>{language === 'ar' ? 'المبلغ الفعلي في الصندوق' : 'Montant réel en caisse'}</Label>
                  <Input
                    type="number"
                    value={actualCash}
                    onChange={(e) => setActualCash(parseFloat(e.target.value) || 0)}
                    className="mt-1 text-lg"
                  />
                </div>

                {actualCash !== currentStats.expectedCash && (
                  <div className={`p-3 rounded-lg ${actualCash > currentStats.expectedCash ? 'bg-blue-50 text-blue-700' : 'bg-red-50 text-red-700'}`}>
                    <p className="font-semibold">
                      {language === 'ar' ? 'الفرق' : 'Différence'}: {(actualCash - currentStats.expectedCash).toFixed(2)} {t.currency}
                    </p>
                    <p className="text-sm">
                      {actualCash > currentStats.expectedCash 
                        ? (language === 'ar' ? 'فائض في الصندوق' : 'Excédent de caisse')
                        : (language === 'ar' ? 'عجز في الصندوق' : 'Déficit de caisse')}
                    </p>
                  </div>
                )}

                <div>
                  <Label>{language === 'ar' ? 'ملاحظات (اختياري)' : 'Notes (optionnel)'}</Label>
                  <Textarea
                    value={closingNotes}
                    onChange={(e) => setClosingNotes(e.target.value)}
                    placeholder={language === 'ar' ? 'أي ملاحظات عن الحصة...' : 'Notes sur la session...'}
                    className="mt-1"
                    rows={2}
                  />
                </div>
              </div>
            )}

            <AlertDialogFooter>
              <AlertDialogCancel>{t.cancel}</AlertDialogCancel>
              <AlertDialogAction onClick={closeSession} className="bg-red-600 hover:bg-red-700">
                {language === 'ar' ? 'تأكيد الغلق' : 'Confirmer la fermeture'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Session Details Dialog */}
        <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {language === 'ar' ? 'تفاصيل الحصة' : 'Détails de la session'}
              </DialogTitle>
            </DialogHeader>
            {selectedSession && (
              <div className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-muted/50 rounded-lg">
                    <p className="text-sm text-muted-foreground">{language === 'ar' ? 'وقت الافتتاح' : 'Ouverture'}</p>
                    <p className="font-semibold">{formatDate(selectedSession.opened_at)}</p>
                  </div>
                  <div className="p-3 bg-muted/50 rounded-lg">
                    <p className="text-sm text-muted-foreground">{language === 'ar' ? 'وقت الإغلاق' : 'Fermeture'}</p>
                    <p className="font-semibold">{selectedSession.closed_at ? formatDate(selectedSession.closed_at) : '-'}</p>
                  </div>
                </div>
                
                <div className="space-y-2 p-4 bg-muted/30 rounded-lg">
                  <div className="flex justify-between">
                    <span>{language === 'ar' ? 'رصيد الافتتاح' : 'Ouverture'}</span>
                    <span className="font-semibold">{selectedSession.opening_cash?.toFixed(2)} {t.currency}</span>
                  </div>
                  <div className="flex justify-between text-emerald-600">
                    <span>{language === 'ar' ? 'إجمالي المبيعات' : 'Total ventes'}</span>
                    <span className="font-semibold">{selectedSession.total_sales?.toFixed(2)} {t.currency}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>{language === 'ar' ? 'رصيد الإغلاق' : 'Fermeture'}</span>
                    <span className="font-semibold">{selectedSession.closing_cash?.toFixed(2)} {t.currency}</span>
                  </div>
                </div>

                {selectedSession.notes && (
                  <div className="p-3 bg-amber-50 rounded-lg">
                    <p className="text-sm font-medium text-amber-700">{language === 'ar' ? 'ملاحظات' : 'Notes'}:</p>
                    <p className="text-amber-600">{selectedSession.notes}</p>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
