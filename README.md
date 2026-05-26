# Caomei — 草莓分割检测系统

YOLOv8s-seg 草莓分割模型，部署在 Atlas 200 DK（Ascend 310）。

基于 StrawDI_Db1 温室草莓数据集训练，mAP50 0.922。提供 Flask 后端检测 API 和 Vue 3 前端界面，支持本地 ONNX 推理和 Atlas 远程推理。

---

## 项目架构

```
caomei/
├── backend/                          # Flask Web 后端
│   ├── app.py                        # 应用入口
│   ├── config.py                     # 配置（模型路径、Atlas 地址、目录）
│   ├── config_settings.json          # 用户设置覆盖
│   ├── extensions.py                 # SQLAlchemy
│   ├── migrate_db.py                 # 数据库迁移
│   ├── requirements.txt
│   ├── data.db                       # SQLite
│   ├── detectors/                    # 推理引擎
│   │   ├── yolo_seg.py               # ONNX Runtime 推理（nc=1 适配）
│   │   ├── local_detector.py         # 本地推理封装
│   │   └── atlas_client.py           # Atlas 远程客户端
│   ├── services/                     # 业务逻辑
│   │   ├── detect_service.py         # 检测 + 视频 + 批量
│   │   ├── annotate.py               # 标注图画框
│   │   ├── video_processor.py        # 视频逐帧处理
│   │   └── stats_service.py          # 统计
│   ├── routes/                       # API 路由
│   │   ├── detect.py                 # /api/detect, /video, /batch
│   │   ├── settings.py               # /api/settings
│   │   └── stats.py                  # /api/stats
│   ├── models/                       # ORM + 类别
│   │   ├── detect_record.py
│   │   └── classes.txt               # "Strawberry"
│   ├── uploads/                      # 上传图片
│   ├── videos/                       # 标注视频
│   └── annotated/                    # 标注图
│
├── frontend/                         # Vue 3 前端
│   ├── index.html
│   ├── vite.config.js                # Vite 代理配置
│   ├── package.json
│   ├── dist/                         # 构建产物
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/index.js              # Axios API 封装
│       ├── router/index.js
│       ├── views/
│       │   ├── DetectView.vue        # 检测页（单图/视频/批量）
│       │   ├── HistoryView.vue       # 历史记录
│       │   ├── DashboardView.vue     # 统计看板
│       │   └── SettingsView.vue      # 设置页
│       └── components/
│           ├── ImageUploader.vue
│           ├── ResultViewer.vue
│           ├── HistoryTable.vue
│           ├── StatsCards.vue
│           └── TrendChart.vue
│
└── training/                         # 训练全流程
    ├── scripts/
    │   ├── train_strawberry.py        # 训练入口
    │   ├── export_strawberry_onnx.py  # 导出 ONNX（opset=11）
    │   ├── convert_strawdi.py         # StrawDI → YOLOv8 seg 格式
    │   ├── export_onnx2.py            # ONNX 导出（注入 C2fNAM）
    │   ├── test_v2.py                 # 推理测试
    │   ├── test_onnx_windows.py       # Windows ONNX 验证
    │   ├── test_atlas_server.py       # Atlas 板端服务测试
    │   └── ultralytics1/             # 定制模块 (C2fNAM)
    ├── datasets/
    │   └── strawdi/                   # YOLOv8 seg 格式（训练/验证/测试）
    ├── weights/
    │   ├── strawberry_v2_best.pt      # 训练结果
    │   ├── strawberry_v2_last.pt
    │   ├── train19_best.pt            # 基模型
    │   └── best.onnx                  # 导出 ONNX
    ├── predict/                       # 推理测试
    │   ├── infer_strawberry.py
    │   ├── strawberry.jpg
    │   └── strawberry.onnx
    ├── results/
    │   └── strawberry-v2/             # 训练曲线、验证样本
    └── deployment/
        └── vart_py/                   # Atlas 200 DK 推理
            ├── yolo_acllite.py        # ACLLite 推理（nc=1）
            ├── server_acllite.py      # HTTP 推理服务
            ├── model_data/            # 类别文件
            ├── data/                  # 测试图片
            └── out/                   # 推理结果
```

---

## 检测模式

| 模式 | 路由 | 说明 |
|------|------|------|
| 单图检测 | POST `/api/detect` | 上传单张图片，返回标注图 |
| 视频检测 | POST `/api/detect/video` | 上传视频，逐帧检测，轮询进度 |
| 批量检测 | POST `/api/detect/batch` | 一次上传多张（最多 100 张） |

推理后端可在设置页切换：**本地 ONNX Runtime** / **Atlas 200 DK 远程**。

---

## 启动

```powershell
# 后端
cd backend
conda activate tomato-p310
python app.py           # → http://localhost:5000

# 前端
cd frontend
npm install
npm run dev             # → http://localhost:5173
```

---

## 数据集

使用 [StrawDI_Db1](https://drive.google.com/file/d/1elFB-q9dgPbfnleA7qIrTb96Qsli8PZl/view)（西班牙韦尔瓦大学），3100 张真实温室草莓图片，PNG 实例分割标注。

### 训练指标

| 指标 | Box | Mask |
|------|-----|------|
| mAP50 | 0.922 | 0.929 |
| mAP50-95 | 0.803 | 0.793 |
| Precision | 0.974 | 0.985 |
| Recall | 0.856 | 0.865 |

---

## Atlas 200 DK 部署

板子 IP: `192.168.1.2` / CANN: 21.0.3

```bash
# PC: .pt → ONNX
python export_strawberry_onnx.py

# 传到板子
scp best.onnx HwHiAiUser@192.168.1.2:/home/HwHiAiUser/

# 板子: ONNX → OM
atc --model=best.onnx --framework=5 --output=best --soc_version=Ascend310

# 推理
python3 yolo_acllite.py
```
