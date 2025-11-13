#!/usr/bin/env python
"""
KYC Agent CLI - Interactive Command Line Interface

一个交互式的 KYC 文档处理 Agent CLI 工具。
支持多轮对话、文档分析、信息提取等功能。
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock
)

# Load environment variables
load_dotenv()

console = Console()


class KYCAgentCLI:
    """KYC Agent 交互式命令行工具"""

    def __init__(self):
        self.agent = None
        self.kyc_docs_path = Path(__file__).parent / "kyc_documents"
        self.session_active = False
        self.show_react_steps = False  # 是否显示 ReAct 过程

    def check_api_key(self) -> bool:
        """检查 API Key 是否配置"""
        if not os.getenv("ANTHROPIC_API_KEY"):
            console.print(
                "[red]错误：未找到 ANTHROPIC_API_KEY 环境变量[/red]"
            )
            console.print(
                "请在 .env 文件中配置你的 API Key\n"
                "参考：https://console.anthropic.com/settings/keys"
            )
            return False
        return True

    async def initialize_agent(self):
        """初始化 KYC Agent"""
        try:
            options = ClaudeAgentOptions(
                allowed_tools=["Read", "Write", "Bash", "Grep", "Glob", "Search"],
                permission_mode='acceptEdits',
                cwd=str(self.kyc_docs_path.absolute()),
            )

            self.agent = ClaudeSDKClient(options=options)

            # 重要：必须先连接才能使用
            await self.agent.connect()
            self.session_active = True

            console.print(
                Panel(
                    f"[green]✓ KYC Agent 初始化成功[/green]\n\n"
                    f"工作目录：{self.kyc_docs_path}\n"
                    f"可用工具：{', '.join(options.allowed_tools)}",
                    title="Agent 状态",
                    border_style="green"
                )
            )
        except Exception as e:
            console.print(f"[red]初始化失败：{e}[/red]")
            sys.exit(1)

    def show_welcome(self):
        """显示欢迎信息"""
        welcome_text = """
# 🤖 KYC Agent CLI - 智能文档处理助手

欢迎使用 KYC Agent！我可以帮你：

- 📋 列出和统计文档（快速、安全）
- 🔍 搜索文件和提取元信息
- 📊 预览文本文件内容（前几行）
- ✅ 验证文档完整性
- 💡 回答关于企业材料的问题

## 🛡️ 大文件保护机制

为避免读取超大文件导致错误，Agent 会：
- ✅ 优先使用文件系统命令（ls、find）
- ✅ 自动跳过大于 500KB 的文件
- ✅ 仅预览文本文件的前几行
- ✅ 对于 PDF/图片/音频，只返回文件信息

## 💡 推荐的提问方式

**✅ 推荐（高效、安全）：**
- `列出所有文档及其大小`
- `有哪些 Excel 文件？`
- `找出所有关于比亚迪的文档`
- `财务报表目录下有什么文件？`

**⚠️ 避免（可能超时）：**
- `分析所有文档的内容`
- `读取所有 PDF 文件`

## 📝 快速命令

- `/list` - 列出所有文档（推荐使用）
- `/debug` - 开启/关闭调试模式（查看 ReAct 推理过程）
- `/help` - 查看帮助
- `/quit` - 退出

## 🔍 ReAct 调试模式

输入 `/debug` 可以看到 Agent 的完整推理过程：
- 🔧 使用了哪些工具
- ✅ 每个工具返回什么结果
- 📊 总共执行了多少次工具调用

