import re
import subprocess
import sys

PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', 'Posible clave AWS'),
    (r'gh[pousr]_[A-Za-z0-9_]{20,}', 'Posible token GitHub'),
    (r'sk-[A-Za-z0-9_-]{20,}', 'Posible API key'),
    (r'(?i)(api[_-]?key|secret|password|passwd|credential)\s*[:=]\s*["\'][^"\']{8,}["\']',
     'Posible credencial incrustada'),
]

result = subprocess.run(
    ['git', 'diff', '--cached', '--no-ext-diff', '--unified=0'],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

text = '\n'.join(
    line[1:] for line in result.stdout.splitlines()
    if line.startswith('+') and not line.startswith('+++')
)

alerts = [name for pattern, name in PATTERNS if re.search(pattern, text)]

if alerts:
    print('\n*** OPERACION BLOQUEADA ***')
    print('Se detecto informacion potencialmente sensible:')
    for alert in sorted(set(alerts)):
        print(' -', alert)
    print('\nRevise los archivos antes de hacer commit.')
    sys.exit(1)

print('SEGURIDAD OK: no se detectaron secretos en los cambios preparados.')
sys.exit(0)
