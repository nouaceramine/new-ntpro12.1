import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Wifi,
  Send,
  History,
  ArrowRight,
  Globe,
  Loader2,
  CheckCircle2,
  XCircle,
  Router
} from 'lucide-react';
import { Link } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Idoom offers
const IDOOM_OFFERS = [
  { id: 'adsl_500', name: '500 دج - ADSL', price: 500, type: 'adsl' },
  { id: 'adsl_1000', name: '1000 دج - ADSL', price: 1000, type: 'adsl' },
  { id: 'adsl_2000', name: '2000 دج - ADSL', price: 2000, type: 'adsl' },
  { id: '4g_500', name: '500 دج - 4G LTE', price: 500, type: '4g' },
  { id: '4g_1000', name: '1000 دج - 4G LTE', price: 1000, type: '4g' },
  { id: '4g_1500', name: '1500 دج - 4G LTE', price: 1500, type: '4g' },
  { id: '4g_2000', name: '2000 دج - 4G LTE', price: 2000, type: '4g' },
  { id: '4g_2500', name: '2500 دج - 4G LTE', price: 2500, type: '4g' },
];

export default function IdoomServicePage() {
  const { language } = useLanguage();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [selectedOffer, setSelectedOffer] = useState(null);
  const [offerType, setOfferType] = useState('4g');
  const [loading, setLoading] = useState(false);
  const [recentTransactions, setRecentTransactions] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!phoneNumber) {
      toast.error(language === 'ar' ? 'يرجى إدخال رقم الهاتف أو الحساب' : 'Veuillez entrer le numéro');
      return;
    }

    if (!selectedOffer) {
      toast.error(language === 'ar' ? 'يرجى اختيار عرض' : 'Veuillez choisir une offre');
      return;
    }

    setLoading(true);
    try {
      // Simulated API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const offer = IDOOM_OFFERS.find(o => o.id === selectedOffer);
      toast.success(
        language === 'ar' 
          ? `تم تعبئة ${offer.name} بنجاح`
          : `${offer.name} rechargé avec succès`
      );

      setRecentTransactions(prev => [{
        id: Date.now(),
        phone: phoneNumber,
        offer: offer.name,
        amount: offer.price,
        type: offer.type,
        status: 'success',
        date: new Date().toISOString()
      }, ...prev.slice(0, 9)]);

      setPhoneNumber('');
      setSelectedOffer(null);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل في عملية التعبئة' : 'Échec de la recharge');
    } finally {
      setLoading(false);
    }
  };

  const filteredOffers = IDOOM_OFFERS.filter(o => o.type === offerType);

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="idoom-service-page">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link to="/services">
            <Button variant="ghost" size="icon">
              <ArrowRight className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <Wifi className="h-8 w-8 text-emerald-500" />
              </div>
              {language === 'ar' ? 'تعبئة أيدوم' : 'Recharge Idoom'}
            </h1>
            <p className="text-muted-foreground mt-1">
              {language === 'ar' ? 'تعبئة رصيد الإنترنت ADSL و 4G' : 'Recharge internet ADSL et 4G'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recharge Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  {language === 'ar' ? 'تعبئة جديدة' : 'Nouvelle recharge'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Phone/Account Number */}
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'رقم الهاتف أو الحساب' : 'Numéro de téléphone ou compte'}</Label>
                    <Input
                      type="text"
                      placeholder={language === 'ar' ? 'أدخل الرقم' : 'Entrez le numéro'}
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      className="text-lg h-12 font-mono"
                      dir="ltr"
                      data-testid="idoom-number-input"
                    />
                  </div>

                  {/* Offer Type Selection */}
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'نوع الخدمة' : 'Type de service'}</Label>
                    <div className="grid grid-cols-2 gap-3">
                      <Button
                        type="button"
                        variant={offerType === '4g' ? 'default' : 'outline'}
                        className="h-16 flex-col gap-1"
                        onClick={() => {
                          setOfferType('4g');
                          setSelectedOffer(null);
                        }}
                      >
                        <Router className="h-6 w-6" />
                        <span>4G LTE</span>
                      </Button>
                      <Button
                        type="button"
                        variant={offerType === 'adsl' ? 'default' : 'outline'}
                        className="h-16 flex-col gap-1"
                        onClick={() => {
                          setOfferType('adsl');
                          setSelectedOffer(null);
                        }}
                      >
                        <Globe className="h-6 w-6" />
                        <span>ADSL</span>
                      </Button>
                    </div>
                  </div>

                  {/* Offer Selection */}
                  <div className="space-y-2">
                    <Label>{language === 'ar' ? 'اختر العرض' : 'Choisir l\'offre'}</Label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {filteredOffers.map((offer) => (
                        <Button
                          key={offer.id}
                          type="button"
                          variant={selectedOffer === offer.id ? 'default' : 'outline'}
                          className={`h-auto py-3 flex-col ${selectedOffer === offer.id ? 'ring-2 ring-primary' : ''}`}
                          onClick={() => setSelectedOffer(offer.id)}
                        >
                          <span className="text-lg font-bold">{offer.price} دج</span>
                          <span className="text-xs opacity-80">{offer.type.toUpperCase()}</span>
                        </Button>
                      ))}
                    </div>
                  </div>

                  {/* Submit Button */}
                  <Button 
                    type="submit" 
                    className="w-full h-14 text-lg bg-emerald-600 hover:bg-emerald-700"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-5 w-5 me-2 animate-spin" />
                        {language === 'ar' ? 'جاري التعبئة...' : 'Recharge en cours...'}
                      </>
                    ) : (
                      <>
                        <Send className="h-5 w-5 me-2" />
                        {language === 'ar' ? 'تعبئة الآن' : 'Recharger maintenant'}
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Recent Transactions */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  {language === 'ar' ? 'آخر العمليات' : 'Dernières opérations'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {recentTransactions.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Wifi className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>{language === 'ar' ? 'لا توجد عمليات حديثة' : 'Aucune opération récente'}</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recentTransactions.map((tx) => (
                      <div key={tx.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-3">
                          {tx.status === 'success' ? (
                            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-500" />
                          )}
                          <div>
                            <p className="font-mono text-sm">{tx.phone}</p>
                            <p className="text-xs text-muted-foreground">{tx.offer}</p>
                          </div>
                        </div>
                        <div className="text-end">
                          <p className="font-bold text-emerald-600">{tx.amount} دج</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(tx.date).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
}
