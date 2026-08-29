# 安裝與移植指南

把 podcast-ingest-core 的 25 個 MCP tools 與 portable Skills 裝到一台新電腦上。

本文件分三段：**A 裝核心**（任何機器都要做）、**B 搬資料**、**C 驗收**。
最後一段是**已知限制**，動手前請先看過。

> **關於 Hermes：** 本文件原本有「C. 接上 Hermes」一整段 sidecar 部署與 config/Skill 同步步驟。
> Hermes 稽核鏈（specs 026–034）終止於 BLOCKED，已於 2026-08-29 從 main 移除，`deploy/hermes/`、
> 驗證器腳本與 digest 基準表都不在這個 repo 裡了。完整內容保存在 git tag `archive/hermes-audit-chain`。

> **A 段已實測驗證。** 在一個模擬全新 clone 的乾淨環境（無 `data/`、全新 venv）中從頭跑過一次：
> `pip install -e .[dev]` 成功、`import podcast_ingest_core` 成功、`validate_mcp_setup.py` 回 `"ok": true`。
>
> ⚠️ **`python -m pytest` 在正確安裝的環境下全綠。** `pyproject.toml` 的
> `[tool.pytest.ini_options]` 沒有任何 `--ignore`：`tests/` 下每一個測試都會跑到。
>
> 💡 **有紅燈就代表環境沒裝對，失敗仍然是安裝正確性的訊號。** 有些測試會直接對照
> `pyproject.toml` 宣告的相依版本，有些用子行程執行 CLI（子行程繼承不到 pytest 的
> `pythonpath` 設定），所以環境不符宣告就會紅。**實測 2026-08-22** 在一台看似正常的
> 機器上抓到兩個缺口：
>
> | 症狀 | 原因 | 修法 |
> |---|---|---|
> | `test_mcp_http_transport` 三個測試全紅 | `mcp` 裝的是 1.10.1，低於宣告的 `>=1.27` | `pip install -U "mcp[cli]>=1.27,<2"` |
> | `ModuleNotFoundError: No module named 'podcast_ingest_core'` | A2 的 `pip install -e .` 從未執行；`pythonpath = ["src"]` 只對 pytest 本身有效 | `pip install -e .[dev]` |
>
> 兩個補上後這些紅燈全部消失。
>
> ⚠️ **`validate_mcp_setup.py` 不能單獨當環境完整性的判準。** 上述兩個缺口都存在時，它仍回
> `ok: true`、18 項全過——它驗的是產品功能可用，不是環境符合宣告。兩者要一起看。

---

## 前置需求

| 項目 | 需求 | 備註 |
|---|---|---|
| Python | 3.11 以上 | `pyproject.toml` 的 `requires-python` |
| Git | 任意近期版本 | |
| NVIDIA 驅動 + cuBLAS/cuDNN | **僅 GPU 轉錄需要** | 見「已知限制」 |
| `ffmpeg` 在 `PATH` | **目前的影片擷取不需要** | X / YouTube 共用 `bestaudio/best`，不合併影音流；PyAV 負責轉成 corpus WAV |
| `yt-dlp` 保持最新 | **僅影片擷取需要** | YouTube 會讓舊版失效；實測十週前的版本 metadata 正常但媒體網址回 `403` |

---

## A. 安裝核心（必做）

### A1. 取得原始碼

```powershell
git clone <repo-url> podcast-ingest-core
cd podcast-ingest-core
```

### A2. 建立獨立環境並安裝

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

會安裝 5 個執行相依：`feedparser`、`faster-whisper`、`mcp[cli]`、`PyYAML`、`requests`，以及開發用的 `pytest`。

### A3. 設定環境變數

```powershell
Copy-Item .env.example .env
```

`.env` 只有三個欄位，供選用的 LLM 語意摘要使用：

```text
API_KEY=your-api-key
MODEL=your-model
BASE_URL=https://api.example.com/v1
```

**`.env` 永遠不進版控、不放進 Docker image、不貼進任何對話或紀錄。** 只做讀取與 deterministic 工作的話可以先不填。

### A4. 確認 podcast 設定

`config/podcasts.yaml` 已內建 `gooaye`，不需修改即可使用：

```yaml
podcasts:
  gooaye:
    display_name: Gooaye 股癌
    rss_url: https://feeds.soundon.fm/podcasts/...
    language: zh
    default_episode_prefix: EP
```

