# BCP 国内災害情報 ＆ 海外危機管理 統合ダッシュボード

**BCP (Business Continuity Plan) Disaster & Global Crisis Management Dashboard**

日本国内の自然災害・インフラ障害と、世界各国の地政学リスク・治安・交通網・ライフライン危機をリアルタイムに一元監視・可視化する統合危機管理コックピット／ダッシュボードシステムです。

---

## 1. システム概要と特徴

1. **24時間365日 クラウド常時稼働 (PC停止時も動作)**:
   - **GitHub Pages & GitHub Actions**: PCの電源を切っていても、GitHubのクラウドサーバーが15分おきに自動巡回・データ収集を行い、静的ダッシュボード（`index.html` / `overseas.html`）を最新化。スマホやタブレットからいつでもリアルタイム監視可能。
2. **2つの専用ダッシュボード**:
   - 🇯🇵 **国内災害情報ダッシュボード (`/`)**: 地震（気象庁震度速報）、津波、火山、気象警報、河川氾濫、避難情報、警察・消防出動、電力・水道・ガス、鉄道交通網、通信4キャリア、SNS口コミ緊急ワード監視、総合BCP/行政速報の12大指標。
   - 🌍 **海外危機管理ダッシュボード (`/overseas`)**: 外務省危険レベル、感染症危険情報、在外公館領事速報、USGS世界大地震、現地気象・異常気象、リアルタイム為替（yfinance連動）、国際線主要ハブ空港、交通網・労組ストライキ、ライフライン・通信インフラ、治安・テロ警戒（MI5/JTACテロ脅威連動）、海外SNS口コミ監視、医療・救護態勢の12大指標。
2. **24時間メディア統合**:
   - YouTube LIVE（NHK/ウェザーニュース/TBS/日テレ/テレ朝/フジ / 海外: BBC/Sky News/France24/DW/NHK World）
   - 定点ライブカメラ（国内: 渋谷/大阪/那覇/富士山/桜島 / 海外: ロンドン/NY/パリ/ベルリン/ローマ）
   - 気象庁・Windy世界リアルタイム雨雲・台風レーダー
3. **柔軟な表示モード**:
   - **20m遠視認モード**: 大型司令室モニター・プロジェクター向け（特大フォント、高コントラスト設計）
   - **スマホ（iPhone 15等）完全最適化**: 1画面モード（スクロール不要で12指標全貌把握）とスクロールモードをワンタップ切替。
4. **指標 閾値カスタマイズ機能**:
   - 国内外ともに、各指標が「注意（黄）」「警戒（赤）」に切り替わる基準値をユーザーがブラウザ上で自由に変更可能（`localStorage` 永続保存＆即時再判定）。

---

## 2. 開発環境・動作要件

- **OS**: Windows 10 / 11, macOS, Linux
- **Python**: Python 3.10 以上 (Python 3.11 推奨)
- **ブラウザ**: Google Chrome, Microsoft Edge, Safari 等（モダンブラウザ）
- **通信環境**: インターネット接続（外部API、気象庁、USGS、yfinance、YouTube等の取得に必要）

---

## 3. セットアップ手順

### 【方法 0】GitHub 24時間常時稼働セットアップ（PC不要・スマホ閲覧）

ご自身のPCの電源を切っていても、GitHub上でダッシュボードを24時間稼働させる手順です：

