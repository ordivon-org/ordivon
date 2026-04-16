# 02_Sandbox_Architecture: 环境物理隔离与自适应沙箱

## 一、 工程思想：环境隔离的“物理分层”

`claw-code` 的沙箱架构体现了对 **“执行安全”** 的极致追求。

### 1. 最小化依赖攻击面 (Attack Surface Reduction)
Agent 执行环境不仅仅是逻辑上的隔离，更是物理级的切分。核心哲学是：**即使 Agent 的逻辑被污染，它也无法离开预设的“鱼缸”。**

### 2. 运行时自适应 (Runtime Adaptivity)
系统并不会盲目启动沙箱。它会执行一套详尽的“探针逻辑”来确定当前的底层环境情况：
- **容器感知**：它能识别自己是否已经运行在 Docker、Podman 或 Kubernetes 中。
- **能力探测 (Capability Probing)**：它不通过检查 `unshare` 二进制是否存在来判断，而是通过执行一个轻量级的测试进程（Test-Process）来验证当前内核是否允许创建 User Namespace。
- **降级保护**：如果硬件/内核不支持物理限制，系统会显式切换到基于逻辑校验的限制模式（如前文提到的 Permission Mode），并向用户发出安全警告。

---

## 二、 具体实现逻辑 (Technical Implementation)

### 1. 环境指纹探测 (Container Detection)
在 `sandbox.rs` 中，系统通过以下多重手段确定环境位置：
- **文件标记**：检查 `/.dockerenv` 或 `/run/.containerenv`。
- **cgroup 分析**：读取 `/proc/1/cgroup`。如果内容包含 `docker` 或 `kubepods` 关键字，则判定为受限容器环境。
- **环境变量**：监听 `container` 或 `KUBERNETES_SERVICE_HOST`。

### 2. Linux 命名空间切分 (Namespace Isolation)
对于 Linux 宿主机，核心隔离通过 `unshare` 实现。具体的参数组合非常考究：
```bash
unshare --user --map-root-user --mount --ipc --pid --uts --fork --net
```
- **`--user / --map-root-user`**：将原本的非 root 用户映射为沙箱内的 root，从而让 Agent 能执行合法的包安装操作，但对外部系统没有任何权限。
- **`--mount`**：创建一个独立的挂载空间，防止 Agent 卸载或挂载物理磁盘。
- **`--net` (按需开启)**：切断网络。对于不需要外网权限的任务，这是防止数据外泄的最强防线。

### 3. 沙箱主目录构建 (.sandbox-home)
为了防止 Agent 污染用户的 `$HOME` 目录，系统会动态创建一个隔离的临时主目录：
```rust
let sandbox_home = cwd.join(".sandbox-home");
let sandbox_tmp = cwd.join(".sandbox-tmp");

// 在环境变量中强制覆盖 HOME 和 TMPDIR
let env = vec![
    ("HOME".to_string(), sandbox_home.display().to_string()),
    ("TMPDIR".to_string(), sandbox_tmp.display().to_string()),
];
```

---

## 三、 对 Quant-Agent 的应用建议
1. **数据拉取隔离**：目前我们的数据采集是通过 `ccxt` 直接发起的。如果我们将来允许用户在 Dashboard 编写自定义过滤脚本（Python），我们可以参考其思路，将这些脚本运行在一个**覆盖了 `$HOME` 和 `$TEMP` 路径的子进程**中，防止恶意脚本读取您的 SSH Keys 等敏感信息。
2. **Docker 内层保护**：对于已经在 Docker 中运行的量化镜像，我们可以学习其“cgroup 感知”逻辑，在 Agent 初始化阶段自动输出环境安全报告，提醒用户当前是否开启了必要的隔离参数。
