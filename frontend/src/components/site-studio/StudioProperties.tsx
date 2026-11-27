import { useEffect, useRef } from "react"
import { Image, Plus, Trash2, X } from "lucide-react"
import type { Item, Model, Project, Section, Summary, Theme } from "./studioApi"

type Props = {
  model: Model
  section: Section
  project: Project
  summary: Summary
  kind: "section" | "site"
  busy: boolean
  onModelChange: (change: (model: Model) => Model) => void
  onRemove: () => void
  onError: (error: string) => void
}

const colors = [
  { key: "primary", label: "Destaque" },
  { key: "background", label: "Fundo" },
  { key: "text", label: "Texto" },
] as const

export function StudioProperties({ model, section, project, summary, kind, busy, onModelChange, onRemove, onError }: Props) {
  const reader = useRef<FileReader | null>(null)

  useEffect(() => () => reader.current?.abort(), [])

  function update(sectionId: string, patch: Partial<Section>) {
    onModelChange((current) => ({
      ...current,
      sections: current.sections.map((item) => item.id === sectionId ? { ...item, ...patch } : item),
    }))
  }

  function theme(patch: Partial<Theme>) {
    onModelChange((current) => ({ ...current, theme: { ...current.theme, ...patch } }))
  }

  function updateItem(index: number, patch: Partial<Item>) {
    update(section.id, { items: section.items.map((item, position) => position === index ? { ...item, ...patch } : item) })
  }

  function upload(file: File) {
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 1_000_000) {
      onError("Use um arquivo PNG, JPEG ou WebP de até 1 MB.")
      return
    }
    reader.current?.abort()
    const uploadReader = new FileReader()
    reader.current = uploadReader
    uploadReader.onload = () => {
      if (typeof uploadReader.result === "string") update(section.id, { image: uploadReader.result, image_alt: "" })
    }
    uploadReader.onerror = () => onError("Não foi possível ler a imagem.")
    uploadReader.readAsDataURL(file)
  }

  if (kind === "site") {
    return (
      <fieldset className="studio-form" disabled={busy}>
        <label>Nome do site
          <input className="studio-field" value={model.title} maxLength={160}
            onChange={(event) => onModelChange((current) => ({ ...current, title: event.target.value }))} />
        </label>
        <label>Descrição SEO
          <textarea className="studio-field" rows={3} value={model.description} maxLength={300}
            onChange={(event) => onModelChange((current) => ({ ...current, description: event.target.value }))} />
        </label>
        <label>WhatsApp comercial
          <input className="studio-field" type="tel" value={model.phone} maxLength={40} placeholder="DDD e número"
            onChange={(event) => onModelChange((current) => ({ ...current, phone: event.target.value }))} />
        </label>
        <label>Tema do site gerado
          <select className="studio-field" value={model.theme.appearance} onChange={(event) => {
            const key = event.target.value
            const palette = key === "template" ? summary.template_palettes[project.template] : summary.palettes[key]
            if (palette) theme({ background: palette.background, text: palette.text, appearance: key })
          }}>
            {model.theme.appearance === "custom" && <option value="custom" disabled>Personalizado</option>}
            {Object.entries(summary.appearances).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <div className="studio-colors">
          {colors.map(({ key, label }) => (
            <label key={key}>
              <span>{label}</span>
              <input type="color" value={model.theme[key]}
                onChange={(event) => theme({ [key]: event.target.value, ...(key !== "primary" ? { appearance: "custom" } : {}) })} />
              <small>{model.theme[key]}</small>
            </label>
          ))}
        </div>
        <label>Direção visual
          <select className="studio-field" value={model.theme.layout} onChange={(event) => theme({ layout: event.target.value })}>
            {Object.entries(summary.styles).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </label>
        <label>Fonte do corpo
          <select className="studio-field" value={model.theme.font} onChange={(event) => theme({ font: event.target.value })}>
            {summary.fonts.map((font) => <option key={font} value={font}>{font === "system-ui" ? "Do sistema" : font}</option>)}
          </select>
        </label>
      </fieldset>
    )
  }

  const isActionSection = ["hero", "contact", "cta"].includes(section.kind)
  const isFaq = section.kind === "faq"

  return (
    <fieldset className="studio-form" disabled={busy}>
      <p className="studio-section-kind">{summary.kind_labels[section.kind]}</p>
      <label>Título
        <input className="studio-field" value={section.title} maxLength={160}
          onChange={(event) => update(section.id, { title: event.target.value })} />
      </label>
      <label>Texto
        <textarea className="studio-field" rows={4} value={section.body} maxLength={4000}
          onChange={(event) => update(section.id, { body: event.target.value })} />
      </label>
      <label>Composição
        <select className="studio-field" value={section.variant} onChange={(event) => update(section.id, { variant: event.target.value })}>
          {summary.kind_variants[section.kind]?.map((key) => <option key={key} value={key}>{summary.variants[key]}</option>)}
        </select>
      </label>
      <details className="studio-details">
        <summary>Subtítulo e chamada</summary>
        <div className="studio-form">
          <label>Rótulo acima do título
            <input className="studio-field" value={section.eyebrow} maxLength={80}
              onChange={(event) => update(section.id, { eyebrow: event.target.value })} />
          </label>
          {isActionSection && <label>Texto do botão
            <input className="studio-field" value={section.cta} maxLength={64}
              onChange={(event) => update(section.id, { cta: event.target.value })} />
          </label>}
        </div>
      </details>
      {summary.item_kinds.includes(section.kind) && (
        <details className="studio-details">
          <summary>{isFaq ? "Perguntas e respostas" : "Itens da seção"} ({section.items.length})</summary>
          <div className="studio-form">
            {section.items.map((item, index) => (
              <div className="studio-content-item" key={index}>
                <div className="studio-item-top">
                  <strong>{isFaq ? "Pergunta" : "Item"} {index + 1}</strong>
                  <button className="studio-icon-button" type="button" aria-label={"Remover item " + (index + 1)}
                    onClick={() => update(section.id, { items: section.items.filter((_, position) => position !== index) })}>
                    <X aria-hidden="true" />
                  </button>
                </div>
                <label>{isFaq ? "Pergunta" : "Título do item"}
                  <input className="studio-field" value={item.title} maxLength={120}
                    onChange={(event) => updateItem(index, { title: event.target.value })} />
                </label>
                <label>{isFaq ? "Resposta" : "Descrição do item"}
                  <textarea className="studio-field" value={item.body} maxLength={500} rows={2}
                    onChange={(event) => updateItem(index, { body: event.target.value })} />
                </label>
              </div>
            ))}
            <button className="studio-button" type="button" disabled={section.items.length >= 8}
              onClick={() => update(section.id, { items: [...section.items, { title: "", body: "" }] })}>
              <Plus aria-hidden="true" /> {isFaq ? "Adicionar pergunta" : "Adicionar item"}
            </button>
          </div>
        </details>
      )}
      <details className="studio-details">
        <summary><Image aria-hidden="true" /> Imagem {section.image ? "adicionada" : ""}</summary>
        <div className="studio-form">
          <label>Imagem autorizada <span className="studio-optional">até 1 MB</span>
            <input type="file" className="studio-field studio-file" accept="image/png,image/jpeg,image/webp"
              onChange={(event) => {
                const file = event.target.files?.[0]
                if (file) upload(file)
                event.target.value = ""
              }} />
          </label>
          {section.image && <>
            <label>Texto alternativo
              <input className="studio-field" value={section.image_alt} maxLength={160}
                onChange={(event) => update(section.id, { image_alt: event.target.value })} />
            </label>
            <button className="studio-button" type="button" onClick={() => update(section.id, { image: "", image_alt: "" })}>
              Remover imagem
            </button>
          </>}
        </div>
      </details>
      <button type="button" className="studio-button studio-danger" disabled={model.sections.length <= 1} onClick={onRemove}>
        <Trash2 aria-hidden="true" /> Excluir seção
      </button>
    </fieldset>
  )
}
