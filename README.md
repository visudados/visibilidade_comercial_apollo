# Visibilidade Comercial - Apollo 🚀

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey)

Repositório dedicado à automação de processos para o time de Visibilidade Comercial. O objetivo principal deste projeto é automatizar o fluxo de coleta e gestão de dados utilizando web scraping e RPA em plataformas como Google e Apollo.

---

## 📋 Arquitetura e Tecnologias

O projeto foi construído utilizando:
* **Linguagem Principal:** Python 3.10+
* **Automação Web:** Selenium WebDriver (Chromedriver)
* **Orquestração:** Scripts em lote (`.bat`) para facilidade de execução pelo usuário final.

---

## 📁 Estrutura do Projeto

```text
visibilidade_comercial_apollo/
├── src/                  # Código-fonte da automação
│   ├── auth/             # Módulos de login (Google e Apollo)
│   └── core/             # Motores de scraping e regras de negócio
├── tests/                # Reservado para futuros testes unitários
├── .gitignore            # Arquivos ignorados pelo Git (.env, venv, etc.)
├── automation_start.bat  # Script de inicialização rápida
├── requirements.txt      # Dependências do projeto
└── README.md             # Esta documentação
```

---

## ⚙️ Pré-requisitos e Instalação

Como o projeto roda em ambiente Windows e utiliza navegação virtualizada, certifique-se de cumprir os requisitos abaixo:

### 1. Ambiente Local
* Python 3.10 ou superior instalado e adicionado ao `PATH`.
* Google Chrome instalado.

### 2. Configuração do Projeto
Clone o repositório e configure o ambiente virtual:

```bash
# Clone o repositório (Agora na Organização)
git clone [https://github.com/visudados/visibilidade_comercial_apollo.git](https://github.com/visudados/visibilidade_comercial_apollo.git)
cd visibilidade_comercial_apollo

# Crie e ative o ambiente virtual (venv)
python -m venv venv
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

> 📌 **Nota sobre o Chromedriver:** O Selenium tentará gerenciar o driver automaticamente. Caso utilize uma versão específica do Chrome que exija download manual, garanta que o `chromedriver.exe` esteja referenciado corretamente nas variáveis de ambiente ou na pasta raiz.

---

## 🚀 Como Executar

### Modo Prático (Usuário Final)
Basta executar o arquivo `automation_start.bat` na raiz do projeto. Ele se encarregará de validar o ambiente e disparar o fluxo principal da automação.

### Modo Desenvolvedor
Com o ambiente virtual ativado, execute diretamente o arquivo de inicialização Python:
```bash
python src/main.py
```

---

## 🛠️ Fluxo de Trabalho (Git Flow)

Para manter a integridade do projeto na organização, evite commitar direto na branch `main`. Siga o padrão:

1. Crie uma branch para a sua tarefa: `git checkout -b feature/nome-da-task`
2. Faça suas alterações e realize o commit: `git commit -m "feat: adiciona funcionalidade x"`
3. Envie a branch: `git push origin feature/nome-da-task`
4. Abra um **Pull Request** para revisão.

---
Desenvolvido por [Visudados](https://github.com/visudados).