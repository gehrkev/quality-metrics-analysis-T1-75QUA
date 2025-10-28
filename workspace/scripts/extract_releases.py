#!/usr/bin/env python3
"""
Script para extrair informações de releases usando PyDriller
"""

import sys
import os
from datetime import datetime
from pydriller import Repository
import pandas as pd
import json

def extract_releases(repo_path, output_dir):
    """
    Extrai informações sobre todas as releases (tags) do repositório
    """
    print(f"Analisando repositório: {repo_path}")

    releases = []

    # Iterar sobre commits que são releases
    for commit in Repository(repo_path, only_releases=True).traverse_commits():
        release_info = {
            'hash': commit.hash,
            'tag': ','.join(commit.branches) if commit.branches else 'unknown',
            'author': commit.author.name,
            'author_email': commit.author.email,
            'date': commit.author_date.isoformat(),
            'message': commit.msg.strip(),
            'files_modified': len(commit.modified_files),
            'insertions': commit.insertions,
            'deletions': commit.deletions,
            'lines_changed': commit.insertions + commit.deletions,
            'dmm_unit_size': commit.dmm_unit_size if hasattr(commit, 'dmm_unit_size') else None,
            'dmm_unit_complexity': commit.dmm_unit_complexity if hasattr(commit, 'dmm_unit_complexity') else None,
            'dmm_unit_interfacing': commit.dmm_unit_interfacing if hasattr(commit, 'dmm_unit_interfacing') else None
        }

        releases.append(release_info)
        print(f"  - Release encontrada: {release_info['tag']} ({release_info['date']})")

    if not releases:
        print("Nenhuma release encontrada no repositório")
        return

    # Criar DataFrame
    df = pd.DataFrame(releases)

    # Ordenar por data
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Salvar resultados
    os.makedirs(output_dir, exist_ok=True)

    # CSV
    csv_path = os.path.join(output_dir, 'releases.csv')
    df.to_csv(csv_path, index=False)
    print(f"\nCSV salvo em: {csv_path}")

    # JSON
    json_path = os.path.join(output_dir, 'releases.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(releases, f, indent=2, ensure_ascii=False)
    print(f"JSON salvo em: {json_path}")

    # Estatísticas básicas
    print(f"\n{'='*50}")
    print(f"Estatísticas das Releases")
    print(f"{'='*50}")
    print(f"Total de releases: {len(releases)}")
    print(f"Primeira release: {df.iloc[0]['tag']} ({df.iloc[0]['date'].date()})")
    print(f"Última release: {df.iloc[-1]['tag']} ({df.iloc[-1]['date'].date()})")
    print(f"\nMédia de arquivos modificados por release: {df['files_modified'].mean():.2f}")
    print(f"Média de linhas adicionadas por release: {df['insertions'].mean():.2f}")
    print(f"Média de linhas removidas por release: {df['deletions'].mean():.2f}")

    return df

def analyze_commits_between_releases(repo_path, output_dir):
    """
    Analisa commits entre releases para entender a evolução
    """
    print(f"\n{'='*50}")
    print(f"Analisando commits entre releases...")
    print(f"{'='*50}")

    # Obter todas as tags
    repo = Repository(repo_path)

    commits_data = []

    for commit in repo.traverse_commits():
        commit_info = {
            'hash': commit.hash,
            'date': commit.author_date.isoformat(),
            'author': commit.author.name,
            'files_modified': len(commit.modified_files),
            'insertions': commit.insertions,
            'deletions': commit.deletions,
            'is_merge': commit.merge,
        }
        commits_data.append(commit_info)

    df_commits = pd.DataFrame(commits_data)

    # Salvar
    commits_csv = os.path.join(output_dir, 'all_commits.csv')
    df_commits.to_csv(commits_csv, index=False)
    print(f"Commits salvos em: {commits_csv}")
    print(f"Total de commits: {len(commits_data)}")

    return df_commits

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_releases.py <nome-do-projeto>")
        print("Exemplo: python3 extract_releases.py meu-projeto")
        sys.exit(1)

    project_name = sys.argv[1]
    repo_path = f"/workspace/projetos/{project_name}"
    output_dir = f"/workspace/resultados/{project_name}"

    if not os.path.exists(repo_path):
        print(f"Erro: Projeto não encontrado em {repo_path}")
        sys.exit(1)

    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Erro: {repo_path} não é um repositório git")
        sys.exit(1)

    # Extrair releases
    try:
        df_releases = extract_releases(repo_path, output_dir)

        # Análise adicional de commits (opcional - pode demorar)
        if df_releases is not None and len(df_releases) >= 20:
            print(f"\nProjeto possui {len(df_releases)} releases (requisito: ≥ 20) ✓")
        elif df_releases is not None:
            print(f"\nATENÇÃO: Projeto possui apenas {len(df_releases)} releases (requisito: ≥ 20) ✗")

    except Exception as e:
        print(f"Erro durante análise: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
