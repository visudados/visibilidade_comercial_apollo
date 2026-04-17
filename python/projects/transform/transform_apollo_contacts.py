"""
transform_apollo_contacts.py - VISU Dados
==========================================

Módulo ETL (Transform).
Cria a Staging Area segura, captura apenas os arquivos extraídos na data corrente,
enriquece os dados e atualiza o Data Warehouse (Parquet).
"""

import os
import sys
import glob
import shutil
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

# -------------------------------------------------------------------------
# Configuração de logging
# -------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout), # Imprime no terminal (ecrã preto)
        logging.FileHandler("transform_apollo_contacts.log", encoding="utf-8") # Grava no ficheiro
    ]
)
log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Configurações de Diretórios e Datas
# -------------------------------------------------------------------------
# Pega a data e hora exatas de quando o script rodou
AGORA = datetime.now()
DATA_PASTA = AGORA.strftime("%Y_%m_%d")  # Formato para a pasta: 2026_04_17
DATA_COLUNA = AGORA.strftime("%Y-%m-%d") # Formato ISO para o PowerBI: 2026-04-17

PASTA_DOWNLOADS = Path.home() / "Downloads"

# Diretório principal de dados do projeto
PASTA_DATA = Path(__file__).resolve().parents[2] / "data"

# Cria a pasta cofre (Staging Area) com a data de hoje
PASTA_RAW = PASTA_DATA / f"raw_extract_apollo_{DATA_PASTA}"
os.makedirs(PASTA_RAW, exist_ok=True)

# Caminho do Parquet principal
CAMINHO_PARQUET = PASTA_DATA / "database_apollo.parquet"


def extrair_metadados_do_nome(nome_arquivo: str):
    """Extrai Consultor e Step a partir do nome do arquivo."""
    nome_base = os.path.basename(nome_arquivo).replace(".csv", "")
    
    if "_Step_" in nome_base:
        partes = nome_base.split("_Step_")
        consultor = partes[0].strip()
        step_num = partes[1].strip()
        return consultor, f"Step: {step_num}"
    
    return "Desconhecido", "Step: Desconhecido"


def capturar_arquivos_do_dia() -> list:
    """
    Busca na pasta Downloads apenas os CSVs do Apollo que foram 
    modificados/criados na data de HOJE, movendo-os para a pasta Raw.
    """
    padrao_busca = os.path.join(PASTA_DOWNLOADS, "*_Step_*.csv")
    todos_arquivos = glob.glob(padrao_busca)
    
    arquivos_movidos = []
    
    for arquivo in todos_arquivos:
        # Pega o timestamp de modificação do arquivo no Windows
        timestamp_modificacao = os.path.getmtime(arquivo)
        data_arquivo = datetime.fromtimestamp(timestamp_modificacao).strftime("%Y_%m_%d")
        
        # Filtro de Segurança: Só aceita se a data do arquivo for igual a hoje
        if data_arquivo == DATA_PASTA:
            nome_arquivo = os.path.basename(arquivo)
            destino = PASTA_RAW / nome_arquivo
            
            # Recorta do Downloads e cola na pasta Raw
            shutil.move(arquivo, destino)
            arquivos_movidos.append(destino)
            log.info(f"  [MOVE] Arquivo capturado: {nome_arquivo}")
        else:
            log.warning(f"  [IGNORE] Arquivo antigo ignorado: {os.path.basename(arquivo)} (Data: {data_arquivo})")
            
    return arquivos_movidos


def processar_transformacao():
    log.info("=" * 60)
    log.info("  INICIANDO TRANSFORMAÇÃO DE DADOS (ETL) ")
    log.info(f"  Data de Referência: {DATA_PASTA}")
    log.info("=" * 60)

    # 1. Passo Zero: Captura e Isolamento
    log.info("Buscando extrações do dia na pasta Downloads...")
    arquivos_para_processar = capturar_arquivos_do_dia()

    if not arquivos_para_processar:
        log.warning("Nenhum arquivo CSV válido (com data de hoje) foi encontrado para processar.")
        return

    log.info(f"Total de {len(arquivos_para_processar)} arquivos movidos para a área de Staging.")
    
    lista_dataframes = []

    # 2. Leitura e Enriquecimento dos dados
    log.info("Aplicando transformações e criando novas colunas...")
    for arquivo in arquivos_para_processar:
        consultor, step_label = extrair_metadados_do_nome(arquivo)
        
        # dtype=str previne que o Pandas corte zeros à esquerda de telefones
        df = pd.read_csv(arquivo, dtype=str) 
        
        df["Consultor"] = consultor
        df["Step"] = step_label
        df["Data da Extração"] = DATA_COLUNA
        
        df["Full Name"] = df["First Name"].fillna("") + " " + df["Last Name"].fillna("")
        df["Full Name"] = df["Full Name"].str.strip()
        
        lista_dataframes.append(df)

    # 3. Une todos os arquivos
    df_master = pd.concat(lista_dataframes, ignore_index=True)
    log.info(f"Unificação concluída. Total de contatos na carga de hoje: {len(df_master)}")

    # 4. Salva o CSV Master (Dentro da mesma pasta Raw, para ficar organizado por dia)
    nome_master = f"master_apollo_{DATA_PASTA}.csv"
    caminho_master = PASTA_RAW / nome_master
    df_master.to_csv(caminho_master, index=False, encoding="utf-8-sig")
    log.info(f"✅ CSV Master de backup salvo em: {caminho_master}")

    # 5. Atualiza o Parquet Principal (Histórico Unificado)
    if os.path.exists(CAMINHO_PARQUET):
        log.info("Base Parquet encontrada. Adicionando carga ao histórico...")
        df_historico = pd.read_parquet(CAMINHO_PARQUET)
        df_final = pd.concat([df_historico, df_master], ignore_index=True)
    else:
        log.info("Base Parquet não existe. Criando nova base...")
        df_final = df_master.copy()

    # =========================================================================
    # REGRAS DE NEGÓCIO SUSPENSAS (Descomente quando decidir usar a limpeza)
    # =========================================================================
    # log.info("Limpando dados antigos (Janela Deslizante)...")
    # limite_data = (AGORA - pd.Timedelta(days=40)).strftime("%Y-%m-%d")
    # df_final = df_final[df_final["Data da Extração"] >= limite_data]
    # =========================================================================

    # Salva o arquivo Parquet
    df_final.to_parquet(CAMINHO_PARQUET, index=False)
    log.info(f"✅ Parquet atualizado com sucesso em: {CAMINHO_PARQUET}")
    log.info(f"Total de linhas na base do Power BI agora: {len(df_final)}")
    log.info("=" * 60)


if __name__ == "__main__":
    processar_transformacao()