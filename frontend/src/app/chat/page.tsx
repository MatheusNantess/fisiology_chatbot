"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Send, User, Bot, Loader2, LogOut, ShieldCheck } from "lucide-react";
import { supabase } from "@/lib/supabase";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "bot";
  content: string;
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const router = useRouter();
  
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  // Guarda Costas de Rota: Puxa o Auth real do Supabase
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        // Redireciona usuários fantasma pra fora
        router.push("/");
        return;
      }
      
      // Armazena o UUID real de banco do usuário!
      const uid = session.user.id;
      setUserId(uid);
      setUserEmail(session.user.email ?? "Aluno Desconhecido");

      // Buscar no Backend Python passando o seu UUID único e blindado
      fetch(`http://localhost:8000/chat/history/${uid}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.history) {
            setMessages(data.history);
          }
        })
        .catch((err) => console.error("Erro ao puxar história da vida:", err));
    };

    checkAuth();

    // Listener para o botão de Deslogar em tempo real
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) router.push("/");
    });

    return () => subscription.unsubscribe();
  }, [router]);

  // Autoscroll
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !userId) return;

    const userMsg = input.trim();
    setInput("");
    
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          thread_id: userId, // Cada Humano é um único grande Thread no Checkpointer
          message: userMsg
        })
      });

      const data = await response.json();
      if (data.reply) {
        setMessages((prev) => [...prev, { role: "bot", content: data.reply }]);
      }
    } catch (error) {
      console.error("Erro API LangGraph:", error);
      setMessages((prev) => [...prev, { role: "bot", content: "❌ Ocorreu um erro no servidor Python RAG." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };

  if (!userId) return <div className="h-screen bg-[#09090b] text-white flex justify-center items-center"><Loader2 className="w-10 h-10 animate-spin text-blue-500"/></div>;

  return (
    <div className="flex h-screen bg-[#09090b] text-white overflow-hidden">
      {/* Sidebar Histórico e Controle */}
      <div className="w-72 border-r border-zinc-800/50 bg-zinc-950/30 flex flex-col p-4 backdrop-blur-xl">
        <div className="flex items-center gap-3 mb-8 px-2 mt-4">
          <div className="w-10 h-10 bg-blue-600/20 rounded-xl flex items-center justify-center border border-blue-500/30">
            <Bot className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <h2 className="font-semibold text-zinc-100 tracking-wide">Fisiologia AI</h2>
            <p className="text-xs text-blue-500 font-medium">Acesso Restrito</p>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3 px-2 flex items-center gap-2">
            Identidade Oficial <ShieldCheck className="w-3 h-3 text-emerald-500"/>
          </div>
          <div className="glass-panel p-4 rounded-xl flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0">
                <User className="w-4 h-4 text-zinc-400" />
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-medium text-zinc-200 truncate">{userEmail}</p>
              </div>
            </div>
            <p className="text-[10px] text-zinc-500 font-mono break-all mt-1 bg-zinc-900/50 p-2 rounded-lg border border-zinc-800">
              UUID: {userId}
            </p>
          </div>
        </div>

        <button 
          onClick={handleLogout}
          className="flex items-center justify-center gap-2 bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white hover:bg-red-600 hover:border-red-500 transition-colors px-2 py-3 rounded-xl text-sm font-medium mt-auto"
        >
          <LogOut className="w-4 h-4" />
          Desconectar Cofre
        </button>
      </div>

      {/* Cérebro Central de Conversação */}
      <div className="flex-1 flex flex-col relative bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900/20 via-[#09090b] to-[#09090b]">
        {/* Histórico Flow */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
          <div className="max-w-3xl mx-auto flex flex-col gap-6 pb-20">
            {messages.length === 0 && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-center mt-32 opacity-50">
                 <Bot className="w-16 h-16 text-zinc-700 mb-4" />
                 <h3 className="text-xl font-medium text-zinc-300">Sala Particular Limpa.</h3>
                 <p className="text-sm text-zinc-500">Seus dados agora são mantidos pela Auth Suprema do Supabase.</p>
              </div>
            )}
            
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "bot" && (
                  <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/20 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-5 h-5 text-blue-500" />
                  </div>
                )}
                
                <div className={`px-5 py-3.5 max-w-[85%] rounded-2xl text-[15px] leading-relaxed shadow-sm
                  ${msg.role === "user" 
                    ? "bg-blue-600 text-white rounded-br-sm" 
                    : "glass-panel text-zinc-200 rounded-bl-sm"}`}
                >
                  {msg.role === "user" ? (
                    <p className="whitespace-pre-wrap font-sans">{msg.content}</p>
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ children }) => <h1 className="text-xl font-bold text-white mt-4 mb-2 first:mt-0">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-bold text-white mt-4 mb-2 first:mt-0">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-base font-semibold text-zinc-100 mt-3 mb-1.5 first:mt-0">{children}</h3>,
                        p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                        strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                        em: ({ children }) => <em className="italic text-zinc-300">{children}</em>,
                        hr: () => <hr className="border-zinc-700 my-4" />,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-2 border-blue-500 pl-4 my-3 text-zinc-400 italic">{children}</blockquote>
                        ),
                        code: ({ inline, children }: { inline?: boolean; children?: React.ReactNode }) =>
                          inline ? (
                            <code className="bg-zinc-800 text-emerald-400 px-1.5 py-0.5 rounded text-[13px] font-mono">{children}</code>
                          ) : (
                            <pre className="bg-zinc-900 border border-zinc-700 rounded-xl p-4 my-3 overflow-x-auto">
                              <code className="text-emerald-400 text-[13px] font-mono leading-relaxed">{children}</code>
                            </pre>
                          ),
                        table: ({ children }) => (
                          <div className="overflow-x-auto my-3">
                            <table className="min-w-full border border-zinc-700 rounded-lg overflow-hidden text-sm">{children}</table>
                          </div>
                        ),
                        th: ({ children }) => <th className="bg-zinc-800 px-4 py-2 text-left font-semibold text-zinc-200 border-b border-zinc-700">{children}</th>,
                        td: ({ children }) => <td className="px-4 py-2 border-b border-zinc-800 text-zinc-300">{children}</td>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  )}
                </div>
                
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-4 h-4 text-zinc-400" />
                  </div>
                )}
              </div>
            ))}
            
            {loading && (
              <div className="flex gap-4 justify-start">
                <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/20 flex items-center justify-center shrink-0">
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                </div>
                <div className="px-5 py-4 max-w-[85%] rounded-2xl glass-panel rounded-bl-sm flex items-center">
                  <div className="dot-flashing"></div>
                </div>
              </div>
            )}
            <div ref={endOfMessagesRef} />
          </div>
        </div>

        {/* Input */}
        <div className="p-4 md:p-6 bg-gradient-to-t from-[#09090b] via-[#09090b] to-transparent">
          <div className="max-w-3xl mx-auto relative">
            <form onSubmit={handleSend} className="relative flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Exemplo de RAG Seguro: O que é pressão capilar?"
                className="w-full bg-zinc-900/80 border border-zinc-800 focus:border-blue-500/50 rounded-2xl pl-5 pr-14 py-4 focus:outline-none focus:ring-1 focus:ring-blue-500/50 transition-all text-white placeholder:text-zinc-500 shadow-xl"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="absolute right-2 p-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-xl transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
