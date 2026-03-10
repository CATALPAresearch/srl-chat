#!/bin/bash
# Development build script for SRL Chat frontend

echo "🚀 Building SRL Chat Frontend..."
echo "=================================="

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run development build
echo "🔨 Running development build..."
npm run dev

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo "📁 Output files are in: ../amd/build/"
    echo ""
    echo "🌐 You can now:"
    echo "   1. Run the standalone version at: http://localhost:5000/ (via lti_provider.py)"
    echo "   2. Test LTI integration at: http://localhost:5000/launch"
    echo "   3. Start the main API server: poetry run python api/main.py"
else
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi