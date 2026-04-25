import { useState, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

interface TypingIndicatorProps {
  statusMessage?: string;
}

//Renders the animated typing bubble shown while the bot response is loading.
const TypingIndicator = ({ statusMessage }: TypingIndicatorProps) => {
  const { t, isRTL } = useLanguage();

  //Tracks the text currently visible in the bubble and its opacity state.
  const [displayed, setDisplayed] = useState(statusMessage ?? '');
  const [visible, setVisible] = useState(!!statusMessage);

  useEffect(() => {
    if (statusMessage === displayed) return;

    if (displayed) {
      //Fade out the current text, then swap to the new one and fade in.
      setVisible(false);
      const swap = setTimeout(() => {
        setDisplayed(statusMessage ?? '');
        setVisible(!!statusMessage);
      }, 150);
      return () => clearTimeout(swap);
    } else {
      //No current text — just fade the new text straight in.
      setDisplayed(statusMessage ?? '');
      setVisible(!!statusMessage);
    }
  }, [statusMessage]);

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
            {displayed && (
              <span
                className="text-sm font-semibold leading-none transition-opacity duration-150"
                style={{ color: '#0A8FB8', opacity: visible ? 1 : 0 }}
                dir="auto"
              >
                {displayed}
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
