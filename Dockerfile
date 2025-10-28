FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Mirrors BR e pacotes essenciais
RUN sed -i 's|archive.ubuntu.com|br.archive.ubuntu.com|g' /etc/apt/sources.list \
 && sed -i 's|security.ubuntu.com|br.archive.ubuntu.com|g' /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
    openjdk-11-jdk \
    openjdk-17-jdk \
    maven \
    gradle \
    git \
    wget \
    curl \
    unzip \
    python3 \
    python3-pip \
    graphviz \
    locales \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Locale pt_BR (acentos no Jupyter/Python)
RUN locale-gen pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8
ENV LANGUAGE=pt_BR:pt
ENV LC_ALL=pt_BR.UTF-8

# JAVA_HOME / PATH (padrão = Java 11 para o CK)
ENV JAVA_HOME_11=/usr/lib/jvm/java-11-openjdk-amd64
ENV JAVA_HOME_17=/usr/lib/jvm/java-17-openjdk-amd64
ENV JAVA_HOME=$JAVA_HOME_11
ENV PATH=$JAVA_HOME/bin:$PATH

WORKDIR /workspace

# Python libs
RUN pip3 install --no-cache-dir \
    pydriller \
    pandas \
    matplotlib \
    seaborn \
    numpy \
    jupyter

# CK 0.7.0 (jar com dependências)
RUN mkdir -p /tools/ck \
 && wget -O /tools/ck/ck.jar \
    https://repo1.maven.org/maven2/com/github/mauricioaniche/ck/0.7.0/ck-0.7.0-jar-with-dependencies.jar

# PMD 7.7.0 (requer Java 17)
RUN mkdir -p /tools/pmd \
 && (wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 3 \
      -O /tmp/pmd.zip https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.7.0/pmd-dist-7.7.0-bin.zip \
     || curl -L -o /tmp/pmd.zip https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.7.0/pmd-dist-7.7.0-bin.zip) \
 && unzip /tmp/pmd.zip -d /tools/ \
 && mv /tools/pmd-bin-7.7.0 /tools/pmd \
 && rm /tmp/pmd.zip

# SpotBugs 4.8.6 (+ FindSecBugs) — roda em Java 8+, ok com 11
RUN mkdir -p /tools/spotbugs \
 && (wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 3 \
      -O /tmp/spotbugs.tgz https://github.com/spotbugs/spotbugs/releases/download/4.8.6/spotbugs-4.8.6.tgz \
     || curl -L -o /tmp/spotbugs.tgz https://github.com/spotbugs/spotbugs/releases/download/4.8.6/spotbugs-4.8.6.tgz) \
 && tar -xzf /tmp/spotbugs.tgz -C /tools/ \
 && mv /tools/spotbugs-4.8.6 /tools/spotbugs \
 && rm /tmp/spotbugs.tgz \
 && mkdir -p /tools/spotbugs/plugin \
 && (wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 3 \
      -O /tools/spotbugs/plugin/findsecbugs-plugin.jar \
      https://github.com/find-sec-bugs/find-sec-bugs/releases/download/version-1.13.0/findsecbugs-plugin-1.13.0.jar \
     || curl -L -o /tools/spotbugs/plugin/findsecbugs-plugin.jar \
      https://github.com/find-sec-bugs/find-sec-bugs/releases/download/version-1.13.0/findsecbugs-plugin-1.13.0.jar)

# RefactoringMiner 3.0.9 (requer Java 17)
RUN mkdir -p /tools/refactoring-miner \
 && (wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 3 \
      -O /tools/refactoring-miner/RefactoringMiner.jar \
      https://github.com/tsantalis/RefactoringMiner/releases/download/3.0.9/RefactoringMiner-3.0.9.jar \
     || curl -L -o /tools/refactoring-miner/RefactoringMiner.jar \
      https://github.com/tsantalis/RefactoringMiner/releases/download/3.0.9/RefactoringMiner-3.0.9.jar)

# Wrappers:
# - ck: usa Java 11 (padrão)
# - pmd7: força Java 17
# - refminer: força Java 17
# - spotbugs: usa Java 11 (ok)
RUN printf '%s\n' '#!/bin/bash' \
 'exec java -jar /tools/ck/ck.jar "$@"' > /usr/local/bin/ck \
 && chmod +x /usr/local/bin/ck \
 && printf '%s\n' '#!/bin/bash' \
 'export JAVA_HOME='"$JAVA_HOME_17" \
 'export PATH="$JAVA_HOME/bin:'"$PATH"'"' \
 'exec /tools/pmd/bin/run.sh "$@"' > /usr/local/bin/pmd7 \
 && chmod +x /usr/local/bin/pmd7 \
 && printf '%s\n' '#!/bin/bash' \
 'export JAVA_HOME='"$JAVA_HOME_17" \
 'export PATH="$JAVA_HOME/bin:'"$PATH"'"' \
 'exec java -jar /tools/refactoring-miner/RefactoringMiner.jar "$@"' > /usr/local/bin/refminer \
 && chmod +x /usr/local/bin/refminer

# Adiciona binários úteis ao PATH
ENV PATH=/tools/pmd/bin:/tools/spotbugs/bin:$PATH

# Diretórios padrões
RUN mkdir -p /workspace/results
VOLUME ["/workspace"]

# Sanity check no build (mostra versões)
RUN bash -lc 'echo "Java default:" && java -version && echo && echo "Maven:" && mvn -version && echo && echo "Gradle:" && gradle -version'

CMD ["/bin/bash"]
