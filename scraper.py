import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd


classifieds_cars = []


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent="Mozilla/5.0(Windows NT 10.0;Win64;x64)AppleWebkit/537.36 Chrome/ 120.0.0.0 Safari/537.36(KHTML, like Gecko)Chrome/120.0.0.0 Safari 537.36")

    context.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    page = context.new_page()

    def fetch_page(page, url, retries=3):
        for attempt in range(retries):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=180000)
                return True
            except Exception as e:
                print(f"Attempt {attempt+1} failed for {url}. Error:{e}")
                time.sleep(2)
        return False

    for page_num in range(1, 11):

        url = f"https://www.classifieds.co.zw/zimbabwe-cars?page={page_num}"
        print(f"scraping page {page_num}")

        try:
            success = fetch_page(page, url)
            if not success:
                print(f"could not load page {page_num}, skipping...")
                continue

            page.wait_for_selector(".panel-body", timeout=15000)
            time.sleep(2)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            all_cars = soup.select(".listings-containers .panel-body")
            if not all_cars:
                all_cars = soup.find_all("div", class_="panel-body")
            print(f"found {len(all_cars)} cars on page {page_num}")

            valid_cars_count = 0
            for a_car in all_cars:

                title_tag = a_car.find(
                    "h5", class_="listing-title") or a_car.find("a")
                if not title_tag or not title_tag.text.strip():
                    continue
                title = title_tag.text.strip()
                invalid_headers = ["Cars & Vehicles", "Toyota",
                                   "Used", "Automatic", "On Offer", "Harare", "Diesel", "Motorcyces", "Boats"]
                if title in invalid_headers:
                    continue

                seller_logo = a_car.find("span", class_="pull-right")

                logo = seller_logo.text.strip() if seller_logo else "N/A"

                p = a_car.find("div", class_="usd-price-tooltip")

                price = p.text.strip() if p else "N/A"

                lp = a_car.find("div", class_="local-price-tooltip")

                local_price = lp.text.strip() if lp else "N/A"

                var = a_car.find("div", class_="line-clamp-3")

                variant = var.text.strip() if var else "N/A"

                whatsapp = a_car.find(
                    "button", {"id": lambda x: x and x.startswith("whatsapp-advert")})
                data_href = whatsapp.get("data-href", "") if whatsapp else ""
                phone = "N/A"
                if "phone" in data_href:
                    try:
                        phone = data_href.split("phone=")[1].split("&")[0]
                    except IndexError:
                        phone = "N/A"

                properties_ul = a_car.find("ul", class_="list-unstyled")
                properties = properties_ul.find_all(
                    "li", class_="property") if properties_ul else []

                mileage = properties[0].text.strip() if len(
                    properties) > 0 else "N/A"
                fuel = properties[1].text.strip() if len(
                    properties) > 1 else "N/A"
                transmission = properties[2].text.strip() if len(
                    properties) > 2 else "N/A"
                location = properties[3].text.strip() if len(
                    properties) > 3 else "N/A"

                classifieds_cars.append({"Title": title,
                                        "Variant": variant,
                                         "Mileage": mileage,
                                         "Fuel": fuel,
                                         "Transmission": transmission,
                                         "Location": location,
                                         "Price": price,
                                         "Local Price": local_price,
                                         "Seller's Number": phone,
                                         "Seller's Logo": logo})

        except Exception as e:
            print(f"failed to scrape {e}")

    browser.close()

df = pd.DataFrame(classifieds_cars)
df.to_csv("classifieds.co.zw_cars.csv", index=False)

print(f"scraping complete found {len(df)} cars")
