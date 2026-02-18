import sys
sys.path.insert(0, '.')
from scripts import rag_engine

print('=== 查詢：遲到與早退規定 ===')
results = rag_engine.query('遲到與早退規定', top_k=3)
for i, r in enumerate(results):
    print(f'[結果 {i+1}] 相似度: {r["similarity"]}')
    print(f'來源: {r["metadata"].get("filename", "未知")}')
    print(f'內容: {r["text"]}')
    print()
