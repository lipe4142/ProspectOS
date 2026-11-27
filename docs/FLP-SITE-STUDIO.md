# FLP Site Studio — primeira implementação

Branch: feat/flp-site-studio, baseada em feat/flp-ferramentas-comerciais.

## Como usar

1. Preserve suas alterações locais antes de trocar de branch. Não faça commit de .env, banco de dados, sessões do Instagram ou .venv.
2. No backend, com a .venv ativa, execute `python -m pip install -r requirements.txt` e `python -m pytest`. No frontend execute `npm install` e `npm run build`.
3. Reinicie a aplicação. Abra Site Studio no cabeçalho ou "Criar demonstração de site" no detalhe de um lead do Google Maps. O botão "Abrir briefing no Site Studio" importa o briefing já gerado.
4. Escolha um template, confirme o conteúdo e crie um projeto. Na área de IA solicite "Crie um site completo com base neste briefing", confirme a autorização de possível cobrança e revise o resultado.
5. Edite cores, fontes do sistema, títulos, textos, ordem e imagens autorizadas; salve e exporte o ZIP. O painel HTML é somente leitura. A versão anterior é registrada antes de alterações persistidas, trocas de template, IA e publicação.
6. A IA gera um modelo estruturado validado; o backend o converte em HTML/CSS estáticos. Não é um agente que escreve ou executa código arbitrário. A prévia usa iframe sandbox sem scripts e sem acesso à origem. As imagens aceitas são PNG/JPEG/WebP locais até 1 MB.
7. Para publicar, configure no arquivo backend/.env (não versionado) CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN. Crie um token limitado à sua conta com permissão Pages Edit. Não coloque as credenciais no frontend.
8. Teste a conexão, salve o projeto, revise o conteúdo e autorize a publicação. O módulo solicita Direct Upload via REST e verifica o conteúdo publicado antes de registrar sucesso. Republicações reutilizam o projeto Cloudflare registrado. Não há registro de domínio pago nem publicação automática.
9. Copie o link ou abra o WhatsApp e envie manualmente. Confirme o envio para registrar a atividade; um lead novo passa a contatado, sem regredir outros status.

## Limites atuais

- Dez templates de grupos de nichos, sete tipos de seções, seis fontes do sistema, um site de uma página.
- IA reutiliza Gemini/Groq/NVIDIA e fallback da plataforma, exige confirmação de cobrança potencial; limite fixo de 10 operações diárias e 100 mensais. Contagem é de operações, não de chamadas individuais nem tokens/faturamento.
- Não há editor de código editável, canvas de arrastar elementos livres, animações avançadas, páginas múltiplas, biblioteca de fontes licenciadas, domínios próprios, custos detalhados, conta Cloudflare configurável pela interface, nem extração automática adicional de mídia. Use os recursos de análise de sites já existentes.
- Projetos e versões permanecem no SQLite local. Não são excluídos registros existentes; migrações criam tabelas novas. A integração usa leads Google Maps.
- Se um deploy for interrompido ou ficar pendente, confira a Cloudflare antes de repetir. Um projeto criado remotamente mas não gravado no banco pode precisar de conciliação manual.
- O fluxo real depende de provedores de IA e credenciais Cloudflare válidos. Não há demonstração publicada no desenvolvimento desta branch.
- O app existente é local; não exponha a API à internet sem autenticação e controles adicionais.
- Testes adicionados em backend/tests/test_site_studio.py. Validação de build e execução em ambiente real ainda pendentes.


## Evolução premium — referência visual LPaaS

O material de referência fornecido continha uma captura pública da landing page comercial (index.html), scripts/assets e seis imagens de exemplos. Não continha o ambiente autenticado nem o motor de geração privado. Foram extraídos princípios de design, não código, fotos ou identidade de terceiros.

