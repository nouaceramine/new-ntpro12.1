import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
import { ArrowRight, ArrowLeft, Save, Camera, Loader2, RefreshCw, Plus, FolderTree, PlusCircle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AddProductPage() {
  const navigate = useNavigate();
  const { t, language, isRTL } = useLanguage();
  const BackArrow = isRTL ? ArrowRight : ArrowLeft;
  const fileInputRef = useRef(null);
  
  const [loading, setLoading] = useState(false);
  const [saveAndNew, setSaveAndNew] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [generatingBarcode, setGeneratingBarcode] = useState(false);
  const [families, setFamilies] = useState([]);
  const [showAddFamilyDialog, setShowAddFamilyDialog] = useState(false);
  const [newFamily, setNewFamily] = useState({ name_ar: '', name_en: '' });
  const [addingFamily, setAddingFamily] = useState(false);
  
  const [formData, setFormData] = useState({
    name_en: '',
    name_ar: '',
    description_en: '',
    description_ar: '',
    purchase_price: '',
    wholesale_price: '',
    retail_price: '',
    image_url: '',
    barcode: '',
    family_id: '',
    compatible_models: '',
    low_stock_threshold: '10'
  });

  useEffect(() => {
    fetchFamilies();
  }, []);

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

  const generateBarcode = async () => {
    setGeneratingBarcode(true);
    try {
      const response = await axios.get(`${API}/products/generate-barcode`);
      setFormData(prev => ({ ...prev, barcode: response.data.barcode }));
      toast.success(t.barcodeGenerated);
    } catch (error) {
      toast.error(t.error);
    } finally {
      setGeneratingBarcode(false);
    }
  };

  const handleAddFamily = async () => {
    if (!newFamily.name_ar && !newFamily.name_en) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم العائلة' : 'Please enter family name');
      return;
    }

    setAddingFamily(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/product-families`, {
        name_ar: newFamily.name_ar || newFamily.name_en,
        name_en: newFamily.name_en || newFamily.name_ar
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setFamilies(prev => [...prev, response.data]);
      setFormData(prev => ({ ...prev, family_id: response.data.id }));
      setShowAddFamilyDialog(false);
      setNewFamily({ name_ar: '', name_en: '' });
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

  const resetForm = () => {
    setFormData({
      name_en: '',
      name_ar: '',
      description_en: '',
      description_ar: '',
      purchase_price: '',
      wholesale_price: '',
      retail_price: '',
      image_url: '',
      barcode: '',
      family_id: '',
      compatible_models: '',
      low_stock_threshold: '10'
    });
  };

  const handleSubmit = async (e, createNew = false) => {
    e?.preventDefault();
    
    // Manual validation for prices
    if (!formData.name_en.trim() || !formData.name_ar.trim()) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم المنتج' : 'Veuillez entrer le nom du produit');
      return;
    }
    
    if (!formData.purchase_price || parseFloat(formData.purchase_price) < 0) {
      toast.error(language === 'ar' ? 'يرجى إدخال سعر الشراء' : 'Veuillez entrer le prix d\'achat');
      return;
    }
    
    if (!formData.wholesale_price || parseFloat(formData.wholesale_price) < 0) {
      toast.error(language === 'ar' ? 'يرجى إدخال سعر الجملة' : 'Veuillez entrer le prix de gros');
      return;
    }
    
    if (!formData.retail_price || parseFloat(formData.retail_price) < 0) {
      toast.error(language === 'ar' ? 'يرجى إدخال سعر التجزئة' : 'Veuillez entrer le prix de détail');
      return;
    }
    
    setLoading(true);
    setSaveAndNew(createNew);

    try {
      const payload = {
        name_en: formData.name_en,
        name_ar: formData.name_ar,
        description_en: formData.description_en,
        description_ar: formData.description_ar,
        purchase_price: parseFloat(formData.purchase_price) || 0,
        wholesale_price: parseFloat(formData.wholesale_price) || 0,
        retail_price: parseFloat(formData.retail_price) || 0,
        quantity: 0,
        image_url: formData.image_url,
        barcode: formData.barcode,
        family_id: formData.family_id || null,
        compatible_models: formData.compatible_models.split(',').map(m => m.trim()).filter(m => m),
        low_stock_threshold: parseInt(formData.low_stock_threshold) || 10
      };

      await axios.post(`${API}/products`, payload);
      toast.success(t.productAdded);
      
      if (createNew) {
        resetForm();
        // Focus on first input
        document.querySelector('[data-testid="product-name-en-input"]')?.focus();
      } else {
        navigate('/products');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setLoading(false);
      setSaveAndNew(false);
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

              {/* Family Selection with Quick Add */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{t.productFamilies}</Label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddFamilyDialog(true)}
                    className="gap-1"
                  >
                    <Plus className="h-4 w-4" />
                    {t.quickAddFamily}
                  </Button>
                </div>
                <Select value={formData.family_id || "none"} onValueChange={(v) => setFormData({...formData, family_id: v === "none" ? "" : v})}>
                  <SelectTrigger data-testid="family-select">
                    <FolderTree className="h-4 w-4 me-2" />
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
                  <Input id="purchase_price" name="purchase_price" type="number" step="0.01" min="0" value={formData.purchase_price} onChange={handleChange} className="h-11" data-testid="purchase-price-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="wholesale_price">{t.wholesalePrice} ({t.currency}) *</Label>
                  <Input id="wholesale_price" name="wholesale_price" type="number" step="0.01" min="0" value={formData.wholesale_price} onChange={handleChange} className="h-11" data-testid="wholesale-price-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="retail_price">{t.retailPrice} ({t.currency}) *</Label>
                  <Input id="retail_price" name="retail_price" type="number" step="0.01" min="0" value={formData.retail_price} onChange={handleChange} className="h-11" data-testid="retail-price-input" />
                </div>
              </div>

              {/* Threshold, Barcode */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="low_stock_threshold">{t.lowStockThreshold}</Label>
                  <Input id="low_stock_threshold" name="low_stock_threshold" type="number" min="1" value={formData.low_stock_threshold} onChange={handleChange} className="h-11" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="barcode">{t.barcode}</Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={generateBarcode}
                      disabled={generatingBarcode}
                      className="gap-1 h-auto py-1"
                    >
                      {generatingBarcode ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      {t.generateBarcode}
                    </Button>
                  </div>
                  <Input 
                    id="barcode" 
                    name="barcode" 
                    value={formData.barcode} 
                    onChange={handleChange} 
                    className="h-11 font-mono" 
                    data-testid="barcode-input" 
                  />
                </div>
              </div>

              {/* Stock Info */}
              <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                <p className="text-sm text-amber-700 dark:text-amber-400 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  {language === 'ar' 
                    ? 'المخزون يبدأ من 0. لإضافة كمية، قم بإنشاء عملية شراء جديدة من صفحة المشتريات.'
                    : 'Le stock commence à 0. Pour ajouter une quantité, créez un nouvel achat depuis la page des achats.'}
                </p>
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
              <div className="flex justify-end gap-3 pt-4">
                <Link to="/products">
                  <Button type="button" variant="outline">{t.cancel}</Button>
                </Link>
                <Button 
                  type="button" 
                  variant="outline"
                  onClick={() => handleSubmit(null, true)} 
                  disabled={loading} 
                  className="gap-2" 
                  data-testid="save-and-new-btn"
                >
                  <PlusCircle className="h-4 w-4" />
                  {language === 'ar' ? 'حفظ وإنشاء جديد' : 'Enregistrer et créer nouveau'}
                </Button>
                <Button type="submit" disabled={loading} className="gap-2" data-testid="save-product-btn">
                  <Save className="h-4 w-4" />
                  {loading && !saveAndNew ? t.loading : t.save}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Add Family Dialog */}
      <Dialog open={showAddFamilyDialog} onOpenChange={setShowAddFamilyDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{t.addNewFamily}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t.familyNameAr}</Label>
              <Input
                value={newFamily.name_ar}
                onChange={(e) => setNewFamily({...newFamily, name_ar: e.target.value})}
                dir="rtl"
                placeholder={language === 'ar' ? 'مثال: واقيات الشاشة' : 'e.g., Screen Protectors'}
              />
            </div>
            <div>
              <Label>{t.familyNameEn}</Label>
              <Input
                value={newFamily.name_en}
                onChange={(e) => setNewFamily({...newFamily, name_en: e.target.value})}
                placeholder="e.g., Screen Protectors"
              />
            </div>
            <div className="flex gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowAddFamilyDialog(false)} className="flex-1">
                {t.cancel}
              </Button>
              <Button onClick={handleAddFamily} disabled={addingFamily} className="flex-1">
                {addingFamily ? t.loading : t.save}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
