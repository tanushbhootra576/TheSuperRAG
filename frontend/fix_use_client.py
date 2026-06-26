import os

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '"use client"' in content or "'use client'" in content:
        return
        
    needs_client = any(keyword in content for keyword in [
        'useState', 'useEffect', 'useRef', 'useCallback', 'useContext', 
        'useVirtualizer', 'useSidebarStore', 'useUploadStore', 
        'useBreakpoint', 'useMediaQuery'
    ])
    
    if needs_client:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('"use client";\n' + content)
        print(f'Added use client to {filepath}')

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            if file == 'layout.tsx' or file == 'page.tsx':
                continue
            process_file(os.path.join(root, file))
