# 安裝與移植指南

把 podcast-ingest-core 的 22 個 MCP tools 與 portable Skills 裝到一台新電腦上。

本文件分四段：**A 裝核心**（任何機器都要做）、**B 搬資料**、**C 接上 Hermes**（只有要用 Hermes 才需要）、**D 驗收**。
最後一段是**已知限制**，動手前請先看過。

> **A 段已實測驗證。** 在一個模擬全新 clone 的乾淨環境（無 `data/`、全新 venv）中從頭跑過一次：
> `pip install -e .[dev]` 成功、`import podcast_ingest_core` 成功、`validate_mcp_setup.py` 回 `"ok": true`。
> C 段的指令對照過程式碼與設定檔，但未在第二台實機跑過。
>
> ⚠️ **`python -m pytest` 在正確安裝的環境下全綠。** Spec 030–034 的 BLOCKED 文件鏈已從預設
> 執行排除（清單與理由見 `pyproject.toml` 的 `[tool.pytest.ini_options]`）。被排除的檔案沒有
> 消失，指定路徑就跑得到，各自也有 `scripts/verify_spec_0NN*.py` 離線入口。
>
> 💡 **有紅燈就代表環境沒裝對，失敗仍然是安裝正確性的訊號。** `test_spec_029_offline`、
> `test_mcp_http_transport`、`test_hermes_runtime_capability` 三個檔案刻意留在預設執行裡。
> 它們用子行程執行 CLI，而子行程繼承不到 pytest 的設定，所以只要環境不符 `pyproject.toml`
> 的宣告就會紅。**實測 2026-08-22** 在一台看似正常的機器上抓到兩個缺口：
>
> | 症狀 | 原因 | 修法 |
> |---|---|---|
> | `test_mcp_http_transport` 三個測試全紅 | `mcp` 裝的是 1.10.1，低於宣告的 `>=1.27` | `pip install -U "mcp[cli]>=1.27,<2"` |
> | `ModuleNotFoundError: No module named 'podcast_ingest_core'` | A2 的 `pip install -e .` 從未執行；`pythonpath = ["src"]` 只對 pytest 本身有效 | `pip install -e .[dev]` |
>
> 兩個補上後這三個檔案 35 passed。
>
> ⚠️ **`validate_mcp_setup.py` 不能單獨當環境完整性的判準。** 上述兩個缺口都存在時，它仍回
> `ok: true`、18 項全過——它驗的是產品功能可用，不是環境符合宣告。兩者要一起看。

---

## 前置需求

| 項目 | 需求 | 備註 |
|---|---|---|
| Python | 3.11 以上 | `pyproject.toml` 的 `requires-python` |
| Git | 任意近期版本 | |
| WSL2 + Docker | **僅 C 段需要** | Hermes sidecar 與驗證器都必須在 POSIX 環境跑 |
| NVIDIA 驅動 + cuBLAS/cuDNN | **僅 GPU 轉錄需要** | 見「已知限制」 |
| `ffmpeg` 在 `PATH` | **僅 YouTube 影片擷取需要** | yt-dlp 要合併 YouTube 的分離影音流；X 影片是混流 MP4，不需要 |
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

`validate_mcp_setup.py` 是本機 readiness 檢查，會確認 MCP server 能起、tool registry 完整（22 個）、搜尋路徑可用。**這是判斷安裝成功與否的依據。**

想跑測試的話直接跑就好——BLOCKED 的 Hermes 鏈已經是 `pyproject.toml` 裡的預設排除：

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

## C. 接上 Hermes（選用）

前提：新機器上你已自行安裝好 Hermes / OpenAB，且 podcast-ingest-core 與 OpenAB 是**同層目錄**。

### C1. 建置 sidecar image

```powershell
wsl.exe -d <你的WSL發行版> -u root bash scripts/build_hermes_sidecar.sh podcast-ingest-core-mcp:local
wsl.exe -d <你的WSL發行版> -u root docker image inspect --format "{{.Id}}" podcast-ingest-core-mcp:local
```

把印出來的 image ID 記下來。建置只會把套件 metadata、`src/`、`config/`、HTTP runner 與 Dockerfile 放進 context——`.env`、`data/`、測試、agent 狀態都不會進 image。

### C2. 驗證 Compose 定義再啟動

```powershell
docker compose -f deploy/hermes/docker-compose.sidecar.yml config --quiet
docker compose -f deploy/hermes/docker-compose.sidecar.yml up -d
docker inspect --format "{{.State.Health.Status}}" podcast-ingest-core-mcp
```

服務綁 `127.0.0.1:8767`，使用 host network，**不對外開 port**，以非 root 的 `podcast` 使用者執行。

資料目錄不在預設位置時設定：

```powershell
$env:PODCAST_INGEST_HOST_DATA_DIR = "D:\podcast-data"
```

### C3. 同步 config 與 Skills

