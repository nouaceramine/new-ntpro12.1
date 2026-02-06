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
import { ArrowRight, ArrowLeft, Save } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function EditProductPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t, isRTL } = useLanguage();
  const BackArrow = isRTL ? ArrowRight : ArrowLeft;
  
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [formData, setFormData] = useState({
    name_en: '', name_ar: '', description_en: '', description_ar: '',
    purchase_price: '', wholesale_price: '', retail_price: '',
    quantity: '', image_url: '', barcode: '', compatible_models: '', low_stock_threshold: ''
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
          retail_price: p.retail_price?.toString() || '0',
          quantity: p.quantity.toString(),
          image_url: p.image_url || '',
          barcode: p.barcode || '',
          compatible_models: p.compatible_models.join(', '),
          low_stock_threshold: p.low_stock_threshold?.toString() || '10'
        });
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
        retail_price: parseFloat(formData.retail_price) || 0,
        quantity: parseInt(formData.quantity) || 0,
        image_url: formData.image_url,
        barcode: formData.barcode,
        compatible_models: formData.compatible_models.split(',').map(m => m.trim()).filter(m => m),
        low_stock_threshold: parseInt(formData.low_stock_threshold) || 10
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
      <div className="max-w-3xl mx-auto space-y-6 animate-fade-in" data-testid="edit-product-page">
        <Link to={`/products/${id}`}>
          <Button variant="ghost" className="gap-2">
            <BackArrow className="h-4 w-4" />
            {t.viewDetails}
          </Button>
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">{t.editProduct}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Names */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>{t.productNameEn} *</Label>
                  <Input name="name_en" value={formData.name_en} onChange={handleChange} required className="h-11" />
                </div>
                <div className="space-y-2">
                  <Label>{t.productNameAr} *</Label>
                  <Input name="name_ar" value={formData.name_ar} onChange={handleChange} required className="h-11" dir="rtl" />
                </div>
              </div>

              {/* Descriptions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>{t.descriptionEn}</Label>
                  <Textarea name="description_en" value={formData.description_en} onChange={handleChange} rows={2} />
                </div>
                <div className="space-y-2">
                  <Label>{t.descriptionAr}</Label>
                  <Textarea name="description_ar" value={formData.description_ar} onChange={handleChange} rows={2} dir="rtl" />
                </div>
              </div>

              {/* Prices */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label>{t.purchasePrice} ({t.currency})</Label>
                  <Input name="purchase_price" type="number" step="0.01" min="0" value={formData.purchase_price} onChange={handleChange} className="h-11" />
                </div>
                <div className="space-y-2">
                  <Label>{t.wholesalePrice} ({t.currency})</Label>
                  <Input name="wholesale_price" type="number" step="0.01" min="0" value={formData.wholesale_price} onChange={handleChange} className="h-11" />
                </div>
                <div className="space-y-2">
                  <Label>{t.retailPrice} ({t.currency})</Label>
                  <Input name="retail_price" type="number" step="0.01" min="0" value={formData.retail_price} onChange={handleChange} className="h-11" />
                </div>
              </div>

              {/* Quantity & Barcode */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label>{t.quantity}</Label>
                  <Input name="quantity" type="number" min="0" value={formData.quantity} onChange={handleChange} className="h-11" />
                </div>
                <div className="space-y-2">
                  <Label>{t.lowStockThreshold}</Label>
                  <Input name="low_stock_threshold" type="number" min="1" value={formData.low_stock_threshold} onChange={handleChange} className="h-11" />
                </div>
                <div className="space-y-2">
                  <Label>{t.barcode}</Label>
                  <Input name="barcode" value={formData.barcode} onChange={handleChange} className="h-11" />
                </div>
              </div>

              {/* Image URL */}
              <div className="space-y-2">
                <Label>{t.imageUrl}</Label>
                <Input name="image_url" type="url" value={formData.image_url} onChange={handleChange} className="h-11" />
              </div>

              {/* Compatible Models */}
              <div className="space-y-2">
                <Label>{t.compatibleModels}</Label>
                <Textarea name="compatible_models" value={formData.compatible_models} onChange={handleChange} rows={3} />
                <p className="text-sm text-muted-foreground">{t.compatibleModelsHelp}</p>
              </div>

              {/* Submit */}
              <div className="flex justify-end gap-4 pt-4">
                <Link to={`/products/${id}`}>
                  <Button type="button" variant="outline">{t.cancel}</Button>
                </Link>
                <Button type="submit" disabled={loading} className="gap-2" data-testid="update-product-btn">
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
