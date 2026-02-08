import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Layout } from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { 
  Package, 
  Plus, 
  Search,
  X,
  Filter,
  Grid3X3,
  List,
  LayoutGrid,
  ArrowUpDown,
  SortAsc,
  SortDesc
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ProductsPage() {
  const { t, isRTL, language } = useLanguage();
  const { isAdmin } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [modelFilter, setModelFilter] = useState(searchParams.get('model') || '');
  const [viewMode, setViewMode] = useState(localStorage.getItem('productsViewMode') || 'grid'); // grid, list, compact
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  const changeViewMode = (mode) => {
    setViewMode(mode);
    localStorage.setItem('productsViewMode', mode);
  };

  // Sort products
  const sortedProducts = [...products].sort((a, b) => {
    let comparison = 0;
    switch (sortBy) {
      case 'name':
        const nameA = language === 'ar' ? (a.name_ar || a.name_en) : (a.name_en || a.name_ar);
        const nameB = language === 'ar' ? (b.name_ar || b.name_en) : (b.name_en || b.name_ar);
        comparison = nameA.localeCompare(nameB);
        break;
      case 'price':
        comparison = (a.retail_price || 0) - (b.retail_price || 0);
        break;
      case 'stock':
        comparison = (a.quantity || 0) - (b.quantity || 0);
        break;
      case 'purchase_price':
        comparison = (a.purchase_price || 0) - (b.purchase_price || 0);
        break;
      default:
        comparison = 0;
    }
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.set('search', searchQuery);
      if (modelFilter) params.set('model', modelFilter);
      
      const response = await axios.get(`${API}/products?${params.toString()}`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [searchQuery, modelFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (searchQuery) params.set('search', searchQuery);
    if (modelFilter) params.set('model', modelFilter);
    setSearchParams(params);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setModelFilter('');
    setSearchParams({});
  };

  const getStockBadge = (quantity) => {
    if (quantity === 0) {
      return <Badge variant="destructive">{t.outOfStock}</Badge>;
    } else if (quantity < 10) {
      return <Badge className="bg-amber-100 text-amber-800 border-amber-200">{t.lowStockWarning}</Badge>;
    }
    return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">{t.inStock}</Badge>;
  };

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="products-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.products}</h1>
            <p className="text-muted-foreground mt-1">
              {products.length} {t.products.toLowerCase()}
            </p>
          </div>
          {isAdmin && (
            <Link to="/products/add">
              <Button className="gap-2" data-testid="add-product-btn">
                <Plus className="h-5 w-5" />
                {t.addProduct}
              </Button>
            </Link>
          )}
        </div>

        {/* Search & Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {language === 'ar' ? 'طريقة العرض:' : 'Affichage:'}
                </span>
                <div className="flex border rounded-lg">
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => changeViewMode('grid')}
                    className="rounded-r-none"
                    data-testid="view-grid-btn"
                  >
                    <Grid3X3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => changeViewMode('list')}
                    className="rounded-none border-x"
                    data-testid="view-list-btn"
                  >
                    <List className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'compact' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => changeViewMode('compact')}
                    className="rounded-l-none"
                    data-testid="view-compact-btn"
                  >
                    <LayoutGrid className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              {/* Sort Controls */}
              <div className="flex items-center gap-2">
                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="w-[150px]">
                    <ArrowUpDown className="h-4 w-4 me-2" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="name">{language === 'ar' ? 'الاسم' : 'Nom'}</SelectItem>
                    <SelectItem value="price">{language === 'ar' ? 'السعر' : 'Prix'}</SelectItem>
                    <SelectItem value="stock">{language === 'ar' ? 'المخزون' : 'Stock'}</SelectItem>
                    <SelectItem value="purchase_price">{language === 'ar' ? 'سعر الشراء' : 'Prix achat'}</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  title={sortOrder === 'asc' ? 'تصاعدي' : 'تنازلي'}
                >
                  {sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
                <Input
                  type="text"
                  placeholder={t.searchPlaceholder}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`h-11 ${isRTL ? 'pr-10' : 'pl-10'}`}
                  data-testid="product-search-input"
                />
              </div>
              <div className="relative flex-1 sm:max-w-xs">
                <Filter className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? 'right-3' : 'left-3'}`} />
                <Input
                  type="text"
                  placeholder={t.filterByModel}
                  value={modelFilter}
                  onChange={(e) => setModelFilter(e.target.value)}
                  className={`h-11 ${isRTL ? 'pr-10' : 'pl-10'}`}
                  data-testid="model-filter-input"
                />
              </div>
              {(searchQuery || modelFilter) && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={clearFilters}
                  className="gap-2"
                  data-testid="clear-filters-btn"
                >
                  <X className="h-4 w-4" />
                  {t.clearFilters}
                </Button>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Products Grid */}
        {loading ? (
          <div className="flex items-center justify-center min-h-[40vh]">
            <div className="spinner" />
          </div>
        ) : sortedProducts.length === 0 ? (
          <div className="empty-state py-16">
            <Package className="h-20 w-20 text-muted-foreground mb-4" />
            <h3 className="text-xl font-medium">{t.noProducts}</h3>
            <p className="text-muted-foreground mt-2">{t.noProductsSubtitle}</p>
            {isAdmin && (
              <Link to="/products/add" className="mt-6">
                <Button className="gap-2">
                  <Plus className="h-5 w-5" />
                  {t.addProduct}
                </Button>
              </Link>
            )}
          </div>
        ) : viewMode === 'list' ? (
          /* List View */
          <div className="space-y-2">
            {sortedProducts.map((product) => (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="block"
                data-testid={`product-item-${product.id}`}
              >
                <div className="flex items-center gap-4 p-4 border rounded-lg bg-card hover:bg-muted/50 transition-colors">
                  <img
                    src={product.image_url || 'https://images.unsplash.com/photo-1634403665443-81dc4d75843a?crop=entropy&cs=srgb&fm=jpg&q=85'}
                    alt={language === 'ar' ? product.name_ar : product.name_en}
                    className="w-16 h-16 object-cover rounded-lg"
                  />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">{language === 'ar' ? product.name_ar : product.name_en}</h3>
                    <p className="text-sm text-muted-foreground">{product.barcode}</p>
                  </div>
                  <div className="text-end">
                    <p className="font-bold">{product.retail_price?.toFixed(2)} {t.currency}</p>
                    <p className="text-sm text-muted-foreground">{t.stock}: {product.quantity}</p>
                  </div>
                  {getStockBadge(product.quantity)}
                </div>
              </Link>
            ))}
          </div>
        ) : viewMode === 'compact' ? (
          /* Compact View */
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
            {sortedProducts.map((product) => (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="block"
                data-testid={`product-item-${product.id}`}
              >
                <div className="border rounded-lg p-2 bg-card hover:bg-muted/50 transition-colors text-center">
                  <img
                    src={product.image_url || 'https://images.unsplash.com/photo-1634403665443-81dc4d75843a?crop=entropy&cs=srgb&fm=jpg&q=85'}
                    alt={language === 'ar' ? product.name_ar : product.name_en}
                    className="w-full aspect-square object-cover rounded-md mb-2"
                  />
                  <p className="text-xs font-medium truncate">{language === 'ar' ? product.name_ar : product.name_en}</p>
                  <p className="text-xs font-bold text-primary">{product.retail_price?.toFixed(0)} {t.currency}</p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          /* Grid View (default) */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {sortedProducts.map((product) => (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="block"
                data-testid={`product-item-${product.id}`}
              >
                <div className="product-card border rounded-xl overflow-hidden bg-card h-full flex flex-col">
                  <div className="product-image-container aspect-square relative">
                    <img
                      src={product.image_url || 'https://images.unsplash.com/photo-1634403665443-81dc4d75843a?crop=entropy&cs=srgb&fm=jpg&q=85'}
                      alt={language === 'ar' ? product.name_ar : product.name_en}
                      className="w-full h-full object-cover"
                    />
                    <div className={`absolute top-3 ${isRTL ? 'left-3' : 'right-3'}`}>
                      {getStockBadge(product.quantity)}
                    </div>
                  </div>
                  <div className="p-5 flex-1 flex flex-col">
                    <h3 className="font-semibold text-lg line-clamp-1">
                      {language === 'ar' ? product.name_ar : product.name_en}
                    </h3>
                    <p className="text-muted-foreground text-sm mt-1 line-clamp-2 flex-1">
                      {language === 'ar' ? product.description_ar : product.description_en}
                    </p>
                    <div className="mt-4">
                      <p className="text-primary font-bold text-xl">
                        {(product.retail_price ?? product.price ?? 0).toFixed(2)} {t.currency}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {t.quantity}: {product.quantity ?? 0}
                      </p>
                    </div>
                    {product.compatible_models && product.compatible_models.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-muted-foreground uppercase mb-2">
                          {t.compatibleModels}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {product.compatible_models.slice(0, 3).map((model, idx) => (
                            <span key={idx} className="model-badge">
                              {model}
                            </span>
                          ))}
                          {product.compatible_models.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{product.compatible_models.length - 3}
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
