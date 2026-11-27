import { useEffect, useRef, useState } from "react"
import {
  ArrowDown, ArrowLeft, ArrowUp, CodeXml, Download, Eye, Globe, GripVertical, History,
  Laptop, Layers3, Monitor, PanelTop, Plus, Save, Settings2, Smartphone, Sparkles, Tablet,
} from "lucide-react"
import { StudioGenerator, StudioPublish } from "./StudioDelivery"
import type { ProjectAction } from "./StudioDelivery"
import { StudioPreviewFrame } from "./StudioPreviewFrame"
import { StudioProperties } from "./StudioProperties"
import { studioApi, studioDate, studioError, studioStatuses } from "./studioApi"
import type { Model, Project, Result, Summary, Version } from "./studioApi"

type Props = {
  project: Project
  model: Model
  summary: Summary
  versions: Version[]
  versionsError: string
  dirty: boolean
  busy: boolean
  onBack: () => void
  onSave: () => void
  onModelChange: (change: (model: Model) => Model) => void
  onAction: ProjectAction
  onTest: () => Promise<string | null>
  onFeedback: (message: string, error?: boolean) => void
}

const devices = [
  { width: 1440, label: "Desktop", icon: Monitor },
  { width: 1280, label: "Notebook", icon: Laptop },
  { width: 768, label: "Tablet", icon: Tablet },
  { width: 390, label: "Celular", icon: Smartphone },
] as const

const workspaceViews = [
  { key: "editor", label: "Editor", icon: PanelTop },
  { key: "generator", label: "Gerador", icon: Sparkles },
  { key: "publish", label: "Publicação", icon: Globe },
] as const

const compactViews = [
  { key: "outline", label: "Seções", icon: Layers3 },
  { key: "preview", label: "Prévia", icon: Eye },
  { key: "properties", label: "Ajustes", icon: Settings2 },
] as const

function useDocumentPreview(model: Model, source: boolean) {
  const [result, setResult] = useState<{ data: Result; model: Model; source: boolean } | null>(null)
  const [failure, setFailure] = useState<{ message: string; model: Model; source: boolean } | null>(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      void studioApi<Result>("/preview", "POST", { model, source }, controller.signal).then((data) => {
        if (typeof data?.html !== "string" || !Array.isArray(data.checks)) {
          throw new Error("O backend retornou uma prévia incompatível.")
        }
        if (!controller.signal.aborted) {
          setResult({ data, model, source })
          setFailure(null)
        }
      }).catch((error) => {
        if (!controller.signal.aborted) setFailure({ message: studioError(error), model, source })
      })
    }, 300)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [model, source, retry])

  const error = failure?.model === model && failure.source === source ? failure.message : ""
  return {
    html: result?.source === source ? result.data.html : "",
    checks: result?.model === model ? result.data.checks : [],
    waiting: !error && (result?.model !== model || result.source !== source),
    error,
    refresh: () => { setFailure(null); setRetry((value) => value + 1) },
  }
}

