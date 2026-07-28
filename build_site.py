#!/usr/bin/env python3
import json
import re
import os
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
import concurrent.futures
from datetime import datetime
import html

def clean_html(raw_html):
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
    clean_text = html.unescape(clean_text)
    return re.sub(r'\s+', ' ', clean_text).strip()

def extract_image(raw_html):
    if not raw_html:
        return None
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)
    return match.group(1) if match else None

def fetch_feed(pub_info):
    name = pub_info['name']
    url = pub_info['url']
    feed_url = pub_info['feed']
    
    req = Request(feed_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
    try:
        with urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            channel = root.find('channel')
            if channel is None:
                return {'name': name, 'url': url, 'lead_story': None, 'top_stories': []}
            
            items = channel.findall('item')
            stories = []
            for item in items[:6]:
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pub_date_elem = item.find('pubDate')
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                desc_raw = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                
                summary = clean_html(desc_raw)
                image_url = extract_image(desc_raw)
                pub_date = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else ""
                
                if title and link:
                    stories.append({
                        'title': title,
                        'link': link,
                        'summary': summary[:220] + '...' if len(summary) > 220 else summary,
                        'image': image_url,
                        'date': pub_date
                    })
            
            lead_story = stories[0] if len(stories) > 0 else None
            top_stories = stories[1:6] if len(stories) > 1 else []
            
            return {
                'name': name,
                'url': url,
                'lead_story': lead_story,
                'top_stories': top_stories
            }
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return {'name': name, 'url': url, 'lead_story': None, 'top_stories': []}

def build_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pub_file = os.path.join(base_dir, 'publications.json')
    
    with open(pub_file, 'r', encoding='utf-8') as f:
        categories = json.load(f)
        
    all_pubs = []
    for cat in categories:
        for pub in cat['publications']:
            all_pubs.append(pub)
            
    print(f"Fetching RSS feeds for {len(all_pubs)} publications...")
    
    results_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_pub = {executor.submit(fetch_feed, pub): pub for pub in all_pubs}
        for future in concurrent.futures.as_completed(future_to_pub):
            pub = future_to_pub[future]
            try:
                data = future.result()
                results_map[pub['name']] = data
            except Exception as exc:
                print(f"{pub['name']} generated error: {exc}")
                results_map[pub['name']] = {'name': pub['name'], 'url': pub['url'], 'lead_story': None, 'top_stories': []}
                
    today_str = datetime.now().strftime('%B %d, %Y')
    
    categorized_digest = []
    total_stories = 0
    for cat in categories:
        cat_name = cat['category']
        cat_pubs = []
        for pub in cat['publications']:
            pub_data = results_map.get(pub['name'])
            if pub_data and (pub_data['lead_story'] or pub_data['top_stories']):
                cat_pubs.append(pub_data)
                if pub_data['lead_story']: total_stories += 1
                total_stories += len(pub_data['top_stories'])
        if cat_pubs:
            categorized_digest.append({
                'category': cat_name,
                'publications': cat_pubs
            })
            
    return {
        'date': today_str,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_stories': total_stories,
        'categories': categorized_digest
    }

def render_webapp(data):
    """Render a mobile PWA HTML app with enlarged typography and comfortable tap targets."""
    data_json_str = json.dumps(data)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Industry Dive Daily - Executive Briefing</title>
    
    <!-- PWA & Mobile Icons -->
    <meta name="theme-color" content="#f8fafc" media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <link rel="apple-touch-icon" href="https://www.industrydive.com/static/site/images/favicon.ico">
    
    <!-- Google Fonts & Icons -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            /* Light Theme Defaults */
            --bg-main: #f8fafc;
            --bg-header: rgba(255, 255, 255, 0.95);
            --bg-card: #ffffff;
            --bg-lead: #f1f5f9;
            --accent-blue: #0284c7;
            --accent-rose: #e11d48;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --text-title: #0f172a;
            --text-link: #0f172a;
            --text-story: #1e293b;
            --border-color: #e2e8f0;
            --chip-bg: #f1f5f9;
            --chip-text: #334155;
            --chip-active-bg: #0284c7;
            --chip-active-text: #ffffff;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }}
        
        @media (prefers-color-scheme: dark) {{
            :root {{
                /* Dark Theme Overrides */
                --bg-main: #0f172a;
                --bg-header: rgba(15, 23, 42, 0.95);
                --bg-card: #1e293b;
                --bg-lead: linear-gradient(180deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
                --accent-blue: #38bdf8;
                --accent-rose: #f43f5e;
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --text-title: #ffffff;
                --text-link: #f8fafc;
                --text-story: #e2e8f0;
                --border-color: #334155;
                --chip-bg: #1e293b;
                --chip-text: #cbd5e1;
                --chip-active-bg: #38bdf8;
                --chip-active-text: #0f172a;
                --shadow: 0 4px 12px rgba(0,0,0,0.2);
            }}
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}
        
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            padding-bottom: 50px;
            line-height: 1.55;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        
        /* App Header with Smooth Hide/Show Transition */
        header {{
            position: sticky;
            top: 0;
            z-index: 100;
            background-color: var(--bg-header);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 16px;
            transition: transform 0.3s ease, opacity 0.3s ease;
            transform: translateY(0);
            opacity: 1;
        }}
        
        header.header-hidden {{
            transform: translateY(-100%);
            opacity: 0;
            pointer-events: none;
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .brand {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .brand-badge {{
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            padding: 4px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .brand-title {{
            font-size: 19px;
            font-weight: 800;
            letter-spacing: -0.3px;
            color: var(--text-title);
        }}
        
        .date-badge {{
            font-size: 13px;
            color: var(--text-muted);
            font-weight: 600;
        }}
        
        /* Category Chips Slider with Touch-Friendly Sizing */
        .chips-scroll {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
            padding-bottom: 2px;
        }}
        
        .chips-scroll::-webkit-scrollbar {{
            display: none;
        }}
        
        .chip {{
            white-space: nowrap;
            background-color: var(--chip-bg);
            border: 1px solid var(--border-color);
            color: var(--chip-text);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .chip.active, .chip:hover {{
            background-color: var(--chip-active-bg);
            color: var(--chip-active-text);
            border-color: var(--chip-active-bg);
        }}
        
        /* Main Layout */
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 18px 16px;
        }}
        
        .category-section {{
            margin-bottom: 32px;
        }}
        
        .category-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--border-color);
        }}
        
        .category-title {{
            font-size: 20px;
            font-weight: 800;
            color: var(--text-title);
        }}
        
        .pubs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
            gap: 16px;
        }}
        
        /* Publication Card */
        .pub-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: var(--shadow);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        
        .pub-card:hover {{
            border-color: var(--accent-blue);
        }}
        
        .pub-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .pub-name {{
            font-size: 18.5px;
            font-weight: 800;
            color: var(--text-title);
            text-decoration: none;
            padding: 2px 0;
            transition: color 0.2s;
        }}
        
        .pub-name:hover {{
            color: var(--accent-blue);
        }}
        
        .pub-domain {{
            font-size: 11.5px;
            font-weight: 600;
            color: var(--text-muted);
            background-color: var(--chip-bg);
            padding: 3px 8px;
            border-radius: 10px;
        }}
        
        /* Lead Story */
        .lead-card {{
            background: var(--bg-lead);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            padding: 12px;
        }}
        
        .lead-badge {{
            display: inline-block;
            background-color: var(--accent-rose);
            color: #ffffff;
            font-size: 10.5px;
            font-weight: 800;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 4px;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }}
        
        .lead-img {{
            width: 100%;
            max-height: 200px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        
        .lead-title {{
            font-size: 16.5px;
            font-weight: 700;
            color: var(--text-link);
            text-decoration: none;
            line-height: 1.4;
            display: block;
            margin-bottom: 6px;
            padding: 2px 0;
        }}
        
        .lead-title:hover {{
            color: var(--accent-blue);
        }}
        
        .lead-summary {{
            font-size: 13.5px;
            color: var(--text-muted);
            line-height: 1.5;
        }}
        
        /* Top Stories List - Enlarged Touch Targets */
        .top-stories-title {{
            font-size: 13px;
            font-weight: 800;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
        }}
        
        .story-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .story-item {{
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }}
        
        .story-bullet {{
            color: var(--accent-blue);
            font-weight: 800;
            font-size: 16px;
            line-height: 1.4;
        }}
        
        .story-link {{
            font-size: 15px;
            font-weight: 600;
            color: var(--text-story);
            text-decoration: none;
            line-height: 1.45;
            padding: 3px 0;
            display: block;
            transition: color 0.2s ease;
        }}
        
        .story-link:hover {{
            color: var(--accent-blue);
        }}
    </style>
</head>
<body>

    <header id="appHeader">
        <div class="header-top">
            <div class="brand">
                <span class="brand-badge">Daily Brief</span>
                <span class="brand-title">Industry Dive</span>
            </div>
            <div class="date-badge" id="dateBadge">{data['date']}</div>
        </div>
        
        <div class="chips-scroll" id="categoryChips">
            <div class="chip active" data-category="ALL">All Categories</div>
        </div>
    </header>

    <main class="container" id="mainContainer">
        <!-- Rendered via JS -->
    </main>

    <script>
        const APP_DATA = {data_json_str};
        let currentCategory = 'ALL';

        function initApp() {{
            renderChips();
            renderContent();
            setupScrollHide();
        }}

        function setupScrollHide() {{
            let lastScrollY = window.scrollY;
            const header = document.getElementById('appHeader');
            
            window.addEventListener('scroll', () => {{
                const currentScrollY = window.scrollY;
                if (currentScrollY > lastScrollY && currentScrollY > 50) {{
                    // Hide header when scrolling down
                    header.classList.add('header-hidden');
                }} else if (currentScrollY < lastScrollY) {{
                    // Show header when scrolling up
                    header.classList.remove('header-hidden');
                }}
                lastScrollY = currentScrollY;
            }}, {{ passive: true }});
        }}

        function renderChips() {{
            const container = document.getElementById('categoryChips');
            const chips = ['<div class="chip active" data-category="ALL">All Categories</div>'];
            
            APP_DATA.categories.forEach(cat => {{
                chips.push(`<div class="chip" data-category="${{cat.category}}">${{cat.category}}</div>`);
            }});
            
            container.innerHTML = chips.join('');
            
            container.querySelectorAll('.chip').forEach(chip => {{
                chip.addEventListener('click', () => {{
                    container.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                    chip.classList.add('active');
                    currentCategory = chip.getAttribute('data-category');
                    renderContent();
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                }});
            }});
        }}

        function renderContent() {{
            const main = document.getElementById('mainContainer');
            let html = [];
            
            let filteredCats = APP_DATA.categories.filter(cat => {{
                if (currentCategory !== 'ALL' && cat.category !== currentCategory) return false;
                return true;
            }});

            filteredCats.forEach(cat => {{
                html.push(`
                    <section class="category-section">
                        <div class="category-header">
                            <h2 class="category-title">${{cat.category}}</h2>
                        </div>
                        <div class="pubs-grid">
                `);

                cat.publications.forEach(pub => {{
                    let leadHtml = '';
                    if (pub.lead_story) {{
                        const imgTag = pub.lead_story.image ? `<img src="${{pub.lead_story.image}}" class="lead-img" alt="Story" />` : '';
                        leadHtml = `
                            <div class="lead-card">
                                <span class="lead-badge">Lead Story</span>
                                ${{imgTag}}
                                <a href="${{pub.lead_story.link}}" target="_blank" class="lead-title">${{pub.lead_story.title}}</a>
                                <div class="lead-summary">${{pub.lead_story.summary}}</div>
                            </div>
                        `;
                    }}

                    let topStoriesHtml = '';
                    if (pub.top_stories && pub.top_stories.length > 0) {{
                        const items = pub.top_stories.map(item => `
                            <li class="story-item">
                                <span class="story-bullet">•</span>
                                <a href="${{item.link}}" target="_blank" class="story-link">${{item.title}}</a>
                            </li>
                        `).join('');

                        topStoriesHtml = `
                            <div>
                                <div class="top-stories-title">Top 5 Stories</div>
                                <ul class="story-list" style="margin-top: 8px;">
                                    ${{items}}
                                </ul>
                            </div>
                        `;
                    }}

                    html.push(`
                        <div class="pub-card">
                            <div class="pub-header">
                                <a href="${{pub.url}}" target="_blank" class="pub-name">${{pub.name}}</a>
                                <span class="pub-domain">${{pub.name.toLowerCase().replace(/\\s+/g, '')}}</span>
                            </div>
                            ${{leadHtml}}
                            ${{topStoriesHtml}}
                        </div>
                    `);
                }});

                html.push(`
                        </div>
                    </section>
                `);
            }});

            main.innerHTML = html.join('');
        }}

        document.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>
'''
    return html_content

def main():
    data = build_data()
    html_content = render_webapp(data)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Save JSON data
    data_path = os.path.join(base_dir, 'data.json')
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    # Save index.html for root and docs/ (for GitHub Pages compatibility)
    index_path = os.path.join(base_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    docs_dir = os.path.join(base_dir, 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    docs_index_path = os.path.join(docs_dir, 'index.html')
    with open(docs_index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Successfully generated Web App for {data['date']}!")
    print(f"Main index file saved to: {index_path}")
    print(f"GitHub Pages docs file saved to: {docs_index_path}")

if __name__ == '__main__':
    main()
