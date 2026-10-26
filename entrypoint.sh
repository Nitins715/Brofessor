#!/bin/sh
set -e

# ==============================================================================
# Brofessor Local-First Single Container Startup Script
# ==============================================================================

# Ensure unified data directory and subfolders exist
DATA_DIR="${DATA_DIR:-/data}"
mkdir -p "$DATA_DIR/media" "$DATA_DIR/logs" "$DATA_DIR/cache/huggingface" "$DATA_DIR/cache/fastembed"

export DATA_DIR="$DATA_DIR"
export DOCKER_CONTAINER=1
export PYTHONUNBUFFERED=1

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Checking standard curriculum data..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.roadmap.models import Domain, LearningResource
from django.core.management import call_command
if Domain.objects.count() == 0:
    print('Fresh install detected. Seeding roadmap and initial assessment benchmarks...')
    call_command('seed_roadmap')
call_command('seed_domain_roadmaps')
if LearningResource.objects.count() == 0:
    print('Seeding verified learning resources...')
    try:
        call_command('import_learning_resources')
    except Exception as e:
        print(f'Learning resources seed warning: {e}')
"


# Display prominent startup banner with access URL and port
cat << "EOF"

================================================================================
   ____   ____   ____  ______ ______ _____ _____ ____  ____  
  |  _ \ |  _ \ / __ \|  ____|  ____/ ____/ ____/ __ \|  _ \ 
  | |_) || |_) | |  | | |__  | |__ | (___| (___| |  | | |_) |
  |  _ < |  _ <| |  | |  __| |  __| \___ \\___ \| |  | |  _ < 
  | |_) || | | | |__| | |    | |________) |___) | |__| | | \ \
  |____/ |_|  \_\\____/|_|    |______|_____/_____/ \____/|_|  \_\

  Brofessor: Personal Knowledge System (Local-First Edition)
================================================================================
  Status:         READY & RUNNING
  Access URL:     http://localhost:8000/
  Container Port: 8000
  Local Storage:  /data (Mapped to your host PC disk)
  Authentication: Single-User Local Workspace (No password required)
================================================================================
  To access from your browser, open:
  -> http://localhost:8000/
================================================================================

EOF

# Execute production Gunicorn server with multithreading support
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --timeout 180 \
    --access-logfile - \
    --error-logfile -
