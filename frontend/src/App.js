import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { LanguageProvider } from "./contexts/LanguageContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";

// Pages
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import ProductsPage from "./pages/ProductsPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import AddProductPage from "./pages/AddProductPage";
import EditProductPage from "./pages/EditProductPage";
import UsersPage from "./pages/UsersPage";
import POSPage from "./pages/POSPage";
import CustomersPage from "./pages/CustomersPage";
import SuppliersPage from "./pages/SuppliersPage";
import CashManagementPage from "./pages/CashManagementPage";
import SalesHistoryPage from "./pages/SalesHistoryPage";
import EmployeesPage from "./pages/EmployeesPage";
import DebtsPage from "./pages/DebtsPage";
import ReportsPage from "./pages/ReportsPage";
import ApiKeysPage from "./pages/ApiKeysPage";
import RechargePage from "./pages/RechargePage";
import ProductFamiliesPage from "./pages/ProductFamiliesPage";
import CustomerDebtsPage from "./pages/CustomerDebtsPage";
import SettingsPage from "./pages/SettingsPage";
import BulkPriceUpdatePage from "./pages/BulkPriceUpdatePage";
import PurchasesPage from "./pages/PurchasesPage";
import WarehousesPage from "./pages/WarehousesPage";
import InventoryCountPage from "./pages/InventoryCountPage";
import BarcodePrintPage from "./pages/BarcodePrintPage";
import DailySessionsPage from "./pages/DailySessionsPage";
import CustomerFamiliesPage from "./pages/CustomerFamiliesPage";
import SupplierFamiliesPage from "./pages/SupplierFamiliesPage";
import WooCommercePage from "./pages/WooCommercePage";
import ShippingPage from "./pages/ShippingPage";
import SimManagementPage from "./pages/SimManagementPage";
import AdvancedAnalyticsPage from "./pages/AdvancedAnalyticsPage";
import LoyaltyPage from "./pages/LoyaltyPage";

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, loading, isAdmin } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Public Route Component (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pos"
        element={
          <ProtectedRoute>
            <POSPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/products"
        element={
          <ProtectedRoute>
            <ProductsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/products/add"
        element={
          <ProtectedRoute adminOnly>
            <AddProductPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/products/:id"
        element={
          <ProtectedRoute>
            <ProductDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/products/:id/edit"
        element={
          <ProtectedRoute adminOnly>
            <EditProductPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/sales"
        element={
          <ProtectedRoute>
            <SalesHistoryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/purchases"
        element={
          <ProtectedRoute adminOnly>
            <PurchasesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/warehouses"
        element={
          <ProtectedRoute adminOnly>
            <WarehousesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/inventory-count"
        element={
          <ProtectedRoute adminOnly>
            <InventoryCountPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/barcode-print"
        element={
          <ProtectedRoute adminOnly>
            <BarcodePrintPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/customers"
        element={
          <ProtectedRoute>
            <CustomersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/suppliers"
        element={
          <ProtectedRoute adminOnly>
            <SuppliersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cash"
        element={
          <ProtectedRoute adminOnly>
            <CashManagementPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedRoute adminOnly>
            <UsersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/employees"
        element={
          <ProtectedRoute adminOnly>
            <EmployeesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/debts"
        element={
          <ProtectedRoute adminOnly>
            <DebtsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute adminOnly>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/api-keys"
        element={
          <ProtectedRoute adminOnly>
            <ApiKeysPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recharge"
        element={
          <ProtectedRoute>
            <RechargePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/product-families"
        element={
          <ProtectedRoute adminOnly>
            <ProductFamiliesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/customer-debts"
        element={
          <ProtectedRoute>
            <CustomerDebtsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute adminOnly>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/bulk-price-update"
        element={
          <ProtectedRoute adminOnly>
            <BulkPriceUpdatePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/daily-sessions"
        element={
          <ProtectedRoute adminOnly>
            <DailySessionsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/customer-families"
        element={
          <ProtectedRoute adminOnly>
            <CustomerFamiliesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/supplier-families"
        element={
          <ProtectedRoute adminOnly>
            <SupplierFamiliesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/woocommerce"
        element={
          <ProtectedRoute adminOnly>
            <WooCommercePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/shipping"
        element={
          <ProtectedRoute adminOnly>
            <ShippingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/sim-management"
        element={
          <ProtectedRoute adminOnly>
            <SimManagementPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute adminOnly>
            <AdvancedAnalyticsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/loyalty"
        element={
          <ProtectedRoute adminOnly>
            <LoyaltyPage />
          </ProtectedRoute>
        }
      />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRoutes />
            <Toaster position="top-center" richColors />
          </BrowserRouter>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
