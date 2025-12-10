import os
import time
import csv
import json
import logging
from logging.handlers import RotatingFileHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib.parse import urlparse, parse_qs
import random
import requests

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler("scraper.log", maxBytes=5*1024*1024, backupCount=5)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)


def scrape_basic_channel_details(channel_url):
    opts = Options()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--start-maximized")
    # opts.add_argument("--headless")
    driver = webdriver.Chrome(options=opts)
    driver.get(channel_url)

    results = []

    try:
        accept_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/form[2]/div/div/button'))
        )
        accept_cookies.click()
        logger.info("Clicked accept cookies button (channel)")
    except TimeoutException:
        logger.info("No accept cookies button on channel.")

    # Expand description
    try:
        expand_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-description-preview-view-model/truncated-text/button'))
        )
        expand_button.click()
    except TimeoutException:
        logger.info(f"No expand button for {channel_url}")

    # Country
    try:
        country_element = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'tr.description-item:has(yt-icon[icon="privacy_public"]) td:nth-of-type(2)'))
        )
        country = country_element.text
    except TimeoutException:
        logger.warning(f"Country not found for {channel_url}")
        country = "N/A"

    # Joined
    try:
        joined_youtube_element = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'tr.description-item:has(yt-icon[icon="info_outline"]) td:nth-of-type(2)'))
        )
        joined_youtube = joined_youtube_element.text
    except TimeoutException:
        logger.warning(f"Joined date not found for {channel_url}")
        joined_youtube = "N/A"

    # Subscribers
    try:
        subscribers_element = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'tr.description-item:has(yt-icon[icon="person_radar"]) td:nth-of-type(2)'))
        )
        subscribers = subscribers_element.text
    except TimeoutException:
        logger.warning(f"Subscribers not found for {channel_url}")
        subscribers = "N/A"

    # Number of videos
    try:
        videos_element = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'tr.description-item:has(yt-icon[icon="my_videos"]) td:nth-of-type(2)'))
        )
        number_of_videos = videos_element.text
    except TimeoutException:
        logger.warning(f"Number of videos not found for {channel_url}")
        number_of_videos = "N/A"

    # Views
    try:
        views_element = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'tr.description-item:has(yt-icon[icon="trending_up"]) td:nth-of-type(2)'))
        )
        views = views_element.text
    except TimeoutException:
        logger.warning(f"Views not found for {channel_url}")
        views = "N/A"

    results.append((channel_url, country, joined_youtube, subscribers, number_of_videos, views))

    logger.info(
        f"Scraped {channel_url} -> {country} -> {joined_youtube} -> {subscribers} -> {number_of_videos} -> {views}"
    )

    return results, driver

def scraper_videos(channel_url, driver):
    driver.get(f"{channel_url}/videos")

    last_count = 0
    scroll_pause = random.uniform(0.5, 2)

    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(scroll_pause)

        video_links = driver.find_elements(By.CSS_SELECTOR, "a#video-title-link")

        current_count = len(video_links)
        if current_count == last_count:
            break

        last_count = current_count

    # Extract all video URLs
    video_urls = [v.get_attribute("href") for v in video_links if v.get_attribute("href")]

    logger.info(f"Total video results: {len(video_urls)}")

    # Save URLs to txt
    with open("video_urls.txt", "w", encoding="utf-8") as f:
        for url in video_urls:
            f.write(url + "\n")

    logger.info("Saved all video URLs to video_urls.txt")

    # LOOP THROUGH VIDEO URLS
    for idx, video_url in enumerate(video_urls, start=1):
        logger.info(f"Opening video {idx}/{len(video_urls)} -> {video_url}")
        driver.get(video_url)
        time.sleep(random.randrange(2, 4))

        # Scroll the screen a little to load the number of comments
        driver.execute_script("window.scrollBy(0, 300);")

        # VIDEO SCRAPING LOGIC HERE
        video_id = parse_qs(urlparse(video_url).query)['v'][0]
        title = driver.find_element(By.CSS_SELECTOR,"h1.style-scope.ytd-watch-metadata yt-formatted-string").get_attribute("title")
        published = [el.text.strip()for el in driver.find_element(By.CSS_SELECTOR, "yt-formatted-string#info").find_elements(By.TAG_NAME, "span")if el.text.strip()][1]
        views = [el.text.strip() for el in driver.find_element(By.CSS_SELECTOR, "yt-formatted-string#info").find_elements(By.TAG_NAME, "span")if el.text.strip()][0]
        description = driver.find_element(By.CSS_SELECTOR,"yt-attributed-string.style-scope.ytd-text-inline-expander").text
        likes = driver.find_element(By.CSS_SELECTOR, "button[aria-label^='like this video'] div.yt-spec-button-shape-next__button-text-content").text
        comments = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-comments-header-renderer yt-formatted-string.count-text span:nth-of-type(1)"))).text
        type = "Long"

        print(f"""
        Video ID: {video_id}
        Title: {title}
        Published: {published}
        Views: {views}
        Description: {description}
        Likes: {likes}
        Comments: {comments}
        Type: {type}
        """)

    return video_urls