```powershell
$IntegrationArgs = @(
  "--config-path",       "<hermes-data>/config.yaml",
  "--skills-source",     ".agents/skills",
  "--skills-target",     "<hermes-data>/podcast-ingest-core-skills",
  "--local-skills-root", "<hermes-data>/skills",
  "--backup-root",       "<hermes-data>/integration-backups"
)
python scripts/manage_hermes_integration.py plan  @IntegrationArgs   # 零寫入預覽
python scripts/manage_hermes_integration.py apply @IntegrationArgs   # 備份後原子套用
```

`plan` 先看、`apply` 才寫。`apply` 會回傳一個 **manifest 路徑，務必保存**——回滾時要用，而且必須帶當初那組完全相同的路徑：

```powershell
python scripts/manage_hermes_integration.py rollback `
  --manifest "<備份路徑>/manifest.json" `
  --config-path "<與 apply 相同>" `
  --skills-target "<與 apply 相同>"
```

若 OpenAB 是用 `config.yaml.template` 產生 live config，helper 要指向 **template**，不要指向含憑證的 live config。

### C4. 重啟 Hermes 並確認發現

```powershell
docker restart <hermes-container>
docker exec <hermes-container> hermes mcp test podcast-ingest-core
docker exec <hermes-container> hermes skills list --source local --enabled-only
```

---

## D. 驗收清單

- [ ] `validate_mcp_setup.py` 回 `"ok": true`（安裝成功的判準）
- [ ] 核心產品測試全綠（全套的 ~24 個 Hermes 紅燈是預期的）
- [ ] `rebuild_cache.py` 後搜尋得到既有逐字稿
- [ ] sidecar health 為 `healthy`
- [ ] `hermes mcp test` 看得到 **22 個** tools
- [ ] `hermes skills list` 看得到同步過去的 Skills
- [ ] integration manifest 路徑已保存

---

## 已知限制與陷阱

**1. 版本鎖定檔沒進版控——而且第一次裝就漂移了。**
專案裡有 `uv.lock`，但它未被 git 追蹤，`pyproject.toml` 只寫版本下限（`>=`）。

實測證據：乾淨環境安裝後拿到的是 **`mcp-1.29.0`**，但 sidecar 的建置紀錄明確指定 **`mcp==1.28.1`**。兩台機器裝到不同版本的情形**已經發生**，不是理論風險。

要讓兩台一致，得把 `uv.lock` 加入版控並改用它安裝，或在 `pyproject.toml` 釘上上限。在那之前，sidecar image 重建時務必確認 SDK 版本。

**2. 兩份 Skill 清單，用途不同（五個都會同步）。**
`hermes_integration.py` 有兩個常數，刻意分開：

- `MANAGED_SKILLS`（四個）— Spec 027 的**契約**集合。027 要求每個 Skill 的 `SKILL.md` 只能提到它自己綁定的那一個 registry tool，違反就以 `WRONG_TOOL_MAPPING` fail closed。這四個各自只提到一個 tool。
- `SYNCED_SKILLS`（五個）— **實際會複製到 Hermes 的**集合，額外含 `historical-episode-verified-report-path`。

第五個是**調度器**（先診斷再分流），`SKILL.md` 依設計會提到四個 tool，本質上無法滿足 027 的單一 tool 契約——所以它同步過去，但不進入 027 的契約集合。它有自己的 Spec 023 契約測試（`tests/test_historical_verified_report_path_skill.py`）。

修改 `MANAGED_SKILLS` 會觸發 027 的 drift 檢查；要增減**同步**內容請改 `SYNCED_SKILLS`。

**2a. 兩項合法變更使 Hermes 稽核鏈的 digest 基準失效（待負責人重建）。**

Spec 026–034 以 SHA-256 釘住檔案位元組。以下兩項變更是刻意且經過驗證的，但它們使既有基準過期：

- **`SYNCED_SKILLS`**（讓第五個 Skill 隨 `apply` 同步）
- **Tool 22 `generate_stock_lens_report`**（含用官方腳本 `scripts/export_spec029_tool_descriptor_snapshot.py` 重簽 descriptor 快照）
- **Tool 23 `ingest_x_video`**（同一官方腳本再次重簽 descriptor 快照；deny adapter size 22→23）
- **Tool 24 `ingest_youtube_video`**（同一官方腳本再次重簽 descriptor 快照；deny adapter size 23→24）
- **Tool 25 `derive_workflow_bundle`**（spec 043；同一官方腳本再次重簽 descriptor 快照；deny adapter size 24→25;`hermes_skill_protocol` 的 AST 清單與其內部 exact-count 閘門同步）
- **把 Tool 22 補進 Spec 026 的 live harness**（否則新機器的授權 preflight 會判定 registry 不符而失敗）
- **把 Tool 25 補進同一個 live harness**（`scripts/validate_hermes_integration.py` 的 `EXPECTED_TOOL_ORDER` 與 `tests/test_hermes_live_smoke.py` 的副本;上一條的教訓在 043 又重演了一次,因為那份清單寫死且其鏡像測試自帶同樣過期的期望值,所以永遠是綠的）

需要重建基準的檔案與**目前**的正確 digest：

| 檔案 | 目前 SHA-256 |
|---|---|
| `deploy/hermes/README.md` | `e13769dd02fed7d38f91e49f24d716b27e6ab42cbec6bcc0218f48af72dc29e8` |
| `deploy/hermes/spec029/contracts/mcp-tool-descriptor-snapshot.json` | `2c712c4e7b4c78370a904e4fc2dfa6c24268b1cd10cc533dd4ef2fa8f02919d0` |
| `deploy/hermes/spec029/spec029_mcp_deny_adapter.py` | `95687aa845e00808c9f0a38883a0b1e6aa01eac0b99467fdd8f86fc5178132fd` |
| `scripts/validate_hermes_integration.py` | `08442ddac0815330dc62bdf0164007ade4bec0d4693ad36d7575065d03c10efe` |
| `specs/027-.../contracts/skill-routing-and-protocol.md` | `b0c5622041102294bc976826f445c1f64fbdcd11b01e5cefdb6a839c97a0c097` |
| `src/podcast_ingest_core/hermes_integration.py` | `311706a0d1d5b8d1a1cf719013d4720b62b61270941c5e69e10301b34cb29e43` |
| `src/podcast_ingest_core/hermes_skill_protocol.py` | `860a714e8c8c66cbc030a875e30b0b8c2dbdff2466f13166588c7a35a303269a` |
| `src/podcast_ingest_core/mcp_server.py` | `8f2635710d1cf02d11a4d828a5b35ca0ece521f2e4c19401ffaf434417eaebbc` |
| `tests/test_hermes_integration.py` | `e51321608916b5c2227b96e47237cf538124caf347fd51c038f70ef0cb771fac` |
| `tests/test_hermes_live_smoke.py` | `7c4b5024b55959fcc528cefd7b746bda7a46570fbf3e6940ef5e3b5f217d4ae2` |
| `tests/test_hermes_skill_protocol.py` | `43577f95d9b58ff3f60ae2abd055eda5cd690c388a33aa6e68d3a1c61f2eaced` |
| `tests/test_spec_027_hermes_skill_protocol_docs.py` | `bd8e11ff9cfe4a97dfb99ff49122eba604820188185e75ea4966e6fec2337ae7` |
| `tests/test_spec_029_offline.py` | `f12cddb4409e1856700e3bf0e27f5698195b4045b4a829458549b3c4c3035b1b` |

110 個條目中 13 個需重建，其餘 97 個仍吻合。

記錄基準的兩處：`specs/032-.../contracts/predecessor-digests.json`（110 個條目，其餘 101 個仍吻合）與 `tests/test_spec_030_g1r_offline_remediation.py::test_task42_deep_ledger_adapter_hash_and_verifier_guards`（測試內硬編 4 個）。

對應失敗的測試：

```
test_spec_033_hermes_source_audit_docs::test_predecessor_boundary_covers_spec029_through_spec032_...
test_spec_030_g1r_offline_remediation::test_task42_deep_ledger_adapter_hash_and_verifier_guards
```

**功能本身不受影響**：`test_hermes_integration.py` 全綠（`apply` 確實同步五個 Skill），Tool 22 的 registry／契約／文件一致性測試全綠。這是稽核證據邊界待重建，不是功能缺陷——重建前請勿把這兩個紅燈解讀為同步或 registry 壞掉。

**3. 驗證器不能在原生 Windows 跑。**
`validate_hermes_integration.py` 需要 descriptor-only no-follow 的檔案系統原語，原生 Windows 會在碰觸受保護路徑**之前**就 fail closed。請在 WSL/Docker 內執行。

**4. GPU 轉錄的系統相依不在 pip 範圍。**
`--device cuda` 需要 NVIDIA 驅動、cuBLAS 與 cuDNN 在 PATH 上。faster-whisper 的 ct2 只內建 cuDNN，**不含 cuBLAS**，要另外準備。沒有 GPU 就用預設的 `--device cpu`。

**5. `.env` 與 Hermes 憑證是分開的受保護面。**
兩者都不放進 image、不放進任一 repo。含憑證的 live config 要逐位元組備份，只透過官方 Hermes CLI 設定，不要解析或輸出其內容。template 綁定的 manifest **無法**回滾 live config。

**6. Hermes 整合的正式狀態是 Blocked。**
Spec 026 因 C7（Hermes 執行期路由證據）未取得而維持 Blocked，Spec 030–034 的離線稽核鏈同樣未完成。**這不影響你手動安裝 Hermes 並依本文件使用**——被擋住的是「自動啟用與執行期觀測」的保證，不是傳輸通道或 Skill 同步（那些的測試都是綠的）。

**7. C6 live 驗證有一次性限制。**
舊機器已用掉它唯一一次核准的 C6 validator 執行，不可重跑。新機器屬於另一次獨立安裝，需要自己的授權範圍。

---

## 疑難排解

先看 `docs/mcp-troubleshooting.md`。其他相關文件：

- `docs/mcp-usage.md` — MCP tools 用法
- `docs/claude-mcp-setup.md` / `docs/codex-mcp-setup.md` — 本機 stdio client 設定
- `deploy/hermes/README.md` — sidecar 部署細節
- `specs/026-hermes-mcp-integration/quickstart.md` — 原始移植 runbook
