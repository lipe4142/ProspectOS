import { useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { Header } from "@/components/layout/Header"

type Section = {kind:string; title:string; body:string; image:string}
type Model = {title:string; description:string; phone:string; theme:{primary:string;background:string;text:string;font:string;layout:string}; sections:Section[]}
type Project = {id:string; name:string; lead_id:string|null; template:string; status:string; url:string|null; model:Model; revision:number; briefing:string;provider:string|null}
type Summary = {projects:Omit<Project,"model"|"revision"|"briefing"|"provider">[];templates:Record<string,string>; fonts:string[];kinds:string[];requests_today:number}
type Version = {id:number;label:string;created_at:string}
async function api<T>(path:string,method="GET",body?:unknown):Promise<T>{
  const r=await fetch("/api/studio"+path,{method,headers:{"Content-Type":"application/json"},...(body===undefined?{}:{body:JSON.stringify(body)})})
  const data=await r.json()
  if(!r.ok) throw new Error(data.erro||"Falha na operação")
  return data as T
}
const field="w-full rounded-lg border border-white/15 bg-[#161616] p-2 text-sm text-white"
const button="rounded-lg border border-white/15 px-3 py-2 text-sm hover:bg-white/10 disabled:opacity-40"
const primary=button+" bg-[#ff6a00] text-black font-semibold hover:bg-orange-400"
const sectionNames:Record<string,string>={hero:"Abertura",about:"Sobre",services:"Serviços",gallery:"Galeria",faq:"Perguntas frequentes",contact:"Contato",cta:"Chamada para ação"}

export function SiteStudioPage(){
  const [params]=useSearchParams()
  const [leadId,setLeadId]=useState(params.get("lead")||"")
  const [name,setName]=useState("")
  const [briefing,setBriefing]=useState("")
  const [template,setTemplate]=useState("servicos")
  const [summary,setSummary]=useState<Summary|null>(null)
  const [project,setProject]=useState<Project|null>(null)
  const [draft,setDraft]=useState<Model|null>(null)
  const [versions,setVersions]=useState<Version[]>([])
  const [preview,setPreview]=useState("")
  const [width,setWidth]=useState(1440)
  const [selected,setSelected]=useState(0)
  const [drag,setDrag]=useState<number|null>(null)
  const [instruction,setInstruction]=useState("")
  const [busy,setBusy]=useState(false)
  const [notice,setNotice]=useState("")
  const [error,setError]=useState("")
  const [reviewed,setReviewed]=useState(false)
  const [cfStatus,setCfStatus]=useState("")
  const [showCode,setShowCode]=useState(false)
  const dirty=!!(project&&draft&&JSON.stringify(project.model)!==JSON.stringify(draft))
  const reload=async()=>setSummary(await api<Summary>("/projects"))
  const adopt=async(p:Project)=>{setProject(p);setDraft(p.model);setSelected(0);setReviewed(false);setVersions(await api<Version[]>("/projects/"+p.id+"/versions"));await reload()}
  const run=async(task:()=>Promise<void>)=>{setBusy(true);setError("");setNotice("");try{await task()}catch(e){setError(e instanceof Error?e.message:"Erro inesperado")}finally{setBusy(false)}}
  useEffect(()=>{void reload().catch(e=>setError(String(e)))},[])
  useEffect(()=>{
    if(!draft){setPreview("");return}
    let active=true
    const timer=window.setTimeout(()=>{void api<{html:string}>("/preview","POST",{model:draft}).then(r=>{if(active)setPreview(r.html)}).catch(e=>{if(active)setError(String(e))})},300)
    return()=>{active=false;window.clearTimeout(timer)}
  },[draft])
  useEffect(()=>{setReviewed(false)},[draft])
  const open=(id:string)=>{if(dirty&&!window.confirm("Descartar alterações não salvas?"))return;void run(async()=>adopt(await api<Project>("/projects/"+id)))}
  const save=async()=>{if(!project||!draft)return;await adopt(await api<Project>("/projects/"+project.id,"PUT",{revision:project.revision,model:draft}));setNotice("Projeto salvo.")}
  const changeSection=(patch:Partial<Section>)=>setDraft(d=>d?{...d,sections:d.sections.map((s,i)=>i===selected?{...s,...patch}:s)}:d)
  const move=(from:number,to:number)=>{if(!draft||to<0||to>=draft.sections.length)return;const list=[...draft.sections];const item=list.splice(from,1)[0];if(!item)return;list.splice(to,0,item);setDraft({...draft,sections:list});setSelected(to)}
  const theme=(key:keyof Model["theme"],value:string)=>setDraft(d=>d?{...d,theme:{...d.theme,[key]:value}}:d)
  const action=async(path:string,body?:unknown)=>{if(!project)return;if(dirty)throw new Error("Salve as alterações antes de continuar.");await adopt(await api<Project>("/projects/"+project.id+path,"POST",body??{}))}
  const s=draft?.sections[selected]
  return <div className="min-h-screen bg-background text-foreground"><Header/><main className="min-h-[90vh] bg-[#090909] p-4 text-white lg:p-6">
    <div className="mx-auto max-w-[1800px] space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.25em] text-[#ff6a00]">FLP Systems / Desenvolvimento</p><h1 className="mt-1 text-3xl font-bold">Site Studio</h1><p className="text-sm text-zinc-400">Crie, personalize e exporte demonstrações profissionais.</p></div><button className={button} onClick={()=>{if(!dirty||window.confirm("Descartar alterações?")){setProject(null);setDraft(null)}}}>Meus projetos</button></div>
      {error&&<div role="alert" className="rounded-lg border border-red-500/50 bg-red-950/50 p-3 text-sm">{error}</div>}
      {notice&&<div role="status" className="rounded-lg border border-green-500/50 p-3 text-sm">{notice}</div>}
      {!project?<><div className="grid gap-3 sm:grid-cols-3">{[["Projetos",summary?.projects.length??0],["Publicados",summary?.projects.filter(p=>p.status==="publicado").length??0],["Operações IA hoje",summary?.requests_today??0]].map(([label,value])=><div key={label} className="rounded-xl border border-white/10 bg-[#141414] p-5"><p className="text-zinc-400">{label}</p><strong className="text-3xl">{value}</strong></div>)}</div>
      <div className="grid gap-5 lg:grid-cols-2"><section className="space-y-3 rounded-xl border border-white/10 bg-[#141414] p-5"><h2 className="text-xl font-bold">Novo projeto</h2><label className="block text-sm">Empresa<input className={field} value={name} onChange={e=>setName(e.target.value)} placeholder="Nome da empresa (opcional com lead)"/></label><label className="block text-sm">Lead vinculado<input className={field} value={leadId} onChange={e=>setLeadId(e.target.value)} placeholder="ID do lead, preenchido pelo CRM"/></label><label className="block text-sm">Template<select className={field} value={template} onChange={e=>setTemplate(e.target.value)}>{Object.entries(summary?.templates??{}).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label><label className="block text-sm">Briefing confirmado<textarea className={field} rows={5} value={briefing} onChange={e=>setBriefing(e.target.value)} placeholder="Cole seu briefing existente ou use os dados cadastrados do lead."/></label><button disabled={busy||(!name&&!leadId)} className={primary} onClick={()=>void run(async()=>{await adopt(await api<Project>("/projects","POST",{name,lead_id:leadId,template,briefing}))})}>Criar projeto</button></section>
      <section className="space-y-3 rounded-xl border border-white/10 bg-[#141414] p-5"><h2 className="text-xl font-bold">Meus projetos</h2>{summary?.projects.map(p=><button className="block w-full rounded-lg border border-white/10 p-3 text-left hover:bg-white/10" key={p.id} onClick={()=>open(p.id)}><strong>{p.name}</strong><p className="text-xs text-zinc-400">{p.status} · {p.template}</p></button>)}{summary?.projects.length===0&&<p className="text-zinc-400">Nenhum projeto ainda.</p>}</section></div>
      </>:draft&&<><div className="flex flex-wrap items-center gap-2 rounded-xl border border-white/10 bg-[#141414] p-3"><strong className="mr-auto">{project.name} {dirty?"*":""}</strong>{[1440,1280,768,390].map(w=><button key={w} className={button+(width===w?" border-orange-500":"")} onClick={()=>setWidth(w)}>{w}px</button>)}<button className={button} onClick={()=>setShowCode(v=>!v)}>{showCode?"Prévia":"HTML"}</button><button className={primary} disabled={busy||!dirty} onClick={()=>void run(save)}>Salvar</button><a className={button} href={"/api/studio/projects/"+project.id+"/export"} onClick={e=>{if(dirty){e.preventDefault();setError("Salve antes de exportar.")}}}>Exportar ZIP</a></div>
      <div className="grid gap-3 xl:grid-cols-[250px_minmax(0,1fr)_300px]">
      <aside className="space-y-4 rounded-xl border border-white/10 bg-[#141414] p-4"><h2 className="font-bold">Estrutura</h2>{draft.sections.map((item,i)=><div key={i} draggable onDragStart={()=>setDrag(i)} onDragOver={e=>e.preventDefault()} onDrop={()=>{if(drag!==null)move(drag,i);setDrag(null)}} className={"flex items-center gap-1 rounded-lg border p-1 "+(i===selected?"border-orange-500":"border-white/10")}><button className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap p-2 text-left text-sm" onClick={()=>setSelected(i)}>{sectionNames[item.kind]} · {item.title}</button><button aria-label="Mover para cima" onClick={()=>move(i,i-1)}>↑</button><button aria-label="Mover para baixo" onClick={()=>move(i,i+1)}>↓</button></div>)}
      <label className="block text-sm">Adicionar componente<select className={field} value="" onChange={e=>{if(e.target.value&&draft.sections.length<20){setDraft({...draft,sections:[...draft.sections,{kind:e.target.value,title:sectionNames[e.target.value],body:"",image:""}]});setSelected(draft.sections.length)}}}><option value="">Selecionar</option>{summary?.kinds.map(k=><option key={k} value={k}>{sectionNames[k]}</option>)}</select></label>
      <label className="block text-sm">Trocar template<select className={field} value={project.template} disabled={busy||dirty} onChange={e=>void run(()=>action("/template",{template:e.target.value}))}>{Object.entries(summary?.templates??{}).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
      <h3 className="font-semibold">Histórico</h3>{versions.map(v=><button key={v.id} className="block text-left text-xs text-zinc-300 hover:text-orange-400" disabled={busy||dirty} onClick={()=>{if(window.confirm("Restaurar esta versão?"))void run(()=>action("/restore/"+v.id))}}>{v.label} · {v.created_at}</button>)}</aside>
      <section className="min-w-0 overflow-auto rounded-xl border border-white/10 bg-[#252525] p-3">{showCode?<textarea readOnly value={preview} className="min-h-[650px] w-full bg-[#101010] p-4 font-mono text-xs text-green-300"/>:<div className="overflow-auto"><iframe title="Prévia isolada do site" sandbox="" referrerPolicy="no-referrer" srcDoc={preview} className="mx-auto block min-h-[680px] rounded-md bg-white" style={{width,maxWidth:"none",border:0}}/></div>}</section>
      <aside className="space-y-4 rounded-xl border border-white/10 bg-[#141414] p-4"><h2 className="font-bold">Propriedades</h2><label className="block text-sm">Nome do site<input className={field} value={draft.title} onChange={e=>setDraft({...draft,title:e.target.value})}/></label><label className="block text-sm">Descrição SEO<input className={field} value={draft.description} onChange={e=>setDraft({...draft,description:e.target.value})}/></label><label className="block text-sm">WhatsApp comercial confirmado<input className={field} value={draft.phone} onChange={e=>setDraft({...draft,phone:e.target.value})}/></label><div className="grid grid-cols-3 gap-1">{(["primary","background","text"] as const).map((k,i)=><label key={k} className="text-xs">{["Destaque","Fundo","Texto"][i]}<input className="block h-8 w-full" type="color" value={draft.theme[k]} onChange={e=>theme(k,e.target.value)}/></label>)}</div><label className="block text-sm">Fonte<select className={field} value={draft.theme.font} onChange={e=>theme("font",e.target.value)}>{summary?.fonts.map(f=><option key={f}>{f}</option>)}</select></label>
      {s&&<div className="space-y-2 border-t border-white/10 pt-3"><h3 className="font-semibold">{sectionNames[s.kind]}</h3><input aria-label="Título da seção" className={field} value={s.title} onChange={e=>changeSection({title:e.target.value})}/><textarea aria-label="Texto da seção" className={field} rows={5} value={s.body} onChange={e=>changeSection({body:e.target.value})}/><label className="block text-xs">Imagem autorizada (até 1 MB)<input type="file" accept="image/png,image/jpeg,image/webp" className="w-full text-xs" onChange={e=>{const f=e.target.files?.[0];if(!f)return;if(f.size>1000000){setError("Imagem acima de 1 MB.");return}const reader=new FileReader();reader.onload=()=>{if(typeof reader.result==="string")changeSection({image:reader.result})};reader.readAsDataURL(f)}}/></label><button className={button} onClick={()=>changeSection({image:""})}>Remover imagem</button><button className={button} disabled={draft.sections.length<=1} onClick={()=>{setDraft({...draft,sections:draft.sections.filter((_,i)=>i!==selected)});setSelected(0)}}>Excluir seção</button></div>}
      </aside></div>
      <div className="grid gap-4 lg:grid-cols-2"><section className="space-y-2 rounded-xl border border-white/10 bg-[#141414] p-4"><h2 className="font-bold text-orange-400">Assistente de IA</h2><p className="text-xs text-zinc-400">Usa os provedores existentes. Limite de 10 operações/dia e 100/mês. O provedor poderá cobrar conforme sua conta.</p><textarea className={field} rows={3} value={instruction} onChange={e=>setInstruction(e.target.value)} placeholder="Crie um site completo com base no briefing ou altere uma seção."/><button className={primary} disabled={busy||dirty||!instruction.trim()} onClick={()=>{if(window.confirm("Autorizar esta operação de IA e eventual cobrança do provedor?"))void run(async()=>{await action("/ai",{instruction,confirm_cost:true});setInstruction("");setNotice("Alteração por IA salva.")})}}>{busy?"Processando…":"Aplicar com IA"}</button></section>
      <section className="space-y-2 rounded-xl border border-white/10 bg-[#141414] p-4"><h2 className="font-bold">Publicação Cloudflare Pages</h2><p className="text-xs text-zinc-400">Configure as credenciais no backend. Nenhum site é publicado sem revisão.</p><button className={button} disabled={busy} onClick={()=>void run(async()=>{const r=await api<{message:string}>("/cloudflare");setCfStatus(r.message)})}>Testar conexão</button><p className="text-xs">{cfStatus}</p><label className="flex gap-2 text-sm"><input type="checkbox" checked={reviewed} onChange={e=>setReviewed(e.target.checked)}/> Revisei o conteúdo e autorizo a publicação pública.</label><button className={primary} disabled={busy||dirty||!reviewed} onClick={()=>void run(async()=>{await action("/publish",{reviewed:true});setNotice("Publicação confirmada.")})}>{project.url?"Republicar":"Publicar"}</button>{project.url&&<div className="space-y-2"><a href={project.url} target="_blank" rel="noreferrer" className="block break-all text-orange-400 underline">{project.url}</a><button className={button} onClick={()=>void navigator.clipboard.writeText(project.url||"")}>Copiar link</button><button className={button} onClick={()=>{const msg="Olá! Desenvolvi uma demonstração de um novo site para sua empresa, sem compromisso. Confira: "+project.url;void navigator.clipboard.writeText(msg).then(()=>setNotice("Mensagem copiada. Revise e envie manualmente."))}}>Copiar mensagem comercial</button></div>}</section></div>
      </>}
      {busy&&<p role="status" className="text-sm text-orange-400">Processando operação…</p>}
    </div></main></div>
}
