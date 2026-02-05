import sys
from pathlib import Path

# Busca la raíz del proyecto (donde está la carpeta 'utils')
p = Path.cwd().resolve()
while p != p.parent and not (p / "utils").exists():
    p = p.parent

sys.path.insert(0, str(p))
