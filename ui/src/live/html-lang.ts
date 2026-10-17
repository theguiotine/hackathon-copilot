// Keeps <html lang> in step with the UI language (screen readers and translation tools read it).
import i18n from '../i18n/config';

const apply = (lng?: string) => {
  const code = (lng ?? 'en').slice(0, 2);
  if (typeof document !== 'undefined' && document.documentElement.lang !== code) document.documentElement.lang = code;
};

apply(i18n.resolvedLanguage ?? i18n.language);
i18n.on('languageChanged', apply);
