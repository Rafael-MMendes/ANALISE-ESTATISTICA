file_path = "d:\\Nova pasta\\Dashboard - Antigravity\\app.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False

for i in range(len(lines)):
    line = lines[i]

    # Swap header info
    if '<div style="color: rgba(255,255,255,0.65); font-size: 0.72rem; font-weight: 400; text-align: right;">' in line and \
       "Created By 2&#186;" in lines[i+1]:
        new_lines.append('                <div style="color: rgba(255,255,255,0.80); font-size: 0.75rem; font-weight: 500; text-align: right; margin-top: 2px;">\n')
        new_lines.append('                    Fonte de Dados: NEAC / CAD / Pentaho\n')
        new_lines.append('                </div>\n')
        new_lines.append('                <div style="color: rgba(255,255,255,0.80); font-size: 0.75rem; font-weight: 500; text-align: right; margin-top: 2px;">\n')
        new_lines.append('                    Created By 2&#186; Sgt PM Monteiro e 3&#186; Sgt PM Alan Kleber\n')
        new_lines.append('                </div>\n')
        skip = True # skip the next few lines
        continue

    # How many lines to skip for the old header?
    if skip:
        # If we reached the end of the previous `</div>` after Fonte de dados, we stop skipping
        # we know there are 6 lines to skip total
        pass # we'll implement skip by checking exact strings to make it robust

    # Remove "ANO DE REFERÊNCIA" from the sidebar
    if '<div style="color: #64748B; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;' in line and \
       'ANO DE REFERÊNCIA' in lines[i+2]:
        # we are at `<div style="color: #64...`
        pass

    new_lines.append(line)

# Let me use a more precise string replacement logic for the second time
