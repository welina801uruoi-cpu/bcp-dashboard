@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ======================================================================
echo   BCP 国内災害情報 ＆ 海外危機管理 統合ダッシュボード 起動システム
echo ======================================================================
echo.

:: カレントディレクトリをスクリプトの場所に固定
cd /d "%~dp0"

:: 1. Pythonの存在確認
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python がインストールされていないか、PATHが通っていません。
    echo Python 3.10 以上をインストールし、「Add Python to PATH」にチェックを入れてください。
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. 仮想環境 (venv) の確認と自動作成
if not exist "venv" (
    echo [INFO] 初回起動のため、Python仮想環境 (venv) を作成しています...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] 仮想環境の作成に失敗しました。
        pause
        exit /b 1
    )
    echo [INFO] 仮想環境の作成が完了しました。
)

:: 3. 仮想環境のアクティベート
call venv\Scripts\activate.bat

:: 4. 依存パッケージの確認とインストール
if exist "requirements.txt" (
    echo [INFO] 依存パッケージをチェック・インストールしています...
    pip install -r requirements.txt --quiet
)

:: 5. 5秒後にブラウザでダッシュボードを開くバックグラウンド処理
start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:5000/"

:: 6. Flask バックエンドサーバーの起動
echo.
echo ======================================================================
echo   システムが正常に起動しました！
echo   - 国内災害情報: http://127.0.0.1:5000/
echo   - 海外危機管理: http://127.0.0.1:5000/overseas
echo   サーバーを停止するには、このウィンドウで Ctrl + C を押してください。
echo ======================================================================
echo.

python backend_server.py

pause
