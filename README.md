# Manufacturing Guidance Search Bot
---
## Overview
This repository contains a Retrieval Augmented Generation chat bot tool intended for use by the GPS team for Q&A against their playbook information.
Components could be applied for other use cases, as a majority of the build is general purpose.

---
## Key Features
- Chat interface allowing users to query information, follow up on previous queries, reload previous chat instances.
- Scripts to create and evaluate new RAG pipelines

---
## Development
### Stack
- Python
- Streamlit UI
- ChromaDB vector DB
- Azure OpenAI RAG pipeline

### Local Setup
> **_NOTE:_**  <em>The application has been developed on MacOS so there is no current standard installation or run instructions for Windows machines.</em>

Create a .env.local file with the following variables.  Please discuss with project owners for API variables.
```
AZURE_OPENAI_ENDPOINT={azure openai endpoint URL}
AZURE_OPENAI_API_KEY={azure openai API key}
DEPLOYMENT_TYPE=LOCAL #This controls some functionality depending on deployment enviornment
MODEL_CACHE={cache directory for hugging face model weights to be stored}
RAG_VERSION_DIR={the directory where pipeline versions and chats will be stored}
KUBE_CONFIG_LOCAL_PATH={the directory where the kube config is stored.  This is useful for testing kube jobs.}
# Authentication params
AUTHORIZATION_ENDPOINT
TOKEN_ENDPOINT
JWKS_URI
REDIRECT_URI
CLIENT_ID
CLIENT_SECRET
SCOPE
AUDIENCE

```
To install dependecies:
```
brew install poppler
python3.10 -m venv .venv
source .venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.dev.txt
pre-commit install
```
### Versioning a new RAG pipeline

To create a new RAG pipeline version, a directory needs to be created with the following structure under your RAG_VERSION_DIR folder:

- {version name}
    - conf.yml (this is the configuration file for the pipeline, an example can be found in example_conf.yml in the top directory)
    - files (a folder containing the PDFs that you would like to vectorise)

Evaluation question versions are included in Evaluation folder.

```
python rag_versioning.py -d {version_directory} -q {evaluation_question_path} -v (optional, if creation of a new vectorDB is required e.g. if chunking config has changed)
```


### Running the application
```
streamlit run Welcome.py
```

### Contributing
1. PRs of feature branches or bug fixes should be made to dev branch
2. Merges to dev should be "Squash and merge"
3. Only dev will be merged into main

### Deployment
- Deployment to dev is automatically run on merge to dev.
- Deployment to pre-prod is automatically run on merge to main.
- RAG pipeline versions need to be manually uploaded to the deployment service.
- If dependencies are changed, a new base image will need to be manually run before any deployments are run.
