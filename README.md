# xhs-fashion-qc-publish

女装小红书“产品事实与卖点 → 原生生图 → 独立审图 → 事实型文案 → RedBeacon 自主添加审稿 → 人工确认后发布”的 Codex 编排 Skill。

本仓库只提供编排 Skill，不包含账号、Cookie、API Key、测试图片、数据库或任何企业私有资料。独立审图与事实型文案 Agent 请从配套仓库安装。

请先安装并验证 [xhs-fashion-agents](https://github.com/znnw4m6k7k-dotcom/xhs-fashion-agents) 的两个自定义 Agent，再安装本编排技能。涉及发布时，还需检查 RedBeacon 配置并取得人工确认。

## 在 Codex 聊天窗口安装

把下面一整句话发送给 Codex：

```text
请使用 $skill-installer 从 https://github.com/znnw4m6k7k-dotcom/xhs-fashion-qc-publish/tree/main/xhs-fashion-qc-publish 安装；安装成功后读取 ~/.codex/skills/xhs-fashion-qc-publish/references/使用说明-中文.md，并在当前聊天窗口给我一份完整中文说明书、依赖检查结果和首次使用示例。不要声称未安装的依赖已经可用。
```

安装成功后，Skill 会在下一轮对话可用。标准安装器发现同名目录时会停止，不会覆盖旧版本。

## 终端安装

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo znnw4m6k7k-dotcom/xhs-fashion-qc-publish \
  --path xhs-fashion-qc-publish
```

## 依赖边界

完整流程会调用宿主中已有的相关能力，包括原生图像生成、`xiaohongshu-fashion-prompt-draw`、独立审图、RedBeacon 审稿/发布能力。安装本 Skill 不等于这些外部能力、账号或登录态已经就绪；首次使用前应按中文说明书逐项检查。
