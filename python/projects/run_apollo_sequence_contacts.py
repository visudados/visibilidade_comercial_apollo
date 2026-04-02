"""
run_apollo_sequence_contacts.py - VISU Dados
=============================================

Ponto de entrada para exportação de contatos filtrados por Step
de uma Sequence específica do Apollo.io.

Segue o padrão run_*.py do projeto VISU: configuração centralizada
no topo do arquivo, sem arquivos .env ou argumentos de linha de comando.

Uso:
----
    python run_apollo_sequence_contacts.py

    Ou via .bat (duplo-clique):
        iniciar_apollo_contacts.bat  (a criar)

Configuração:
-------------
Edite as variáveis da seção CONFIG abaixo:
    NOME_SEQUENCE  — texto (parcial) do nome da Sequence na lista Apollo
    STEP_LABEL     — rótulo exato do Step conforme exibido na UI
    DOWNLOAD_DIR   — pasta de destino do CSV (None = Downloads do Windows)
    HEADLESS       — True para rodar sem abrir o Chrome visivelmente
    TIMEOUT        — segundos máximos de espera por cada elemento
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from projects.extract.extract_apollo_sequence_contacts import extrair_contatos_por_step

# -------------------------------------------------------------------------
# CONFIG — ajuste conforme necessário
# -------------------------------------------------------------------------

# Texto parcial do nome da Sequence a ser selecionada na lista.
# Use um trecho único o suficiente para não corresponder a outra sequence.
NOME_SEQUENCE = "Presença Invisível"

# Rótulo exato do Step, conforme aparece no filtro lateral do Apollo.
# Exemplos: "Step: 1", "Step: 2", "Step: 3"
STEP_LABEL = "Step: 1"

# Pasta de destino do CSV exportado.
# None = usa a pasta Downloads padrão do Windows do usuário atual.
# Exemplo com caminho fixo: r"C:\Relatorios\Apollo"
DOWNLOAD_DIR = None

# False = abre o Chrome visível (recomendado para validação e primeiro uso)
# True  = roda em segundo plano (para agendamentos automatizados)
HEADLESS = False

# Tempo máximo (segundos) para aguardar cada elemento na página
TIMEOUT = 30

# -------------------------------------------------------------------------
# Execução
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  VISU Dados — Apollo Sequence Contacts Extractor")
    print("=" * 60)
    print(f"  Sequence : {NOME_SEQUENCE}")
    print(f"  Step     : {STEP_LABEL}")
    print()

    resultado = extrair_contatos_por_step(
        nome_sequence=NOME_SEQUENCE,
        step_label=STEP_LABEL,
        download_dir=DOWNLOAD_DIR,
        headless=HEADLESS,
        timeout=TIMEOUT,
    )

    print()
    if resultado:
        print("=" * 60)
        print("  Extração concluída com sucesso!")
        print(f"  Arquivo: {resultado}")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  Extração falhou.")
        print("  Verifique: apollo_sequence_contacts_extract.log")
        print("  Screenshots de erro estão na pasta python\\projects")
        print("=" * 60)
    print()
