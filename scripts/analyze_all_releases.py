#!/usr/bin/env python3
"""
Script para análise completa de todas as releases de um projeto Java.
Executa CK, PMD, SpotBugs, RefactoringMiner em todas as releases.
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def run_command(cmd, cwd=None, capture_output=False):
    """Executa um comando shell."""
    print(f"[CMD] {cmd}")
    if capture_output:
        result = subprocess.run(cmd, shell=True, cwd=cwd,
                              capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    else:
        result = subprocess.run(cmd, shell=True, cwd=cwd)
        return result.returncode, None, None

def fetch_releases(owner, repo):
    """Busca releases usando o script fetch-github-releases."""
    print(f"\n{'='*60}")
    print(f"Buscando releases de {owner}/{repo}...")
    print(f"{'='*60}\n")

    cmd = f"fetch-github-releases {owner}/{repo} --output json"
    returncode, stdout, stderr = run_command(cmd, capture_output=True)

    if returncode != 0:
        print(f"Erro ao buscar releases: {stderr}")
        sys.exit(1)

    releases = json.loads(stdout)
    print(f"✓ Encontradas {len(releases)} releases\n")
    return releases

def clone_or_update_repo(repo_url, project_dir):
    """Clona ou atualiza o repositório."""
    if os.path.exists(project_dir):
        print(f"Repositório já existe em {project_dir}, atualizando...")
        run_command("git fetch --all --tags", cwd=project_dir)
    else:
        print(f"Clonando repositório {repo_url}...")
        run_command(f"git clone {repo_url} {project_dir}")

    # Configurar safe directory
    run_command(f"git config --global --add safe.directory {project_dir}")

def checkout_release(project_dir, tag_name):
    """Faz checkout de uma release específica."""
    print(f"  → Checkout {tag_name}")
    # Limpar completamente o working tree (duas vezes para garantir)
    run_command("git clean -fdx", cwd=project_dir)
    run_command("git clean -fdx", cwd=project_dir)  # Segunda vez para arquivos problemáticos
    run_command("git reset --hard HEAD", cwd=project_dir)
    # Fazer checkout com force
    returncode, stdout, stderr = run_command(f"git checkout -f {tag_name}", cwd=project_dir, capture_output=True)
    if returncode != 0:
        # Se ainda falhou, pode ser problema de case-sensitivity (macOS)
        # Remover arquivos manualmente e tentar novamente
        print(f"    ℹ Limpando arquivos problemáticos...")
        run_command("find . -name '*.java' -type f ! -path './.git/*' -delete", cwd=project_dir)
        returncode, stdout, stderr = run_command(f"git checkout -f {tag_name}", cwd=project_dir, capture_output=True)
        if returncode != 0:
            print(f"    ⚠ ERRO no checkout: {stderr}")
            return False
    # Limpar novamente após checkout para remover qualquer artefato
    run_command("git clean -fdx", cwd=project_dir)
    return True

def build_project(project_dir):
    """Compila o projeto (Maven ou Gradle)."""
    print(f"  → Compilando projeto...")

    # Detectar tipo de build
    if os.path.exists(os.path.join(project_dir, "pom.xml")):
        cmd = "mvn clean package -DskipTests -q"
    elif os.path.exists(os.path.join(project_dir, "build.gradle")) or \
         os.path.exists(os.path.join(project_dir, "build.gradle.kts")):
        cmd = "gradle clean build -x test -q"
    else:
        print("    ⚠ Nenhum sistema de build detectado (Maven/Gradle)")
        return False

    returncode, _, stderr = run_command(cmd, cwd=project_dir, capture_output=True)
    if returncode != 0:
        print(f"    ⚠ Falha na compilação: {stderr[:200]}")
        return False

    print("    ✓ Compilação concluída")
    return True

def run_ck_analysis(project_dir, output_dir):
    """Executa análise CK."""
    print(f"  → Executando CK Metrics...")
    ck_output = os.path.join(output_dir, "ck")
    os.makedirs(ck_output, exist_ok=True)

    # CK gera os arquivos no diretório de onde é executado (cwd)
    # Por isso executamos a partir do diretório de saída
    cmd = f"ck {project_dir} ."
    returncode, _, _ = run_command(cmd, cwd=ck_output, capture_output=True)

    if returncode == 0:
        # Verificar se os arquivos foram gerados
        expected_files = ['class.csv', 'method.csv', 'field.csv', 'variable.csv']
        files_found = [f for f in expected_files if os.path.exists(os.path.join(ck_output, f))]

        if files_found:
            print(f"    ✓ CK Metrics salvo em {ck_output} ({len(files_found)} arquivos)")
            return True
        else:
            print(f"    ⚠ CK executado mas nenhum arquivo gerado")
            return False
    else:
        print(f"    ⚠ Erro ao executar CK")
        return False

def run_pmd_analysis(project_dir, output_dir):
    """Executa análise PMD."""
    print(f"  → Executando PMD...")

    src_dir = os.path.join(project_dir, "src")
    if not os.path.exists(src_dir):
        print(f"    ⚠ Diretório src não encontrado")
        return False

    pmd_output = os.path.join(output_dir, "pmd-report.csv")
    pmd_log = os.path.join(output_dir, "pmd.log")

    # PMD retorna exit code != 0 quando encontra problemas, por isso o '|| true'
    cmd = f"/tools/pmd/pmd-bin-7.7.0/bin/pmd check -d {src_dir} -R rulesets/java/quickstart.xml -f csv -r {pmd_output} 2>&1 | tee {pmd_log} || true"

    returncode, stdout, stderr = run_command(cmd, capture_output=True)

    # Salvar log sempre
    with open(pmd_log, 'w') as f:
        f.write(stdout if stdout else "")
        if stderr:
            f.write("\n" + stderr)

    if os.path.exists(pmd_output) and os.path.getsize(pmd_output) > 0:
        print(f"    ✓ PMD report salvo em {pmd_output}")
        return True
    else:
        print(f"    ℹ PMD executado (nenhum problema encontrado ou relatório vazio)")
        print(f"      Log: {pmd_log}")
        return True  # Considerar sucesso mesmo sem problemas

def run_spotbugs_analysis(project_dir, output_dir):
    """Executa análise SpotBugs com find-sec-bugs."""
    print(f"  → Executando SpotBugs + find-sec-bugs...")

    # Procurar JARs compilados (excluir -sources, -javadoc, -tests)
    jar_files = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.jar') and ('target' in root or 'build' in root):
                # Excluir JARs de fontes, javadoc, exemplos, testes
                if not any(x in file for x in ['-sources', '-javadoc', '-examples', '-tests', '-test']):
                    jar_path = os.path.join(root, file)
                    jar_files.append(jar_path)

    if not jar_files:
        print(f"    ⚠ Nenhum JAR encontrado para análise")
        return False

    print(f"      Analisando {len(jar_files)} JAR(s)...")

    spotbugs_output = os.path.join(output_dir, "spotbugs-report.xml")
    spotbugs_log = os.path.join(output_dir, "spotbugs.log")

    # Limitar a 3 JARs principais para não demorar muito
    jar_list = " ".join(jar_files[:3])

    cmd = f"/tools/spotbugs/bin/spotbugs -textui -effort:max " \
          f"-pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar " \
          f"-xml:withMessages -output {spotbugs_output} {jar_list} 2>&1 | tee {spotbugs_log} || true"

    returncode, stdout, stderr = run_command(cmd, capture_output=True)

    # Salvar log
    with open(spotbugs_log, 'w') as f:
        f.write(stdout if stdout else "")
        if stderr:
            f.write("\n" + stderr)

    if os.path.exists(spotbugs_output) and os.path.getsize(spotbugs_output) > 100:
        print(f"    ✓ SpotBugs report salvo em {spotbugs_output}")
        return True
    else:
        print(f"    ℹ SpotBugs executado (relatório vazio ou nenhum bug encontrado)")
        print(f"      Log: {spotbugs_log}")
        return True  # Considerar sucesso

def analyze_release(project_dir, release, results_base_dir):
    """Analisa uma release completa."""
    tag_name = release['tag_name']
    date = release['published_date']

    print(f"\n{'─'*60}")
    print(f"Analisando: {tag_name} ({date})")
    print(f"{'─'*60}")

    # Criar diretório para resultados desta release
    release_dir = os.path.join(results_base_dir, tag_name)
    os.makedirs(release_dir, exist_ok=True)

    # Salvar metadata da release
    metadata_file = os.path.join(release_dir, "metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(release, f, indent=2)

    # Checkout da release
    checkout_success = checkout_release(project_dir, tag_name)
    if not checkout_success:
        print(f"    ⚠ Pulando análise (checkout falhou)")
        return {
            'tag_name': tag_name,
            'date': date,
            'ck': False,
            'pmd': False,
            'spotbugs': False,
            'error': 'Checkout failed'
        }

    # Compilar projeto
    build_success = build_project(project_dir)

    # Executar análises
    results = {
        'tag_name': tag_name,
        'date': date,
        'ck': run_ck_analysis(project_dir, release_dir),
        'pmd': run_pmd_analysis(project_dir, release_dir),
        'spotbugs': False
    }

    # SpotBugs apenas se compilação teve sucesso (habilitado agora!)
    if build_success:
        results['spotbugs'] = run_spotbugs_analysis(project_dir, release_dir)
    else:
        print(f"    ⚠ Pulando SpotBugs (compilação falhou)")

    # Salvar resumo dos resultados
    summary_file = os.path.join(release_dir, "summary.json")
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)

    return results

def run_refactoring_miner(project_dir, results_base_dir):
    """Executa RefactoringMiner em todo o repositório."""
    print(f"\n{'='*60}")
    print(f"Executando RefactoringMiner em todo o repositório...")
    print(f"{'='*60}\n")

    output_file = os.path.join(results_base_dir, "refactorings-all.json")
    cmd = f"/tools/refactoring-miner/refactoring-miner.sh " \
          f"-a {project_dir} {output_file} || true"

    returncode, _, _ = run_command(cmd, capture_output=True)

    if returncode == 0 and os.path.exists(output_file):
        print(f"✓ RefactoringMiner completado: {output_file}\n")
        return True
    else:
        print(f"⚠ RefactoringMiner falhou ou não gerou saída\n")
        return False

def generate_summary_report(results_base_dir, all_results):
    """Gera relatório resumido de todas as análises."""
    report_file = os.path.join(results_base_dir, "analysis-summary.txt")

    with open(report_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("RESUMO DA ANÁLISE DE RELEASES\n")
        f.write("="*70 + "\n\n")
        f.write(f"Total de releases analisadas: {len(all_results)}\n\n")

        f.write("Resultados por release:\n")
        f.write("-"*70 + "\n")
        for result in all_results:
            f.write(f"\n{result['tag_name']} ({result['date']}):\n")
            f.write(f"  CK Metrics:  {'✓' if result['ck'] else '✗'}\n")
            f.write(f"  PMD:         {'✓' if result['pmd'] else '✗'}\n")
            f.write(f"  SpotBugs:    {'✓' if result['spotbugs'] else '✗'}\n")

        # Estatísticas
        ck_success = sum(1 for r in all_results if r['ck'])
        pmd_success = sum(1 for r in all_results if r['pmd'])
        spotbugs_success = sum(1 for r in all_results if r['spotbugs'])

        f.write("\n" + "="*70 + "\n")
        f.write("ESTATÍSTICAS:\n")
        f.write("-"*70 + "\n")
        f.write(f"CK Metrics bem-sucedidos:  {ck_success}/{len(all_results)}\n")
        f.write(f"PMD bem-sucedidos:         {pmd_success}/{len(all_results)}\n")
        f.write(f"SpotBugs bem-sucedidos:    {spotbugs_success}/{len(all_results)}\n")

    print(f"\n✓ Relatório resumido salvo em: {report_file}\n")

def main():
    if len(sys.argv) < 2:
        print("Uso: analyze_all_releases.py <owner/repo> [--limit N]")
        print("\nExemplo:")
        print("  analyze_all_releases.py jhy/jsoup")
        print("  analyze_all_releases.py jhy/jsoup --limit 5")
        sys.exit(1)

    repo_path = sys.argv[1]
    limit = None

    if '--limit' in sys.argv:
        limit_idx = sys.argv.index('--limit')
        if limit_idx + 1 < len(sys.argv):
            limit = int(sys.argv[limit_idx + 1])

    if '/' not in repo_path:
        print("Erro: Formato deve ser 'owner/repo'")
        sys.exit(1)

    owner, repo = repo_path.split('/', 1)

    # Configurar diretórios organizados (estrutura: /workspace/projects, /workspace/results)
    workspace = "/workspace"
    project_name = repo
    project_dir = os.path.join(workspace, "projects", project_name)
    results_base_dir = os.path.join(workspace, "results", project_name)

    # Criar diretórios necessários
    os.makedirs(os.path.join(workspace, "projects"), exist_ok=True)
    os.makedirs(results_base_dir, exist_ok=True)

    # Buscar releases
    releases = fetch_releases(owner, repo)

    if limit:
        print(f"Limitando análise às primeiras {limit} releases\n")
        releases = releases[:limit]

    # Clonar/atualizar repositório
    repo_url = f"https://github.com/{owner}/{repo}.git"
    clone_or_update_repo(repo_url, project_dir)

    # Analisar cada release
    all_results = []
    for i, release in enumerate(releases, 1):
        print(f"\n[{i}/{len(releases)}]", end=" ")
        result = analyze_release(project_dir, release, results_base_dir)
        all_results.append(result)

    # RefactoringMiner em todo o repositório
    run_refactoring_miner(project_dir, results_base_dir)

    # Gerar relatório resumido
    generate_summary_report(results_base_dir, all_results)

    print(f"\n{'='*70}")
    print(f"ANÁLISE COMPLETA!")
    print(f"{'='*70}")
    print(f"Resultados salvos em: {results_base_dir}")
    print(f"Total de releases analisadas: {len(all_results)}")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
