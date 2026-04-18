import { useState } from 'react';
import { Link, Copy, Check, RefreshCw } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

interface Source {
  title: string;
  url: string;
}

//Props for a single chat bubble — includes the message, metadata, and optional action callbacks.
interface ChatMessageProps {
  role: 'user' | 'bot';
  content: string;
  timestamp: string;
  sources?: Source[];
  onRegenerate?: () => void;
}

//Renders a single chat bubble — user messages align right, bot messages align left.
const ChatMessage = ({ role, content, timestamp, sources, onRegenerate }: ChatMessageProps) => {
  const isUser = role === 'user';
  const { t, isRTL } = useLanguage();
  const [copied, setCopied] = useState(false);

  const ariaLabel = isUser
    ? `${t.youSaid} ${content}`
    : `${t.botSays} ${content}`;

  //Copies the message text to the clipboard and briefly shows a checkmark.
  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      className={`px-4 md:px-6 py-3 md:py-4 animate-fade-in ${isUser ? 'flex justify-end' : 'flex justify-start'}`}
      role="article"
      aria-label={ariaLabel}
    >
      {isUser ? (
        <div className={`hc-user-bubble bg-primary rounded-2xl px-4 py-2.5 max-w-[85%] md:max-w-[70%] ${isRTL ? 'rounded-bl-sm' : 'rounded-br-sm'}`}>
          <p className="text-[15px] md:text-base leading-relaxed whitespace-pre-wrap text-primary-foreground hc-user-text font-medium" dir="auto">
            {content}
          </p>
          <span className="hidden">{timestamp}</span>
        </div>
      ) : (
        <div className="flex max-w-[85%] md:max-w-[75%]">
          <div className="flex-1">
            <div className={`group hc-bot-bubble bg-card rounded-2xl px-4 py-3 shadow-[0_1px_6px_-1px_hsl(var(--primary)/0.08)] border border-border/60 ${isRTL ? 'rounded-tr-sm' : 'rounded-tl-sm'}`}>
              <p className="text-[15px] md:text-base leading-relaxed whitespace-pre-wrap text-bot-text" dir="auto">
                {content}
              </p>
              <span className="hidden">{timestamp}</span>
            </div>

            <div className="mt-1 flex justify-start gap-1">
              <button
                onClick={handleCopy}
                aria-label={isRTL ? 'نسخ الرد' : 'Copy reply'}
                className="copy-btn p-1 rounded-md text-muted-foreground transition-all hover:text-foreground active:scale-90"
              >
                {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
              </button>
              {onRegenerate && (
                <button
                  onClick={onRegenerate}
                  aria-label={isRTL ? 'إعادة توليد الرد' : 'Regenerate response'}
                  className="copy-btn p-1 rounded-md text-muted-foreground transition-all hover:text-foreground active:scale-90"
                >
                  <RefreshCw size={14} />
                </button>
              )}
            </div>

            {sources && sources.length > 0 && (
              <div className="mt-2.5 flex flex-col gap-1.5 items-start">
                <span className="text-xs text-timestamp font-medium ps-1">{t.sources}</span>
                <div className="flex flex-wrap gap-2 justify-start" role="list">
                  {sources.map((source, i) => (
                    <a
                      key={i}
                      href={source.url}
                      role="listitem"
                      aria-label={`${t.sourceLabel} ${source.title}`}
                      className="flex items-center gap-1.5 bg-card border border-border/60 rounded-full px-3 py-1.5 text-xs text-link hover:bg-secondary transition-colors font-arabic shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none hc-link"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Link size={11} className="shrink-0 text-link" aria-hidden="true" />
                      <span>{source.title}</span>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;