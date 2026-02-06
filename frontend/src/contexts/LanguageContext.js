import { createContext, useContext, useState, useEffect } from 'react';

const translations = {
  en: {
    // General
    appName: 'ScreenGuard Pro',
    search: 'Search',
    searchPlaceholder: 'Search by product name or phone model...',
    loading: 'Loading...',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    actions: 'Actions',
    confirm: 'Confirm',
    yes: 'Yes',
    no: 'No',
    
    // Auth
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    email: 'Email',
    password: 'Password',
    name: 'Name',
    welcomeBack: 'Welcome Back',
    createAccount: 'Create Account',
    loginSubtitle: 'Sign in to manage your screen protectors inventory',
    registerSubtitle: 'Create an account to get started',
    noAccount: "Don't have an account?",
    hasAccount: 'Already have an account?',
    invalidCredentials: 'Invalid email or password',
    registerAsAdmin: 'Register as Admin',
    
    // Navigation
    dashboard: 'Dashboard',
    products: 'Products',
    addProduct: 'Add Product',
    settings: 'Settings',
    users: 'Users',
    userManagement: 'User Management',
    
    // Dashboard
    totalProducts: 'Total Products',
    totalUsers: 'Total Users',
    lowStock: 'Low Stock',
    recentProducts: 'Recent Products',
    quickStats: 'Quick Stats',
    
    // Products
    productName: 'Product Name',
    productNameEn: 'Product Name (English)',
    productNameAr: 'Product Name (Arabic)',
    description: 'Description',
    descriptionEn: 'Description (English)',
    descriptionAr: 'Description (Arabic)',
    price: 'Price',
    quantity: 'Quantity',
    imageUrl: 'Image URL',
    compatibleModels: 'Compatible Models',
    compatibleModelsHelp: 'Enter phone models separated by commas',
    addNewProduct: 'Add New Product',
    editProduct: 'Edit Product',
    deleteProduct: 'Delete Product',
    deleteConfirm: 'Are you sure you want to delete this product?',
    productAdded: 'Product added successfully',
    productUpdated: 'Product updated successfully',
    productDeleted: 'Product deleted successfully',
    noProducts: 'No products found',
    noProductsSubtitle: 'Add your first screen protector product',
    viewDetails: 'View Details',
    inStock: 'In Stock',
    outOfStock: 'Out of Stock',
    lowStockWarning: 'Low Stock',
    
    // Filters
    filterByModel: 'Filter by Model',
    allModels: 'All Models',
    clearFilters: 'Clear Filters',
    
    // Low Stock Alerts
    lowStockAlerts: 'Low Stock Alerts',
    lowStockThreshold: 'Low Stock Threshold',
    lowStockThresholdHelp: 'Alert when quantity falls below this number',
    viewLowStockProducts: 'View Low Stock Products',
    noLowStockProducts: 'No low stock products',
    belowThreshold: 'Below threshold',
    
    // OCR
    extractFromImage: 'Extract from Image',
    uploadImage: 'Upload Image',
    extractingModels: 'Extracting models...',
    modelsExtracted: 'Models extracted successfully',
    ocrFailed: 'Failed to extract models from image',
    dropImageHere: 'Drop image here or click to upload',
    supportedFormats: 'Supported formats: JPG, PNG, WEBP',
    
    // Errors
    error: 'Error',
    somethingWentWrong: 'Something went wrong',
    tryAgain: 'Try Again',
    notFound: 'Not Found',
    unauthorized: 'Unauthorized',
    forbidden: 'Access Denied',
    
    // User Management
    allUsers: 'All Users',
    userRole: 'Role',
    userEmail: 'Email',
    userName: 'Name',
    changeRole: 'Change Role',
    deleteUser: 'Delete User',
    deleteUserConfirm: 'Are you sure you want to delete this user?',
    userDeleted: 'User deleted successfully',
    userUpdated: 'User updated successfully',
    noUsers: 'No users found',
    adminRole: 'Admin',
    userRoleLabel: 'User',
    cannotDeleteSelf: 'Cannot delete your own account',
    createdAt: 'Created At',
  },
  ar: {
    // General
    appName: 'سكرين جارد برو',
    search: 'بحث',
    searchPlaceholder: 'ابحث باسم المنتج أو موديل الهاتف...',
    loading: 'جاري التحميل...',
    save: 'حفظ',
    cancel: 'إلغاء',
    delete: 'حذف',
    edit: 'تعديل',
    add: 'إضافة',
    actions: 'الإجراءات',
    confirm: 'تأكيد',
    yes: 'نعم',
    no: 'لا',
    
    // Auth
    login: 'تسجيل الدخول',
    register: 'إنشاء حساب',
    logout: 'تسجيل الخروج',
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    name: 'الاسم',
    welcomeBack: 'مرحباً بعودتك',
    createAccount: 'إنشاء حساب جديد',
    loginSubtitle: 'سجل دخولك لإدارة مخزون زجاج الحماية',
    registerSubtitle: 'أنشئ حساباً للبدء',
    noAccount: 'ليس لديك حساب؟',
    hasAccount: 'لديك حساب بالفعل؟',
    invalidCredentials: 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
    registerAsAdmin: 'التسجيل كمدير',
    
    // Navigation
    dashboard: 'لوحة التحكم',
    products: 'المنتجات',
    addProduct: 'إضافة منتج',
    settings: 'الإعدادات',
    users: 'المستخدمين',
    userManagement: 'إدارة المستخدمين',
    
    // Dashboard
    totalProducts: 'إجمالي المنتجات',
    totalUsers: 'إجمالي المستخدمين',
    lowStock: 'مخزون منخفض',
    recentProducts: 'أحدث المنتجات',
    quickStats: 'إحصائيات سريعة',
    
    // Products
    productName: 'اسم المنتج',
    productNameEn: 'اسم المنتج (بالإنجليزية)',
    productNameAr: 'اسم المنتج (بالعربية)',
    description: 'الوصف',
    descriptionEn: 'الوصف (بالإنجليزية)',
    descriptionAr: 'الوصف (بالعربية)',
    price: 'السعر',
    quantity: 'الكمية',
    imageUrl: 'رابط الصورة',
    compatibleModels: 'الموديلات المتوافقة',
    compatibleModelsHelp: 'أدخل موديلات الهواتف مفصولة بفواصل',
    addNewProduct: 'إضافة منتج جديد',
    editProduct: 'تعديل المنتج',
    deleteProduct: 'حذف المنتج',
    deleteConfirm: 'هل أنت متأكد من حذف هذا المنتج؟',
    productAdded: 'تمت إضافة المنتج بنجاح',
    productUpdated: 'تم تحديث المنتج بنجاح',
    productDeleted: 'تم حذف المنتج بنجاح',
    noProducts: 'لا توجد منتجات',
    noProductsSubtitle: 'أضف أول منتج زجاج حماية',
    viewDetails: 'عرض التفاصيل',
    inStock: 'متوفر',
    outOfStock: 'غير متوفر',
    lowStockWarning: 'مخزون منخفض',
    
    // Filters
    filterByModel: 'تصفية حسب الموديل',
    allModels: 'جميع الموديلات',
    clearFilters: 'مسح الفلاتر',
    
    // Low Stock Alerts
    lowStockAlerts: 'تنبيهات المخزون المنخفض',
    lowStockThreshold: 'حد المخزون المنخفض',
    lowStockThresholdHelp: 'تنبيه عندما تقل الكمية عن هذا الرقم',
    viewLowStockProducts: 'عرض المنتجات منخفضة المخزون',
    noLowStockProducts: 'لا توجد منتجات منخفضة المخزون',
    belowThreshold: 'أقل من الحد',
    
    // OCR
    extractFromImage: 'استخراج من صورة',
    uploadImage: 'رفع صورة',
    extractingModels: 'جاري استخراج الموديلات...',
    modelsExtracted: 'تم استخراج الموديلات بنجاح',
    ocrFailed: 'فشل استخراج الموديلات من الصورة',
    dropImageHere: 'اسحب الصورة هنا أو انقر للرفع',
    supportedFormats: 'الصيغ المدعومة: JPG, PNG, WEBP',
    
    // Errors
    error: 'خطأ',
    somethingWentWrong: 'حدث خطأ ما',
    tryAgain: 'حاول مرة أخرى',
    notFound: 'غير موجود',
    unauthorized: 'غير مصرح',
    forbidden: 'الوصول مرفوض',
    
    // User Management
    allUsers: 'جميع المستخدمين',
    userRole: 'الدور',
    userEmail: 'البريد الإلكتروني',
    userName: 'الاسم',
    changeRole: 'تغيير الدور',
    deleteUser: 'حذف المستخدم',
    deleteUserConfirm: 'هل أنت متأكد من حذف هذا المستخدم؟',
    userDeleted: 'تم حذف المستخدم بنجاح',
    userUpdated: 'تم تحديث المستخدم بنجاح',
    noUsers: 'لا يوجد مستخدمين',
    adminRole: 'مدير',
    userRoleLabel: 'مستخدم',
    cannotDeleteSelf: 'لا يمكن حذف حسابك الخاص',
    createdAt: 'تاريخ الإنشاء',
  }
};

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'ar';
  });
  
  const isRTL = language === 'ar';
  const t = translations[language];
  
  useEffect(() => {
    localStorage.setItem('language', language);
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    document.body.dir = isRTL ? 'rtl' : 'ltr';
  }, [language, isRTL]);
  
  const toggleLanguage = () => {
    setLanguage(prev => prev === 'en' ? 'ar' : 'en');
  };
  
  const value = {
    language,
    setLanguage,
    toggleLanguage,
    isRTL,
    t
  };
  
  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
