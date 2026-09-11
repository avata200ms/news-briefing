<#
.SYNOPSIS
    news-briefing 프로젝트를 위한 Astral uv 기반 편의 런처 스크립트.
.DESCRIPTION
    모든 파이썬 및 패키지 도구를 'uv run' 가상환경 명령을 통해 안전하게 실행합니다.
.EXAMPLE
    .\dev.ps1 run
    .\dev.ps1 test
    .\dev.ps1 check
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet("run", "test", "lint", "format", "typecheck", "sync", "check", "django", "help")]
    [string]$Command = "help",

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

switch ($Command) {
    "run" {
        Write-Host "[news-briefing] 프로젝트 실행 중 (uv run)..." -ForegroundColor Cyan
        uv run news-briefing @ExtraArgs
    }
    "test" {
        Write-Host "[pytest] 단위 테스트 실행 중 (uv run pytest)..." -ForegroundColor Green
        uv run pytest -v @ExtraArgs
    }
    "lint" {
        Write-Host "[ruff] 코드 린트 검사 중 (uv run ruff check)..." -ForegroundColor Yellow
        uv run ruff check . @ExtraArgs
    }
    "format" {
        Write-Host "[ruff] 코드 자동 포맷팅 적용 중 (uv run ruff format)..." -ForegroundColor Magenta
        uv run ruff format . @ExtraArgs
    }
    "typecheck" {
        Write-Host "[mypy] 정적 타입 검사 중 (uv run mypy)..." -ForegroundColor Blue
        uv run mypy src @ExtraArgs
    }
    "sync" {
        Write-Host "[uv sync] 가상환경 및 의존성 동기화 중..." -ForegroundColor Cyan
        uv sync @ExtraArgs
    }
    "check" {
        Write-Host "[CHECK] 전체 코드 품질 점검 (Lint + Format Check + Typecheck + Tests)..." -ForegroundColor Cyan
        Write-Host "1. Ruff Lint 검사..." -ForegroundColor Yellow
        uv run ruff check .
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        Write-Host "2. Ruff Format 검사..." -ForegroundColor Yellow
        uv run ruff format --check .
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        Write-Host "3. Mypy 타입 검사..." -ForegroundColor Yellow
        uv run mypy src
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        Write-Host "4. Pytest 실행..." -ForegroundColor Yellow
        uv run pytest -v
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

        Write-Host "[SUCCESS] 모든 품질 점검을 통과했습니다!" -ForegroundColor Green
    }
    "django" {
        Write-Host "[Django] uv run python 실행..." -ForegroundColor Cyan
        uv run python @ExtraArgs
    }
    default {
        Write-Host "=========================================================" -ForegroundColor Cyan
        Write-Host "  news-briefing 개발 편의 런처 (uv 가상환경 기반)" -ForegroundColor White
        Write-Host "=========================================================" -ForegroundColor Cyan
        Write-Host "사용법: .\dev.ps1 <명령어> [추가 인자...]"
        Write-Host ""
        Write-Host "명령어 목록:"
        Write-Host "  run       : 프로젝트 메인 CLI 실행 (uv run news-briefing)"
        Write-Host "  test      : 단위 테스트 실행 (uv run pytest -v)"
        Write-Host "  lint      : Ruff 린트 검사 (uv run ruff check .)"
        Write-Host "  format    : Ruff 코드 포맷팅 (uv run ruff format .)"
        Write-Host "  typecheck : Mypy 정적 타입 검사 (uv run mypy src)"
        Write-Host "  sync      : 의존성 동기화 (uv sync)"
        Write-Host "  check     : Lint, Format, Type, Test 종합 무결성 검증"
        Write-Host "  django    : Django 관리 명령 실행 (예: .\dev.ps1 django manage.py runserver)"
        Write-Host "  help      : 도움말 출력"
        Write-Host "=========================================================" -ForegroundColor Cyan
    }
}
