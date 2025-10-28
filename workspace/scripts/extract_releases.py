#!/usr/bin/env python3
"""
Extrai informações de releases:
- Modo padrão: GitHub Releases (API) -> exatamente o que aparece em "Releases" (ex.: 20 no jsoup)
- Fallback (--source pydriller): tags de Git via PyDriller (only_releases=True)

Uso:
  python3 extract_releases.py <nome-projeto> [--source github|pydriller]

Requer:
  - Repo clonado em /workspace/projetos/<nome-projeto>
  - Internet para modo github
  - (Opcional) export GITHUB_TOKEN=seu_token   # para evitar rate limit
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timezone
import pandas as pd

def run(cmd, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()

def parse_owner_repo_from_remote(repo_path):
    # pega origin
    url = run(["git", "remote", "get-url", "origin"], cwd=repo_path)
    # padrões comuns
    # https://github.com/jhy/jsoup.git
    # git@github.com:jhy/jsoup.git
    url = url.replace(".git", "")
    if "github.com" in url:
        if url.startswith("git@github.com:"):
            owner_repo = url.split("git@github.com:")[1]
        else:
            owner_repo = url.split("github.com/")[1]
        parts = owner_repo.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
    raise RuntimeError(f"Não consegui extrair owner/repo a partir da URL remota: {url}")

def fetch_github_releases(owner, repo, token=None):
    import requests
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    releases = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=100&page={page}"
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        releases.extend(data)
        page += 1
    return releases

def map_tag_to_hash(repo_path, tag):
    # tenta pegar o commit da tag (funciona para release/tag normal)
    for cmd in (["git", "rev-list", "-n", "1", tag],
                ["git", "rev-parse", tag]):
        try:
            return run(cmd, cwd=repo_path)
        except subprocess.CalledProcessError:
            continue
    return None

def extract_releases_github(repo_path, output_dir):
    print(f"Analisando (GitHub Releases) repositório: {repo_path}")
    owner, repo = parse_owner_repo_from_remote(repo_path)
    token = os.environ.get("GITHUB_TOKEN")

    gh_rels = fetch_github_releases(owner, repo, token)
    if not gh_rels:
        print("Nenhuma release do GitHub encontrada. (Verifique internet/token)")
        return None

    rows = []
    for rel in gh_rels:
        # ignora drafts/prereleases se quiser só “publicadas estáveis”
        # (se quiser incluir pre-releases, remova o if)
        # keep_prerelease = True  # opcional
        # if not keep_prerelease and rel.get("prerelease", False):
        #     continue

        tag = rel.get("tag_name") or ""
        published_at = rel.get("published_at")
        name = rel.get("name") or ""
        body = rel.get("body") or ""

        # commit hash da tag (precisa existir localmente)
        git_hash = map_tag_to_hash(repo_path, tag)

        # published_at pode ser None em releases antigas – tenta created_at
        dt_str = published_at or rel.get("created_at")
        try:
            date = datetime.fromisoformat(dt_str.replace("Z","+00:00"))
        except Exception:
            date = None

        rows.append({
            "hash": git_hash or "",
            "tag": tag,
            "author": "",                 # a API de Releases não traz autor do commit
            "author_email": "",
            "date": date.isoformat() if date else "",
            "message": (name or "").strip(),   # título da release
            "notes": (body or "").strip(),
            "files_modified": None,
            "insertions": None,
            "deletions": None,
            "lines_changed": None,
            "dmm_unit_size": None,
            "dmm_unit_complexity": None,
            "dmm_unit_interfacing": None,
        })

    df = pd.DataFrame(rows)
    # mantém só releases com tag resolvida localmente (opcional)
    # df = df[df["hash"] != ""]

    # ordena por data
    if "date" in df and df["date"].notna().any():
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "releases.csv")
    json_path = os.path.join(output_dir, "releases.json")

    cols = ["hash","tag","author","author_email","date","message","notes",
            "files_modified","insertions","deletions","lines_changed",
            "dmm_unit_size","dmm_unit_complexity","dmm_unit_interfacing"]
    df = df[cols]

    df.to_csv(csv_path, index=False)
    
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, pd.Timestamp):
                r[k] = v.isoformat()

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print("\n==================================================")
    print("Estatísticas das GitHub Releases")
    print("==================================================")
    print(f"Total de releases: {len(df)}")
    if len(df) > 0:
        first = df.iloc[0]
        last  = df.iloc[-1]
        print(f"Primeira release: {first['tag']} ({str(first['date'])[:10]})")
        print(f"Última release: {last['tag']} ({str(last['date'])[:10]})")

    return df

def extract_releases_pydriller(repo_path, output_dir):
    # Fallback: usa tags de Git via PyDriller
    print(f"Analisando (PyDriller/tags) repositório: {repo_path}")
    from pydriller import Repository

    releases = []
    for commit in Repository(repo_path, only_releases=True).traverse_commits():
        releases.append({
            "hash": commit.hash,
            # CORREÇÃO: tags (não branches)
            "tag": ",".join(getattr(commit, "tags", []) or []) or "unknown",
            "author": commit.author.name,
            "author_email": commit.author.email,
            "date": commit.author_date.isoformat(),
            "message": commit.msg.strip(),
            "notes": "",
            "files_modified": len(commit.modified_files),
            "insertions": commit.insertions,
            "deletions": commit.deletions,
            "lines_changed": commit.insertions + commit.deletions,
            "dmm_unit_size": getattr(commit, "dmm_unit_size", None),
            "dmm_unit_complexity": getattr(commit, "dmm_unit_complexity", None),
            "dmm_unit_interfacing": getattr(commit, "dmm_unit_interfacing", None),
        })

    if not releases:
        print("Nenhuma release (tag) encontrada")
        return None

    df = pd.DataFrame(releases)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "releases.csv")
    json_path = os.path.join(output_dir, "releases.json")

    cols = ["hash","tag","author","author_email","date","message","notes",
            "files_modified","insertions","deletions","lines_changed",
            "dmm_unit_size","dmm_unit_complexity","dmm_unit_interfacing"]
    df = df[cols]
    df.to_csv(csv_path, index=False)
    # Converter Timestamps para string ISO antes de salvar
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, pd.Timestamp):
                r[k] = v.isoformat()

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print("\n==================================================")
    print("Estatísticas (tags via PyDriller)")
    print("==================================================")
    print(f"Total de tags (consideradas releases): {len(df)}")
    print(f"Primeira: {df.iloc[0]['tag']} ({str(df.iloc[0]['date'])[:10]})")
    print(f"Última: {df.iloc[-1]['tag']} ({str(df.iloc[-1]['date'])[:10]})")
    return df

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_releases.py <nome-projeto> [--source github|pydriller]")
        sys.exit(1)

    project_name = sys.argv[1]
    source = "github"
    if len(sys.argv) >= 3 and sys.argv[2].startswith("--source"):
        _, val = sys.argv[2].split("=", 1) if "=" in sys.argv[2] else (None, None)
        if val in ("github","pydriller"):
            source = val

    repo_path = f"/workspace/projetos/{project_name}"
    output_dir = f"/workspace/resultados/{project_name}"

    if not os.path.isdir(repo_path) or not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Erro: {repo_path} não é um repositório Git válido")
        sys.exit(1)

    try:
        if source == "github":
            df = extract_releases_github(repo_path, output_dir)
        else:
            df = extract_releases_pydriller(repo_path, output_dir)

        if df is not None:
            n = len(df)
            alvo = "GitHub Releases" if source == "github" else "tags"
            print(f"\nProjeto possui {n} {alvo}.")
    except Exception as e:
        print(f"Erro durante análise: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
