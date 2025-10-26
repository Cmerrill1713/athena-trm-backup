# CI/CD Integration Examples
# =========================

## GitHub Actions

```yaml
name: RAG Quality Gates

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  rag-evaluation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install requests sentence-transformers
    
    - name: Start Weaviate
      run: |
        docker run -d --name weaviate \
          -p 8080:8080 \
          -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
          -e DEFAULT_VECTORIZER_MODULE=none \
          semitechnologies/weaviate:1.21.0
    
    - name: Wait for Weaviate
      run: |
        timeout 60 bash -c 'until curl -f http://localhost:8080/v1/meta; do sleep 2; done'
    
    - name: Create DocsV2 schema
      run: |
        curl -X POST "http://localhost:8080/v1/schema" \
          -H "Content-Type: application/json" \
          -d '{
            "class": "DocsV2",
            "description": "Unified documentation chunks with consistent 384-dim embeddings",
            "vectorizer": "text2vec-huggingface",
            "moduleConfig": {
              "text2vec-huggingface": {
                "model": "sentence-transformers/all-MiniLM-L6-v2"
              }
            },
            "properties": [
              {"name": "path", "dataType": ["text"]},
              {"name": "text", "dataType": ["text"]},
              {"name": "chunk_id", "dataType": ["int"]},
              {"name": "file_hash", "dataType": ["text"]}
            ]
          }'
    
    - name: Run RAG Delta Evaluation
      run: |
        make rag-delta-gates WEAVIATE_URL=http://localhost:8080
      env:
        WEAVIATE_URL: http://localhost:8080
    
    - name: Upload RAG Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: rag-evaluation-results
        path: artifacts/
    
    - name: Add RAG Summary to Job Summary
      if: always()
      run: |
        echo "## RAG Delta Summary" >> "$GITHUB_STEP_SUMMARY"
        cat artifacts/delta_bm25_vs_nearText_*.md >> "$GITHUB_STEP_SUMMARY" || true
```

## Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        WEAVIATE_URL = 'http://localhost:8080'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install requests sentence-transformers'
                sh 'docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.21.0'
                sh 'timeout 60 bash -c "until curl -f http://localhost:8080/v1/meta; do sleep 2; done"'
            }
        }
        
        stage('RAG Evaluation') {
            steps {
                sh 'make rag-delta-gates WEAVIATE_URL=http://localhost:8080'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'artifacts/**/*', fingerprint: true
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'artifacts',
                        reportFiles: 'delta_bm25_vs_nearText_*.md',
                        reportName: 'RAG Delta Report'
                    ])
                }
            }
        }
    }
    
    post {
        always {
            sh 'docker stop weaviate || true'
            sh 'docker rm weaviate || true'
        }
    }
}
```

## GitLab CI

```yaml
stages:
  - test

rag-evaluation:
  stage: test
  image: python:3.9
  
  services:
    - name: semitechnologies/weaviate:1.21.0
      alias: weaviate
  
  variables:
    WEAVIATE_URL: http://weaviate:8080
  
  before_script:
    - pip install requests sentence-transformers
    - timeout 60 bash -c 'until curl -f http://weaviate:8080/v1/meta; do sleep 2; done'
  
  script:
    - make rag-delta-gates WEAVIATE_URL=http://weaviate:8080
  
  artifacts:
    reports:
      junit: artifacts/delta_*.json
    paths:
      - artifacts/
    expire_in: 1 week
  
  after_script:
    - echo "## RAG Delta Summary" > $CI_PROJECT_DIR/rag_summary.md
    - cat artifacts/delta_bm25_vs_nearText_*.md >> $CI_PROJECT_DIR/rag_summary.md || true
```

## CircleCI

```yaml
version: 2.1

jobs:
  rag-evaluation:
    docker:
      - image: python:3.9
      - image: semitechnologies/weaviate:1.21.0
        environment:
          AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: true
    
    steps:
      - checkout
      
      - run:
          name: Install dependencies
          command: pip install requests sentence-transformers
      
      - run:
          name: Wait for Weaviate
          command: |
            timeout 60 bash -c 'until curl -f http://localhost:8080/v1/meta; do sleep 2; done'
      
      - run:
          name: Run RAG Evaluation
          command: make rag-delta-gates WEAVIATE_URL=http://localhost:8080
          environment:
            WEAVIATE_URL: http://localhost:8080
      
      - store_artifacts:
          path: artifacts/
          destination: rag-evaluation-results

workflows:
  version: 2
  rag-test:
    jobs:
      - rag-evaluation
```

## Azure DevOps

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  WEAVIATE_URL: 'http://localhost:8080'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.9'
  displayName: 'Use Python 3.9'

- script: |
    pip install requests sentence-transformers
  displayName: 'Install dependencies'

- script: |
    docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.21.0
    timeout 60 bash -c 'until curl -f http://localhost:8080/v1/meta; do sleep 2; done'
  displayName: 'Start Weaviate'

- script: |
    make rag-delta-gates WEAVIATE_URL=http://localhost:8080
  displayName: 'Run RAG Evaluation'
  env:
    WEAVIATE_URL: $(WEAVIATE_URL)

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: 'artifacts'
    artifactName: 'rag-evaluation-results'

- script: |
    echo "## RAG Delta Summary" > rag_summary.md
    cat artifacts/delta_bm25_vs_nearText_*.md >> rag_summary.md || true
  displayName: 'Generate Summary'