- Motor original com 9 estilos, 20 grupos de nichos, 11 tipos de seções e 7 opções de composição. Cabeçalho responsivo, FAQ interativo nativo, CTA, tipografia editorial e ilustração geométrica original quando não há foto.
- Criação completa com IA em um clique, com validação mínima de estrutura (5 seções e 4 tipos distintos, começando com hero). Edição de seção selecionada preserva as demais. Projetos antigos continuam editáveis.
- Ajustes locais de estilo, paleta, variante, textos, CTA, cards e perguntas sem consumo de IA. Histórico e publicação permanecem como antes.
- Checklist estrutural de oito critérios, não uma avaliação visual automatizada. Fotos reais são fornecidas pelo cliente ou escolhidas pelo operador no Pexels; sem foto, a interface usa arte abstrata original.
- Opcional: configure PEXELS_API_KEY no backend/.env (https://www.pexels.com/api/). Pesquise por nicho e selecione uma foto ilustrativa. A importação otimiza para WebP e preserva crédito. Não represente foto de banco como instalação, equipe ou cliente real. Respeite licença e cotas do Pexels.
- Não há treinamento de pesos de modelos de IA nem geração automática de fotografia; o sistema usa direção de arte, validação e composição programática próprias. Não é uma reprodução integral do LPaaS.
- Limites de IA e cobrança potencial permanecem os do sistema existente. Não foi adicionada cobrança ou contratação automática.
- Testes adicionados em test_site_studio.py. Execute pytest e npm run build antes de mesclar. Teste um site com imagens autorizadas, compare todos os tamanhos e publique apenas depois de revisar.


## Studio Premium — fluxo em sete etapas

1. Análise local: identifica o segmento a partir do nome, categoria, nicho e briefing. A classificação é heurística, não pesquisa externa nem verificação factual. Escolher o template manualmente continua possível.
2. Direção de arte: perfil do nicho orienta a geração por IA; fontes de títulos, espaçamento, bordas e superfícies por seção podem ser editados sem consumir IA.
3. Imagens: PIXABAY_API_KEY no backend/.env habilita o Pixabay prioritário, com consulta sugerida pelo segmento, cache SQLite por 24 horas, seleção humana e download local otimizado em WebP. PEXELS_API_KEY é fallback opcional. A API é destinada a consultas humanas, não a coleta em massa. Créditos e indicação de imagem ilustrativa são mantidos. Imagens de banco não representam equipe, clientes ou instalações reais.
4. Composição: o motor combina direções de arte, estrutura, conteúdo, paleta, variantes e superfícies. Não promete exclusividade absoluta; ainda é um sistema de componentes. A abertura não usa formas geométricas genéricas quando não há foto.
5. Código: gera um HTML independente com CSS e JavaScript fixo e revisável para microinterações. O modelo fornece somente dados estruturados, não executa código arbitrário. O script publicado é autorizado por hash CSP; a prévia permanece em iframe sandbox sem scripts.
6. Auditoria: botão "Auditar responsividade no navegador" usa Chromium com rede bloqueada, sem acessar o CRM, em 390, 768 e 1440 px. Mostra capturas do primeiro viewport, overflow, imagens quebradas, H1 e altura de botões. Não é Lighthouse nem avaliação estética por IA. Se necessário instale Chromium com python -m playwright install chromium.
7. Editor e publicação: prévia com escala automática, edição por seção, histórico, exportação e publicação Cloudflare após confirmação. As alterações não publicam automaticamente nem modificam sites já hospedados.

Para validar localmente: git pull --ff-only origin feat/studio-premium, execute pytest e npm run build, reinicie o sistema e teste um projeto de advocacia com template automático. Pesquise uma foto usando a consulta sugerida e selecione uma imagem ilustrativa autorizada. Salve e execute a auditoria. O limite interno de operações IA continua em 10/dia e 100/mês. Nenhum token real foi usado durante o desenvolvimento. A compilação, execução dos testes e chamadas reais Pixabay/Cloudflare ainda precisam ser verificadas.
