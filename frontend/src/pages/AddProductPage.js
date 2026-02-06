import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { ArrowRight, ArrowLeft, Save, Camera, Loader2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AddProductPage() {
  const navigate = useNavigate();
  const { t, isRTL } = useLanguage();
  const BackArrow = isRTL ? ArrowRight : ArrowLeft;
  const fileInputRef = useRef(null);
  
  const [loading, setLoading] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [formData, setFormData] = useState({
    name_en: '',
    name_ar: '',
    description_en: '',
    description_ar: '',
    purchase_price: '',
    wholesale_price: '',
    retail_price: '',
    quantity: '',
    image_url: '',
    barcode: '',
    compatible_models: '',
    low_stock_threshold: '10'
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error(t.supportedFormats);
      return;
    }

    setOcrLoading(true);
    try {
      const base64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      const response = await axios.post(`${API}/ocr/extract-models`, { image_base64: base64 });
      const { extracted_models } = response.data;
      
      if (extracted_models.length > 0) {
        const currentModels = formData.compatible_models.trim();
        const newModels = extracted_models.join(', ');
        setFormData(prev => ({
          ...prev,
          compatible_models: currentModels ? `${currentModels}, ${newModels}` : newModels
        }));
        toast.success(`${t.modelsExtracted} (${extracted_models.length})`);
      }
    } catch (error) {
      toast.error(t.ocrFailed);
    } finally {
      setOcrLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
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

      await axios.post(`${API}/products`, payload);
      toast.success(t.productAdded);
      navigate('/products');
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-6 animate-fade-in" data-testid="add-product-page">
        <Link to="/products">
          <Button variant="ghost" className="gap-2" data-testid="back-to-products-btn">
            <BackArrow className="h-4 w-4" />
            {t.products}
          </Button>
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">{t.addNewProduct}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Product Names */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="name_en">{t.productNameEn} *</Label>
                  <Input id="name_en" name="name_en" value={formData.name_en} onChange={handleChange} required className="h-11" data-testid="product-name-en-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name_ar">{t.productNameAr} *</Label>
                  <Input id="name_ar" name="name_ar" value={formData.name_ar} onChange={handleChange} required className="h-11" dir="rtl" data-testid="product-name-ar-input" />
                </div>
              </div>

              {/* Descriptions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="description_en">{t.descriptionEn}</Label>
                  <Textarea id="description_en" name="description_en" value={formData.description_en} onChange={handleChange} rows={2} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description_ar">{t.descriptionAr}</Label>
                  <Textarea id="description_ar" name="description_ar" value={formData.description_ar} onChange={handleChange} rows={2} dir="rtl" />
                </div>
              </div>

              {/* Prices */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="purchase_price">{t.purchasePrice} ({t.currency}) *</Label>
                  <Input id="purchase_price" name="purchase_price" type="number" step="0.01" min="0" value={formData.purchase_price} onChange={handleChange} required className="h-11" data-testid="purchase-price-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="wholesale_price">{t.wholesalePrice} ({t.currency}) *</Label>
                  <Input id="wholesale_price" name="wholesale_price" type="number" step="0.01" min="0" value={formData.wholesale_price} onChange={handleChange} required className="h-11" data-testid="wholesale-price-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="retail_price">{t.retailPrice} ({t.currency}) *</Label>
                  <Input id="retail_price" name="retail_price" type="number" step="0.01" min="0" value={formData.retail_price} onChange={handleChange} required className="h-11" data-testid="retail-price-input" />
                </div>
              </div>

              {/* Quantity, Threshold, Barcode */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="quantity">{t.quantity} *</Label>
                  <Input id="quantity" name="quantity" type="number" min="0" value={formData.quantity} onChange={handleChange} required className="h-11" data-testid="product-quantity-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="low_stock_threshold">{t.lowStockThreshold}</Label>
                  <Input id="low_stock_threshold" name="low_stock_threshold" type="number" min="1" value={formData.low_stock_threshold} onChange={handleChange} className="h-11" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="barcode">{t.barcode}</Label>
                  <Input id="barcode" name="barcode" value={formData.barcode} onChange={handleChange} className="h-11" data-testid="barcode-input" />
                </div>
              </div>

              {/* Image URL */}
              <div className="space-y-2">
                <Label htmlFor="image_url">{t.imageUrl}</Label>
                <Input id="image_url" name="image_url" type="url" value={formData.image_url} onChange={handleChange} className="h-11" />
              </div>

              {/* Compatible Models with OCR */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="compatible_models">{t.compatibleModels} *</Label>
                  <div>
                    <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleImageUpload} className="hidden" id="ocr-upload" />
                    <Button type="button" variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={ocrLoading} className="gap-2" data-testid="ocr-upload-btn">
                      {ocrLoading ? <><Loader2 className="h-4 w-4 animate-spin" />{t.extractingModels}</> : <><Camera className="h-4 w-4" />{t.extractFromImage}</>}
                    </Button>
                  </div>
                </div>
                <Textarea id="compatible_models" name="compatible_models" value={formData.compatible_models} onChange={handleChange} required placeholder="iPhone 15 Pro, Samsung Galaxy S24" rows={3} data-testid="product-models-input" />
                <p className="text-sm text-muted-foreground">{t.compatibleModelsHelp}</p>
              </div>

              {/* Submit */}
              <div className="flex justify-end gap-4 pt-4">
                <Link to="/products">
                  <Button type="button" variant="outline">{t.cancel}</Button>
                </Link>
                <Button type="submit" disabled={loading} className="gap-2" data-testid="save-product-btn">
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
