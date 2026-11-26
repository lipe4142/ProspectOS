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
type Proposta = {
  cliente: string; projeto: string; objetivo: string; servicos: string; beneficios: string;
  etapas: string; inicial: string; mensal: string; prazo: string; pagamento: string; validade: string;
  recorrencia: string; responsabilidades: string; limites: string; observacoes: string
}

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
    cliente: lead.nome,
    projeto: "Desenvolvimento de site profissional",
    objetivo: "Fortalecer a presença digital da empresa, apresentar seus serviços com clareza e facilitar o contato de potenciais clientes.",
    servicos: [
      "• Design personalizado com a identidade visual da empresa.",
      "• Layout responsivo para celular, tablet e computador.",
      "• Apresentação institucional, serviços e canais de contato.",
      "• Integração com WhatsApp e otimização básica para mecanismos de busca.",
      "• Testes de navegação e publicação após aprovação.",
    ].join("\n"),
    beneficios: "Mais credibilidade digital, apresentação profissional dos serviços e uma jornada de contato mais simples para os visitantes.",
    etapas: "1. Briefing e coleta dos materiais.\n2. Criação do layout e desenvolvimento.\n3. Revisão, aprovação e ajustes previstos no escopo.\n4. Testes e publicação.",
    inicial: "0", mensal: "90", prazo: "7 dias após receber os materiais e aprovar o escopo",
    pagamento: "Valor inicial conforme acordado. Mensalidade com vencimento definido na contratação.",
    validade: "7 dias",
    recorrencia: "A definir na contratação: hospedagem, manutenção, suporte e atualizações previstas no plano.",
    responsabilidades: "O cliente fornece logomarca, textos, imagens autorizadas e informações comerciais, além de aprovar o conteúdo antes da publicação.",
    limites: "Domínio, serviços de terceiros, campanhas de tráfego pago e funcionalidades fora do escopo devem ser acordados separadamente.",
    observacoes: "",
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
  type Campo = { chave: keyof Proposta; titulo: string; longo?: boolean; numero?: boolean }
  const grupos: { titulo: string; campos: Campo[] }[] = [
    { titulo: "01 · Apresentação do projeto", campos: [
      { chave: "cliente", titulo: "Cliente" }, { chave: "projeto", titulo: "Nome do projeto" },
      { chave: "objetivo", titulo: "Objetivo personalizado", longo: true },
      { chave: "servicos", titulo: "Serviços e entregáveis", longo: true },
      { chave: "beneficios", titulo: "Benefícios esperados", longo: true },
      { chave: "etapas", titulo: "Etapas de desenvolvimento", longo: true },
    ] },
    { titulo: "02 · Investimento e condições", campos: [
      { chave: "inicial", titulo: "Valor inicial (R$)", numero: true },
      { chave: "mensal", titulo: "Mensalidade (R$)", numero: true },
      { chave: "prazo", titulo: "Prazo de entrega" },
      { chave: "pagamento", titulo: "Condições de pagamento", longo: true },
      { chave: "validade", titulo: "Validade da proposta" },
      { chave: "recorrencia", titulo: "O que a mensalidade contempla", longo: true },
      { chave: "responsabilidades", titulo: "Responsabilidades e materiais", longo: true },
      { chave: "limites", titulo: "Limites do escopo e custos adicionais", longo: true },
      { chave: "observacoes", titulo: "Observações", longo: true },
    ] },
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
        {grupos.map(grupo => <fieldset key={grupo.titulo} className="space-y-3 rounded-lg border border-border p-3">
          <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-primary">{grupo.titulo}</legend>
          {grupo.campos.map(({ chave, titulo, longo, numero }) => <label className="block space-y-1 text-sm" key={chave}>
            <span className="font-medium">{titulo}</span>
            {longo ? <Textarea rows={chave === "servicos" ? 6 : 3} maxLength={chave === "pagamento" ? 1500 : 4000} disabled={ocupado} value={proposta[chave]} onChange={e => atualizar(chave, e.target.value)} />
              : <Input disabled={ocupado} type={numero ? "number" : "text"} maxLength={numero ? undefined : 200} min={numero ? 0 : undefined} max={numero ? 10000000 : undefined} step={numero ? "0.01" : undefined} value={proposta[chave]} onChange={e => atualizar(chave, e.target.value)} />}
          </label>)}
        </fieldset>)}
        <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted p-3">
          <div><p className="text-xs text-muted-foreground">Investimento inicial</p><p className="text-lg font-semibold">{(Number(proposta.inicial) || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</p></div>
          <div><p className="text-xs text-muted-foreground">Mensalidade</p><p className="text-lg font-semibold text-primary">{(Number(proposta.mensal) || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</p></div>
        </div>
        <Button size="sm" disabled={ocupado} onClick={baixarProposta}>{ocupado ? "Gerando..." : "Baixar proposta PDF"}</Button>
        <Button size="sm" variant="outline" disabled={!pdfBaixado || !lead.whatsapp_link || ocupado} onClick={enviarProposta}>Abrir WhatsApp para enviar</Button>
        <p className="text-xs text-muted-foreground">Anexe o PDF baixado manualmente. O aplicativo não envia mensagens nem arquivos sozinho.</p>
      </div>}
    </section>
  )
}
