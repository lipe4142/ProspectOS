import { useEffect, useRef, useState } from "react"
import { useLocation, useSearchParams } from "react-router-dom"
import "./SiteStudioPage.css"
import { Header } from "@/components/layout/Header"
import { abrirWhatsappInstalado } from "@/services/tarefasService"

type Section = {kind:string; title:string; body:string; image:string}
type Model = {title:string; description:string; phone:string; theme:{primary:string;background:string;text:string;font:string;layout:string}; sections:Section[]}
type Project = {id:string; name:string; lead_id:string|null; template:string; status:string; url:string|null; model:Model; revision:number; briefing:string;provider:string|null;sent_at:string|null}
type Summary = {projects:Omit<Project,"model"|"revision"|"briefing"|"provider">[];templates:Record<string,string>; fonts:string[];kinds:string[];requests_today:number}
type Version = {id:number;label:string;created_at:string}
async function api<T>(path:string,method="GET",body?:unknown):Promise<T>{
  let r:Response
  try {
    r=await fetch("/api/studio"+path,{method,headers:{"Accept":"application/json","Content-Type":"application/json"},...(body===undefined?{}:{body:JSON.stringify(body)})})
  } catch {
    throw new Error("Não foi possível conectar ao backend. Reinicie o FLP Prospect e tente novamente.")
  }
  const raw=await r.text()
  let data:unknown
  try { data=JSON.parse(raw) } catch {
    if(r.status===404) throw new Error("API do Site Studio não encontrada (404). Atualize e reinicie o backend do FLP Prospect.")
    if(r.status===502||r.status===503||r.status===504) throw new Error("Backend indisponível (HTTP "+r.status+"). Reinicie o FLP Prospect.")
    throw new Error("Resposta inesperada da API (HTTP "+r.status+"). Confira se o backend está atualizado e em execução.")
  }
  if(!r.ok){
    const detail=data&&typeof data==="object"&&"erro" in data&&typeof data.erro==="string"?data.erro:null
    throw new Error(detail||"Falha na operação (HTTP "+r.status+").")
  }
  return data as T
}
const field="studio-field"
const button="studio-button"
const primary="studio-button studio-primary"
const devices: {width:number; label:string}[]=[{width:1440,label:"Desktop"},{width:1280,label:"Notebook"},{width:768,label:"Tablet"},{width:390,label:"Celular"}]
const sectionNames:Record<string,string>={hero:"Abertura",about:"Sobre",services:"Serviços",gallery:"Galeria",faq:"Perguntas frequentes",contact:"Contato",cta:"Chamada para ação"}

