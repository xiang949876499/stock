# Stock Hub 启动脚本
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stock Hub - 量化交易一体化平台" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[信息] Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到 Python" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[信息] 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[成功] 虚拟环境创建完成" -ForegroundColor Green
}

# 安装依赖
if (-not (Test-Path ".venv\Lib\site-packages\fastapi")) {
    Write-Host "[信息] 安装依赖..." -ForegroundColor Yellow
    .venv\Scripts\pip.exe install -r requirements.txt
    Write-Host "[成功] 依赖安装完成" -ForegroundColor Green
}

# 检查配置
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "[警告] 请编辑 .env 配置 AI API Key" -ForegroundColor Yellow
}

# 创建目录
New-Item -ItemType Directory -Force -Path "data\catalog" | Out-Null
New-Item -ItemType Directory -Force -Path "data\daily\A" | Out-Null
New-Item -ItemType Directory -Force -Path "data\daily\HK" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

# 菜单
Write-Host ""
Write-Host "请选择操作:" -ForegroundColor White
Write-Host ""
Write-Host "  1 - 启动服务（后端 + 前端）" -ForegroundColor Cyan
Write-Host "  2 - 仅启动后端" -ForegroundColor Cyan
Write-Host "  3 - 仅启动前端" -ForegroundColor Cyan
Write-Host "  4 - 初始化数据" -ForegroundColor Cyan
Write-Host "  5 - 运行测试" -ForegroundColor Cyan
Write-Host "  6 - 退出" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "请输入选项"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "[信息] 启动后端..." -ForegroundColor Yellow
        Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m", "src.main", "serve" -WindowStyle Normal
        Start-Sleep -Seconds 3
        Write-Host "[信息] 启动前端..." -ForegroundColor Yellow
        Set-Location frontend
        Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WindowStyle Normal
        Set-Location ..
        Write-Host ""
        Write-Host "[成功] 服务已启动" -ForegroundColor Green
        Write-Host "  后端: http://localhost:8000" -ForegroundColor White
        Write-Host "  前端: http://localhost:3000" -ForegroundColor White
        Write-Host "  API: http://localhost:8000/docs" -ForegroundColor White
    }
    "2" {
        Write-Host ""
        Write-Host "[信息] 启动后端..." -ForegroundColor Yellow
        .venv\Scripts\python.exe -m src.main serve
    }
    "3" {
        Write-Host ""
        Write-Host "[信息] 启动前端..." -ForegroundColor Yellow
        Set-Location frontend
        npm run dev
        Set-Location ..
    }
    "4" {
        Write-Host ""
        Write-Host "[信息] 初始化数据..." -ForegroundColor Yellow
        .venv\Scripts\python.exe -m src.main init
        Write-Host "[成功] 初始化完成" -ForegroundColor Green
    }
    "5" {
        Write-Host ""
        Write-Host "[信息] 运行测试..." -ForegroundColor Yellow
        .venv\Scripts\python.exe -m pytest tests/ -v --tb=short
    }
    "6" {
        Write-Host "[信息] 退出" -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "[错误] 无效选项" -ForegroundColor Red
    }
}

Write-Host ""
Read-Host "按回车退出"
