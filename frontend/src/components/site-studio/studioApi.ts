export type Options = Record<string, string>
export type Item = { title: string; body: string }
export type Section = {
  id: string
  kind: string
  title: string
  body: string
  eyebrow: string
  cta: string
  image: string
  image_alt: string
  variant: string
  items: Item[]
}

export type Theme = {
  primary: string
  background: string
  text: string
  font: string
  layout: string
  appearance: string
}

export type Model = {
  title: string
  description: string
  phone: string
  theme: Theme
  strategy: { goal: string; depth: string }
  sections: Section[]
}

export type ProjectRow = {
  id: string
  name: string
  lead_id: string | null
  template: string
  status: string
  url: string | null
  sent_at: string | null
  updated_at: string
}

export type Project = ProjectRow & {
  model: Model
  revision: number
  briefing: string
  provider: string | null
}

export type Summary = {
  projects: ProjectRow[]
  templates: Options
  template_palettes: Record<string, Theme>
  fonts: string[]
  kinds: string[]
  kind_labels: Options
  item_kinds: string[]
  kind_variants: Record<string, string[]>
  styles: Options
  variants: Options
  goals: Options
  depths: Options
  appearances: Options
  palettes: Record<string, Pick<Theme, "background" | "text">>
  requests_month: number
}

export type Version = { id: number; label: string; created_at: string }
export type Creation = {
  name: string
  lead_id: string
  briefing: string
  phone: string
  template: string
  goal: string
  depth: string
  appearance: string
}
export type Plan = {
  html: string
  template: string
  theme: Theme
  goal: string
  sections: Pick<Section, "id" | "title" | "kind">[]
}
export type Check = { id: string; label: string; passed: boolean; hint: string }
export type Result = { html: string; checks: Check[] }

export const studioStatuses: Options = {
  em_edicao: "Em edição",
  publicado: "Publicado",
  publicando: "Publicando",
  erro_publicacao: "Falha na publicação",
}

export const studioMessages = {
  fallback: "Ocorreu um erro no Estúdio. Tente novamente.",
  service: "Confira se o backend do FLP Prospect está atualizado e em execução.",
}

export async function studioApi<T>(path: string, method = "GET", body?: unknown, signal?: AbortSignal): Promise<T> {
  let response: Response
  try {
    response = await fetch("/api/studio" + path, {
      method,
      signal,
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new Error("Não foi possível conectar ao backend. " + studioMessages.service)
  }

  let data: unknown
  try {
    data = await response.json()
  } catch (error) {
    if (signal?.aborted) throw error
    throw new Error("Resposta inesperada da API (HTTP " + response.status + "). " + studioMessages.service)
  }
  if (!response.ok) {
    const detail = data && typeof data === "object" && "erro" in data && typeof data.erro === "string" ? data.erro : ""
    throw new Error(detail || "Falha na operação (HTTP " + response.status + ").")
  }
  return data as T
}

export function studioError(error: unknown, fallback = studioMessages.fallback) {
  return error instanceof Error ? error.message : fallback
}

export function studioDate(value: string, withTime = false) {
  const date = new Date(value.includes("T") ? value : value.replace(" ", "T") + "Z")
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    ...(withTime ? { timeStyle: "short" } : {}),
  }).format(date)
}
