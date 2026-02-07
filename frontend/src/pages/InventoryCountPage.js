import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import * as XLSX from 'xlsx';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Checkbox } from '../components/ui/checkbox';
import { Switch } from '../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  ClipboardList, 
  Search,
  Package,
  Check,
  X,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  Pause,
  Save,
  RotateCcw,
  Barcode,
  Camera,
  Plus,
  Minus,
  FileText,
  Download,
  Upload,
  FileUp,
  Table as TableIcon,
  Calendar,
  ScanLine,
  Filter,
  ArrowUpDown,
  Printer,
  FileSpreadsheet,
  Eye,
  EyeOff,
  Zap,
  Box,
  TrendingUp,
  TrendingDown,
  Equal
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function InventoryCountPage() {
  const { t, language } = useLanguage();
  const barcodeInputRef = useRef(null);
  
  const [products, setProducts] = useState([]);
  const [inventorySessions, setInventorySessions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Current session
  const [activeSession, setActiveSession] = useState(null);
  const [countedItems, setCountedItems] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [barcodeInput, setBarcodeInput] = useState('');
  
  // Dialogs
  const [showStartDialog, setShowStartDialog] = useState(false);
  const [showFinishDialog, setShowFinishDialog] = useState(false);
  const [sessionName, setSessionName] = useState('');
  const [selectedFamily, setSelectedFamily] = useState('all');
  const [families, setFamilies] = useState([]);
  
  // Excel Import
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importData, setImportData] = useState([]);
  const [importPreview, setImportPreview] = useState([]);
  const [importFileName, setImportFileName] = useState('');
  const [importMapping, setImportMapping] = useState({
    barcode: '',
    quantity: '',
    name: ''
  });
  const [excelColumns, setExcelColumns] = useState([]);
  const [importStep, setImportStep] = useState(1); // 1: upload, 2: mapping, 3: preview
  const fileInputRef = useRef(null);
  
  // Enhanced features
  const [viewMode, setViewMode] = useState('all'); // all, counted, uncounted, differences
  const [sortBy, setSortBy] = useState('name'); // name, barcode, difference
  const [sortOrder, setSortOrder] = useState('asc');
  const [autoFocus, setAutoFocus] = useState(true);
  const [showOnlyLowStock, setShowOnlyLowStock] = useState(false);
  const [quickCountMode, setQuickCountMode] = useState(false);
  const [lastScannedProduct, setLastScannedProduct] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  // Auto-focus barcode input
  useEffect(() => {
    if (activeSession && autoFocus) {
      const timer = setTimeout(() => barcodeInputRef.current?.focus(), 100);
      return () => clearTimeout(timer);
    }
  }, [activeSession, autoFocus, countedItems]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [productsRes, sessionsRes, familiesRes] = await Promise.all([
        axios.get(`${API}/products`, { headers }),
        axios.get(`${API}/inventory-sessions`, { headers }).catch(() => ({ data: [] })),
        axios.get(`${API}/product-families`, { headers }).catch(() => ({ data: [] }))
      ]);
      setProducts(productsRes.data);
      setInventorySessions(sessionsRes.data);
      setFamilies(familiesRes.data);
      
      // Check for active session
      const active = sessionsRes.data.find(s => s.status === 'active');
      if (active) {
        setActiveSession(active);
        setCountedItems(active.counted_items || {});
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error(language === 'ar' ? 'خطأ في تحميل البيانات' : 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = async () => {
    if (!sessionName.trim()) {
      toast.error(language === 'ar' ? 'يرجى إدخال اسم الجرد' : 'Veuillez entrer un nom');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const session = {
        name: sessionName,
        family_filter: selectedFamily,
        status: 'active',
        started_at: new Date().toISOString(),
        counted_items: {}
      };
      
      const response = await axios.post(`${API}/inventory-sessions`, session, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActiveSession(response.data);
      setCountedItems({});
      setShowStartDialog(false);
      setSessionName('');
      toast.success(language === 'ar' ? 'تم بدء الجرد' : 'Inventaire démarré');
      
      // Focus barcode input
      setTimeout(() => barcodeInputRef.current?.focus(), 100);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    }
  };

  const handleBarcodeSubmit = (e) => {
    e.preventDefault();
    if (!barcodeInput.trim()) return;

    const product = products.find(p => 
      p.barcode === barcodeInput.trim() || 
      p.barcode?.toLowerCase() === barcodeInput.trim().toLowerCase()
    );
    
    if (product) {
      if (quickCountMode) {
        // Quick mode: set count to current system quantity
        setManualCount(product.id, product.quantity);
        toast.success(`${language === 'ar' ? 'تم تأكيد' : 'Confirmé'}: ${language === 'ar' ? product.name_ar : product.name_en} (${product.quantity})`);
      } else {
        incrementCount(product.id);
        toast.success(`${language === 'ar' ? 'تم إضافة' : 'Ajouté'}: ${language === 'ar' ? product.name_ar : product.name_en}`);
      }
      setLastScannedProduct(product);
    } else {
      toast.error(language === 'ar' ? 'منتج غير موجود' : 'Produit non trouvé');
    }
    setBarcodeInput('');
    barcodeInputRef.current?.focus();
  };

  const incrementCount = useCallback((productId) => {
    setCountedItems(prev => {
      const newCount = (prev[productId] || 0) + 1;
      saveCountToSession({ ...prev, [productId]: newCount });
      return { ...prev, [productId]: newCount };
    });
  }, []);

  const decrementCount = useCallback((productId) => {
    setCountedItems(prev => {
      const newCount = Math.max(0, (prev[productId] || 0) - 1);
      saveCountToSession({ ...prev, [productId]: newCount });
      return { ...prev, [productId]: newCount };
    });
  }, []);

  const setManualCount = useCallback((productId, count) => {
    const value = Math.max(0, parseInt(count) || 0);
    setCountedItems(prev => {
      saveCountToSession({ ...prev, [productId]: value });
      return { ...prev, [productId]: value };
    });
  }, []);

  // Set count to match current system quantity
  const confirmCurrentQuantity = useCallback((productId, currentQty) => {
    setCountedItems(prev => {
      saveCountToSession({ ...prev, [productId]: currentQty });
      return { ...prev, [productId]: currentQty };
    });
  }, []);

  const saveCountToSession = async (items) => {
    if (!activeSession) return;
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/inventory-sessions/${activeSession.id}`, {
        ...activeSession,
        counted_items: items
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Error saving count:', error);
    }
  };

  const finishSession = async (applyChanges) => {
    if (!activeSession) return;

    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      // Calculate differences and apply if needed
      if (applyChanges) {
        for (const product of filteredProducts) {
          const countedQty = countedItems[product.id];
          if (countedQty !== undefined && countedQty !== product.quantity) {
            await axios.put(`${API}/products/${product.id}`, {
              ...product,
              quantity: countedQty
            }, { headers });
          }
        }
      }

      // Update session status
      await axios.put(`${API}/inventory-sessions/${activeSession.id}`, {
        ...activeSession,
        status: 'completed',
        completed_at: new Date().toISOString(),
        applied_changes: applyChanges,
        counted_items: countedItems
      }, { headers });

      toast.success(language === 'ar' 
        ? (applyChanges ? 'تم تحديث المخزون بنجاح' : 'تم حفظ الجرد') 
        : (applyChanges ? 'Stock mis à jour' : 'Inventaire enregistré'));
      
      setActiveSession(null);
      setCountedItems({});
      setShowFinishDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    }
  };

  const cancelSession = async () => {
    if (!activeSession) return;
    if (!confirm(language === 'ar' ? 'هل أنت متأكد من إلغاء الجرد؟' : 'Êtes-vous sûr d\'annuler?')) return;

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/inventory-sessions/${activeSession.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActiveSession(null);
      setCountedItems({});
      toast.success(language === 'ar' ? 'تم إلغاء الجرد' : 'Inventaire annulé');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.somethingWentWrong);
    }
  };

  // Excel Import Functions
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setImportFileName(file.name);
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const data = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        if (jsonData.length < 2) {
          toast.error(language === 'ar' ? 'الملف فارغ أو لا يحتوي على بيانات' : 'Le fichier est vide');
          return;
        }

        // Get columns from first row
        const columns = jsonData[0].map((col, idx) => ({
          index: idx,
          name: String(col || `Column ${idx + 1}`)
        }));
        setExcelColumns(columns);
        
        // Store data (skip header)
        setImportData(jsonData.slice(1));
        
        // Auto-detect columns
        const autoMapping = { barcode: '', quantity: '', name: '' };
        columns.forEach(col => {
          const colLower = col.name.toLowerCase();
          if (colLower.includes('barcode') || colLower.includes('باركود') || colLower.includes('code')) {
            autoMapping.barcode = col.index.toString();
          }
          if (colLower.includes('quantity') || colLower.includes('كمية') || colLower.includes('qty') || colLower.includes('quantité')) {
            autoMapping.quantity = col.index.toString();
          }
          if (colLower.includes('name') || colLower.includes('اسم') || colLower.includes('nom') || colLower.includes('product') || colLower.includes('منتج')) {
            autoMapping.name = col.index.toString();
          }
        });
        setImportMapping(autoMapping);
        
        setImportStep(2);
        toast.success(`${language === 'ar' ? 'تم تحميل' : 'Chargé'}: ${jsonData.length - 1} ${language === 'ar' ? 'صف' : 'lignes'}`);
      } catch (error) {
        console.error('Excel parse error:', error);
        toast.error(language === 'ar' ? 'خطأ في قراءة الملف' : 'Erreur de lecture du fichier');
      }
    };
    
    reader.readAsArrayBuffer(file);
  };

  const generateImportPreview = () => {
    if (!importMapping.barcode || !importMapping.quantity) {
      toast.error(language === 'ar' ? 'يرجى تحديد أعمدة الباركود والكمية' : 'Sélectionnez les colonnes code-barres et quantité');
      return;
    }

    const barcodeIdx = parseInt(importMapping.barcode);
    const quantityIdx = parseInt(importMapping.quantity);
    const nameIdx = importMapping.name ? parseInt(importMapping.name) : null;

    const preview = [];
    let matched = 0;
    let notFound = 0;

    importData.forEach((row, rowIndex) => {
      const barcode = String(row[barcodeIdx] || '').trim();
      const quantity = parseInt(row[quantityIdx]) || 0;
      const excelName = nameIdx !== null ? String(row[nameIdx] || '') : '';

      if (!barcode) return;

      const product = products.find(p => 
        p.barcode === barcode || 
        p.barcode?.toLowerCase() === barcode.toLowerCase()
      );

      if (product) {
        matched++;
        preview.push({
          id: product.id,
          barcode,
          excelName,
          productName: language === 'ar' ? product.name_ar : product.name_en,
          currentQty: product.quantity,
          newQty: quantity,
          diff: quantity - product.quantity,
          status: 'matched'
        });
      } else {
        notFound++;
        preview.push({
          id: null,
          barcode,
          excelName,
          productName: null,
          currentQty: null,
          newQty: quantity,
          diff: null,
          status: 'not_found'
        });
      }
    });

    setImportPreview(preview);
    setImportStep(3);
    
    toast.info(`${matched} ${language === 'ar' ? 'متطابق' : 'trouvés'}, ${notFound} ${language === 'ar' ? 'غير موجود' : 'non trouvés'}`);
  };

  const applyImportData = () => {
    const newCounts = { ...countedItems };
    let appliedCount = 0;

    importPreview.forEach(item => {
      if (item.status === 'matched' && item.id) {
        newCounts[item.id] = item.newQty;
        appliedCount++;
      }
    });

    setCountedItems(newCounts);
    saveCountToSession(newCounts);
    
    toast.success(`${language === 'ar' ? 'تم استيراد' : 'Importé'}: ${appliedCount} ${language === 'ar' ? 'منتج' : 'produits'}`);
    
    // Reset import state
    setShowImportDialog(false);
    setImportData([]);
    setImportPreview([]);
    setImportFileName('');
    setImportStep(1);
    setExcelColumns([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const downloadTemplate = () => {
    const templateData = [
      [language === 'ar' ? 'الباركود' : 'Barcode', language === 'ar' ? 'الكمية' : 'Quantité', language === 'ar' ? 'اسم المنتج (اختياري)' : 'Nom du produit (optionnel)'],
      ...products.slice(0, 10).map(p => [p.barcode || '', p.quantity, language === 'ar' ? p.name_ar : p.name_en])
    ];
    
    const ws = XLSX.utils.aoa_to_sheet(templateData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Inventory');
    
    // Set column widths
    ws['!cols'] = [{ wch: 20 }, { wch: 10 }, { wch: 40 }];
    
    XLSX.writeFile(wb, `inventory_template_${new Date().toISOString().split('T')[0]}.xlsx`);
    toast.success(language === 'ar' ? 'تم تحميل القالب' : 'Modèle téléchargé');
  };

  const resetImport = () => {
    setImportStep(1);
    setImportData([]);
    setImportPreview([]);
    setImportFileName('');
    setExcelColumns([]);
    setImportMapping({ barcode: '', quantity: '', name: '' });
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Export inventory report
  const exportReport = () => {
    const reportData = filteredProducts.map(p => ({
      name: language === 'ar' ? p.name_ar : p.name_en,
      barcode: p.barcode || '',
      system_qty: p.quantity,
      counted_qty: countedItems[p.id] ?? '',
      difference: countedItems[p.id] !== undefined ? countedItems[p.id] - p.quantity : ''
    }));
    
    // Create CSV
    const headers = language === 'ar' 
      ? ['المنتج', 'الباركود', 'الكمية الحالية', 'الكمية المجرودة', 'الفرق']
      : ['Product', 'Barcode', 'System Qty', 'Counted Qty', 'Difference'];
    
    const csv = [
      headers.join(','),
      ...reportData.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inventory_${activeSession?.name || 'report'}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success(language === 'ar' ? 'تم تصدير التقرير' : 'Rapport exporté');
  };

  // Filter and sort products
  const filteredProducts = products
    .filter(p => {
      const matchesSearch = searchQuery === '' || 
        p.name_ar?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name_en?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.barcode?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesFamily = selectedFamily === 'all' || p.family_id === selectedFamily;
      
      const counted = countedItems[p.id];
      const matchesView = 
        viewMode === 'all' ||
        (viewMode === 'counted' && counted !== undefined) ||
        (viewMode === 'uncounted' && counted === undefined) ||
        (viewMode === 'differences' && counted !== undefined && counted !== p.quantity);
      
      const matchesLowStock = !showOnlyLowStock || p.quantity <= (p.min_stock || 5);
      
      return matchesSearch && matchesFamily && matchesView && matchesLowStock;
    })
    .sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = (language === 'ar' ? a.name_ar : a.name_en).localeCompare(language === 'ar' ? b.name_ar : b.name_en);
          break;
        case 'barcode':
          comparison = (a.barcode || '').localeCompare(b.barcode || '');
          break;
        case 'difference':
          const diffA = countedItems[a.id] !== undefined ? countedItems[a.id] - a.quantity : -Infinity;
          const diffB = countedItems[b.id] !== undefined ? countedItems[b.id] - b.quantity : -Infinity;
          comparison = diffA - diffB;
          break;
        default:
          comparison = 0;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // Calculate statistics
  const totalProducts = filteredProducts.length;
  const countedProducts = filteredProducts.filter(p => countedItems[p.id] !== undefined).length;
  const progress = totalProducts > 0 ? (countedProducts / totalProducts) * 100 : 0;
  
  const differences = filteredProducts.filter(p => {
    const counted = countedItems[p.id];
    return counted !== undefined && counted !== p.quantity;
  });

  const positiveCount = differences.filter(p => countedItems[p.id] > p.quantity).length;
  const negativeCount = differences.filter(p => countedItems[p.id] < p.quantity).length;

  const formatDate = (dateString) => {
    return new Intl.DateTimeFormat(language === 'ar' ? 'ar-SA' : 'fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  if (loading) {
    return <Layout><div className="flex items-center justify-center min-h-[60vh]"><div className="spinner" /></div></Layout>;
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="inventory-count-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {language === 'ar' ? 'جرد المخزون' : 'Inventaire'}
            </h1>
            <p className="text-muted-foreground mt-1">
              {language === 'ar' ? 'جرد وتحديث كميات المنتجات' : 'Compter et mettre à jour les quantités'}
            </p>
          </div>
          {!activeSession ? (
            <Button onClick={() => setShowStartDialog(true)} className="gap-2" size="lg">
              <Play className="h-5 w-5" />
              {language === 'ar' ? 'بدء جرد جديد' : 'Démarrer inventaire'}
            </Button>
          ) : (
            <div className="flex gap-2 flex-wrap">
              <Button variant="outline" onClick={() => setShowImportDialog(true)} className="gap-2">
                <Upload className="h-4 w-4" />
                {language === 'ar' ? 'استيراد Excel' : 'Importer Excel'}
              </Button>
              <Button variant="outline" onClick={exportReport} className="gap-2">
                <FileSpreadsheet className="h-4 w-4" />
                {language === 'ar' ? 'تصدير' : 'Exporter'}
              </Button>
              <Button variant="outline" onClick={cancelSession} className="gap-2 text-red-500 hover:text-red-600">
                <X className="h-4 w-4" />
                {language === 'ar' ? 'إلغاء' : 'Annuler'}
              </Button>
              <Button onClick={() => setShowFinishDialog(true)} className="gap-2 bg-green-600 hover:bg-green-700">
                <CheckCircle2 className="h-4 w-4" />
                {language === 'ar' ? 'إنهاء الجرد' : 'Terminer'}
              </Button>
            </div>
          )}
        </div>

        {activeSession ? (
          <>
            {/* Session Info & Progress */}
            <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="md:col-span-2">
                    <h3 className="font-semibold text-xl mb-1">{activeSession.name}</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      {language === 'ar' ? 'بدأ في' : 'Démarré le'}: {formatDate(activeSession.started_at)}
                    </p>
                    <Progress value={progress} className="h-4" />
                    <p className="text-sm text-muted-foreground mt-2">
                      {countedProducts} / {totalProducts} ({Math.round(progress)}%)
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-emerald-100 rounded-xl">
                      <TrendingUp className="h-6 w-6 text-emerald-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-emerald-600">{positiveCount}</p>
                      <p className="text-sm text-muted-foreground">{language === 'ar' ? 'زيادة' : 'Surplus'}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-red-100 rounded-xl">
                      <TrendingDown className="h-6 w-6 text-red-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-red-600">{negativeCount}</p>
                      <p className="text-sm text-muted-foreground">{language === 'ar' ? 'نقص' : 'Manque'}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Barcode Scanner Input */}
            <Card className="border-2 border-dashed border-primary/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <Zap className={`h-5 w-5 ${quickCountMode ? 'text-amber-500' : 'text-muted-foreground'}`} />
                    <Label htmlFor="quick-mode" className="cursor-pointer">
                      {language === 'ar' ? 'وضع التأكيد السريع' : 'Mode confirmation rapide'}
                    </Label>
                    <Switch
                      id="quick-mode"
                      checked={quickCountMode}
                      onCheckedChange={setQuickCountMode}
                    />
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {quickCountMode 
                      ? (language === 'ar' ? 'المسح يؤكد الكمية الحالية' : 'Le scan confirme la quantité actuelle')
                      : (language === 'ar' ? 'المسح يضيف +1' : 'Le scan ajoute +1')}
                  </div>
                </div>
                
                <form onSubmit={handleBarcodeSubmit} className="flex gap-2">
                  <div className="relative flex-1">
                    <ScanLine className="absolute start-3 top-1/2 -translate-y-1/2 h-6 w-6 text-primary animate-pulse" />
                    <Input
                      ref={barcodeInputRef}
                      value={barcodeInput}
                      onChange={(e) => setBarcodeInput(e.target.value)}
                      placeholder={language === 'ar' ? 'امسح الباركود أو أدخله يدوياً...' : 'Scanner ou saisir le code-barres...'}
                      className="ps-12 h-14 text-xl font-mono border-2 focus:border-primary"
                      autoFocus
                    />
                  </div>
                  <Button type="submit" size="lg" className="h-14 px-6">
                    <Plus className="h-6 w-6" />
                  </Button>
                </form>
                
                {lastScannedProduct && (
                  <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="font-medium text-green-800">
                          {language === 'ar' ? lastScannedProduct.name_ar : lastScannedProduct.name_en}
                        </p>
                        <p className="text-sm text-green-600">
                          {language === 'ar' ? 'الكمية المجرودة:' : 'Quantité comptée:'} {countedItems[lastScannedProduct.id] || 0}
                        </p>
                      </div>
                    </div>
                    <Badge className="bg-green-600">{lastScannedProduct.barcode}</Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Filters & Controls */}
            <div className="flex flex-wrap gap-4 items-center">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={language === 'ar' ? 'بحث...' : 'Rechercher...'}
                  className="ps-9"
                />
              </div>
              
              <Select value={selectedFamily} onValueChange={setSelectedFamily}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{language === 'ar' ? 'جميع العائلات' : 'Toutes les familles'}</SelectItem>
                  {families.map(f => (
                    <SelectItem key={f.id} value={f.id}>
                      {language === 'ar' ? f.name_ar : f.name_en}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Tabs value={viewMode} onValueChange={setViewMode} className="w-auto">
                <TabsList>
                  <TabsTrigger value="all" className="gap-1">
                    <Box className="h-4 w-4" />
                    {language === 'ar' ? 'الكل' : 'Tous'}
                  </TabsTrigger>
                  <TabsTrigger value="uncounted" className="gap-1">
                    <EyeOff className="h-4 w-4" />
                    {language === 'ar' ? 'غير مجرود' : 'Non comptés'}
                  </TabsTrigger>
                  <TabsTrigger value="differences" className="gap-1">
                    <AlertTriangle className="h-4 w-4" />
                    {language === 'ar' ? 'فروقات' : 'Différences'}
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            {/* Products Table */}
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/50">
                      <TableHead className="w-12">
                        <Checkbox 
                          onCheckedChange={(checked) => {
                            if (checked) {
                              // Confirm all visible products
                              const newCounts = { ...countedItems };
                              filteredProducts.forEach(p => {
                                if (newCounts[p.id] === undefined) {
                                  newCounts[p.id] = p.quantity;
                                }
                              });
                              setCountedItems(newCounts);
                              saveCountToSession(newCounts);
                            }
                          }}
                        />
                      </TableHead>
                      <TableHead>{language === 'ar' ? 'المنتج' : 'Produit'}</TableHead>
                      <TableHead className="text-center w-32">{language === 'ar' ? 'الكمية الحالية' : 'Qté système'}</TableHead>
                      <TableHead className="text-center w-48">{language === 'ar' ? 'الكمية المجرودة' : 'Qté comptée'}</TableHead>
                      <TableHead className="text-center w-28">{language === 'ar' ? 'الفرق' : 'Diff'}</TableHead>
                      <TableHead className="w-20">{language === 'ar' ? 'تأكيد' : 'Confirmer'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredProducts.map(product => {
                      const counted = countedItems[product.id];
                      const diff = counted !== undefined ? counted - product.quantity : null;
                      const rowClass = counted !== undefined 
                        ? (diff === 0 ? 'bg-emerald-50/50' : diff > 0 ? 'bg-blue-50/50' : 'bg-red-50/50') 
                        : '';
                      
                      return (
                        <TableRow key={product.id} className={`${rowClass} hover:bg-muted/30 transition-colors`}>
                          <TableCell>
                            <Checkbox 
                              checked={counted !== undefined}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  confirmCurrentQuantity(product.id, product.quantity);
                                }
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <div>
                              <p className="font-medium">{language === 'ar' ? product.name_ar : product.name_en}</p>
                              <p className="text-xs text-muted-foreground font-mono">{product.barcode}</p>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge variant="outline" className="font-mono text-base px-3 py-1">
                              {product.quantity}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center justify-center gap-1">
                              <Button
                                variant="outline"
                                size="icon"
                                className="h-9 w-9"
                                onClick={() => decrementCount(product.id)}
                              >
                                <Minus className="h-4 w-4" />
                              </Button>
                              <Input
                                type="number"
                                min="0"
                                value={counted ?? ''}
                                onChange={(e) => setManualCount(product.id, e.target.value)}
                                className="w-20 text-center h-9 font-mono text-lg"
                                placeholder="-"
                              />
                              <Button
                                variant="outline"
                                size="icon"
                                className="h-9 w-9"
                                onClick={() => incrementCount(product.id)}
                              >
                                <Plus className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            {diff !== null && (
                              <Badge className={`font-mono text-sm px-3 ${
                                diff === 0 ? 'bg-emerald-100 text-emerald-700' : 
                                diff > 0 ? 'bg-blue-100 text-blue-700' : 
                                'bg-red-100 text-red-700'
                              }`}>
                                {diff === 0 ? <Equal className="h-3 w-3" /> : diff > 0 ? `+${diff}` : diff}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                              onClick={() => confirmCurrentQuantity(product.id, product.quantity)}
                              title={language === 'ar' ? 'تأكيد الكمية الحالية' : 'Confirmer quantité actuelle'}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
                
                {filteredProducts.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>{language === 'ar' ? 'لا توجد منتجات' : 'Aucun produit trouvé'}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Differences Summary */}
            {differences.length > 0 && (
              <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-amber-700">
                    <AlertTriangle className="h-5 w-5" />
                    {language === 'ar' ? 'ملخص الفروقات' : 'Résumé des différences'} ({differences.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {differences.slice(0, 9).map(product => {
                      const diff = countedItems[product.id] - product.quantity;
                      return (
                        <div key={product.id} className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm border">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{language === 'ar' ? product.name_ar : product.name_en}</p>
                            <p className="text-xs text-muted-foreground">{product.barcode}</p>
                          </div>
                          <Badge className={`ms-2 whitespace-nowrap ${diff > 0 ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}`}>
                            {product.quantity} → {countedItems[product.id]}
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                  {differences.length > 9 && (
                    <p className="text-sm text-amber-600 mt-4 text-center">
                      +{differences.length - 9} {language === 'ar' ? 'منتجات أخرى' : 'autres produits'}
                    </p>
                  )}
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          /* No Active Session - Show History */
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                {language === 'ar' ? 'سجل الجرد السابق' : 'Historique des inventaires'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {inventorySessions.length === 0 ? (
                <div className="text-center py-16 text-muted-foreground">
                  <ClipboardList className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <h3 className="text-xl font-medium mb-2">{language === 'ar' ? 'لا يوجد سجل جرد سابق' : 'Aucun historique d\'inventaire'}</h3>
                  <p className="mb-6">{language === 'ar' ? 'ابدأ أول جرد للمخزون الآن' : 'Commencez votre premier inventaire maintenant'}</p>
                  <Button onClick={() => setShowStartDialog(true)} size="lg" className="gap-2">
                    <Play className="h-5 w-5" />
                    {language === 'ar' ? 'بدء أول جرد' : 'Démarrer le premier inventaire'}
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{language === 'ar' ? 'الاسم' : 'Nom'}</TableHead>
                      <TableHead>{language === 'ar' ? 'التاريخ' : 'Date'}</TableHead>
                      <TableHead>{language === 'ar' ? 'الحالة' : 'Statut'}</TableHead>
                      <TableHead>{language === 'ar' ? 'المنتجات' : 'Produits'}</TableHead>
                      <TableHead>{language === 'ar' ? 'تم التطبيق' : 'Appliqué'}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inventorySessions.map(session => (
                      <TableRow key={session.id}>
                        <TableCell className="font-medium">{session.name}</TableCell>
                        <TableCell>{formatDate(session.started_at)}</TableCell>
                        <TableCell>
                          <Badge className={session.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}>
                            {session.status === 'completed' 
                              ? (language === 'ar' ? 'مكتمل' : 'Terminé')
                              : (language === 'ar' ? 'جاري' : 'En cours')}
                          </Badge>
                        </TableCell>
                        <TableCell>{Object.keys(session.counted_items || {}).length}</TableCell>
                        <TableCell>
                          {session.applied_changes ? (
                            <Check className="h-4 w-4 text-emerald-600" />
                          ) : (
                            <X className="h-4 w-4 text-muted-foreground" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        )}

        {/* Start Session Dialog */}
        <Dialog open={showStartDialog} onOpenChange={setShowStartDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <ClipboardList className="h-5 w-5" />
                {language === 'ar' ? 'بدء جرد جديد' : 'Démarrer un inventaire'}
              </DialogTitle>
              <DialogDescription>
                {language === 'ar' ? 'أدخل اسم الجرد واختر العائلة (اختياري)' : 'Entrez un nom et sélectionnez une famille (optionnel)'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label>{language === 'ar' ? 'اسم الجرد' : 'Nom de l\'inventaire'}</Label>
                <Input
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  placeholder={language === 'ar' ? 'مثال: جرد شهر فبراير' : 'Ex: Inventaire février'}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>{language === 'ar' ? 'تصفية حسب العائلة' : 'Filtrer par famille'}</Label>
                <Select value={selectedFamily} onValueChange={setSelectedFamily}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{language === 'ar' ? 'جميع المنتجات' : 'Tous les produits'}</SelectItem>
                    {families.map(f => (
                      <SelectItem key={f.id} value={f.id}>
                        {language === 'ar' ? f.name_ar : f.name_en}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={startNewSession} className="w-full gap-2" size="lg">
                <Play className="h-5 w-5" />
                {language === 'ar' ? 'بدء الجرد' : 'Démarrer'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Finish Session Dialog */}
        <Dialog open={showFinishDialog} onOpenChange={setShowFinishDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                {language === 'ar' ? 'إنهاء الجرد' : 'Terminer l\'inventaire'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg text-center">
                  <p className="text-3xl font-bold text-blue-600">{countedProducts}</p>
                  <p className="text-sm text-blue-600">{language === 'ar' ? 'منتج تم جرده' : 'Produits comptés'}</p>
                </div>
                <div className="p-4 bg-amber-50 rounded-lg text-center">
                  <p className="text-3xl font-bold text-amber-600">{differences.length}</p>
                  <p className="text-sm text-amber-600">{language === 'ar' ? 'فروقات' : 'Différences'}</p>
                </div>
              </div>
              
              {differences.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-sm text-amber-700">
                    {language === 'ar' 
                      ? 'يوجد فروقات في الكميات. هل تريد تحديث المخزون؟' 
                      : 'Il y a des différences. Voulez-vous mettre à jour le stock?'}
                  </p>
                </div>
              )}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => finishSession(false)} className="flex-1">
                  <Save className="h-4 w-4 me-2" />
                  {language === 'ar' ? 'حفظ فقط' : 'Enregistrer'}
                </Button>
                <Button onClick={() => finishSession(true)} className="flex-1 bg-green-600 hover:bg-green-700">
                  <Check className="h-4 w-4 me-2" />
                  {language === 'ar' ? 'تحديث المخزون' : 'Mettre à jour'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
