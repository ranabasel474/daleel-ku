import { useLanguage } from '@/contexts/LanguageContext';

const TypingIndicator = () => {
  const { t, isRTL } = useLanguage();

  return (
    <div
      className={`px-4 md:px-6 py-3 md:py-4 flex justify-start`}
      role="status"
      aria-label={t.typingAriaLabel}
    >
      <div className="flex max-w-[85%] md:max-w-[75%]">
        <div className={`hc-bot-bubble bg-card rounded-2xl px-4 py-3 shadow-[0_1px_6px_-1px_hsl(var(--primary)/0.08)] border border-border/60 ${isRTL ? 'rounded-tr-sm' : 'rounded-tl-sm'}`}>
          <div className="flex items-center gap-[6px] h-5" aria-hidden="true">
            <span className="w-2 h-2 rounded-full bg-[#0DABE2] animate-dot-fade [animation-delay:0ms]" />
            <span className="w-2 h-2 rounded-full bg-[#0DABE2] animate-dot-fade [animation-delay:200ms]" />
            <span className="w-2 h-2 rounded-full bg-[#0DABE2] animate-dot-fade [animation-delay:400ms]" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
