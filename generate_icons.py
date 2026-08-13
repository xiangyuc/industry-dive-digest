#!/usr/bin/env python3
"""
Generate minimalist letter-based flat icon assets for Industry Dive Daily:
- favicon.svg
- apple-touch-icon.png (180x180)
- icon-192.png (192x192)
- icon-512.png (512x512)
- favicon-32x32.png (32x32)
"""

import os
import zlib
import struct

def make_svg_icon():
    """Create a minimalist, flat, letter-based SVG icon with an 'ID' monogram on a deep slate squircle background."""
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>

  <!-- Flat Background Squircle -->
  <rect x="0" y="0" width="512" height="512" rx="112" ry="112" fill="url(#bgGrad)"/>
  
  <!-- Subtle Outer Rim Accent -->
  <rect x="8" y="8" width="496" height="496" rx="104" ry="104" fill="none" stroke="#ffffff" stroke-width="4" stroke-opacity="0.15"/>

  <!-- Minimalist Letter Monogram 'D' (Dive) with Accent Bar 'I' -->
  <g transform="translate(256, 256)" text-anchor="middle" dominant-baseline="central">
    <!-- Letter 'I' Pillar -->
    <rect x="-140" y="-120" width="44" height="240" rx="12" fill="#38bdf8"/>
    
    <!-- Letter 'D' Body -->
    <path d="M -60 -120 H 30 C 100 -120 150 -70 150 0 C 150 70 100 120 30 120 H -60 Z M -14 -72 V 72 H 30 C 70 72 102 42 102 0 C 102 -42 70 -72 30 -72 Z" fill="#ffffff"/>
    
    <!-- Coral Red Accent Dot -->
    <circle cx="130" cy="-100" r="22" fill="#f43f5e"/>
  </g>
</svg>'''
    return svg_content

def create_png(width, height, draw_func):
    """Create raw RGBA PNG image without external dependencies using zlib."""
    # RGBA image buffer (width * height * 4)
    pixels = bytearray(width * height * 4)
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = draw_func(x, y, width, height)
            idx = (y * width + x) * 4
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b
            pixels[idx+3] = a

    # PNG chunks building
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    # Raw scanlines with filter byte 0 (None)
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0) # Filter byte
        start = y * width * 4
        raw_data.extend(pixels[start:start + width * 4])

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0) # 8-bit RGBA
    idat = zlib.compress(bytes(raw_data), level=9)
    
    png_data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
    return png_data

def render_icon_pixel(x, y, w, h):
    """Draw smooth flat icon pixel (Squircle background + white/cyan letter 'D' & 'I')."""
    # Normalize coordinates to 0..1
    nx = (x / (w - 1)) * 2 - 1  # -1 to 1
    ny = (y / (h - 1)) * 2 - 1  # -1 to 1
    
    # Squircle radius (rounded rectangle formula: (|x/r|^p + |y/r|^p) <= 1)
    # Power 4.5 gives iOS style squircle
    corner_dist = (abs(nx) ** 3.5 + abs(ny) ** 3.5) ** (1 / 3.5)
    
    if corner_dist > 0.96:
        # Anti-aliased outer background margin
        if corner_dist > 0.98:
            return (0, 0, 0, 0) # Transparent
        else:
            alpha = int((0.98 - corner_dist) / 0.02 * 255)
            return (15, 23, 42, alpha)

    # Background gradient: #0284c7 (top left) to #0f172a (bottom right)
    t = (nx + ny + 2) / 4 # 0 to 1
    br = int(2 * (1 - t) + 15 * t)
    bg = int(132 * (1 - t) + 23 * t)
    bb = int(199 * (1 - t) + 42 * t)
    
    # Letter geometry matching 'I' and 'D'
    # Letter 'I' rect: nx in [-0.55, -0.38], ny in [-0.48, 0.48]
    is_i = (-0.55 <= nx <= -0.38) and (-0.48 <= ny <= 0.48)
    
    # Letter 'D' outer bounds
    # D left bar: nx in [-0.25, -0.06], ny in [-0.48, 0.48]
    is_d_bar = (-0.25 <= nx <= -0.06) and (-0.48 <= ny <= 0.48)
    
    # D curve
    dx = nx - (-0.06)
    dy = ny
    in_d_curve = False
    if dx >= 0 and abs(dy) <= 0.48:
        # Oval outer radius
        outer_r = (dx / 0.55)**2 + (dy / 0.48)**2
        inner_r = ((dx) / 0.36)**2 + (dy / 0.28)**2
        if outer_r <= 1.0 and inner_r >= 1.0:
            in_d_curve = True

    # Red dot at top right
    dot_dist = ((nx - 0.52)**2 + (ny - (-0.40))**2)**0.5
    is_dot = dot_dist <= 0.095

    if is_i:
        return (56, 189, 248, 255) # Cyan #38bdf8 for 'I'
    elif is_d_bar or in_d_curve:
        return (255, 255, 255, 255) # Pure White #ffffff for 'D'
    elif is_dot:
        return (244, 63, 94, 255) # Coral Red #f43f5e
    else:
        return (br, bg, bb, 255) # Background gradient

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    
    # Save SVG Icon
    svg_str = make_svg_icon()
    for d in [base_dir, docs_dir]:
        with open(os.path.join(d, 'favicon.svg'), 'w', encoding='utf-8') as f:
            f.write(svg_str)
            
    print("Generated favicon.svg")

    # Render PNG icons
    sizes = [
        ('apple-touch-icon.png', 180),
        ('icon-192.png', 192),
        ('icon-512.png', 512),
        ('favicon-32x32.png', 32),
        ('favicon-16x16.png', 16)
    ]
    
    for filename, sz in sizes:
        print(f"Rendering {filename} ({sz}x{sz})...")
        png_bytes = create_png(sz, sz, render_icon_pixel)
        for d in [base_dir, docs_dir]:
            with open(os.path.join(d, filename), 'wb') as f:
                f.write(png_bytes)
                
    print("All icon assets generated successfully!")

if __name__ == '__main__':
    main()
