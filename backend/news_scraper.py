import requests
from bs4 import BeautifulSoup
from typing import List, Dict

class NewsScraper:
    """
    Scans financial news to detect bullish/bearish catalysts.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_latest_news(self, query: str = "Indian Stock Market NSE BSE") -> List[Dict]:
        """
        Aggregates news from Google, Moneycontrol, and ET.
        """
        news_items = []
        
        # 1. Google News
        news_items.extend(self._fetch_google_news(query))
        
        # 2. Moneycontrol (Market Section)
        news_items.extend(self._fetch_moneycontrol())
        
        # 3. Economic Times
        news_items.extend(self._fetch_et())

        if not news_items:
            # Fallback
            news_items = [{"title": "Market eyes global cues.", "snippet": "Cautious sentiment ahead of key events.", "source": "System Fallback"}]

        return news_items[:10] # Top 10 broad headlines

    def _fetch_google_news(self, query):
        search_url = f"https://www.google.com/search?q={query}&tbm=nws"
        items = []
        try:
            response = requests.get(search_url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            for g in soup.find_all('div', class_='SoNo7c')[:3]:
                title_tag = g.find('div', class_='n0W69d')
                snippet_tag = g.find('div', class_='GI74Re')
                if title_tag:
                    items.append({"title": title_tag.text, "snippet": snippet_tag.text if snippet_tag else "", "source": "Google News"})
        except: pass
        return items

    def _fetch_moneycontrol(self):
        url = "https://www.moneycontrol.com/news/business/markets/"
        items = []
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for headlines in the markets section
            for entry in soup.find_all('li', class_='clearfix')[:3]:
                h2 = entry.find('h2')
                if h2 and h2.find('a'):
                    items.append({"title": h2.find('a').text.strip(), "snippet": "", "source": "Moneycontrol"})
        except: pass
        return items

    def _fetch_et(self):
        url = "https://economictimes.indiatimes.com/markets/stocks/news"
        items = []
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for headlines
            for entry in soup.find_all('div', class_='eachStory')[:3]:
                h3 = entry.find('h3')
                if h3 and h3.find('a'):
                    items.append({"title": h3.find('a').text.strip(), "snippet": "", "source": "Economic Times"})
        except: pass
        return items

if __name__ == "__main__":
    scraper = NewsScraper()
    news = scraper.fetch_latest_news()
    for item in news:
        print(f"[{item['source']}] {item['title']}")