要加別的 podcast 就在這裡新增一段。

### A5. 驗證安裝

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```

`validate_mcp_setup.py` 是本機 readiness 檢查，會確認 MCP server 能起、tool registry 完整（25 個）、搜尋路徑可用。**這是判斷安裝成功與否的依據。**

想跑測試的話直接跑就好：

```powershell
python -m pytest -q
```

---

## B. 搬資料

`data/` 在 `.gitignore` 內，**不會跟著 git 過去**。裡面是逐字稿、摘要、研究報告、lineage 與 SQLite cache。三選一：

**B1. 整包複製（最快，保留全部歷史成果）**

把舊機器的 `data/` 整個複製到新機器同一位置。

**B2. 放在別的位置**

```powershell
$env:PODCAST_INGEST_DATA_DIR = "D:\podcast-data"
```

`storage.py` 讀這個環境變數，未設定時預設為 `./data`。

> ⚠️ **跑測試前要把這個變數取消。** 有 9 個路徑契約測試把 `data/` 寫成字面值
> （例如 `tests/test_contracts.py` 的 `assert audio_path("gooaye", "ep-001") ==`
> `Path("data/audio/gooaye/ep-001.mp3")`），它們釘的就是「未設定變數時的預設路徑」。
> 設了變數再跑 `pytest`，這 9 個會紅，而失敗訊息完全看不出跟環境變數有關。
> 實測 2026-08-22：設定變數後 9 failed / 1639 passed，取消後全綠。
> 搬遷本身不受影響——衝突只在測試，不在執行期。這是設計，不是缺陷：spec 025 FR-008 把
> 「變數未設定時 `storage.DATA_DIR` 維持 `Path("data")`」列為受保護不變量，測試要隔離路徑時
> 認可的方式是 `tests/conftest.py` 的 `tmp_data_dirs` fixture，不是這個環境變數。

**B2b. 節目清單也可以放在別處**

```powershell
$env:PODCAST_INGEST_CONFIG = "config/podcasts.local.yaml"
```

`config.py` 讀這個環境變數，未設定時預設為 `config/podcasts.yaml`。用途是**不要為了跑一次
擷取而編輯已進版控的節目清單**：`tests/test_contracts.py` 對那個檔案做精確集合斷言（刻意的守衛，
防止私人 profile 被 commit），所以在裡面加一個 `yt-…` 或 `x-…` profile 會讓它變紅，跑完還得記得
刪掉。`config/*.local.yaml` 已在 `.gitignore` 內，所以私人清單不會進版控。

**B3. 重新 ingest（乾淨開始）**

不複製任何東西，在新機器重跑一次擷取流程。轉錄會耗大量時間與算力。

複製完成後重建索引：

```powershell
python scripts/rebuild_cache.py --podcast gooaye
```

---

## C. 驗收清單

- [ ] `validate_mcp_setup.py` 回 `"ok": true`（安裝成功的判準）
- [ ] `python -m pytest` 全綠
- [ ] `rebuild_cache.py` 後搜尋得到既有逐字稿

---

## 已知限制與陷阱

**1. 版本鎖定檔沒進版控——而且第一次裝就漂移了。**
專案裡有 `uv.lock`，但它未被 git 追蹤，`pyproject.toml` 只寫版本下限（`>=`）。

實測證據：乾淨環境安裝後拿到的是 **`mcp-1.29.0`**，而當時另一份已封存的建置紀錄（tag `archive/hermes-audit-chain`）明確指定 **`mcp==1.28.1`**。兩台機器裝到不同版本的情形**已經發生**，不是理論風險。

要讓兩台一致，得把 `uv.lock` 加入版控並改用它安裝，或在 `pyproject.toml` 釘上上限。在那之前，換機器時務必確認實際裝到的 SDK 版本。

**2. GPU 轉錄的系統相依不在 pip 範圍。**
`--device cuda` 需要 NVIDIA 驅動、cuBLAS 與 cuDNN 在 PATH 上。faster-whisper 的 ct2 只內建 cuDNN，**不含 cuBLAS**，要另外準備。沒有 GPU 就用預設的 `--device cpu`。

---

## 疑難排解

先看 `docs/mcp-troubleshooting.md`。其他相關文件：

- `docs/mcp-usage.md` — MCP tools 用法
- `docs/claude-mcp-setup.md` / `docs/codex-mcp-setup.md` — 本機 stdio client 設定
