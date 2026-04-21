---
applyTo: "**/anticorruptionlayer/**/*.java,**/*AntiCorruptionLayer*.java,**/*Consumer*.java"
---

# Anti-Corruption Layer Conventions

- Each external system has a dedicated anti-corruption layer
- Translate external DTOs into internal domain models at the boundary
- Never leak external DTOs into domain logic
- Name adapters `*AntiCorruptionLayer`
- Name external API clients `*Consumer`
- Keep DTOs (`*Dto`) as close to the external API shape as possible
