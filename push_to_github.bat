@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ===================================================
echo   BCPダッシュボード GitHub 初期プッシュ・同期ツール
echo ===================================================
echo.
echo PCが起動していなくてもGitHub上でBCPダッシュボードを
echo 24時間常時稼働させるための初回セットアップを行います。
echo.
echo ※ GitHub ( https://github.com/new ) で新しいリポジトリ
echo   （例: bcp-dashboard ）を「Public」または「Private」で作成してください。
echo.

set /p REPO_URL="GitHubリポジトリのURLを入力してください (例: https://github.com/welina801uruoi-cpu/bcp-dashboard.git): "

if "%REPO_URL%"=="" (
    echo [エラー] URLが入力されませんでした。処理を中止します。
    pause
    exit /b
)

echo.
echo [1/4] Gitリポジトリの初期化中...
if not exist ".git" (
    git init
    git branch -M main
)

echo.
echo [2/4] リモートリポジトリの設定中...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo.
echo [3/4] ファイルのステージングとコミット中...
git add .
git commit -m "feat: initial commit for 24/7 cloud BCP dashboard"

echo.
echo [4/4] GitHubへプッシュ中...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================================
    echo  [成功] GitHubへのプッシュが正常に完了しました！
    echo ===================================================
    echo.
    echo 【次のステップ: GitHub Pagesの有効化】
    echo 1. GitHubのリポジトリページを開きます。
    echo 2. [Settings] タブ -^> 左メニューの [Pages] を開きます。
    echo 3. [Build and deployment] の Source を「Deploy from a branch」にします。
    echo 4. Branch を「main」/「/ (root)」にして [Save] をクリックします。
    echo 5. 数分後、発行されたURL ( https://welina801uruoi-cpu.github.io/... )
    echo    からPC停止時でもスマホや別PCでアクセスできるようになります！
    echo.
) else (
    echo.
    echo ===================================================
    echo  [エラー] プッシュに失敗しました。
    echo  リポジトリURLまたはGitHub認証情報を確認してください。
    echo ===================================================
)
pause
