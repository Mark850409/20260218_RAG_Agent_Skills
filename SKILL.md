---
name: rag_knowledge_base
description: |
  RAG（Retrieval-Augmented Generation）知識庫查找技能。
  當使用者需要從本地文件庫中搜尋資訊、建立私有知識庫、
  對文件進行語意搜尋，或需要啟動知識庫 Web UI 時，使用此技能。
  支援 Markdown、PDF、Word、CSV、Excel 格式的文件索引與查詢。
---

# RAG 知識庫查找技能

## 功能概述

此技能提供完整的 RAG（Retrieval-Augmented Generation）知識庫系統，包含：
- **Web UI 介面**：使用 Gradio 建立的視覺化操作介面
- **多格式支援**：`.md` / `.txt` / `.pdf` / `.docx` / `.csv` / `.xlsx`
- **語意搜尋**：使用 sentence-transformers 多語言嵌入模型（支援中文）
- **本地向量庫**：使用 ChromaDB 儲存，無需外部服務

## 何時使用此技能

- 使用者想要建立私有知識庫
- 使用者需要對大量文件進行語意搜尋
- 使用者想要啟動 RAG 知識庫 Web UI
- 使用者需要索引文件並查詢相關內容

## 目錄結構

```
rag_knowledge_base/
├── SKILL.md                    # 本文件
├── app.py                      # Web UI 主程式（Gradio）
├── config.yaml                 # 系統配置
├── requirements.txt            # Python 依賴
├── scripts/
│   ├── rag_engine.py           # RAG 核心引擎
│   └── document_loader.py      # 多格式文件載入器
└── examples/
    └── sample_docs/            # 範例文件
```

## 使用步驟

### 步驟 1：安裝依賴

```powershell
cd d:\AI_project\20260218_agent_skills\rag_knowledge_base
pip install -r requirements.txt
```

### 步驟 2：啟動 Web UI

```powershell
python app.py
```

瀏覽器會自動開啟 `http://localhost:7860`

### 步驟 3：上傳文件並索引

1. 在「📁 文件管理」分頁，拖放上傳文件
2. 點擊「🚀 開始索引」
3. 等待索引完成（首次啟動需下載嵌入模型）

### 步驟 4：查詢知識庫

1. 前往「🔍 知識庫查詢」分頁
2. 輸入自然語言查詢
3. 查看相關文件片段與相似度分數

## 支援格式說明

| 格式 | 解析方式 |
|------|---------|
| `.md` / `.txt` | 依標題結構分割 |
| `.pdf` | 每頁為一個片段 |
| `.docx` | 依 Word 標題樣式分割 |
| `.csv` | 每 20 行為一個片段 |
| `.xlsx` | 每個工作表分別索引 |

## 配置說明（config.yaml）

```yaml
embedding:
  model: paraphrase-multilingual-MiniLM-L12-v2  # 嵌入模型
  device: cpu                                    # cpu 或 cuda

chunking:
  chunk_size: 500    # 每個片段的字元數
  chunk_overlap: 50  # 片段間重疊字元數

retrieval:
  top_k: 5           # 返回結果數量
  score_threshold: 0.0  # 相似度門檻（0~1）

server:
  port: 7860         # Web UI 埠號
```

## 注意事項

- 首次啟動會自動下載嵌入模型（約 500MB），需要網路連線
- 向量庫儲存於 `./knowledge_base/` 目錄，可備份此目錄保存索引
- 支援中文查詢，模型已針對多語言優化
- 若需 GPU 加速，將 `config.yaml` 中的 `device` 改為 `cuda`
