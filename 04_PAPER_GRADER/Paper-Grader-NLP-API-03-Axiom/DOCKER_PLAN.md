# Docker Plan

The Paper Grader can be containerized, but the heavy NLP model weights should not be committed to Git.

## What Goes In The Repo

Commit these:

```text
schemas
prompts
workflow configs
pipeline code
HTML/CSS/JS prototypes
Dockerfile
docker-compose.yml
requirements.txt
README docs
```

Do not commit these:

```text
Hugging Face model weights
DeBERTa cache
SBERT cache
Qdrant storage
Postgres data
paper inputs
generated reports
Excel outputs
local secrets
```

## Recommended Docker Shape

Use separate services:

```text
paper-grader-api     Python/FastAPI or CLI runner for intake, metrics, Excel, reports
qdrant               vector database
infinity             embedding server for sentence-transformers/all-MiniLM-L6-v2
postgres             optional structured database
ollama               optional local model reviewer
```

## NLP Model Strategy

For DeBERTa / Hugging Face models:

- The repo declares the model name.
- The container downloads the model on first run.
- The model cache is mounted as a Docker volume.
- The cache survives rebuilds.

Example volume:

```text
hf_cache:/models/huggingface
```

For embeddings:

- Prefer the existing Infinity service when running on the NAS/local network.
- In Docker mode, either connect to external Infinity or run an `infinity` service in compose.

For Ollama:

- Keep Ollama optional.
- Pull models outside the repo, for example `ollama pull llama3.1`.
- Mount Ollama's model volume instead of committing model files.

## First Docker MVP

The first Docker version should not try to include every NLP component.

Build order:

1. `paper-grader-api` reads `.txt`, `.md`, `.html` from `/data/input`.
2. Writes JSON, Markdown, HTML, and Excel to `/data/output`.
3. Uses deterministic raw metrics first.
4. Calls external Qdrant/Infinity if configured.
5. Adds DeBERTa only after the deterministic pipeline works.
6. Adds Ollama as optional second-reader review.

## Example Runtime Folders

```text
/data/input
/data/output
/data/archive
/models/huggingface
```

## Environment Variables

```text
QDRANT_URL=http://qdrant:6333
INFINITY_URL=http://infinity:7997
HF_HOME=/models/huggingface
TRANSFORMERS_CACHE=/models/huggingface
OLLAMA_URL=http://ollama:11434
```

## Practical Answer

Yes, this can become Docker. The Docker image should contain the code and dependencies. The NLP weights should download into mounted volumes or run in separate services.
