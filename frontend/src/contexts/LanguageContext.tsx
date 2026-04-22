import { createContext, useContext, useState, ReactNode } from 'react';

type Lang = 'ar' | 'en';

//Translations for all UI text, keyed by language code
const translations = {
  en: {
    // Chat translations
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

    // Admin - Layout
    adminPanel: 'Admin Panel',
    adminPanelHeader: 'Daleel KU Admin Panel',
    dashboard: 'Dashboard',
    contentManagement: 'Content Management',
    queryLogs: 'Query Logs',
    logout: 'Logout',

    // Admin - Login
    email: 'Email',
    password: 'Password',
    signIn: 'Sign In',
    loginError: 'Please enter your email and password',
    loginInvalid: 'Invalid email or password',

    // Admin - Dashboard
    overview: 'Overview',
    totalDocuments: 'Total Documents',
    totalQueries: 'Total Queries',
    answeredQueries: 'Answered Queries',
    referralQueries: 'Referral Queries',
    recentQueries: 'Recent Queries',
    viewAll: 'View All',
    latestContent: 'Latest Content',
    queryText: 'Query Text',
    status: 'Status',
    time: 'Time',
    answered: 'Answered',
    referral: 'Referral',
    title: 'Title',
    type: 'Type',
    topic: 'Topic',
    college: 'College',
    dateAdded: 'Date Added',

    // Admin - Queries
    searchQueries: 'Search queries...',
    exportCSV: 'Export CSV',
    all: 'All',
    session: 'Session',
    query: 'query',
    queries: 'queries',
    noQueriesFound: 'No queries found.',

    // Admin - Query Detail
    queryDetails: 'Query Details',
    backToQueryLogs: 'Back to Query Logs',
    question: 'Question',
    response: 'Response',
    queryNotFound: 'Query not found.',
    otherQueriesInSession: 'Other Queries in This Session',

    // Admin - Knowledge
    content: 'Content',
    addDocument: 'Add Document',
    searchByTitleOrTopic: 'Search by title or topic...',
    sourceUrl: 'Source URL',
    actions: 'Actions',
    noDocumentsFound: 'No documents found.',
    editDocument: 'Edit Document',
    editDocumentDesc: 'Update the document details below.',
    addDocumentDesc: 'Fill in the details to add a new document to the knowledge base.',
    titleRequired: 'Title is required',
    documentTitle: 'Document title',
    documentType: 'Document Type',
    uploadPDF: 'Upload PDF',
    cancel: 'Cancel',
    saveChanges: 'Save Changes',
    deleteDocument: 'Delete Document',
    deleteConfirm: 'Are you sure you want to delete this document? This action cannot be undone.',
    delete: 'Delete',
    edit: 'Edit',

    // Admin - Settings
    adminSettings: 'Settings',
    interfaceLanguage: 'Interface Language',
    interfaceLanguageDesc: 'Choose the display language for the admin panel',
    english: 'English',
    arabic: 'Arabic',

    // Colleges
    allColleges: 'All Colleges',
    engineering: 'Engineering',
    science: 'Science',
    arts: 'Arts',
    law: 'Law',
    medicine: 'Medicine',
    education: 'Education',
    businessAdmin: 'Business Administration',
    sharia: 'Sharia & Islamic Studies',

    // Topics
    admissions: 'Admissions',
    registration: 'Registration',
    exams: 'Exams',
    scholarships: 'Scholarships',
    calendar: 'Calendar',
    regulations: 'Regulations',
    studentServices: 'Student Services',
    graduation: 'Graduation',
  },
  ar: {
    // Chat translations
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
    headerAriaLabel: 'رأس DALEEL KU',
    chatAreaAriaLabel: 'رسائل المحادثة',
    inputBarAriaLabel: 'منطقة إدخال الرسالة',
    drawerAriaLabel: 'قائمة التنقل',
    botSays: 'DALEEL KU يقول:',
    youSaid: 'قلت:',
    botLogoAlt: 'بوت DALEEL KU',
    typingAriaLabel: 'DALEEL KU يكتب',

    // Admin - Layout
    adminPanel: 'لوحة الإدارة',
    adminPanelHeader: 'لوحة إدارة DALEEL KU',
    dashboard: 'لوحة التحكم',
    contentManagement: 'إدارة المحتوى',
    queryLogs: 'سجل الاستعلامات',
    logout: 'تسجيل الخروج',

    // Admin - Login
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    signIn: 'تسجيل الدخول',
    loginError: 'يرجى إدخال البريد الإلكتروني وكلمة المرور',
    loginInvalid: 'البريد الإلكتروني أو كلمة المرور غير صحيحة',

    // Admin - Dashboard
    overview: 'نظرة عامة',
    totalDocuments: 'إجمالي المستندات',
    totalQueries: 'إجمالي الاستعلامات',
    answeredQueries: 'الاستعلامات المُجابة',
    referralQueries: 'استعلامات الإحالة',
    recentQueries: 'الاستعلامات الأخيرة',
    viewAll: 'عرض الكل',
    latestContent: 'أحدث المحتوى',
    queryText: 'نص الاستعلام',
    status: 'الحالة',
    time: 'الوقت',
    answered: 'مُجاب',
    referral: 'إحالة',
    title: 'العنوان',
    type: 'النوع',
    topic: 'الموضوع',
    college: 'الكلية',
    dateAdded: 'تاريخ الإضافة',

    // Admin - Queries
    searchQueries: 'البحث في الاستعلامات...',
    exportCSV: 'تصدير CSV',
    all: 'الكل',
    session: 'جلسة',
    query: 'استعلام',
    queries: 'استعلامات',
    noQueriesFound: 'لم يتم العثور على استعلامات.',

    // Admin - Query Detail
    queryDetails: 'تفاصيل الاستعلام',
    backToQueryLogs: 'العودة إلى سجل الاستعلامات',
    question: 'السؤال',
    response: 'الإجابة',
    queryNotFound: 'لم يتم العثور على الاستعلام.',
    otherQueriesInSession: 'استعلامات أخرى في هذه الجلسة',

    // Admin - Knowledge
    content: 'المحتوى',
    addDocument: 'إضافة مستند',
    searchByTitleOrTopic: 'البحث بالعنوان أو الموضوع...',
    sourceUrl: 'رابط المصدر',
    actions: 'الإجراءات',
    noDocumentsFound: 'لم يتم العثور على مستندات.',
    editDocument: 'تعديل المستند',
    editDocumentDesc: 'قم بتحديث تفاصيل المستند أدناه.',
    addDocumentDesc: 'أدخل التفاصيل لإضافة مستند جديد إلى قاعدة المعرفة.',
    titleRequired: 'العنوان مطلوب',
    documentTitle: 'عنوان المستند',
    documentType: 'نوع المستند',
    uploadPDF: 'رفع ملف PDF',
    cancel: 'إلغاء',
    saveChanges: 'حفظ التغييرات',
    deleteDocument: 'حذف المستند',
    deleteConfirm: 'هل أنت متأكد من حذف هذا المستند؟ لا يمكن التراجع عن هذا الإجراء.',
    delete: 'حذف',
    edit: 'تعديل',

    // Admin - Settings
    adminSettings: 'الإعدادات',
    interfaceLanguage: 'لغة الواجهة',
    interfaceLanguageDesc: 'اختر لغة العرض للوحة الإدارة',
    english: 'الإنجليزية',
    arabic: 'العربية',

    // Colleges
    allColleges: 'جميع الكليات',
    engineering: 'الهندسة',
    science: 'العلوم',
    arts: 'الآداب',
    law: 'الحقوق',
    medicine: 'الطب',
    education: 'التربية',
    businessAdmin: 'إدارة الأعمال',
    sharia: 'الشريعة والدراسات الإسلامية',

    // Topics
    admissions: 'القبول',
    registration: 'التسجيل',
    exams: 'الامتحانات',
    scholarships: 'المنح الدراسية',
    calendar: 'التقويم',
    regulations: 'اللوائح',
    studentServices: 'خدمات الطلاب',
    graduation: 'التخرج',
  },
} as const;

interface LanguageContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: Record<string, string>;
  isRTL: boolean;
}

// eslint-disable-next-line react-refresh/only-export-components
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
