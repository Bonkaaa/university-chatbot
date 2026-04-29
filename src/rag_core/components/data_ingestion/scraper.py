import requests
import json
from markdownify import markdownify as md

from ...utils import setup_logger
from ....config import DOCS_FOR_SCRAPE_DIR, RAW_DOCS_DIR

logger = setup_logger("scraper.log", "scraper")

class Scraper:
    def __init__(
        self, 
        api_url: str, 
    ):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        } 

    def scrape(
        self,
        payload: dict,
        doc_name: str
    ):
        logger.info("Đang gọi API lấy dữ liệu...")

        response = requests.post(self.api_url, json=payload, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            
            html_content = data['WebTitleInfo']['Description']

            md_text = md(html_content, heading_style="ATX")

            # Path to save the scraped markdown file
            path = RAW_DOCS_DIR / f"{doc_name}.md"
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(md_text)
            
            logger.info(f"Đã lưu file {doc_name}.md vào {path}")
        
        else:
            logger.error(f"Lỗi truy cập. Mã lỗi: {response.status_code}")
            return None
        
if __name__ == "__main__":
    # Example usage
    api_url = "https://ctsv.hust.edu.vn/api-t/HWAdmin/GetWebTitleInfo"
    

    scraper = Scraper(api_url)

    docs_json = DOCS_FOR_SCRAPE_DIR / "docs.json"

    with open(docs_json, "r", encoding="utf-8") as f:
        docs = json.load(f)

    for doc in docs:
        docs_name = doc["doc_name"]
        payload = doc["payload"]
        
        scraper.scrape(payload, docs_name)