1. **GitHubで新規リポジトリを作成**:
   - [https://github.com/new](https://github.com/new) にアクセスします。
   - Repository name に `bcp-dashboard` （または任意名）を入力し、「Create repository」をクリック。
2. **ワンクリックでGitHubへプッシュ**:
   - `BCP/` フォルダ内の **`push_to_github.bat`** をダブルクリック。
   - 作成したリポジトリURL（例: `https://github.com/welina801uruoi-cpu/bcp-dashboard.git`）を入力してEnter。
   - 自動でファイルがGitHubへプッシュされます。
3. **GitHub Pages の有効化**:
   - GitHubのリポジトリページで **Settings** > **Pages** を開きます。
   - **Source**: `Deploy from a branch` を選択。
   - **Branch**: `main` ブランチ、フォルダ `/ (root)` を選択して **Save** をクリック。
4. **利用開始**:
   - 発行されたURL（`https://welina801uruoi-cpu.github.io/bcp-dashboard/`）にアクセスすれば、スマホやPCから常時閲覧できます！
   - GitHub Actions（`.github/workflows/update_dashboard.yml`）が15分おきに自動巡回し、最新データに自動更新し続けます。

---

### 【方法 A】Windows ワンクリックローカル起動（開発・ローカル運用）

1. プロジェクトフォルダ（`BCP/`）をコピーまたは配置します。
2. フォルダ内の **`run_dashboard.bat`** をダブルクリックします。
   - Python仮想環境（`venv`）の作成
   - 依存パッケージ（`requirements.txt`）の自動インストール
   - バックエンドサーバーの自動起動
   - ブラウザ（`http://127.0.0.1:5000/`）の自動オープン
   が全自動で行われます。

---

### 【方法 B】手動セットアップ（コマンドライン）

```powershell
# 1. BCPディレクトリへ移動
cd BCP

# 2. 仮想環境の作成とアクティベート (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# ※ Mac/Linuxの場合: source venv/bin/activate

# 3. 依存ライブラリのインストール
pip install -r requirements.txt

# 4. サーバー起動
python backend_server.py
```

起動後、ブラウザで以下のURLを開きます：
- **国内災害情報**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **海外危機管理**: [http://127.0.0.1:5000/overseas](http://127.0.0.1:5000/overseas)

---

## 4. プロジェクト構成とファイル役割

```text
BCP/
├── backend_server.py         # Flask バックエンド API サーバー (国内・海外データ統合・スクレイピング)
├── BCP-dashboard.html        # 国内災害情報ダッシュボード SPA (HTML/CSS/JS)
├── overseas-dashboard.html   # 海外危機管理ダッシュボード SPA (HTML/CSS/JS)
├── requirements.txt          # Python 依存ライブラリ定義
├── run_dashboard.bat         # Windows用ワンクリック自動起動バッチ
├── README.md                 # 本マニュアル
├── PROMPT_FOR_AI.md          # 他PCでAIに開発を引き継ぐための完全指示プロンプト
├── manifest.json             # PWA Webアプリマニフェスト
├── sw.js                     # Service Worker
└── docs/
    └── screenshots/          # 動作確認・設計仕様スクリーンショット
        ├── 01_domestic_pc_main.png
        ├── 02_domestic_pc_threshold_modal.png
        ├── 03_domestic_pc_detail_modal.png
        ├── 04_domestic_mobile_compact.png
        ├── 05_domestic_mobile_scroll.png
        ├── 06_overseas_pc_main.png
        ├── 07_overseas_pc_transit_modal.png
        ├── 08_overseas_pc_lifeline_modal.png
        ├── 09_overseas_pc_security_modal.png
        ├── 10_overseas_pc_threshold_modal.png
        ├── 11_overseas_mobile_compact.png
        └── 12_overseas_mobile_scroll.png
```

---

## 5. 画面キャプチャギャラリー（正常動作イメージ）

各画面のキャプチャ画像は `docs/screenshots/` に格納されています。他のPCで動作させた際、これらのキャプチャと同じ画面・レイアウト・動作になっているかを確認してください。

### ① 国内災害情報ダッシュボード
| 画面 | ファイル名 | 説明 |
| :--- | :--- | :--- |
| **PC デスクトップ全体** | `01_domestic_pc_main.png` | 12指標カード、YouTube生放送、ライブカメラ、気象レーダー |
| **国内 閾値設定画面** | `02_domestic_pc_threshold_modal.png` | 地震震度、警報モード、津波警報、停電規模の閾値可変モーダル |
| **指標 詳細解析画面** | `03_domestic_pc_detail_modal.png` | 気象庁地震情報等の詳細データ展開モーダル |
| **スマホ 1画面モード** | `04_domestic_mobile_compact.png` | iPhone 15 等の縦長画面にスクロール不要で12指標が収まるモード |
| **スマホ スクロールモード** | `05_domestic_mobile_scroll.png` | 詳細カードや生放送プレイヤーを縦スクロールで順次閲覧するモード |

### ② 海外危機管理ダッシュボード
| 画面 | ファイル名 | 説明 |
| :--- | :--- | :--- |
| **PC デスクトップ全体** | `06_overseas_pc_main.png` | イギリス選択時：交通遅延アラート（Victoria線）、治安注意、リアルタイム為替連動 |
| **交通網・ストライキ詳細** | `07_overseas_pc_transit_modal.png` | 4大交通機関一覧、Victoria線遅延インシデント、管轄全19路線チップ |
| **ライフライン・通信詳細** | `08_overseas_pc_lifeline_modal.png` | 送電網、主要通信4社、国際IX接続性、都市インフラの常時監視一覧 |
| **治安・テロ警戒詳細** | `09_overseas_pc_security_modal.png` | MI5/JTACテロ脅威レベル（Substantial）、抗議デモ・放火インシデント一覧 |
| **海外 閾値設定画面** | `10_overseas_pc_threshold_modal.png` | 外務省危険レベル、為替変動率、USGS地震M、空港欠航率の閾値可変モーダル |
| **スマホ 1画面モード** | `11_overseas_mobile_compact.png` | 海外12指標がスクロールなしで収まり、ボトムドックから生放送・カメラへ即アクセス |
| **スマホ スクロールモード** | `12_overseas_mobile_scroll.png` | 海外メディア（BBC/Sky News等）やカメラ、全指標を順次確認するモード |

---

## 6. トラブルシューティング

- **Q. `Port 5000 is already in use` というエラーが出る**
  - **A**: すでに前回の `backend_server.py` または他のアプリ（AirPlay等）がポート5000を使用しています。
  - Windows PowerShell で以下を実行して該当プロセスを終了させてください：
    ```powershell
    Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process -Force
    ```
- **Q. 為替レートが取得できない（`レート取得中...` のまま）**
  - **A**: `yfinance` パッケージがインストールされているか確認してください（`pip install yfinance`）。オフライン環境やレート取得制限時は安全側のフォールバック値が自動設定されます。
- **Q. 社内プロキシ環境で動かない**
  - **A**: `HTTP_PROXY`, `HTTPS_PROXY` 環境変数を設定するか、`backend_server.py` 内の `urllib.request` にプロキシ設定を追記してください。
