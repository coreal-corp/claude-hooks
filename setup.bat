@echo off
REM Claude Code Hooks - Automated Setup Script for Windows
REM Automatically checks and installs Python 3.6+ if needed

setlocal enabledelayedexpansion

echo.
echo ======================================
echo   Claude Code Hooks - Setup Script
echo ======================================
echo.

REM Required Python version
set "REQUIRED_PYTHON_MAJOR=3"
set "REQUIRED_PYTHON_MINOR=6"

REM Script directory
set "SCRIPT_DIR=%~dp0"
set "HOOKS_DIR=%USERPROFILE%\.claude-hooks"
set "ENV_FILE=%USERPROFILE%\.ultrathink.env"

REM Step 1: Check Python installation
echo [*] Step 1: Python 버전 확인 중...

set "PYTHON_CMD="

REM Check python3 command
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('python3 --version 2^>^&1') do set "PYTHON_VERSION=%%v"
    call :check_version "!PYTHON_VERSION!"
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python3"
        echo [+] Python 3 발견: !PYTHON_VERSION!
        goto :python_found
    )
)

REM Check python command
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%v"
    call :check_version "!PYTHON_VERSION!"
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python"
        echo [+] Python 발견: !PYTHON_VERSION!
        goto :python_found
    )
)

REM Python not found or version too old
echo [!] Python 3.6 이상을 찾을 수 없습니다.
echo.
echo Python 설치가 필요합니다. 자동으로 설치하시겠습니까? (y/n)
set /p "INSTALL_CHOICE=선택: "

if /i not "!INSTALL_CHOICE!"=="y" (
    echo.
    echo [i] 수동 설치를 선택하셨습니다.
    echo.
    echo Python 3.6 이상을 다음 방법으로 설치하세요:
    echo.
    echo   1. 공식 사이트: https://www.python.org/downloads/
    echo   2. winget 사용: winget install Python.Python.3
    echo   3. Chocolatey 사용: choco install python
    echo.
    echo 설치 후 이 스크립트를 다시 실행하세요.
    pause
    exit /b 1
)

REM Try to install Python
echo.
echo [*] Python 자동 설치 시도 중...

REM Check if winget is available (Windows 10+)
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo [i] winget을 사용하여 Python 설치 중...
    echo [i] 관리자 권한이 필요할 수 있습니다.
    winget install Python.Python.3 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% equ 0 (
        echo [+] Python 설치 완료!
        echo [*] Python 실행파일 탐색 중...
        echo.

        REM Python 설치 직후 일반적인 경로들을 순차적으로 확인
        set "FOUND_PYTHON="

        REM 1. 사용자 설치 경로 (가장 흔함 - winget 기본 경로)
        for /d %%p in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
            if exist "%%p\python.exe" (
                set "PYTHON_CMD=%%p\python.exe"
                set "FOUND_PYTHON=1"
                goto :python_found_after_install
            )
        )

        REM 2. WindowsApps 경로 (Microsoft Store 버전)
        if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
            set "PYTHON_CMD=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
            set "FOUND_PYTHON=1"
            goto :python_found_after_install
        )

        REM 3. Program Files 경로 (시스템 전역 설치)
        for /d %%p in ("%ProgramFiles%\Python3*") do (
            if exist "%%p\python.exe" (
                set "PYTHON_CMD=%%p\python.exe"
                set "FOUND_PYTHON=1"
                goto :python_found_after_install
            )
        )

        REM 4. C:\ 루트 경로 (레거시 설치)
        for /d %%p in ("C:\Python3*") do (
            if exist "%%p\python.exe" (
                set "PYTHON_CMD=%%p\python.exe"
                set "FOUND_PYTHON=1"
                goto :python_found_after_install
            )
        )

        REM 경로를 못 찾은 경우 - 기존 동작 유지 (재시작 안내)
        echo [!] Python 실행파일을 찾을 수 없습니다.
        echo [i] PATH 업데이트를 위해 터미널을 재시작하세요.
        echo.
        echo 설치 후 이 스크립트를 다시 실행하세요.
        pause
        exit /b 0
    ) else (
        echo [!] winget 설치 실패
        goto :manual_install
    )
) else (
    echo [!] winget을 찾을 수 없습니다.
    goto :manual_install
)

:manual_install
echo.
echo [i] 자동 설치 실패. 수동 설치가 필요합니다.
echo.
echo 다음 링크에서 Python을 다운로드하세요:
echo https://www.python.org/downloads/
echo.
echo 설치 시 "Add Python to PATH" 옵션을 체크하세요!
echo.
pause
exit /b 1

