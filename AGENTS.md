# Installation Handoff

When a user asks Codex to install this repository:

1. Use the standard `skill-installer` on `xhs-fashion-qc-publish/`.
2. Verify that `SKILL.md`, `agents/openai.yaml`, both JSON references, the validator script, and `references/使用说明-中文.md` exist in the installed directory.
3. Run the standard skill validator when available.
4. Read the installed Chinese manual.
5. In the same chat, report in Chinese: the installed path, validation result, missing dependencies or login prerequisites, what the Skill does and does not do, and one first-use prompt.
6. Never report image generation, RedBeacon access, account login, review, or publishing as available unless separately verified on that machine.
