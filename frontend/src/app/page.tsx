"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Stethoscope, Loader2, UserPlus, LogIn } from "lucide-react";
import { supabase } from "@/lib/supabase";

type Mode = "login" | "register";

export default function Home() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [infoMsg, setInfoMsg] = useState("");
  const router = useRouter();

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setErrorMsg("");
    setInfoMsg("");
  };

  const switchMode = (m: Mode) => {
    resetForm();
    setMode(m);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    const { data, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) { setErrorMsg(error.message); setLoading(false); return; }
    if (data.session) router.push("/chat");
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setInfoMsg("");

    if (password !== confirmPassword) {
      setErrorMsg("As senhas não coincidem. Verifique e tente novamente.");
      return;
    }
    if (password.length < 6) {
      setErrorMsg("A senha deve ter pelo menos 6 caracteres.");
      return;
    }

    setLoading(true);
    const { data, error } = await supabase.auth.signUp({ email, password });
    setLoading(false);

    if (error) {
      setErrorMsg(error.message);
    } else if (data.session) {
      router.push("/chat");
    } else {
      setInfoMsg("Conta criada! Verifique seu e-mail para confirmar o cadastro, depois faça o login.");
      switchMode("login");
    }
  };

  const isLogin = mode === "login";

  return (
    <main className="flex min-h-screen items-center justify-center p-4 relative overflow-hidden bg-[#09090b]">
      {/* Aura de fundo - muda sutilmente de cor por modo */}
      <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[120px] -z-10 transition-colors duration-700 ${isLogin ? "bg-blue-600/20" : "bg-emerald-600/15"}`}></div>

      <div className="glass-panel w-full max-w-md p-8 rounded-2xl shadow-2xl flex flex-col items-center border border-zinc-800/80">

        {/* Ícone e título mudam por modo */}
        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 border transition-colors duration-500 ${isLogin ? "bg-blue-600/20 border-blue-500/30" : "bg-emerald-600/20 border-emerald-500/30"}`}>
          {isLogin
            ? <Stethoscope className="w-8 h-8 text-blue-500" />
            : <UserPlus className="w-8 h-8 text-emerald-500" />
          }
        </div>

        <h1 className="text-3xl font-bold tracking-tight mb-2 text-center text-white">
          {isLogin ? "Portal Fisiologia" : "Criar Conta"}
        </h1>
        <p className="text-zinc-400 text-center mb-6 text-sm">
          {isLogin
            ? "Plataforma de IA com Memória Persistente."
            : "Preencha os dados abaixo para criar seu acesso."
          }
        </p>

        {/* Toggle Login / Cadastro */}
        <div className="w-full flex bg-zinc-900 rounded-xl p-1 mb-6 border border-zinc-800">
          <button
            onClick={() => switchMode("login")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${isLogin ? "bg-blue-600 text-white shadow" : "text-zinc-400 hover:text-zinc-200"}`}
          >
            <LogIn className="w-4 h-4" /> Login
          </button>
          <button
            onClick={() => switchMode("register")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${!isLogin ? "bg-emerald-600 text-white shadow" : "text-zinc-400 hover:text-zinc-200"}`}
          >
            <UserPlus className="w-4 h-4" /> Cadastro
          </button>
        </div>

        {errorMsg && (
          <div className="w-full bg-red-900/30 border border-red-500/50 text-red-200 p-3 rounded-xl mb-4 text-sm">
            {errorMsg}
          </div>
        )}
        {infoMsg && (
          <div className="w-full bg-emerald-900/30 border border-emerald-500/50 text-emerald-200 p-3 rounded-xl mb-4 text-sm">
            {infoMsg}
          </div>
        )}

        <form onSubmit={isLogin ? handleLogin : handleSignUp} className="w-full flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1 ml-1 uppercase tracking-wider">E-mail</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1 ml-1 uppercase tracking-wider">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm"
              required
            />
          </div>

          {/* Campo extra só no modo Cadastro */}
          {!isLogin && (
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1 ml-1 uppercase tracking-wider">Confirmar Senha</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className={`w-full bg-zinc-900/50 border rounded-xl px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 transition-all text-sm ${
                  confirmPassword && confirmPassword !== password
                    ? "border-red-500/70 focus:ring-red-500/30"
                    : confirmPassword && confirmPassword === password
                    ? "border-emerald-500/70 focus:ring-emerald-500/30"
                    : "border-zinc-800 focus:ring-emerald-500/30"
                }`}
                required
              />
              {confirmPassword && confirmPassword !== password && (
                <p className="text-xs text-red-400 mt-1 ml-1">As senhas não coincidem</p>
              )}
              {confirmPassword && confirmPassword === password && (
                <p className="text-xs text-emerald-400 mt-1 ml-1">✓ Senhas coincidem</p>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`w-full text-white font-medium py-3 rounded-xl transition-colors flex justify-center items-center mt-2 ${
              isLogin
                ? "bg-blue-600 hover:bg-blue-500"
                : "bg-emerald-600 hover:bg-emerald-500"
            }`}
          >
            {loading
              ? <Loader2 className="w-5 h-5 animate-spin" />
              : isLogin ? "Entrar no Laboratório" : "Criar Minha Conta"
            }
          </button>
        </form>
      </div>
    </main>
  );
}
