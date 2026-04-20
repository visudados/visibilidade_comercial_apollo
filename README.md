# Visibilidade Comercial - Apollo 🚀

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey)
![Environment](https://img.shields.io/badge/manager-uv-blueviolet)

Repositório dedicado à automação de processos para o time de Visibilidade Comercial. O objetivo principal deste projeto é automatizar o fluxo de coleta e gestão de dados utilizando web scraping e RPA em plataformas como Google e Apollo.

---

## 📋 Arquitetura e Tecnologias

O projeto foi construído utilizando:
* **Linguagem Principal:** Python 3.10+
* **Gerenciador de Ambiente:** [uv](https://docs.astral.sh/uv/) (Astral)
* **Automação Web:** Selenium WebDriver
* **Processamento de Dados:** Pandas & PyArrow (Parquet)
* **Orquestração:** Scripts em lote (`.bat`) para automação ponta a ponta.

---

## 📁 Estrutura do Projeto

```text
visibilidade_comercial_apollo/
├── python/
│   ├── common/           # Motores de browser e setups compartilhados
│   ├── data/             # Staging Area (CSVs) e Data Warehouse (Parquet)
│   └── projects/         # Scripts de execução
│       ├── extract/      # Lógica de Web Scraping (Apollo)
│       └── transform/    # Lógica de ETL e Tratamento de Dados
├── automation_start.bat  # Inicia a extração de contatos (Scraping)
├── transform_start.bat   # Inicia a transformação e carga (ETL)
└── README.md             # Esta documentação
```

---

## ⚙️ Fluxo de Dados (ETL)

O projeto opera em um ciclo completo de **Extração, Transformação e Carga**:

### 1. Extração (Extract) 🕸️
* **Script:** `automation_start.bat` -> `run_apollo_sequence_contacts.py`
* **O que faz:** Navega automaticamente pelo Apollo, acessa sequências específicas e realiza o download de contatos para a pasta `Downloads` do Windows.

### 2. Transformação (Transform) 🛠️
* **Script:** `transform_start.bat` -> `transform_apollo_contacts.py`
* **Processamento:**
    * **Captura Inteligente:** Identifica e move apenas os arquivos baixados na data atual de `Downloads` para a pasta de dados do projeto (`python/data/raw_extract_apollo_...`).
    * **Limpeza e Enriquecimento:** Adiciona metadados como nome do Consultor e Step, normaliza nomes e formata datas para o padrão ISO (Power BI).
    * **Unificação:** Consolida múltiplos arquivos de diferentes consultores em um único `master_apollo_YYYY_MM_DD.csv`.

### 3. Carga (Load) 📦
* **Data Warehouse:** Os dados transformados são anexados ao arquivo `database_apollo.parquet`.
* **Consumo:** Este arquivo Parquet é otimizado para ser lido diretamente pelo **Power BI**, garantindo performance no histórico de milhares de registros.

---

## 🔐 Guia de Uso e Login (Importante!)

Para que a automação funcione perfeitamente, siga estas orientações:

### Primeiro Acesso ou Sessão Expirada
1. Ao executar o `automation_start.bat`, uma janela do Chrome será aberta.
2. Se você não estiver logado no **Apollo.io**, o robô aguardará pacientemente.
3. **Sua Ação:** Realize o login manualmente (e-mail/senha ou Google Auth).
4. Assim que você entrar na tela inicial do Apollo, o robô reconhecerá sua sessão e assumirá o controle automaticamente.

### Dicas para uma Automação Sem Erros
* **Mãos ao Alto!** 👐 Enquanto o robô estiver navegando, evite clicar na janela do Chrome ou minimizar o terminal. Ele precisa do foco para interagir com os elementos.
* **Algo deu errado?** Se o login funcionou mas o robô parece "travado" ou não encontra os botões, não se preocupe:
    * Feche a janela preta (terminal).
    * Feche a janela do Chrome aberta pelo robô.
    * Execute o `automation_start.bat` novamente. 
    * *Isso limpa o estado anterior e geralmente resolve 99% dos problemas de navegação.*

---

## 🚀 Como Executar

O projeto utiliza o gerenciador **uv**. Caso você não o tenha instalado, o script `automation_start.bat` tentará instalá-lo automaticamente via WinGet.

### Fluxo do Usuário Final:
1.  **Extração:** Execute `automation_start.bat`. O robô abrirá o Chrome e baixará os contatos.
2.  **Processamento:** Após o robô fechar, execute `transform_start.bat`. Isso atualizará sua base de dados.

### Fluxo do Desenvolvedor:
```bash
cd python
uv sync
uv run python projects/transform/transform_apollo_contacts.py
```

## 🛠️ Fluxo de Trabalho (Git Flow)

Para manter a integridade do projeto na organização, evite commitar direto na branch `main`. Siga o padrão:

1. Crie uma branch para a sua tarefa: `git checkout -b feature/nome-da-task`
2. Faça suas alterações e realize o commit: `git commit -m "feat: adiciona funcionalidade x"`
3. Envie a branch: `git push origin feature/nome-da-task`
4. Abra um **Pull Request** para revisão.

---
Desenvolvido por [Visudados](https://github.com/visudados).