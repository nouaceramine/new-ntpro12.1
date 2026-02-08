import { useState, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import {
  GripVertical,
  LayoutDashboard,
  Package,
  ShoppingCart,
  Truck,
  Users,
  CreditCard,
  Wallet,
  BarChart3,
  Settings,
  Bell,
  Wrench,
  Save,
  RotateCcw,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react';
import { Switch } from '../components/ui/switch';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Default menu items with their icons
const defaultMenuItems = [
  { id: 'dashboard', path: '/dashboard', icon: 'LayoutDashboard', labelAr: 'لوحة التحكم', labelFr: 'Tableau de bord', visible: true },
  { id: 'pos', path: '/pos', icon: 'ShoppingCart', labelAr: 'نقطة البيع', labelFr: 'Point de vente', visible: true },
  { id: 'products', path: '/products', icon: 'Package', labelAr: 'المنتجات', labelFr: 'Produits', visible: true },
  { id: 'customers', path: '/customers', icon: 'Users', labelAr: 'الزبائن', labelFr: 'Clients', visible: true },
  { id: 'suppliers', path: '/suppliers', icon: 'Truck', labelAr: 'الموردين', labelFr: 'Fournisseurs', visible: true },
  { id: 'sales', path: '/sales', icon: 'CreditCard', labelAr: 'المبيعات', labelFr: 'Ventes', visible: true },
  { id: 'purchases', path: '/purchases', icon: 'ShoppingCart', labelAr: 'المشتريات', labelFr: 'Achats', visible: true },
  { id: 'debts', path: '/debts', icon: 'Wallet', labelAr: 'الديون', labelFr: 'Dettes', visible: true },
  { id: 'repairs', path: '/repairs', icon: 'Wrench', labelAr: 'الصيانة', labelFr: 'Réparations', visible: true },
  { id: 'reports', path: '/reports', icon: 'BarChart3', labelAr: 'التقارير', labelFr: 'Rapports', visible: true },
  { id: 'notifications', path: '/notifications', icon: 'Bell', labelAr: 'الإشعارات', labelFr: 'Notifications', visible: true },
  { id: 'settings', path: '/settings', icon: 'Settings', labelAr: 'الإعدادات', labelFr: 'Paramètres', visible: true },
];

const iconMap = {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Truck,
  Users,
  CreditCard,
  Wallet,
  BarChart3,
  Settings,
  Bell,
  Wrench
};

// Sortable Item Component
function SortableItem({ item, language, onToggleVisibility }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1000 : 1,
  };

  const IconComponent = iconMap[item.icon] || Package;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-3 p-4 bg-card border rounded-lg ${
        isDragging ? 'shadow-lg ring-2 ring-primary' : ''
      } ${!item.visible ? 'opacity-50' : ''}`}
    >
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing p-1 hover:bg-muted rounded"
        data-testid={`drag-handle-${item.id}`}
      >
        <GripVertical className="h-5 w-5 text-muted-foreground" />
      </button>
      
      <div className="flex items-center gap-3 flex-1">
        <div className={`p-2 rounded-lg ${item.visible ? 'bg-primary/10' : 'bg-muted'}`}>
          <IconComponent className={`h-5 w-5 ${item.visible ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>
        <div className="flex-1">
          <p className={`font-medium ${!item.visible ? 'text-muted-foreground' : ''}`}>
            {language === 'ar' ? item.labelAr : item.labelFr}
          </p>
          <p className="text-xs text-muted-foreground">{item.path}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">
          {item.visible 
            ? (language === 'ar' ? 'ظاهر' : 'Visible') 
            : (language === 'ar' ? 'مخفي' : 'Masqué')}
        </span>
        <Switch
          checked={item.visible}
          onCheckedChange={() => onToggleVisibility(item.id)}
          data-testid={`visibility-${item.id}`}
        />
      </div>
    </div>
  );
}

export default function SidebarSettingsPage() {
  const { language, isRTL } = useLanguage();
  const [menuItems, setMenuItems] = useState(defaultMenuItems);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const t = {
    ar: {
      title: 'ترتيب القائمة الجانبية',
      description: 'اسحب العناصر لتغيير ترتيبها في القائمة الجانبية',
      save: 'حفظ الترتيب',
      reset: 'إعادة الترتيب الافتراضي',
      saved: 'تم حفظ الترتيب بنجاح',
      resetSuccess: 'تم إعادة الترتيب الافتراضي',
      dragHint: 'اسحب من الأيقونة للترتيب',
      visibilityHint: 'يمكنك إخفاء العناصر التي لا تحتاجها'
    },
    fr: {
      title: 'Organiser le menu latéral',
      description: 'Faites glisser les éléments pour modifier leur ordre dans le menu',
      save: 'Enregistrer',
      reset: 'Réinitialiser',
      saved: 'Ordre enregistré avec succès',
      resetSuccess: 'Ordre par défaut restauré',
      dragHint: 'Glissez depuis l\'icône pour réorganiser',
      visibilityHint: 'Vous pouvez masquer les éléments inutiles'
    }
  };

  const texts = t[language] || t.ar;

  useEffect(() => {
    fetchSidebarOrder();
  }, []);

  const fetchSidebarOrder = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/settings/sidebar-order`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.sidebar_order) {
        // Merge saved order with default items
        const savedOrder = response.data.sidebar_order;
        const mergedItems = savedOrder.map(saved => {
          const defaultItem = defaultMenuItems.find(d => d.id === saved.id);
          return { ...defaultItem, ...saved };
        }).filter(Boolean);
        
        // Add any new items that weren't in saved order
        defaultMenuItems.forEach(item => {
          if (!mergedItems.find(m => m.id === item.id)) {
            mergedItems.push(item);
          }
        });
        
        setMenuItems(mergedItems);
      }
    } catch (error) {
      console.error('Error fetching sidebar order:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      setMenuItems((items) => {
        const oldIndex = items.findIndex(item => item.id === active.id);
        const newIndex = items.findIndex(item => item.id === over.id);
        const newItems = arrayMove(items, oldIndex, newIndex);
        setHasChanges(true);
        return newItems;
      });
    }
  };

  const handleToggleVisibility = (itemId) => {
    setMenuItems(items => 
      items.map(item => 
        item.id === itemId ? { ...item, visible: !item.visible } : item
      )
    );
    setHasChanges(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/settings/sidebar-order`, menuItems, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Save to localStorage for immediate effect
      localStorage.setItem('sidebarOrder', JSON.stringify(menuItems));
      
      toast.success(texts.saved);
      setHasChanges(false);
      
      // Trigger a refresh of the layout
      window.dispatchEvent(new CustomEvent('sidebarOrderChanged'));
    } catch (error) {
      toast.error(language === 'ar' ? 'حدث خطأ' : 'Une erreur est survenue');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setMenuItems(defaultMenuItems);
    localStorage.removeItem('sidebarOrder');
    setHasChanges(true);
    toast.success(texts.resetSuccess);
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 max-w-2xl mx-auto" data-testid="sidebar-settings-page">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GripVertical className="h-5 w-5" />
              {texts.title}
            </CardTitle>
            <CardDescription>{texts.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Hints */}
            <div className="flex flex-col gap-2 p-3 bg-muted/50 rounded-lg text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <GripVertical className="h-4 w-4" />
                <span>{texts.dragHint}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Eye className="h-4 w-4" />
                <span>{texts.visibilityHint}</span>
              </div>
            </div>

            {/* Sortable List */}
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={menuItems.map(item => item.id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-2">
                  {menuItems.map((item) => (
                    <SortableItem
                      key={item.id}
                      item={item}
                      language={language}
                      onToggleVisibility={handleToggleVisibility}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              <Button
                variant="outline"
                onClick={handleReset}
                className="gap-2"
                data-testid="reset-order-btn"
              >
                <RotateCcw className="h-4 w-4" />
                {texts.reset}
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving || !hasChanges}
                className="gap-2 flex-1"
                data-testid="save-order-btn"
              >
                {saving ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {texts.save}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
