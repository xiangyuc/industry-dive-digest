#!/usr/bin/env python3
import json
import re
import os
import sys
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import concurrent.futures
from datetime import datetime
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def clean_html(raw_html):
    """Remove HTML tags and clean whitespace."""
    if not raw_html:
        return ""
    # Extract text content
    clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
    clean_text = html.unescape(clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def extract_image(raw_html):
    """Extract thumbnail image URL from RSS description if present."""
    if not raw_html:
        return None
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)
    if match:
        return match.group(1)
    return None

def fetch_feed(pub_info):
    """Fetch RSS feed for a single publication."""
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
        print(f"Error fetching feed for {name} ({feed_url}): {e}")
        return {'name': name, 'url': url, 'lead_story': None, 'top_stories': []}

def build_digest():
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
                print(f"{pub['name']} generated an exception: {exc}")
                results_map[pub['name']] = {'name': pub['name'], 'url': pub['url'], 'lead_story': None, 'top_stories': []}
                
    # Build categorized report
    today_str = datetime.now().strftime('%B %d, %Y')
    
    categorized_digest = []
    for cat in categories:
        cat_name = cat['category']
        cat_pubs = []
        for pub in cat['publications']:
            pub_data = results_map.get(pub['name'])
            if pub_data and (pub_data['lead_story'] or pub_data['top_stories']):
                cat_pubs.append(pub_data)
        if cat_pubs:
            categorized_digest.append({
                'category': cat_name,
                'publications': cat_pubs
            })
            
    return categorized_digest, today_str

def render_email_html(categorized_digest, date_str):
    """Render a mobile-friendly, beautiful HTML email template."""
    
    # Generate Table of Contents / Category Quick Links
    category_nav_items = []
    for idx, cat in enumerate(categorized_digest):
        cat_id = f"cat-{idx}"
        category_nav_items.append(f'<a href="#{cat_id}" style="display: inline-block; background-color: #f1f5f9; color: #1e293b; font-size: 12px; font-weight: 600; padding: 6px 12px; margin: 3px 2px; border-radius: 16px; text-decoration: none;">{cat["category"]}</a>')
    
    category_nav_html = "".join(category_nav_items)
    
    cat_blocks = []
    for idx, cat in enumerate(categorized_digest):
        cat_id = f"cat-{idx}"
        pub_cards = []
        for pub in cat['publications']:
            lead = pub['lead_story']
            top_list = pub['top_stories']
            
            lead_html = ""
            if lead:
                img_html = f'<img src="{lead["image"]}" style="width: 100%; max-width: 520px; height: auto; border-radius: 8px; margin-bottom: 10px; display: block;" alt="Story Image" />' if lead['image'] else ""
                lead_html = f'''
                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                    <div style="font-size: 11px; font-weight: 700; color: #e11d48; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">★ Lead Story</div>
                    {img_html}
                    <a href="{lead['link']}" style="font-size: 16px; font-weight: 700; color: #0f172a; text-decoration: none; line-height: 1.35; display: block; margin-bottom: 6px;" target="_blank">{lead['title']}</a>
                    <div style="font-size: 13px; color: #475569; line-height: 1.45; margin-bottom: 6px;">{lead['summary']}</div>
                </div>
                '''
            
            top_stories_html = ""
            if top_list:
                items_html = []
                for item in top_list:
                    items_html.append(f'''
                    <li style="margin-bottom: 8px; line-height: 1.4;">
                        <a href="{item['link']}" style="font-size: 14px; font-weight: 600; color: #2563eb; text-decoration: none;" target="_blank">{item['title']}</a>
                    </li>
                    ''')
                top_stories_html = f'''
                <div style="padding-left: 4px;">
                    <div style="font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 6px;">Top News</div>
                    <ul style="margin: 0; padding-left: 18px; color: #334155;">
                        {"".join(items_html)}
                    </ul>
                </div>
                '''
                
            pub_cards.append(f'''
            <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <a href="{pub['url']}" style="font-size: 18px; font-weight: 800; color: #0f172a; text-decoration: none;" target="_blank">{pub['name']}</a>
                    <span style="font-size: 11px; color: #64748b;">industrydive.com</span>
                </div>
                {lead_html}
                {top_stories_html}
            </div>
            ''')
            
        cat_blocks.append(f'''
        <div id="{cat_id}" style="margin-top: 24px; margin-bottom: 30px;">
            <div style="border-bottom: 2px solid #cbd5e1; padding-bottom: 6px; margin-bottom: 14px;">
                <h2 style="font-size: 20px; font-weight: 800; color: #0f172a; margin: 0;">{cat['category']}</h2>
            </div>
            {"".join(pub_cards)}
        </div>
        ''')
        
    full_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Industry Dive Morning Digest - {date_str}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f1f5f9; padding: 16px 8px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); overflow: hidden; padding: 20px;">
                    <!-- Header -->
                    <tr>
                        <td style="padding-bottom: 16px; border-bottom: 1px solid #e2e8f0;">
                            <div style="font-size: 12px; font-weight: 700; color: #0284c7; text-transform: uppercase; letter-spacing: 1px;">Daily Executive Briefing</div>
                            <h1 style="font-size: 24px; font-weight: 900; color: #0f172a; margin: 4px 0 2px 0;">Industry Dive Top Stories</h1>
                            <div style="font-size: 13px; color: #64748b;">{date_str} • 35+ Publications Summary</div>
                        </td>
                    </tr>
                    
                    <!-- Quick Navigation -->
                    <tr>
                        <td style="padding: 14px 0; border-bottom: 1px solid #f1f5f9;">
                            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 6px;">Jump to Category:</div>
                            {category_nav_html}
                        </td>
                    </tr>
                    
                    <!-- Content Categories -->
                    <tr>
                        <td>
                            {"".join(cat_blocks)}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                            Automated Morning Digest powered by GitHub Actions & Industry Dive RSS.<br/>
                            Delivered daily to your phone.
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''
    return full_html

def send_email(html_content, date_str):
    """Send email via SMTP or Resend API if environment variables are provided."""
    to_email = os.environ.get('TO_EMAIL')
    if not to_email:
        print("TO_EMAIL environment variable not set. Skipping email dispatch (saved to file).")
        return
        
    subject = f"Industry Dive Morning Digest - {date_str}"
    from_email = os.environ.get('FROM_EMAIL', to_email)
    
    # Check for Resend API Key first
    resend_key = os.environ.get('RESEND_API_KEY')
    if resend_key:
        print(f"Sending email via Resend API to {to_email}...")
        try:
            req_data = json.dumps({
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }).encode('utf-8')
            req = Request("https://api.resend.com/emails", data=req_data, headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            })
            with urlopen(req) as resp:
                print(f"Email sent successfully via Resend: {resp.status}")
                return
        except Exception as e:
            print(f"Failed to send via Resend API: {e}")
            
    # Fallback to standard SMTP
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    
    if smtp_host and smtp_user and smtp_pass:
        print(f"Sending email via SMTP ({smtp_host}) to {to_email}...")
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [to_email], msg.as_string())
            print("Email sent successfully via SMTP.")
        except Exception as e:
            print(f"Failed to send via SMTP: {e}")
    else:
        print("No SMTP or Resend credentials provided. Email body was saved locally.")

def main():
    digest_data, date_str = build_digest()
    html_content = render_email_html(digest_data, date_str)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    preview_path = os.path.join(base_dir, 'digest_preview.html')
    with open(preview_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Successfully generated digest for {date_str}!")
    print(f"Local preview saved to: {preview_path}")
    
    send_email(html_content, date_str)

if __name__ == '__main__':
    main()
