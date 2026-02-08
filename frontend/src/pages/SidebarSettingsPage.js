import { useState, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
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
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../components/ui/collapsible';
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
  EyeOff,
  ChevronDown,
  ChevronRight,
  Receipt,
  FolderTree,
  Warehouse,
  ClipboardList,
  QrCode,
  DollarSign,
  ShoppingBag,
  Clock,
  Smartphone,
  Store,
  Shield,
  Key
} from 'lucide-react';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Icon mapping
const iconMap = {
  LayoutDashboard, Package, ShoppingCart, Truck, Users, CreditCard, Wallet,
  BarChart3, Settings, Bell, Wrench, Receipt, FolderTree, Warehouse,
  ClipboardList, QrCode, DollarSign, ShoppingBag, Clock, Smartphone, Store, Shield, Key
};

// Default menu structure with sections and items
const defaultMenuSections = [
  {
    id: 'main',
    titleAr: 'الرئيسية',
    titleFr: 'Principal',
    icon: 'LayoutDashboard',
    visible: true,
    items: [
      { id: 'dashboard', path: '/', icon: 'LayoutDashboard', labelAr: 'لوحة التحكم', labelFr: 'Tableau de bord', visible: true },
    ]
  },
  {
    id: 'inventory',
    titleAr: 'المخزون',
    titleFr: 'Stock',
    icon: 'Package',
    visible: true,
    items: [
      { id: 'products', path: '/products', icon: 'Package', labelAr: 'المنتجات', labelFr: 'Produits', visible: true },
      { id: 'product-families', path: '/product-families', icon: 'FolderTree', labelAr: 'عائلات المنتجات', labelFr: 'Familles produits', visible: true },
      { id: 'warehouses', path: '/warehouses', icon: 'Warehouse', labelAr: 'المخازن', labelFr: 'Entrepôts', visible: true },
      { id: 'inventory-count', path: '/inventory-count', icon: 'ClipboardList', labelAr: 'جرد المخزون', labelFr: 'Inventaire', visible: true },
      { id: 'barcode-print', path: '/barcode-print', icon: 'QrCode', labelAr: 'طباعة الباركود', labelFr: 'Codes-barres', visible: true },
      { id: 'bulk-price-update', path: '/bulk-price-update', icon: 'DollarSign', labelAr: 'تحديث الأسعار', labelFr: 'Mise à jour prix', visible: true },
    ]
  },
  {
    id: 'finance',
    titleAr: 'المالية',
    titleFr: 'Finances',
    icon: 'Wallet',
    visible: true,
    items: [
      { id: 'pos', path: '/pos', icon: 'ShoppingCart', labelAr: 'نقطة البيع', labelFr: 'Point de vente', visible: true },
      { id: 'daily-sessions', path: '/daily-sessions', icon: 'Clock', labelAr: 'حصص البيع اليومية', labelFr: 'Sessions', visible: true },
      { id: 'sales', path: '/sales', icon: 'Receipt', labelAr: 'المبيعات', labelFr: 'Ventes', visible: true },
      { id: 'purchases', path: '/purchases', icon: 'ShoppingBag', labelAr: 'المشتريات', labelFr: 'Achats', visible: true },
      { id: 'expenses', path: '/expenses', icon: 'Receipt', labelAr: 'التكاليف', labelFr: 'Dépenses', visible: true },
      { id: 'cash', path: '/cash', icon: 'Wallet', labelAr: 'إدارة المال', labelFr: 'Gestion caisse', visible: true },
      { id: 'customer-debts', path: '/customer-debts', icon: 'CreditCard', labelAr: 'ديون الزبائن', labelFr: 'Dettes clients', visible: true },
      { id: 'debts', path: '/debts', icon: 'Receipt', labelAr: 'الديون', labelFr: 'Dettes', visible: true },
    ]
  },
  {
    id: 'relations',
    titleAr: 'العلاقات',
    titleFr: 'Relations',
    icon: 'Users',
    visible: true,
    items: [
      { id: 'customers', path: '/customers', icon: 'Users', labelAr: 'الزبائن', labelFr: 'Clients', visible: true },
      { id: 'customer-families', path: '/customer-families', icon: 'FolderTree', labelAr: 'عائلات الزبائن', labelFr: 'Familles clients', visible: true },
      { id: 'suppliers', path: '/suppliers', icon: 'Truck', labelAr: 'الموردين', labelFr: 'Fournisseurs', visible: true },
      { id: 'supplier-families', path: '/supplier-families', icon: 'FolderTree', labelAr: 'عائلات الموردين', labelFr: 'Familles fournisseurs', visible: true },
      { id: 'employees', path: '/employees', icon: 'Users', labelAr: 'الموظفين', labelFr: 'Employés', visible: true },
    ]
  },
  {
    id: 'repairs',
    titleAr: 'الصيانة',
    titleFr: 'Réparations',
    icon: 'Wrench',
    visible: true,
    items: [
      { id: 'repairs-list', path: '/repairs', icon: 'ClipboardList', labelAr: 'تتبع الصيانة', labelFr: 'Suivi réparations', visible: true },
      { id: 'repairs-new', path: '/repairs/new', icon: 'Smartphone', labelAr: 'استقبال جهاز', labelFr: 'Réception', visible: true },
      { id: 'repairs-parts', path: '/repairs/parts', icon: 'Package', labelAr: 'قطع الغيار', labelFr: 'Pièces', visible: true },
    ]
  },
  {
    id: 'admin',
    titleAr: 'الإدارة',
    titleFr: 'Administration',
    icon: 'Settings',
    visible: true,
    items: [
      { id: 'reports', path: '/reports', icon: 'BarChart3', labelAr: 'التقارير', labelFr: 'Rapports', visible: true },
      { id: 'analytics', path: '/analytics', icon: 'BarChart3', labelAr: 'إحصائيات متقدمة', labelFr: 'Analyses', visible: true },
      { id: 'notifications', path: '/notifications', icon: 'Bell', labelAr: 'الإشعارات', labelFr: 'Notifications', visible: true },
      { id: 'users', path: '/users', icon: 'Shield', labelAr: 'المستخدمين', labelFr: 'Utilisateurs', visible: true },
      { id: 'api-keys', path: '/api-keys', icon: 'Key', labelAr: 'مفاتيح API', labelFr: 'Clés API', visible: true },
      { id: 'settings', path: '/settings', icon: 'Settings', labelAr: 'الإعدادات', labelFr: 'Paramètres', visible: true },
    ]
  },
];

