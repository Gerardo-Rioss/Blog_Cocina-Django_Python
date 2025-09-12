# Blog de Cocina - Django & Python  

**Proyecto final del curso de Desarrollo Web en El Informatorio**. Un blog interactivo sobre gastronomía con gestión de roles, permisos avanzados y contenido dinámico.  

## 🎯 Objetivo  
Crear una plataforma segura y colaborativa donde los usuarios compartan recetas, interactúen y gestionen contenido según sus roles.  

## 🚀 Características  
### 🔹 Gestión de Usuarios y Permisos  
- **Tres roles jerárquicos**:  
  | Rol | Permisos |  
  |---|---|  
  | **Usuario Registrado** | Comentar + eliminar *sus comentarios*. |  
  | **Colaborador** | Publicar/editar *sus artículos* + eliminar *sus publicaciones*. |  
  | **Administrador** | CRUD completo (usuarios, posts, comentarios). |  

### 🔹 Sistema de Contenido  
- **Publicación de recetas**:  
  - Formularios con campos para título, ingredientes, pasos, imagen y categoría.  
- **Organización**:  
  - Categorías predefinidas (ej: "Cena Rápida", "Recetas Saludables").  
  - Búsqueda por título o ingrediente.  

### 🔹 Interacción Comunitaria  
- **Comentarios**:  
  - Hilos anidados en cada receta.  
  - Notificaciones de respuestas (integración con Django Signals).  
- **Perfil de usuario**:  
  - Historial de publicaciones y comentarios.  
  - Avatar personalizable.  

## 🛠️ Tecnologías  
- **Backend**: Django 4.2+ (Python 3.10+)  
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)  
- **Extras**:  
  - Pillow (manejo de imágenes).  
  
## 📊 Vista previa 
        
<img width="1193" height="608" alt="Blog1" src="https://github.com/user-attachments/assets/1375a75b-dcda-4162-87d3-608b4ba16ebe" />
<img width="1009" height="519" alt="Blog5" src="https://github.com/user-attachments/assets/9e0cdc14-c308-40dd-b597-e7ce8eea5d4c" />
<img width="1014" height="550" alt="Blog3" src="https://github.com/user-attachments/assets/f0391574-042b-48b0-bb9b-37692b24151c" />
<img width="1084" height="542" alt="Blog2" src="https://github.com/user-attachments/assets/40f96624-2a0d-4f7d-8221-18e7df9503b9" />
