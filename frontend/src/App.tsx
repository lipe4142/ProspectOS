import { useEffect } from "react"
import { SiteStudioPage } from "@/pages/SiteStudioPage"
import { toast } from "sonner"
import { BrowserRouter, Route, Routes } from "react-router-dom"
import { QueryClientProvider } from "@tanstack/react-query"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/sonner"
import { queryClient } from "@/lib/queryClient"
import { PaletaComando } from "@/components/shared/PaletaComando"
import { DashboardPage } from "@/pages/DashboardPage"
import { TarefasPage } from "@/pages/TarefasPage"
import { SessaoProspeccaoPage } from "@/pages/SessaoProspeccaoPage"
import { LeadsMapsPage } from "@/pages/LeadsMapsPage"
import { ConversaPage } from "@/pages/ConversaPage"
import { AnalyticsPage } from "@/pages/AnalyticsPage"
import { InstagramPage } from "@/pages/InstagramPage"
import { InstagramAnalyticsPage } from "@/pages/InstagramAnalyticsPage"
import { InstagramArquivadosPage } from "@/pages/InstagramArquivadosPage"
import { ConfiguracoesPage } from "@/pages/ConfiguracoesPage"
import { DocumentacaoPage } from "@/pages/DocumentacaoPage"

function SincronizarContatoWhatsapp() {
  useEffect(() => {
    const ponte = window.prospectOS
    if (!ponte?.aoReceber) return
    return ponte.aoReceber("cockpit:mensagens-novas", (dados) => {
      if (dados && typeof dados === "object" && "contato_registrado" in dados && dados.contato_registrado === true) {
        toast.success("Mensagem enviada: lead marcado como contatado.")
      }
      for (const chave of ["leads", "lead", "metricas", "metricas-combinadas", "follow-ups-hoje", "meta-semanal", "tarefas-hoje", "conversa", "lead-historico"]) {
        queryClient.invalidateQueries({ queryKey: [chave] })
      }
    })
  }, [])
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SincronizarContatoWhatsapp />
      <TooltipProvider>
        <BrowserRouter>
          <PaletaComando />
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/site-studio" element={<SiteStudioPage />} />
            <Route path="/tarefas" element={<TarefasPage />} />
            <Route path="/sessao" element={<SessaoProspeccaoPage />} />
            <Route path="/leads" element={<LeadsMapsPage />} />
            <Route path="/conversas/:placeId" element={<ConversaPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/instagram" element={<InstagramPage />} />
            <Route path="/instagram/analytics" element={<InstagramAnalyticsPage />} />
            <Route path="/instagram/arquivados" element={<InstagramArquivadosPage />} />
            <Route path="/configuracoes" element={<ConfiguracoesPage />} />
            <Route path="/documentacao" element={<DocumentacaoPage />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="bottom-right" richColors />
      </TooltipProvider>
    </QueryClientProvider>
  )
}
