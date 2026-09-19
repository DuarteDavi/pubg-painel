# Como Iniciar o Painel Survival Macro

Guia rÃ¡pido para iniciar os serviÃ§os de desenvolvimento e teste.

## PrÃ©-requisitos

- Python 3.10+
- Node.js 16+
- npm

## InstalaÃ§Ã£o de DependÃªncias (primeira vez apenas)

### Backend

```bash
cd survival-panel/backend
pip install -r requirements.txt
```

### Frontend

```bash
cd survival-panel/frontend
npm install
```

## Iniciar ServiÃ§os

### Terminal 1: Backend (FastAPI)

```bash
cd survival-panel/backend
python main.py
```

**Esperado:**
```
INFO:     Started server process [8800]
INFO:     Uvicorn running on http://127.0.0.1:3014
```

**DisponÃ­vel em:** http://127.0.0.1:3014
- Health: GET http://127.0.0.1:3014/health
- Swagger (dev only): GET http://127.0.0.1:3014/docs (se DEBUG=True)

### Terminal 2: Frontend (Vite)

```bash
cd survival-panel/frontend
npm run dev
```

**Esperado:**
```
VITE v5.4.21  ready in 919 ms

  âžœ  Local:   http://127.0.0.1:5173/
```

**DisponÃ­vel em:** http://127.0.0.1:5173
- Login: http://127.0.0.1:5173/login
- Dashboard: http://127.0.0.1:5173/ (apÃ³s login)

## ConfiguraÃ§Ã£o do Admin

### 1. Gerar Hash da Senha

No diretÃ³rio `backend/`:

```bash
python app/scripts/hash_password.py
```

**Entrada:**
```
Enter admin password: <senha-configurada-localmente>
Confirm password: <senha-configurada-localmente>
```

**SaÃ­da:**
```
ADMIN_PASSWORD_HASH=$2b$12$...hash completo...
```

### 2. Atualizar .env

Editar `backend/.env`:

```env
ADMIN_LOGIN=admin
ADMIN_PASSWORD_HASH=<colar hash do passo anterior>
JWT_SECRET=<gerar com: openssl rand -hex 32>
```

### 3. Reiniciar Backend

Parar o serviÃ§o (Ctrl+C) e iniciar novamente:

```bash
python main.py
```

## Testar a AplicaÃ§Ã£o

### 1. Acessar Interface de Login

Abrir navegador: http://127.0.0.1:5173/login

**Esperado:**
- Fundo preto profundo
- TÃ­tulo "SURVIVAL MACRO" em vermelho ferrugem
- SubtÃ­tulo "ACCESS CONTROL" em amarelo industrial
- Campos de login e senha com borda vermelha
- BotÃ£o "ENTER" destacado

### 2. Fazer Login (apÃ³s configurar hash)

```
Login: admin
Senha: <senha-configurada-localmente>
```

**Esperado:**
- Redirecionar para Dashboard
- Mostrar estatÃ­sticas: Total de clientes, licenÃ§as, dispositivos

### 3. Testar API

#### Health Check

```bash
curl http://127.0.0.1:3014/health
```

**Resposta esperada:**
```json
{"status":"ok"}
```

#### Validar Produto

```bash
curl -X POST http://127.0.0.1:3014/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "login":"testuser",
    "password":"testpass",
    "product":"survival_macro",
    "device":{"system_uuid_hash":"abc123def456"}
  }'
```

**Resposta esperada (cliente nÃ£o existe):**
```json
{"detail":"INVALID_CREDENTIALS"}
```

**Se retornar `INVALID_PRODUCT`**: produto nÃ£o foi criado

## Estrutura de Arquivos

