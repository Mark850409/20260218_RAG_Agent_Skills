"""
RAG 知識庫查找 Web UI
使用 Gradio 建立互動式介面
支援文件上傳、索引、語意搜尋查詢
"""

import sys
import os
from pathlib import Path

# 確保 scripts 目錄在 Python 路徑中
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

import gradio as gr
import yaml

# ─────────────────────────────────────────────
# 輔助函式
# ─────────────────────────────────────────────

def _load_config():
    config_path = ROOT_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def _format_results_markdown(results):
    """將查詢結果格式化為 Markdown"""
    if not results:
        return "❌ 找不到相關資訊，請嘗試其他查詢詞彙或先上傳文件。"

    md = ""
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        filename = meta.get("filename", "未知文件")
        similarity = r.get("similarity", 0)
        text = r.get("text", "")
        section = meta.get("section", "")
        page = meta.get("page", "")
        sheet = meta.get("sheet", "")

        # 來源標籤
        source_parts = [f"📄 **{filename}**"]
        if section:
            source_parts.append(f"章節：{section}")
        if page:
            source_parts.append(f"第 {page} 頁")
        if sheet:
            source_parts.append(f"工作表：{sheet}")

        bar_len = int(similarity * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)

        md += f"""### 結果 {i}
{" ｜ ".join(source_parts)}
**相似度：** `{similarity:.1%}` `{bar}`

{text}

---
"""
    return md


def _get_docs_table():
    """取得已索引文件的 Markdown 表格"""
    from scripts.rag_engine import list_documents
    docs = list_documents()
    if not docs:
        return "（尚未索引任何文件）"

    rows = ["| # | 文件名稱 | 片段數 |", "|---|---------|--------|"]
    for i, doc in enumerate(docs, 1):
        rows.append(f"| {i} | {doc['filename']} | {doc['chunks']} |")
    return "\n".join(rows)


def _get_stats_markdown():
    """取得知識庫統計資訊"""
    from scripts.rag_engine import get_stats
    stats = get_stats()
    return f"""### 📊 知識庫統計
| 項目 | 數值 |
|------|------|
| 已索引文件數 | **{stats.get('total_documents', 0)}** |
| 總片段數 | **{stats.get('total_chunks', 0)}** |
| 嵌入模型 | `{stats.get('embedding_model', '-')}` |
| Chunk 大小 | {stats.get('chunk_size', '-')} 字元 |
| Chunk 重疊 | {stats.get('chunk_overlap', '-')} 字元 |
"""


# ─────────────────────────────────────────────
# 事件處理函式
# ─────────────────────────────────────────────

def handle_upload(files, progress=gr.Progress()):
    """處理文件上傳並索引"""
    from scripts.rag_engine import index_document

    if not files:
        return "⚠️ 請選擇要上傳的文件。", _get_docs_table()

    results = []
    for i, file in enumerate(files):
        progress((i / len(files)), desc=f"正在處理：{Path(file.name).name}")
        file_path = file.name

        def cb(msg):
            pass  # Gradio progress 已處理

        result = index_document(file_path, progress_callback=cb)
        filename = Path(file_path).name

        if result["success"]:
            results.append(f"✅ **{filename}** — 成功索引 {result['chunks']} 個片段")
        else:
            results.append(f"❌ **{filename}** — {result['message']}")

    progress(1.0, desc="完成！")
    status = "\n".join(results)
    return status, _get_docs_table()


def handle_query(query_text, top_k, score_threshold):
    """處理查詢請求"""
    from scripts.rag_engine import query

    if not query_text.strip():
        return "⚠️ 請輸入查詢內容。"

    try:
        results = query(query_text, top_k=int(top_k), score_threshold=float(score_threshold))
        return _format_results_markdown(results)
    except Exception as e:
        return f"❌ 查詢失敗：{str(e)}"


