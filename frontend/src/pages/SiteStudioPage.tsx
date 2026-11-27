import { useEffect, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useLocation, useSearchParams } from "react-router-dom"
import { CircleCheck, LoaderCircle, TriangleAlert, X } from "lucide-react"
import { Header } from "@/components/layout/Header"
import { StudioLibrary } from "@/components/site-studio/StudioLibrary"
import { StudioWorkbench } from "@/components/site-studio/StudioWorkbench"
import { studioApi, studioError, studioMessages } from "@/components/site-studio/studioApi"
import type { Creation, Model, Project, Summary, Version } from "@/components/site-studio/studioApi"
import "./SiteStudioPage.css"

type Feedback = { message: string; error: boolean }
const summaryKey = ["site-studio-projects"] as const

async function fetchSummary(signal: AbortSignal) {
  const data = await studioApi<Summary>("/projects", "GET", undefined, signal)
  if (!Array.isArray(data?.projects) || !data?.template_palettes || !data?.kind_variants
      || !data?.appearances || !Number.isInteger(data?.requests_month)) {
    throw new Error("Versão incompatível da API do Estúdio. " + studioMessages.service)
  }
  return data
}

export default function SiteStudioPage() {
  const [params] = useSearchParams()
  const location = useLocation()
  const imported = location.state as { name?: string; briefing?: string } | null
  const queryClient = useQueryClient()
  const [project, setProject] = useState<Project | null>(null)
  const [draft, setDraft] = useState<Model | null>(null)
  const [operation, setOperation] = useState("")
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const inFlight = useRef(false)
  const summary = useQuery({ queryKey: summaryKey, queryFn: ({ signal }) => fetchSummary(signal) })
  const projectId = project?.id
  const revision = project?.revision
  const versions = useQuery({
    queryKey: ["site-studio-versions", projectId, revision],
    queryFn: ({ signal }) => studioApi<Version[]>("/projects/" + projectId + "/versions", "GET", undefined, signal),
    enabled: !!projectId,
  })
  const busy = operation !== ""
  const dirty = !!project && draft !== project.model

  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener("beforeunload", warn)
    return () => window.removeEventListener("beforeunload", warn)
  }, [dirty])

  function report(message: string, error = false) {
    setFeedback({ message, error })
  }

  async function run(label: string, task: () => Promise<void>) {
    if (inFlight.current) return false
    inFlight.current = true
    setOperation(label)
    setFeedback(null)
    try {
      await task()
      return true
    } catch (error) {
      report(studioError(error), true)
      return false
    } finally {
      inFlight.current = false
      setOperation("")
    }
  }

  function adopt(next: Project) {
    setProject(next)
    setDraft(next.model)
  }

  function refreshList() {
    void queryClient.invalidateQueries({ queryKey: summaryKey })
  }

  function create(input: Creation) {
    void run("Criando projeto…", async () => {
      adopt(await studioApi<Project>("/projects", "POST", { ...input, name: input.name.trim(), lead_id: input.lead_id.trim() }))
      refreshList()
    })
  }

  function open(id: string) {
    void run("Abrindo projeto…", async () => {
      adopt(await studioApi<Project>("/projects/" + id))
    })
  }

  function close() {
    if (dirty && !window.confirm("Voltar aos projetos e descartar as alterações não salvas?")) return
    setFeedback(null)
    setProject(null)
    setDraft(null)
    window.scrollTo(0, 0)
  }

  function save() {
    if (!project || !draft || !dirty) return
    void run("Salvando projeto…", async () => {
      adopt(await studioApi<Project>("/projects/" + project.id, "PUT", { revision: project.revision, model: draft }))
      refreshList()
      report("Projeto salvo.")
    })
  }

  async function projectAction(path: string, body: Record<string, unknown>, progress: string, success: string) {
    if (!project || dirty) return false
    return run(progress, async () => {
      try {
        adopt(await studioApi<Project>("/projects/" + project.id + path, "POST", { ...body, revision: project.revision }))
        report(success)
      } finally {
        refreshList()
        if (path === "/publish") void versions.refetch()
      }
    })
  }

  async function testConnection() {
    let message: string | null = null
    await run("Testando conexão…", async () => {
      message = (await studioApi<{ message: string }>("/cloudflare")).message
    })
    return message
  }

  return (
    <div className="studio-page min-h-screen bg-background text-foreground">
      <Header />
      <main className="studio">
        <div className="studio-shell">
          {feedback && (
            <div className="studio-message" data-error={feedback.error} role={feedback.error ? "alert" : "status"}>
              {feedback.error ? <TriangleAlert aria-hidden="true" /> : <CircleCheck aria-hidden="true" />}
              <span>{feedback.message}</span>
              <button type="button" className="studio-icon-button" onClick={() => setFeedback(null)} aria-label="Fechar aviso"><X aria-hidden="true" /></button>
            </div>
          )}
          {busy && <div className="studio-progress" role="status"><LoaderCircle aria-hidden="true" /> {operation}</div>}
          {project && draft && summary.data ? (
            <StudioWorkbench key={project.id} project={project} model={draft} summary={summary.data}
              versions={versions.data ?? []} versionsError={versions.error ? studioError(versions.error) : ""}
              dirty={dirty} busy={busy} onBack={close} onSave={save} onAction={projectAction}
              onModelChange={(change) => setDraft((current) => current ? change(current) : current)}
              onTest={testConnection} onFeedback={report} />
          ) : (
            <StudioLibrary key={location.key} summary={summary.data} loading={summary.isPending} busy={busy}
              initial={{ leadId: params.get("lead") || "", name: imported?.name || "", briefing: imported?.briefing || "" }}
              loadError={summary.error && !summary.data ? studioError(summary.error) : ""}
              onCreate={create} onOpen={open} onRetry={() => { void summary.refetch() }} />
          )}
        </div>
      </main>
    </div>
  )
}
