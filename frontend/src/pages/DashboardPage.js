import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Package, Users, AlertTriangle, ArrowRight, ArrowLeft, Plus } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DashboardPage() {
  const { t, isRTL, language } = useLanguage();
  const { isAdmin } = useAuth();
  const [stats, setStats] = useState({ total_products: 0, total_users: 0, low_stock_count: 0 });
  const [recentProducts, setRecentProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [productsRes] = await Promise.all([
          axios.get(`${API}/products`)
        ]);
        
        setRecentProducts(productsRes.data.slice(0, 6));
        
        // Only fetch stats if admin
        if (isAdmin) {
          try {
            const statsRes = await axios.get(`${API}/stats`);
            setStats(statsRes.data);
          } catch (e) {
            // Fallback stats from products
            setStats({
              total_products: productsRes.data.length,
              total_users: 1,
              low_stock_count: productsRes.data.filter(p => p.quantity < 10).length
            });
          }
        } else {
          setStats({
            total_products: productsRes.data.length,
            total_users: 0,
            low_stock_count: productsRes.data.filter(p => p.quantity < 10).length
          });
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [isAdmin]);

  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  const statsCards = [
    {
      title: t.totalProducts,
      value: stats.total_products,
      icon: Package,
      color: 'text-primary',
      bgColor: 'bg-primary/10'
    },
    ...(isAdmin ? [{
      title: t.totalUsers,
      value: stats.total_users,
      icon: Users,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100'
    }] : []),
    {
      title: t.lowStock,
      value: stats.low_stock_count,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bgColor: 'bg-amber-100'
    }
  ];

  if (loading) {
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
      <div className="space-y-8 animate-fade-in" data-testid="dashboard-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t.dashboard}</h1>
            <p className="text-muted-foreground mt-1">{t.quickStats}</p>
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

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {statsCards.map((stat, index) => (
            <Card key={index} className="stats-card" data-testid={`stat-card-${index}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                    <p className="text-3xl font-bold mt-2">{stat.value}</p>
                  </div>
                  <div className={`p-4 rounded-xl ${stat.bgColor}`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent Products */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <CardTitle className="text-xl">{t.recentProducts}</CardTitle>
            <Link to="/products">
              <Button variant="ghost" className="gap-2" data-testid="view-all-products-btn">
                {t.products}
                <Arrow className="h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentProducts.length === 0 ? (
              <div className="empty-state py-12">
                <Package className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">{t.noProducts}</h3>
                <p className="text-muted-foreground mt-1">{t.noProductsSubtitle}</p>
                {isAdmin && (
                  <Link to="/products/add" className="mt-4">
                    <Button className="gap-2">
                      <Plus className="h-5 w-5" />
                      {t.addProduct}
                    </Button>
                  </Link>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {recentProducts.map((product) => (
                  <Link
                    key={product.id}
                    to={`/products/${product.id}`}
                    className="block"
                    data-testid={`product-card-${product.id}`}
                  >
                    <div className="product-card border rounded-xl overflow-hidden bg-card">
                      <div className="product-image-container h-40">
                        <img
                          src={product.image_url || 'https://images.unsplash.com/photo-1634403665443-81dc4d75843a?crop=entropy&cs=srgb&fm=jpg&q=85'}
                          alt={language === 'ar' ? product.name_ar : product.name_en}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-4">
                        <h3 className="font-semibold truncate">
                          {language === 'ar' ? product.name_ar : product.name_en}
                        </h3>
                        <p className="text-primary font-bold mt-1">
                          ${product.price.toFixed(2)}
                        </p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {product.compatible_models.slice(0, 2).map((model, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {model}
                            </Badge>
                          ))}
                          {product.compatible_models.length > 2 && (
                            <Badge variant="outline" className="text-xs">
                              +{product.compatible_models.length - 2}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
