import sys
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup, SoupStrainer

from parse import parse_content, parse_options
from utils import find_numerical, encode, decode, get_year

data = {}
skipped_pages = []
oldest_year_allowed = 2017
content_path, tag_path = ".qa-q-view-content", ".qa-q-view-tags"

"""
The issues:
  1. Finding question along with images in the question
  2. Finding the tags (Easiest)
  3. Finding options and separating them from the question
  4. Finding the correct answer (Manually)
"""

# For only parsing the div tags with given classes
# Source: https://beautiful-soup-4.readthedocs.io/en/latest/index.html#soupstrainer
div_tags = SoupStrainer(class_=["qa-q-view-content", "qa-q-view-tags"])

async def parse_page(url: str, html: str) -> None:
    soup = BeautifulSoup(html, "lxml", parse_only=div_tags)
    div = soup.select_one(content_path)
    tags = [tag.get_text() for tag in soup.select_one(tag_path).select("li > a")]
    year = None
    for tag in tags:
        if "gate" not in tag: continue
        year = get_year(tag)
        break

    gzipped_html = encode(div.prettify())

    # Ignoring descriptive and questions before 2008 (Storing them for later)
    if "descriptive" in tags or year is None or year < oldest_year_allowed:
        skipped_pages.append({
            "url": url,
            "year": year,
            "tags": tags,
            "html.gz": gzipped_html
        })
        return
        
    data[url] = {
        "tags": tags,
        "year": year,
        # Incase some questions were malformed, use the raw content
        # to manually fix the them later
        "raw_gzip": gzipped_html
    }

    content = div.select_one(".qa-q-view-content > div:nth-child(2)")
    # In the view content div, usually the last ol tag contains the options
    last_ord_list = content.select("ol:nth-last-child(1)")

    opts = None
    if len(last_ord_list) != 0:
        # Remove the options from the content
        opts = await parse_options(last_ord_list[0].extract())

    # If we didnt find any options and the question wasn't tagged as numerical
    if opts is None and find_numerical(tags):
        # Save it for later
        skipped_pages.append({
            "url": url,
            "year": year,
            "tags": tags,
            "html.gz": gzipped_html
        })
        del data[url]
        return
    
    data[url]["options"] = opts
    data[url]["content"] = await parse_content(content)


async def get_page(session: any, url: str) -> None: 
    # Not requesting html of questions that were asked before 
    year = get_year(url)
    if year is None or year < oldest_year_allowed: return
    async with session.get(url) as response:
        html = await response.text()
        await parse_page(url, html)


async def main(FILE_NAME: str) -> None:
    async with aiohttp.ClientSession() as session:
    #    with open(FILE_NAME+".txt", "r") as fp:
    #        tasks = [get_page(session, line.strip()) for line in fp if line.startswith("http")]
    #        await asyncio.gather(*tasks)
       await get_page(session, "https://gateoverflow.in/399278/gate-cse-2023-question-33")
    json.dump(data, open(f"{FILE_NAME}.json", "w"), indent=4)
    json.dump(skipped_pages, open(f"{FILE_NAME}.skipped.json", "w"), indent=4)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <file_name>")
        exit(1)
    file_name = sys.argv[1]
    asyncio.run(main(file_name))