:python_found_after_install
REM Python found after installation - continue with setup
echo [+] Python 발견: %PYTHON_CMD%
echo.

:python_found
REM Verify Python modules
echo [*] Python 모듈 확인 중...
%PYTHON_CMD% -c "import sys; import json; import os; import urllib.request" 2>nul
if %errorlevel% neq 0 (
    echo [!] Python 모듈 확인 실패
    exit /b 1
)
echo [+] 필수 Python 모듈 확인 완료

REM Step 2: Create hooks directory
echo.
echo [*] Step 2: Hook 디렉토리 생성 중...

if not exist "%HOOKS_DIR%" (
    mkdir "%HOOKS_DIR%"
    echo [+] 디렉토리 생성: %HOOKS_DIR%
) else (
    echo [i] 디렉토리 이미 존재: %HOOKS_DIR%
)

REM Step 3: Copy hook files
echo.
echo [*] Step 3: Hook 파일 복사 중...

set "FILES=SessionStart SessionEnd Stop Notification analyze_transcript.py"

for %%f in (%FILES%) do (
    if exist "%SCRIPT_DIR%%%f" (
        copy /y "%SCRIPT_DIR%%%f" "%HOOKS_DIR%\" >nul
        echo [+] 복사 완료: %%f
    ) else (
        echo [!] 파일을 찾을 수 없음: %%f
    )
)

REM Step 4: Create environment file template
echo.
echo [*] Step 4: 환경 변수 파일 생성 중...

if not exist "%ENV_FILE%" (
    (
        echo # Claude Code Slack Hooks Configuration
        echo.
        echo # Slack Bot Token (필수 - xoxb-로 시작^)
        echo SLACK_BOT_TOKEN=xoxb-YOUR-TOKEN-HERE
        echo.
        echo # Slack Channel ID (필수 - C로 시작하는 11자리, # 없이^)
        echo SLACK_CHANNEL_ID=C09J29WDSHK
        echo.
        echo # 자동 로깅 활성화
        echo ULTRATHINK_AUTO_LOG=true
        echo.
        echo # 사용자 이름 (선택^)
        echo SLACK_USER_NAME=your_name
    ) > "%ENV_FILE%"
    echo [+] 환경 변수 템플릿 생성: %ENV_FILE%
    echo [!] ⚠️  %ENV_FILE% 파일을 편집하여 Slack 토큰을 설정하세요!
) else (
    echo [i] 환경 변수 파일 이미 존재: %ENV_FILE%
)

REM Step 5: Verify installation
echo.
echo [*] Step 5: 설치 검증 중...

set "VERIFICATION_PASSED=1"

for %%f in (%FILES%) do (
    if not exist "%HOOKS_DIR%\%%f" (
        echo [!] 파일 없음: %%f
        set "VERIFICATION_PASSED=0"
    )
)

if not exist "%ENV_FILE%" (
    echo [!] 환경 변수 파일 없음: %ENV_FILE%
    set "VERIFICATION_PASSED=0"
)

if !VERIFICATION_PASSED! equ 1 (
    echo [+] 모든 검증 통과!
) else (
    echo [!] 일부 검증 실패. 위 메시지를 확인하세요.
    pause
    exit /b 1
)

REM Installation complete
echo.
echo ======================================
echo [+] 설치 완료!
echo ======================================
echo.
echo [i] 다음 단계:
echo.
echo   1. Slack 토큰 설정:
echo      notepad "%ENV_FILE%"
echo.
echo   2. SLACK_BOT_TOKEN을 실제 토큰으로 교체
echo.
echo   3. 테스트 실행:
echo      echo {"initial_user_message":"테스트"} ^| %PYTHON_CMD% "%HOOKS_DIR%\SessionStart"
echo.
echo   4. Slack 채널에서 알림 확인
echo.
echo [i] 문제 발생 시 로그 확인:
echo      type %TEMP%\claude-hook-debug.log
echo.
pause
exit /b 0

REM Function: Check Python version
:check_version
set "VERSION=%~1"
for /f "tokens=1,2 delims=." %%a in ("%VERSION%") do (
    set "MAJOR=%%a"
    set "MINOR=%%b"
)

if %MAJOR% gtr %REQUIRED_PYTHON_MAJOR% (
    exit /b 0
)
if %MAJOR% equ %REQUIRED_PYTHON_MAJOR% (
    if %MINOR% geq %REQUIRED_PYTHON_MINOR% (
        exit /b 0
    )
)
exit /b 1
