# OneDrive / SharePoint 使用指南

## 推荐的文件夹结构

在 OneDrive 或 SharePoint 的团队文件夹中，建议如下组织：

```
📁 团队共享文件夹/
├── 📁 power-trading-pipeline/     ← 整个项目放这里
│   ├── 📁 data/raw/               ← 大家往这里放原始数据
│   ├── 📁 outputs/                ← 结果在这里取
│   ├── 📄 run_pipeline.bat        ← 双击运行
│   └── ...
```

## 日常操作流程

1. **等 OneDrive 同步完成**（托盘图标显示绿色对勾 ✓）
2. 把新下载的数据文件放入 `data/raw/对应文件夹/`
3. **等同步完成**
4. 双击 `run_pipeline.bat`
5. 去 `outputs/` 取结果

## 常见问题

### "文件被锁定"错误
- 原因：OneDrive 正在同步，或有人在 Excel 中打开了文件
- 解决：等一会儿再运行，或请同事关闭文件

### 多人协作
- **规则：同一时间只有一个人运行管道**
- 建议在团队群里喊一声"我要跑管道了"
- 如果需要更严格的控制，后续可以加锁机制

### 大文件性能慢
- OneDrive 同步大文件时会很慢
- 超过 50MB 的文件建议先下载到本地 `C:\temp\`，处理完再同步回去
- 或者在 `configs/pipeline.yaml` 中配置只处理特定日期范围

### 文件冲突
- OneDrive 冲突文件会生成类似 `xxx (1).csv` 的副本
- 管道会忽略这些冲突副本（只读取符合命名规则的文件）
- 定期清理冲突文件

## Git 版本管理（可选）

如果团队使用 Git：

```
.gitignore 建议内容：

data/raw/**/*.csv
data/raw/**/*.xlsx
data/processed/
outputs/
logs/
__pycache__/
*.pyc
~$*                    # Excel 临时文件
*.tmp
```

即：**代码进 Git，数据不进 Git**。数据通过 OneDrive 同步。
