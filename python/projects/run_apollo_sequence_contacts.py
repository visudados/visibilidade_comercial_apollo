"""
run_apollo_sequence_contacts.py - VISU Dados
=============================================

Script de execução (Entry Point) para a extração em lote de contatos
de múltiplas Sequences e múltiplos Steps no Apollo.io.

Este arquivo serve como o painel de configuração da automação.
Para adicionar novas pessoas ou etapas, basta alterar as listas abaixo.
"""

import sys
from pathlib import Path

# Garante que o Python encontre os módulos internos do projeto
sys.path.append(str(Path(__file__).resolve().parents[1]))

from projects.extract.extract_apollo_sequence_contacts import orquestrar_extracao_sequences

# =========================================================================
# CONFIGURAÇÕES DA AUTOMAÇÃO
# =========================================================================

# 1. Pessoas / Sequences
# Use apenas o identificador único para evitar problemas com aspas ou emojis.
NOMES_SEQUENCES = [
    "[André]",
    "[Antonio]",
    "[Alessandro]",
    # Adicione outras pessoas aqui embaixo seguindo o mesmo padrão:
    # "[NomeDaPessoa]",
]

# 2. Etapas (Steps)
# Lista exata de como o rótulo aparece no filtro do Apollo.
STEPS_LABELS = [
    "Step: 1",
    "Step: 2",
    "Step: 4",
    "Step: 5",
    "Step: 6"
]

# 3. Configurações de Ambiente
# Se None, o robô usará a pasta 'Downloads' padrão do seu Windows.
DOWNLOAD_DIR = None

# Se True, o Chrome roda escondido (em background).
# IMPORTANTE: Deixe False para conseguir fazer o login manual na primeira vez!
HEADLESS = False

# Tempo máximo (em segundos) que o robô espera um elemento ou página carregar.
TIMEOUT = 30

# =========================================================================
# EXECUÇÃO PRINCIPAL
# =========================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  INICIANDO AUTOMAÇÃO VISU - APOLLO (LOTE)")
    print("=" * 60)
    print(f"  Sequences alvo: {len(NOMES_SEQUENCES)}")
    print(f"  Steps por alvo: {len(STEPS_LABELS)}")
    print("=" * 60)

    # Chama a Camada 1 (Top Level) da nossa arquitetura
    resultados = orquestrar_extracao_sequences(
        nomes_sequences=NOMES_SEQUENCES,
        step_labels=STEPS_LABELS,
        download_dir=DOWNLOAD_DIR,
        headless=HEADLESS,
        timeout=TIMEOUT,
    )

    # =========================================================================
    # RELATÓRIO FINAL (UX)
    # =========================================================================
    print("\n" + "=" * 60)
    print("  RESUMO DA EXTRAÇÃO CONCLUÍDA")
    print("=" * 60)

    if not resultados:
        print("  ⚠️ Nenhum arquivo foi extraído. Verifique os logs para erros.")
    else:
        total_arquivos = sum(len(arquivos) for arquivos in resultados.values())
        print(f"  ✅ Total de arquivos baixados com sucesso: {total_arquivos}\n")

        # Imprime os resultados organizados por pessoa
        for pessoa, arquivos in resultados.items():
            print(f"  👤 {pessoa}: {len(arquivos)} steps extraídos")
            for arq in arquivos:
                # Extrai apenas o nome do arquivo final para o console não ficar poluído
                nome_arquivo = Path(arq).name
                print(f"     -> {nome_arquivo}")

    print("=" * 60)
    print("  A operação foi finalizada. Pode fechar esta janela.")
    print("=" * 60)