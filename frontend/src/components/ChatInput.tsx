import { useState, useRef, useCallback, useEffect } from "react";
import { Mic, MicOff, SendHorizontal, X, Check } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const SpeechRecognition =
  (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [text, setText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [waveHeights, setWaveHeights] = useState<number[]>(
    Array(24).fill(0.15),
  );
  const { t, isRTL, lang } = useLanguage();
  const recognitionRef = useRef<any>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const waveRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const transcriptRef = useRef("");
  const shouldRestartRef = useRef(false);

  useEffect(() => {
    if (isRecording) {
      setRecordingTime(0);
      timerRef.current = setInterval(
        () => setRecordingTime((prev) => prev + 1),
        1000,
      );
      waveRef.current = setInterval(() => {
        setWaveHeights((prev) => {
          const next = [...prev];
          // Shift left, add new bar on right
          next.shift();
          next.push(0.1 + Math.random() * 0.9);
          return next;
        });
      }, 120);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      if (waveRef.current) clearInterval(waveRef.current);
      setWaveHeights(Array(24).fill(0.15));
      setRecordingTime(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (waveRef.current) clearInterval(waveRef.current);
    };
  }, [isRecording]);

  const formatTime = (s: number) =>
    `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  };

  const startRecording = useCallback(() => {
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    transcriptRef.current = "";
    shouldRestartRef.current = true;
    const recognition = new SpeechRecognition();
    recognition.lang = lang === "ar" ? "ar-KW" : "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognitionRef.current = recognition;

    recognition.onresult = (event: any) => {
      let finalTranscript = "";
      let interimTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }
      transcriptRef.current = finalTranscript + interimTranscript;
    };

    recognition.onerror = (event: any) => {
      // Ignore no-speech errors — just let it restart
      if (event.error === "no-speech") return;
      shouldRestartRef.current = false;
      setIsRecording(false);
    };

    recognition.onend = () => {
      if (shouldRestartRef.current) {
        try {
          const newRecognition = new SpeechRecognition();
          newRecognition.lang = lang === "ar" ? "ar-KW" : "en-US";
          newRecognition.interimResults = true;
          newRecognition.continuous = true;
          newRecognition.onresult = recognition.onresult;
          newRecognition.onerror = recognition.onerror;
          newRecognition.onend = recognition.onend;
          recognitionRef.current = newRecognition;
          newRecognition.start();
        } catch {
          shouldRestartRef.current = false;
          setIsRecording(false);
        }
      } else {
        setIsRecording(false);
      }
    };

    recognition.start();
    setIsRecording(true);
  }, [lang]);

  const cancelRecording = useCallback(() => {
    shouldRestartRef.current = false;
    recognitionRef.current?.stop();
    transcriptRef.current = "";
    setIsRecording(false);
  }, []);

  const confirmRecording = useCallback(() => {
    shouldRestartRef.current = false;
    recognitionRef.current?.stop();
    setIsRecording(false);
    const transcript = transcriptRef.current.trim();
    if (transcript) {
      setText((prev) => (prev ? prev + " " + transcript : transcript));
    }
  }, []);

  const MAX_CHARS = 1000;
  const charCount = text.length;
  const showCounter = charCount > MAX_CHARS * 0.7;
  const isOverLimit = charCount >= MAX_CHARS;

  return (
    <div
      className="bg-card px-3 md:px-5 py-3 md:py-4 border-t border-border shadow-[0_-4px_20px_-4px_hsl(var(--foreground)/0.06)] shrink-0"
      role="region"
      aria-label={t.inputBarAriaLabel}
    >
      <div className="max-w-3xl mx-auto relative flex flex-col gap-1">
        {isRecording ? (
          <div className="w-full bg-secondary rounded-full py-2.5 px-2 flex items-center gap-2 hc-input">
            {/* Cancel button */}
            <button
              onClick={cancelRecording}
              className="shrink-0 w-9 h-9 rounded-full bg-muted flex items-center justify-center text-foreground hover:bg-muted-foreground/20 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              aria-label="Cancel recording"
            >
              <X size={16} aria-hidden="true" />
            </button>

            {/* Waveform + timer */}
            <div className="flex-1 flex items-center justify-center gap-2 min-w-0">
              <div className="flex items-center gap-[2px] h-6">
                {waveHeights.map((h, i) => (
                  <div
                    key={i}
                    className="w-[2.5px] rounded-full bg-foreground/60 transition-all duration-100"
                    style={{ height: `${Math.max(h * 22, 3)}px` }}
                  />
                ))}
              </div>
              <span className="text-xs font-medium text-muted-foreground tabular-nums shrink-0">
                {formatTime(recordingTime)}
              </span>
            </div>

            {/* Confirm button */}
            <button
              onClick={confirmRecording}
              className="shrink-0 w-9 h-9 rounded-full bg-primary flex items-center justify-center text-primary-foreground hover:opacity-90 transition-opacity focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:outline-none"
              aria-label="Confirm recording"
            >
              <Check size={16} aria-hidden="true" />
            </button>
          </div>
        ) : (
          <>
            <div className="relative flex items-end">
              <textarea
                dir="auto"
                rows={1}
                value={text}
                onChange={(e) => {
                  if (e.target.value.length <= MAX_CHARS)
                    setText(e.target.value);
                  // Auto-resize
                  e.target.style.height = "auto";
                  e.target.style.height =
                    Math.min(e.target.scrollHeight, 160) + "px";
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={t.placeholder}
                aria-label={t.inputAriaLabel}
                disabled={disabled}
                maxLength={MAX_CHARS}
                className={`w-full bg-secondary rounded-2xl py-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:ring-2 focus:ring-ring/40 transition-shadow font-arabic hc-input resize-none overflow-y-auto ${isRTL ? "pr-4 pl-24 text-right" : "pl-4 pr-24 text-left"}`}
                style={{ maxHeight: "160px" }}
              />

              <div
                className={`absolute flex items-center gap-1 ${isRTL ? "left-2" : "right-2"}`}
              >
                <button
                  onClick={startRecording}
                  className="p-2 rounded-full transition-colors text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                  aria-label={t.voiceInput}
                >
                  <Mic size={18} aria-hidden="true" />
                </button>
                <button
                  onClick={handleSend}
                  disabled={!text.trim() || disabled || isOverLimit}
                  className="bg-send-btn text-primary-foreground p-2 rounded-full hover:opacity-90 transition-opacity disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:outline-none hc-btn"
                  aria-label={t.send}
                >
                  <SendHorizontal
                    size={16}
                    className={isRTL ? "rotate-180" : ""}
                    aria-hidden="true"
                  />
                </button>
              </div>
            </div>

            {showCounter && (
              <div
                className={`flex ${isRTL ? "justify-start" : "justify-end"} px-3`}
              >
                <span
                  className={`text-[11px] tabular-nums ${isOverLimit ? "text-destructive font-medium" : "text-muted-foreground"}`}
                >
                  {charCount}/{MAX_CHARS}
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatInput;
