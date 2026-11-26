import { httpClient } from "@/services/httpClient"
import { ajustarSaudacao } from "@/lib/saudacao"
import type { TarefasHoje } from "@/types/tarefas"

export const tarefasService = {
  tarefasHoje: () => httpClient.get<TarefasHoje>("/api/tarefas-hoje"),
}

/** Link nativo: abre o WhatsApp instalado sem carregar WhatsApp Web. */
export function linkWhatsappComMensagem(
  whatsappLink: string,
  mensagem?: string | null
): string {
  const original = new URL(whatsappLink)
  const host = original.hostname.toLowerCase()
  const telefone = (host === "wa.me"
    ? original.pathname.slice(1)
    : original.searchParams.get("phone") ?? "").replace(/\D/g, "")
  if (!["wa.me", "api.whatsapp.com", "web.whatsapp.com"].includes(host) ||
      original.protocol !== "https:" || !/^\d{8,15}$/.test(telefone)) {
    throw new Error("Número de WhatsApp inválido.")
  }
  const texto = mensagem ? ajustarSaudacao(mensagem) : original.searchParams.get("text") ?? ""
  return `whatsapp://send?phone=${telefone}&text=${encodeURIComponent(texto)}`
}

/** No navegador, a navegação por protocolo externo preserva a aba da FLP.
 * No Electron, a janela solicitada é interceptada e encaminhada ao Windows. */
export function abrirWhatsappInstalado(whatsappLink: string, mensagem?: string | null) {
  const url = linkWhatsappComMensagem(whatsappLink, mensagem)
  if (window.prospectOS?.desktop) window.open(url, "_blank")
  else window.location.assign(url)
}
