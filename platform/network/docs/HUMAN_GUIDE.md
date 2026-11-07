# Ordivon Network｜Human 操作手册

**适用对象：** 使用、维护 Ordivon 的人类用户。需要修改实现或自动化执行的 Agent，请阅读 [Agent 操作契约](AGENT_GUIDE.md)。这里按 Diátaxis 的方法区分「入门、操作、参考、原理」，避免让用户阅读整个源码才能知道下一步怎么做。

## 一、先弄清楚 Network 能做什么

**Ordivon Network 不是把整个电脑强制接入 VPN 的万能开关。** 它负责组合成熟的网络能力，并证明指定应用的真实网络路径。

    应用 → 各自的网络策略/本地代理 → 共享 Carrier
                                      → 一个 Gluetun/Surfshark WireGuard
                                      → 外部互联网

    Linux 通用底座：dnsproxy + sing-box + Blackbox Exporter + Prometheus
    Windows：应用进程自行绑定已配置的本地代理
    iPad/iPhone：设备端必须主动选择 Tailscale Exit Node

只有一个共享的物理 WireGuard 身份。Network 的通用底座、物理 Provider、每个 Consumer 都是不同模块。Windows/WSL 开机归 Workstation；任务与 Workspace 归 Runtime；凭据归 Security；业务目的地策略归相应 Consumer。

**重要区别：** VPN 进程运行、服务返回 READY、某次测试返回 HTTP 200，都不自动证明所有应用或手机正在使用 VPN。

## 二、五分钟入门

从项目的 platform/network/ 目录运行以下现有原生命令：

| 你想知道什么 | 直接运行 | 实际证明了什么 |
| --- | --- | --- |
| 有哪些实际能力？ | task --list-all | 当前 Owner 可用的任务接口 |
| Linux 通用 Network 是否健康？ | task core:verify | 已安装配置、DNS、代理、监控的真实读回 |
| Surfshark 隧道是否正常？ | task provider:gluetun:verify | Gluetun 配置与实际 Provider 路径 |
| VPN 当前走哪个公网出口？ | task provider:gluetun:observe-exit | 通过 https://ipinfo.io/json 进行一次真实 HTTPS 采样 |
| Codex 网络消费者是否正常？ | task consumer:codex:verify | Linux 侧范围受限的 HTTPS 代理与拒绝行为 |
| 手机 Exit Node 服务端是否就绪？ | task consumer:mobile-tailnet-exit:verify | 服务器端公告、批准、命名空间与 Provider |
| 配置源码是否有效？ | task all:validate | 静态配置有效，不能代替应用实测 |
| 受限出口路由符合授权契约吗？ | mise run formal | 原生 Z3 对八组 Consumer 的符号化规格精化证明；不等于真实 VPN 应用已验证 |

Claude、Finance、Browserless、Discord、Model Provider、Supply Chain、Chat Ingress、X Reality、Windows Chrome 等应用各有自己的 Consumer 任务。运行 task --list-all 找到真实接口，不要推测任务名。

## 三、具体怎么使用

### 1. 查 VPN 出口，而不是看客户端图标

1. 执行 task provider:gluetun:verify。
2. 执行 task provider:gluetun:observe-exit，观察返回的 IP、国家和网络组织。
3. 执行所需应用自己的 consumer:*:verify。
4. 最后从**那个应用本身**发起真实请求，才可以检查应用是否正确走代理。

IPinfo 的结果只代表这一次指定 HTTPS 连接；之后 Gluetun 可能原生切换服务器。Windows 或 Linux 主机的直接出口可以与 VPN 出口不同，这本身不等于故障。

### 2. Windows 原生 Google Chrome 自动使用 VPN

Chrome 使用 **自身的原生 Windows 策略**，而不是 Surfshark 桌面 GUI 或 Windows 全局系统代理。正确配置时，Windows 用户侧 `HKCU\Software\Policies\Google\Chrome` 中的 `ProxySettings` 应采用 `ProxyMode=fixed_servers` 和 `ProxyServer=http://127.0.0.1:19781`，并以 Chrome 实际加载的策略为准。这份浏览器策略的长期配置与开机恢复归 **Workstation**；Network 只拥有下游代理、出口及消费者的验证。

1. 在 Windows Chrome 中访问 `chrome://policy`，确认实际加载的 `ProxySettings`，不要只检查注册表或代理端口。
2. 访问 https://ipinfo.io，比较 Chrome 的公网 IP 与 Linux 的 `task provider:gluetun:observe-exit` 结果。
3. 检查 `task consumer:windows-real-chrome:verify`，验证 Linux 代理 SourceCut 和真实 HTTPS 后果。

验证时可以使用 Chrome 原生无界面模式和新的临时配置目录，且**不要传入代理命令行参数**，否则无法证明策略自动生效。用完删除临时目录。这只能证明被测试的 Chrome HTTPS 请求，**不自动涵盖 WebRTC、所有扩展、DNS/IPv6 泄漏或正常登录资料是否选择了相同设置**。不需要新建专用 Chrome 启动器。