```
survival-panel/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ models.py         â† Banco de dados
â”‚   â”‚   â”œâ”€â”€ routes/
â”‚   â”‚   â”‚   â”œâ”€â”€ auth.py       â† API cliente
â”‚   â”‚   â”‚   â””â”€â”€ admin.py      â† API admin
â”‚   â”‚   â””â”€â”€ ...
â”‚   â”œâ”€â”€ .env                  â† Criar com hash do admin
â”‚   â”œâ”€â”€ .env.example          â† Template
â”‚   â”œâ”€â”€ main.py               â† Iniciar aqui
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â”œâ”€â”€ README.md
â”‚   â””â”€â”€ survival_macro.db     â† Banco de dados (criado ao iniciar)
â”‚
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â”‚   â”œâ”€â”€ Login.jsx
â”‚   â”‚   â”‚   â”œâ”€â”€ Dashboard.jsx
â”‚   â”‚   â”‚   â””â”€â”€ ...
â”‚   â”‚   â””â”€â”€ ...
â”‚   â”œâ”€â”€ .env                  â† Criar com VITE_API_URL
â”‚   â”œâ”€â”€ .env.example
â”‚   â”œâ”€â”€ vite.config.js
â”‚   â”œâ”€â”€ package.json
â”‚   â””â”€â”€ index.html
â”‚
â”œâ”€â”€ README.md
â”œâ”€â”€ CONFORMIDADE_CONTEXTO_PADRAO.md
â”œâ”€â”€ COMO_INICIAR.md           â† VocÃª estÃ¡ aqui
â””â”€â”€ .gitignore
```

## Troubleshooting

### Backend nÃ£o inicia

**Erro:** `ModuleNotFoundError: No module named 'app'`
- SoluÃ§Ã£o: Estar no diretÃ³rio `backend/` ao executar

**Erro:** `pydantic_core._pydantic_core.ValidationError`
- SoluÃ§Ã£o: Verificar `.env`, pode ter caracteres invÃ¡lidos
- Criar novo .env: `cat > .env << EOF` (bash) ou editar manualmente

**Erro:** `Internal Server Error` no login
- SoluÃ§Ã£o: `ADMIN_PASSWORD_HASH` vazio ou invÃ¡lido
- Executar `python app/scripts/hash_password.py` novamente

### Frontend nÃ£o carrega

**Erro:** `Connection refused on 127.0.0.1:5173`
- SoluÃ§Ã£o: npm run dev estÃ¡ rodando?
- Tentar: `npm install` novamente

**Erro:** `Cannot find module 'react'`
- SoluÃ§Ã£o: `npm install`

**Erro:** `VITE does not recognize vite command`
- SoluÃ§Ã£o: `npm install` ou `npm run build` no frontend

### API retorna 401/403

- Verificar token em localStorage
- Fazer logout e login novamente
- Limpar cache do navegador (F12 > Storage > Clear All)

### Banco de dados "corrompido"

- Deletar `backend/survival_macro.db`
- Reiniciar backend (recria banco automaticamente)
- âš ï¸ Perde todos os dados, use apenas em desenvolvimento

## Comandos Ãšteis

### Parar todos os serviÃ§os

```bash
# Linux/Mac
pkill -f "python main.py"
pkill -f "npm run dev"

# Windows
taskkill /IM python.exe /F
taskkill /IM node.exe /F
```

### Ver logs do backend

Backend escreve em stdout. Para salvar em arquivo:

```bash
python main.py > backend.log 2>&1 &
tail -f backend.log
```

### Resetar banco de dados

```bash
rm backend/survival_macro.db
# Reiniciar backend
python main.py
```

### Testar rate limiting

```bash
for i in {1..6}; do
  curl -X POST http://127.0.0.1:3014/api/admin/login \
    -H "Content-Type: application/json" \
    -d '{"login":"admin","password":"wrong"}'
  echo "Request $i"
done
```

Esperado: Primeiras 5 retornam `INVALID_CREDENTIALS`, sexta retorna `RATE_LIMITED`

## Build para ProduÃ§Ã£o

### Backend

```bash
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:3014 main:app
```

### Frontend

```bash
cd frontend
npm run build
# SaÃ­da em: dist/
# Servir com nginx, Apache, ou static server
```

## PrÃ³ximas Etapas

1. âœ… Iniciar backend e frontend
2. âœ… Acessar http://127.0.0.1:5173/login
3. âœ… Fazer login com credenciais configuradas localmente
4. âœ… Ver dashboard
5. â­ï¸ Criar cliente via "Create Client"
6. â­ï¸ Testar login do cliente via API
7. â­ï¸ Testar gerenciamento de dispositivos
8. â­ï¸ Deploy com PostgreSQL + Nginx

## Suporte

Verificar:
- `backend/README.md` - DocumentaÃ§Ã£o API
- `frontend/README.md` - DocumentaÃ§Ã£o frontend
- `CONFORMIDADE_CONTEXTO_PADRAO.md` - SeguranÃ§a

