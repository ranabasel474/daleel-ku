import { createContext, useContext, useState, ReactNode } from 'react';

type Lang = 'ar' | 'en';

//Translations for all UI text, keyed by language code. 
const translations = {
  en: {
    headerSubtitle: 'Your Academic Guide at Kuwait University',
    menuAriaLabel: 'Open menu',
    newChat: 'New Chat',
    settings: 'Settings',
    highContrast: 'High Contrast',
    screenReader: 'Screen Reader',
    language: 'Language',
    closeMenu: 'Close menu',
    placeholder: 'Type your message...',
    inputAriaLabel: 'Type your message',
    voiceInput: 'Voice input',
    voiceRecording: 'Recording, tap to stop',
    send: 'Send message',
    sources: 'Sources',
    sourceLabel: 'Source:',
    serverError: 'Sorry, the server is currently unavailable.',
    welcomeMessage: 'مرحباً! أنا دليل، مساعدك الأكاديمي لجامعة الكويت. كيف يمكنني مساعدتك اليوم؟',
    headerAriaLabel: 'Daleel KU header',
    chatAreaAriaLabel: 'Chat messages',
    inputBarAriaLabel: 'Message input area',
    drawerAriaLabel: 'Navigation menu',
    botSays: 'Daleel KU says:',
    youSaid: 'You said:',
    botLogoAlt: 'Daleel KU bot',
    typingAriaLabel: 'Daleel KU is typing',
  },
  ar: {
    headerSubtitle: 'دليلك الأكاديمي لجامعة الكويت',
    menuAriaLabel: 'فتح القائمة',
    newChat: 'محادثة جديدة',
    settings: 'الإعدادات',
    highContrast: 'تباين عالي',
    screenReader: 'قارئ الشاشة',
    language: 'اللغة',
    closeMenu: 'إغلاق القائمة',
    placeholder: 'اكتب رسالتك...',
    inputAriaLabel: 'اكتب رسالتك',
    voiceInput: 'إدخال صوتي',
    voiceRecording: 'جاري التسجيل، انقر للإيقاف',
    send: 'إرسال رسالة',
    sources: 'المصادر',
    sourceLabel: 'مصدر:',
    serverError: 'عذراً، يبدو أن الخادم غير متاح حالياً',
    welcomeMessage: 'مرحباً! أنا دليل، مساعدك الأكاديمي لجامعة الكويت. كيف يمكنني مساعدتك اليوم؟',
    headerAriaLabel: 'رأس دليل كيو',
    chatAreaAriaLabel: 'رسائل المحادثة',
    inputBarAriaLabel: 'منطقة إدخال الرسالة',
    drawerAriaLabel: 'قائمة التنقل',
    botSays: 'دليل كيو يقول:',
    youSaid: 'قلت:',
    botLogoAlt: 'بوت دليل كيو',
    typingAriaLabel: 'دليل كيو يكتب',
  },
} as const;

interface LanguageContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: Record<string, string>;
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextType | null>(null);

//Provides language, translations, and RTL flag to the whole app
export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [lang, setLang] = useState<Lang>('en');
  const t = translations[lang];
  const isRTL = lang === 'ar';

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, isRTL }}>
      {children}
    </LanguageContext.Provider>
  );
};

//Hook to read the language context, must be used inside LanguageProvider
export const useLanguage = () => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
};