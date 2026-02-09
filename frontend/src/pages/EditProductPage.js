import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { ArrowRight, ArrowLeft, Save, Info, Calculator } from 'lucide-react';
import { Switch } from '../components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function EditProductPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t, language, isRTL } = useLanguage();
  const BackArrow = isRTL ? ArrowRight : ArrowLeft;
  
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [useAveragePrice, setUseAveragePrice] = useState(false);
  const [formData, setFormData] = useState({
    name_en: '', name_ar: '', description_en: '', description_ar: '',
    purchase_price: '', wholesale_price: '', retail_price: '', super_wholesale_price: '',
    quantity: '', image_url: '', barcode: '', article_code: '', compatible_models: '', low_stock_threshold: ''
  });

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`${API}/products/${id}`);
        const p = response.data;
        setFormData({
          name_en: p.name_en, name_ar: p.name_ar,
          description_en: p.description_en || '', description_ar: p.description_ar || '',
          purchase_price: p.purchase_price?.toString() || '0',
          wholesale_price: p.wholesale_price?.toString() || '0',
          super_wholesale_price: p.super_wholesale_price?.toString() || '0',
          retail_price: p.retail_price?.toString() || '0',
          quantity: p.quantity.toString(),
          image_url: p.image_url || '',
          barcode: p.barcode || '',
          article_code: p.article_code || '',
          compatible_models: p.compatible_models.join(', '),
          low_stock_threshold: p.low_stock_threshold?.toString() || '10'
        });
        setUseAveragePrice(p.use_average_price || false);
      } catch (error) {
        toast.error(t.notFound);
        navigate('/products');
      } finally {
        setFetching(false);
      }
    };
    fetchProduct();
  }, [id, navigate, t.notFound]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        name_en: formData.name_en,
        name_ar: formData.name_ar,
        description_en: formData.description_en,
        description_ar: formData.description_ar,
        purchase_price: parseFloat(formData.purchase_price) || 0,
        wholesale_price: parseFloat(formData.wholesale_price) || 0,
        super_wholesale_price: parseFloat(formData.super_wholesale_price) || 0,
        retail_price: parseFloat(formData.retail_price) || 0,
        image_url: formData.image_url,
        barcode: formData.barcode,
        compatible_models: formData.compatible_models.split(',').map(m => m.trim()).filter(m => m),
        low_stock_threshold: parseInt(formData.low_stock_threshold) || 10,
        use_average_price: useAveragePrice
      };

      await axios.put(`${API}/products/${id}`, payload);
      toast.success(t.productUpdated);
      navigate(`/products/${id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return <Layout><div className="flex items-center justify-center min-h-[60vh]"><div className="spinner" /></div></Layout>;
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-4 animate-fade-in" data-testid="edit-product-page">
        <Link to={`/products/${id}`}>
          <Button variant="ghost" size="sm" className="gap-2">
            <BackArrow className="h-4 w-4" />
            {t.viewDetails}
          </Button>
        </Link>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-xl">{t.editProduct}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Names & Article Code */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{t.productNameEn} *</Label>
                  <Input name="name_en" value={formData.name_en} onChange={handleChange} required className="h-9" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.productNameAr} *</Label>
                  <Input name="name_ar" value={formData.name_ar} onChange={handleChange} required className="h-9" dir="rtl" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'ar' ? 'كود المنتج' : 'Code Article'}</Label>
                  <Input 
                    name="article_code" 
                    value={formData.article_code} 
                    className="h-9 font-mono text-sm bg-muted/50" 
                    readOnly
                    placeholder="AR00001"
                  />
                </div>
              </div>

              {/* Descriptions */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{t.descriptionEn}</Label>
                  <Textarea name="description_en" value={formData.description_en} onChange={handleChange} rows={2} className="text-sm" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.descriptionAr}</Label>
                  <Textarea name="description_ar" value={formData.description_ar} onChange={handleChange} rows={2} dir="rtl" className="text-sm" />
                </div>
              </div>

              {/* Prices */}
              <div className="grid grid-cols-4 gap-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">{t.purchasePrice}</Label>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center gap-1">
                            <Calculator className={`h-3 w-3 ${useAveragePrice ? 'text-primary' : 'text-muted-foreground'}`} />
                            <Switch checked={useAveragePrice} onCheckedChange={setUseAveragePrice} className="scale-[0.6]" />
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{language === 'ar' ? 'حساب السعر المتوسط' : 'Calcul prix moyen'}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <Input name="purchase_price" type="number" step="0.01" min="0" value={formData.purchase_price} onChange={handleChange} className="h-9" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'ar' ? 'سوبر الجملة' : 'Super gros'}</Label>
                  <Input name="super_wholesale_price" type="number" step="0.01" min="0" value={formData.super_wholesale_price} onChange={handleChange} className="h-9" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.wholesalePrice}</Label>
                  <Input name="wholesale_price" type="number" step="0.01" min="0" value={formData.wholesale_price} onChange={handleChange} className="h-9" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.retailPrice}</Label>
                  <Input name="retail_price" type="number" step="0.01" min="0" value={formData.retail_price} onChange={handleChange} className="h-9" />
                </div>
              </div>

              {/* Quantity, Threshold, Barcode */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs flex items-center gap-1">
                    {t.quantity}
                    <span className="text-[10px] text-muted-foreground">({language === 'ar' ? 'للقراءة' : 'lecture'})</span>
                  </Label>
                  <Input name="quantity" type="number" value={formData.quantity} readOnly disabled className="h-9 bg-muted cursor-not-allowed" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.lowStockThreshold}</Label>
                  <Input name="low_stock_threshold" type="number" min="1" value={formData.low_stock_threshold} onChange={handleChange} className="h-9" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.barcode}</Label>
                  <Input name="barcode" value={formData.barcode} onChange={handleChange} className="h-9" />
                </div>
              </div>

              {/* Image & Models */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{t.imageUrl}</Label>
                  <Input name="image_url" type="url" value={formData.image_url} onChange={handleChange} className="h-9" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.compatibleModels}</Label>
                  <Input name="compatible_models" value={formData.compatible_models} onChange={handleChange} className="h-9" placeholder={language === 'ar' ? 'مفصولة بفواصل' : 'séparés par virgules'} />
                </div>
              </div>

              {/* Submit */}
              <div className="flex justify-end gap-2 pt-2">
                <Link to={`/products/${id}`}>
                  <Button type="button" variant="outline" size="sm">{t.cancel}</Button>
                </Link>
                <Button type="submit" size="sm" disabled={loading} className="gap-1" data-testid="update-product-btn">
                  <Save className="h-4 w-4" />
                  {loading ? t.loading : t.save}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
