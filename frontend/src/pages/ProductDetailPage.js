import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Layout } from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { 
  ArrowRight, 
  ArrowLeft, 
  Edit, 
  Trash2, 
  Package,
  DollarSign,
  Boxes
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t, isRTL, language } = useLanguage();
  const { isAdmin } = useAuth();
  
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const BackArrow = isRTL ? ArrowRight : ArrowLeft;

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`${API}/products/${id}`);
        setProduct(response.data);
      } catch (error) {
        console.error('Error fetching product:', error);
        toast.error(t.notFound);
        navigate('/products');
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [id, navigate, t.notFound]);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await axios.delete(`${API}/products/${id}`);
      toast.success(t.productDeleted);
      navigate('/products');
    } catch (error) {
      console.error('Error deleting product:', error);
      toast.error(t.somethingWentWrong);
    } finally {
      setDeleting(false);
      setDeleteDialogOpen(false);
    }
  };

  const getStockStatus = (quantity) => {
    if (quantity === 0) {
      return { label: t.outOfStock, variant: 'destructive' };
    } else if (quantity < 10) {
      return { label: t.lowStockWarning, className: 'bg-amber-100 text-amber-800 border-amber-200' };
    }
    return { label: t.inStock, className: 'bg-emerald-100 text-emerald-800 border-emerald-200' };
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="spinner" />
        </div>
      </Layout>
    );
  }

  if (!product) {
    return (
      <Layout>
        <div className="empty-state py-16">
          <Package className="h-20 w-20 text-muted-foreground mb-4" />
          <h3 className="text-xl font-medium">{t.notFound}</h3>
        </div>
      </Layout>
    );
  }

  const stockStatus = getStockStatus(product.quantity);

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="product-detail-page">
        {/* Back Button */}
        <Link to="/products">
          <Button variant="ghost" className="gap-2" data-testid="back-to-products-btn">
            <BackArrow className="h-4 w-4" />
            {t.products}
          </Button>
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Product Image */}
          <div className="lg:col-span-1">
            <Card className="overflow-hidden">
              <div className="aspect-square bg-muted">
                <img
                  src={product.image_url || 'https://images.unsplash.com/photo-1634403665443-81dc4d75843a?crop=entropy&cs=srgb&fm=jpg&q=85'}
                  alt={language === 'ar' ? product.name_ar : product.name_en}
                  className="w-full h-full object-cover"
                />
              </div>
            </Card>
          </div>

          {/* Product Info */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                  <div>
                    <Badge 
                      variant={stockStatus.variant} 
                      className={stockStatus.className}
                    >
                      {stockStatus.label}
                    </Badge>
                    <h1 className="text-3xl font-bold mt-3">
                      {language === 'ar' ? product.name_ar : product.name_en}
                    </h1>
                    {language === 'ar' && product.name_en && (
                      <p className="text-muted-foreground mt-1">{product.name_en}</p>
                    )}
                    {language === 'en' && product.name_ar && (
                      <p className="text-muted-foreground mt-1">{product.name_ar}</p>
                    )}
                  </div>
                  
                  {isAdmin && (
                    <div className="flex gap-2">
                      <Link to={`/products/${id}/edit`}>
                        <Button variant="outline" className="gap-2" data-testid="edit-product-btn">
                          <Edit className="h-4 w-4" />
                          {t.edit}
                        </Button>
                      </Link>
                      <Button 
                        variant="destructive" 
                        className="gap-2"
                        onClick={() => setDeleteDialogOpen(true)}
                        data-testid="delete-product-btn"
                      >
                        <Trash2 className="h-4 w-4" />
                        {t.delete}
                      </Button>
                    </div>
                  )}
                </div>

                {/* Description */}
                <div className="mt-6">
                  <h3 className="font-semibold text-lg mb-2">{t.description}</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {language === 'ar' ? product.description_ar : product.description_en}
                  </p>
                </div>

                {/* Price & Quantity */}
                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="p-4 rounded-xl bg-primary/5 border border-primary/10">
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                      <DollarSign className="h-4 w-4" />
                      <span className="text-sm font-medium">{t.price}</span>
                    </div>
                    <p className="text-2xl font-bold text-primary">
                      ${product.price.toFixed(2)}
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-muted/50 border">
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                      <Boxes className="h-4 w-4" />
                      <span className="text-sm font-medium">{t.quantity}</span>
                    </div>
                    <p className="text-2xl font-bold">
                      {product.quantity}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Compatible Models */}
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-lg mb-4">{t.compatibleModels}</h3>
                <div className="flex flex-wrap gap-2">
                  {product.compatible_models.map((model, idx) => (
                    <span 
                      key={idx} 
                      className="model-badge text-sm px-3 py-1.5"
                      data-testid={`compatible-model-${idx}`}
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{t.deleteProduct}</AlertDialogTitle>
              <AlertDialogDescription>
                {t.deleteConfirm}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={deleting}>
                {t.cancel}
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                disabled={deleting}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                data-testid="confirm-delete-btn"
              >
                {deleting ? t.loading : t.delete}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
}
