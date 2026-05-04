#!/usr/bin/env python3
# backup.py - Script de Backup Automático do Banco de Dados
# Executa manualmente ou configure no Agendador de Tarefas do Windows.
#
# USO MANUAL: python backup.py
# AGENDAMENTO (Windows): Agendar via "Agendador de Tarefas" para rodar diariamente.

import os
import shutil
import datetime
import glob

# ─────────────────────────────────────────────────────────────
# CONFIGURAÇÕES — Ajuste conforme necessário
# ─────────────────────────────────────────────────────────────
# Caminho do arquivo de banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "almoxarifado.db")

# Destino do backup (pode ser um pen drive ou pasta de rede)
# Exemplos:
#   Windows pen drive: "D:\\Backup_PM\\"
#   Pasta local:       "./backups/"
#   Rede interna:      "\\\\SERVIDOR\\Backup\\PM\\"
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

# Quantos backups manter (os mais antigos serão removidos automaticamente)
MAX_BACKUPS = 30


# ─────────────────────────────────────────────────────────────
# EXECUÇÃO DO BACKUP
# ─────────────────────────────────────────────────────────────
def fazer_backup():
    agora = datetime.datetime.now()
    timestamp = agora.strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"almoxarifado_backup_{timestamp}.db"

    print("=" * 50)
    print("  BACKUP DO SISTEMA DE ALMOXARIFADO PM")
    print(f"  Data/Hora: {agora.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)

    # Verifica se o banco de dados existe
    if not os.path.exists(DB_PATH):
        print(f"[ERRO] Banco de dados não encontrado em: {DB_PATH}")
        print("       Certifique-se de que o sistema foi iniciado ao menos uma vez.")
        return False

    # Cria a pasta de backup se não existir
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except Exception as e:
        print(f"[ERRO] Não foi possível criar a pasta de backup: {e}")
        return False

    # Copia o arquivo do banco
    destino = os.path.join(BACKUP_DIR, nome_arquivo)
    try:
        shutil.copy2(DB_PATH, destino)
        tamanho = os.path.getsize(destino) / 1024
        print(f"[OK] Backup criado: {destino}")
        print(f"     Tamanho: {tamanho:.1f} KB")
    except Exception as e:
        print(f"[ERRO] Falha ao copiar o banco: {e}")
        return False

    # Remove backups antigos (mantém os MAX_BACKUPS mais recentes)
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "almoxarifado_backup_*.db")))
    if len(backups) > MAX_BACKUPS:
        remover = backups[:len(backups) - MAX_BACKUPS]
        for arq in remover:
            try:
                os.remove(arq)
                print(f"[INFO] Backup antigo removido: {os.path.basename(arq)}")
            except Exception as e:
                print(f"[AVISO] Não foi possível remover {arq}: {e}")

    total = len(glob.glob(os.path.join(BACKUP_DIR, "almoxarifado_backup_*.db")))
    print(f"\n[INFO] Total de backups armazenados: {total}/{MAX_BACKUPS}")
    print("[OK] Backup concluído com sucesso!")
    return True


if __name__ == "__main__":
    sucesso = fazer_backup()
    if not sucesso:
        print("\n[ATENÇÃO] O backup NÃO foi realizado. Verifique os erros acima.")
    input("\nPressione ENTER para fechar...")
