# AcademiaFit — versão roxa

## O que foi ajustado
- Identidade visual roxa responsiva compartilhada entre as páginas (`css/tema-roxo.css`).
- API Flask com rotas para dashboard, alunos, professores, planos, pagamentos e treinos.
- Banco SQLite com criação automática e migração aditiva para bases existentes.
- Cadastro e listagem de alunos/professores conectados à API; contadores do dashboard conectados.
- Senhas novas armazenadas com hash; compatibilidade com contas antigas após login válido.

## Executar localmente (Windows / VS Code)
Abra o terminal na pasta `back`:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
A API fica em `http://127.0.0.1:5000`. Abra o front-end com um servidor local, por exemplo Live Server no VS Code. Não abra os HTML como `file://` em produção.

Teste a API em `http://127.0.0.1:5000/api/teste`.

## Publicar no Render
1. Envie a pasta do projeto para um repositório GitHub.
2. Crie um Web Service no Render usando esse repositório.
3. **Root Directory:** `back`
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `gunicorn app:app`
6. Para preservar os dados entre deploys, configure um disco persistente e a variável `DATABASE_PATH` para um arquivo dentro do disco, por exemplo `/var/data/academia.db`.
7. Se o front-end ficar em outro domínio, configure `CORS_ORIGINS` com o domínio do front-end.

## Observações
- SQLite é adequado para protótipos e sistemas pequenos. Para muitos acessos simultâneos, considere PostgreSQL.
- O login ainda não implementa sessão/token de autorização para proteger as rotas. Antes de usar com dados reais, implemente autenticação e autorização.
- As telas de planos, pagamentos e treinos precisam ter seus formulários ligados às rotas da API para que esses módulos estejam completos.


## Login e logo AcademiaFit
- Abra `html/login.html` pelo Live Server para acessar a tela de login.
- O back-end Flask deve estar ativo em `http://127.0.0.1:5000`.
- No primeiro acesso, clique em **Criar uma conta** para registrar nome, e-mail e senha (mínimo de 6 caracteres).
- Após entrar, o usuário é encaminhado ao painel. As páginas internas redirecionam ao login se não houver sessão no navegador.
- A imagem oficial está em `assets/academiafit-logo.png`.
- Para ambientes hospedados separadamente, defina `window.API_BASE` antes dos scripts de login/cadastro com a URL pública da API.

## Correção de conexão (cadastro de alunos e professores)
- As páginas servidas pelo Live Server na porta 5500 agora enviam as requisições para o Flask em `http://127.0.0.1:5000`.
- Corrigido o acesso aos campos do formulário de professores.
- Inicie a API na pasta `back` com `py app.py` e mantenha o terminal aberto.
- Teste `http://127.0.0.1:5000/api/teste` antes de usar os formulários.
