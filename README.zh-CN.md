[English](README.md) | 简体中文

<p align="center">
  <img src="assets/logo.svg" alt="xywdisk 标志" width="112" height="112">
</p>

<h1 align="center">xywdisk</h1>

<p align="center"><strong>47 路执行器输入，34 路红外传感器输出：一份加热晶圆热校准的现场记录。</strong></p>

<p align="center"><em>1,929 条真实对象响应、曾使用它们的雅可比搜索，以及一份关于哪些部分从未跑通的诚实记录。</em></p>

> **状态：归档。** 这是 2025 年 6 月一次私有实验台的公开记录。采集链路确实在真实硬件上跑过，控制链路则没有完成。没有实验台，仓库里的任何东西都无法重新运行；它也不是一个持续维护的软件包。

一眼看过去：

- **47 → 34 的 MIMO 实验台**——47 路 Modbus 设定值（7 路在一块 PLC 上，40 路在另一块上）驱动加热板，34 路红外传感器读取温度场。
- **1,929 行真实采集**（预留了 1,987 行），保存在四个 numpy memmap 文件中：真实输入、真实测量，没有仿真数据。
- **两个 notebook 与两个脚本版本**——可用的采集代码、更早的代理模型控制器，以及后来未能完成的无模型搜索。

## 快速开始

唯一不依赖硬件的入口是数据分析 notebook。它读取仓库中的采集文件，并绘制最小二乘灵敏度。运行前必须先改一处：第一个 cell 申请的是 `shape=9999`，也就是 3.24 MB，而 `real4.47f,34f` 只有 165,240 字节、510 行，numpy 会直接拒绝建立映射。把这一格改成 `shape=510`，或者干脆去掉 `shape=`（按文件实际大小映射），然后就能一路跑到底：

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install numpy matplotlib scikit-learn jupyter
jupyter nbconvert --to notebook --execute data-inspection.ipynb
```


归档的采集脚本需要实验台，**无法端到端运行**：

```bash
pip install numpy scipy pymodbus

export HEAT_HOST=localhost   HEAT_PORT=502
export PTM_HOST=localhost    PTM_PORT=502
export SENSOR_HOST=localhost SENSOR_PORT=9090
export DISK_DATA=real4.47f,34f

python disk.py   # 先在 memmap 形状处报错，再停在下文的裸 `raise` 处
```

所有地址都从环境变量读取，没有任何默认值指向原来的私有实验台网络。

## 现在能做什么

**已经可用，并在硬件上实际跑过**

- 建立两个 Modbus TCP 连接和一个原始 TCP 传感器连接。
- 按设备分别缩放，向两块 PLC 写入设定值（`heat` 乘 100，`ptm` 乘 400）——这个版本里两块拿到的是同一组 7 个值。
- 发送 `b'GetData'`，解析逗号分隔的 ASCII 回复，等待最近 10 个样本稳定后取平均。
- 减去固定基线 `120.1`，把一行 `(47 路输入, 34 路输出)` 追加到 memmap。
- 离线检查采集数据：加载 dtype、拟合线性灵敏度矩阵，并绘制热图。

**当前提交中损坏或未完成的部分**

- `disk.py` 根本跑不起来：`np.memmap(DATA_PATH, '47f,34f', shape=9999)`（第 98 行）申请 3.24 MB，而仓库里的采集文件只有 30–350 kB，numpy 在任何硬件调用之前就会报 `mmap length is greater than file size`。
- 做完和 notebook 同样的那处修改之后，`disk.py` 会停在优化循环之前的无条件的 `raise`（第 107 行），后面的代码永远不会执行。
- 这段不可达代码调用了 `JFit`，而仓库中没有任何地方定义它；即使删掉 `raise`，也会立刻得到 `NameError`。
- `disk.py` 向第二块 PLC 写入的是 `x[:7]` 而不是 `x[7:]`，因此 47 路中有 40 路从未被驱动。`control-loop.ipynb` 里的拆分是正确的；这是后来脚本引入的回归。
- `disk.old.py` 的控制循环本身是连贯的，但它的导入和代理模型只有在实验台连接时才跑过。
- 没有测试，没有时间戳，也没有记录哪个采集文件对应哪次实验。

## 架构

```text
        Modbus TCP：7 路设定值          Modbus TCP：40 路设定值
                 │                                │
                 ▼                                ▼
              heat PLC                           ptm PLC
                 └──────────────┬─────────────────┘
                                ▼
                         加热板 / 晶圆
                                │
                       34 路红外传感器接口
                                │
                                ▼
              disk.py · disk.old.py · control-loop.ipynb
                                │
                                ▼
                  real*.47f,34f（numpy memmap）
                                │
                                ▼
                    data-inspection.ipynb
