# Python 程式設計完整指南

## Python 簡介

Python 是一種高階、通用、直譯式程式語言，以其簡潔易讀的語法著稱。由 Guido van Rossum 於 1991 年創建，目前是全球最受歡迎的程式語言之一，廣泛應用於資料科學、人工智慧、網頁開發和自動化腳本。

## 安裝 Python

### Windows 安裝步驟
1. 前往 [python.org](https://www.python.org/downloads/) 下載最新版本
2. 執行安裝程式，**務必勾選「Add Python to PATH」**
3. 開啟命令提示字元，輸入 `python --version` 確認安裝成功

### 使用 pip 安裝套件
```bash
pip install 套件名稱
pip install numpy pandas matplotlib
pip install -r requirements.txt  # 從清單安裝
pip list                          # 列出已安裝套件
pip upgrade 套件名稱              # 升級套件
```

## 基本資料型別

Python 有以下主要資料型別：

### 數值型別
- **int**（整數）：`x = 42`
- **float**（浮點數）：`y = 3.14`
- **complex**（複數）：`z = 2 + 3j`

### 文字型別
- **str**（字串）：`name = "Hello, World!"`
- 字串可用單引號或雙引號
- 多行字串使用三引號：`"""多行文字"""`

### 序列型別
- **list**（列表）：`fruits = ["蘋果", "香蕉", "橘子"]`，可修改
- **tuple**（元組）：`point = (10, 20)`，不可修改
- **range**（範圍）：`r = range(0, 10, 2)`

### 映射型別
- **dict**（字典）：`person = {"name": "Alice", "age": 30}`

### 集合型別
- **set**（集合）：`unique = {1, 2, 3, 3}`（自動去重）
- **frozenset**（不可變集合）

### 布林型別
- **bool**：`True` 或 `False`

## 控制流程

### 條件判斷
```python
age = 18
if age >= 18:
    print("成年人")
elif age >= 13:
    print("青少年")
else:
    print("兒童")
```

### 迴圈
```python
# for 迴圈
for i in range(5):
    print(i)

# while 迴圈
count = 0
while count < 5:
    count += 1

# 列表推導式
squares = [x**2 for x in range(10)]
```

## 函式

```python
def greet(name, greeting="你好"):
    """問候函式"""
    return f"{greeting}，{name}！"

# 呼叫函式
result = greet("Alice")
result2 = greet("Bob", "嗨")

# Lambda 函式
square = lambda x: x ** 2
```

## 常用內建函式

| 函式 | 說明 | 範例 |
|------|------|------|
| `len()` | 取得長度 | `len([1,2,3])` → 3 |
| `type()` | 取得型別 | `type(42)` → int |
| `print()` | 輸出到終端 | `print("Hello")` |
| `input()` | 讀取使用者輸入 | `name = input("請輸入名字：")` |
| `int()` | 轉換為整數 | `int("42")` → 42 |
| `str()` | 轉換為字串 | `str(42)` → "42" |
| `list()` | 轉換為列表 | `list(range(3))` → [0,1,2] |
| `sorted()` | 排序 | `sorted([3,1,2])` → [1,2,3] |
| `sum()` | 加總 | `sum([1,2,3])` → 6 |
| `max()` / `min()` | 最大/最小值 | `max([1,2,3])` → 3 |

## 常用標準函式庫

### os 模組（作業系統操作）
```python
import os
os.getcwd()           # 取得當前目錄
os.listdir(".")       # 列出目錄內容
os.makedirs("新目錄") # 建立目錄
os.path.exists("檔案") # 檢查是否存在
```

### pathlib 模組（現代路徑操作）
```python
from pathlib import Path
p = Path("./data")
p.mkdir(exist_ok=True)
files = list(p.glob("*.txt"))
```

### json 模組
```python
import json
data = {"name": "Alice", "age": 30}
json_str = json.dumps(data, ensure_ascii=False)
parsed = json.loads(json_str)
```

## 虛擬環境

建議為每個專案建立獨立的虛擬環境：

```bash
# 建立虛擬環境
python -m venv venv

# 啟動（Windows）
venv\Scripts\activate

# 啟動（macOS/Linux）
source venv/bin/activate

# 停用
deactivate
```
