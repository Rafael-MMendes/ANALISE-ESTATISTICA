with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re
matches = re.findall(r'(<h2.*?>.*?</h2>|<h3.*?>.*?</h3>|st\.markdown\("###.*?"\)|st\.markdown\(f"###.*?"\))', text)
for m in set(matches):
    print(m)
