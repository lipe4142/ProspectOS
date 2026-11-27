import { useEffect, useState } from "react"
import { ArrowRight, FileText, Globe, LayoutGrid, LayoutTemplate, Link2, Plus, Search } from "lucide-react"
import { StudioPreviewFrame } from "./StudioPreviewFrame"
import { studioApi, studioDate, studioError, studioStatuses } from "./studioApi"
import type { Creation, Plan, Summary } from "./studioApi"

type Props = {
  summary?: Summary
  loading: boolean
  loadError: string
  busy: boolean
  initial: { leadId: string; name: string; briefing: string }
  onCreate: (input: Creation) => void
  onOpen: (id: string) => void
  onRetry: () => void
}

const presets = [
  { id: "all", label: "Todos" },
  { id: "em_edicao", label: "Em edição" },
  { id: "publicado", label: "Publicados" },
]

function searchable(text: string) {
  return text.toLocaleLowerCase("pt-BR").normalize("NFD").replace(/\p{Diacritic}/gu, "")
}

export function StudioLibrary({ summary, loading, loadError, busy, initial, onCreate, onOpen, onRetry }: Props) {
  const [input, setInput] = useState<Creation>({
    name: initial.name,
    lead_id: initial.leadId,
    briefing: initial.briefing,
    phone: "",
    template: "auto",
    goal: "auto",
    depth: "full",
    appearance: "template",
  })
  const [plan, setPlan] = useState<Plan | null>(null)
  const [planError, setPlanError] = useState("")
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("all")
  const ready = !!summary

  useEffect(() => {
    if (!ready) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      void studioApi<Plan>("/plan", "POST", input, controller.signal).then((result) => {
        if (typeof result?.html !== "string" || !Array.isArray(result.sections)) {
          throw new Error("Não foi possível carregar a amostra do modelo.")
        }
        if (!controller.signal.aborted) {
          setPlan(result)
          setPlanError("")
        }
      }).catch((error) => {
        if (!controller.signal.aborted) setPlanError(studioError(error))
      })
    }, 350)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [ready, input])

  function update<K extends keyof Creation>(key: K, value: Creation[K]) {
    setInput((current) => ({ ...current, [key]: value }))
    setPlanError("")
  }

  const query = searchable(search.trim())
  const all = summary?.projects ?? []
  const projects = all.filter((project) => (status === "all" || project.status === status)
    && searchable(project.name + " " + (summary?.templates[project.template] ?? "")).includes(query))
  const published = all.filter((project) => project.status === "publicado").length

  return (
    <>
      <header className="studio-intro">
        <div className="studio-intro-copy">
          <span className="studio-hero-icon" aria-hidden="true"><Globe /></span>
          <h1>Estúdio de sites</h1>
          <p>Crie demonstrações para seus leads, revise cada seção e apresente o site da empresa.</p>
          <div className="studio-intro-metrics" aria-label="Resumo dos projetos">
            <span><strong>{summary ? all.length : "—"}</strong> {all.length === 1 ? "projeto" : "projetos"}</span>
            <span><strong>{summary ? published : "—"}</strong> {published === 1 ? "publicado" : "publicados"}</span>
          </div>
        </div>
        <div className="studio-sample">
          <div className="studio-sample-bar">
            <div className="studio-browser-dots" aria-hidden="true"><i /><i /><i /></div>
            <span>Amostra do modelo</span>
            <LayoutTemplate aria-hidden="true" />
          </div>
          <div className="studio-sample-content">
            {plan ? <StudioPreviewFrame html={plan.html} width={960} height={172} thumbnail />
              : <p className="studio-sample-placeholder">{planError || loadError || "Carregando amostra…"}</p>}
          </div>
          <div className="studio-sample-footer">
            {planError && plan ? <span role="status">{planError}</span> : (
              <>
                <span>{plan ? summary?.templates[plan.template] : "Modelo de site"}</span>
                {plan && <span>{plan.sections.length} seções · {summary?.goals[plan.goal]}</span>}
              </>
            )}
          </div>
        </div>
      </header>

      <div className="studio-home">
        <section className="studio-panel studio-creation" aria-labelledby="studio-create">
          <div className="studio-panel-heading">
            <span className="studio-panel-icon" aria-hidden="true"><Plus /></span>
            <div>
              <h2 id="studio-create">Novo projeto</h2>
              <p className="studio-muted">Defina como o site deve começar.</p>
            </div>
          </div>
          <form className="studio-form" onSubmit={(event) => {
            event.preventDefault()
            if (!busy && ready && (input.name.trim() || input.lead_id.trim())) onCreate(input)
          }}>
            <fieldset className="studio-form" disabled={busy || !ready}>
              <label>Nome da empresa
                <input autoComplete="organization" className="studio-field" value={input.name} maxLength={160}
                  onChange={(event) => update("name", event.target.value)}
                  placeholder={input.lead_id.trim() ? "Usar o nome do lead vinculado" : "Ex. Lima Arquitetura"}
                  required={!input.lead_id.trim()} />
              </label>
              <div className="studio-form-row">
                <label>Modelo
                  <select className="studio-field" value={input.template} onChange={(event) => update("template", event.target.value)}>
                    <option value="auto">Detectar pelo segmento</option>
                    {Object.entries(summary?.templates ?? {}).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                  </select>
                </label>
                <label>Objetivo
                  <select className="studio-field" value={input.goal} onChange={(event) => update("goal", event.target.value)}>
                    <option value="auto">Sugerido pelo modelo</option>
                    {Object.entries(summary?.goals ?? {}).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                  </select>
                </label>
              </div>
              <div className="studio-form-row">
                <label>Estrutura
                  <select className="studio-field" value={input.depth} onChange={(event) => update("depth", event.target.value)}>
                    {Object.entries(summary?.depths ?? {}).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                  </select>
                </label>
                <label>Aparência do site
                  <select className="studio-field" value={input.appearance} onChange={(event) => update("appearance", event.target.value)}>
                    {Object.entries(summary?.appearances ?? {}).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                  </select>
                </label>
              </div>
              <label>Briefing <span className="studio-optional">Opcional</span>
                <textarea className="studio-field" rows={3} value={input.briefing} maxLength={20000}
                  onChange={(event) => update("briefing", event.target.value)}
                  placeholder="Ex. Sobre: escritório de interiores. Serviços: projetos residenciais; consultoria." />
              </label>
              <details className="studio-details">
                <summary><Link2 aria-hidden="true" /> {input.lead_id ? "Lead vinculado e WhatsApp" : "Vincular lead ou adicionar WhatsApp"}</summary>
                <div className="studio-form">
                  <label>ID do lead no CRM
                    <input className="studio-field" value={input.lead_id} maxLength={500}
                      onChange={(event) => update("lead_id", event.target.value)} placeholder="Opcional com nome da empresa" />
                  </label>
                  <label>WhatsApp comercial
                    <input type="tel" className="studio-field" value={input.phone} maxLength={40}
                      onChange={(event) => update("phone", event.target.value)} placeholder="DDD e número" />
                  </label>
                </div>
              </details>
              <button className="studio-button studio-primary studio-create-submit"
                disabled={!input.name.trim() && !input.lead_id.trim()} type="submit">
                Criar projeto <ArrowRight aria-hidden="true" />
              </button>
            </fieldset>
          </form>
        </section>

        <section className="studio-panel studio-library" aria-labelledby="studio-library">
          <div className="studio-panel-heading">
            <span className="studio-panel-icon" aria-hidden="true"><LayoutGrid /></span>
            <div>
              <h2 id="studio-library">Meus projetos</h2>
              <p className="studio-muted">Abra um projeto para continuar a edição.</p>
            </div>
          </div>
          <div className="studio-library-tools">
            <label className="studio-search">
              <Search aria-hidden="true" />
              <span className="sr-only">Buscar projetos</span>
              <input type="search" className="studio-field" value={search} onChange={(event) => setSearch(event.target.value)}
                placeholder="Buscar por nome ou modelo" disabled={!ready} />
            </label>
            <div className="studio-segmented" role="group" aria-label="Filtrar projetos por status">
              {presets.map((preset) => <button className="studio-tab" type="button" key={preset.id} disabled={!ready}
                aria-pressed={status === preset.id} onClick={() => setStatus(preset.id)}>{preset.label}</button>)}
            </div>
          </div>
          {loading && <p className="studio-empty" role="status">Carregando projetos…</p>}
          {loadError && (
            <div className="studio-empty" role="alert">
              <p>{loadError}</p>
              <button type="button" className="studio-button" onClick={onRetry}>Tentar novamente</button>
            </div>
          )}
          {ready && !projects.length && (
            <div className="studio-empty studio-library-empty">
              <span className="studio-empty-icon" aria-hidden="true"><FileText /></span>
              <div>
                <strong>{search || status !== "all" ? "Nenhum projeto encontrado" : "Você ainda não tem projetos"}</strong>
                <p>{search || status !== "all" ? "Altere a busca ou o filtro." : "Crie um projeto para editar e pré-visualizar o site."}</p>
              </div>
            </div>
          )}
          <div className="studio-project-list">
            {projects.map((project) => (
              <button type="button" key={project.id} disabled={busy} className="studio-project-row" onClick={() => onOpen(project.id)}>
                <span className="studio-project-mark" style={{ "--project-color": summary?.template_palettes[project.template]?.primary } as React.CSSProperties}
                  aria-hidden="true"><LayoutTemplate /></span>
                <span className="studio-project-name">
                  <strong>{project.name}</strong>
                  <small>{summary?.templates[project.template] ?? project.template} · {studioDate(project.updated_at)}</small>
                </span>
                <span className="studio-badge" data-status={project.status}>{studioStatuses[project.status] ?? project.status}</span>
                <ArrowRight className="studio-project-arrow" aria-hidden="true" />
              </button>
            ))}
          </div>
        </section>
      </div>
    </>
  )
}
