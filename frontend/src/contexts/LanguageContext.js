import { createContext, useContext, useState, useEffect } from 'react';

const translations = {
  en: {
    // General
    appName: 'ScreenGuard Pro',
    search: 'Search',
    searchPlaceholder: 'Search by product name, model or barcode...',
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
    currency: 'DZD',
    
    // Auth
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    email: 'Email',
    password: 'Password',
    name: 'Name',
    welcomeBack: 'Welcome Back',
    createAccount: 'Create Account',
    loginSubtitle: 'Sign in to manage your inventory',
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
    customers: 'Customers',
    suppliers: 'Suppliers',
    sales: 'Sales',
    pos: 'Point of Sale',
    purchases: 'Purchases',
    cashManagement: 'Cash Management',
    reports: 'Reports',
    notifications: 'Notifications',
    
    // Dashboard
    totalProducts: 'Total Products',
    totalUsers: 'Total Users',
    totalCustomers: 'Total Customers',
    totalSuppliers: 'Total Suppliers',
    lowStock: 'Low Stock',
    recentProducts: 'Recent Products',
    quickStats: 'Quick Stats',
    todaySales: "Today's Sales",
    totalCash: 'Total Cash',
    
    // Products
    productName: 'Product Name',
    productNameEn: 'Product Name (English)',
    productNameAr: 'Product Name (Arabic)',
    description: 'Description',
    descriptionEn: 'Description (English)',
    descriptionAr: 'Description (Arabic)',
    price: 'Price',
    purchasePrice: 'Purchase Price',
    wholesalePrice: 'Wholesale Price',
    retailPrice: 'Retail Price',
    quantity: 'Quantity',
    imageUrl: 'Image URL',
    barcode: 'Barcode',
    compatibleModels: 'Compatible Models',
    compatibleModelsHelp: 'Enter phone models separated by commas',
    addNewProduct: 'Add New Product',
    editProduct: 'Edit Product',
    deleteProduct: 'Delete Product',
    deleteConfirm: 'Are you sure you want to delete this?',
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
    
    // Customers
    addCustomer: 'Add Customer',
    editCustomer: 'Edit Customer',
    customerName: 'Customer Name',
    phone: 'Phone',
    address: 'Address',
    notes: 'Notes',
    totalPurchases: 'Total Purchases',
    balance: 'Balance',
    noCustomers: 'No customers found',
    customerAdded: 'Customer added successfully',
    customerUpdated: 'Customer updated successfully',
    customerDeleted: 'Customer deleted successfully',
    
    // Suppliers
    addSupplier: 'Add Supplier',
    editSupplier: 'Edit Supplier',
    supplierName: 'Supplier Name',
    noSuppliers: 'No suppliers found',
    supplierAdded: 'Supplier added successfully',
    supplierUpdated: 'Supplier updated successfully',
    supplierDeleted: 'Supplier deleted successfully',
    
    // POS / Sales
    newSale: 'New Sale',
    addToCart: 'Add to Cart',
    cart: 'Cart',
    emptyCart: 'Cart is empty',
    subtotal: 'Subtotal',
    discount: 'Discount',
    total: 'Total',
    paidAmount: 'Paid Amount',
    remaining: 'Remaining',
    paymentMethod: 'Payment Method',
    cash: 'Cash',
    bank: 'Bank',
    wallet: 'E-Wallet',
    completeSale: 'Complete Sale',
    printInvoice: 'Print Invoice',
    saleCompleted: 'Sale completed successfully',
    invoiceNumber: 'Invoice Number',
    selectCustomer: 'Select Customer',
    walkInCustomer: 'Walk-in Customer',
    scanBarcode: 'Scan Barcode',
    returnSale: 'Return Sale',
    saleReturned: 'Sale returned successfully',
    
    // Purchases
    newPurchase: 'New Purchase',
    selectSupplier: 'Select Supplier',
    purchaseCompleted: 'Purchase completed successfully',
    
    // Cash Management
    cashBox: 'Cash Box',
    bankAccount: 'Bank Account',
    eWallet: 'E-Wallet',
    transfer: 'Transfer',
    transferFunds: 'Transfer Funds',
    fromBox: 'From',
    toBox: 'To',
    amount: 'Amount',
    transferCompleted: 'Transfer completed successfully',
    transactions: 'Transactions',
    income: 'Income',
    expense: 'Expense',
    
    // Status
    paid: 'Paid',
    partial: 'Partial',
    unpaid: 'Unpaid',
    returned: 'Returned',
    
    // Notifications
    markAsRead: 'Mark as Read',
    markAllRead: 'Mark All as Read',
    noNotifications: 'No notifications',
    restockAlert: 'Restock Alert',
    lowStockAlert: 'Low Stock Alert',
    
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
    searchPlaceholder: 'ابحث باسم المنتج أو الموديل أو الباركود...',
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
    currency: 'دج',
    
    // Auth
    login: 'تسجيل الدخول',
    register: 'إنشاء حساب',
    logout: 'تسجيل الخروج',
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    name: 'الاسم',
    welcomeBack: 'مرحباً بعودتك',
    createAccount: 'إنشاء حساب جديد',
    loginSubtitle: 'سجل دخولك لإدارة المخزون',
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
    customers: 'الزبائن',
    suppliers: 'الموردين',
    sales: 'المبيعات',
    pos: 'نقطة البيع',
    purchases: 'المشتريات',
    cashManagement: 'إدارة المال',
    reports: 'التقارير',
    notifications: 'الإشعارات',
    
    // Dashboard
    totalProducts: 'إجمالي المنتجات',
    totalUsers: 'إجمالي المستخدمين',
    totalCustomers: 'إجمالي الزبائن',
    totalSuppliers: 'إجمالي الموردين',
    lowStock: 'مخزون منخفض',
    recentProducts: 'أحدث المنتجات',
    quickStats: 'إحصائيات سريعة',
    todaySales: 'مبيعات اليوم',
    totalCash: 'إجمالي النقد',
    
    // Products
    productName: 'اسم المنتج',
    productNameEn: 'اسم المنتج (بالإنجليزية)',
    productNameAr: 'اسم المنتج (بالعربية)',
    description: 'الوصف',
    descriptionEn: 'الوصف (بالإنجليزية)',
    descriptionAr: 'الوصف (بالعربية)',
    price: 'السعر',
    purchasePrice: 'سعر الشراء',
    wholesalePrice: 'سعر الجملة',
    retailPrice: 'سعر التجزئة',
    quantity: 'الكمية',
    imageUrl: 'رابط الصورة',
    barcode: 'الباركود',
    compatibleModels: 'الموديلات المتوافقة',
    compatibleModelsHelp: 'أدخل موديلات الهواتف مفصولة بفواصل',
    addNewProduct: 'إضافة منتج جديد',
    editProduct: 'تعديل المنتج',
    deleteProduct: 'حذف المنتج',
    deleteConfirm: 'هل أنت متأكد من الحذف؟',
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
    
    // Customers
    addCustomer: 'إضافة زبون',
    editCustomer: 'تعديل الزبون',
    customerName: 'اسم الزبون',
    phone: 'الهاتف',
    address: 'العنوان',
    notes: 'ملاحظات',
    totalPurchases: 'إجمالي المشتريات',
    balance: 'الرصيد',
    noCustomers: 'لا يوجد زبائن',
    customerAdded: 'تمت إضافة الزبون بنجاح',
    customerUpdated: 'تم تحديث الزبون بنجاح',
    customerDeleted: 'تم حذف الزبون بنجاح',
    
    // Suppliers
    addSupplier: 'إضافة مورد',
    editSupplier: 'تعديل المورد',
    supplierName: 'اسم المورد',
    noSuppliers: 'لا يوجد موردين',
    supplierAdded: 'تمت إضافة المورد بنجاح',
    supplierUpdated: 'تم تحديث المورد بنجاح',
    supplierDeleted: 'تم حذف المورد بنجاح',
    
    // POS / Sales
    newSale: 'بيع جديد',
    addToCart: 'أضف للسلة',
    cart: 'السلة',
    emptyCart: 'السلة فارغة',
    subtotal: 'المجموع الفرعي',
    discount: 'الخصم',
    total: 'الإجمالي',
    paidAmount: 'المبلغ المدفوع',
    remaining: 'المتبقي',
    paymentMethod: 'طريقة الدفع',
    cash: 'نقداً',
    bank: 'بنك',
    wallet: 'محفظة إلكترونية',
    completeSale: 'إتمام البيع',
    printInvoice: 'طباعة الفاتورة',
    saleCompleted: 'تم البيع بنجاح',
    invoiceNumber: 'رقم الفاتورة',
    selectCustomer: 'اختر الزبون',
    walkInCustomer: 'عميل نقدي',
    scanBarcode: 'مسح الباركود',
    returnSale: 'إرجاع البيع',
    saleReturned: 'تم إرجاع البيع بنجاح',
    
    // Purchases
    newPurchase: 'شراء جديد',
    selectSupplier: 'اختر المورد',
    purchaseCompleted: 'تم الشراء بنجاح',
    
    // Cash Management
    cashBox: 'الصندوق النقدي',
    bankAccount: 'الحساب البنكي',
    eWallet: 'المحفظة الإلكترونية',
    transfer: 'تحويل',
    transferFunds: 'تحويل أموال',
    fromBox: 'من',
    toBox: 'إلى',
    amount: 'المبلغ',
    transferCompleted: 'تم التحويل بنجاح',
    transactions: 'الحركات المالية',
    income: 'دخل',
    expense: 'مصروف',
    
    // Status
    paid: 'مدفوع',
    partial: 'جزئي',
    unpaid: 'غير مدفوع',
    returned: 'مرتجع',
    
    // Notifications
    markAsRead: 'تحديد كمقروء',
    markAllRead: 'تحديد الكل كمقروء',
    noNotifications: 'لا توجد إشعارات',
    restockAlert: 'تنبيه إعادة تخزين',
    lowStockAlert: 'تنبيه مخزون منخفض',
    
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
