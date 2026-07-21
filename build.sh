#!/usr/bin/env bash
# Script de build para Render
set -o errexit

echo "🌱 Instalando dependencias..."
pip install -r requirements.txt

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "🗄️  Aplicando migraciones..."
python manage.py migrate --noinput

echo "♻️  Reseteando datos para asegurar imagenes correctas..."
python manage.py shell -c "
from apps.articulos.models import Articulo, Comentario
from apps.contacto.models import Contacto
Comentario.objects.all().delete()
Articulo.objects.all().delete()
Contacto.objects.all().delete()
print('✅ Datos viejos eliminados')
"

echo "🌿 Poblando datos de prueba con imagenes Unsplash..."
python manage.py seed_data

echo "✅ Build completado exitosamente"
