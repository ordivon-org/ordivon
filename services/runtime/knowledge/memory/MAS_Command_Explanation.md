PowerShell 命令详解：irm https://get.activated.win | iex1. 命令概述这个命令是 Microsoft Activation Scripts (MAS) 的官方一键启动方式。全称：Microsoft Activation Scripts (MAS)
官方站点：https://massgrave.dev/
GitHub：https://github.com/massgravel/Microsoft-Activation-Scripts
作用：通过 PowerShell 远程下载并立即执行一个脚本，启动一个交互式菜单，用于激活 Windows 和 Office 的各种方法（HWID、Ohook、TSforge、Online KMS 等）。

注意：这是一个非官方的开源激活工具，社区广泛使用，但微软官方明确视其为违反许可协议的行为。2. 命令拆解（逐部分解释）powershell

irm https://get.activated.win | iex

irm
全称：Invoke-RestMethod（Invoke-WebRequest 的简化别名）。
功能：向指定的 URL 发送 HTTP GET 请求，下载返回的内容（这里是一个 PowerShell 脚本）。
相当于浏览器访问网页，但把内容以字符串形式返回给 PowerShell。
https://get.activated.win
这是一个重定向/代理链接，实际指向 MAS 项目托管的启动脚本（最新版本）。
它会下载一个较小的引导脚本，该脚本再负责下载完整的 MAS 工具集。
|（管道符）
将 irm 的输出（下载到的脚本内容）直接传递给下一个命令作为输入。
iex
全称：Invoke-Expression。
功能：将字符串当作 PowerShell 代码执行。
这意味着下载到的脚本内容会被立即在当前 PowerShell 进程中运行。

整体流程：irm 从互联网下载脚本文本。
iex 在内存中直接执行该脚本（不保存到磁盘）。
脚本运行后弹出交互菜单，让你选择激活 Windows 或 Office 的方法。

3. 执行前提条件必须以管理员身份运行 PowerShell（右键 → 以管理员身份运行）。
Windows 10 / 11（推荐最新版本）。
需要联网（下载脚本和后续激活组件）。
建议临时关闭 Windows Defender 实时保护（否则可能被拦截或误报）。

4. 执行后会发生什么出现一个黑色命令行菜单（Activation Methods）。
主要选项包括：[1] HWID → Windows 永久激活（硬件绑定）
[2] Ohook → Office 永久激活（最常用）
[3] TSforge → Windows + Office + ESU（扩展安全更新）
[4] Online KMS → 180 天续期激活
[5] Check Activation Status → 查看当前状态
[6] Change Windows Edition → 切换 Windows 版本（如家庭版 → 专业版）
[7] Change Office Edition → 切换 Office 版本

执行后通常需要重启电脑，并重新检查激活状态。5. 安全与风险分析（重要）优点：开源（GitHub 可查看源码）。
不修改核心系统文件（部分方法如 Ohook 使用应用级重定向）。
社区维护较活跃。

主要风险：远程代码执行：irm | iex 是典型的高风险模式。下载的内容完全取决于服务器当时返回什么，存在供应链攻击风险（即使官方链接，也可能被 DNS 污染或 CDN 劫持）。
杀毒软件拦截：Windows Defender、第三方杀软常将此类脚本标记为威胁。
法律风险：违反 Microsoft 最终用户许可协议（EULA），属于非授权激活。
稳定性风险：激活状态可能在 Office/Windows 大更新后失效，需要重新运行。
隐私风险：脚本会连接外部服务器，你的 IP 和硬件信息可能被记录。
系统污染：可能留下计划任务、注册表项、自定义 DLL 等残留，增加后续排障难度。

推荐安全做法（记录在文档中）：优先从 GitHub 下载完整源码，手动审查后再运行（而非直接 irm | iex）。
在虚拟机或非主力设备上测试。
执行前备份重要数据。
执行后运行全盘扫描。

6. 替代执行方式（更安全版本）官方推荐的备用命令（如果主链接被阻挡）：powershell

iex (curl.exe -s --doh-url https://1.1.1.1/dns-query https://get.activated.win | Out-String)

手动方式（推荐用于文档记录）：访问 https://github.com/massgravel/Microsoft-Activation-Scripts
下载 ZIP 源码。
解压后进入 All-In-One-Version 文件夹，双击 MAS_AIO.cmd 或运行对应 PowerShell 文件。

7. 使用建议与注意事项适合场景：临时测试、学习激活机制、无法购买正版时的短期使用。
不适合场景：主力生产环境、需要长期稳定和云端权益（OneDrive、Copilot 等）的设备。
失效处理：激活后若出现问题，可使用脚本的 Troubleshoot 选项，或官方的联机修复功能重置 Office/Windows。
长期推荐：使用正版 Microsoft 365 个人/家庭版、教育版，或网页版 office.com + LibreOffice/WPS 组合。

8. 参考链接（建议存档）官方站点：https://massgrave.dev/
GitHub 项目：https://github.com/massgravel/Microsoft-Activation-Scripts
PowerShell 官方文档：Invoke-RestMethod、Invoke-Expression

