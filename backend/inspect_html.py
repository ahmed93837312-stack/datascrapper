from bs4 import BeautifulSoup
with open('debug_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
print('--- ALL ANCHORS IN RESULTS ---')
for a in soup.find_all('a'):
    href = a.get('href', '')
    if 'maps/place' in href or 'maps/dir' in href or 'gym' in href.lower():
        cl = ' '.join(a.get('class', []))
        print(f"text: {a.text.strip()[:30]} | href: {href[:50]} | class: {cl}")
