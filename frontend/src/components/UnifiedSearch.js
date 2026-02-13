import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Search, Package, Loader2, X, AlertTriangle } from 'lucide-react';
import { playSuccessBeep, playErrorBeep } from '../utils/beep';

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

/**
 * UnifiedSearch - High-performance unified search component
 * 
 * Features:
 * - Fast API-based search with debouncing
 * - Barcode scanner support (Enter key)
 * - Keyboard navigation (arrows, escape)
 * - RTL support
 * - Sound feedback
 * - Works in: Header, POS, Products page
 * 
 * @param {Object} props
 * @param {'header' | 'pos' | 'inline'} props.mode - Search mode
 * @param {Function} props.onSelect - Called when product is selected (for pos/inline)
 * @param {string} props.priceType - 'retail' or 'wholesale' (for pos)
 * @param {Function} props.formatCurrency - Currency formatter
 * @param {string} props.currency - Currency symbol
 * @param {boolean} props.autoFocus - Auto focus input
 * @param {string} props.className - Additional CSS classes
 */
export function UnifiedSearch({
  mode = 'header',
  onSelect,
  priceType = 'retail',
  formatCurrency = (v) => v?.toFixed?.(2) || '0.00',
  currency = 'دج',
  autoFocus = false,
  className = '',
  disabled = false,
}) {
  const { language, isRTL } = useLanguage();
  const navigate = useNavigate();
  
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [totalResults, setTotalResults] = useState(0);
  
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const containerRef = useRef(null);
  
  const debouncedQuery = useDebounce(query, 150); // Fast debounce

  // Search products via API
  const searchProducts = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 1) {
      setResults([]);
      setTotalResults(0);
      setIsOpen(false);
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/products/quick-search`, {
        params: { q: searchQuery, limit: 15 }
      });
      
      setResults(response.data.results || []);
      setTotalResults(response.data.total || 0);
      setIsOpen(response.data.results?.length > 0 || searchQuery.length > 0);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Search error:', error);
      // Fallback to regular search
      try {
        const response = await axios.get(`${API}/products`, {
          params: { search: searchQuery }
        });
        const products = (response.data || []).slice(0, 15);
        setResults(products);
        setTotalResults(products.length);
        setIsOpen(products.length > 0 || searchQuery.length > 0);
      } catch (e) {
        setResults([]);
        setTotalResults(0);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Effect for debounced search
  useEffect(() => {
    if (debouncedQuery) {
      searchProducts(debouncedQuery);
    }
  }, [debouncedQuery, searchProducts]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle product selection
  const handleSelect = useCallback((product) => {
    if (mode === 'header') {
      // Navigate to product detail or products page
      navigate(`/products/${product.id}`);
    } else if (onSelect) {
      onSelect(product);
      playSuccessBeep();
    }
    
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  }, [mode, navigate, onSelect]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      
      if (query) {
        // Check for exact barcode/article_code match first
        const exactMatch = results.find(p => 
          p.barcode === query || 
          p.article_code?.toLowerCase() === query.toLowerCase()
        );
        
        if (exactMatch) {
          handleSelect(exactMatch);
          return;
        }
        
        // If there's a selected item, use it
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex]);
          return;
        }
        
        // If only one result, select it
        if (results.length === 1) {
          handleSelect(results[0]);
          return;
        }
        
        // In header mode, navigate to products page with search
        if (mode === 'header') {
          navigate(`/products?search=${encodeURIComponent(query)}`);
          setQuery('');
          setIsOpen(false);
          return;
        }
        
        // No match found
        playErrorBeep();
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, -1));
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setSelectedIndex(-1);
    }
  }, [query, results, selectedIndex, handleSelect, mode, navigate]);

  // Handle input change
  const handleChange = useCallback((e) => {
    const value = e.target.value;
    setQuery(value);
    if (value) {
      setIsOpen(true);
    }
  }, []);

  // Clear search
  const handleClear = useCallback(() => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    inputRef.current?.focus();
  }, []);

  // Get product display name
  const getProductName = useCallback((product) => {
    return language === 'ar' 
      ? (product.name_ar || product.name_en || product.name) 
      : (product.name_en || product.name_ar || product.name);
  }, [language]);

  // Get price based on type
  const getPrice = useCallback((product) => {
    return priceType === 'wholesale' 
      ? (product.wholesale_price || product.price || 0) 
      : (product.retail_price || product.price || 0);
  }, [priceType]);

  // Placeholder text
  const placeholder = useMemo(() => {
    return language === 'ar' 
      ? 'ابحث بالاسم أو الباركود أو كود المنتج...' 
      : 'Rechercher par nom, code-barres ou code article...';
  }, [language]);

  // Input height based on mode
  const inputHeight = mode === 'pos' ? 'h-11' : 'h-11';

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      <div className="relative">
        <Search 
          className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground pointer-events-none ${
            isRTL ? 'right-3' : 'left-3'
          }`} 
        />
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query && setIsOpen(true)}
          placeholder={placeholder}
          className={`${inputHeight} ${isRTL ? 'pr-10 pl-10' : 'pl-10 pr-10'} search-input focus:ring-2 focus:ring-primary/20`}
          autoFocus={autoFocus}
          disabled={disabled}
          autoComplete="off"
          data-testid="unified-search-input"
        />
        
        {/* Loading indicator */}
        {loading && (
          <Loader2 
            className={`absolute top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground ${
              isRTL ? 'left-3' : 'right-3'
            }`} 
          />
        )}
        
        {/* Clear button */}
        {query && !loading && (
          <button
            onClick={handleClear}
            className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground hover:text-foreground transition-colors ${
              isRTL ? 'left-3' : 'right-3'
            }`}
            type="button"
            data-testid="search-clear-btn"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute z-50 top-full mt-1 w-full bg-popover border rounded-xl shadow-xl max-h-96 overflow-y-auto"
          data-testid="search-dropdown"
        >
          {results.length > 0 ? (
            <>
              {results.map((product, index) => (
                <div
                  key={product.id}
                  onClick={() => handleSelect(product)}
                  className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-all duration-150 ${
                    index === selectedIndex 
                      ? 'bg-primary/10 border-s-2 border-primary' 
                      : product.quantity <= 0
                        ? 'bg-gradient-to-r from-amber-50 to-orange-50 hover:from-amber-100 hover:to-orange-100'
                        : 'hover:bg-muted'
                  } ${index !== results.length - 1 ? 'border-b' : ''}`}
                  data-testid={`search-result-${product.id}`}
                >
                  {/* Product Image/Icon */}
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    product.quantity <= 0 
                      ? 'bg-amber-200 ring-2 ring-amber-400' 
                      : 'bg-muted'
                  }`}>
                    {product.image_url ? (
                      <img 
                        src={product.image_url} 
                        alt="" 
                        className="w-full h-full object-cover rounded-lg"
                        loading="lazy"
                      />
                    ) : product.quantity <= 0 ? (
                      <AlertTriangle className="h-5 w-5 text-amber-700" />
                    ) : (
                      <Package className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>

                  {/* Product Info */}
                  <div className="flex-1 min-w-0">
                    <p className={`font-medium truncate ${product.quantity <= 0 ? 'text-amber-900' : ''}`}>
                      {getProductName(product)}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                      {product.article_code && (
                        <span className="font-mono bg-muted px-1.5 py-0.5 rounded">
                          {product.article_code}
                        </span>
                      )}
                      {product.barcode && (
                        <span className="font-mono">{product.barcode}</span>
                      )}
                      <span>•</span>
                      <span className={product.quantity <= 0 
                        ? 'text-red-600 font-bold' 
                        : ''
                      }>
                        {language === 'ar' ? 'المخزون:' : 'Stock:'} {product.quantity}
                      </span>
                    </div>
                  </div>

                  {/* Price & Stock Badge */}
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className="font-bold text-primary text-lg">
                      {formatCurrency(getPrice(product))} {currency}
                    </span>
                    {product.quantity <= 0 && (
                      <Badge className="text-xs bg-gradient-to-r from-amber-500 to-orange-500 text-white">
                        <AlertTriangle className="h-3 w-3 me-1" />
                        {language === 'ar' ? 'غير متوفر' : 'Rupture'}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
              
              {/* More results indicator */}
              {totalResults > results.length && (
                <div className="px-4 py-2 text-center text-sm text-muted-foreground bg-muted/50">
                  {language === 'ar' 
                    ? `+${totalResults - results.length} نتيجة أخرى - اضغط Enter للبحث الكامل` 
                    : `+${totalResults - results.length} autres résultats - Appuyez Entrée pour recherche complète`}
                </div>
              )}
            </>
          ) : query && !loading ? (
            <div className="p-6 text-center text-muted-foreground">
              <Package className="h-10 w-10 mx-auto mb-2 opacity-30" />
              <p className="font-medium">
                {language === 'ar' ? 'لا توجد نتائج' : 'Aucun résultat'}
              </p>
              <p className="text-sm mt-1">
                {language === 'ar' 
                  ? 'جرب البحث بالباركود أو اسم مختلف' 
                  : 'Essayez avec un code-barres ou nom différent'}
              </p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default UnifiedSearch;
