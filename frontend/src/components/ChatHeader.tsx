import { Menu } from 'lucide-react';
import AcademicBotLogo from './AcademicBotLogo';
import { useLanguage } from '@/contexts/LanguageContext';
import { RefObject } from 'react';

//Props used by ChatHeader, including the function that opens the side menu.
interface ChatHeaderProps {
  onMenuOpen: () => void;
  hamburgerRef?: RefObject<HTMLButtonElement>;
  drawerOpen?: boolean;
}

//Renders the top app bar with the menu button and centered branding.
const ChatHeader = ({ onMenuOpen, hamburgerRef, drawerOpen }: ChatHeaderProps) => {
  const { t, isRTL } = useLanguage();

  return (
    <header
      dir="ltr"
      role="banner"
      aria-label={t.headerAriaLabel}
      className="bg-primary shadow-md flex items-center justify-between px-4 py-3 shrink-0 relative"
    >
      <button
        ref={hamburgerRef}
        onClick={onMenuOpen}
        aria-expanded={drawerOpen}
        aria-haspopup="dialog"
        className={`w-10 h-10 rounded-full bg-primary-foreground/10 hover:bg-primary-foreground/20 flex items-center justify-center text-primary-foreground transition-colors z-10 focus-visible:ring-2 focus-visible:ring-send-btn focus-visible:ring-offset-2 focus-visible:ring-offset-primary focus-visible:outline-none ${isRTL ? 'order-3' : 'order-1'}`}
        aria-label={t.menuAriaLabel}
      >
        <Menu size={20} aria-hidden="true" />
      </button>

      {/* Centered logo and title — positioned absolutely so it stays centered. */}
      <div className="order-2 absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="flex items-center gap-2" dir="ltr">
          <div className="flex items-center justify-center">
            <AcademicBotLogo size={22} animated={true} ariaLabel={t.botLogoAlt} />
          </div>
          <div className="flex items-center self-center">
            <span style={{ fontFamily: "'Somar', sans-serif" }} className="text-send-btn font-bold text-sm translate-y-[4px]" aria-hidden="true">
              DALEEL KU
            </span>
          </div>
        </div>
      </div>

      {/* Empty spacer keeps the layout balanced on the opposite side of the menu button. */}
      <div className={`w-10 h-10 ${isRTL ? 'order-1' : 'order-3'}`} aria-hidden="true" />
    </header>
  );
};

export default ChatHeader;