export function SiteStudioPage(){
  const [params]=useSearchParams()
  const location=useLocation()
  const imported=location.state as {briefing?:string;name?:string}|null
  const [leadId,setLeadId]=useState(params.get("lead")||"")
  const [name,setName]=useState(imported?.name||"")
  const [briefing,setBriefing]=useState(imported?.briefing||"")
  const [template,setTemplate]=useState("servicos")
  const [summary,setSummary]=useState<Summary|null>(null)
  const [loadingProjects,setLoadingProjects]=useState(true)
  const [previewError,setPreviewError]=useState("")
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
  const [inspector,setInspector]=useState<"section"|"site">("section")
  const [filter,setFilter]=useState("")
  const [stageWidth,setStageWidth]=useState(0)
  const stageRef=useRef<HTMLDivElement>(null)
  const dirty=!!(project&&draft&&JSON.stringify(project.model)!==JSON.stringify(draft))
  const reload=async()=>{
    setLoadingProjects(true)
    try{
      const data=await api<Summary>("/projects")
      if(!data||!Array.isArray(data.projects)||!data.templates||!Array.isArray(data.fonts)||!Array.isArray(data.kinds))throw new Error("Resposta incompatível do Site Studio. Atualize e reinicie o backend.")
      setSummary(data)
      setTemplate(current=>current in data.templates?current:Object.keys(data.templates)[0]||"servicos")
    }finally{setLoadingProjects(false)}
  }
  const adopt=async(p:Project)=>{setProject(p);setDraft(p.model);setSelected(0);setReviewed(false);setVersions([]);setVersions(await api<Version[]>("/projects/"+p.id+"/versions"));await reload()}
  const run=async(task:()=>Promise<void>)=>{setBusy(true);setError("");setNotice("");try{await task()}catch(e){setError(e instanceof Error?e.message:"Erro inesperado")}finally{setBusy(false)}}
  useEffect(()=>{void reload().catch(e=>setError(String(e)))},[])
  useEffect(()=>{setPreview("");setPreviewError("")},[project?.id])
  useEffect(()=>{
    if(!draft){setPreview("");setPreviewError("");return}
    let active=true
    setPreviewError("")
    const timer=window.setTimeout(()=>{void api<{html:string}>("/preview","POST",{model:draft}).then(r=>{
      if(typeof r?.html!=="string")throw new Error("Prévia inválida recebida do backend.")
      if(active)setPreview(r.html)
    }).catch(e=>{if(active)setPreviewError(e instanceof Error?e.message:"Falha ao gerar a prévia.")})},300)
    return()=>{active=false;window.clearTimeout(timer)}
  },[draft])
  useEffect(()=>{setReviewed(false)},[draft])
  const open=(id:string)=>{if(dirty&&!window.confirm("Descartar alterações não salvas?"))return;void run(async()=>adopt(await api<Project>("/projects/"+id)))}
  const save=async()=>{if(!project||!draft)return;await adopt(await api<Project>("/projects/"+project.id,"PUT",{revision:project.revision,model:draft}));setNotice("Projeto salvo.")}
  const changeSection=(patch:Partial<Section>)=>setDraft(d=>d?{...d,sections:d.sections.map((s,i)=>i===selected?{...s,...patch}:s)}:d)
  const move=(from:number,to:number)=>{if(!draft||to<0||to>=draft.sections.length)return;const list=[...draft.sections];const item=list.splice(from,1)[0];if(!item)return;list.splice(to,0,item);setDraft({...draft,sections:list});setSelected(to)}
  const theme=(key:keyof Model["theme"],value:string)=>setDraft(d=>d?{...d,theme:{...d.theme,[key]:value}}:d)
  const action=async(path:string,body?:unknown)=>{if(!project)return;if(dirty)throw new Error("Salve as alterações antes de continuar.");await adopt(await api<Project>("/projects/"+project.id+path,"POST",body??{}))}
  useEffect(()=>{
    const el=stageRef.current
    if(!el)return
    const measure=()=>setStageWidth(el.clientWidth)
    measure()
    if(typeof ResizeObserver==="undefined"){
      window.addEventListener("resize",measure)
      return()=>window.removeEventListener("resize",measure)
    }
    const observer=new ResizeObserver(measure)
    observer.observe(el)
    return()=>observer.disconnect()
  },[project?.id,showCode])
  const scale=Math.max(0.05,Math.min(1,(stageWidth||width)/width))
  const s=draft?.sections[selected]
  const projects=summary?.projects.filter(p=>(p.name+" "+p.status+" "+p.template).toLocaleLowerCase().includes(filter.toLocaleLowerCase()))??[]
  const goBack=()=>{if(!dirty||window.confirm("Descartar alterações não salvas?")){setProject(null);setDraft(null);setShowCode(false);setInspector("section")}}
  const chooseSection=(i:number)=>{setSelected(i);setInspector("section")}

  return <div className="min-h-screen bg-background text-foreground">
    <Header/>
    <main className="studio">
      <div className="studio-shell">
        <header className="studio-heading">
          <div>
            <p className="studio-breadcrumb">FLP Systems / Site Studio{project?" / Editor":""}</p>
            <h1>{project?project.name:"Site Studio"}</h1>
            <p className="studio-muted">{project?"Personalize, revise e publique a demonstração.":"Da oportunidade comercial ao site pronto para apresentar."}</p>
          </div>
          {project&&<button className={button} onClick={goBack}>Voltar aos projetos</button>}
        </header>
        {error&&<div role="alert" className="studio-message studio-error"><span>{error}</span><button className={button} onClick={()=>setError("")}>Fechar</button></div>}
        {notice&&<div role="status" className="studio-message"><span>{notice}</span><button className={button} onClick={()=>setNotice("")}>Fechar</button></div>}
        {busy&&<p role="status" className="studio-progress">Processando operação…</p>}
        {!project?<div className="studio-home">
          <section className="studio-creation" aria-labelledby="studio-create">
            <p className="studio-muted">Novo projeto</p>
            <h2 id="studio-create">Comece pelo briefing.</h2>
            <p className="studio-muted">Vincule um lead ou inicie com os dados da empresa.</p>
            <div className="studio-form">
              <label>Empresa<input className={field} maxLength={160} value={name} onChange={e=>setName(e.target.value)} placeholder="Nome da empresa"/></label>
              <label>Lead vinculado <span className="studio-hint">(opcional com empresa)</span><input className={field} value={leadId} onChange={e=>setLeadId(e.target.value)} placeholder="ID do lead no CRM"/></label>
              <label>Template<select className={field} value={template} onChange={e=>setTemplate(e.target.value)}>{Object.entries(summary?.templates??{}).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
              <label>Briefing confirmado<textarea className={field} rows={7} maxLength={20000} value={briefing} onChange={e=>setBriefing(e.target.value)} placeholder="Cole o briefing ou use os dados cadastrados do lead."/></label>
              <button disabled={busy||!summary||(!name.trim()&&!leadId.trim())} className={primary} onClick={()=>void run(async()=>{await adopt(await api<Project>("/projects","POST",{name,lead_id:leadId,template,briefing}))})}>{busy?"Criando…":"Criar projeto"}</button>
            </div>
          </section>
          <section className="studio-library" aria-labelledby="studio-library">
            <div className="studio-metrics">{[["Projetos",summary?.projects.length],["Publicados",summary?.projects.filter(p=>p.status==="publicado").length],["IA hoje",summary?.requests_today]].map(([label,value])=><div key={label}><span>{label}</span><strong>{value??"—"}{label==="IA hoje"&&summary&&<small> / 10</small>}</strong></div>)}</div>
            <div className="studio-library-head"><h2 id="studio-library">Meus projetos</h2><label className="studio-search"><span className="sr-only">Buscar projetos</span><input className={field} placeholder="Buscar projeto…" value={filter} onChange={e=>setFilter(e.target.value)}/></label></div>
            {!summary?<div className="studio-empty"><p>{loadingProjects?"Carregando projetos…":"Não foi possível carregar os projetos."}</p>{!loadingProjects&&<button className={button} disabled={busy} onClick={()=>void run(reload)}>Tentar novamente</button>}</div>:projects.length===0?<p className="studio-empty">{filter?"Nenhum projeto corresponde à busca.":"Seus projetos aparecerão aqui após a criação."}</p>:<div className="studio-project-list">{projects.map(p=><button key={p.id} className="studio-project-row" disabled={busy} onClick={()=>open(p.id)}><span className="studio-project-mark" aria-hidden="true">{p.name.slice(0,1).toUpperCase()}</span><span className="studio-project-name"><strong>{p.name}</strong><small>{summary.templates[p.template]??p.template}</small></span><span className="studio-project-status">{p.status}</span><span aria-hidden="true">›</span></button>)}</div>}
          </section>
        </div>:draft&&<>
          <div className="studio-toolbar">
            <div className="studio-project-state"><strong>{dirty?"Alterações não salvas":"Alterações salvas"}</strong><small>Versão {project.revision} / {project.status}</small></div>
            <div className="studio-devices" role="group" aria-label="Largura da prévia">{devices.map(device=><button key={device.width} className={button} aria-pressed={width===device.width} title={device.width+" pixels"} onClick={()=>setWidth(device.width)}>{device.label}</button>)}</div>
            <div className="studio-toolbar-actions"><button className={button} aria-pressed={showCode} onClick={()=>setShowCode(v=>!v)}>{showCode?"Ver prévia":"Ver HTML"}</button><button className={primary} disabled={busy||!dirty} onClick={()=>void run(save)}>Salvar</button><a className={button} href={"/api/studio/projects/"+project.id+"/export"} onClick={e=>{if(dirty){e.preventDefault();setError("Salve antes de exportar.")}}}>Exportar ZIP</a></div>
          </div>
          <div className="studio-workbench">
            <aside className="studio-outline" aria-label="Estrutura do site">
              <div className="studio-panel-title"><h2>Estrutura</h2><span>{draft.sections.length} seções</span></div>
              <div className="studio-outline-list">{draft.sections.map((item,i)=><div key={i} draggable onDragStart={()=>setDrag(i)} onDragEnd={()=>setDrag(null)} onDragOver={e=>e.preventDefault()} onDrop={()=>{if(drag!==null)move(drag,i);setDrag(null)}} className={"studio-section-row"+(i===selected?" is-selected":"")}><span className="studio-index" aria-hidden="true">{String(i+1).padStart(2,"0")}</span><button className="studio-section-select" aria-pressed={i===selected} onClick={()=>chooseSection(i)}><strong>{item.title||sectionNames[item.kind]}</strong><small>{sectionNames[item.kind]??item.kind}</small></button><div className="studio-order"><button aria-label={"Mover "+item.title+" para cima"} disabled={i===0} onClick={()=>move(i,i-1)}>↑</button><button aria-label={"Mover "+item.title+" para baixo"} disabled={i===draft.sections.length-1} onClick={()=>move(i,i+1)}>↓</button></div></div>)}</div>
              <label>Adicionar seção<select className={field} value="" disabled={draft.sections.length>=20} onChange={e=>{if(e.target.value&&draft.sections.length<20){setDraft({...draft,sections:[...draft.sections,{kind:e.target.value,title:sectionNames[e.target.value],body:"",image:""}]});chooseSection(draft.sections.length)}}}><option value="">Escolher componente</option>{summary?.kinds.map(k=><option key={k} value={k}>{sectionNames[k]??k}</option>)}</select></label>
              <details className="studio-details"><summary>Template e versões</summary><label>Trocar template<select className={field} value={project.template} disabled={busy||dirty} onChange={e=>void run(()=>action("/template",{template:e.target.value}))}>{Object.entries(summary?.templates??{}).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label><h3>Histórico</h3>{versions.length===0&&<p className="studio-hint">Sem versões anteriores.</p>}{versions.map(v=><button key={v.id} className="studio-version" disabled={busy||dirty} onClick={()=>{if(window.confirm("Restaurar esta versão?"))void run(()=>action("/restore/"+v.id))}}><strong>{v.label}</strong><small>{v.created_at}</small></button>)}</details>
            </aside>
            <section className="studio-preview" aria-label="Prévia do site">
              <div className="studio-panel-title"><h2>{showCode?"Código HTML":"Prévia do site"}</h2><span>{showCode?"Somente leitura":width+" px / "+Math.round(scale*100)+"%"}</span></div>
              {previewError&&<div role="alert" className="studio-message studio-error">{previewError}{preview?" A prévia anterior pode estar desatualizada.":""}</div>}
              {showCode?<textarea readOnly aria-label="Código HTML gerado" value={preview} className="studio-code" spellCheck={false}/>:<div className="studio-stage"><div ref={stageRef} className="studio-stage-width">{preview?<div className="studio-frame" style={{width:width*scale,height:680}}><iframe title="Prévia isolada do site" sandbox="" referrerPolicy="no-referrer" srcDoc={preview} style={{width,height:680/scale,transform:"scale("+scale+")",transformOrigin:"top left"}}/></div>:<p className="studio-empty" role="status">{previewError?"Corrija o problema indicado para gerar a prévia.":"Preparando a prévia…"}</p>}</div></div>}
            </section>
            <aside className="studio-inspector" aria-label="Propriedades do site">
              <div className="studio-panel-title"><h2>Propriedades</h2></div>
              <div className="studio-tabs" role="group" aria-label="Tipo de propriedade"><button className={button} aria-pressed={inspector==="section"} onClick={()=>setInspector("section")}>Seção</button><button className={button} aria-pressed={inspector==="site"} onClick={()=>setInspector("site")}>Site e tema</button></div>
              {inspector==="site"?<div className="studio-form"><label>Nome do site<input className={field} maxLength={160} value={draft.title} onChange={e=>setDraft({...draft,title:e.target.value})}/></label><label>Descrição SEO<textarea className={field} rows={3} maxLength={300} value={draft.description} onChange={e=>setDraft({...draft,description:e.target.value})}/></label><label>WhatsApp comercial<input className={field} maxLength={40} value={draft.phone} onChange={e=>setDraft({...draft,phone:e.target.value})}/></label><h3>Paleta do site</h3><div className="studio-colors">{(["primary","background","text"] as const).map((k,i)=><label key={k}>{["Destaque","Fundo","Texto"][i]}<input type="color" value={draft.theme[k]} onChange={e=>theme(k,e.target.value)}/><small>{draft.theme[k]}</small></label>)}</div><label>Tipografia<select className={field} value={draft.theme.font} onChange={e=>theme("font",e.target.value)}>{summary?.fonts.map(f=><option key={f}>{f}</option>)}</select></label></div>:s&&<div className="studio-form"><p className="studio-muted">{sectionNames[s.kind]??s.kind}</p><label>Título<input className={field} maxLength={160} value={s.title} onChange={e=>changeSection({title:e.target.value})}/></label><label>Conteúdo<textarea className={field} rows={7} maxLength={4000} value={s.body} onChange={e=>changeSection({body:e.target.value})}/></label><label>Imagem autorizada <span className="studio-hint">até 1 MB</span><input type="file" accept="image/png,image/jpeg,image/webp" className="studio-field studio-file" onChange={e=>{const f=e.target.files?.[0];if(!f)return;if(f.size>1000000){setError("Imagem acima de 1 MB.");return}const reader=new FileReader();reader.onload=()=>{if(typeof reader.result==="string")changeSection({image:reader.result})};reader.readAsDataURL(f)}}/></label><button className={button} disabled={!s.image} onClick={()=>changeSection({image:""})}>Remover imagem</button><button className="studio-button studio-danger" disabled={draft.sections.length<=1} onClick={()=>{setDraft({...draft,sections:draft.sections.filter((_,i)=>i!==selected)});setSelected(0)}}>Excluir seção</button></div>}
            </aside>
          </div>
          <div className="studio-delivery">
            <section className="studio-delivery-panel"><h2>Assistente de IA</h2><p className="studio-muted">Gere ou refine o conteúdo. Limite de 10 operações/dia e 100/mês. O provedor poderá cobrar conforme sua conta.</p><label><span className="sr-only">Instrução para a IA</span><textarea className={field} rows={4} maxLength={4000} value={instruction} onChange={e=>setInstruction(e.target.value)} placeholder="Descreva o site ou a alteração desejada."/></label><button className={primary} disabled={busy||dirty||!instruction.trim()} onClick={()=>{if(window.confirm("Autorizar esta operação de IA e eventual cobrança do provedor?"))void run(async()=>{await action("/ai",{instruction,confirm_cost:true});setInstruction("");setNotice("Alteração por IA salva.")})}}>{busy?"Processando…":"Aplicar com IA"}</button>{dirty&&<p className="studio-hint">Salve as alterações para usar a IA.</p>}</section>
            <section className="studio-delivery-panel"><h2>Publicação</h2><p className="studio-muted">Cloudflare Pages. Configure as credenciais no backend antes de publicar.</p><div><button className={button} disabled={busy} onClick={()=>void run(async()=>{const r=await api<{message:string}>("/cloudflare");setCfStatus(r.message)})}>Testar conexão</button></div>{cfStatus&&<p role="status">{cfStatus}</p>}<label className="studio-check"><input type="checkbox" checked={reviewed} onChange={e=>setReviewed(e.target.checked)}/> Revisei o conteúdo e autorizo a publicação pública.</label><div><button className={primary} disabled={busy||dirty||!reviewed} onClick={()=>void run(async()=>{await action("/publish",{reviewed:true});setNotice("Publicação confirmada.")})}>{project.url?"Republicar":"Publicar site"}</button></div>{project.url&&<div className="studio-published"><a href={project.url} target="_blank" rel="noreferrer">{project.url}</a><div className="studio-toolbar-actions"><button className={button} onClick={()=>void navigator.clipboard.writeText(project.url||"").then(()=>setNotice("Link copiado."),()=>setError("Não foi possível copiar."))}>Copiar link</button><button className={button} onClick={()=>{const msg="Olá! Desenvolvi uma demonstração de um novo site para sua empresa, sem compromisso. Confira: "+project.url;void navigator.clipboard.writeText(msg).then(()=>setNotice("Mensagem copiada. Revise e envie manualmente."),()=>setError("Não foi possível copiar."))}}>Copiar mensagem</button>{draft.phone&&<button className={button} onClick={()=>{let phone=draft.phone.replace(/\D/g,"");if(phone.length===10||phone.length===11)phone="55"+phone;if(phone.length<12||phone.length>15){setError("Confirme o telefone comercial.");return}abrirWhatsappInstalado("https://wa.me/"+phone,"Olá! Desenvolvi uma demonstração de um novo site para sua empresa, sem compromisso. Confira: "+project.url)}}>Abrir WhatsApp</button>}{project.lead_id&&<button className={button} disabled={busy||dirty||!!project.sent_at||project.status!=="publicado"} onClick={()=>{if(window.confirm("Você confirma que já enviou a demonstração ao lead?"))void run(async()=>{await action("/sent",{confirmed:true});setNotice("Envio registrado no CRM.")})}}>{project.sent_at?"Envio registrado":"Registrar envio confirmado"}</button>}</div></div>}</section>
          </div>
        </>}
      </div>
    </main>
  </div>
}
