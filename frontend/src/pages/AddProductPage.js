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
import { ArrowRight, ArrowLeft, Save, Upload, Camera, Loader2 } from 'lucide-react';

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
    price: '',
    quantity: '',
    image_url: '',
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

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error(t.supportedFormats);
      return;
    }

    setOcrLoading(true);

    try {
      // Convert to base64
      const base64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result;
          // Remove the data:image/...;base64, prefix
          const base64Data = result.split(',')[1];
          resolve(base64Data);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      // Call OCR API
      const response = await axios.post(`${API}/ocr/extract-models`, {
        image_base64: base64
      });

      const { extracted_models } = response.data;
      
      if (extracted_models.length > 0) {
        // Append to existing models
        const currentModels = formData.compatible_models.trim();
        const newModels = extracted_models.join(', ');
        const combinedModels = currentModels 
          ? `${currentModels}, ${newModels}` 
          : newModels;
        
        setFormData(prev => ({
          ...prev,
          compatible_models: combinedModels
        }));
        
        toast.success(`${t.modelsExtracted} (${extracted_models.length})`);
      } else {
        toast.info(t.noProducts);
      }
    } catch (error) {
      console.error('OCR error:', error);
      toast.error(t.ocrFailed);
    } finally {
      setOcrLoading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
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
        price: parseFloat(formData.price) || 0,
        quantity: parseInt(formData.quantity) || 0,
        image_url: formData.image_url,
        compatible_models: formData.compatible_models
          .split(',')
          .map(m => m.trim())
          .filter(m => m),
        low_stock_threshold: parseInt(formData.low_stock_threshold) || 10
      };

      await axios.post(`${API}/products`, payload);
      toast.success(t.productAdded);
      navigate('/products');
    } catch (error) {
      console.error('Error adding product:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-6 animate-fade-in" data-testid="add-product-page">
        {/* Back Button */}
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
              <div className="form-grid">
                <div className="space-y-2">
                  <Label htmlFor="name_en">{t.productNameEn} *</Label>
                  <Input
                    id="name_en"
                    name="name_en"
                    value={formData.name_en}
                    onChange={handleChange}
                    required
                    placeholder="Premium Tempered Glass"
                    className="h-11"
                    data-testid="product-name-en-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name_ar">{t.productNameAr} *</Label>
                  <Input
                    id="name_ar"
                    name="name_ar"
                    value={formData.name_ar}
                    onChange={handleChange}
                    required
                    placeholder="زجاج حماية فاخر"
                    className="h-11"
                    dir="rtl"
                    data-testid="product-name-ar-input"
                  />
                </div>
              </div>

              {/* Descriptions */}
              <div className="form-grid">
                <div className="space-y-2">
                  <Label htmlFor="description_en">{t.descriptionEn}</Label>
                  <Textarea
                    id="description_en"
                    name="description_en"
                    value={formData.description_en}
                    onChange={handleChange}
                    placeholder="High-quality tempered glass screen protector..."
                    rows={3}
                    data-testid="product-desc-en-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description_ar">{t.descriptionAr}</Label>
                  <Textarea
                    id="description_ar"
                    name="description_ar"
                    value={formData.description_ar}
                    onChange={handleChange}
                    placeholder="زجاج حماية عالي الجودة..."
                    rows={3}
                    dir="rtl"
                    data-testid="product-desc-ar-input"
                  />
                </div>
              </div>

              {/* Price, Quantity & Low Stock Threshold */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="price">{t.price} ($) *</Label>
                  <Input
                    id="price"
                    name="price"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.price}
                    onChange={handleChange}
                    required
                    placeholder="9.99"
                    className="h-11"
                    data-testid="product-price-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="quantity">{t.quantity} *</Label>
                  <Input
                    id="quantity"
                    name="quantity"
                    type="number"
                    min="0"
                    value={formData.quantity}
                    onChange={handleChange}
                    required
                    placeholder="100"
                    className="h-11"
                    data-testid="product-quantity-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="low_stock_threshold">{t.lowStockThreshold}</Label>
                  <Input
                    id="low_stock_threshold"
                    name="low_stock_threshold"
                    type="number"
                    min="1"
                    value={formData.low_stock_threshold}
                    onChange={handleChange}
                    placeholder="10"
                    className="h-11"
                    data-testid="product-threshold-input"
                  />
                  <p className="text-xs text-muted-foreground">{t.lowStockThresholdHelp}</p>
                </div>
              </div>

              {/* Image URL */}
              <div className="space-y-2">
                <Label htmlFor="image_url">{t.imageUrl}</Label>
                <Input
                  id="image_url"
                  name="image_url"
                  type="url"
                  value={formData.image_url}
                  onChange={handleChange}
                  placeholder="https://example.com/image.jpg"
                  className="h-11"
                  data-testid="product-image-input"
                />
              </div>

              {/* Compatible Models with OCR */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="compatible_models">{t.compatibleModels} *</Label>
                  <div className="flex gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleImageUpload}
                      className="hidden"
                      id="ocr-upload"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={ocrLoading}
                      className="gap-2"
                      data-testid="ocr-upload-btn"
                    >
                      {ocrLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          {t.extractingModels}
                        </>
                      ) : (
                        <>
                          <Camera className="h-4 w-4" />
                          {t.extractFromImage}
                        </>
                      )}
                    </Button>
                  </div>
                </div>
                <Textarea
                  id="compatible_models"
                  name="compatible_models"
                  value={formData.compatible_models}
                  onChange={handleChange}
                  required
                  placeholder="iPhone 15 Pro, iPhone 15 Pro Max, iPhone 14 Pro"
                  rows={3}
                  data-testid="product-models-input"
                />
                <p className="text-sm text-muted-foreground">{t.compatibleModelsHelp}</p>
              </div>

              {/* Submit Button */}
              <div className="flex justify-end gap-4 pt-4">
                <Link to="/products">
                  <Button type="button" variant="outline" data-testid="cancel-add-btn">
                    {t.cancel}
                  </Button>
                </Link>
                <Button 
                  type="submit" 
                  disabled={loading}
                  className="gap-2"
                  data-testid="save-product-btn"
                >
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
