import { Check, ScanSearch, ShieldCheck, ShieldAlert, X } from "lucide-react"
import type { Lead } from "@/types/lead"

interface RaioXSiteProps {
  checklist: NonNullable<Lead["site_checklist"]>
}

/** Raio-X do site do lead: o que a página realmente tem e o que falta -
 * extraído do HTML na busca, nada é chute. São os ganchos concretos da venda. */
export function RaioXSite({ checklist }: RaioXSiteProps) {
  const seguranca = checklist.seguranca
  const resumo = {
    https: "Conexão protegida (HTTPS)",
    http: "Conexão não segura (HTTP)",
    http_com_https: "HTTPS disponível, mas o link HTTP não redireciona",
    certificado_invalido: "Conexão com problema no certificado",
    misto: "HTTPS com recursos não protegidos",
    indeterminada: "Segurança não confirmada",
  } as const
  return (
    <div className="space-y-2 rounded-xl border border-border bg-card p-4">
      <h3 className="flex items-center gap-1.5 text-sm font-semibold">
        <ScanSearch className="size-4 text-primary" />
        Raio-X do site atual
      </h3>
      {seguranca && (
        <div className="space-y-1 rounded-lg border border-border p-3 text-xs">
          <p className={seguranca === "https" ? "flex items-center gap-2 font-semibold text-success" : "flex items-center gap-2 font-semibold text-warning"}>
            {seguranca === "https" ? <ShieldCheck className="size-4" /> : <ShieldAlert className="size-4" />}
            {resumo[seguranca]}
          </p>
          <p className="text-muted-foreground">A verificação avalia a proteção da conexão, não a segurança completa do site.</p>
          {checklist.tipo_endereco && (
            <p>{checklist.tipo_endereco === "plataforma" ? "Endereço hospedado em plataforma de terceiros" : "Domínio personalizado aparente (titularidade não verificada)"}</p>
          )}
          {checklist.url_final && <p className="break-all text-muted-foreground">Destino: {checklist.url_final}</p>}
        </div>
      )}
      {checklist.resumo_ia && (
        <div className="rounded-lg bg-muted/40 p-3 text-xs">
          <p className="mb-1 font-semibold">Resumo da IA</p>
          <p>{checklist.resumo_ia}</p>
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-success">
            Já tem
          </p>
          {checklist.tem.length === 0 ? (
            <p className="text-xs text-muted-foreground">nada detectado</p>
          ) : (
            <ul className="space-y-1">
              {checklist.tem.map((item) => (
                <li key={item} className="flex items-start gap-1.5 text-xs">
                  <Check className="mt-0.5 size-3 shrink-0 text-success" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-warning">
            Está faltando
          </p>
          {checklist.falta.length === 0 ? (
            <p className="text-xs text-muted-foreground">nenhuma falta detectada</p>
          ) : (
            <ul className="space-y-1">
              {checklist.falta.map((item) => (
                <li key={item} className="flex items-start gap-1.5 text-xs">
                  <X className="mt-0.5 size-3 shrink-0 text-warning" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