### 3. Windows Codex / ChatGPT锛氭甯稿惎鍔ㄨ嚜鍔ㄦ帴鍏?VPN

褰撳墠 Windows 浜や簰鐢ㄦ埛鐨勭郴缁熶唬鐞嗘寚鍚?Ordivon 鐨?127.0.0.1:19781锛孿nCodex 鐨勫師鐢?respect_system_proxy 鍔熻兘宸插惎鐢ㄣ€傜洿鎺ョ偣鍑绘闈㈠簲鐢╘n鍗冲彲浣跨敤宸查厤缃殑浠ｇ悊锛屼笉闇€瑕?PowerShell 鍖呰鑴氭湰鎴栫壒娈婂惎鍔ㄥ懡浠ゃ€俓n
Linux 鐨?127.0.0.1:19982 鏄?*鍙︿竴涓寖鍥村彈闄愮殑 Codex Consumer**锛孿n骞堕潪 Windows Desktop 鐨勯粯璁ょ綉缁滅瓥鐣ャ€侰hrome 鍒欎娇鐢ㄨ嚜宸辩殑鍘熺敓浠ｇ悊绛栫暐銆俓n
楠屾敹椤哄簭锛氱郴缁熶唬鐞嗕笌 Codex 璁剧疆 鈫?瀹為檯妗岄潰杩涚▼鐨勬湰鍦颁唬鐞嗚繛鎺n鈫?搴旂敤鑷繁鐨勭湡瀹?HTTPS 璇锋眰 鈫?Network 涓嬫父 Consumer 涓?Gluetun銆俓n鏈夐檺鐨?TCP 鏍锋湰涓嶈兘璇佹槑鎵€鏈?DNS銆乁DP 鎴栨彃浠惰矾寰勫潎鏃犵粫琛屻€俓nWindows 閰嶇疆鎸佷箙鍖栧綊 Workstation锛汵etwork 璐熻矗杞戒綋銆佸彈闄愯矾鐢卞拰
鐪熷疄娑堣垂鑰呴獙鏀躲€傛棫鐨勬墜鍔?CLI 鍚姩鍣ㄥ凡閫€褰癸紝涓嶅簲閲嶆柊寮曞叆銆俓n
### 4. 让 iPad 或 iPhone 使用电脑提供的 VPN 出口

服务器已通过 Tailscale 广告批准的 Exit Node：**ordivon-surfshark-exit**。

1. 在需要使用 VPN 的 **每台设备**打开 Tailscale。
2. 选择这个已批准的 Exit Node；不能只看服务器的 READY 标识。
3. 使用同一台 iPad/iPhone 的浏览器打开 https://ipinfo.io，核对公网出口。
4. 单独验证 Wi-Fi、蜂窝移动网络切换后的 DNS 和出口。

如果某台 iOS 设备离线，服务器无法代替它完成选择和出口验收。服务端运行正常 ≠ 手机流量已经被转发。

### 鍚屼竴灞€鍩熺綉鐨?iPad 鐩磋繛浼樺寲

褰撳墠鍚屼竴 LAN 鍐呭凡瀹炴祴锛歩Pad 鍒板嚭鍙ｈ妭鐐圭敱涓滀含 DERP 涓户绾?400ms
鏀瑰杽涓?Tailscale 鐩磋繛绾?8鈥?ms銆備娇鐢?Gluetun 瀹樻柟鏀寔鐨刓nFIREWALL_OUTBOUND_SUBNETS=192.168.0.0/24 瀹炵幇灞€鍩熺綉閫氫俊銆俓n
**娉ㄦ剰锛氳繖鏄鏁翠釜灞€鍩熺綉缃戞鐨勫嚭绔欎緥澶栵紝涓嶆槸浠呮斁琛屼竴涓?UDP 绔彛銆?*
鍏綉璇锋眰浠嶉』閫氳繃 Surfshark銆俰Pad 鍒囨崲鍒板叾浠栫綉缁滃悗鍙兘鎭㈠浣跨敤
DERP锛涘鏋滃搴?LAN 缃戞鏇存敼锛岄渶瑕侀噸鏂版鏌?CIDR銆佸疄闄呰矾鐢便€乗n瀹㈡埛绔?IPinfo 涓?DNS锛屼笉鑳藉彧鍑?Exit Node 鏄剧ず READY 灏遍獙鏀躲€俓n
Surfshark 褰撳墠娌℃湁鍙敤鐨勫叕缃?IPv6 鍑哄彛锛屼笉蹇呰拷姹?IPv6 寰楀垎锛孿n浣嗕篃涓嶅緱璁?IPv6 缁曡繃宸查€変腑鐨勫嚭鍙ｇ洿鎺ヨ闂叕缃戙€俓n
### 5. 改配置或恢复服务