开始提问吧！
        """
        console.print(Markdown(welcome_text))

    def show_help(self):
        """显示帮助信息"""
        table = Table(title="可用命令", show_header=True, header_style="bold cyan")
        table.add_column("命令", style="green", width=20)
        table.add_column("说明", style="white")

        commands = [
            ("/help", "显示此帮助信息"),
            ("/list", "列出 kyc_documents 目录下的所有文件"),
            ("/status", "显示 Agent 当前状态"),
            ("/debug", "切换调试模式（显示 ReAct 推理过程）"),
            ("/clear", "清除屏幕"),
            ("/quit 或 /exit", "退出程序"),
            ("其他任何问题", "直接输入你的问题，Agent 会自动处理"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        console.print(table)
        console.print()

        # 示例问题
        examples_table = Table(
            title="示例问题", show_header=True, header_style="bold magenta"
        )
        examples_table.add_column("问题类型", style="cyan", width=20)
        examples_table.add_column("示例", style="white")

        examples = [
            ("文档列表", "有哪些文档？给我列个清单"),
            ("信息提取", "提取营业执照上的公司名称和注册资本"),
            ("文档分析", "分析法人王传福的征信报告"),
            ("数据汇总", "汇总主要客户和供应商的信息"),
            ("完整性检查", "检查企业材料是否齐全，缺少什么"),
            ("财务分析", "分析财务报表中的关键指标"),
        ]

        for q_type, example in examples:
            examples_table.add_row(q_type, example)

        console.print(examples_table)

    def show_status(self):
        """显示 Agent 状态"""
        status_panel = Panel(
            f"[green]✓ Agent 运行中[/green]\n\n"
            f"工作目录：{self.kyc_docs_path}\n"
            f"会话状态：{'活跃' if self.session_active else '未初始化'}\n"
            f"模型：Claude Sonnet 4.5",
            title="Agent 状态",
            border_style="green"
        )
        console.print(status_panel)

    def list_documents(self):
        """列出所有文档"""
        console.print("[cyan]正在扫描文档目录...[/cyan]")
        try:
            all_files = list(self.kyc_docs_path.rglob("*"))
            files = [f for f in all_files if f.is_file() and not f.name.startswith('.')]

            if not files:
                console.print("[yellow]未找到任何文档[/yellow]")
                return

            table = Table(title=f"文档列表 (共 {len(files)} 个文件)", show_header=True)
            table.add_column("序号", style="cyan", width=6)
            table.add_column("文件名", style="white")
            table.add_column("大小", style="green", width=12)
            table.add_column("路径", style="dim")

            for idx, file in enumerate(files, 1):
                size = file.stat().st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"

                rel_path = file.relative_to(self.kyc_docs_path)
                table.add_row(str(idx), file.name, size_str, str(rel_path.parent))

            console.print(table)
        except Exception as e:
            console.print(f"[red]列出文档失败：{e}[/red]")

    async def process_command(self, user_input: str) -> bool:
        """处理用户命令"""
        user_input = user_input.strip()

        if not user_input:
            return True

        # 处理特殊命令
        if user_input in ["/quit", "/exit", "/q"]:
            console.print("[yellow]再见！[/yellow]")
            return False

        if user_input == "/help":
            self.show_help()
            return True

        if user_input == "/list":
            self.list_documents()
            return True

        if user_input == "/status":
            self.show_status()
            return True

        if user_input == "/debug":
            self.show_react_steps = not self.show_react_steps
            status = "开启" if self.show_react_steps else "关闭"
            console.print(f"[cyan]调试模式已{status}[/cyan]")
            if self.show_react_steps:
                console.print("[dim]现在会显示 Agent 的推理和工具使用过程[/dim]")
            return True

        if user_input == "/clear":
            os.system('clear' if os.name == 'posix' else 'cls')
            return True

        # 处理普通问题 - 调用 Agent（异步）
        await self.query_agent(user_input)
        return True

    async def query_agent(self, question: str):
        """向 Agent 提问（优化版：智能避免大文件）"""
        try:
            console.print(f"\n[dim]正在处理你的问题...[/dim]\n")

            # 添加系统提示，指导 Agent 安全地处理文件
            enhanced_prompt = f"""
用户问题：{question}

⚠️ 重要提示（请务必遵守）：

1. **文件大小限制**：
   - 读取任何文件前，先用 `ls -lh` 或 `stat` 检查文件大小
   - 跳过大于 500KB 的文件（PDF、图片、音频等）
   - 对于这些大文件，只返回文件名、大小、类型等元信息

2. **读取文件时的限制**：
   - 使用 `head -n 20` 而不是 `cat`，只读取前 20 行
   - Excel/CSV 文件：只读取前几行数据
   - 文本文件：只读取前 500 字节

3. **推荐的命令**：
   - 列出文件：`ls -lh` 或 `find . -type f`
   - 查看大小：`du -h` 或 `stat`
   - 预览文本：`head -n 20 filename`
   - 搜索内容：`grep -n "关键词" filename | head -n 10`

4. **必须跳过的文件类型**：
   - 图片：.png, .jpg, .jpeg, .gif
   - PDF：.pdf
   - 音频：.m4a, .mp3, .wav
   - 视频：.mp4, .avi, .mov
   - 对这些文件只报告元信息

