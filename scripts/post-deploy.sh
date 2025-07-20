#!/bin/bash

# Post-deployment script for DigitalOcean App Platform
# This script runs after the main deployment to ensure everything is set up correctly

set -e

echo "🚀 Starting post-deployment setup..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Collect static files (Django admin CSS, etc.)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Create cache table if using database cache
echo "💾 Setting up cache..."
python manage.py createcachetable || echo "Cache table already exists or not needed"

# Check Django deployment readiness
echo "🔍 Running deployment checks..."
python manage.py check --deploy

echo "✅ Post-deployment setup completed successfully!"
echo "🌐 Your Tavonga API is ready at: https://jellyfish-app-ho48c.ondigitalocean.app/"
echo "👤 Admin interface: https://jellyfish-app-ho48c.ondigitalocean.app/admin/"
echo "📚 API docs: https://jellyfish-app-ho48c.ondigitalocean.app/swagger/" 