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
