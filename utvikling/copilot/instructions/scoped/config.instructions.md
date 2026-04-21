---
applyTo: "**/config/**/*.java,**/*.properties,**/nais/**"
---

# Configuration Conventions

## File Layout

- `app/src/main/resources/application.properties` — core settings
- `app/src/main/resources/application-nais.properties` — NAIS/production overrides
- `nais/naiserator.yaml` — Kubernetes deployment manifest (templated)
- `nais/q*-config.json` / `nais/p-config.json` — environment-specific config

## Config Classes

- Key config classes: `<app-name>Properties`, `AzureProperties`, `NaisProperties`, `WebProxyProperties`
- Use strict Jakarta Bean Validation on all config classes
