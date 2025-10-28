#!/usr/bin/env python3
"""
Script para buscar releases do GitHub de qualquer repositório.
Uso: fetch_github_releases.py <owner/repo> [--min-releases N] [--output formato]
"""

import sys
import json
import requests
from datetime import datetime

def fetch_releases(owner, repo, min_releases=20):
    """
    Busca releases de um repositório GitHub via API.

    Args:
        owner: Dono do repositório (ex: 'jhy')
        repo: Nome do repositório (ex: 'jsoup')
        min_releases: Número mínimo de releases esperadas

    Returns:
        Lista de dicionários com informações das releases
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    params = {"per_page": 100}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        releases = response.json()

        # Filtrar releases válidas (não drafts, não pre-releases)
        valid_releases = [
            r for r in releases
            if not r.get('draft', False) and not r.get('prerelease', False)
        ]

        # Ordenar por data de publicação (mais antiga primeiro)
        valid_releases.sort(key=lambda r: r['published_at'])

        result = []
        for release in valid_releases:
            result.append({
                'tag_name': release['tag_name'],
                'name': release.get('name', release['tag_name']),
                'published_at': release['published_at'],
                'published_date': datetime.strptime(
                    release['published_at'],
                    '%Y-%m-%dT%H:%M:%SZ'
                ).strftime('%Y-%m-%d'),
                'url': release['html_url']
            })

        return result

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar releases: {e}", file=sys.stderr)
        sys.exit(1)

def print_releases(releases, format='text', min_releases=None):
    """Imprime releases no formato especificado."""

    if min_releases and len(releases) < min_releases:
        print(f"Aviso: Apenas {len(releases)} releases encontradas, mínimo esperado: {min_releases}",
              file=sys.stderr)

    if format == 'json':
        print(json.dumps(releases, indent=2))

    elif format == 'csv':
        print("tag_name,name,published_date,url")
        for r in releases:
            print(f"{r['tag_name']},{r['name']},{r['published_date']},{r['url']}")

    elif format == 'tags':
        # Apenas lista de tags, útil para scripts
        for r in releases:
            print(r['tag_name'])

    else:  # text
        print(f"Total de releases: {len(releases)}\n")
        for i, r in enumerate(releases, 1):
            print(f"{i:2d}. {r['tag_name']:20s} - {r['published_date']} - {r['name']}")

def main():
    if len(sys.argv) < 2:
        print("Uso: fetch_github_releases.py <owner/repo> [--min-releases N] [--output formato]")
        print("\nFormatos disponíveis: text, json, csv, tags")
        print("\nExemplo:")
        print("  fetch_github_releases.py jhy/jsoup --min-releases 20 --output json")
        sys.exit(1)

    # Parse argumentos
    repo_path = sys.argv[1]
    min_releases = 20
    output_format = 'text'

    for i in range(2, len(sys.argv)):
        if sys.argv[i] == '--min-releases' and i + 1 < len(sys.argv):
            min_releases = int(sys.argv[i + 1])
        elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]

    # Validar formato do repositório
    if '/' not in repo_path:
        print("Erro: Formato deve ser 'owner/repo' (ex: jhy/jsoup)", file=sys.stderr)
        sys.exit(1)

    owner, repo = repo_path.split('/', 1)

    # Buscar releases
    releases = fetch_releases(owner, repo, min_releases)

    # Imprimir resultado
    print_releases(releases, output_format, min_releases)

if __name__ == '__main__':
    main()