export function StudioWorkbench({
  project, model, summary, versions, versionsError, dirty, busy, onBack, onSave,
  onModelChange, onAction, onTest, onFeedback,
}: Props) {
  const [view, setView] = useState<(typeof workspaceViews)[number]["key"]>("editor")
  const [compact, setCompact] = useState<(typeof compactViews)[number]["key"]>("preview")
  const [inspector, setInspector] = useState<"section" | "site">("section")
  const [selectedId, setSelectedId] = useState(model.sections[0].id)
  const [device, setDevice] = useState<(typeof devices)[number]["width"]>(
    () => window.matchMedia("(max-width: 640px)").matches ? 390 : 1440,
  )
  const [source, setSource] = useState(false)
  const dragging = useRef<string | null>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const selected = model.sections.find((section) => section.id === selectedId) ?? model.sections[0]
  const preview = useDocumentPreview(model, view === "editor" && source)

  useEffect(() => {
    heading.current?.focus({ preventScroll: true })
    window.scrollTo(0, 0)
  }, [])

  function chooseSection(sectionId: string) {
    setSelectedId(sectionId)
    setInspector("section")
    setCompact("properties")
  }

  function move(id: string, offset: number) {
    onModelChange((current) => {
      const from = current.sections.findIndex((section) => section.id === id)
      const to = from + offset
      if (from < 0 || to < 0 || to >= current.sections.length || from === to) return current
      const sections = [...current.sections]
      const [section] = sections.splice(from, 1)
      sections.splice(to, 0, section)
      return { ...current, sections }
    })
  }

  function add(kind: string) {
    if (model.sections.length >= 20 || !kind) return
    let index = model.sections.length + 1
    while (model.sections.some((section) => section.id === "section-" + index)) index += 1
    const id = "section-" + index
    onModelChange((current) => ({
      ...current,
      sections: [...current.sections, { id, kind, title: summary.kind_labels[kind], body: "", eyebrow: "", cta: "",
        image: "", image_alt: "", variant: "auto", items: [] }],
    }))
    chooseSection(id)
  }

  function remove() {
    onModelChange((current) => current.sections.length <= 1 ? current : {
      ...current,
      sections: current.sections.filter((section) => section.id !== selected.id),
    })
  }

  return (
    <>
      <header className="studio-project-heading">
        <div className="studio-project-context">
          <button type="button" className="studio-back" disabled={busy} onClick={onBack}><ArrowLeft aria-hidden="true" /> Projetos</button>
          <div className="studio-project-title">
            <h1 ref={heading} tabIndex={-1}>{project.name}</h1>
            <span className="studio-badge" data-status={project.status}>{studioStatuses[project.status] ?? project.status}</span>
          </div>
          <p className="studio-muted">{summary.templates[project.template]} · Versão {project.revision}</p>
        </div>
        <div className="studio-project-actions">
          <span className="studio-save-state" data-dirty={dirty} role="status">{dirty ? "Alterações não salvas" : "Alterações salvas"}</span>
          <a className="studio-button" aria-disabled={dirty || busy}
            href={"/api/studio/projects/" + project.id + "/export"} onClick={(event) => {
              if (dirty || busy) {
                event.preventDefault()
                if (dirty) onFeedback("Salve as alterações antes de exportar.", true)
              }
            }}><Download aria-hidden="true" /> Exportar ZIP</a>
          <button type="button" className="studio-button studio-primary" disabled={busy || !dirty} onClick={onSave}>
            <Save aria-hidden="true" /> Salvar
          </button>
        </div>
      </header>
      <div className="studio-workspace-tabs" role="group" aria-label="Área do projeto">
        {workspaceViews.map(({ key, label, icon: Icon }) => (
          <button type="button" className="studio-workspace-tab" key={key} aria-pressed={view === key}
            disabled={busy} onClick={() => setView(key)}><Icon aria-hidden="true" /> {label}</button>
        ))}
      </div>

      {view === "editor" && (
        <>
          <div className="studio-segmented studio-compact-tabs" role="group" aria-label="Painel do editor">
            {compactViews.map(({ key, label, icon: Icon }) => (
              <button type="button" className="studio-tab" key={key} aria-pressed={compact === key}
                onClick={() => setCompact(key)}><Icon aria-hidden="true" /> {label}</button>
            ))}
          </div>
          <div className="studio-workbench" data-compact-pane={compact}>
            <aside className="studio-outline" aria-labelledby="studio-outline-title">
              <div className="studio-workbench-heading">
                <Layers3 aria-hidden="true" /><h2 id="studio-outline-title">Seções</h2><span>{model.sections.length}</span>
              </div>
              <div className="studio-outline-list">
                {model.sections.map((section, index) => (
                  <div key={section.id} className="studio-section-row" data-selected={section.id === selected.id}
                    onDragOver={(event) => { if (dragging.current && !busy) event.preventDefault() }}
                    onDrop={(event) => {
                      event.preventDefault()
                      if (dragging.current && !busy) {
                        const from = model.sections.findIndex((item) => item.id === dragging.current)
                        if (from >= 0) move(dragging.current, index - from)
                      }
                      dragging.current = null
                    }}>
                    <span className="studio-grip" draggable={!busy} aria-hidden="true"
                      onDragStart={(event) => {
                        event.dataTransfer.setData("text/plain", section.id)
                        event.dataTransfer.effectAllowed = "move"
                        dragging.current = section.id
                      }}
                      onDragEnd={() => { dragging.current = null }}><GripVertical /></span>
                    <button type="button" className="studio-section-select" onClick={() => chooseSection(section.id)}
                      aria-pressed={section.id === selected.id}>
                      <strong>{section.title || summary.kind_labels[section.kind]}</strong>
                      <small>{summary.kind_labels[section.kind]}</small>
                    </button>
                    <div className="studio-order">
                      <button type="button" className="studio-icon-button" disabled={busy || index === 0}
                        onClick={() => move(section.id, -1)} aria-label={"Subir seção " + (section.title || summary.kind_labels[section.kind])}>
                        <ArrowUp aria-hidden="true" />
                      </button>
                      <button type="button" className="studio-icon-button" disabled={busy || index === model.sections.length - 1}
                        onClick={() => move(section.id, 1)} aria-label={"Descer seção " + (section.title || summary.kind_labels[section.kind])}>
                        <ArrowDown aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <label className="studio-add-section"><Plus aria-hidden="true" /> <span>Adicionar seção</span>
                <select className="studio-field" value="" disabled={busy || model.sections.length >= 20}
                  onChange={(event) => add(event.target.value)}>
                  <option value="">Escolher um bloco</option>
                  {summary.kinds.map((kind) => <option key={kind} value={kind}>{summary.kind_labels[kind]}</option>)}
                </select>
              </label>
              <details className="studio-details">
                <summary><History aria-hidden="true" /> Modelo e versões</summary>
                <div className="studio-form">
                  <label>Aplicar visual de outro modelo
                    <select className="studio-field" value={project.template} disabled={busy || dirty} onChange={(event) => {
                      void onAction("/template", { template: event.target.value }, "Aplicando modelo…", "Visual do modelo aplicado.")
                    }}>
                      {Object.entries(summary.templates).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                    </select>
                  </label>
                  <h3>Histórico de versões</h3>
                  {versionsError ? <p className="studio-muted">{versionsError}</p>
                    : !versions.length && <p className="studio-muted">Sem versões anteriores.</p>}
                  {versions.map((version) => (
                    <button className="studio-version" type="button" key={version.id} disabled={busy || dirty}
                      onClick={() => {
                        if (window.confirm("Restaurar esta versão? A versão atual ficará no histórico.")) {
                          void onAction("/restore/" + version.id, {}, "Restaurando versão…", "Versão restaurada.")
                        }
                      }}><strong>{version.label}</strong><small>{studioDate(version.created_at, true)}</small></button>
                  ))}
                </div>
              </details>
            </aside>

            <section className="studio-preview" aria-label="Prévia do site">
              <div className="studio-preview-bar">
                <div className="studio-preview-heading">
                  {source ? <CodeXml aria-hidden="true" /> : <Eye aria-hidden="true" />}
                  <h2>{source ? "Código HTML" : "Prévia do site"}</h2>
                </div>
                <div className="studio-segmented studio-devices" role="group" aria-label="Largura da prévia">
                  {devices.map(({ width, label, icon: Icon }) => (
                    <button key={width} type="button" className="studio-tab" aria-label={label} aria-pressed={width === device}
                      disabled={source} title={label + " · " + width + " px"} onClick={() => setDevice(width)}>
                      <Icon aria-hidden="true" />
                    </button>
                  ))}
                </div>
                <button type="button" className="studio-icon-button studio-code-toggle" aria-label={source ? "Ver prévia" : "Ver HTML"}
                  title={source ? "Ver prévia" : "Ver HTML"} onClick={() => setSource((value) => !value)} aria-pressed={source}>
                  {source ? <Eye aria-hidden="true" /> : <CodeXml aria-hidden="true" />}
                </button>
              </div>
              {preview.error && <div className="studio-preview-error" role="alert">
                <span>{preview.error}{preview.html ? " A última prévia pode estar desatualizada." : ""}</span>
                <button className="studio-button" type="button" onClick={preview.refresh}>Tentar novamente</button>
              </div>}
              <div className="studio-stage" aria-busy={preview.waiting}>
                {source ? (
                  <textarea readOnly aria-label="HTML gerado para exportação" className="studio-code" value={preview.html}
                    placeholder={preview.waiting ? "Carregando HTML…" : ""} spellCheck={false} />
                ) : preview.html ? <StudioPreviewFrame html={preview.html} width={device} height={610} />
                  : <p className="studio-empty" role="status">{preview.waiting ? "Preparando a prévia…" : "Prévia indisponível."}</p>}
              </div>
              <div className="studio-preview-footer">
                <span>{source ? "Somente leitura" : device + " px"}</span>
                {preview.waiting && preview.html && <span role="status">Atualizando…</span>}
              </div>
            </section>

            <aside className="studio-inspector" aria-label="Ajustes do editor">
              <div className="studio-workbench-heading"><Settings2 aria-hidden="true" /><h2>Ajustes</h2></div>
              <div className="studio-segmented" role="group" aria-label="Ajustes da prévia">
                <button type="button" className="studio-tab" aria-pressed={inspector === "section"} onClick={() => setInspector("section")}>Seção</button>
                <button type="button" className="studio-tab" aria-pressed={inspector === "site"} onClick={() => setInspector("site")}>Site e tema</button>
              </div>
              <StudioProperties model={model} section={selected} project={project} summary={summary}
                kind={inspector} busy={busy} onModelChange={onModelChange} onRemove={remove}
                onError={(message) => onFeedback(message, true)} />
            </aside>
          </div>
        </>
      )}
      {view === "generator" && (
        <StudioGenerator model={model} project={project} summary={summary} dirty={dirty} busy={busy} selectedId={selected.id}
          onAction={onAction} onGenerated={() => { setView("editor"); setCompact("preview"); setSource(false) }} />
      )}
      {view === "publish" && (
        <StudioPublish project={project} model={model} checks={preview.checks} checking={preview.waiting} reviewError={preview.error}
          dirty={dirty} busy={busy} onAction={onAction} onTest={onTest} onFeedback={onFeedback} />
      )}
    </>
  )
}
