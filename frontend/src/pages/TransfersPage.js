import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  ArrowUpRight,
  ArrowDownLeft,
  ArrowRight,
  Send,
  User,
  DollarSign,
  Clock,
  CheckCircle2,
  XCircle,
  Plus,
  Search,
  Loader2
} from 'lucide-react';
import { Link } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function TransfersPage() {
  const { language } = useLanguage();
  const [activeTab, setActiveTab] = useState('outgoing');
  const [showTransferDialog, setShowTransferDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Transfer form
  const [transferForm, setTransferForm] = useState({
    recipient: '',
    amount: '',
    note: ''
  });

  // Sample transfers data
  const [outgoingTransfers, setOutgoingTransfers] = useState([
    { id: 1, recipient: 'أحمد محمد', recipientId: 'user123', amount: 5000, status: 'completed', date: '2026-02-07T10:30:00' },
    { id: 2, recipient: 'سارة علي', recipientId: 'user456', amount: 2000, status: 'pending', date: '2026-02-07T09:15:00' },
    { id: 3, recipient: 'محمد خالد', recipientId: 'user789', amount: 10000, status: 'completed', date: '2026-02-06T14:45:00' },
  ]);

  const [incomingTransfers, setIncomingTransfers] = useState([
    { id: 1, sender: 'الموزع الرئيسي', senderId: 'admin001', amount: 50000, status: 'completed', date: '2026-02-07T08:00:00' },
    { id: 2, sender: 'وكيل فرعي', senderId: 'agent123', amount: 15000, status: 'completed', date: '2026-02-05T16:30:00' },
  ]);

  const handleTransfer = async () => {
    if (!transferForm.recipient || !transferForm.amount) {
      toast.error(language === 'ar' ? 'يرجى ملء جميع الحقول' : 'Veuillez remplir tous les champs');
      return;
    }

    const amount = parseFloat(transferForm.amount);
    if (amount <= 0) {
      toast.error(language === 'ar' ? 'المبلغ يجب أن يكون أكبر من 0' : 'Le montant doit être supérieur à 0');
      return;
    }

    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const newTransfer = {
        id: Date.now(),
        recipient: transferForm.recipient,
        recipientId: 'new_user',
        amount: amount,
        status: 'pending',
        date: new Date().toISOString()
      };

      setOutgoingTransfers(prev => [newTransfer, ...prev]);
      setTransferForm({ recipient: '', amount: '', note: '' });
      setShowTransferDialog(false);
      toast.success(language === 'ar' ? 'تم إرسال التحويل بنجاح' : 'Transfert envoyé avec succès');
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل في إرسال التحويل' : 'Échec du transfert');
    } finally {
      setLoading(false);
    }
  };

  const getTotalOutgoing = () => outgoingTransfers.reduce((sum, t) => sum + t.amount, 0);
  const getTotalIncoming = () => incomingTransfers.reduce((sum, t) => sum + t.amount, 0);

  const filteredOutgoing = outgoingTransfers.filter(t => 
    t.recipient.includes(searchQuery) || t.recipientId.includes(searchQuery)
  );
  const filteredIncoming = incomingTransfers.filter(t => 
    t.sender.includes(searchQuery) || t.senderId.includes(searchQuery)
  );

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="transfers-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/services">
              <Button variant="ghost" size="icon">
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                  <Send className="h-8 w-8 text-indigo-500" />
                </div>
                {language === 'ar' ? 'التحويلات' : 'Transferts'}
              </h1>
              <p className="text-muted-foreground mt-1">
                {language === 'ar' ? 'إدارة التحويلات الصادرة والواردة' : 'Gérer les transferts sortants et entrants'}
              </p>
            </div>
          </div>
          <Button onClick={() => setShowTransferDialog(true)}>
            <Plus className="h-4 w-4 me-2" />
            {language === 'ar' ? 'تحويل جديد' : 'Nouveau transfert'}
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="border-r-4 border-r-red-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <ArrowUpRight className="h-4 w-4 text-red-500" />
                    {language === 'ar' ? 'إجمالي الصادرة' : 'Total sortant'}
                  </p>
                  <p className="text-2xl font-bold text-red-500 mt-1">
                    {getTotalOutgoing().toLocaleString()} دج
                  </p>
                </div>
                <Badge variant="outline">{outgoingTransfers.length} {language === 'ar' ? 'تحويل' : 'transferts'}</Badge>
              </div>
            </CardContent>
          </Card>

          <Card className="border-r-4 border-r-emerald-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <ArrowDownLeft className="h-4 w-4 text-emerald-500" />
                    {language === 'ar' ? 'إجمالي الواردة' : 'Total entrant'}
                  </p>
                  <p className="text-2xl font-bold text-emerald-500 mt-1">
                    {getTotalIncoming().toLocaleString()} دج
                  </p>
                </div>
                <Badge variant="outline">{incomingTransfers.length} {language === 'ar' ? 'تحويل' : 'transferts'}</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={language === 'ar' ? 'بحث بالاسم أو المعرف...' : 'Rechercher par nom ou ID...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pe-10"
          />
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="outgoing" className="gap-2">
              <ArrowUpRight className="h-4 w-4" />
              {language === 'ar' ? 'الصادرة' : 'Sortants'}
            </TabsTrigger>
            <TabsTrigger value="incoming" className="gap-2">
              <ArrowDownLeft className="h-4 w-4" />
              {language === 'ar' ? 'الواردة' : 'Entrants'}
            </TabsTrigger>
          </TabsList>

          {/* Outgoing Tab */}
          <TabsContent value="outgoing" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>{language === 'ar' ? 'التحويلات الصادرة' : 'Transferts sortants'}</CardTitle>
                <CardDescription>
                  {language === 'ar' ? 'التحويلات التي أرسلتها' : 'Transferts que vous avez envoyés'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {filteredOutgoing.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <ArrowUpRight className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>{language === 'ar' ? 'لا توجد تحويلات صادرة' : 'Aucun transfert sortant'}</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{language === 'ar' ? 'المستلم' : 'Destinataire'}</TableHead>
                        <TableHead>{language === 'ar' ? 'المعرف' : 'ID'}</TableHead>
                        <TableHead>{language === 'ar' ? 'المبلغ' : 'Montant'}</TableHead>
                        <TableHead>{language === 'ar' ? 'الحالة' : 'Statut'}</TableHead>
                        <TableHead>{language === 'ar' ? 'التاريخ' : 'Date'}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredOutgoing.map(transfer => (
                        <TableRow key={transfer.id}>
                          <TableCell className="font-medium">{transfer.recipient}</TableCell>
                          <TableCell className="text-muted-foreground">{transfer.recipientId}</TableCell>
                          <TableCell className="font-bold text-red-500">-{transfer.amount.toLocaleString()} دج</TableCell>
                          <TableCell>
                            {transfer.status === 'completed' ? (
                              <Badge className="bg-emerald-500">
                                <CheckCircle2 className="h-3 w-3 me-1" />
                                {language === 'ar' ? 'مكتمل' : 'Terminé'}
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <Clock className="h-3 w-3 me-1" />
                                {language === 'ar' ? 'معلق' : 'En attente'}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(transfer.date).toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Incoming Tab */}
          <TabsContent value="incoming" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>{language === 'ar' ? 'التحويلات الواردة' : 'Transferts entrants'}</CardTitle>
                <CardDescription>
                  {language === 'ar' ? 'التحويلات التي استلمتها' : 'Transferts que vous avez reçus'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {filteredIncoming.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <ArrowDownLeft className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>{language === 'ar' ? 'لا توجد تحويلات واردة' : 'Aucun transfert entrant'}</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{language === 'ar' ? 'المرسل' : 'Expéditeur'}</TableHead>
                        <TableHead>{language === 'ar' ? 'المعرف' : 'ID'}</TableHead>
                        <TableHead>{language === 'ar' ? 'المبلغ' : 'Montant'}</TableHead>
                        <TableHead>{language === 'ar' ? 'الحالة' : 'Statut'}</TableHead>
                        <TableHead>{language === 'ar' ? 'التاريخ' : 'Date'}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredIncoming.map(transfer => (
                        <TableRow key={transfer.id}>
                          <TableCell className="font-medium">{transfer.sender}</TableCell>
                          <TableCell className="text-muted-foreground">{transfer.senderId}</TableCell>
                          <TableCell className="font-bold text-emerald-500">+{transfer.amount.toLocaleString()} دج</TableCell>
                          <TableCell>
                            <Badge className="bg-emerald-500">
                              <CheckCircle2 className="h-3 w-3 me-1" />
                              {language === 'ar' ? 'مكتمل' : 'Terminé'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(transfer.date).toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Transfer Dialog */}
        <Dialog open={showTransferDialog} onOpenChange={setShowTransferDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Send className="h-5 w-5 text-indigo-500" />
                {language === 'ar' ? 'تحويل جديد' : 'Nouveau transfert'}
              </DialogTitle>
              <DialogDescription>
                {language === 'ar' 
                  ? 'أدخل بيانات المستلم والمبلغ المراد تحويله'
                  : 'Entrez les informations du destinataire et le montant'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  {language === 'ar' ? 'معرف المستلم' : 'ID du destinataire'}
                </Label>
                <Input
                  placeholder={language === 'ar' ? 'أدخل معرف المستلم' : 'Entrez l\'ID du destinataire'}
                  value={transferForm.recipient}
                  onChange={(e) => setTransferForm(prev => ({ ...prev, recipient: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  {language === 'ar' ? 'المبلغ (دج)' : 'Montant (DA)'}
                </Label>
                <Input
                  type="number"
                  placeholder="0"
                  value={transferForm.amount}
                  onChange={(e) => setTransferForm(prev => ({ ...prev, amount: e.target.value }))}
                  min="1"
                />
              </div>
              <div className="space-y-2">
                <Label>{language === 'ar' ? 'ملاحظة (اختياري)' : 'Note (optionnel)'}</Label>
                <Input
                  placeholder={language === 'ar' ? 'سبب التحويل' : 'Raison du transfert'}
                  value={transferForm.note}
                  onChange={(e) => setTransferForm(prev => ({ ...prev, note: e.target.value }))}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowTransferDialog(false)}>
                {language === 'ar' ? 'إلغاء' : 'Annuler'}
              </Button>
              <Button onClick={handleTransfer} disabled={loading}>
                {loading ? (
                  <Loader2 className="h-4 w-4 me-2 animate-spin" />
                ) : (
                  <Send className="h-4 w-4 me-2" />
                )}
                {language === 'ar' ? 'تحويل' : 'Transférer'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
