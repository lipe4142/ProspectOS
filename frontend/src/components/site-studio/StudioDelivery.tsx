import { useState } from "react"
import { ArrowUpRight, Check, CircleCheck, Clipboard, Globe, MessageCircle, Send, Sparkles, TriangleAlert } from "lucide-react"
import { abrirWhatsappInstalado } from "@/services/tarefasService"
import type { Check as ChecklistItem, Model, Project, Summary } from "./studioApi"

export type ProjectAction = (path: string, body: Record<string, unknown>, loading: string, success: string) => Promise<boolean>

const generationModes = [
  { id: "generate", label: "Site completo", description: "Escreve o conteúdo de todas as seções do roteiro." },
  { id: "edit", label: "Revisar o site", description: "Aplica um pedido ao conteúdo, à estrutura ou ao visual." },
  { id: "section", label: "Refinar uma seção", description: "Edita o texto de uma seção escolhida." },
] as const

type GeneratorProps = {
  model: Model
  project: Project
  summary: Summary
  dirty: boolean
  busy: boolean
  selectedId: string
  onAction: ProjectAction
  onGenerated: () => void
}

export function StudioGenerator({ model, project, summary, dirty, busy, selectedId, onAction, onGenerated }: GeneratorProps) {
  const [mode, setMode] = useState<(typeof generationModes)[number]["id"]>("generate")
  const [input, setInput] = useState("")
  const [confirmed, setConfirmed] = useState(false)
  const [target, setTarget] = useState("")
  const chosen = model.sections.some((section) => section.id === target) ? target : selectedId
  const quotaReached = summary.requests_month >= 100

  async function generate() {
    const ok = await onAction("/ai", {
      mode,
      section_id: mode === "section" ? chosen : undefined,
      instruction: input.trim() || "Gere o conteúdo completo com base no briefing e no objetivo do projeto.",
      confirm_cost: true,
    }, mode === "section" ? "Refinando a seção…" : "Gerando conteúdo do site…", "Conteúdo da IA salvo no projeto.")
    if (ok) {
      setConfirmed(false)
      setInput("")
      onGenerated()
    }
  }

  return (
    <div className="studio-task-grid">
      <section className="studio-panel studio-task-panel" aria-labelledby="studio-generate-title">
        <div className="studio-panel-heading">
          <span className="studio-panel-icon" aria-hidden="true"><Sparkles /></span>
          <div>
            <h2 id="studio-generate-title">Gerar conteúdo com IA</h2>
            <p className="studio-muted">Escolha o que a IA deve escrever ou revisar.</p>
          </div>
        </div>
        <form className="studio-form" onSubmit={(event) => {
          event.preventDefault()
          if (!dirty && !busy && !quotaReached && confirmed && (mode === "generate" || input.trim())) void generate()
        }}>
          <fieldset className="studio-form" disabled={busy}>
            <div className="studio-generation-options" role="group" aria-label="O que gerar">
              {generationModes.map((option) => (
                <button type="button" className="studio-choice" key={option.id} aria-pressed={option.id === mode}
                  onClick={() => { setMode(option.id); setConfirmed(false) }}>
                  <strong>{option.label}</strong>
                  <span>{option.description}</span>
                </button>
              ))}
            </div>
            {mode === "section" && (
              <label>Seção
                <select className="studio-field" value={chosen} onChange={(event) => setTarget(event.target.value)}>
                  {model.sections.map((section) => <option key={section.id} value={section.id}>{section.title || summary.kind_labels[section.kind]}</option>)}
                </select>
              </label>
            )}
            <label>Instrução {mode === "generate" && <span className="studio-optional">Opcional</span>}
              <textarea className="studio-field" rows={4} maxLength={4000} value={input}
                required={mode !== "generate"} onChange={(event) => setInput(event.target.value)}
                placeholder={mode === "section" ? "Ex. Torne a abertura mais direta e convide para um orçamento." : "Ex. Use um tom acolhedor e destaque o atendimento residencial."} />
            </label>
            <label className="studio-check">
              <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
              <span>Autorizo o uso de IA e possíveis cobranças do provedor.</span>
            </label>
            <div className="studio-inline-actions">
              <button type="submit" className="studio-button studio-primary"
                disabled={dirty || quotaReached || !confirmed || (mode !== "generate" && !input.trim())}>
                <Sparkles aria-hidden="true" /> {mode === "generate" ? "Gerar site completo" : "Aplicar com IA"}
              </button>
              {dirty && <span className="studio-muted">Salve as alterações para gerar.</span>}
              {quotaReached && <span className="studio-muted">Limite mensal atingido.</span>}
            </div>
          </fieldset>
        </form>
      </section>
      <aside className="studio-panel studio-task-panel studio-task-aside" aria-label="Contexto da geração">
        <h2>Roteiro do projeto</h2>
        <dl className="studio-facts">
          <div><dt>Objetivo</dt><dd>{summary.goals[model.strategy.goal]}</dd></div>
          <div><dt>Estrutura</dt><dd>{summary.depths[model.strategy.depth]} · {model.sections.length} seções</dd></div>
          <div><dt>Operações no mês</dt><dd>{summary.requests_month} de 100</dd></div>
        </dl>
        <details className="studio-details" open={!!project.briefing}>
          <summary>Briefing usado na geração</summary>
          <p className="studio-briefing">{project.briefing || "Projeto criado sem briefing."}</p>
        </details>
        {project.provider && <p className="studio-muted">Última geração: {project.provider}.</p>}
      </aside>
    </div>
  )
}

