import time
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

from db import init_db, save_channel, save_video, save_short, video_exists, short_exists

URL = "https://www.youtube.com/@PokerStars"

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
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36")
    # opts.add_argument("--headless")
    driver = webdriver.Chrome(options=opts)
    driver.get(channel_url)

    try:
        accept_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/form[2]/div/div/button'))
        )
        accept_cookies.click()
    except TimeoutException:
        pass

    # Expand description
    try:
        expand_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-description-preview-view-model/truncated-text/button'))
        )
        expand_button.click()
    except TimeoutException:
        pass

    # Extract fields
    def safe_find(css, default="N/A"):
        try:
            return WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css))
            ).text
        except TimeoutException:
            return default

    country = safe_find('tr.description-item:has(yt-icon[icon="privacy_public"]) td:nth-of-type(2)')
    joined_youtube = safe_find('tr.description-item:has(yt-icon[icon="info_outline"]) td:nth-of-type(2)')
    subscribers = safe_find('tr.description-item:has(yt-icon[icon="person_radar"]) td:nth-of-type(2)')
    number_of_videos = safe_find('tr.description-item:has(yt-icon[icon="my_videos"]) td:nth-of-type(2)')
    views = safe_find('tr.description-item:has(yt-icon[icon="trending_up"]) td:nth-of-type(2)')

    channel_id = channel_url.rstrip("/").split("@")[-1]

    save_channel(
        channel_id=channel_id,
        url=channel_url,
        country=country,
        joined=joined_youtube,
        subscribers=subscribers,
        video_count=number_of_videos,
        views=views
    )

    return (channel_id, driver)


def scraper_videos(channel_url, driver):
    driver.get(f"{channel_url}/videos")

    last_count = 0

    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(random.uniform(0.8, 2.2))

        video_links = driver.find_elements(By.CSS_SELECTOR, "a#video-title-link")

        current_count = len(video_links)
        if current_count == last_count:
            break

        last_count = current_count

    video_urls = [v.get_attribute("href") for v in video_links if v.get_attribute("href")]
    channel_id = channel_url.rstrip("/").split("@")[-1]

    for video_url in video_urls:
        video_id = parse_qs(urlparse(video_url).query)['v'][0]

        if video_exists(video_id):
            continue

        driver.get(video_url)
        time.sleep(random.randrange(2, 5))

        driver.execute_script("window.scrollBy(0, 300);")
        try:
            title = driver.find_element(
                By.CSS_SELECTOR,
                "h1.style-scope.ytd-watch-metadata yt-formatted-string"
            ).get_attribute("title")
        except Exception:
            title = "N/A"

        try:
            spans = [el.text.strip() for el in driver.find_element(
                By.CSS_SELECTOR, "yt-formatted-string#info"
            ).find_elements(By.TAG_NAME, "span") if el.text.strip()]

            published = spans[1]
            views = spans[0]
        except Exception:
            published = "N/A"
            views = "N/A"

        try:
            expand_description = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="expand"]'))
            )
            expand_description.click()
        except TimeoutException:
            pass

        try:
            description = driver.find_element(
                By.CSS_SELECTOR, "#description-inline-expander > div:nth-child(1)"
            ).text

            likes = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label^='like this video'] div.yt-spec-button-shape-next__button-text-content"
            ).text
        except Exception:
            description = "N/A"

        try:
            comments = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ytd-comments-header-renderer yt-formatted-string.count-text span:nth-of-type(1)")
                )
            ).text
        except TimeoutException:
            comments = "N/A"

        save_video(
            video_id=video_id,
            channel_id=channel_id,
            url=video_url,
            title=title,
            published=published,
            views=views,
            likes=likes,
            comments=comments,
            description=description,
            type_="Long"
        )

    return video_urls


def scrape_shorts(channel_url, driver):
    driver.get(f"{channel_url}/shorts")

    last_count = 0

    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(random.uniform(0.8, 2.2))

        shorts_links = driver.find_elements(By.CSS_SELECTOR, "a.shortsLockupViewModelHostEndpoint.reel-item-endpoint")

        current_count = len(shorts_links)
        if current_count == last_count:
            break

        last_count = current_count

    shorts_urls = [v.get_attribute("href") for v in shorts_links if v.get_attribute("href")]
    channel_id = channel_url.rstrip("/").split("@")[-1]

    for short_url in shorts_urls:
        short_id = urlparse(short_url).path.rstrip("/").split("/")[-1]

        if short_exists(short_id):
            continue

        driver.get(short_url)
        time.sleep(random.randrange(2, 5))

        # TITLE
        try:
            title = driver.find_element(
                By.CSS_SELECTOR,
                "h2.ytShortsVideoTitleViewModelShortsVideoTitle span"
            ).text
        except Exception:
            title = "N/A"

        # PUBLISHED
        try:
            published = driver.find_element(
                By.CSS_SELECTOR,
                "meta[itemprop='datePublished']"
            ).get_attribute("content")
        except Exception:
            published = "N/A"

        # VIEWS
        try:
            views = driver.find_element(
                By.CSS_SELECTOR,
                "div.ytwFactoidRendererFactoid[aria-label$='views']"
            ).get_attribute("aria-label").split()[0]
        except Exception:
            views = "N/A"

        # DESCRIPTION
        try:
            description = driver.find_element(
                By.CSS_SELECTOR, "meta[name='description']"
            ).get_attribute("content")
        except Exception:
            description = "N/A"

        # LIKES
        try:
            likes = driver.find_element(
                By.CSS_SELECTOR,
                "button-view-model .yt-spec-button-shape-with-label__label span"
            ).text
        except Exception:
            likes = "N/A"

        # COMMENTS
        try:
            comments = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label*='comment'] + div span"
            ).text
        except Exception:
            comments = "N/A"

        save_short(
            short_id=short_id,
            channel_id=channel_id,
            url=short_url,
            title=title,
            published=published,
            views=views,
            likes=likes,
            comments=comments,
            description=description,
            type_="Shorts"
        )

    return shorts_urls


if __name__ == "__main__":
    init_db()

    channel_id, driver = scrape_basic_channel_details(URL)
    scraper_videos(URL, driver)
    scrape_shorts(URL, driver)
