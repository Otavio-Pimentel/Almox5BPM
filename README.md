# 🚔 Sistema de Almoxarifado / Reserva de Armamentos — PM

Sistema completo para gerenciamento do almoxarifado de um Batalhão da Polícia Militar. Desenvolvido para rodar **localmente**, sem necessidade de internet ou servidor externo.

---

## 📋 Funcionalidades

- **Dashboard** com visão geral: cautelas ativas, atrasos, alertas de manutenção
- **Gestão de Estoque**: CRUD completo de armamentos, coletes, rádios HT, munição e demais itens
- **Gestão do Efetivo**: Cadastro e controle dos policiais do batalhão
- **Painel de Cautela**: Interface rápida para registrar saídas e devoluções de material
- **Leitor de Código de Barras**: Compatível nativamente (o leitor funciona como teclado)
- **Backup Automático** do banco de dados

---

## ⚙️ Pré-Requisitos

Antes de instalar, você precisa ter o **Python 3.10 ou superior** instalado.

### Como instalar o Python (para leigos):
1. Acesse: **https://www.python.org/downloads/**
2. Clique em **"Download Python 3.x.x"**
3. Execute o instalador
4. ⚠️ **IMPORTANTE**: Marque a caixa **"Add Python to PATH"** antes de clicar em Install
5. Clique em **"Install Now"**

---

## 🚀 Instalação e Execução

### Método Fácil (Windows) — Recomendado

1. Extraia a pasta do sistema em um local fixo no computador (ex: `C:\AlmoxarifadoPM\`)
2. Dê **duplo clique** no arquivo `INICIAR_SISTEMA.bat`
3. Na primeira execução, o sistema instalará as dependências automaticamente (aguarde ~1 minuto)
4. O navegador abrirá automaticamente com o sistema

> 💡 **Dica**: Crie um atalho do arquivo `INICIAR_SISTEMA.bat` na área de trabalho para acesso rápido.

---

### Método Manual (todos os sistemas)

Abra o **Prompt de Comando** (Windows) ou **Terminal** (Linux/Mac) e execute:

```bash
# 1. Entre na pasta do projeto
cd C:\AlmoxarifadoPM

# 2. Crie um ambiente virtual Python (apenas na primeira vez)
python -m venv venv

# 3. Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# 4. Instale as dependências (apenas na primeira vez)
pip install -r backend/requirements.txt

# 5. Inicie o servidor
cd backend
python main.py
```

6. Abra o navegador em: **http://localhost:8000**

---

## 🌐 Acesso pela Rede Interna (Outros Computadores do Batalhão)

Se quiser acessar o sistema de outros computadores na mesma rede:

1. Descubra o IP do computador onde o sistema roda (ex: `192.168.1.10`)
   - Abra o CMD e digite: `ipconfig`
   - Procure por "Endereço IPv4"

2. Nos outros computadores, abra o navegador e acesse:
   `http://192.168.1.10:8000`

---

## 💾 Backup do Banco de Dados

O banco de dados fica no arquivo **`almoxarifado.db`** na raiz do projeto. É **fundamental** fazer backups regularmente.

### Backup Manual
Dê duplo clique no arquivo `backup.py` ou execute:
```bash
python backup.py
```
Os backups serão salvos na pasta `backups/`.

### Backup Automático Diário (Windows)
1. Pressione `Win + R` → digite `taskschd.msc` → Enter
2. Clique em **"Criar Tarefa Básica"**
3. Nome: `Backup Almoxarifado PM`
4. Frequência: **Diariamente**
5. Horário: `23:00` (ou conforme preferir)
6. Ação: **Iniciar um programa**
7. Programa: `C:\AlmoxarifadoPM\venv\Scripts\python.exe`
8. Argumentos: `C:\AlmoxarifadoPM\backup.py`
9. Conclua o assistente

> 💡 **Dica extra**: Configure o destino do backup no arquivo `backup.py` para salvar direto em um pen drive ou pasta de rede do batalhão.

---

## 📁 Estrutura do Projeto

```
almoxarifado-pm/
├── backend/
│   ├── main.py              # Servidor FastAPI (ponto de entrada)
│   ├── database.py          # Conexão com SQLite
│   ├── models.py            # Definição das tabelas
│   ├── schemas.py           # Validação de dados da API
│   ├── requirements.txt     # Dependências Python
│   └── routers/
│       ├── policiais.py     # API de policiais
│       ├── itens.py         # API de estoque
│       └── cautelas.py      # API de cautelas
├── frontend/
│   ├── index.html           # Dashboard principal
│   ├── estoque.html         # Gestão de estoque
│   ├── efetivo.html         # Gestão do efetivo
│   ├── cautelas.html        # Painel de cautela
│   └── static/
│       └── app.js           # Utilitários JavaScript
├── backup.py                # Script de backup
├── INICIAR_SISTEMA.bat      # Atalho de inicialização (Windows)
├── almoxarifado.db          # Banco de dados (gerado automaticamente)
└── README.md                # Este arquivo
```

---

## 🔫 Uso com Leitor de Código de Barras

O sistema é **100% compatível** com leitores de código de barras USB. Eles funcionam como teclados automáticos:

1. Clique no campo **"Número de Série"** no Painel de Cautela
2. "Bipe" o armamento/colete com o leitor
3. O sistema buscará o item automaticamente (o leitor envia Enter ao final)

> Para isso funcionar, os números de série dos itens devem ser cadastrados com o mesmo código que está no código de barras impresso.

---

## 🗃️ Banco de Dados

O SQLite não requer instalação de servidor. O arquivo `almoxarifado.db` é criado automaticamente na primeira execução e contém todas as informações do sistema. **Mantenha este arquivo em local seguro com backups regulares.**

---

## 🆘 Problemas Comuns

| Problema | Solução |
|---|---|
| "python não é reconhecido" | Reinstale o Python marcando "Add to PATH" |
| Porta 8000 ocupada | Encerre outros programas ou edite `main.py` trocando a porta |
| Navegador não abre | Acesse manualmente: `http://localhost:8000` |
| Erro ao instalar dependências | Verifique sua conexão com a internet |
| Sistema lento | Normal no primeiro acesso. Subsequentes são rápidos. |

---

## 📞 Documentação da API

Com o sistema rodando, acesse a documentação interativa da API em:
**http://localhost:8000/docs**

Permite testar todas as rotas diretamente pelo navegador.

---

*Sistema desenvolvido para uso interno da Polícia Militar. Todos os dados são armazenados localmente.*
