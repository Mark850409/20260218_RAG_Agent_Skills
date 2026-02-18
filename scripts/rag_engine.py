"""
RAG 核心引擎
負責文件索引（向量化）與語意搜尋查詢
使用 ChromaDB 作為向量資料庫，sentence-transformers 作為嵌入模型
"""

import os
import uuid
import yaml
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 延遲載入，避免啟動時間過長
_embedding_model = None
_chroma_client = None
_collection = None
_config = None


def _load_config() -> Dict:
    """載入配置文件"""
    global _config
    if _config is not None:
        return _config

    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    else:
        # 預設配置
        _config = {
            "embedding": {"model": "paraphrase-multilingual-MiniLM-L12-v2", "device": "cpu"},
            "chunking": {"chunk_size": 500, "chunk_overlap": 50},
            "retrieval": {"top_k": 5, "score_threshold": 0.0},
            "knowledge_base": {
                "persist_directory": str(Path(__file__).parent.parent / "knowledge_base"),
                "collection_name": "rag_documents",
            },
        }
    return _config


def _get_embedding_model():
    """取得嵌入模型（懶加載）"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        config = _load_config()
        model_name = config["embedding"]["model"]
        device = config["embedding"].get("device", "cpu")
        _embedding_model = SentenceTransformer(model_name, device=device)
    return _embedding_model


def _get_collection():
    """取得 ChromaDB collection（懶加載）"""
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        config = _load_config()
        persist_dir = config["knowledge_base"]["persist_directory"]
        collection_name = config["knowledge_base"]["collection_name"]

        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        _collection = _chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """將長文字切割成重疊的 chunks"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 嘗試在句子邊界切割
        if end < len(text):
            for sep in ["。", "！", "？", "\n\n", "\n", ".", "!", "?"]:
                last_sep = chunk.rfind(sep)
                if last_sep > chunk_size // 2:
                    chunk = chunk[: last_sep + 1]
                    break

        chunks.append(chunk.strip())
        start += len(chunk) - chunk_overlap

    return [c for c in chunks if c.strip()]


def _get_doc_id(file_path: str, chunk_index: int) -> str:
    """生成文件 chunk 的唯一 ID"""
    hash_val = hashlib.md5(file_path.encode()).hexdigest()[:8]
    return f"{hash_val}_{chunk_index}"


def index_document(file_path: str, progress_callback=None) -> Dict[str, Any]:
    """
    索引單一文件到知識庫
    返回：{"success": bool, "chunks": int, "message": str}
    """
    from scripts.document_loader import load_document

    config = _load_config()
    chunk_size = config["chunking"]["chunk_size"]
    chunk_overlap = config["chunking"]["chunk_overlap"]

    try:
        # 載入文件
        if progress_callback:
            progress_callback(f"正在載入文件：{Path(file_path).name}")
        raw_chunks = load_document(file_path)

        # 切割文字
        all_chunks = []
        for raw in raw_chunks:
            text = raw["text"]
            meta = raw["metadata"]
            sub_chunks = _split_text(text, chunk_size, chunk_overlap)
            for sub in sub_chunks:
                if sub.strip():
                    all_chunks.append({"text": sub, "metadata": meta})

        if not all_chunks:
            return {"success": False, "chunks": 0, "message": "文件內容為空"}

        # 生成嵌入向量
        if progress_callback:
            progress_callback(f"正在生成嵌入向量（共 {len(all_chunks)} 個片段）...")
        model = _get_embedding_model()
        texts = [c["text"] for c in all_chunks]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        # 先刪除舊的同名文件索引
        delete_document(file_path)

        # 存入 ChromaDB
        collection = _get_collection()
        ids = [_get_doc_id(file_path, i) for i in range(len(all_chunks))]
        metadatas = [c["metadata"] for c in all_chunks]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        return {"success": True, "chunks": len(all_chunks), "message": f"成功索引 {len(all_chunks)} 個片段"}

    except Exception as e:
        return {"success": False, "chunks": 0, "message": f"索引失敗：{str(e)}"}


def query(query_text: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    語意搜尋查詢
    返回最相關的文件片段列表
    """
    if not query_text.strip():
        return []

    try:
        model = _get_embedding_model()
        query_embedding = model.encode([query_text]).tolist()

        collection = _get_collection()
        total_docs = collection.count()
        if total_docs == 0:
            return []

        actual_top_k = min(top_k, total_docs)
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=actual_top_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            # ChromaDB cosine distance: 0=完全相同, 2=完全相反
            # 轉換為相似度分數 0~1
            similarity = max(0.0, 1.0 - distance / 2.0)

            if similarity >= score_threshold:
                output.append(
                    {
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity": round(similarity, 4),
                    }
                )

        return output

    except Exception as e:
        raise RuntimeError(f"查詢失敗：{str(e)}")


def list_documents() -> List[Dict[str, Any]]:
    """
    列出所有已索引的文件
    返回：[{"filename": str, "source": str, "chunks": int}]
    """
    try:
        collection = _get_collection()
        total = collection.count()
        if total == 0:
            return []

        # 取得所有 metadata
        results = collection.get(include=["metadatas"])
        metadatas = results["metadatas"]

        # 依來源文件分組統計
        doc_stats = {}
        for meta in metadatas:
            source = meta.get("source", "未知")
            filename = meta.get("filename", Path(source).name)
            if source not in doc_stats:
                doc_stats[source] = {"filename": filename, "source": source, "chunks": 0}
            doc_stats[source]["chunks"] += 1

        return list(doc_stats.values())

    except Exception as e:
        return []


def delete_document(file_path: str) -> Dict[str, Any]:
    """
    刪除指定文件的所有索引
    返回：{"success": bool, "deleted": int, "message": str}
    """
    try:
        collection = _get_collection()
        results = collection.get(include=["metadatas"])

        ids_to_delete = []
        for i, meta in enumerate(results["metadatas"]):
            if meta.get("source") == file_path or meta.get("filename") == Path(file_path).name:
                ids_to_delete.append(results["ids"][i])

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            return {"success": True, "deleted": len(ids_to_delete), "message": f"已刪除 {len(ids_to_delete)} 個片段"}
        else:
            return {"success": True, "deleted": 0, "message": "找不到對應文件"}

    except Exception as e:
        return {"success": False, "deleted": 0, "message": f"刪除失敗：{str(e)}"}


def get_stats() -> Dict[str, Any]:
    """取得知識庫統計資訊"""
    try:
        collection = _get_collection()
        total_chunks = collection.count()
        docs = list_documents()
        config = _load_config()

        return {
            "total_documents": len(docs),
            "total_chunks": total_chunks,
            "embedding_model": config["embedding"]["model"],
            "chunk_size": config["chunking"]["chunk_size"],
            "chunk_overlap": config["chunking"]["chunk_overlap"],
        }
    except Exception as e:
        return {"total_documents": 0, "total_chunks": 0, "error": str(e)}


def reset_knowledge_base() -> Dict[str, Any]:
    """清空並重建知識庫"""
    global _chroma_client, _collection
    try:
        import chromadb
        config = _load_config()
        persist_dir = config["knowledge_base"]["persist_directory"]
        collection_name = config["knowledge_base"]["collection_name"]

        if _chroma_client is not None:
            try:
                _chroma_client.delete_collection(collection_name)
            except Exception:
                pass

        _collection = None
        _chroma_client = None
        _get_collection()  # 重新建立

        return {"success": True, "message": "知識庫已重置"}
    except Exception as e:
        return {"success": False, "message": f"重置失敗：{str(e)}"}
