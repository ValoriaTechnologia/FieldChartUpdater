# FieldChartUpdater

Action GitHub réutilisable (Docker, Python) qui édite un ou plusieurs champs dans un fichier YAML. Équivalent à `yq -i`, sans dépendance au binaire yq. Utilise la notation pointée pour les clés imbriquées (ex. `image.tag`).

## Utilisation

Référencer l'action depuis un autre dépôt : `uses: <owner>/FieldChartUpdater@main` (ou une tag/branch). Pour tester dans ce dépôt : `uses: ./`.

### Inputs

| Input   | Requis | Description |
|---------|--------|-------------|
| `file`  | Oui    | Chemin du fichier YAML à modifier, relatif au workspace (ex. `./value.yaml`, `charts/app/values.yaml`). |
| `edits` | Oui    | Tableau JSON d'objets `{"path": "cle.nested", "value": valeur}`. Les types (string, number, boolean) sont conservés dans le YAML. |

Le chemin `file` doit être sous le répertoire de travail du job (généralement `GITHUB_WORKSPACE`). Lorsque `GITHUB_WORKSPACE` est défini, l'action n'accepte que des fichiers dont le chemin résolu est sous ce répertoire.

### Exemples

**Un seul champ** (équivalent à `yq -i '.image.tag = "valu"' ./value.yaml`) :

```yaml
- uses: owner/FieldChartUpdater@main
  with:
    file: ./value.yaml
    edits: '[{"path": "image.tag", "value": "valu"}]'
```

**Plusieurs champs** :

```yaml
- uses: owner/FieldChartUpdater@main
  with:
    file: ./charts/app/values.yaml
    edits: |
      [
        {"path": "image.tag", "value": "v1.2.3"},
        {"path": "replicaCount", "value": 3}
      ]
```

## Développement

### Prérequis

- Python 3.12 (ou compatible)
- Docker (pour builder l'image de l'action)

### Structure du dépôt

- `action.yaml` — Métadonnées de l'action (inputs, image Docker)
- `Dockerfile` — Image Python exécutant `edit_yaml.py`
- `edit_yaml.py` — Script d'édition YAML
- `requirements.txt` / `requirements-dev.txt` — PyYAML, pytest
- `tests/` — Tests pytest

### Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Le workflow [.github/workflows/test.yml](.github/workflows/test.yml) exécute les tests unitaires et l'intégration de l'action sur chaque push/PR sur `main`. Le workflow [.github/workflows/release.yml](.github/workflows/release.yml) gère les releases et le versionnage par tags.
