import { useLanguage } from '@/contexts/LanguageContext';

interface TypingIndicatorProps {
  statusMessage?: string;
}

//Renders the animated typing bubble shown while the bot response is loading.
const TypingIndicator = ({ statusMessage }: TypingIndicatorProps) => {
  const { t, isRTL } = useLanguage();

  return (
    <div
      className={`px-4 md:px-6 py-3 md:py-4 flex justify-start`}
      role="status"
      aria-label={t.typingAriaLabel}
    >
      <div className="flex max-w-[85%] md:max-w-[75%]">
        {/* Change the bubble corner based on the text direction. */}
        <div className={`hc-bot-bubble bg-card rounded-2xl px-4 py-3 shadow-[0_1px_6px_-1px_hsl(var(--primary)/0.08)] border border-border/60 ${isRTL ? 'rounded-tr-sm' : 'rounded-tl-sm'}`}>
          <div className="flex items-center gap-2" aria-hidden="true">
            {statusMessage && (
              <span className="text-sm text-muted-foreground leading-none" dir="auto">
                {statusMessage}
              </span>
            )}
            <div className="flex items-center gap-[5px]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0DABE2] animate-dot-fade [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-[#0DABE2] animate-dot-fade [animation-delay:200ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-[#0DABE2] animate-dot-fade [animation-delay:400ms]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
