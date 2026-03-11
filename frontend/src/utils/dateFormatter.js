/**
 * Date/Time Format Configuration for NT Commerce
 * Supports Western (Latin) numerals and customizable formats
 */

// Default configuration with Western numerals
const defaultConfig = {
  shortDateFormat: 'dd/MM/yyyy',
  longDateFormat: 'dd MMMM yyyy',
  timeFormat: 'HH:mm:ss',
  useWesternNumerals: true,
  language: 'ar'
};

// Arabic month names
const ARABIC_MONTHS = {
  1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
  5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
  9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
};

// French month names
const FRENCH_MONTHS = {
  1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
  5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
  9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
};

// Arabic-Indic numerals
const ARABIC_NUMERALS = {
  '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
  '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
};

// Western numerals (reverse mapping)
const WESTERN_NUMERALS = {
  '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
  '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
};

/**
 * Convert numerals based on configuration
 */
export function convertNumerals(text, toWestern = true) {
  if (!text) return text;
  
  let result = String(text);
  
  if (toWestern) {
    // Convert Arabic numerals to Western
    Object.entries(WESTERN_NUMERALS).forEach(([ar, western]) => {
      result = result.replace(new RegExp(ar, 'g'), western);
    });
  } else {
    // Convert Western numerals to Arabic
    Object.entries(ARABIC_NUMERALS).forEach(([western, ar]) => {
      result = result.replace(new RegExp(western, 'g'), ar);
    });
  }
  
  return result;
}

/**
 * Get month name
 */
export function getMonthName(month, language = 'ar') {
  const months = language === 'ar' ? ARABIC_MONTHS : FRENCH_MONTHS;
  return months[month] || String(month);
}

/**
 * Apply format to date
 */
function applyFormat(date, formatStr, config = defaultConfig) {
  let result = formatStr;
  
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const seconds = date.getSeconds();
  
  // Year
  result = result.replace('yyyy', String(year));
  result = result.replace('yy', String(year).slice(-2));
  
  // Month
  result = result.replace('MMMM', getMonthName(month, config.language));
  result = result.replace('MMM', getMonthName(month, config.language).slice(0, 3));
  result = result.replace('MM', String(month).padStart(2, '0'));
  result = result.replace(/(?<!M)M(?!M)/g, String(month));
  
  // Day
  result = result.replace('dd', String(day).padStart(2, '0'));
  result = result.replace(/(?<!d)d(?!d)/g, String(day));
  
  // Hours (24-hour)
  result = result.replace('HH', String(hours).padStart(2, '0'));
  result = result.replace(/(?<!H)H(?!H)/g, String(hours));
  
  // Hours (12-hour)
  const hours12 = hours % 12 || 12;
  result = result.replace('hh', String(hours12).padStart(2, '0'));
  result = result.replace(/(?<!h)h(?!h)/g, String(hours12));
  
  // AM/PM
  const ampm = config.language === 'ar' ? (hours < 12 ? 'ص' : 'م') : (hours < 12 ? 'AM' : 'PM');
  result = result.replace('a', ampm);
  
  // Minutes
  result = result.replace('mm', String(minutes).padStart(2, '0'));
  result = result.replace(/(?<!m)m(?!m)/g, String(minutes));
  
  // Seconds
  result = result.replace('ss', String(seconds).padStart(2, '0'));
  result = result.replace(/(?<!s)s(?!s)/g, String(seconds));
  
  // Apply numeral conversion
  result = convertNumerals(result, config.useWesternNumerals);
  
  return result;
}

/**
 * Format date with short format
 */
export function formatShortDate(date = new Date(), config = defaultConfig) {
  return applyFormat(date, config.shortDateFormat, config);
}

/**
 * Format date with long format
 */
export function formatLongDate(date = new Date(), config = defaultConfig) {
  return applyFormat(date, config.longDateFormat, config);
}

/**
 * Format time
 */
export function formatTime(date = new Date(), config = defaultConfig) {
  return applyFormat(date, config.timeFormat, config);
}

/**
 * Format date and time together
 */
export function formatDateTime(date = new Date(), config = defaultConfig, includeTime = true) {
  const dateStr = formatShortDate(date, config);
  if (includeTime) {
    const timeStr = formatTime(date, config);
    return `${dateStr} ${timeStr}`;
  }
  return dateStr;
}

/**
 * Format relative date (e.g., "منذ 5 دقائق")
 */
export function formatRelative(date, config = defaultConfig) {
  const now = new Date();
  const diff = (now - date) / 1000; // seconds
  
  const format = (num) => convertNumerals(String(num), config.useWesternNumerals);
  
  if (config.language === 'ar') {
    if (diff < 60) return 'الآن';
    if (diff < 3600) return `منذ ${format(Math.floor(diff / 60))} دقيقة`;
    if (diff < 86400) return `منذ ${format(Math.floor(diff / 3600))} ساعة`;
    if (diff < 604800) return `منذ ${format(Math.floor(diff / 86400))} يوم`;
    return formatShortDate(date, config);
  } else {
    if (diff < 60) return 'Maintenant';
    if (diff < 3600) return `Il y a ${format(Math.floor(diff / 60))} minutes`;
    if (diff < 86400) return `Il y a ${format(Math.floor(diff / 3600))} heures`;
    if (diff < 604800) return `Il y a ${format(Math.floor(diff / 86400))} jours`;
    return formatShortDate(date, config);
  }
}

/**
 * Format currency with Western or Arabic numerals
 */
export function formatCurrency(amount, currency = 'DZD', config = defaultConfig) {
  const formatted = new Intl.NumberFormat(config.language === 'ar' ? 'ar-DZ' : 'fr-DZ', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount || 0);
  
  // Convert numerals based on config
  const result = convertNumerals(formatted, config.useWesternNumerals);
  
  return config.language === 'ar' ? `${result} دج` : `${result} DA`;
}

/**
 * Format number with Western or Arabic numerals
 */
export function formatNumber(num, config = defaultConfig) {
  const formatted = new Intl.NumberFormat(config.language === 'ar' ? 'ar-DZ' : 'fr-DZ').format(num || 0);
  return convertNumerals(formatted, config.useWesternNumerals);
}

/**
 * Parse date string to Date object
 */
export function parseDate(dateStr, formatStr = 'dd/MM/yyyy') {
  // Convert any Arabic numerals to Western for parsing
  const westernStr = convertNumerals(dateStr, true);
  
  // Simple parsing for common formats
  if (formatStr === 'dd/MM/yyyy') {
    const parts = westernStr.split('/');
    if (parts.length === 3) {
      return new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]));
    }
  }
  
  // Fallback to native parsing
  return new Date(westernStr);
}

// Default export with configuration
export default {
  config: defaultConfig,
  convertNumerals,
  formatShortDate,
  formatLongDate,
  formatTime,
  formatDateTime,
  formatRelative,
  formatCurrency,
  formatNumber,
  parseDate,
  getMonthName,
  
  // Update configuration
  setConfig(newConfig) {
    Object.assign(this.config, newConfig);
  },
  
  // Get current configuration
  getConfig() {
    return { ...this.config };
  }
};
