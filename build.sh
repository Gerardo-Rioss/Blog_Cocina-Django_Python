#!/usr/bin/env bash
# Script de build para Render
set -o errexit

echo "🌱 Instalando dependencias..."
pip install -r requirements.txt

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Copiar imagenes de media/ a staticfiles/ para que WhiteNoise las sirva
echo "🖼️  Copiando imagenes a staticfiles/..."
mkdir -p staticfiles/media/articulos
cp -r media/articulos/*.jpg staticfiles/media/articulos/ 2>/dev/null || true
cp -r media/*.png staticfiles/media/ 2>/dev/null || true
echo "  ✅ $(ls staticfiles/media/articulos/*.jpg 2>/dev/null | wc -l) imagenes copiadas"

echo "🗄️  Aplicando migraciones..."
python manage.py migrate --noinput

echo "🌿 Poblando datos de prueba..."
python manage.py seed_data

echo "🖼️  Forzando imagenes Unsplash reales..."
python manage.py fix_images

echo "✅ Build completado exitosamente"
