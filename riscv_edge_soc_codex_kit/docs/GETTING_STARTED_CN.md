# 中文上手说明 — 把这个工程交给 Codex

## 本项目目前有、没有什么

已经交付：系统规格、风险边界、参考资料、40 个任务、依赖关系、验证验收规则、每天一次状态管理脚本、Codex Prompt、harness 自测。

还没有：任何 CPU RTL 的实际实现、通过的 HDL 仿真、Vivado 结果、FPGA 实机结果、ASIC 物理设计结果。**不要把项目脚手架当成已完成 CPU。**

## 第一次（手动操作）

1. 解压到一个专用目录，例如 `~/projects/riscv-edge-soc`；在终端运行：

```bash
cd ~/projects/riscv-edge-soc
python3 scripts/harness.py validate
python3 scripts/test_harness.py
python3 scripts/harness.py next

git init
git add .
git commit -m "chore: initialize scoped RV32I SoC engineering project"
```

2. 用 Codex 桌面应用打开这个项目目录。给 Codex `prompts/BOOTSTRAP_PROMPT.md` 全文。
3. Codex 的任务是只做 T001。完成后核查证据、代码差异、commit。每天一个任务，不自动滚入后续任务。

## 自动每天一次

- 在支持 Scheduled 的 ChatGPT/Codex 桌面工作流中，把 `prompts/DAILY_CODEX_PROMPT.md` 保存为周期任务文本，绑定这个**专用 Git checkout**，选择每天运行，保留默认受限沙箱。
- 保持机器开机和桌面应用运行。不要把 Web Scheduled 的能力误解成它可以直接编辑 Mac/Ubuntu 本地文件。
- 最初几个 scheduled run 必须人工仔细检查结果，再决定是否继续自动运行。
- 如果使用新的 Git worktree 每次执行，前一次的变更不会神奇地合并到下一次；必须先集成。
- 对有 `review_gate: true` 的任务，由你审核后，才能执行 `python3 scripts/harness.py approve <ID> --confirm-owner-review` 并 commit 状态文件。

## 每天检查 4 个东西

- 变更是否只属于选中 Task ID？
- 测试是否真正运行，记录了工具版本和失败/跳过情况？
- 有没有新的不符合架构规格的行为或未经你批准的接口变更？
- 是否可以把这次改动解释给面试官听？

## 可选功能

- T033–T036 AXI-Lite/DMA 分支默认关闭。以后如有招聘 JD 特别要求 AXI/DMA，你可以自行启用：

```bash
python3 scripts/harness.py enable T033 --confirm-owner-review
python3 scripts/harness.py enable T034 --confirm-owner-review
python3 scripts/harness.py enable T035 --confirm-owner-review
python3 scripts/harness.py enable T036 --confirm-owner-review
```

在把状态提交到 Git 之后，下次运行才会看到这些任务。优先保证主线 L1/L2 的完成度。

## 如果 Codex 说“我完成了所有东西”

不接受仅有自然语言的完成声明。请它给出可重复执行的命令、测试报告、仿真种子、FPGA 的设备与 XDC、真正的 Timing Summary。缺少对应硬件/工具时，结果必须是 NOT RUN，而不是 PASS。