def scrape_shorts(channel_url, driver):
    driver.get(f"{channel_url}/shorts")

    last_count = 0
    scroll_pause = random.uniform(0.5, 2)

    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(scroll_pause)

        shorts_links = driver.find_elements(By.CSS_SELECTOR, "a.shortsLockupViewModelHostEndpoint.reel-item-endpoint")

        current_count = len(shorts_links)
        if current_count == last_count:
            break

        last_count = current_count

    # Extract all video URLs
    shorts_urls = [v.get_attribute("href") for v in shorts_links if v.get_attribute("href")]

    logger.info(f"Total shorts results: {len(shorts_urls)}")

    # Save URLs to txt
    with open("shorts_urls.txt", "w", encoding="utf-8") as f:
        for url in shorts_urls:
            f.write(url + "\n")

    logger.info("Saved all shorts URLs to shorts_urls.txt")

    for idx, short_url in enumerate(shorts_urls, start=1):
        logger.info(f"Opening video {idx}/{len(shorts_urls)} -> {short_url}")
        driver.get(short_url)
        time.sleep(random.randrange(2, 4))

        # VIDEO SCRAPING LOGIC HERE
        shorts_id = urlparse(short_url).path.rstrip("/").split("/")[-1]
        title = driver.find_element(By.CSS_SELECTOR,"h2.ytShortsVideoTitleViewModelShortsVideoTitle span").text
        published = driver.find_element(By.CSS_SELECTOR, "meta[itemprop='datePublished']").get_attribute("content")
        views = driver.find_element(By.CSS_SELECTOR, "div.ytwFactoidRendererFactoid[aria-label$='views']").get_attribute("aria-label").split()[0]
        description = driver.find_element(By.CSS_SELECTOR, "meta[name='description']").get_attribute("content")
        likes = driver.find_element(By.CSS_SELECTOR,"button-view-model .yt-spec-button-shape-with-label__label span").text
        comments = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='comment'] + div span").text
        type = "Shorts"

        print(f"""
                Shorts ID: {shorts_id}
                Title: {title}
                Published: {published}
                Views: {views}
                Description: {description}
                Likes: {likes}
                Comments: {comments}
                Type: {type}
                """)

    return shorts_urls

def save_to_csv(filename, data):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["channel_url", "country", "joined youtube since", "subscribers", "number_of_videos", "views"])
        for channel, country, joined_youtube, subscribers, number_of_videos, views in data:
            writer.writerow([channel, country, joined_youtube, subscribers, number_of_videos, views])

    logger.info(f"Saved data to {filename}")

if __name__ == "__main__":
    url = 'https://www.youtube.com/@BrightData'
    results, driver = scrape_basic_channel_details(url)
    # scraper_videos(url, driver)
    scrape_shorts(url, driver)
    save_to_csv("channels.csv", results)
