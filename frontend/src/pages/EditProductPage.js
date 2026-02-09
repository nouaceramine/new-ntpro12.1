import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import { ArrowRight, ArrowLeft, Save, Camera, Loader2, RefreshCw, Plus, FolderTree, Calculator } from 'lucide-react';
import { Switch } from '../components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function EditProductPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t, language, isRTL } = useLanguage();
  const BackArrow = isRTL ? ArrowRight : ArrowLeft;
  const fileInputRef = useRef(null);
  const imageUploadRef = useRef(null);
  
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [generatingBarcode, setGeneratingBarcode] = useState(false);
  const [uploadingProductImage, setUploadingProductImage] = useState(false);
  const [families, setFamilies] = useState([]);
  const [showAddFamilyDialog, setShowAddFamilyDialog] = useState(false);
  const [newFamily, setNewFamily] = useState({ name: '' });
  const [addingFamily, setAddingFamily] = useState(false);
  const [useAveragePrice, setUseAveragePrice] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description_en: '',
    purchase_price: '0',
    wholesale_price: '0',
    super_wholesale_price: '0',
    retail_price: '0',
    quantity: '0',
    image_url: '',
    barcode: '',
    article_code: '',
    family_id: '',
    compatible_models: '',
    low_stock_threshold: '10'
  });

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`${API}/products/${id}`);
        const p = response.data;
        setFormData({
          name: p.name_en || p.name_ar || '',
          description_en: p.description_en || '',
          purchase_price: p.purchase_price?.toString() || '0',
          wholesale_price: p.wholesale_price?.toString() || '0',
          super_wholesale_price: p.super_wholesale_price?.toString() || '0',
          retail_price: p.retail_price?.toString() || '0',
          quantity: p.quantity?.toString() || '0',
          image_url: p.image_url || '',
          barcode: p.barcode || '',
          article_code: p.article_code || '',
          family_id: p.family_id || '',
          compatible_models: Array.isArray(p.compatible_models) ? p.compatible_models.join(', ') : '',
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
    fetchFamilies();
  }, [id, navigate, t.notFound]);

  const fetchFamilies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/product-families`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFamilies(response.data);
    } catch (error) {
      console.error('Error fetching families:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Upload product image
  const handleProductImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploadingProductImage(true);
    try {
      const reader = new FileReader();
      reader.onload = (event) => {
        setFormData(prev => ({ ...prev, image_url: event.target.result }));
        toast.success(language === 'ar' ? 'تم رفع الصورة' : 'Image téléchargée');
        setUploadingProductImage(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      toast.error(language === 'ar' ? 'فشل رفع الصورة' : 'Échec du téléchargement');
      setUploadingProductImage(false);
    }
  };

  const generateBarcode = async () => {
    setGeneratingBarcode(true);
    try {
      const response = await axios.get(`${API}/products/generate-barcode?article_code=${formData.article_code}`);
      setFormData(prev => ({ ...prev, barcode: response.data.barcode }));
      toast.success(t.barcodeGenerated);
    } catch (error) {
      toast.error(t.error);
    } finally {
      setGeneratingBarcode(false);
    }
  };

  const handleAddFamily = async () => {
    if (!newFamily.name) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم العائلة' : 'Veuillez entrer le nom de la famille');
      return;
    }

    setAddingFamily(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/product-families`, {
        name_ar: newFamily.name,
        name_en: newFamily.name
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setFamilies(prev => [...prev, response.data]);
      setFormData(prev => ({ ...prev, family_id: response.data.id }));
      setShowAddFamilyDialog(false);
      setNewFamily({ name: '' });
      toast.success(t.familyAdded);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setAddingFamily(false);
    }
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
    
    if (!formData.name.trim()) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم المنتج' : 'Veuillez entrer le nom du produit');
      return;
    }
    
    setLoading(true);

    try {
      const payload = {
        name_en: formData.name,
        name_ar: formData.name,
        description_en: formData.description_en,
        description_ar: formData.description_en,
        purchase_price: parseFloat(formData.purchase_price) || 0,
        wholesale_price: parseFloat(formData.wholesale_price) || 0,
        super_wholesale_price: parseFloat(formData.super_wholesale_price) || 0,
        retail_price: parseFloat(formData.retail_price) || 0,
        image_url: formData.image_url,
        barcode: formData.barcode,
        family_id: formData.family_id || null,
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
          <Button variant="ghost" size="sm" className="gap-2" data-testid="back-to-product-btn">
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
              {/* Product Name, Article Code & Family */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'ar' ? 'اسم المنتج' : 'Nom du produit'} *</Label>
                  <Input 
                    name="name" 
                    value={formData.name} 
                    onChange={handleChange} 
                    required 
                    className="h-9" 
                    data-testid="product-name-input"
                    placeholder={language === 'ar' ? 'يقبل العربية والفرنسية' : 'Accepte arabe et français'}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'ar' ? 'كود المنتج' : 'Code Article'}</Label>
                  <Input 
                    name="article_code" 
                    value={formData.article_code} 
                    className="h-9 font-mono text-sm bg-muted/50" 
                    data-testid="article-code-input"
                    placeholder="AR00001"
                    readOnly
                  />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">{t.productFamilies}</Label>
                    <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddFamilyDialog(true)} className="h-5 px-1 text-xs">
                      <Plus className="h-3 w-3" />
                      {t.quickAddFamily}
                    </Button>
                  </div>
                  <Select value={formData.family_id || "none"} onValueChange={(v) => setFormData({...formData, family_id: v === "none" ? "" : v})}>
                    <SelectTrigger className="h-9" data-testid="family-select">
                      <FolderTree className="h-3 w-3 me-1" />
                      <SelectValue placeholder={t.selectFamily} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">{language === 'ar' ? 'بدون عائلة' : 'No Family'}</SelectItem>
                      {families.map((f) => (
                        <SelectItem key={f.id} value={f.id}>
                          {language === 'ar' ? f.name_ar : f.name_en}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Image Upload & Description */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'ar' ? 'صورة المنتج' : 'Image produit'}</Label>
                  <div className="flex gap-2">
                    <Input 
                      name="image_url" 
                      value={formData.image_url} 
                      onChange={handleChange} 
                      placeholder="URL..."
                      className="h-9 flex-1" 
                    />
                    <input
                      ref={imageUploadRef}
                      type="file"
                      accept="image/*"
                      onChange={handleProductImageUpload}
                      className="hidden"
                      id="product-image-upload"
                    />
                    <Button 
                      type="button" 
                      variant="outline" 
                      size="sm" 
                      onClick={() => imageUploadRef.current?.click()}
                      disabled={uploadingProductImage}
                      className="h-9 px-2"
                    >
                      {uploadingProductImage ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
                    </Button>
                  </div>
                  {formData.image_url && (
                    <img src={formData.image_url} alt="Preview" className="h-16 w-16 object-cover rounded mt-1" />
                  )}
                </div>
                <div className="col-span-2 space-y-1">
                  <Label className="text-xs">{language === 'ar' ? 'الوصف' : 'Description'}</Label>
                  <Input name="description_en" value={formData.description_en} onChange={handleChange} className="h-9" placeholder={language === 'ar' ? 'وصف المنتج...' : 'Description du produit...'} />
                </div>
              </div>

              {/* Prices - 4 columns with super wholesale */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">{t.purchasePrice} *</Label>
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
                  <Input name="purchase_price" type="number" step="0.01" min="0" value={formData.purchase_price} onChange={handleChange} className="h-9" data-testid="purchase-price-input" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{language === 'ar' ? 'سوبر الجملة' : 'Super gros'}</Label>
                  <Input name="super_wholesale_price" type="number" step="0.01" min="0" value={formData.super_wholesale_price} onChange={handleChange} className="h-9" data-testid="super-wholesale-price-input" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.wholesalePrice} *</Label>
                  <Input name="wholesale_price" type="number" step="0.01" min="0" value={formData.wholesale_price} onChange={handleChange} className="h-9" data-testid="wholesale-price-input" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.retailPrice} *</Label>
                  <Input name="retail_price" type="number" step="0.01" min="0" value={formData.retail_price} onChange={handleChange} className="h-9" data-testid="retail-price-input" />
                </div>
              </div>

              {/* Quantity (read-only), Threshold, Barcode */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs flex items-center gap-1">
                    {t.quantity}
                    <span className="text-[10px] text-muted-foreground">({language === 'ar' ? 'للقراءة فقط' : 'lecture seule'})</span>
                  </Label>
                  <Input name="quantity" type="number" value={formData.quantity} readOnly disabled className="h-9 bg-muted cursor-not-allowed" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t.lowStockThreshold}</Label>
                  <Input name="low_stock_threshold" type="number" min="1" value={formData.low_stock_threshold} onChange={handleChange} className="h-9" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">{t.barcode}</Label>
                    <Button type="button" variant="ghost" size="sm" onClick={generateBarcode} disabled={generatingBarcode} className="h-5 px-1 text-xs">
                      {generatingBarcode ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
                      {t.generateBarcode}
                    </Button>
                  </div>
                  <Input name="barcode" value={formData.barcode} onChange={handleChange} className="h-9 font-mono" data-testid="barcode-input" />
                </div>
              </div>

              {/* Stock Info */}
              <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                <p className="text-xs text-amber-700 dark:text-amber-400 flex items-center gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  {language === 'ar' 
                    ? 'لتعديل الكمية، قم بإنشاء عملية شراء جديدة من صفحة المشتريات.'
                    : 'Pour modifier la quantité, créez un nouvel achat depuis la page des achats.'}
                </p>
              </div>

              {/* Compatible Models with OCR */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="compatible_models">{t.compatibleModels}</Label>
                  <div>
                    <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleImageUpload} className="hidden" id="ocr-upload" />
                    <Button type="button" variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={ocrLoading} className="gap-2" data-testid="ocr-upload-btn">
                      {ocrLoading ? <><Loader2 className="h-3 w-3 animate-spin" />{t.extractingModels}</> : <><Camera className="h-3 w-3" />{t.extractFromImage}</>}
                    </Button>
                  </div>
                </div>
                <Textarea name="compatible_models" value={formData.compatible_models} onChange={handleChange} placeholder="iPhone 15 Pro, Samsung Galaxy S24" rows={2} className="text-sm" data-testid="product-models-input" />
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

      {/* Add Family Dialog */}
      <Dialog open={showAddFamilyDialog} onOpenChange={setShowAddFamilyDialog}>
        <DialogContent className="max-w-xs">
          <DialogHeader className="pb-2">
            <DialogTitle className="text-lg">{t.addNewFamily}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label className="text-xs">{language === 'ar' ? 'اسم العائلة' : 'Nom de la famille'}</Label>
              <Input className="h-9" value={newFamily.name} onChange={(e) => setNewFamily({...newFamily, name: e.target.value})} placeholder={language === 'ar' ? 'مثال: شاشات' : 'Ex: Écrans'} />
            </div>
            <div className="flex gap-2 pt-1">
              <Button variant="outline" size="sm" onClick={() => setShowAddFamilyDialog(false)} className="flex-1">{t.cancel}</Button>
              <Button size="sm" onClick={handleAddFamily} disabled={addingFamily} className="flex-1">{addingFamily ? t.loading : t.save}</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
