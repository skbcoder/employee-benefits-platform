"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendChatMessage, type ChatResponse } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  toolCalls?: string[];
  agentUsed?: string;
  confidence?: number;
  complianceRisk?: string;
  latencyMs?: number;
  timestamp: Date;
}

const SUGGESTED_QUESTIONS = [
  "What enrollments are currently processing?",
  "What medical plans are available?",
  "How do I add a dependent?",
  "What is COBRA coverage?",
];

const TOOL_LABELS: Record<string, string> = {
  submit_enrollment: "Submitted enrollment",
  get_enrollment: "Retrieved enrollment",
  check_enrollment_status: "Checked status",
  list_enrollments_by_status: "Listed enrollments",
  list_enrollments_by_employee_id: "Looked up by employee",
  list_enrollments_by_employee_name: "Searched by name",
};

export default function AIChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [aiAvailable, setAiAvailable] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check AI Gateway health on mount
  useEffect(() => {
    fetch("/api/ai/health")
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(() => setAiAvailable(true))
      .catch(() => setAiAvailable(false));
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && !isClosing) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen, isClosing]);

  const handleClose = useCallback(() => {
    setIsClosing(true);
    setTimeout(() => {
      setIsOpen(false);
      setIsClosing(false);
    }, 250);
  }, []);

  const handleToggle = useCallback(() => {
    if (isOpen) {
      handleClose();
    } else {
      setIsOpen(true);
    }
  }, [isOpen, handleClose]);

  const handleSend = useCallback(
    async (text?: string) => {
      const message = text || input.trim();
      if (!message || loading) return;

      setInput("");
      setMessages((prev) => [
        ...prev,
        { role: "user", content: message, timestamp: new Date() },
      ]);
      setLoading(true);

      try {
        const response: ChatResponse = await sendChatMessage(
          message,
          conversationId || undefined
        );

        setConversationId(response.conversation_id);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: response.message,
            toolCalls: response.tool_calls_made,
            agentUsed: response.agent_used,
            confidence: response.confidence,
            complianceRisk: response.compliance_risk,
            latencyMs: response.latency_ms,
            timestamp: new Date(),
          },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "I'm having trouble connecting right now. Please try again in a moment.",
            timestamp: new Date(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [input, loading, conversationId]
  );

  const handleClearChat = useCallback(async () => {
    if (conversationId) {
      try {
        await fetch(`/api/ai/chat?conversation_id=${conversationId}`, {
          method: "DELETE",
        });
      } catch {
        // Best-effort — clear locally regardless
      }
    }
    setMessages([]);
    setConversationId(null);
  }, [conversationId]);

  return (
    <>
      {/* Floating chat button */}
      <button
        onClick={handleToggle}
        className={`fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-all duration-300 ${
          isOpen
            ? "bg-gray-700 hover:bg-gray-600"
            : "bg-green-600 hover:bg-green-500 hover:scale-110"
        }`}
        aria-label={isOpen ? "Close chat" : "Open AI assistant"}
      >
        {isOpen ? (
          <svg
            className="h-6 w-6 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        ) : (
          <svg
            className="h-6 w-6 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        )}
      </button>

      {/* Backdrop overlay */}
      {isOpen && (
        <div
          className={`fixed inset-0 z-40 bg-black/10 transition-opacity duration-300 ${
            isClosing ? "opacity-0" : "opacity-100"
          }`}
          onClick={handleClose}
        />
      )}

      {/* Slide-in panel from the right */}
      {isOpen && (
        <div
          className={`fixed top-0 right-0 z-50 flex h-full w-full max-w-2xl flex-col border-l border-gray-800 bg-[#0d0d14] shadow-2xl shadow-black/50 ${
            isClosing ? "animate-chat-slide-out" : "animate-chat-slide-in"
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-800 bg-[#111118] px-4 py-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/15">
                <svg
                  className="h-4 w-4 text-green-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-100">
                  Benefits Assistant
                </h3>
                <p className="flex items-center gap-1.5 text-xs text-gray-500">
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      aiAvailable === true
                        ? "bg-green-400"
                        : aiAvailable === false
                          ? "bg-red-400"
                          : "bg-gray-500"
                    }`}
                  />
                  {aiAvailable === true
                    ? "Online"
                    : aiAvailable === false
                      ? "Offline"
                      : "Connecting..."}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  onClick={handleClearChat}
                  className="rounded-lg p-2 text-gray-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                  title="Clear chat"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                    />
                  </svg>
                </button>
              )}
              <button
                onClick={handleClose}
                className="rounded-lg p-2 text-gray-500 hover:bg-gray-800 hover:text-gray-300 transition-colors"
                title="Close panel"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.length === 0 && (
              <div className="space-y-3 py-8">
                {aiAvailable === false ? (
                  <div className="flex flex-col items-center gap-3 py-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/10">
                      <svg
                        className="h-6 w-6 text-amber-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                        />
                      </svg>
                    </div>
                    <p className="text-center text-sm text-gray-400">
                      AI assistant is currently unavailable.
                    </p>
                    <p className="text-center text-xs text-gray-600">
                      Start the AI Gateway service to enable chat.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="flex flex-col items-center gap-2 py-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
                        <svg
                          className="h-6 w-6 text-green-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                          />
                        </svg>
                      </div>
                      <p className="text-center text-sm text-gray-300 font-medium">
                        How can I help you today?
                      </p>
                      <p className="text-center text-xs text-gray-500">
                        Ask me anything about your benefits enrollment.
                      </p>
                    </div>
                    <div className="space-y-2 px-2">
                      {SUGGESTED_QUESTIONS.map((q) => (
                        <button
                          key={q}
                          onClick={() => handleSend(q)}
                          className="w-full rounded-lg border border-gray-800 bg-[#111118] px-3 py-2.5 text-left text-xs text-gray-400 hover:border-green-500/30 hover:text-gray-300 transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                    msg.role === "user"
                      ? "bg-green-600/20 text-green-100 rounded-br-sm"
                      : "bg-[#111118] text-gray-300 border border-gray-800/50 rounded-bl-sm"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="prose-chat break-words">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          table: ({ children }) => (
                            <div className="chat-table-wrap">
                              <table>{children}</table>
                            </div>
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap break-words">
                      {msg.content}
                    </div>
                  )}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {msg.toolCalls.map((tool, j) => (
                        <span
                          key={j}
                          className="inline-flex items-center rounded-md bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-medium text-blue-400"
                        >
                          {TOOL_LABELS[tool] || tool.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  )}
                  {msg.agentUsed && (
                    <div className="mt-1.5 flex items-center gap-2 text-[10px]">
                      <span
                        className={`rounded-full px-2 py-0.5 font-medium ${
                          msg.agentUsed === "enrollment"
                            ? "bg-blue-500/15 text-blue-400"
                            : msg.agentUsed === "advisor"
                              ? "bg-green-500/15 text-green-400"
                              : msg.agentUsed === "compliance"
                                ? "bg-amber-500/15 text-amber-400"
                                : msg.agentUsed === "escalation"
                                  ? "bg-red-500/15 text-red-400"
                                  : "bg-gray-500/15 text-gray-400"
                        }`}
                      >
                        {msg.agentUsed}
                      </span>
                      {msg.confidence !== undefined && (
                        <span
                          className={`flex items-center gap-1 ${
                            msg.confidence >= 0.7
                              ? "text-green-500"
                              : msg.confidence >= 0.4
                                ? "text-amber-500"
                                : "text-red-500"
                          }`}
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-current" />
                          {Math.round(msg.confidence * 100)}%
                        </span>
                      )}
                      {msg.complianceRisk && msg.complianceRisk !== "low" && (
                        <span
                          className={`rounded px-1.5 py-0.5 ${
                            msg.complianceRisk === "medium"
                              ? "bg-amber-500/10 text-amber-400"
                              : "bg-red-500/10 text-red-400"
                          }`}
                        >
                          risk: {msg.complianceRisk}
                        </span>
                      )}
                      {msg.latencyMs !== undefined && (
                        <span className="text-gray-600">{msg.latencyMs}ms</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-xl bg-[#111118] border border-gray-800/50 px-4 py-3 rounded-bl-sm">
                  <p className="text-[10px] text-gray-500 mb-1.5">
                    Processing your request...
                  </p>
                  <div className="flex items-center gap-1.5">
                    <div
                      className="h-2 w-2 rounded-full bg-green-400 animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <div
                      className="h-2 w-2 rounded-full bg-green-400 animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <div
                      className="h-2 w-2 rounded-full bg-green-400 animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-gray-800 p-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about benefits..."
                disabled={loading || aiAvailable === false}
                className="flex-1 rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading || !input.trim() || aiAvailable === false}
                className="rounded-lg bg-green-600 px-3 py-2.5 text-white hover:bg-green-500 disabled:opacity-30 disabled:hover:bg-green-600 transition-colors"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
                  />
                </svg>
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