// Sortable Item Component (for menu items)
function SortableItem({ item, language, onToggleVisibility, sectionId }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: `${sectionId}-${item.id}` });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const IconComponent = iconMap[item.icon] || Package;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-2 p-3 bg-muted/50 rounded-lg ms-6 ${
        isDragging ? 'shadow-md ring-2 ring-primary/50' : ''
      } ${!item.visible ? 'opacity-50' : ''}`}
    >
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing p-1 hover:bg-muted rounded"
      >
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </button>
      
      <IconComponent className={`h-4 w-4 ${item.visible ? 'text-primary' : 'text-muted-foreground'}`} />
      
      <span className={`flex-1 text-sm ${!item.visible ? 'text-muted-foreground line-through' : ''}`}>
        {language === 'ar' ? item.labelAr : item.labelFr}
      </span>
      
      <Switch
        checked={item.visible}
        onCheckedChange={() => onToggleVisibility(sectionId, item.id)}
        className="scale-75"
      />
    </div>
  );
}

// Sortable Section Component
function SortableSection({ section, language, onToggleVisibility, onToggleSectionVisibility, onItemDragEnd, expandedSections, toggleExpanded }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: section.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const IconComponent = iconMap[section.icon] || Package;
  const isExpanded = expandedSections.includes(section.id);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleItemDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      onItemDragEnd(section.id, active.id, over.id);
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`border rounded-xl overflow-hidden bg-card ${
        isDragging ? 'shadow-lg ring-2 ring-primary' : ''
      } ${!section.visible ? 'opacity-60' : ''}`}
    >
      {/* Section Header */}
      <div className="flex items-center gap-3 p-4 bg-muted/30">
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing p-1 hover:bg-muted rounded"
        >
          <GripVertical className="h-5 w-5 text-muted-foreground" />
        </button>
        
        <div className={`p-2 rounded-lg ${section.visible ? 'bg-primary/10' : 'bg-muted'}`}>
          <IconComponent className={`h-5 w-5 ${section.visible ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>
        
        <div className="flex-1">
          <p className={`font-medium ${!section.visible ? 'text-muted-foreground' : ''}`}>
            {language === 'ar' ? section.titleAr : section.titleFr}
          </p>
          <p className="text-xs text-muted-foreground">
            {section.items.filter(i => i.visible).length} / {section.items.length} {language === 'ar' ? 'عنصر' : 'éléments'}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Switch
            checked={section.visible}
            onCheckedChange={() => onToggleSectionVisibility(section.id)}
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleExpanded(section.id)}
            className="h-8 w-8 p-0"
          >
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </div>
      </div>
      
      {/* Section Items */}
      {isExpanded && section.visible && (
        <div className="p-3 space-y-2 border-t bg-background/50">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleItemDragEnd}
          >
            <SortableContext
              items={section.items.map(item => `${section.id}-${item.id}`)}
              strategy={verticalListSortingStrategy}
            >
              {section.items.map((item) => (
                <SortableItem
                  key={item.id}
                  item={item}
                  language={language}
                  onToggleVisibility={onToggleVisibility}
                  sectionId={section.id}
                />
              ))}
            </SortableContext>
          </DndContext>
        </div>
      )}
    </div>
  );
}

