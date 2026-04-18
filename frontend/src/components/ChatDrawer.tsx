import { useState, useEffect, useRef } from 'react';
import { SquarePen, Settings, X, ChevronLeft, Eye, AudioLines, Languages } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

//Props for the ChatDrawer component, which manages the side menu state and actions.
interface ChatDrawerProps {
  open: boolean;
  onClose: () => void;
  onNewChat: () => void;
}

//Renders the side drawer with chat actions and app settings.
const ChatDrawer = ({ open, onClose, onNewChat }: ChatDrawerProps) => {
  const [showSettings, setShowSettings] = useState(false);
  const [highContrast, setHighContrast] = useState(() => {
    return localStorage.getItem('highContrast') === 'true';
  });
  const [screenReader, setScreenReader] = useState(false);
  const { lang, setLang, t, isRTL } = useLanguage();
  const firstFocusRef = useRef<HTMLButtonElement>(null);

  //Locks page scroll while open and moves focus to the first action button.
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
      setTimeout(() => firstFocusRef.current?.focus(), 100);
    } else {
      document.body.style.overflow = '';
      setTimeout(() => setShowSettings(false), 300);
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  //Apply high-contrast mode via data-theme attribute + persist to localStorage
  useEffect(() => {
    if (highContrast) {
      document.documentElement.setAttribute('data-theme', 'high-contrast');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('highContrast', String(highContrast));
  }, [highContrast]);

  const handleNewChat = () => {
    onNewChat();
    onClose();
  };

  //Closes the drawer when the Escape key is pressed.
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  //Reusable switch UI used by settings rows.
  const Toggle = ({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) => {
    const knobPosition = isRTL
      ? (checked ? 'left-0.5' : 'left-[calc(100%-1.375rem)]')
      : (checked ? 'right-0.5' : 'right-[calc(100%-1.375rem)]');

    return (
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${checked ? '' : 'bg-white/20'}`}
        style={checked ? { backgroundColor: '#F8D81B' } : {}}
      >
        <span
          className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all duration-200 ${knobPosition}`}
          aria-hidden="true"
        />
      </button>
    );
  };

  //Drawer slides from the right in RTL and from the left in LTR.
  const drawerPositionClass = isRTL
    ? `fixed top-0 right-0 h-full w-72 z-50 transition-transform duration-300 ease-in-out flex flex-col ${open ? 'translate-x-0' : 'translate-x-full'}`
    : `fixed top-0 left-0 h-full w-72 z-50 transition-transform duration-300 ease-in-out flex flex-col ${open ? 'translate-x-0' : '-translate-x-full'}`;

  return (
    <>
      <div
        className={`fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        className={`${drawerPositionClass} hc-drawer`}
        style={{ backgroundColor: '#002856' }}
        dir={isRTL ? 'rtl' : 'ltr'}
        role="dialog"
        aria-label={t.drawerAriaLabel}
        aria-modal={open}
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          {showSettings ? (
            <button
              onClick={() => setShowSettings(false)}
              className="flex items-center gap-2 text-white hover:opacity-80 transition-opacity"
            >
              <ChevronLeft size={18} style={{ color: '#F8D81B' }} className={isRTL ? 'rotate-180' : ''} aria-hidden="true" />
              <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-sm font-bold">{t.settings}</span>
            </button>
          ) : (
            <span />
          )}
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors focus-visible:ring-2 focus-visible:ring-[#F8D81B] focus-visible:outline-none"
            aria-label={t.closeMenu}
          >
            <X size={18} color="white" aria-hidden="true" />
          </button>
        </div>

        <nav className="p-3 flex flex-col gap-1 flex-1" aria-label={t.drawerAriaLabel}>
          {!showSettings ? (
            <>
              <button
                ref={firstFocusRef}
                onClick={handleNewChat}
                className={`flex items-center gap-3 w-full px-3 py-3 rounded-lg text-white hover:bg-white/10 transition-colors focus-visible:ring-2 focus-visible:ring-[#F8D81B] focus-visible:outline-none ${isRTL ? 'text-right' : 'text-left'}`}
              >
                <SquarePen size={18} style={{ color: '#F8D81B' }} aria-hidden="true" />
                <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-sm">{t.newChat}</span>
              </button>

              <button
                onClick={() => setShowSettings(true)}
                className={`flex items-center gap-3 w-full px-3 py-3 rounded-lg text-white hover:bg-white/10 transition-colors focus-visible:ring-2 focus-visible:ring-[#F8D81B] focus-visible:outline-none ${isRTL ? 'text-right' : 'text-left'}`}
              >
                <Settings size={18} style={{ color: '#F8D81B' }} aria-hidden="true" />
                <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-sm">{t.settings}</span>
              </button>
            </>
          ) : (
            <div className="flex flex-col gap-4 mt-2">
              <div className="flex items-center justify-between px-3 py-2">
                <div className="flex items-center gap-3">
                  <Eye size={18} style={{ color: '#F8D81B' }} aria-hidden="true" />
                  <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-white text-sm">{t.highContrast}</span>
                </div>
                <Toggle checked={highContrast} onChange={setHighContrast} />
              </div>

              <div className="flex items-center justify-between px-3 py-2">
                <div className="flex items-center gap-3">
                  <AudioLines size={18} style={{ color: '#F8D81B' }} aria-hidden="true" />
                  <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-white text-sm">{t.screenReader}</span>
                </div>
                <Toggle checked={screenReader} onChange={setScreenReader} />
              </div>

              <div className="flex items-center justify-between px-3 py-2">
                <div className="flex items-center gap-3">
                  <Languages size={18} style={{ color: '#F8D81B' }} aria-hidden="true" />
                  <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-white text-sm">{t.language}</span>
                </div>
                <div className="flex rounded-lg overflow-hidden border border-white/20">
                  <button
                    onClick={() => setLang('ar')}
                    className={`px-3 py-1 text-xs font-bold transition-colors ${lang === 'ar' ? 'text-[#002856]' : 'text-white hover:bg-white/10'}`}
                    style={lang === 'ar' ? { backgroundColor: '#F8D81B' } : {}}
                    aria-pressed={lang === 'ar'}
                  >
                    AR
                  </button>
                  <button
                    onClick={() => setLang('en')}
                    className={`px-3 py-1 text-xs font-bold transition-colors ${lang === 'en' ? 'text-[#002856]' : 'text-white hover:bg-white/10'}`}
                    style={lang === 'en' ? { backgroundColor: '#F8D81B' } : {}}
                    aria-pressed={lang === 'en'}
                  >
                    EN
                  </button>
                </div>
              </div>
            </div>
          )}
        </nav>

        {/* Bottom branding text */}
        <div className="p-4 border-t border-white/10 flex flex-col items-center gap-1" aria-hidden="true">
          <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-white font-bold text-sm font-mono">
            DALEEL KU
          </span>
          <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-white/60 text-xs text-center">
            {t.headerSubtitle}
          </span>
        </div>
      </div>
    </>
  );
};

export default ChatDrawer;