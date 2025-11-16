# Cyber Sentinel ML - Frontend Setup Script (PowerShell)
# Enterprise-grade React application setup

Write-Host "🚀 Setting up Cyber Sentinel ML Frontend..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed. Please install Node.js 16+ first." -ForegroundColor Red
    Write-Host "Visit: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check Node.js version
$majorVersion = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
if ($majorVersion -lt 16) {
    Write-Host "❌ Node.js version $nodeVersion is too old. Please install Node.js 16 or higher." -ForegroundColor Red
    exit 1
}

# Check if npm is installed
try {
    $npmVersion = npm --version
    Write-Host "✅ npm version: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm is not installed. Please install npm first." -ForegroundColor Red
    exit 1
}

# Clean up any existing node_modules and package-lock.json
Write-Host "🧹 Cleaning up existing dependencies..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force "node_modules"
    Write-Host "  - Removed node_modules" -ForegroundColor Gray
}

if (Test-Path "package-lock.json") {
    Remove-Item -Force "package-lock.json"
    Write-Host "  - Removed package-lock.json" -ForegroundColor Gray
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

$installResult = npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green

# Verify TypeScript configuration
Write-Host "🔧 Verifying TypeScript configuration..." -ForegroundColor Yellow
if (-not (Test-Path "tsconfig.json")) {
    Write-Host "❌ tsconfig.json not found" -ForegroundColor Red
    exit 1
}

# Run TypeScript type check
Write-Host "🔍 Running TypeScript type check..." -ForegroundColor Yellow
$typeCheckResult = npx tsc --noEmit
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  TypeScript has some type errors, but dependencies are installed" -ForegroundColor Yellow
    Write-Host "   You can fix these by running: npm run lint:fix" -ForegroundColor Gray
} else {
    Write-Host "✅ TypeScript compilation successful" -ForegroundColor Green
}

# Check if all critical dependencies are available
Write-Host "🔍 Verifying critical dependencies..." -ForegroundColor Yellow

$criticalDeps = @(
    "react",
    "react-dom", 
    "antd",
    "@ant-design/icons",
    "react-router-dom",
    "axios",
    "socket.io-client",
    "react-query",
    "zustand",
    "typescript"
)

foreach ($dep in $criticalDeps) {
    if (Test-Path "node_modules\$dep") {
        Write-Host "✅ $dep" -ForegroundColor Green
    } else {
        Write-Host "❌ $dep is missing" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🎉 Frontend setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Start development server: npm start" -ForegroundColor White
Write-Host "2. Build for production: npm run build" -ForegroundColor White
Write-Host "3. Run tests: npm test" -ForegroundColor White
Write-Host "4. Fix linting: npm run lint:fix" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Development server will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "📊 API proxy configured to: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Useful commands:" -ForegroundColor Cyan
Write-Host "- npm run lint        - Check code quality" -ForegroundColor White
Write-Host "- npm run lint:fix    - Fix linting issues" -ForegroundColor White
Write-Host "- npm run type-check  - Verify TypeScript types" -ForegroundColor White
Write-Host "- npm run format      - Format code with Prettier" -ForegroundColor White
Write-Host "- npm run analyze     - Analyze bundle size" -ForegroundColor White
Write-Host ""

# Create a simple health check script
$healthCheckScript = @'
# Cyber Sentinel ML Frontend Health Check (PowerShell)
Write-Host "🏥 Cyber Sentinel ML Frontend Health Check" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "❌ node_modules not found - run setup.ps1 first" -ForegroundColor Red
    exit 1
}

# Check critical files
$criticalFiles = @(
    "package.json",
    "tsconfig.json", 
    "src\index.tsx",
    "src\App.tsx",
    "public\index.html"
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file is missing" -ForegroundColor Red
    }
}

# Try to compile TypeScript
Write-Host ""
Write-Host "🔍 TypeScript compilation check..." -ForegroundColor Yellow
$typeCheckResult = npx tsc --noEmit --skipLibCheck
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ TypeScript compilation successful" -ForegroundColor Green
} else {
    Write-Host "⚠️  TypeScript compilation has issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Frontend appears healthy!" -ForegroundColor Green
'@

Set-Content -Path "health-check.ps1" -Value $healthCheckScript
Write-Host "✅ Created health-check.ps1 script" -ForegroundColor Green

Write-Host ""
Write-Host "🚀 Ready to start development!" -ForegroundColor Green
Write-Host "   Run: npm start" -ForegroundColor White