type PublishProps = {
  project: Project
  model: Model
  checks: ChecklistItem[]
  checking: boolean
  reviewError: string
  dirty: boolean
  busy: boolean
  onAction: ProjectAction
  onTest: () => Promise<string | null>
  onFeedback: (message: string, error?: boolean) => void
}

export function StudioPublish({ project, model, checks, checking, reviewError, dirty, busy, onAction, onTest, onFeedback }: PublishProps) {
  const [reviewedRevision, setReviewedRevision] = useState<number | null>(null)
  const [connection, setConnection] = useState("")
  const reviewed = reviewedRevision === project.revision && !dirty
  const approved = project.status === "publicado"
  const phone = model.phone.replace(/\D/g, "")
  const whatsapp = phone.length === 10 || phone.length === 11 ? "55" + phone : phone

  async function copy(value: string, message: string) {
    try {
      await navigator.clipboard.writeText(value)
      onFeedback(message)
    } catch {
      onFeedback("Não foi possível copiar. Selecione e copie o link manualmente.", true)
    }
  }

  return (
    <div className="studio-task-grid">
      <section className="studio-panel studio-task-panel" aria-labelledby="studio-publish-title">
        <div className="studio-panel-heading">
          <span className="studio-panel-icon" aria-hidden="true"><Globe /></span>
          <div>
            <h2 id="studio-publish-title">Publicar site</h2>
            <p className="studio-muted">Disponibilize a demonstração pelo Cloudflare Pages.</p>
          </div>
        </div>
        <fieldset className="studio-form" disabled={busy}>
          <div className="studio-inline-actions">
            <button type="button" className="studio-button" onClick={async () => setConnection(await onTest() ?? "")}>
              Testar conexão
            </button>
            {connection && <span role="status" className="studio-success-text">{connection}</span>}
          </div>
          <label className="studio-check">
            <input type="checkbox" checked={reviewed} disabled={dirty}
              onChange={(event) => setReviewedRevision(event.target.checked ? project.revision : null)} />
            <span>Revisei o conteúdo e autorizo a publicação pública.</span>
          </label>
          <div className="studio-inline-actions">
            <button type="button" className="studio-button studio-primary" disabled={dirty || !reviewed}
              onClick={async () => {
                const ok = await onAction("/publish", { reviewed: true }, "Publicando site…", "Publicação confirmada.")
                if (ok) setReviewedRevision(null)
              }}>
              <ArrowUpRight aria-hidden="true" /> {project.url ? "Republicar site" : "Publicar site"}
            </button>
            {dirty && <span className="studio-muted">Salve as alterações para publicar.</span>}
          </div>
          {project.url && (
            <div className="studio-published">
              <a href={project.url} target="_blank" rel="noreferrer">{project.url} <ArrowUpRight aria-hidden="true" /></a>
              <div className="studio-inline-actions">
                <button type="button" className="studio-button" onClick={() => void copy(project.url || "", "Link copiado.")}>
                  <Clipboard aria-hidden="true" /> Copiar link
                </button>
                <button type="button" className="studio-button" onClick={() => void copy(
                  "Olá! Desenvolvi uma demonstração de um novo site para sua empresa, sem compromisso. Confira: " + project.url,
                  "Mensagem copiada. Revise e envie manualmente.",
                )}>Copiar mensagem</button>
                {model.phone && <button type="button" className="studio-button" onClick={() => {
                  if (whatsapp.length < 12 || whatsapp.length > 15) {
                    onFeedback("Confirme o número comercial em Ajustes do site.", true)
                    return
                  }
                  abrirWhatsappInstalado("https://wa.me/" + whatsapp,
                    "Olá! Desenvolvi uma demonstração de um novo site para sua empresa, sem compromisso. Confira: " + project.url)
                }}><MessageCircle aria-hidden="true" /> Abrir WhatsApp</button>}
                {project.lead_id && (
                  <button type="button" className="studio-button" disabled={dirty || !approved || !!project.sent_at}
                    onClick={() => {
                      if (window.confirm("A demonstração já foi enviada ao lead?")) {
                        void onAction("/sent", { confirmed: true }, "Registrando envio…", "Envio registrado no CRM.")
                      }
                    }}>
                    {project.sent_at ? <Check aria-hidden="true" /> : <Send aria-hidden="true" />}
                    {project.sent_at ? "Envio registrado" : "Registrar envio"}
                  </button>
                )}
              </div>
            </div>
          )}
        </fieldset>
      </section>

      <aside className="studio-panel studio-task-panel studio-task-aside" aria-label="Revisão do site">
        <h2>Revisão antes de publicar</h2>
        {checking && <p className="studio-muted" role="status">Verificando o modelo…</p>}
        {reviewError && <p className="studio-muted" role="status">{reviewError}</p>}
        {!checking && !reviewError && (
          <ul className="studio-checklist">
            {checks.map((check) => (
              <li key={check.id} data-passed={check.passed}>
                {check.passed ? <CircleCheck aria-label="Pronto" /> : <TriangleAlert aria-label="Revisar" />}
                <div><strong>{check.label}</strong>{check.hint && <p>{check.hint}</p>}</div>
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  )
}
