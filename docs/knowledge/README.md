# AgentOS Knowledge

`docs/knowledge` is now a pointer-only guide.

The canonical knowledge repository is:

<https://github.com/gabrielwithappy/knowledge-agent>

Do not add new knowledge notes here. Add them to `knowledge-agent` instead.

## Use The Canonical Repository

Clone and validate the shared repository:

```bash
git clone git@github.com:gabrielwithappy/knowledge-agent.git
cd knowledge-agent
python3 ./catalog/skills/knowledge-curator/scripts/knowledge.py validate --project "$PWD"
```

Add or edit Markdown in the cloned `knowledge-agent` repository, then commit and push through normal Git.

## Authority Boundary

Knowledge files are reusable evidence. They do not override `AGENTS.md`, root project documents, active plans, Gate 2 review, protected-path rules, vendor guides, or reviewer authority.
