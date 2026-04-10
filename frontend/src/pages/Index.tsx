import { useState, useRef, useEffect, useCallback } from 'react';
import ChatHeader from '@/components/ChatHeader';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import TypingIndicator from '@/components/TypingIndicator';
import ChatDrawer from '@/components/ChatDrawer';
import { useLanguage } from '@/contexts/LanguageContext';
import { ArrowDown } from 'lucide-react';

interface Message {
  id: number;
  role: 'user' | 'bot';
  content: string;
  timestamp: string;
  sources?: { title: string; url: string }[];
}

const Index = () => {
  const { t, isRTL } = useLanguage();

  const getInitialMessages = (): Message[] => [
    {
      id: 1,
      role: 'bot',
      content: t.welcomeMessage,
      timestamp: new Date().toLocaleTimeString(isRTL ? 'ar-EG' : 'en-US', { hour: 'numeric', minute: '2-digit' }),
    },
  ];

  const [messages, setMessages] = useState<Message[]>(getInitialMessages);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const hamburgerRef = useRef<HTMLButtonElement>(null);
  // Ref keeps the beforeunload handler in sync with the latest sessionId
  // without needing to re-register the listener on every state change.
  const sessionIdRef = useRef<string | null>(null);

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, []);

  const startSession = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:5000/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      setSessionId(data.session_id ?? null);
      return data.session_id as string | null;
    } catch {
      setSessionId(null);
      return null;
    }
  }, []);

  useEffect(() => {
    startSession();
  }, [startSession]);

  // Mirror sessionId into a ref so the beforeunload handler always reads
  // the current value without needing to be re-registered on each change.
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  // Close the session when the user navigates away or closes the tab (beforeunload),
  // and also on React component unmount (effect cleanup).
  // sendBeacon is used for the unload case because fetch is unreliable at that point.
  useEffect(() => {
    const endSession = () => {
      const id = sessionIdRef.current;
      if (!id) return;
      navigator.sendBeacon(`http://localhost:5000/api/session/${id}`);
    };

    window.addEventListener('beforeunload', endSession);
    return () => {
      window.removeEventListener('beforeunload', endSession);
      endSession();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    let ticking = false;
    const handleScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const isScrollable = el.scrollHeight > el.clientHeight + 50;
        const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
        setShowScrollBtn(isScrollable && distanceFromBottom > 150);
        ticking = false;
      });
    };
    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNewChat = async () => {
    // Close the current session before resetting the UI.
    if (sessionId) {
      try {
        await fetch(`http://localhost:5000/api/session/${sessionId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
        });
      } catch {
        // A session-close failure should not block the user from starting fresh.
      }
    }
    setMessages(getInitialMessages());
    startSession();
  };

  const handleRegenerate = async (botMsgIndex: number) => {
    const userMsg = messages.slice(0, botMsgIndex).reverse().find(m => m.role === 'user');
    if (!userMsg || isTyping) return;

    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const period = isRTL ? (hours >= 12 ? 'م' : 'ص') : (hours >= 12 ? 'PM' : 'AM');
    const h12 = hours % 12 || 12;
    const ts = `${h12}:${minutes} ${period}`;

    // Remove the old bot message
    setMessages(prev => prev.filter((_, i) => i !== botMsgIndex));
    setIsTyping(true);

    try {
      const res = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, session_id: sessionId }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { id: Date.now(), role: 'bot', content: data.response, timestamp: ts }]);
    } catch {
      setMessages(prev => [...prev, { id: Date.now(), role: 'bot', content: t.serverError, timestamp: ts }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleDrawerClose = () => {
    setDrawerOpen(false);
    // Return focus to hamburger when drawer closes
    setTimeout(() => hamburgerRef.current?.focus(), 100);
  };

  const handleSend = async (text: string) => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const period = isRTL ? (hours >= 12 ? 'م' : 'ص') : (hours >= 12 ? 'PM' : 'AM');
    const h12 = hours % 12 || 12;
    const ts = `${h12}:${minutes} ${period}`;

    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: ts,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const res = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await res.json();
      const botMsg: Message = {
        id: Date.now() + 1,
        role: 'bot',
        content: data.response,
        timestamp: ts,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      const botMsg: Message = {
        id: Date.now() + 1,
        role: 'bot',
        content: t.serverError,
        timestamp: ts,
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-dvh w-full bg-chat-bg font-arabic" dir={isRTL ? 'rtl' : 'ltr'}>
      <div className="flex flex-col h-dvh w-full overflow-hidden bg-chat-bg">
        <ChatHeader
          onMenuOpen={() => setDrawerOpen(true)}
          hamburgerRef={hamburgerRef}
          drawerOpen={drawerOpen}
        />
        <ChatDrawer open={drawerOpen} onClose={handleDrawerClose} onNewChat={handleNewChat} />

        <main role="main" className="flex-1 overflow-y-auto relative" ref={scrollRef}>
          <div
            role="log"
            aria-live="polite"
            aria-label={t.chatAreaAriaLabel}
            className="py-2 md:py-4 max-w-3xl mx-auto w-full"
          >
            {messages.map((msg, index) => {
              const isLastBot = msg.role === 'bot' && index === messages.map(m => m.role).lastIndexOf('bot');
              return (
                <ChatMessage
                  key={msg.id}
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.timestamp}
                  sources={msg.sources}
                  onRegenerate={isLastBot && !isTyping ? () => handleRegenerate(index) : undefined}
                />
              );
            })}
            {isTyping && <TypingIndicator />}
          </div>

          {showScrollBtn && (
            <button
              onClick={scrollToBottom}
              aria-label={isRTL ? 'انتقل للأسفل' : 'Scroll to bottom'}
              className="scroll-to-bottom-btn absolute bottom-4 left-1/2 -translate-x-1/2 z-10 rounded-full bg-primary text-primary-foreground shadow-lg p-2 transition-opacity hover:opacity-90 active:scale-95"
            >
              <ArrowDown size={20} />
            </button>
          )}
        </main>

        <ChatInput onSend={handleSend} disabled={isTyping} />
      </div>
    </div>
  );
};

export default Index;