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

//Renders the main chat page and coordinates session lifecycle plus message flow.
const Index = () => {
  const { t, isRTL } = useLanguage();

  //Builds the initial chat state with a welcome message.
  const getInitialMessages = (): Message[] => [
    {
      id: 1,
      role: 'bot',
      content: t.welcomeMessage,
      timestamp: new Date().toLocaleTimeString(isRTL ? 'ar-EG' : 'en-US', { hour: 'numeric', minute: '2-digit' }),
    },
  ];

  //Manages chat messages, session ID for logging, typing state, drawer visibility and scroll button visibility.
  const [messages, setMessages] = useState<Message[]>(getInitialMessages);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const hamburgerRef = useRef<HTMLButtonElement>(null);
  const sessionIdRef = useRef<string | null>(null);

  //Smoothly scrolls the chat container to its latest message.
  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, []);

  //Creates a new backend session and stores its id for later query logging.
  const startSession = useCallback(async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/session`, {
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

  // Update the welcome message whenever the language changes.
  useEffect(() => {
    setMessages(prev =>
      prev.map(msg => (msg.id === 1 ? { ...msg, content: t.welcomeMessage } : msg))
    );
  }, [t.welcomeMessage]);

  //Keep the newest session ID in this ref so endSession can use it.
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  //Ensures the session is closed on page unload to allow proper logging of session duration and queries.
  useEffect(() => {
    const endSession = () => {
      const id = sessionIdRef.current;
      if (!id) return;
      navigator.sendBeacon(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/session/${id}`);
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

  //Starts a fresh chat by ending the current session and resetting local messages.
  const handleNewChat = async () => {
    //Close the current session before resetting the UI.
    if (sessionId) {
      try {
        await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/session/${sessionId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
        });
      } catch {
        //A session-close failure should not block the user from starting fresh.
      }
    }
    setMessages(getInitialMessages());
    startSession();
  };

  //Re-sends the latest matching user question and replaces one bot reply with a new one.
  const handleRegenerate = async (botMsgIndex: number) => {
    const userMsg = messages.slice(0, botMsgIndex).reverse().find(m => m.role === 'user');
    if (!userMsg || isTyping) return;

    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const period = isRTL ? (hours >= 12 ? 'م' : 'ص') : (hours >= 12 ? 'PM' : 'AM');
    const h12 = hours % 12 || 12;
    const ts = `${h12}:${minutes} ${period}`;

    //Remove the old chatbot message
    setMessages(prev => prev.filter((_, i) => i !== botMsgIndex));
    setIsTyping(true);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, session_id: sessionId }),
      });
      const data = await res.json();
      const regenSources =
        data.was_answered && data.source_url
          ? [{ title: data.source_name || data.source_url, url: data.source_url }]
          : undefined;
      setMessages(prev => [...prev, { id: Date.now(), role: 'bot', content: data.response, timestamp: ts, sources: regenSources }]);
    } catch {
      setMessages(prev => [...prev, { id: Date.now(), role: 'bot', content: t.serverError, timestamp: ts }]);
    } finally {
      setIsTyping(false);
    }
  };

  //Close the drawer, then move focus back to the menu button.
  const handleDrawerClose = () => {
    setDrawerOpen(false);

    setTimeout(() => hamburgerRef.current?.focus(), 100);
  };

  //Returns true if the query text contains Arabic characters.
  const isArabicText = (text: string) => /[؀-ۿ]/.test(text);

  //Sends a user message using a two-step classify → complete flow, updating status at each stage.
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

    const arabic = isArabicText(text);

    try {
      // Step 1 — classify the query and show classifying status
      setStatusMessage(arabic ? 'جاري تحليل سؤالك' : 'Understanding your question');

      const classifyRes = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/query/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const classifyData = await classifyRes.json();
      const queryType: string = classifyData.query_type ?? 'general';

      // Step 2 — show search status for general queries, skip it for GPA
      if (queryType === 'general') {
        setStatusMessage(arabic ? 'جاري البحث عن المصادر المناسبة' : 'Looking for relevant resources');
      } else {
        setStatusMessage(arabic ? 'جاري كتابة إجابة سؤالك' : 'Generating your answer');
      }

      const completeRes = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/query/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId, query_type: queryType }),
      });

      // Switch to generating status once the RAG search is done and we await the LLM
      if (queryType === 'general') {
        setStatusMessage(arabic ? 'جاري كتابة إجابة سؤالك' : 'Generating your answer');
      }

      const data = await completeRes.json();

      const sources =
        data.was_answered && data.source_url
          ? [{ title: data.source_name || data.source_url, url: data.source_url }]
          : undefined;

      const botMsg: Message = {
        id: Date.now() + 1,
        role: 'bot',
        content: data.response,
        timestamp: ts,
        sources,
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
      setStatusMessage('');
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
            {isTyping && <TypingIndicator statusMessage={statusMessage} />}
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