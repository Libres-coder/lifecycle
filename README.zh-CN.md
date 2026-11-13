# lifecycle

**产品不是"快好了"。它处在某个阶段，而每个阶段都有别人能核对的产物。**

`lifecycle` 读一遍仓库，告诉你通过了哪几个阶段、卡在什么上、以及解决它需要的那一条命令。下面是我自己一个项目的真实输出：

```
$ lifecycle --repo ../projtruth status
# lifecycle (.../projtruth)
4/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **FAIL** | no architecture document |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |

## Next
Stage 0 Discovery: **vision** - no product vision document

    write docs/product/vision.md with Problem, Audience and Non-goals
```

这个结果是对的：projtruth 有需求、代码、测试、证据和发布，但没有愿景文档和架构文档。

## 为什么

Agent 会因为代码能编译就宣布"做完了"。缺的那些东西——愿景、验收标准、设计决策、证据、发布说明——每一项都有人负责，但没有任何地方说得清哪些已经有了。站会靠问，这个靠读仓库。

现有方案要么用固定 33 阶段的框架替换你的流程（AI-DLC），要么是只校验文档格式、不读仓库状态的半成品（sdlc-mcp）。这个很小、无状态、读你已经在用的东西。

## 契约

| 阶段 | 必须产出 | 怎么检查 |
|---|---|---|
| 0 Discovery | `docs/product/vision.md`，含 Problem / Audience / Non-goals | 标题 |
| 1 Spec | `.projtruth/requirements.json`，每条需求都有验收标准 | 结构 |
| 2 Design | 架构文档 + 至少一条决策记录 | 文件 + `decisions.jsonl` |
| 3 Build | 源码文件和测试文件 | 文件扫描 |
| 4 Verify | 所有需求 `verified`；没有会误导读者的文档问题 | `projtruth report --json`、`corpus report --json` |
| 5 Release | 与版本匹配的 CHANGELOG 条目、对应的 git tag | 文件 + `git tag` |

projtruth / corpus 没安装时，阶段 4 报 **WARN** 并给出安装命令，而不是 FAIL——工具缺失不等于产品缺失。

## 安装

纯标准库，Python 3.8+。

```bash
pip install git+https://github.com/Libres-coder/lifecycle
# 或作为 Claude Code 技能：
git clone https://github.com/Libres-coder/lifecycle ~/.claude/skills/lifecycle
pip install ~/.claude/skills/lifecycle
```

## 命令

| 命令 | 作用 |
|---|---|
| `lifecycle status [--json]` | 阶段表 + 下一步 |
| `lifecycle next` | 一条阻塞项和它的修法 |
| `lifecycle check [--stage N]` | CI 门禁：阶段失败就 exit 1 |
| `lifecycle stages` | 契约本身：每个阶段要求什么 |

## 设计取向

- **不存状态。** 阶段通过是因为仓库现在就是这样，而不是因为上周有人跑过某条命令。会过期的通行证，人就不信了。
- **只读。** 它不会替你创建它要求的产物，所以它造不出一个"通过"。
- **组合而非替换。** projtruth 和 corpus 通过 JSON 输出被调用，缺一个也能跑。
- **有意见，可 fork。** 六个通用阶段覆盖一个产品；游戏或库需要的产物不同——改 `lifecycle/contract.py`，见 [references/forking.md](references/forking.md)。

## 它不做什么

- 不判断质量：愿景可以存在且很糟。
- 不跑测试、不验证需求、不读文档——有 projtruth/corpus 时问它们。
- 自己不做强制：把 `lifecycle check` 放进 CI 才有约束力。
- 版本与 tag 是文本匹配：`v0.2.0` 匹配 `0.2.0`。

## 相关项目

- [projtruth](https://github.com/Libres-coder/projtruth) —— 需求与证据
- [corpus](https://github.com/Libres-coder/corpus) —— 文档堆积、重复、过期
- [verify-first](https://github.com/Libres-coder/verify-first) —— 产出证据的流水线

## 许可证

MIT
