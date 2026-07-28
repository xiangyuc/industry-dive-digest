# Industry Dive Daily Mobile Web App 📱

An automated, cloud-hosted executive news dashboard that aggregates the **lead story** (with thumbnail image & summary) and **top 5 news articles** from all 35+ [Industry Dive](https://www.industrydive.com/publications) publications every morning.

---

## 🌟 Key Features

- **35+ Publications Aggregated**: Covers Banking Dive, CIO Dive, BioPharma Dive, Retail Dive, Construction Dive, Utility Dive, Supply Chain Dive, and more.
- **7 Categorized Sectors**: Filter instantaneously by:
  1. *Finance & Executive*
  2. *Technology & Cybersecurity*
  3. *Healthcare & Life Sciences*
  4. *Retail, Food & Consumer*
  5. *Industrial, Supply Chain & Transport*
  6. *Real Estate & Built Environment*
  7. *Energy, ESG & Education*
- **Instant Search & Filter**: Real-time search bar to search any publication name or article headline.
- **Lead Story + Top 5 Stories**: Displays the featured lead story + 5 top articles per publication.
- **PWA & Mobile-First Design**: Add to iPhone / Android Home Screen for a native app feel.
- **100% Cloud-Automated**: Updated every morning automatically via GitHub Actions (Zero hosting cost).

---

## 🚀 Setup & Deployment Guide (GitHub Pages)

### Step 1: Create a GitHub Repository
1. Initialize and push this code to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Industry Dive Daily Web App"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/industry-dive-app.git
   git push -u origin main
   ```

---

### Step 2: Enable GitHub Pages
1. Go to your GitHub repository -> **Settings** -> **Pages**.
2. Under **Build and deployment**:
   - **Source**: Select `Deploy from a branch`.
   - **Branch**: Select `main` branch and `/docs` directory (or `/root`).
3. Click **Save**.
4. Your Web App will now be live at:
   `https://<YOUR_USERNAME>.github.io/industry-dive-app/`

---

### Step 3: Add to Phone Home Screen (Mobile PWA)
1. Open `https://<YOUR_USERNAME>.github.io/industry-dive-app/` on your phone browser.
2. **iPhone (Safari)**: Tap the Share button -> **Add to Home Screen**.
3. **Android (Chrome)**: Tap the 3 dots menu -> **Add to Home screen** / **Install app**.
4. Now you can tap the icon on your home screen every morning to view all top stories in one place!

---

## 🧪 Local Testing & Building

To generate and test the web app locally on your computer:
```bash
python3 build_site.py
```
Open `index.html` or `docs/index.html` in any web browser to view the interactive dashboard.

---

## 📂 Project Structure

```
.
├── .github/
│   └── workflows/
│       └── daily_digest.yml   # Daily cloud build & auto-update workflow
├── docs/
│   └── index.html             # Generated web app (served by GitHub Pages)
├── publications.json          # Publication registry & category mapping
├── build_site.py              # Scraper & web app generator script
├── index.html                 # Main web app page
├── data.json                  # Aggregated daily stories data
└── README.md                  # Setup guide
```
