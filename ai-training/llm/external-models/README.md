# External Model Storage

Heavy model artifacts are stored externally to maintain repository portability.

## Model Registry

| Model | Size | Checksum | Location |
|-------|------|----------|----------|
| CodeLlama-7B-Instruct | 12.6GB | `sha256:pending` | `./codellama-cache/` |
| Whis-Mega-Model Checkpoints | ~200MB | `sha256:pending` | `./whis-mega-model/` |

## Usage

1. Download models from external storage
2. Place in this directory following the structure above
3. Verify checksums before use
4. Models are automatically excluded from git via .gitignore

## Security

- All models undergo security scanning before inclusion
- Checksums verified on each download
- No model files committed to git repository