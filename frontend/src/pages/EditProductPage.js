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
    name_en: '',
    name_ar: '',
    description_en: '',
    description_ar: '',
    price: '',
    quantity: '',
    image_url: '',
    compatible_models: ''
  });

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`${API}/products/${id}`);
        const product = response.data;
        setFormData({
          name_en: product.name_en,
          name_ar: product.name_ar,
          description_en: product.description_en || '',
          description_ar: product.description_ar || '',
          price: product.price.toString(),
          quantity: product.quantity.toString(),
          image_url: product.image_url || '',
          compatible_models: product.compatible_models.join(', ')
        });
      } catch (error) {
        console.error('Error fetching product:', error);
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
        price: parseFloat(formData.price) || 0,
        quantity: parseInt(formData.quantity) || 0,
        image_url: formData.image_url,
        compatible_models: formData.compatible_models
          .split(',')
          .map(m => m.trim())
          .filter(m => m)
      };

      await axios.put(`${API}/products/${id}`, payload);
      toast.success(t.productUpdated);
      navigate(`/products/${id}`);
    } catch (error) {
      console.error('Error updating product:', error);
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
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
      <div className="max-w-3xl mx-auto space-y-6 animate-fade-in" data-testid="edit-product-page">
        {/* Back Button */}
        <Link to={`/products/${id}`}>
          <Button variant="ghost" className="gap-2" data-testid="back-to-product-btn">
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
                    className="h-11"
                    data-testid="edit-name-en-input"
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
                    className="h-11"
                    dir="rtl"
                    data-testid="edit-name-ar-input"
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
                    rows={3}
                    data-testid="edit-desc-en-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description_ar">{t.descriptionAr}</Label>
                  <Textarea
                    id="description_ar"
                    name="description_ar"
                    value={formData.description_ar}
                    onChange={handleChange}
                    rows={3}
                    dir="rtl"
                    data-testid="edit-desc-ar-input"
                  />
                </div>
              </div>

              {/* Price & Quantity */}
              <div className="form-grid">
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
                    className="h-11"
                    data-testid="edit-price-input"
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
                    className="h-11"
                    data-testid="edit-quantity-input"
                  />
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
                  className="h-11"
                  data-testid="edit-image-input"
                />
              </div>

              {/* Compatible Models */}
              <div className="space-y-2">
                <Label htmlFor="compatible_models">{t.compatibleModels} *</Label>
                <Textarea
                  id="compatible_models"
                  name="compatible_models"
                  value={formData.compatible_models}
                  onChange={handleChange}
                  required
                  rows={3}
                  data-testid="edit-models-input"
                />
                <p className="text-sm text-muted-foreground">{t.compatibleModelsHelp}</p>
              </div>

              {/* Submit Button */}
              <div className="flex justify-end gap-4 pt-4">
                <Link to={`/products/${id}`}>
                  <Button type="button" variant="outline" data-testid="cancel-edit-btn">
                    {t.cancel}
                  </Button>
                </Link>
                <Button 
                  type="submit" 
                  disabled={loading}
                  className="gap-2"
                  data-testid="update-product-btn"
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
