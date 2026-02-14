import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Search, X, Package, Loader2, Barcode } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Debounce hook
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(handler);
  }, [value, delay]);
  
  return debouncedValue;
}

export function ProductAutocomplete({ 
  onSelect, 
  placeholder,
  className = "",
  showPrice = true,
  showStock = true,
  autoFocus = false,
  clearOnSelect = true
}) {
  const { language } = useLanguage();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  
  // Barcode scanner support
  const [barcodeBuffer, setBarcodeBuffer] = useState('');
  const barcodeTimeoutRef = useRef(null);
  const lastKeyTimeRef = useRef(0);
  
  const debouncedQuery = useDebounce(query, 300);
  
  // Search products
  const searchProducts = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/products?search=${encodeURIComponent(searchQuery)}`);
      const products = response.data.slice(0, 10); // Limit to 10 results
      setResults(products);
      setIsOpen(products.length > 0);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Effect for debounced search
  useEffect(() => {
    searchProducts(debouncedQuery);
  }, [debouncedQuery, searchProducts]);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) &&
          inputRef.current && !inputRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen || results.length === 0) {
      if (e.key === 'Enter' && query.length >= 2) {
        searchProducts(query);
      }
      return;
    }
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };
  
  // Handle product selection
  const handleSelect = (product) => {
    if (onSelect) {
      onSelect(product);
    }
    if (clearOnSelect) {
      setQuery('');
    }
    setIsOpen(false);
    setSelectedIndex(-1);
  };
  
  // Clear search
  const handleClear = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    inputRef.current?.focus();
  };
  
  // Get product display name
  const getProductName = (product) => {
    return language === 'ar' ? (product.name_ar || product.name_en) : (product.name_en || product.name_ar);
  };
  
  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && results.length > 0 && setIsOpen(true)}
          placeholder={placeholder || (language === 'ar' ? 'ابحث عن منتج...' : 'Rechercher un produit...')}
          className="pr-10 pl-8"
          autoFocus={autoFocus}
          data-testid="product-autocomplete-input"
        />
        {loading && (
          <Loader2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
        {query && !loading && (
          <button
            onClick={handleClear}
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
      
      {/* Dropdown Results */}
      {isOpen && results.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-popover border rounded-lg shadow-lg max-h-80 overflow-y-auto"
          data-testid="autocomplete-dropdown"
        >
          {results.map((product, index) => (
            <div
              key={product.id}
              onClick={() => handleSelect(product)}
              className={`flex items-center gap-3 p-3 cursor-pointer transition-colors ${
                index === selectedIndex ? 'bg-accent' : 'hover:bg-muted'
              } ${index !== results.length - 1 ? 'border-b' : ''}`}
              data-testid={`autocomplete-item-${index}`}
            >
              {/* Product Image */}
              <div className="w-10 h-10 rounded-md overflow-hidden bg-muted flex-shrink-0">
                {product.image_url ? (
                  <img 
                    src={product.image_url} 
                    alt="" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Package className="h-5 w-5 text-muted-foreground" />
                  </div>
                )}
              </div>
              
              {/* Product Info */}
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{getProductName(product)}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  {product.article_code && (
                    <span className="font-mono">{product.article_code}</span>
                  )}
                  {product.barcode && (
                    <span className="font-mono">| {product.barcode}</span>
                  )}
                </div>
              </div>
              
              {/* Price & Stock */}
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                {showPrice && (
                  <span className="font-bold text-primary">
                    {(product.retail_price || 0).toFixed(2)} {language === 'ar' ? 'دج' : 'DA'}
                  </span>
                )}
                {showStock && (
                  <Badge 
                    variant={product.quantity > 0 ? "secondary" : "destructive"}
                    className="text-xs"
                  >
                    {product.quantity || 0} {language === 'ar' ? 'متوفر' : 'en stock'}
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* No Results */}
      {isOpen && query.length >= 2 && results.length === 0 && !loading && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-popover border rounded-lg shadow-lg p-4 text-center text-muted-foreground"
        >
          <Package className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>{language === 'ar' ? 'لا توجد نتائج' : 'Aucun résultat'}</p>
        </div>
      )}
    </div>
  );
}

export default ProductAutocomplete;
