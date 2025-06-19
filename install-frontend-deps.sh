#!/bin/bash

# Frontend Dependencies Installation Script

echo "🚀 Installing SchemaSage Frontend Dependencies..."

cd frontend

# Core dependencies
echo "📦 Installing core dependencies..."
npm install framer-motion
npm install @radix-ui/react-dialog
npm install @radix-ui/react-dropdown-menu
npm install @radix-ui/react-tabs
npm install @radix-ui/react-toast
npm install @radix-ui/react-tooltip
npm install class-variance-authority
npm install clsx
npm install tailwind-merge

# Development dependencies
echo "🛠️ Installing development dependencies..."
npm install -D @types/react
npm install -D @types/react-dom
npm install -D autoprefixer
npm install -D postcss
npm install -D tailwindcss

echo "✅ All dependencies installed successfully!"
echo "🎨 Your frontend is now ready for stunning animations and interactions!"

# Optional: Update package.json scripts
echo "📝 Consider adding these scripts to your package.json:"
echo "  \"dev\": \"next dev\""
echo "  \"build\": \"next build\""
echo "  \"start\": \"next start\""
echo "  \"lint\": \"next lint\""
