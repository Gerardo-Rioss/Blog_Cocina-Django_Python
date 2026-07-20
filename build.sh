#!/usr/bin/env bash
# Script de build para Render
set -o errexit

echo "🌱 Instalando dependencias..."
pip install -r requirements.txt

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "🗄️  Aplicando migraciones..."
python manage.py migrate --noinput

echo "🌿 Verificando datos iniciales..."
python manage.py seed_data 2>&1 || echo "  ⚠️ Seed ya ejecutado (ignorar errores de duplicados)"

echo "✅ Build completado exitosamente"
