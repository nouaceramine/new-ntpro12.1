import { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout } from '../components/Layout';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import { 
  DollarSign,
  Percent,
  Calculator,
  ArrowUp,
  ArrowDown,
  RefreshCw,
  Check,
  Eye
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BulkPriceUpdatePage() {
  const { t, language } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [families, setFamilies] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [totalProducts, setTotalProducts] = useState(0);
  const [applying, setApplying] = useState(false);
  
  const [updateType, setUpdateType] = useState('percentage');
  const [priceField, setPriceField] = useState('all');
  const [value, setValue] = useState(0);
  const [selectedFamily, setSelectedFamily] = useState('all');
  const [roundTo, setRoundTo] = useState(0);

  useEffect(() => {
    fetchFamilies();
  }, []);

  useEffect(() => {
    if (value !== 0) {
      fetchPreview();
    } else {
      setPreviews([]);
    }
  }, [updateType, priceField, value, selectedFamily, roundTo]);

  const fetchFamilies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/product-families`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFamilies(response.data);
    } catch (error) {
      console.error('Error fetching families:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPreview = async () => {
    if (value === 0) return;
    
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        update_type: updateType,
        price_field: priceField,
        value: value.toString(),
        round_to: roundTo.toString()
      });
      
      if (selectedFamily !== 'all') {
        params.append('family_id', selectedFamily);
      }
      
      const response = await axios.get(`${API}/products/price-preview?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setPreviews(response.data.previews);
      setTotalProducts(response.data.total_products);
    } catch (error) {
      console.error('Error fetching preview:', error);
    }
  };

  const applyChanges = async () => {
    setApplying(true);
    try {
      const token = localStorage.getItem('token');
      const data = {
        update_type: updateType,
        price_field: priceField,
        value: value,
        round_to: roundTo
      };
      
      if (selectedFamily !== 'all') {
        data.family_id = selectedFamily;
      }
      
      const response = await axios.post(`${API}/products/bulk-price-update`, data, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(`${t.priceUpdated}: ${response.data.updated_count} ${language === 'ar' ? 'منتج' : 'products'}`);
      setValue(0);
      setPreviews([]);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.error);
    } finally {
      setApplying(false);
    }
  };

  const formatPrice = (price) => {
    return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const getChangeColor = (diff) => {
    if (diff > 0) return 'text-green-600';
    if (diff < 0) return 'text-red-600';
    return 'text-muted-foreground';
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{t.bulkPriceUpdate}</h1>
          <p className="text-muted-foreground">
            {language === 'ar' ? 'تحديث أسعار المنتجات بشكل جماعي' : 'Update product prices in bulk'}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Update Form */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                {language === 'ar' ? 'إعدادات التحديث' : 'Update Settings'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Update Type */}
              <div>
                <Label>{t.priceUpdateType}</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <Button
                    type="button"
                    variant={updateType === 'percentage' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setUpdateType('percentage')}
                    className="gap-1"
                  >
                    <Percent className="h-4 w-4" />
                    %
                  </Button>
                  <Button
                    type="button"
                    variant={updateType === 'fixed' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setUpdateType('fixed')}
                    className="gap-1"
                  >
                    <DollarSign className="h-4 w-4" />
                    ±
                  </Button>
                  <Button
                    type="button"
                    variant={updateType === 'set' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setUpdateType('set')}
                    className="gap-1"
                  >
                    =
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {updateType === 'percentage' && (language === 'ar' ? 'زيادة/نقصان بنسبة مئوية' : 'Increase/decrease by percentage')}
                  {updateType === 'fixed' && (language === 'ar' ? 'إضافة/طرح مبلغ ثابت' : 'Add/subtract fixed amount')}
                  {updateType === 'set' && (language === 'ar' ? 'تحديد سعر جديد' : 'Set new price')}
                </p>
              </div>

              {/* Price Field */}
              <div>
                <Label>{t.priceField}</Label>
                <Select value={priceField} onValueChange={setPriceField}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t.allPrices}</SelectItem>
                    <SelectItem value="purchase_price">{t.purchasePrice}</SelectItem>
                    <SelectItem value="wholesale_price">{t.wholesalePrice}</SelectItem>
                    <SelectItem value="retail_price">{t.retailPrice}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Value */}
              <div>
                <Label>
                  {updateType === 'percentage' ? (language === 'ar' ? 'النسبة %' : 'Percentage %') :
                   updateType === 'fixed' ? (language === 'ar' ? 'المبلغ' : 'Amount') :
                   (language === 'ar' ? 'السعر الجديد' : 'New Price')}
                </Label>
                <div className="relative">
                  <Input
                    type="number"
                    value={value}
                    onChange={(e) => setValue(parseFloat(e.target.value) || 0)}
                    className={`${updateType === 'percentage' ? 'pe-8' : ''}`}
                  />
                  {updateType === 'percentage' && (
                    <span className="absolute end-3 top-1/2 -translate-y-1/2 text-muted-foreground">%</span>
                  )}
                </div>
                {updateType !== 'set' && (
                  <div className="flex gap-2 mt-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setValue(Math.abs(value))}
                      className="flex-1 gap-1"
                    >
                      <ArrowUp className="h-4 w-4" />
                      {language === 'ar' ? 'زيادة' : 'Increase'}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setValue(-Math.abs(value))}
                      className="flex-1 gap-1"
                    >
                      <ArrowDown className="h-4 w-4" />
                      {language === 'ar' ? 'نقصان' : 'Decrease'}
                    </Button>
                  </div>
                )}
              </div>

              {/* Family Filter */}
              <div>
                <Label>{t.productFamilies}</Label>
                <Select value={selectedFamily} onValueChange={setSelectedFamily}>
                  <SelectTrigger>
                    <SelectValue placeholder={t.allFamilies} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t.allFamilies}</SelectItem>
                    {families.map((f) => (
                      <SelectItem key={f.id} value={f.id}>
                        {language === 'ar' ? f.name_ar : f.name_en}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Round To */}
              <div>
                <Label>{t.roundTo}</Label>
                <Select value={roundTo.toString()} onValueChange={(v) => setRoundTo(parseInt(v))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">{language === 'ar' ? 'بدون تقريب' : 'No rounding'}</SelectItem>
                    <SelectItem value="5">{language === 'ar' ? 'أقرب 5' : 'Nearest 5'}</SelectItem>
                    <SelectItem value="10">{language === 'ar' ? 'أقرب 10' : 'Nearest 10'}</SelectItem>
                    <SelectItem value="50">{language === 'ar' ? 'أقرب 50' : 'Nearest 50'}</SelectItem>
                    <SelectItem value="100">{language === 'ar' ? 'أقرب 100' : 'Nearest 100'}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Apply Button */}
              <Button
                onClick={applyChanges}
                disabled={applying || value === 0 || previews.length === 0}
                className="w-full gap-2"
              >
                {applying ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Check className="h-4 w-4" />
                )}
                {t.applyChanges} ({totalProducts} {language === 'ar' ? 'منتج' : 'products'})
              </Button>
            </CardContent>
          </Card>

          {/* Preview Table */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                {t.previewChanges}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {previews.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Calculator className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>{language === 'ar' ? 'أدخل قيمة لعرض المعاينة' : 'Enter a value to see preview'}</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{language === 'ar' ? 'المنتج' : 'Product'}</TableHead>
                        {(priceField === 'all' || priceField === 'purchase_price') && (
                          <TableHead>{t.purchasePrice}</TableHead>
                        )}
                        {(priceField === 'all' || priceField === 'wholesale_price') && (
                          <TableHead>{t.wholesalePrice}</TableHead>
                        )}
                        {(priceField === 'all' || priceField === 'retail_price') && (
                          <TableHead>{t.retailPrice}</TableHead>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {previews.map((preview) => (
                        <TableRow key={preview.id}>
                          <TableCell className="font-medium">{preview.name}</TableCell>
                          {Object.entries(preview.changes).map(([field, change]) => (
                            <TableCell key={field}>
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className="text-muted-foreground line-through text-sm">
                                    {formatPrice(change.old)}
                                  </span>
                                  <span className="font-bold">
                                    {formatPrice(change.new)}
                                  </span>
                                </div>
                                <Badge variant="outline" className={getChangeColor(change.diff)}>
                                  {change.diff > 0 ? '+' : ''}{formatPrice(change.diff)} {t.currency}
                                </Badge>
                              </div>
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {totalProducts > previews.length && (
                    <p className="text-center text-sm text-muted-foreground mt-4">
                      {language === 'ar' 
                        ? `عرض ${previews.length} من ${totalProducts} منتج`
                        : `Showing ${previews.length} of ${totalProducts} products`}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