提交代码前，从 platform/network/ 执行：

    mise run ci
    mise run behavior
    task all:validate

检查生产配置，执行 task core:verify 和受影响的 consumer:*:verify。task core:converge 已采用 Go Task 原生幂等机制：**当前配置已通过验收时不会重复安装**；只有修复确有必要时才可能重新安装或重启通用 Network 服务。Gluetun 物理 Provider 的准备与启动是不同操作，不要混为一谈。

源码发布走仓库现有的 GitHub PR、必需 CI、合并队列；只有合并之后再进行生产读回，才算实际发布完成。

## 四、出问题时先找谁

| 表现 | 先检查 | 真正的 Owner |
| --- | --- | --- |
| Linux 通用 DNS/HTTP 代理不能用 | task core:verify | Network 通用底座 |
| 共享 VPN 出口异常 | task provider:gluetun:verify；一次 IPinfo 采样 | Gluetun Provider |
| DoH/DoT 超时、VPN 反复重连 | 当前 Gluetun 加载的 DNS、健康检查目标；独立 IP/TLS 与 DNS 观测 | Provider 原生 DNS/健康 |
| 只有一个应用域名被拒绝 | 对应 Consumer 的实际路由策略与请求 | 对应 Consumer |
| 旧 Windows Codex 不使用新代理 | 进程启动时间、实际环境变量、套接字 | Codex Consumer / Workstation |
| iPad/iPhone 出口不符合预期 | 设备端 Exit Node 选择、设备上的 IPinfo | iOS Tailscale 客户端 |
| 重启 Windows 后 WSL 没启动 | Windows 启动 → WSL → systemd → Podman | Workstation |
| 监控显示正常但配置漂移 | 生产 SourceCut、Prometheus 原生加载的抓取池 | Network Observability |

### 多个应用同时断网时如何定位

从已经存在的 Prometheus 读取 `NetworkCorrelatedConsumerOutage`：它只在 PyPI、Codex 与 Claude **三路每分钟 HTTPS 探针最近 90 秒都有样本、并持续两分钟同时失败**时成立。该信号是共享路径优先排查的线索，不是 Gluetun 根因证明；任何一个探针缺席则须查看已有的单独 `absent()` 告警，不能把缺测当作成功或失败。

    curl -fsS http://127.0.0.1:29090/api/v1/alerts |
      jq '.data.alerts[] | select(.labels.alertname=="NetworkCorrelatedConsumerOutage")'

随后顺序检查 `task provider:gluetun:verify`、Gluetun 原生日志、`task provider:gluetun:observe-exit`，最后复测受到影响的 Consumer。代理 CONNECT 200 但 HTTPS TLS 超时属于 **尚未完成源站请求**，不能宣布 READY；`systemctl active` 也不能取代源站探测。先使用 Gluetun 自带健康恢复，**不要在故障时另开一条 WireGuard 或重启全部 Consumer**。IPinfo 的未认证端点有共享限流，只用于一次性出口采样，不用来替代 Prometheus 健康检查。

**DNS 故障与 VPN 故障不能混为一谈。** DNS 超时既可能导致健康检查受影响，也可能只是底层隧道故障的结果。应分别验证原生 IP/TLS 健康目标与 DNS 上游。不要为此添加第二个 VPN Watchdog：Gluetun 自带健康检查与自动恢复。

## 五、如何判断文件或数据可以删除？

判断标准不是创建时间、名称中含有 legacy 或文件暂时没被 grep 到，而是**有没有真实消费者**。任务可能通过 glob、pytest、systemd、Podman、运行时状态或恢复链间接消费文件。

- 不再引用的匿名 Podman 卷，通过 Podman 原生卷操作删除。
- Runtime Workspace 只通过 Runtime 生命周期接口关闭；如果消费关系还没有释放，不直接删除底层 Git worktree。
- 仍用于合法回滚的 Provider 配置和仍有消费者的源文件不当作垃圾。
- 不另外建立 Network 专属垃圾回收控制器、状态数据库或后台清理任务。

## 六、文档入口

- [Network 架构、边界和组成](ARCHITECTURE.md)：为什么这么设计
- [能力验收矩阵](ACCEPTANCE_MATRIX.md)：各种能力需要哪些证据
- [机制选择矩阵](DECISION_MATRIX.md)：成熟组件如何取舍
- [Agent 操作契约](AGENT_GUIDE.md)：可执行的 Agent 工程指引
- [Diátaxis](https://diataxis.fr/)：教程、操作、参考和解释的专业文档范式
- [C4 Model](https://c4model.com/)：跨角色理解系统、容器与组件
- [Gluetun 原生 DNS 选项](https://github.com/qdm12/gluetun-wiki/blob/main/setup/options/dns.md)
- [Gluetun 原生健康检查](https://github.com/qdm12/gluetun-wiki/blob/main/setup/options/healthcheck.md)
