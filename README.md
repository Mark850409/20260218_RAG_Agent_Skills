# RAG 知識庫查找系統

> 基於 RAG（Retrieval-Augmented Generation）技術的本地知識庫查找工具，提供 Web UI 介面，支援多種文件格式。

## 功能特色

- 🌐 **Web UI 介面**：Gradio 視覺化操作，無需命令列
- 📄 **多格式支援**：Markdown、PDF、Word、CSV、Excel
- 🔍 **語意搜尋**：多語言嵌入模型，完整支援中文
- 💾 **本地儲存**：ChromaDB 向量庫，資料不離開本機
- ⚡ **懶加載**：首次查詢時才載入模型，節省記憶體

## 快速開始

### 1. 安裝依賴

```powershell
cd d:\AI_project\20260218_agent_skills\rag_knowledge_base
pip install -r requirements.txt
```

> ⚠️ 首次執行會自動下載嵌入模型（約 500MB），請確保網路連線。

### 2. 啟動 Web UI

```powershell
python app.py
```

瀏覽器會自動開啟 `http://localhost:7860`

### 3. 使用流程

1. **上傳文件**：在「📁 文件管理」分頁拖放文件並點擊「開始索引」
2. **查詢知識庫**：在「🔍 知識庫查詢」分頁輸入自然語言查詢
3. **查看結果**：系統返回最相關的文件片段與相似度分數

## 支援格式

| 格式 | 副檔名 | 解析方式 |
|------|--------|---------|
| Markdown | `.md` | 依標題（#）分割段落 |
| 純文字 | `.txt` | 整份文件為一個片段 |
| PDF | `.pdf` | 每頁為一個片段 |
| Word | `.docx` | 依標題樣式分割 |
| CSV | `.csv` | 每 20 行為一個片段 |
| Excel | `.xlsx` / `.xls` | 每個工作表分別索引 |

## 目錄結構

```
rag_knowledge_base/
├── SKILL.md                    # Agent 技能說明
├── README.md                   # 本文件
├── app.py                      # Web UI 主程式
├── config.yaml                 # 系統配置
├── requirements.txt            # Python 依賴
├── scripts/
│   ├── __init__.py
│   ├── rag_engine.py           # RAG 核心引擎
│   └── document_loader.py      # 多格式文件載入器
├── examples/
│   └── sample_docs/            # 範例文件（可直接上傳測試）
│       ├── ai_introduction.md
│       ├── python_guide.md
│       └── company_policy.md
└── knowledge_base/             # ChromaDB 向量庫（自動生成）
```

## 配置說明

編輯 `config.yaml` 調整系統參數：

```yaml
embedding:
  model: paraphrase-multilingual-MiniLM-L12-v2  # 嵌入模型（支援中文）
  device: cpu                                    # cpu 或 cuda（GPU）

chunking:
  chunk_size: 500    # 每個片段的字元數（越小越精確，越大越有上下文）
  chunk_overlap: 50  # 片段間重疊字元數

retrieval:
  top_k: 5           # 預設返回結果數量
  score_threshold: 0.0  # 相似度門檻（0~1，建議 0.3 以上）

server:
  port: 7860         # Web UI 埠號
  share: false       # 設為 true 可產生公開分享連結
```

## 常見問題

**Q：首次啟動很慢？**
A：首次啟動需下載嵌入模型（約 500MB），之後會快取在本機。

**Q：如何支援 GPU 加速？**
A：將 `config.yaml` 中的 `device: cpu` 改為 `device: cuda`，並確認已安裝 CUDA 版 PyTorch。

**Q：知識庫資料存在哪裡？**
A：儲存於 `./knowledge_base/` 目錄，備份此目錄即可保存所有索引。

**Q：如何清空知識庫重新開始？**
A：在 Web UI 的「📁 文件管理」分頁點擊「🗑️ 清空知識庫」按鈕。
