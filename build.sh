#!/usr/bin/env bash
# Script de build para Render
# Render ejecuta esto en la fase de build

set -o errexit

echo "🌱 Instalando dependencias..."
pip install -r requirements.txt

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "🗄️  Aplicando migraciones..."
python manage.py migrate --noinput

echo "🌿 Poblando datos iniciales (seed)..."
python manage.py seed_data --noinput 2>/dev/null || echo "  ℹ️  Seed ya ejecutado o datos existentes"

echo "✅ Build completado exitosamente"
