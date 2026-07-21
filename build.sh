#!/usr/bin/env bash
# Script de build para Render
set -o errexit

echo "🌱 Instalando dependencias..."
pip install -r requirements.txt

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "🗄️  Aplicando migraciones..."
python manage.py migrate --noinput

echo "🌿 Poblando datos de prueba..."
python manage.py seed_data

echo "🖼️  Forzando imagenes Unsplash reales..."
python manage.py fix_images

echo "✅ Build completado exitosamente"