5. **优先策略**：
   - 优先使用文件系统命令（ls, find, du）获取信息
   - 需要内容时，先确认文件大小安全
   - 分批处理，不要一次性读取多个文件

请按照这些规则处理用户的问题。
"""

            # 发送增强后的查询
            await self.agent.query(enhanced_prompt)

            # 接收并显示响应（支持显示 ReAct 过程）
            response_text = ""
            tool_use_count = 0

            async for message in self.agent.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        # 显示文本回答
                        if isinstance(block, TextBlock):
                            response_text += block.text

                        # 调试模式：显示工具使用
                        elif isinstance(block, ToolUseBlock) and self.show_react_steps:
                            tool_use_count += 1
                            console.print(
                                Panel(
                                    f"[cyan]工具名称:[/cyan] {block.name}\n"
                                    f"[cyan]工具输入:[/cyan] {block.input}",
                                    title=f"🔧 工具调用 #{tool_use_count}",
                                    border_style="cyan",
                                    expand=False
                                )
                            )

                        # 调试模式：显示工具结果
                        elif isinstance(block, ToolResultBlock) and self.show_react_steps:
                            result_preview = str(block.content)
                            if len(result_preview) > 200:
                                result_preview = result_preview[:200] + "..."

                            console.print(
                                Panel(
                                    f"[green]{result_preview}[/green]",
                                    title=f"✅ 工具结果 #{tool_use_count}",
                                    border_style="green",
                                    expand=False
                                )
                            )

            # 显示 Agent 的最终响应
            if response_text:
                console.print(Panel(
                    Markdown(response_text),
                    title="💬 Agent 回答",
                    border_style="blue"
                ))
            else:
                console.print("[yellow]Agent 没有返回文本响应[/yellow]")

            # 调试模式：显示统计
            if self.show_react_steps and tool_use_count > 0:
                console.print(f"\n[dim]本次对话使用了 {tool_use_count} 次工具调用（ReAct 循环）[/dim]")

        except Exception as e:
            error_msg = str(e)
            if "exceeded maximum buffer size" in error_msg or "JSON message exceeded" in error_msg:
                console.print(
                    "[red]❌ 错误：响应数据过大（Agent 可能读取了大文件）[/red]\n\n"
                    "[yellow]💡 建议：[/yellow]\n"
                    "1. 使用 [cyan]/list[/cyan] 命令查看文档列表（快速、安全）\n"
                    "2. 重新提问，明确指定只需要文件列表或摘要\n"
                    "3. 避免使用'分析所有文档'这类宽泛的问题\n\n"
                    "[dim]示例：'列出所有 Excel 文件的文件名和大小'[/dim]"
                )
            else:
                console.print(f"[red]处理失败：{error_msg}[/red]")
                console.print("[yellow]提示：确保你的问题清晰明确，Agent 会尽力帮助你。[/yellow]")

    async def run(self):
        """运行 CLI 主循环"""
        # 检查 API Key
        if not self.check_api_key():
            sys.exit(1)

        # 显示欢迎信息
        self.show_welcome()

        # 初始化 Agent（异步）
        await self.initialize_agent()

        console.print("\n[bold green]开始对话吧！输入 /help 查看帮助[/bold green]\n")

        try:
            # 主循环
            while True:
                try:
                    user_input = Prompt.ask(
                        "\n[bold cyan]你[/bold cyan]",
                        default=""
                    )

                    if not await self.process_command(user_input):
                        break

                except KeyboardInterrupt:
                    console.print("\n[yellow]按 Ctrl+C 再次退出，或输入 /quit[/yellow]")
                    try:
                        confirm = Prompt.ask("确认退出？", choices=["y", "n"], default="n")
                        if confirm == "y":
                            break
                    except KeyboardInterrupt:
                        console.print("\n[yellow]再见！[/yellow]")
                        break
                except Exception as e:
                    console.print(f"[red]发生错误：{e}[/red]")
        finally:
            # 确保断开连接
            if self.agent and self.session_active:
                console.print("\n[dim]正在断开连接...[/dim]")
                await self.agent.disconnect()
                console.print("[green]连接已断开[/green]")


def main():
    """主入口"""
    cli = KYCAgentCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