def handle_delete(filename):
    """刪除指定文件的索引"""
    from scripts.rag_engine import delete_document, list_documents

    if not filename or filename.strip() == "":
        return "⚠️ 請輸入要刪除的文件名稱。", _get_docs_table()

    # 找到完整路徑
    docs = list_documents()
    target = None
    for doc in docs:
        if doc["filename"] == filename.strip():
            target = doc["source"]
            break

    if target is None:
        return f"❌ 找不到文件：{filename}", _get_docs_table()

    result = delete_document(target)
    if result["success"]:
        msg = f"✅ 已刪除 **{filename}**（共 {result['deleted']} 個片段）"
    else:
        msg = f"❌ {result['message']}"

    return msg, _get_docs_table()


def handle_reset():
    """重置整個知識庫"""
    from scripts.rag_engine import reset_knowledge_base
    result = reset_knowledge_base()
    if result["success"]:
        return "✅ 知識庫已清空重置。", _get_docs_table()
    else:
        return f"❌ {result['message']}", _get_docs_table()


def refresh_docs():
    """刷新文件列表"""
    return _get_docs_table()


def refresh_stats():
    """刷新統計資訊"""
    return _get_stats_markdown()


def get_filenames_for_delete():
    """取得可刪除的文件名稱列表"""
    from scripts.rag_engine import list_documents
    docs = list_documents()
    return [doc["filename"] for doc in docs]


# ─────────────────────────────────────────────
# Gradio UI 建構
# ─────────────────────────────────────────────

CUSTOM_CSS = """
.gradio-container {
    max-width: 1100px !important;
    margin: auto;
}
.result-box {
    border-left: 4px solid #4f46e5;
    padding-left: 12px;
}
footer { display: none !important; }
"""

