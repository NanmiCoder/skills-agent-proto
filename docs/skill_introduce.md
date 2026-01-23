# Agent Skills
# Agent Skills（智能技能）

Agent Skills are modular capabilities that extend Claude's functionality. Each Skill packages instructions, metadata, and optional resources (scripts, templates) that Claude uses automatically when relevant.
Agent Skills 是扩展 Claude 功能的模块化能力。每个 Skill 打包了指令、元数据和可选资源（脚本、模板），Claude 会在相关时自动使用它们。

---

## Why use Skills
## 为什么使用 Skills

Skills are reusable, filesystem-based resources that provide Claude with domain-specific expertise: workflows, context, and best practices that transform general-purpose agents into specialists. Unlike prompts (conversation-level instructions for one-off tasks), Skills load on-demand and eliminate the need to repeatedly provide the same guidance across multiple conversations.
Skills 是可重用的、基于文件系统的资源，为 Claude 提供特定领域的专业知识：工作流程、上下文和最佳实践，将通用智能体转变为专家。与提示词（用于一次性任务的对话级指令）不同，Skills 按需加载，无需在多次对话中重复提供相同的指导。

**Key benefits**:
**主要优势**：
- **Specialize Claude**: Tailor capabilities for domain-specific tasks
- **专业化 Claude**：为特定领域任务定制能力
- **Reduce repetition**: Create once, use automatically
- **减少重复**：创建一次，自动使用
- **Compose capabilities**: Combine Skills to build complex workflows
- **组合能力**：结合多个 Skills 构建复杂工作流程

<Note>
For a deep dive into the architecture and real-world applications of Agent Skills, read our engineering blog: [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills).
如需深入了解 Agent Skills 的架构和实际应用，请阅读我们的工程博客：[为现实世界的智能体配备 Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)。
</Note>

## Using Skills
## 使用 Skills

Anthropic provides pre-built Agent Skills for common document tasks (PowerPoint, Excel, Word, PDF), and you can create your own custom Skills. Both work the same way. Claude automatically uses them when relevant to your request.
Anthropic 为常见文档任务（PowerPoint、Excel、Word、PDF）提供了预构建的 Agent Skills，你也可以创建自己的自定义 Skills。两者的工作方式相同。Claude 会在与你的请求相关时自动使用它们。

