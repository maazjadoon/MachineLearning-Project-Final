#!/bin/bash

# Cyber Sentinel ML - Frontend Setup Script
# Enterprise-grade React application setup

echo "🚀 Setting up Cyber Sentinel ML Frontend..."
echo "================================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_VERSION="16.0.0"

if ! node -e "process.exit(require('semver').gte('$NODE_VERSION', '$REQUIRED_VERSION') ? 0 : 1)" 2>/dev/null; then
    echo "❌ Node.js version $NODE_VERSION is too old. Please install Node.js $REQUIRED_VERSION or higher."
    exit 1
fi

echo "✅ Node.js version: $NODE_VERSION"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ npm version: $(npm -v)"

# Clean up any existing node_modules and package-lock.json
echo "🧹 Cleaning up existing dependencies..."
if [ -d "node_modules" ]; then
    rm -rf node_modules
    echo "  - Removed node_modules"
fi

if [ -f "package-lock.json" ]; then
    rm -f package-lock.json
    echo "  - Removed package-lock.json"
fi

# Install dependencies
echo "📦 Installing dependencies..."
echo "This may take a few minutes..."

npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Verify TypeScript configuration
echo "🔧 Verifying TypeScript configuration..."
if [ ! -f "tsconfig.json" ]; then
    echo "❌ tsconfig.json not found"
    exit 1
fi

# Run TypeScript type check
echo "🔍 Running TypeScript type check..."
npx tsc --noEmit

if [ $? -ne 0 ]; then
    echo "⚠️  TypeScript has some type errors, but dependencies are installed"
    echo "   You can fix these by running: npm run lint:fix"
else
    echo "✅ TypeScript compilation successful"
fi

# Check if all critical dependencies are available
echo "🔍 Verifying critical dependencies..."

CRITICAL_DEPS=(
    "react"
    "react-dom"
    "antd"
    "@ant-design/icons"
    "react-router-dom"
    "axios"
    "socket.io-client"
    "react-query"
    "zustand"
    "typescript"
)

for dep in "${CRITICAL_DEPS[@]}"; do
    if [ -d "node_modules/$dep" ]; then
        echo "✅ $dep"
    else
        echo "❌ $dep is missing"
    fi
done

echo ""
echo "🎉 Frontend setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start development server: npm start"
echo "2. Build for production: npm run build"
echo "3. Run tests: npm test"
echo "4. Fix linting: npm run lint:fix"
echo ""
echo "🌐 Development server will be available at: http://localhost:3000"
echo "📊 API proxy configured to: http://localhost:8000"
echo ""
echo "🔧 Useful commands:"
echo "- npm run lint        - Check code quality"
echo "- npm run lint:fix    - Fix linting issues"
echo "- npm run type-check  - Verify TypeScript types"
echo "- npm run format      - Format code with Prettier"
echo "- npm run analyze     - Analyze bundle size"
echo ""

# Create a simple health check script
cat > health-check.sh << 'EOF'
#!/bin/bash

echo "🏥 Cyber Sentinel ML Frontend Health Check"
echo "=========================================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found - run setup.sh first"
    exit 1
fi

# Check critical files
CRITICAL_FILES=(
    "package.json"
    "tsconfig.json"
    "src/index.tsx"
    "src/App.tsx"
    "public/index.html"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file is missing"
    fi
done

# Try to compile TypeScript
echo ""
echo "🔍 TypeScript compilation check..."
npx tsc --noEmit --skipLibCheck

if [ $? -eq 0 ]; then
    echo "✅ TypeScript compilation successful"
else
    echo "⚠️  TypeScript compilation has issues"
fi

echo ""
echo "🎯 Frontend appears healthy!"
EOF

chmod +x health-check.sh
echo "✅ Created health-check.sh script"

echo ""
echo "🚀 Ready to start development!"
echo "   Run: npm start"
