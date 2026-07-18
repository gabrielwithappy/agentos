---
name: architecture-diagram
description: Create dark, self-contained HTML/SVG architecture diagrams.
license: MIT
source: Hermes architecture-diagram reference, adapted for AgentOS catalog use.
---

# Architecture Diagram

Use this skill when the user asks for a cloud, service, deployment, API, database, or system architecture diagram and wants a polished standalone artifact.

Default output is a local `.html` file with inline SVG and CSS. Do not require network calls, hosted design tools, or external renderers.

## Workflow

1. Identify the system boundary, major components, data stores, external actors, and critical flows.
2. Choose a diagram shape: layered architecture, request flow, deployment topology, or data pipeline.
3. Generate one self-contained HTML file with inline SVG.
4. Use concise labels and directional arrows. Include a small legend when component types are color-coded.
5. Verify that the file opens without external assets.

## Visual Contract

- Dark background with high contrast text.
- Use distinct colors for frontend, backend, database, cloud, security, queues, and external systems.
- Keep typography readable at laptop width.
- Do not use decorative gradients or generic abstract art when the user needs to inspect the architecture.
