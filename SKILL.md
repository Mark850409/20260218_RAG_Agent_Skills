---
name: rag_knowledge_base
description: |
  知識庫直接讀取技能。
  當使用者需要從本地文件庫中搜尋資訊時，Agent 直接讀取 examples/sample_docs/ 目錄下的所有文件內容，
  無需建立向量索引，直接根據文件內容回答問題。
  支援 Markdown、PDF、Word、CSV、Excel 格式。
---

# 知識庫直接讀取技能

## 功能概述

此技能提供直接讀取對話模式，結合 Web UI 知識庫編輯界面：
- **Agent 直接讀取檔案**：Agent 透過 `run_command` 執行 Python 腳本，直接讀取 `examples/sample_docs/` 下所有文件內容，不需建立向量索引（**主要使用方式**）
- **Web UI 介面**：使用 Gradio 建立的視覆化操作介面（供使用者手動操作）
- **多格式支援**：`.md` / `.txt` / `.pdf` / `.docx` / `.csv` / `.xlsx`

## 何時使用此技能

- 使用者需要查詢知識庫文件內容
- 使用者想要啟動知識庫 Web UI 進行文件編輯

## 目錄結構

```
rag_knowledge_base/
├── SKILL.md                    # 本文件
├── app.py                      # Web UI 主程式（Gradio）
├── config.yaml                 # 系統配置
├── requirements.txt            # Python 依賴
├── scripts/
│   ├── rag_engine.py           # RAG 核心引擎（索引 + 查詢）
│   └── document_loader.py      # 多格式文件載入器
└── examples/
    └── sample_docs/            # 範例知識庫文件（預設示範資料）
```

> **重要**：`examples/sample_docs/` 目錄是此技能的**預設範例知識庫資料位置**。
> 當需要示範或測試功能時，請直接使用此目錄中的文件進行讀取。
>
> 完整路徑（依作業系統選擇對應路徑）：
> - **Linux（OpenClaw 預設）**：`/root/.openclaw/workspace/skills/rag_knowledge_base/examples/sample_docs/`
> - **Windows**：`d:\AI_project\20260218_agent_skills\rag_knowledge_base\examples\sample_docs\`
>
> ⚠️ **Agent 不需要預先知道此目錄下有哪些檔案。**
> 步驟 2 的腳本會使用 Python 動態掃描該目錄下所有支援格式的文件並自動讀取，
> 同時腳本會自動偵測 SKILL 所在路徑，無需手動指定絕對路徑。

---

## ⚡ Agent 執行方式（主要使用流程）

> **Agent 必須透過以下方式使用腳本，不得自行猜測內容來回答問題。**
> 正確流程：讀取所有文件內容 → 根據文件內容回答使用者。

### 前置條件：確認工作目錄

所有命令必須在以下目錄執行：
- **Windows**：`d:\AI_project\20260218_agent_skills\rag_knowledge_base`
- **Linux**：`/root/.openclaw/workspace/skills/rag_knowledge_base/`

### 步驟 1：� 列出知識庫文件清單（**每次必做，不可跳過**）

> ⚠️ **強制規定**：每次呼叫此技能時，Agent **必須先執行以下腳本**列出所有可用文件。
> **Agent 不需要預先知道目錄內有哪些檔案，腳本會動態掃描並印出完整檔案清單。**

**Windows（PowerShell）：**
```powershell
python -X utf8 -c "
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
skill_root = r'd:\AI_project\20260218_agent_skills\rag_knowledge_base'
doc_dir_path = os.path.join(skill_root, 'examples', 'sample_docs')
from pathlib import Path
doc_dir = Path(doc_dir_path)
print('「' + str(doc_dir) + '」 目錄下的文件：')
supported = ['.md', '.txt', '.pdf', '.docx', '.csv', '.xlsx']
files = [f for f in sorted(doc_dir.iterdir()) if f.suffix.lower() in supported]
for i, f in enumerate(files, 1):
    size_kb = f.stat().st_size // 1024
    print(str(i) + '. ' + f.name + ' (' + f.suffix + ', ' + str(size_kb) + ' KB)')
print('共 ' + str(len(files)) + ' 個文件')
"
```

**Linux / OpenClaw（bash）：**
```bash
python3 -c "
import sys, os
skill_root = '/root/.openclaw/workspace/skills/rag_knowledge_base'
doc_dir_path = os.path.join(skill_root, 'examples', 'sample_docs')
from pathlib import Path
doc_dir = Path(doc_dir_path)
print('「' + str(doc_dir) + '」 目錄下的文件：')
supported = ['.md', '.txt', '.pdf', '.docx', '.csv', '.xlsx']
files = [f for f in sorted(doc_dir.iterdir()) if f.suffix.lower() in supported]
for i, f in enumerate(files, 1):
    size_kb = f.stat().st_size // 1024
    print(str(i) + '. ' + f.name + ' (' + f.suffix + ', ' + str(size_kb) + ' KB)')
