# lifecycle

**产品不是"快好了"。它处在某个阶段，而每个阶段都有别人能核对的产物。**

`lifecycle` 读一遍仓库，告诉你通过了哪几个阶段、卡在什么上，以及解决它需要的那一条命令。真实输出：

```
$ lifecycle --repo ../game status
# lifecycle (.../game)
3/7 stages pass  ·  pack: game

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **WARN** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **FAIL** | no architecture document |
| 3 | Build | **FAIL** | no test files found |
| 4 | Verify | **FAIL** | 1 requirement(s) not verified: R1 |
| 5 | Release | **FAIL** | no CHANGELOG |
| 6 | Sustain | **WARN** | Does the work survive a context reset? |
```

## 契约：七个阶段

| 阶段 | 软件默认产物（可被工作包替换） |
|---|---|
| 0 Discovery | `docs/product/vision.md`：Problem / Audience / Non-goals |
| 1 Spec | `.projtruth/requirements.json`，每条需求都有可判定的验收标准 |
| 2 Design | 架构文档 + 至少一条记录下来的决策 |
| 3 Build | 源码与测试 |
| 4 Verify | 每条需求都有仍然成立的证据；没有会误导读者的文档问题 |
| 5 Release | 与版本匹配的 CHANGELOG 条目、对应的 git tag |
| 6 Sustain | 工作线程、日志、阶段报告、评审记录、上下文预算 |

阶段通过与否由仓库当前状态计算，不存任何"已通过"状态。projtruth / corpus 没安装时，阶段 4 报 WARN 并给出安装命令，而不是 FAIL。

## 工作包：各类开发是平等的

七个阶段只定义问题，不规定产物。内置的 architecture/source/tests 是**软件这一类**的默认值，不是通则。工作包为某一类工作声明自己的产物，并可以替换不适用的检查：

```
game    支柱、世界设定、任务图（act/order、依赖、揭示、知情状态）
story   大纲（幕、情节线）、人物（欲望/障碍/缺陷、初始知情）、章节（顺序、POV、伏笔回收）
```

```bash
lifecycle pack list              # 有哪些包，哪个正在生效
lifecycle pack init game         # 写出空结构（只写模板，不写内容）
lifecycle pack guide story       # 该类工作的深度手册与工艺标准
```

- **自动检测只加检查，绝不删除门槛**：软件仓库里出现 `docs/story/` 只会多出剧情检查，架构要求照旧。
- 替换必须显式：`lifecycle --pack story check`。小说的构建产物是稿子（`story:draft`，报告章节与字数），不是源码和测试。
- 一个项目可以同时属于多类工作：`lifecycle --pack game --with story check` 在保留架构/源码/测试门槛的同时检查剧情（stage 表显示 `pack: game+story`）；`--with` 只加检查，绝不替换。
- 每个包同时是工艺标准：story 要求具体场景、冲突是引擎、困难题材正面写、情节线必须回收；game 要求任务有动词、有代价、世界记得你做过什么。

新增一类工作（service、视频、网页）见 [references/writing-a-pack.md](references/writing-a-pack.md)。

## 长线工作：跨会话、跨压缩

- `docs/work/current.md`：Goal / Done / Next / Blockers，新会话第一眼读的文件；
- `docs/work/plan.md`：里程碑与任务，进度可见；
- `docs/work/log/<日期>.md`：每个工作会话一条记录；
- `docs/reports/status-<日期>.md`：`lifecycle report` 起草，留三节给你填；
- `docs/reviews/`：对抗性评审记录，缺失、过期或"没有发现"都会被报告。

```bash
lifecycle init            # 建好工作线程与目录
lifecycle hook install    # PreCompact -> snapshot，SessionStart -> resume
lifecycle resume          # 压缩或新会话后：线程、日志、当前阻塞项
lifecycle report          # 起草阶段报告
```

## 上下文

状态栏命令 `lifecycle statusline` 会记录 `context_window.used_percentage`，并渲染 `74% ctx`；接近压缩触发线时显示 `74% ctx - /compact`。阈值跟随 `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`（提前 15 点提醒、5 点明确要求压缩）。钩子看不到实时上下文，也无法触发压缩——这是 Claude Code 自己决定的。

## 命令

| 命令 | 作用 |
|---|---|
| `lifecycle status [--json]` | 阶段表 + 下一步 |
| `lifecycle next` | 一条阻塞项和它的修法 |
| `lifecycle check [--stage N]` | CI 门禁：阶段失败就 exit 1 |
| `lifecycle stages` | 契约本身 |
| `lifecycle guide [stage\|pack]` | 阶段或工作包的手册 |
| `lifecycle pack list\|init\|guide <name>` | 工作包：检查、手册、脚手架 |
| `lifecycle init` | 建立工作线程、计划、日志与报告目录 |
| `lifecycle resume` | 压缩或新会话后恢复工作线程 |
| `lifecycle report` | 起草阶段报告 |
| `lifecycle snapshot` | 压缩前写下会丢失的状态（钩子调用） |
| `lifecycle hook install\|uninstall\|status` | 安装/卸载 PreCompact、SessionStart、状态栏 |

## 安装

纯标准库，Python 3.8+。

```bash
pip install git+https://github.com/Libres-coder/lifecycle
# 或作为 Claude Code 技能：
git clone https://github.com/Libres-coder/lifecycle ~/.claude/skills/lifecycle
pip install ~/.claude/skills/lifecycle
```

## 设计取向

- **不存状态。** 阶段通过是因为仓库现在就是这样。会过期的通行证，人就不信了。
- **不伪造通过。** `init` 只建空文件，`report` 只汇总可核对的事实，没有命令替你写愿景、测试或证据。
- **组合而非替换。** projtruth 和 corpus 通过 JSON 输出被调用；接口有端到端契约测试。
- **有意见，可 fork / 可加包。** 契约与工作包都是可改的，见 [references/forking.md](references/forking.md) 与 [references/writing-a-pack.md](references/writing-a-pack.md)。

## 它不做什么

- 不判断质量：愿景可以存在且很糟；工艺标准写进手册，检查只能看声明与长度。
- 不跑测试、不验证需求——有 projtruth/corpus 时问它们。
- 自己不做强制：把 `lifecycle check` 放进 CI 才有约束力。
- 版本与 tag 是文本匹配：`v0.2.0` 匹配 `0.2.0`。

## 相关项目

- [projtruth](https://github.com/Libres-coder/projtruth) —— 需求与证据（含证据质量分区）
- [corpus](https://github.com/Libres-coder/corpus) —— 文档堆积、重复、过期、指向已删除文件
- [verify-first](https://github.com/Libres-coder/verify-first) —— 产出证据的流水线

## 许可证

MIT