def build_ui():
    with gr.Blocks(
        title="RAG 知識庫查找系統",
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="blue",
            neutral_hue="slate",
        ),
        css=CUSTOM_CSS,
    ) as demo:

        # ── 標題 ──
        gr.Markdown(
            """
# 🔍 RAG 知識庫查找系統
**Retrieval-Augmented Generation** — 上傳文件，建立知識庫，用自然語言查詢相關資訊。

支援格式：`Markdown` · `PDF` · `Word (.docx)` · `CSV` · `Excel (.xlsx)`
            """
        )

        with gr.Tabs():

            # ══════════════════════════════════════
            # 分頁 1：文件管理
            # ══════════════════════════════════════
            with gr.TabItem("📁 文件管理"):
                gr.Markdown("### 上傳文件到知識庫")

                with gr.Row():
                    with gr.Column(scale=3):
                        upload_files = gr.File(
                            label="拖放或點擊上傳文件",
                            file_count="multiple",
                            file_types=[".md", ".txt", ".pdf", ".docx", ".csv", ".xlsx", ".xls"],
                            height=160,
                        )
                        upload_btn = gr.Button("🚀 開始索引", variant="primary", size="lg")

                    with gr.Column(scale=2):
                        upload_status = gr.Markdown(
                            value="等待上傳文件...",
                            label="索引狀態",
                        )

                gr.Markdown("---")
                gr.Markdown("### 已索引文件")

                with gr.Row():
                    refresh_btn = gr.Button("🔄 刷新列表", size="sm")
                    reset_btn = gr.Button("🗑️ 清空知識庫", variant="stop", size="sm")

                docs_table = gr.Markdown(value=_get_docs_table())

                gr.Markdown("### 刪除文件")
                with gr.Row():
                    delete_input = gr.Textbox(
                        label="輸入要刪除的文件名稱",
                        placeholder="例如：company_policy.pdf",
                        scale=3,
                    )
                    delete_btn = gr.Button("🗑️ 刪除", variant="secondary", scale=1)

                delete_status = gr.Markdown()

                # 事件綁定
                upload_btn.click(
                    handle_upload,
                    inputs=[upload_files],
                    outputs=[upload_status, docs_table],
                )
                refresh_btn.click(refresh_docs, outputs=[docs_table])
                reset_btn.click(handle_reset, outputs=[delete_status, docs_table])
                delete_btn.click(
                    handle_delete,
                    inputs=[delete_input],
                    outputs=[delete_status, docs_table],
                )

            # ══════════════════════════════════════
            # 分頁 2：知識庫查詢
            # ══════════════════════════════════════
            with gr.TabItem("🔍 知識庫查詢"):
                gr.Markdown("### 輸入查詢，從知識庫中找到最相關的內容")

                with gr.Row():
                    with gr.Column(scale=4):
                        query_input = gr.Textbox(
                            label="查詢內容",
                            placeholder="例如：什麼是機器學習？公司的請假政策是什麼？",
                            lines=3,
                        )
                    with gr.Column(scale=1):
                        top_k_slider = gr.Slider(
                            label="返回結果數量",
                            minimum=1,
                            maximum=20,
                            value=5,
                            step=1,
                        )
                        score_slider = gr.Slider(
                            label="最低相似度門檻",
                            minimum=0.0,
                            maximum=1.0,
                            value=0.0,
                            step=0.05,
                        )

                with gr.Row():
                    query_btn = gr.Button("🔍 查詢", variant="primary", size="lg")
                    clear_btn = gr.ClearButton(components=[query_input], value="清除")

                query_results = gr.Markdown(
                    value="輸入查詢內容後點擊「查詢」按鈕...",
                    label="查詢結果",
                )

                # 範例查詢
                gr.Markdown("#### 💡 範例查詢（點擊套用）")
                gr.Examples(
                    examples=[
                        ["什麼是機器學習？"],
                        ["Python 有哪些資料型別？"],
                        ["公司的請假規定是什麼？"],
                        ["如何安裝 Python 套件？"],
                    ],
                    inputs=[query_input],
                )

                # 事件綁定
                query_btn.click(
                    handle_query,
                    inputs=[query_input, top_k_slider, score_slider],
                    outputs=[query_results],
                )
                query_input.submit(
                    handle_query,
                    inputs=[query_input, top_k_slider, score_slider],
                    outputs=[query_results],
                )

            # ══════════════════════════════════════
            # 分頁 3：系統資訊
            # ══════════════════════════════════════
            with gr.TabItem("⚙️ 系統資訊"):
                gr.Markdown("### 知識庫狀態與設定")

                with gr.Row():
                    stats_refresh_btn = gr.Button("🔄 刷新統計", size="sm")

                stats_display = gr.Markdown(value=_get_stats_markdown())

                gr.Markdown("---")
                gr.Markdown(
                    """
### 📖 使用說明

#### 快速開始
1. 前往「📁 文件管理」分頁，上傳您的文件（支援 .md / .pdf / .docx / .csv / .xlsx）
2. 點擊「🚀 開始索引」，等待系統建立向量索引
3. 前往「🔍 知識庫查詢」分頁，輸入自然語言查詢
4. 系統會返回最相關的文件片段，並顯示相似度分數

#### 支援格式說明
| 格式 | 說明 |
|------|------|
| `.md` / `.txt` | 依標題結構分割，保留層次 |
| `.pdf` | 每頁為一個片段 |
| `.docx` | 依 Word 標題樣式分割 |
| `.csv` | 每 20 行為一個片段，保留欄位名稱 |
| `.xlsx` | 每個工作表分別索引 |

#### 相似度分數說明
- **0.8 以上**：高度相關
- **0.5 ~ 0.8**：中度相關
- **0.5 以下**：低度相關，建議調整查詢詞彙
                    """
                )

                stats_refresh_btn.click(refresh_stats, outputs=[stats_display])

    return demo


# ─────────────────────────────────────────────
# 主程式入口
# ─────────────────────────────────────────────

if __name__ == "__main__":
    config = _load_config()
    server_config = config.get("server", {})

    print("🚀 正在啟動 RAG 知識庫查找系統...")
    print("📦 首次啟動會下載嵌入模型，請稍候...")

    demo = build_ui()
    demo.launch(
        server_name=server_config.get("host", "0.0.0.0"),
        server_port=server_config.get("port", 7860),
        share=server_config.get("share", False),
        inbrowser=True,
    )
