import { useLayoutEffect, useRef, useState } from "react"

type Props = {
  html: string
  width: number
  height: number
  thumbnail?: boolean
}

export function StudioPreviewFrame({ html, width, height, thumbnail = false }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [available, setAvailable] = useState(0)
  const [documentUrl, setDocumentUrl] = useState("")
  useLayoutEffect(() => {
    const element = ref.current
    if (!element) return
    const measure = () => setAvailable(element.clientWidth)
    measure()
    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", measure)
      return () => window.removeEventListener("resize", measure)
    }
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  useLayoutEffect(() => {
    const url = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }))
    setDocumentUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [html])

  const scale = Math.min(1, available / width)
  return (
    <div ref={ref} className="studio-frame-size" aria-hidden={thumbnail || undefined}>
      {scale > 0 && documentUrl && (
        <div className="studio-frame" style={{ width: width * scale, height }}>
          <iframe
            title={thumbnail ? "Amostra do modelo" : "Prévia isolada do site"}
            sandbox=""
            referrerPolicy="no-referrer"
            src={documentUrl}
            tabIndex={thumbnail ? -1 : undefined}
            style={{ width, height: Math.ceil(height / scale), transform: "scale(" + scale + ")" }}
          />
        </div>
      )}
    </div>
  )
}
