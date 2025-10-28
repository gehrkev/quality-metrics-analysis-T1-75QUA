FROM ubuntu:22.04

# Evitar prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Configurar mirrors mais rápidos (usar mirror brasileiro)
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://br.archive.ubuntu.com/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu/|http://br.archive.ubuntu.com/ubuntu/|g' /etc/apt/sources.list

# Instalação de dependências básicas
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    maven \
    gradle \
    git \
    wget \
    curl \
    unzip \
    python3 \
    python3-pip \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Configurar Java 11 como padrão (detecta arquitetura automaticamente)
RUN JAVA_ARCH=$(dpkg --print-architecture) && \
    echo "JAVA_HOME=/usr/lib/jvm/java-11-openjdk-${JAVA_ARCH}" >> /etc/environment && \
    ln -sf /usr/lib/jvm/java-11-openjdk-${JAVA_ARCH} /usr/lib/jvm/default-java

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Criar diretório de trabalho
WORKDIR /workspace

# Instalar Python packages para análise
RUN pip3 install --no-cache-dir \
    pydriller \
    pandas \
    matplotlib \
    seaborn \
    numpy \
    jupyter \
    requests

# Baixar CK metrics tool pré-compilado do Maven Central (versão 0.7.0)
RUN mkdir -p /tools/ck && \
    wget -O /tools/ck/ck.jar \
    https://repo1.maven.org/maven2/com/github/mauricioaniche/ck/0.7.0/ck-0.7.0-jar-with-dependencies.jar

# Instalar PMD (com retry)
RUN mkdir -p /tools/pmd && \
    (wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 3 \
    -O /tmp/pmd.zip https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.7.0/pmd-dist-7.7.0-bin.zip || \
    curl -L -o /tmp/pmd.zip https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.7.0/pmd-dist-7.7.0-bin.zip) && \
    unzip /tmp/pmd.zip -d /tools/ && \
    mv /tools/pmd-bin-7.7.0 /tools/pmd && \
    rm /tmp/pmd.zip

# Instalar SpotBugs (com retry)
RUN mkdir -p /tools/spotbugs && \
    (wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 3 \
    -O /tmp/spotbugs.tgz https://github.com/spotbugs/spotbugs/releases/download/4.8.6/spotbugs-4.8.6.tgz || \
    curl -L -o /tmp/spotbugs.tgz https://github.com/spotbugs/spotbugs/releases/download/4.8.6/spotbugs-4.8.6.tgz) && \
    tar -xzf /tmp/spotbugs.tgz -C /tools/ && \
    mv /tools/spotbugs-4.8.6 /tools/spotbugs && \
    rm /tmp/spotbugs.tgz

# Instalar find-sec-bugs plugin para SpotBugs do Maven Central
RUN mkdir -p /tools/spotbugs/plugin && \
    wget -O /tools/spotbugs/plugin/findsecbugs-plugin.jar \
    https://repo.maven.apache.org/maven2/com/h3xstream/findsecbugs/findsecbugs-plugin/1.13.0/findsecbugs-plugin-1.13.0.jar

# Instalar RefactoringMiner do Maven Central (versão 3.0.9 - all.jar inclui todas as dependências)
RUN mkdir -p /tools/refactoring-miner && \
    wget -O /tools/refactoring-miner/RefactoringMiner.jar \
    https://repo.maven.apache.org/maven2/com/github/tsantalis/refactoring-miner/3.0.9/refactoring-miner-3.0.9-all.jar

# Adicionar ferramentas ao PATH
ENV PATH="/tools/pmd/bin:/tools/spotbugs/bin:${PATH}"

# Criar script wrapper para CK (usa Java padrão - 11)
RUN echo '#!/bin/bash\n\
# Wrapper para executar CK\n\
java -jar /tools/ck/ck.jar "$@"\n\
' > /usr/local/bin/ck && chmod +x /usr/local/bin/ck

# Script auxiliar para facilitar uso das ferramentas
RUN echo '#!/bin/bash\n\
echo "=== Ferramentas disponíveis ==="\n\
echo ""\n\
echo "Java version:"\n\
echo "  - Java 11: $(java -version 2>&1 | head -n1)"\n\
echo ""\n\
echo "1. Buscar GitHub Releases:"\n\
echo "   fetch-github-releases <owner/repo> [--min-releases N] [--output formato]"\n\
echo "   Formatos: text, json, csv, tags"\n\
echo "   Exemplo: fetch-github-releases jhy/jsoup --output json"\n\
echo ""\n\
echo "2. CK Metrics:"\n\
echo "   ck <project-path> <output-path>"\n\
echo "   Extrai: WMC, DIT, NOC, CBO, LCOM, RFC, LOC"\n\
echo ""\n\
echo "3. PMD (análise estática):"\n\
echo "   pmd check -d <source-dir> -R rulesets/java/quickstart.xml -f text"\n\
echo ""\n\
echo "4. SpotBugs (detecção de bugs + segurança):"\n\
echo "   spotbugs -textui -effort:max -pluginList /tools/spotbugs/plugin/findsecbugs-plugin.jar <jar-or-class-files>"\n\
echo ""\n\
echo "5. RefactoringMiner:"\n\
echo "   java -jar /tools/refactoring-miner/RefactoringMiner.jar -a <repo-url> <branch>"\n\
echo ""\n\
echo "6. PyDriller (Python - análise de repositórios):"\n\
echo "   python3 -c \"from pydriller import Repository\""\n\
echo ""\n\
echo "Para mais informações, consulte o README.md"\n\
' > /usr/local/bin/show-tools && chmod +x /usr/local/bin/show-tools

# Criar estrutura de diretórios organizada (projects, results, scripts)
RUN mkdir -p /workspace/projects /workspace/results /workspace/scripts

# Copiar scripts auxiliares
COPY scripts/fetch_github_releases.py /usr/local/bin/fetch-github-releases
COPY scripts/analyze_all_releases.py /usr/local/bin/analyze-all-releases
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/fetch-github-releases /usr/local/bin/analyze-all-releases /usr/local/bin/entrypoint.sh

# Configurar volume padrão
VOLUME ["/workspace"]

# Configurar entrypoint para organizar workspace automaticamente
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Comando padrão
CMD ["/bin/bash"]
