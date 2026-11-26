import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { httpClient } from "@/services/httpClient"
import { abrirWhatsappInstalado } from "@/services/tarefasService"
import { useClipboard } from "@/hooks/useClipboard"
import { toast } from "sonner"
import type { Lead } from "@/types/lead"

type Demonstracao = { briefing: string; prompt: string; provedor?: string | null; avisos?: string[] }
type Proposta = { cliente: string; servicos: string; inicial: string; mensal: string; prazo: string; pagamento: string; validade: string; observacoes: string }

export function FerramentasComerciais({ lead }: { lead: Lead }) {
  const [aba, setAba] = useState<"demo" | "proposta" | null>(null)
  const [identidade, setIdentidade] = useState("")
  const [servicos, setServicos] = useState("")
  const [referencias, setReferencias] = useState("")
  const [demo, setDemo] = useState<Demonstracao | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [pdfBaixado, setPdfBaixado] = useState(false)
  const { copiar } = useClipboard()
  const [proposta, setProposta] = useState<Proposta>({
    cliente: lead.nome, servicos: "Site profissional responsivo, integração com WhatsApp e SEO básico.",
    inicial: "0", mensal: "90", prazo: "7 dias após receber os materiais e aprovar o escopo",
    pagamento: "Mensalidade conforme data de vencimento acordada.", validade: "7 dias", observacoes: "",
  })
  const endpoint = "/api/leads/" + encodeURIComponent(lead.place_id)
  function atualizar(chave: keyof Proposta, valor: string) {
    setProposta(p => ({ ...p, [chave]: valor }))
    setPdfBaixado(false)
  }
  async function gerarDemo() {
    setOcupado(true)
    try {
      const resposta = await httpClient.post<Demonstracao>(endpoint + "/demonstracao", { identidade, servicos, referencias })
      setDemo(resposta)
      if (resposta.avisos?.length) toast.warning(resposta.avisos.join(" "))
    } catch (e) { toast.error(e instanceof Error ? e.message : "Falha ao gerar demonstração.") }
    finally { setOcupado(false) }
  }
  async function baixarProposta() {
    setOcupado(true)
    try {
      const resposta = await fetch(endpoint + "/proposta.pdf", { method: "POST",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(proposta) })
      if (!resposta.ok) {
        const erro = await resposta.json().catch(() => ({}))
        throw new Error(erro.erro || "Não foi possível gerar o PDF.")
      }
      if (!resposta.headers.get("content-type")?.includes("application/pdf")) throw new Error("Resposta não é um PDF.")
      const url = URL.createObjectURL(await resposta.blob())
      const a = document.createElement("a")
      a.href = url
      a.download = "Proposta-FLP-Systems.pdf"
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 30000)
      setPdfBaixado(true)
      toast.success("PDF gerado. Revise antes de anexar no WhatsApp.")
    } catch (e) { toast.error(e instanceof Error ? e.message : "Falha ao gerar proposta.") }
    finally { setOcupado(false) }
  }
  function enviarProposta() {
    if (!lead.whatsapp_link || !pdfBaixado) return
    try {
      abrirWhatsappInstalado(lead.whatsapp_link, "Olá! Preparei uma proposta comercial da FLP Systems para " + proposta.cliente + ". Seguem as condições para sua avaliação.")
    } catch (e) { toast.error(e instanceof Error ? e.message : "Falha ao abrir WhatsApp.") }
  }
  const campos: { chave: keyof Proposta; titulo: string; longo?: boolean; numero?: boolean }[] = [
    { chave: "cliente", titulo: "Cliente" }, { chave: "servicos", titulo: "Serviços e entregáveis", longo: true },
    { chave: "inicial", titulo: "Valor inicial (R$)", numero: true }, { chave: "mensal", titulo: "Mensalidade (R$)", numero: true },
    { chave: "prazo", titulo: "Prazo de entrega" }, { chave: "pagamento", titulo: "Condições de pagamento", longo: true },
    { chave: "validade", titulo: "Validade" }, { chave: "observacoes", titulo: "Observações", longo: true },
  ]
  return (
    <section className="space-y-3 rounded-xl border border-border bg-card p-3">
      <h3 className="font-semibold">Ferramentas comerciais</h3>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant={aba === "demo" ? "default" : "outline"} disabled={ocupado} onClick={() => setAba(aba === "demo" ? null : "demo")}>Criar demonstração</Button>
        <Button size="sm" variant={aba === "proposta" ? "default" : "outline"} disabled={ocupado} onClick={() => setAba(aba === "proposta" ? null : "proposta")}>Gerar proposta comercial</Button>
      </div>
      {aba === "demo" && <div className="space-y-3">
        <p className="text-xs text-muted-foreground">Reúne os dados cadastrados e tenta consultar o conteúdo público do site atual. Complete identidade e serviços não confirmados; não cria nem publica o site automaticamente.</p>
        <label className="block text-sm">Identidade visual (cores, logo, estilo)
          <Textarea value={identidade} maxLength={4000} onChange={e => setIdentidade(e.target.value)} placeholder="Opcional: informações confirmadas da marca" />
        </label>
        <label className="block text-sm">Serviços confirmados
          <Textarea value={servicos} maxLength={4000} onChange={e => setServicos(e.target.value)} />
        </label>
        <label className="block text-sm">Referências e fontes oficiais
          <Textarea value={referencias} maxLength={4000} onChange={e => setReferencias(e.target.value)} />
        </label>
        <Button size="sm" disabled={ocupado} onClick={gerarDemo}>{ocupado ? "Gerando..." : "Gerar briefing e prompt"}</Button>
        {demo && <div className="space-y-3">
          <p className="text-xs text-muted-foreground">{demo.provedor ? "IA: " + demo.provedor : "Modelo local"} · Revise fatos e materiais antes de usar.</p>
          <label className="block text-sm">Briefing
            <Textarea rows={6} value={demo.briefing} onChange={e => setDemo({ ...demo, briefing: e.target.value })} />
          </label>
          <Button size="sm" variant="outline" onClick={() => copiar(demo.briefing).then(() => toast.success("Briefing copiado.")).catch(() => toast.error("Não foi possível copiar."))}>Copiar briefing</Button>
          <label className="block text-sm">Prompt de desenvolvimento
            <Textarea rows={9} value={demo.prompt} onChange={e => setDemo({ ...demo, prompt: e.target.value })} />
          </label>
          <Button size="sm" variant="outline" onClick={() => copiar(demo.prompt).then(() => toast.success("Prompt copiado.")).catch(() => toast.error("Não foi possível copiar."))}>Copiar prompt</Button>
        </div>}
      </div>}
      {aba === "proposta" && <div className="space-y-3">
        <img src="/flp-systems-light.svg" alt="FLP Systems" className="h-10 max-w-full object-contain dark:hidden" />
        <img src="/flp-systems-dark.svg" alt="FLP Systems" className="hidden h-10 max-w-full object-contain dark:block" />
        <p className="text-xs text-muted-foreground">Valores sugeridos são editáveis. Confirme escopo, valores e prazos antes de enviar.</p>
        {campos.map(({ chave, titulo, longo, numero }) => <label className="block text-sm" key={chave}>{titulo}
          {longo ? <Textarea disabled={ocupado} value={proposta[chave]} onChange={e => atualizar(chave, e.target.value)} />
            : <Input disabled={ocupado} type={numero ? "number" : "text"} min={numero ? 0 : undefined} step={numero ? "0.01" : undefined} value={proposta[chave]} onChange={e => atualizar(chave, e.target.value)} />}
        </label>)}
        <Button size="sm" disabled={ocupado} onClick={baixarProposta}>{ocupado ? "Gerando..." : "Baixar proposta PDF"}</Button>
        <Button size="sm" variant="outline" disabled={!pdfBaixado || !lead.whatsapp_link || ocupado} onClick={enviarProposta}>Abrir WhatsApp para enviar</Button>
        <p className="text-xs text-muted-foreground">Anexe o PDF baixado manualmente. O aplicativo não envia mensagens nem arquivos sozinho.</p>
      </div>}
    </section>
  )
}