export default function SidebarSettingsPage() {
  const { language, isRTL } = useLanguage();
  const [menuSections, setMenuSections] = useState(defaultMenuSections);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [expandedSections, setExpandedSections] = useState(['main', 'inventory', 'finance']);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const t = {
    ar: {
      title: 'ترتيب القائمة الجانبية',
      description: 'اسحب الأقسام والعناصر لتغيير ترتيبها',
      save: 'حفظ الترتيب',
      reset: 'إعادة الترتيب الافتراضي',
      saved: 'تم حفظ الترتيب بنجاح',
      resetSuccess: 'تم إعادة الترتيب الافتراضي',
      sectionsHint: 'اسحب الأقسام الرئيسية لتغيير ترتيبها',
      itemsHint: 'افتح القسم واسحب العناصر الفرعية لترتيبها',
      visibilityHint: 'يمكنك إخفاء الأقسام والعناصر',
      expandAll: 'فتح الكل',
      collapseAll: 'إغلاق الكل'
    },
    fr: {
      title: 'Organiser le menu latéral',
      description: 'Glissez les sections et éléments pour les réorganiser',
      save: 'Enregistrer',
      reset: 'Réinitialiser',
      saved: 'Ordre enregistré avec succès',
      resetSuccess: 'Ordre par défaut restauré',
      sectionsHint: 'Glissez les sections pour les réorganiser',
      itemsHint: 'Ouvrez une section pour réorganiser ses éléments',
      visibilityHint: 'Vous pouvez masquer des sections et éléments',
      expandAll: 'Tout ouvrir',
      collapseAll: 'Tout fermer'
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
      
      if (response.data.sidebar_order && Array.isArray(response.data.sidebar_order) && response.data.sidebar_order.length > 0) {
        // Check if it's the new format (sections with items)
        if (response.data.sidebar_order[0].items) {
          setMenuSections(response.data.sidebar_order);
        }
      }
    } catch (error) {
      console.error('Error fetching sidebar order:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSectionDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      setMenuSections((sections) => {
        const oldIndex = sections.findIndex(s => s.id === active.id);
        const newIndex = sections.findIndex(s => s.id === over.id);
        setHasChanges(true);
        return arrayMove(sections, oldIndex, newIndex);
      });
    }
  };

  const handleItemDragEnd = (sectionId, activeId, overId) => {
    setMenuSections(sections => 
      sections.map(section => {
        if (section.id === sectionId) {
          const activeItemId = activeId.replace(`${sectionId}-`, '');
          const overItemId = overId.replace(`${sectionId}-`, '');
          const oldIndex = section.items.findIndex(i => i.id === activeItemId);
          const newIndex = section.items.findIndex(i => i.id === overItemId);
          return {
            ...section,
            items: arrayMove(section.items, oldIndex, newIndex)
          };
        }
        return section;
      })
    );
    setHasChanges(true);
  };

  const handleToggleItemVisibility = (sectionId, itemId) => {
    setMenuSections(sections =>
      sections.map(section => {
        if (section.id === sectionId) {
          return {
            ...section,
            items: section.items.map(item =>
              item.id === itemId ? { ...item, visible: !item.visible } : item
            )
          };
        }
        return section;
      })
    );
    setHasChanges(true);
  };

  const handleToggleSectionVisibility = (sectionId) => {
    setMenuSections(sections =>
      sections.map(section =>
        section.id === sectionId ? { ...section, visible: !section.visible } : section
      )
    );
    setHasChanges(true);
  };

  const toggleExpanded = (sectionId) => {
    setExpandedSections(prev =>
      prev.includes(sectionId)
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const expandAll = () => {
    setExpandedSections(menuSections.map(s => s.id));
  };

  const collapseAll = () => {
    setExpandedSections([]);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/settings/sidebar-order`, menuSections, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      localStorage.setItem('sidebarOrder', JSON.stringify(menuSections));
      toast.success(texts.saved);
      setHasChanges(false);
      window.dispatchEvent(new CustomEvent('sidebarOrderChanged'));
    } catch (error) {
      toast.error(language === 'ar' ? 'حدث خطأ' : 'Une erreur est survenue');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setMenuSections(defaultMenuSections);
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
      <div className="space-y-6 max-w-3xl mx-auto" data-testid="sidebar-settings-page">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <GripVertical className="h-5 w-5" />
                  {texts.title}
                </CardTitle>
                <CardDescription className="mt-1">{texts.description}</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={expandAll}>
                  {texts.expandAll}
                </Button>
                <Button variant="outline" size="sm" onClick={collapseAll}>
                  {texts.collapseAll}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Hints */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 p-3 bg-muted/50 rounded-lg text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <GripVertical className="h-4 w-4 shrink-0" />
                <span>{texts.sectionsHint}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <ChevronDown className="h-4 w-4 shrink-0" />
                <span>{texts.itemsHint}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Eye className="h-4 w-4 shrink-0" />
                <span>{texts.visibilityHint}</span>
              </div>
            </div>

            {/* Sortable Sections */}
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleSectionDragEnd}
            >
              <SortableContext
                items={menuSections.map(s => s.id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-3">
                  {menuSections.map((section) => (
                    <SortableSection
                      key={section.id}
                      section={section}
                      language={language}
                      onToggleVisibility={handleToggleItemVisibility}
                      onToggleSectionVisibility={handleToggleSectionVisibility}
                      onItemDragEnd={handleItemDragEnd}
                      expandedSections={expandedSections}
                      toggleExpanded={toggleExpanded}
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
                {hasChanges && <Badge variant="secondary" className="ms-2">*</Badge>}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