**Pre-built Agent Skills** are available to all users on claude.ai and via the Claude API. See the [Available Skills](#available-skills) section below for the complete list.
**预构建的 Agent Skills** 对 claude.ai 上的所有用户和通过 Claude API 的用户都可用。请参阅下方的[可用 Skills](#available-skills) 部分获取完整列表。

**Custom Skills** let you package domain expertise and organizational knowledge. They're available across Claude's products: create them in Claude Code, upload them via the API, or add them in claude.ai settings.
**自定义 Skills** 让你可以打包领域专业知识和组织知识。它们可在 Claude 的各个产品中使用：在 Claude Code 中创建、通过 API 上传，或在 claude.ai 设置中添加。

<Note>
**Get started:**
**快速开始：**
- For pre-built Agent Skills: See the [quickstart tutorial](/docs/en/agents-and-tools/agent-skills/quickstart) to start using PowerPoint, Excel, Word, and PDF skills in the API
- 对于预构建的 Agent Skills：请参阅[快速入门教程](/docs/en/agents-and-tools/agent-skills/quickstart)，开始在 API 中使用 PowerPoint、Excel、Word 和 PDF skills
- For custom Skills: See the [Agent Skills Cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction) to learn how to create your own Skills
- 对于自定义 Skills：请参阅 [Agent Skills Cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction) 学习如何创建自己的 Skills
</Note>

## How Skills work
## Skills 如何工作

Skills leverage Claude's VM environment to provide capabilities beyond what's possible with prompts alone. Claude operates in a virtual machine with filesystem access, allowing Skills to exist as directories containing instructions, executable code, and reference materials, organized like an onboarding guide you'd create for a new team member.
Skills 利用 Claude 的虚拟机环境来提供仅靠提示词无法实现的能力。Claude 在具有文件系统访问权限的虚拟机中运行，允许 Skills 以目录形式存在，包含指令、可执行代码和参考材料，就像你为新团队成员创建的入职指南一样组织。

This filesystem-based architecture enables **progressive disclosure**: Claude loads information in stages as needed, rather than consuming context upfront.
这种基于文件系统的架构实现了**渐进式披露**：Claude 根据需要分阶段加载信息，而不是预先消耗上下文。

### Three types of Skill content, three levels of loading
### 三种类型的 Skill 内容，三个加载级别

Skills can contain three types of content, each loaded at different times:
Skills 可以包含三种类型的内容，每种在不同时间加载：

### Level 1: Metadata (always loaded)
### 级别 1：元数据（始终加载）

**Content type: Instructions**. The Skill's YAML frontmatter provides discovery information:
**内容类型：指令**。Skill 的 YAML 前置元数据提供发现信息：

```yaml
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---
```

Claude loads this metadata at startup and includes it in the system prompt. This lightweight approach means you can install many Skills without context penalty; Claude only knows each Skill exists and when to use it.
Claude 在启动时加载此元数据并将其包含在系统提示中。这种轻量级方法意味着你可以安装许多 Skills 而不会造成上下文惩罚；Claude 只知道每个 Skill 的存在和使用时机。

### Level 2: Instructions (loaded when triggered)
### 级别 2：指令（触发时加载）

**Content type: Instructions**. The main body of SKILL.md contains procedural knowledge: workflows, best practices, and guidance:
**内容类型：指令**。SKILL.md 的主体包含程序性知识：工作流程、最佳实践和指导：

````markdown
# PDF Processing

## Quick start

Use pdfplumber to extract text from PDFs:

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

For advanced form filling, see [FORMS.md](FORMS.md).
````

When you request something that matches a Skill's description, Claude reads SKILL.md from the filesystem via bash. Only then does this content enter the context window.
当你的请求与 Skill 的描述匹配时，Claude 通过 bash 从文件系统读取 SKILL.md。只有在此时，这些内容才会进入上下文窗口。

### Level 3: Resources and code (loaded as needed)
### 级别 3：资源和代码（按需加载）

**Content types: Instructions, code, and resources**. Skills can bundle additional materials:
**内容类型：指令、代码和资源**。Skills 可以捆绑额外的材料：

```
pdf-skill/
├── SKILL.md (main instructions)        # 主要指令
├── FORMS.md (form-filling guide)       # 表单填写指南
├── REFERENCE.md (detailed API reference) # 详细 API 参考
└── scripts/
    └── fill_form.py (utility script)   # 实用脚本
```

**Instructions**: Additional markdown files (FORMS.md, REFERENCE.md) containing specialized guidance and workflows
**指令**：包含专门指导和工作流程的额外 markdown 文件（FORMS.md、REFERENCE.md）

**Code**: Executable scripts (fill_form.py, validate.py) that Claude runs via bash; scripts provide deterministic operations without consuming context
**代码**：Claude 通过 bash 运行的可执行脚本（fill_form.py、validate.py）；脚本提供确定性操作而不消耗上下文

**Resources**: Reference materials like database schemas, API documentation, templates, or examples
**资源**：参考材料，如数据库模式、API 文档、模板或示例

Claude accesses these files only when referenced. The filesystem model means each content type has different strengths: instructions for flexible guidance, code for reliability, resources for factual lookup.
Claude 只在被引用时访问这些文件。文件系统模型意味着每种内容类型都有不同的优势：指令用于灵活指导，代码用于可靠性，资源用于事实查询。

| Level | When Loaded | Token Cost | Content |
| 级别 | 加载时机 | Token 成本 | 内容 |
|-------|------------|------------|---------|
| **Level 1: Metadata** | Always (at startup) | ~100 tokens per Skill | `name` and `description` from YAML frontmatter |
| **级别 1：元数据** | 始终（启动时） | 每个 Skill 约 100 tokens | YAML 前置元数据中的 `name` 和 `description` |
| **Level 2: Instructions** | When Skill is triggered | Under 5k tokens | SKILL.md body with instructions and guidance |
| **级别 2：指令** | Skill 被触发时 | 少于 5k tokens | 包含指令和指导的 SKILL.md 主体 |
| **Level 3+: Resources** | As needed | Effectively unlimited | Bundled files executed via bash without loading contents into context |
| **级别 3+：资源** | 按需 | 实际上无限制 | 通过 bash 执行的捆绑文件，不将内容加载到上下文中 |

Progressive disclosure ensures only relevant content occupies the context window at any given time.
渐进式披露确保在任何时刻只有相关内容占用上下文窗口。

### The Skills architecture
### Skills 架构

Skills run in a code execution environment where Claude has filesystem access, bash commands, and code execution capabilities. Think of it like this: Skills exist as directories on a virtual machine, and Claude interacts with them using the same bash commands you'd use to navigate files on your computer.
Skills 在代码执行环境中运行，Claude 在该环境中具有文件系统访问、bash 命令和代码执行能力。可以这样理解：Skills 作为虚拟机上的目录存在，Claude 使用与你在计算机上浏览文件相同的 bash 命令与它们交互。

![Agent Skills Architecture - showing how Skills integrate with the agent's configuration and virtual machine](/docs/images/agent-skills-architecture.png)
![Agent Skills 架构 - 展示 Skills 如何与智能体配置和虚拟机集成](/docs/images/agent-skills-architecture.png)

**How Claude accesses Skill content:**
**Claude 如何访问 Skill 内容：**

When a Skill is triggered, Claude uses bash to read SKILL.md from the filesystem, bringing its instructions into the context window. If those instructions reference other files (like FORMS.md or a database schema), Claude reads those files too using additional bash commands. When instructions mention executable scripts, Claude runs them via bash and receives only the output (the script code itself never enters context).
当 Skill 被触发时，Claude 使用 bash 从文件系统读取 SKILL.md，将其指令带入上下文窗口。如果这些指令引用其他文件（如 FORMS.md 或数据库模式），Claude 也会使用额外的 bash 命令读取这些文件。当指令提到可执行脚本时，Claude 通过 bash 运行它们并只接收输出（脚本代码本身永远不会进入上下文）。

**What this architecture enables:**
**这种架构实现了什么：**

**On-demand file access**: Claude reads only the files needed for each specific task. A Skill can include dozens of reference files, but if your task only needs the sales schema, Claude loads just that one file. The rest remain on the filesystem consuming zero tokens.
**按需文件访问**：Claude 只读取每个特定任务所需的文件。一个 Skill 可以包含数十个参考文件，但如果你的任务只需要销售模式，Claude 只加载那一个文件。其余的保留在文件系统上，消耗零 tokens。

**Efficient script execution**: When Claude runs `validate_form.py`, the script's code never loads into the context window. Only the script's output (like "Validation passed" or specific error messages) consumes tokens. This makes scripts far more efficient than having Claude generate equivalent code on the fly.
**高效脚本执行**：当 Claude 运行 `validate_form.py` 时，脚本的代码永远不会加载到上下文窗口中。只有脚本的输出（如"验证通过"或特定错误消息）消耗 tokens。这使得脚本比让 Claude 即时生成等效代码要高效得多。

**No practical limit on bundled content**: Because files don't consume context until accessed, Skills can include comprehensive API documentation, large datasets, extensive examples, or any reference materials you need. There's no context penalty for bundled content that isn't used.
**捆绑内容实际上没有限制**：因为文件在被访问之前不消耗上下文，Skills 可以包含全面的 API 文档、大型数据集、大量示例或你需要的任何参考材料。未使用的捆绑内容不会造成上下文惩罚。

This filesystem-based model is what makes progressive disclosure work. Claude navigates your Skill like you'd reference specific sections of an onboarding guide, accessing exactly what each task requires.
这种基于文件系统的模型使渐进式披露成为可能。Claude 浏览你的 Skill 就像你查阅入职指南的特定章节一样，精确访问每个任务所需的内容。

### Example: Loading a PDF processing skill
### 示例：加载 PDF 处理 skill

Here's how Claude loads and uses a PDF processing skill:
以下是 Claude 如何加载和使用 PDF 处理 skill：

1. **Startup**: System prompt includes: `PDF Processing - Extract text and tables from PDF files, fill forms, merge documents`
1. **启动**：系统提示包含：`PDF Processing - 从 PDF 文件中提取文本和表格，填写表单，合并文档`
2. **User request**: "Extract the text from this PDF and summarize it"
2. **用户请求**："提取这个 PDF 中的文本并总结它"
3. **Claude invokes**: `bash: read pdf-skill/SKILL.md` → Instructions loaded into context
3. **Claude 调用**：`bash: read pdf-skill/SKILL.md` → 指令加载到上下文中
4. **Claude determines**: Form filling is not needed, so FORMS.md is not read
4. **Claude 判断**：不需要表单填写，因此不读取 FORMS.md
5. **Claude executes**: Uses instructions from SKILL.md to complete the task
5. **Claude 执行**：使用 SKILL.md 中的指令完成任务

![Skills loading into context window - showing the progressive loading of skill metadata and content](/docs/images/agent-skills-context-window.png)
![Skills 加载到上下文窗口 - 展示 skill 元数据和内容的渐进式加载](/docs/images/agent-skills-context-window.png)

The diagram shows:
该图显示：
1. Default state with system prompt and skill metadata pre-loaded
1. 系统提示和 skill 元数据预加载的默认状态
2. Claude triggers the skill by reading SKILL.md via bash
2. Claude 通过 bash 读取 SKILL.md 来触发 skill
3. Claude optionally reads additional bundled files like FORMS.md as needed
3. Claude 根据需要可选地读取额外的捆绑文件，如 FORMS.md
4. Claude proceeds with the task
4. Claude 继续执行任务

This dynamic loading ensures only relevant skill content occupies the context window.
这种动态加载确保只有相关的 skill 内容占用上下文窗口。

## Where Skills work
## Skills 在哪里工作

Skills are available across Claude's agent products:
Skills 可在 Claude 的各个智能体产品中使用：

### Claude API

The Claude API supports both pre-built Agent Skills and custom Skills. Both work identically: specify the relevant `skill_id` in the `container` parameter along with the code execution tool.
Claude API 支持预构建的 Agent Skills 和自定义 Skills。两者的工作方式相同：在 `container` 参数中指定相关的 `skill_id`，以及代码执行工具。

**Prerequisites**: Using Skills via the API requires three beta headers:
**前提条件**：通过 API 使用 Skills 需要三个 beta 头：
- `code-execution-2025-08-25` - Skills run in the code execution container
- `code-execution-2025-08-25` - Skills 在代码执行容器中运行
- `skills-2025-10-02` - Enables Skills functionality
- `skills-2025-10-02` - 启用 Skills 功能
- `files-api-2025-04-14` - Required for uploading/downloading files to/from the container
- `files-api-2025-04-14` - 用于向容器上传/下载文件

Use pre-built Agent Skills by referencing their `skill_id` (e.g., `pptx`, `xlsx`), or create and upload your own via the Skills API (`/v1/skills` endpoints). Custom Skills are shared organization-wide.
通过引用它们的 `skill_id`（例如 `pptx`、`xlsx`）使用预构建的 Agent Skills，或通过 Skills API（`/v1/skills` 端点）创建和上传你自己的。自定义 Skills 在组织范围内共享。

To learn more, see [Use Skills with the Claude API](/docs/en/build-with-claude/skills-guide).
要了解更多，请参阅[在 Claude API 中使用 Skills](/docs/en/build-with-claude/skills-guide)。

### Claude Code

[Claude Code](https://code.claude.com/docs/en/overview) supports only Custom Skills.
[Claude Code](https://code.claude.com/docs/en/overview) 仅支持自定义 Skills。

**Custom Skills**: Create Skills as directories with SKILL.md files. Claude discovers and uses them automatically.
**自定义 Skills**：创建包含 SKILL.md 文件的目录作为 Skills。Claude 会自动发现并使用它们。

Custom Skills in Claude Code are filesystem-based and don't require API uploads.
Claude Code 中的自定义 Skills 是基于文件系统的，不需要 API 上传。

To learn more, see [Use Skills in Claude Code](https://code.claude.com/docs/en/skills).
要了解更多，请参阅[在 Claude Code 中使用 Skills](https://code.claude.com/docs/en/skills)。

### Claude Agent SDK

The [Claude Agent SDK](/docs/en/agent-sdk/overview) supports custom Skills through filesystem-based configuration.
[Claude Agent SDK](/docs/en/agent-sdk/overview) 通过基于文件系统的配置支持自定义 Skills。

**Custom Skills**: Create Skills as directories with SKILL.md files in `.claude/skills/`. Enable Skills by including `"Skill"` in your `allowed_tools` configuration.
**自定义 Skills**：在 `.claude/skills/` 中创建包含 SKILL.md 文件的目录作为 Skills。通过在 `allowed_tools` 配置中包含 `"Skill"` 来启用 Skills。

Skills in the Agent SDK are then automatically discovered when the SDK runs.
然后，当 SDK 运行时，Skills 会被自动发现。

To learn more, see [Agent Skills in the SDK](/docs/en/agent-sdk/skills).
要了解更多，请参阅[SDK 中的 Agent Skills](/docs/en/agent-sdk/skills)。

### Claude.ai

[Claude.ai](https://claude.ai) supports both pre-built Agent Skills and custom Skills.
[Claude.ai](https://claude.ai) 支持预构建的 Agent Skills 和自定义 Skills。

**Pre-built Agent Skills**: These Skills are already working behind the scenes when you create documents. Claude uses them without requiring any setup.
**预构建的 Agent Skills**：当你创建文档时，这些 Skills 已经在后台工作。Claude 无需任何设置即可使用它们。

**Custom Skills**: Upload your own Skills as zip files through Settings > Features. Available on Pro, Max, Team, and Enterprise plans with code execution enabled. Custom Skills are individual to each user; they are not shared organization-wide and cannot be centrally managed by admins.
**自定义 Skills**：通过设置 > 功能上传你自己的 Skills（zip 文件）。在启用代码执行的 Pro、Max、Team 和 Enterprise 计划中可用。自定义 Skills 是每个用户独立的；它们不在组织范围内共享，管理员也无法集中管理。

To learn more about using Skills in Claude.ai, see the following resources in the Claude Help Center:
要了解更多关于在 Claude.ai 中使用 Skills 的信息，请参阅 Claude 帮助中心的以下资源：
- [What are Skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [什么是 Skills？](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [在 Claude 中使用 Skills](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [How to create custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [如何创建自定义 Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Teach Claude your way of working using Skills](https://support.claude.com/en/articles/12580051-teach-claude-your-way-of-working-using-skills)
- [使用 Skills 教 Claude 你的工作方式](https://support.claude.com/en/articles/12580051-teach-claude-your-way-of-working-using-skills)

## Skill structure
## Skill 结构

Every Skill requires a `SKILL.md` file with YAML frontmatter:
每个 Skill 都需要一个带有 YAML 前置元数据的 `SKILL.md` 文件：

```yaml
---
name: your-skill-name
description: Brief description of what this Skill does and when to use it
---

# Your Skill Name

## Instructions
[Clear, step-by-step guidance for Claude to follow]

## Examples
[Concrete examples of using this Skill]
```

**Required fields**: `name` and `description`
**必填字段**：`name` 和 `description`

**Field requirements**:
**字段要求**：

`name`:
`name`（名称）：
- Maximum 64 characters
- 最多 64 个字符
- Must contain only lowercase letters, numbers, and hyphens
- 只能包含小写字母、数字和连字符
- Cannot contain XML tags
- 不能包含 XML 标签
- Cannot contain reserved words: "anthropic", "claude"
- 不能包含保留词："anthropic"、"claude"

`description`:
`description`（描述）：
- Must be non-empty
- 不能为空
- Maximum 1024 characters
- 最多 1024 个字符
- Cannot contain XML tags
- 不能包含 XML 标签

The `description` should include both what the Skill does and when Claude should use it. For complete authoring guidance, see the [best practices guide](/docs/en/agents-and-tools/agent-skills/best-practices).
`description` 应包含 Skill 的功能以及 Claude 何时应该使用它。有关完整的编写指南，请参阅[最佳实践指南](/docs/en/agents-and-tools/agent-skills/best-practices)。

## Security considerations
## 安全注意事项

We strongly recommend using Skills only from trusted sources: those you created yourself or obtained from Anthropic. Skills provide Claude with new capabilities through instructions and code, and while this makes them powerful, it also means a malicious Skill can direct Claude to invoke tools or execute code in ways that don't match the Skill's stated purpose.
我们强烈建议仅使用来自可信来源的 Skills：你自己创建的或从 Anthropic 获得的。Skills 通过指令和代码为 Claude 提供新能力，虽然这使它们功能强大，但也意味着恶意 Skill 可以指示 Claude 以与 Skill 声明目的不符的方式调用工具或执行代码。

<Warning>
If you must use a Skill from an untrusted or unknown source, exercise extreme caution and thoroughly audit it before use. Depending on what access Claude has when executing the Skill, malicious Skills could lead to data exfiltration, unauthorized system access, or other security risks.
如果你必须使用来自不受信任或未知来源的 Skill，请在使用前极度谨慎并彻底审核。根据 Claude 在执行 Skill 时的访问权限，恶意 Skills 可能导致数据泄露、未授权系统访问或其他安全风险。
</Warning>

**Key security considerations**:
**主要安全注意事项**：
- **Audit thoroughly**: Review all files bundled in the Skill: SKILL.md, scripts, images, and other resources. Look for unusual patterns like unexpected network calls, file access patterns, or operations that don't match the Skill's stated purpose
- **彻底审核**：检查 Skill 中捆绑的所有文件：SKILL.md、脚本、图片和其他资源。查找异常模式，如意外的网络调用、文件访问模式或与 Skill 声明目的不符的操作
- **External sources are risky**: Skills that fetch data from external URLs pose particular risk, as fetched content may contain malicious instructions. Even trustworthy Skills can be compromised if their external dependencies change over time
- **外部来源有风险**：从外部 URL 获取数据的 Skills 具有特殊风险，因为获取的内容可能包含恶意指令。即使是可信的 Skills，如果其外部依赖随时间变化，也可能被攻击
- **Tool misuse**: Malicious Skills can invoke tools (file operations, bash commands, code execution) in harmful ways
- **工具滥用**：恶意 Skills 可以以有害方式调用工具（文件操作、bash 命令、代码执行）
- **Data exposure**: Skills with access to sensitive data could be designed to leak information to external systems
- **数据泄露**：具有敏感数据访问权限的 Skills 可能被设计为向外部系统泄露信息
- **Treat like installing software**: Only use Skills from trusted sources. Be especially careful when integrating Skills into production systems with access to sensitive data or critical operations
- **像安装软件一样对待**：只使用来自可信来源的 Skills。在将 Skills 集成到具有敏感数据访问权限或关键操作的生产系统时要特别小心

## Available Skills
## 可用的 Skills

### Pre-built Agent Skills
### 预构建的 Agent Skills

The following pre-built Agent Skills are available for immediate use:
以下预构建的 Agent Skills 可立即使用：

- **PowerPoint (pptx)**: Create presentations, edit slides, analyze presentation content
- **PowerPoint (pptx)**：创建演示文稿、编辑幻灯片、分析演示内容
- **Excel (xlsx)**: Create spreadsheets, analyze data, generate reports with charts
- **Excel (xlsx)**：创建电子表格、分析数据、生成带图表的报告
- **Word (docx)**: Create documents, edit content, format text
- **Word (docx)**：创建文档、编辑内容、格式化文本
- **PDF (pdf)**: Generate formatted PDF documents and reports
- **PDF (pdf)**：生成格式化的 PDF 文档和报告

These Skills are available on the Claude API and claude.ai. See the [quickstart tutorial](/docs/en/agents-and-tools/agent-skills/quickstart) to start using them in the API.
这些 Skills 可在 Claude API 和 claude.ai 上使用。请参阅[快速入门教程](/docs/en/agents-and-tools/agent-skills/quickstart)开始在 API 中使用它们。

### Custom Skills examples
### 自定义 Skills 示例

For complete examples of custom Skills, see the [Skills cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction).
有关自定义 Skills 的完整示例，请参阅 [Skills cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)。

## Limitations and constraints
## 限制和约束

Understanding these limitations helps you plan your Skills deployment effectively.
了解这些限制有助于你有效规划 Skills 部署。

### Cross-surface availability
### 跨平台可用性

**Custom Skills do not sync across surfaces**. Skills uploaded to one surface are not automatically available on others:
**自定义 Skills 不会跨平台同步**。上传到一个平台的 Skills 不会自动在其他平台可用：

- Skills uploaded to Claude.ai must be separately uploaded to the API
- 上传到 Claude.ai 的 Skills 必须单独上传到 API
- Skills uploaded via the API are not available on Claude.ai
- 通过 API 上传的 Skills 在 Claude.ai 上不可用
- Claude Code Skills are filesystem-based and separate from both Claude.ai and API
- Claude Code Skills 是基于文件系统的，与 Claude.ai 和 API 都是分开的

You'll need to manage and upload Skills separately for each surface where you want to use them.
你需要为每个想要使用 Skills 的平台单独管理和上传它们。

### Sharing scope
### 共享范围

Skills have different sharing models depending on where you use them:
Skills 根据使用位置有不同的共享模型：
- **Claude.ai**: Individual user only; each team member must upload separately
- **Claude.ai**：仅限个人用户；每个团队成员必须单独上传
- **Claude API**: Workspace-wide; all workspace members can access uploaded Skills
- **Claude API**：工作空间范围；所有工作空间成员都可以访问上传的 Skills
- **Claude Code**: Personal (`~/.claude/skills/`) or project-based (`.claude/skills/`); can also be shared via Claude Code Plugins
- **Claude Code**：个人（`~/.claude/skills/`）或基于项目（`.claude/skills/`）；也可以通过 Claude Code 插件共享

Claude.ai does not currently support centralized admin management or org-wide distribution of custom Skills.
Claude.ai 目前不支持自定义 Skills 的集中管理员管理或组织范围分发。

### Runtime environment constraints
### 运行时环境约束

The exact runtime environment available to your skill depends on the product surface where you use it.
你的 skill 可用的确切运行时环境取决于你使用它的产品平台。

- **Claude.ai**:
- **Claude.ai**：
    - **Varying network access**: Depending on user/admin settings, Skills may have full, partial, or no network access. For more details, see the [Create and Edit Files](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude#h_6b7e833898) support article.
    - **网络访问各异**：根据用户/管理员设置，Skills 可能具有完全、部分或无网络访问权限。有关更多详细信息，请参阅[创建和编辑文件](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude#h_6b7e833898)支持文章。
- **Claude API**:
- **Claude API**：
    - **No network access**: Skills cannot make external API calls or access the internet
    - **无网络访问**：Skills 无法进行外部 API 调用或访问互联网
    - **No runtime package installation**: Only pre-installed packages are available. You cannot install new packages during execution.
    - **无运行时包安装**：只有预安装的包可用。你无法在执行期间安装新包。
    - **Pre-configured dependencies only**: Check the [code execution tool documentation](/docs/en/agents-and-tools/tool-use/code-execution-tool) for the list of available packages
    - **仅预配置依赖**：查看[代码执行工具文档](/docs/en/agents-and-tools/tool-use/code-execution-tool)获取可用包列表
- **Claude Code**:
- **Claude Code**：
    - **Full network access**: Skills have the same network access as any other program on the user's computer
    - **完全网络访问**：Skills 具有与用户计算机上任何其他程序相同的网络访问权限
    - **Global package installation discouraged**: Skills should only install packages locally in order to avoid interfering with the user's computer
    - **不鼓励全局包安装**：Skills 应该只在本地安装包，以避免干扰用户的计算机

Plan your Skills to work within these constraints.
规划你的 Skills 以在这些约束内工作。

## Next steps
## 下一步

<CardGroup cols={2}>
  <Card
    title="Get started with Agent Skills"
    icon="graduation-cap"
    href="/docs/en/agents-and-tools/agent-skills/quickstart"
  >
    Create your first Skill
    创建你的第一个 Skill
  </Card>
  <Card
    title="API Guide"
    icon="code"
    href="/docs/en/build-with-claude/skills-guide"
  >
    Use Skills with the Claude API
    在 Claude API 中使用 Skills
  </Card>
  <Card
    title="Use Skills in Claude Code"
    icon="terminal"
    href="https://code.claude.com/docs/en/skills"
  >
    Create and manage custom Skills in Claude Code
    在 Claude Code 中创建和管理自定义 Skills
  </Card>
  <Card
    title="Use Skills in the Agent SDK"
    icon="cube"
    href="/docs/en/agent-sdk/skills"
  >
    Use Skills programmatically in TypeScript and Python
    在 TypeScript 和 Python 中以编程方式使用 Skills
  </Card>
  <Card
    title="Authoring best practices"
    icon="lightbulb"
    href="/docs/en/agents-and-tools/agent-skills/best-practices"
  >
    Write Skills that Claude can use effectively
    编写 Claude 可以有效使用的 Skills
  </Card>
</CardGroup>
