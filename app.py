import io
import os
import sys
import zipfile
from pathlib import Path

ARCHIVE = Path(__file__).with_name('TJ_AmeriTrade_V6.zip')
EXTRACT_DIR = Path('/tmp/tj_ameritrade_app')

if not EXTRACT_DIR.exists():
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, 'r') as zf:
        zf.extractall(EXTRACT_DIR)

app_path = EXTRACT_DIR / 'TJ_AmeriTrade_V6' / 'app.py'
if not app_path.exists():
    raise FileNotFoundError(f'Could not find extracted app at {app_path}')

os.chdir(app_path.parent)
sys.path.insert(0, str(app_path.parent))
code = compile(app_path.read_text(encoding='utf-8'), str(app_path), 'exec')
exec(code, {'__name__': '__main__', '__file__': str(app_path)})