print('共 ' + str(len(files)) + ' 個文件')
"
```

### 步驟 2：📖 直接讀取所有文件內容（**每次必做，不可跳過**）

> ⚠️ **強制規定**：列出文件後，**必須執行以下腳本**讀取全部文件內容。
> 腳本使用 `document_loader` 支援各種格式（指定檔名 `.docx`/`.pdf` 也聽讀），不需建立任何索引。
> Agent 讀取輸出的內容後，直接根據內容回答使用者。

**Windows（PowerShell）：**
```powershell
python -X utf8 -c "
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
skill_root = r'd:\AI_project\20260218_agent_skills\rag_knowledge_base'
os.chdir(skill_root)
sys.path.insert(0, skill_root)
from pathlib import Path
from scripts.document_loader import load_document

doc_dir = Path(skill_root) / 'examples' / 'sample_docs'
supported = ['.md', '.txt', '.pdf', '.docx', '.csv', '.xlsx']
files = [f for f in sorted(doc_dir.iterdir()) if f.suffix.lower() in supported]

for f in files:
    print('=' * 60)
    print('《檔案：' + f.name + '》')
    print('=' * 60)
    try:
        chunks = load_document(str(f))
        for chunk in chunks:
            section = chunk['metadata'].get('section', '')
            if section:
                print('[' + section + ']')
            print(chunk['text'])
            print()
    except Exception as e:
        print('讀取失敗：' + str(e))
    print()
print('=== 全部文件讀取完成 ===')
"
```

**Linux / OpenClaw（bash）：**
```bash
python3 -c "
import sys, os
skill_root = '/root/.openclaw/workspace/skills/rag_knowledge_base'
os.chdir(skill_root)
sys.path.insert(0, skill_root)
from pathlib import Path
from scripts.document_loader import load_document

doc_dir = Path(skill_root) / 'examples' / 'sample_docs'
supported = ['.md', '.txt', '.pdf', '.docx', '.csv', '.xlsx']
files = [f for f in sorted(doc_dir.iterdir()) if f.suffix.lower() in supported]

for f in files:
    print('=' * 60)
    print('《檔案：' + f.name + '》')
    print('=' * 60)
    try:
        chunks = load_document(str(f))
        for chunk in chunks:
            section = chunk['metadata'].get('section', '')
            if section:
                print('[' + section + ']')
            print(chunk['text'])
            print()
    except Exception as e:
        print('讀取失敗：' + str(e))
    print()
print('=== 全部文件讀取完成 ===')
"  
```

> **如果只需讀取特定檔案**，可將上方 `files` 改為指定單一檔案，例如：
> ```python
> files = [doc_dir / 'company_policy.md']
> ```

---

## ⚙️ Web UI 使用方式（供使用者手動操作）

若使用者要求啟動視覺化介面，執行以下步驟：

### 啟動 Web UI

```powershell
cd d:\AI_project\20260218_agent_skills\rag_knowledge_base
python app.py
```

瀏覽器會自動開啟 `http://localhost:7860`

1. 在「📁 文件管理」分頁上傳文件並點擊「🚀 開始索引」
2. 在「🔍 知識庫查詢」分頁輸入問題查看結果

---

## 支援格式說明

| 格式 | 解析方式 |
|------|---------|
| `.md` / `.txt` | 依標題結構分割 |
| `.pdf` | 每頁為一個片段 |
| `.docx` | 依 Word 標題樣式分割 |
| `.csv` | 每 20 行為一個片段 |
| `.xlsx` | 每個工作表分別索引 |

## 需要安裝的依賴

| 檔案格式 | 需要套件 | 安裝指令 |
|---|---|---|
| `.md` / `.txt` | 無（Python 內建）| 不需要 |
| `.pdf` | pypdf | `pip install pypdf` |
| `.docx` | python-docx | `pip install python-docx` |
| `.csv` / `.xlsx` | pandas, openpyxl | `pip install pandas openpyxl` |

> 如果知識庫嗡含多種格式文件，可一次安裝全部：`pip install pypdf python-docx pandas openpyxl`

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

- **Agent 每次對話時必須先執行步驟 1 列出文件清單，再執行步驟 2 讀取所有內容，不得跳過**
- **Agent 不需要預先知道 `examples/sample_docs/` 內有哪些檔案，腳本會動態掃描**
- **不需建立任何索引，所有內容直接從檔案讀取**
- **Linux（OpenClaw）請使用 `python3` 指令；Windows 請使用 `python -X utf8` 指令**
- **`.md` / `.txt` 檔不需安裝任何套件；`.pdf`/`.docx`/`.csv`/`.xlsx` 需安裝對應套件**
- **Web UI（`app.py`）他 不受上述直接讀取模式影響，從 web UI 上傳仍然支援建立向量索引**