```

| 组件 | 作用 |
| --- | --- |
| `disk.py` | 较晚的无模型版本：采集，以及一个本应运行的 Gauss–Newton / 信赖域搜索。 |
| `disk.old.py` | 较早的版本：采集、有限差分扩散孪生模型、sklearn 代理模型和可用的控制循环。 |
| `control-loop.ipynb` | 正确的 `F()` 与手写的雅可比 / 线搜索循环。 |
| `data-inspection.ipynb` | 不依赖硬件的采集分析：加载 memmap、灵敏度矩阵、热图。 |
| `real*.47f,34f` | 原始 numpy memmap——文件名本身就是 dtype 字符串。 |
| `docs/project-status.md` | 精简的证据与边界记录。 |

## 采集文件

每一行是一次采集：`f0` 是 47 维设定值，`f1` 是减去基线后的 34 路传感器均值。dtype 为 `[('f0', '<f4', (47,)), ('f1', '<f4', (34,))]`，每行 324 字节，行数就是文件大小除以 324。代码里的 `shape=9999` 只是一笔历史遗留的预留量，不是文件的真实尺寸：它比任何一个采集文件都大，拿它去映射只会报错，而不是读出数据。

| 文件 | 字节数 | 预留行数 | 有数据的行数 |
| --- | ---: | ---: | ---: |
| `real.47f,34f` | 350,244 | 1,081 | 1,080 |
| `real2.47f,34f` | 98,172 | 303 | 292 |
| `real3.47f,34f` | 30,132 | 93 | 48 |
| `real4.47f,34f` | 165,240 | 510 | 509 |
| **合计** | 643,788 | 1,987 | 1,929 |

一行只要 `f1` 不全为零，就算作有数据。空缺都事出有因：`real2` 在第 287、289、290 行是空洞，`real3` 只写到 93 行中的第 48 行，而且 `real3` 存下了 70 组设定值却只有 48 行测量——有 22 次指令发了出去，读数却没有回来。单位、行顺序以及每次运行的对应关系都没有留下记录。

## 仓库结构

```text
.
├── README.md
├── README.zh-CN.md
├── LICENSE
├── disk.py
├── disk.old.py
├── control-loop.ipynb
├── data-inspection.ipynb
├── real.47f,34f
├── real2.47f,34f
├── real3.47f,34f
├── real4.47f,34f
├── assets/
│   └── logo.svg
├── CONTRIBUTING.md
└── docs/
    └── project-status.md
```

## 开发说明

这里没有构建、打包、测试或 CI。它是一份定格的归档，不是项目模板。

- 采集文件必须逐字节保持不变。
- 新的结论写进 `docs/project-status.md`，并让证据紧跟结论。
- 把脚本当作历史材料。如果要整理，请让损坏的版本与可用的版本并存，保留版本之间的演化关系。
- 不要把实验台地址、凭据或私有网络细节写进仓库。

## 如何贡献

欢迎带证据的更正，尤其是实验元数据、每个采集文件对应的运行，以及传感器读数的物理单位。具体规则都写在 [CONTRIBUTING.md](CONTRIBUTING.md) 里：哪些内容在范围内、issue 需要给出什么证据、PR 允许改动什么。

## 路线图

**已实现**

- [x] 硬件采集：Modbus 写入、`GetData` 读取、等待稳定后取均值、追加 memmap。
- [x] 四个真实采集文件：预留 1,987 行，其中 1,929 行有数据。
- [x] 离线灵敏度分析与热图检查。
- [x] 用环境变量替换所有私有实验台地址。
- [x] AGPL-3.0-only 许可与一份有证据的记录。

**计划中**

- [ ] 修正两个 notebook 与 `disk.py` 里的 `shape=9999` 预留量，让采集文件能按原样映射。
- [ ] 找回实验元数据：行顺序、单位，以及每个文件对应的运行。
- [ ] 修复 `disk.py` 的尾部，替换未定义的 `JFit` 调用。
- [ ] 修正 `x[:7]` / `x[7:]` 的执行器分组回归。
- [ ] 构建离线回放工具，让没有实验台的人也能研究这批数据。

这些只是可能的方向，不是承诺；目前没有维护者在推进它们。

## 未来设想

真正值得留下的是这批采集数据。一个小的回放工具就能把它们变成系统辨识、稀疏雅可比估计和安全设定值搜索的试验场，而且完全不必接触原来的硬件。理想的结果不是复活实验台脚本，而是一份干净、诚实的数据集，以及一个可供他人与后来的 [`disk`](https://github.com/ZisIsNotZis/disk) 项目对照的参考控制器。

## 沿革

本仓库是作者已发布的 `disk` 项目更早、更原始的版本。`disk.old.py` 与那个仓库的 `disk.py` 几乎是同一份祖先代码；这份快照还保留了采集数据和未完成的较晚版本。`xywdisk` 是原始私有归档迁移时的标签，不是已发布的 `disk` 仓库。

## 许可证

[AGPL-3.0-only](LICENSE)，版权所有 (C) 2025 ZisIsNotZis。原始私有目录没有许可证；这份公开归档以 GNU Affero 通用公共许可证第 3 版发布。
