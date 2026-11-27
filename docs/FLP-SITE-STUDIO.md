# FLP Site Studio

## Como usar

1. Preserve suas alterações locais antes de trocar de branch. Não faça commit de .env, banco de dados, sessões do Instagram ou .venv.
2. No backend, com a .venv ativa, execute `python -m pip install -r requirements.txt` e `python -m pytest`. No frontend execute `npm install` e `npm run build`.
3. Reinicie a aplicação. Abra **Site Studio** no cabeçalho ou **Criar demonstração de site** no detalhe de um lead do Google Maps. O botão **Abrir briefing no Site Studio** importa o briefing já gerado. O Estúdio acompanha o tema claro ou escuro do aplicativo.
4. Escolha o modelo ou deixe o Estúdio sugeri-lo pelo segmento. Selecione o objetivo, a estrutura e a aparência do site. A amostra reflete essas escolhas. No briefing, campos como **Sobre**, **Serviços**, **Diferenciais** e **Endereço** ajudam a preencher a base local.
5. No **Editor**, ajuste o conteúdo, os itens e as composições das seções, a ordem, as imagens autorizadas e o tema do site gerado. Alterne a prévia entre computador, notebook, tablet e celular. Em **Gerador**, você pode preencher o roteiro com IA, revisar o site ou refinar uma seção. Confirme a autorização de possível cobrança e revise o resultado.
6. A IA gera um modelo estruturado validado; o backend o converte em HTML/CSS estáticos. Não é um agente que escreve ou executa código arbitrário. A prévia usa iframe sandbox sem scripts e sem acesso à origem. As imagens aceitas são PNG/JPEG/WebP locais até 1 MB.
7. Para publicar, configure no arquivo backend/.env (não versionado) CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN. Crie um token limitado à sua conta com permissão Pages Edit. Não coloque as credenciais no frontend.
8. Salve o projeto antes de exportar o ZIP ou publicar. A área **Publicação** traz uma revisão de estrutura, descrição SEO, contraste, imagens e WhatsApp. Teste a conexão e autorize a publicação. O módulo verifica o conteúdo publicado antes de registrar sucesso. Republicações reutilizam o projeto Cloudflare.
9. Copie o link ou abra o WhatsApp e envie manualmente. Confirme o envio para registrar a atividade; um lead novo passa a contatado, sem regredir outros status.

## Limites atuais

- Treze modelos de segmentos, quatro objetivos de conversão, duas estruturas, sete direções visuais e onze tipos de seção. Os sites são de uma página.
- IA reutiliza Gemini/Groq/NVIDIA e fallback da plataforma, exige confirmação de cobrança potencial; sem limite diário interno; mantém o limite de 100 operações mensais. Contagem é de operações, não de chamadas individuais nem tokens/faturamento.
- Não há editor de código editável, canvas de arrastar elementos livres, animações avançadas, páginas múltiplas, biblioteca de fontes licenciadas, domínios próprios, custos detalhados, conta Cloudflare configurável pela interface, nem extração automática adicional de mídia. Use os recursos de análise de sites já existentes.
- Projetos e versões permanecem no SQLite local. Não são excluídos registros existentes; migrações criam tabelas novas. A integração usa leads Google Maps.
- Se um deploy for interrompido ou ficar pendente, confira a Cloudflare antes de repetir. Um projeto criado remotamente mas não gravado no banco pode precisar de conciliação manual.
- O fluxo real depende de provedores de IA e credenciais Cloudflare válidos. Não há demonstração publicada no desenvolvimento desta branch.
- O app existente é local; não exponha a API à internet sem autenticação e controles adicionais.
- O painel HTML mostra o código de exportação em modo somente leitura. O histórico registra as versões anteriores antes de edições, trocas de modelo, geração e publicação.
