// Date and time formatting utilities with standard (Western) numerals
// This ensures dates are displayed as 09/02/2026 instead of ٠٩/٠٢/٢٠٢٦

/**
 * Format date to standard numerals (DD/MM/YYYY)
 * @param {string|Date} dateInput - Date string or Date object
 * @param {string} language - 'ar' or 'fr'
 * @param {Object} options - Additional options
 * @returns {string} Formatted date string with Western numerals
 */
export const formatDate = (dateInput, language = 'ar', options = {}) => {
  if (!dateInput) return '-';
  
  try {
    const date = new Date(dateInput);
    if (isNaN(date.getTime())) return '-';
    
    const {
      showTime = false,
      showYear = true,
      shortMonth = false
    } = options;
    
    // Always use en-US locale to get Western numerals
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    
    let formatted = `${day}/${month}`;
    if (showYear) {
      formatted += `/${year}`;
    }
    
    if (showTime) {
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      formatted += ` ${hours}:${minutes}`;
    }
    
    return formatted;
  } catch (e) {
    console.error('Date formatting error:', e);
    return '-';
  }
};

/**
 * Format datetime with standard numerals (DD/MM/YYYY HH:mm)
 * @param {string|Date} dateInput - Date string or Date object
 * @returns {string} Formatted datetime string
 */
export const formatDateTime = (dateInput) => {
  return formatDate(dateInput, 'ar', { showTime: true });
};

/**
 * Format time only with standard numerals (HH:mm)
 * @param {string|Date} dateInput - Date string or Date object
 * @returns {string} Formatted time string
 */
export const formatTime = (dateInput) => {
  if (!dateInput) return '-';
  
  try {
    const date = new Date(dateInput);
    if (isNaN(date.getTime())) return '-';
    
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    
    return `${hours}:${minutes}`;
  } catch (e) {
    return '-';
  }
};

/**
 * Format number with standard numerals and thousand separators
 * @param {number} value - Number to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted number string
 */
export const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '0';
  
  const num = parseFloat(value);
  if (isNaN(num)) return '0';
  
  // Use en-US locale for Western numerals with proper formatting
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).replace(/,/g, ' '); // Replace comma with space for thousand separator
};

/**
 * Format currency with standard numerals
 * @param {number} value - Amount to format
 * @param {string} currency - Currency symbol (default: 'دج')
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (value, currency = 'دج') => {
  const formatted = formatNumber(value, 2);
  return `${formatted} ${currency}`;
};

/**
 * Get relative time string (e.g., "منذ ساعة", "il y a 1 heure")
 * @param {string|Date} dateInput - Date string or Date object
 * @param {string} language - 'ar' or 'fr'
 * @returns {string} Relative time string
 */
export const getRelativeTime = (dateInput, language = 'ar') => {
  if (!dateInput) return '-';
  
  try {
    const date = new Date(dateInput);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (language === 'ar') {
      if (diffMinutes < 1) return 'الآن';
      if (diffMinutes < 60) return `منذ ${diffMinutes} دقيقة`;
      if (diffHours < 24) return `منذ ${diffHours} ساعة`;
      if (diffDays < 7) return `منذ ${diffDays} يوم`;
      return formatDate(date, language);
    } else {
      if (diffMinutes < 1) return 'maintenant';
      if (diffMinutes < 60) return `il y a ${diffMinutes} min`;
      if (diffHours < 24) return `il y a ${diffHours}h`;
      if (diffDays < 7) return `il y a ${diffDays}j`;
      return formatDate(date, language);
    }
  } catch (e) {
    return '-';
  }
};

export default {
  formatDate,
  formatDateTime,
  formatTime,
  formatNumber,
  formatCurrency,
  getRelativeTime
};
