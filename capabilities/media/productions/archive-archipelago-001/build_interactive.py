#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
web=ROOT/'interactive'
html=(web/'index.html').read_text(encoding='utf-8')
css=(web/'styles.css').read_text(encoding='utf-8')
data=(web/'data.js').read_text(encoding='utf-8')
app=(web/'app.js').read_text(encoding='utf-8')
html=html.replace('<link rel="stylesheet" href="styles.css" />', '<style>\n'+css+'\n</style>')
html=html.replace('<script src="data.js"></script><script src="app.js"></script>', '<script>\n'+data+'\n</script><script>\n'+app+'\n</script>')
out=web/'archive-archipelago-001.html'
out.write_text(html,encoding='utf-8')
print(out)
