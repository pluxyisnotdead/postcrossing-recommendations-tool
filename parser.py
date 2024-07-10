import logging
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


class PostcrossingParser:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = self._init_driver()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = "/usr/bin/chromium"
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        logging.info("Initializing Chrome driver")

        # Use chromedriver from the PATH environment variable
        service = Service()

        return webdriver.Chrome(service=service, options=chrome_options)

    def login(self):
        logging.info("Navigating to login page")
        self.driver.get("https://www.postcrossing.com/login?")
        username_input = self.driver.find_element(By.XPATH, '//*[@id="username"]')
        password_input = self.driver.find_element(By.XPATH, '//*[@id="password"]')
        logging.info("Entering username and password")
        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        password_input.send_keys(Keys.RETURN)
        logging.info("Login submitted")

    def scroll_and_collect_logs(self, target_name):
        logging.info(f"Navigating to {target_name}'s gallery page")
        self.driver.get(f"https://www.postcrossing.com/user/{target_name}/gallery/favourites")
        self.driver.get_log('performance')
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            logging.info("Scrolling to the bottom of the page")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logging.info("Reached the bottom of the page")
                break
            last_height = new_height
        logging.info("Collecting logs")
        logs = self.driver.get_log('performance')

        return logs

    def extract_thumb_urls(self, logs):
        logging.info("Extracting thumbnail URLs from logs")
        thumb_urls = []
        for log in logs:
            log_message = json.loads(log['message'])['message']
            if 'Network.requestWillBeSent' in log_message['method']:
                if 'request' in log_message['params']:
                    url = log_message['params']['request']['url']
                    if 'thumb' in url:
                        medium_url = url.replace('thumb', 'medium')
                        thumb_urls.append(medium_url)
        logging.info(f"Extracted {len(thumb_urls)} thumbnail URLs")
        return thumb_urls

    def get_about_text(self, target_name):
        logging.info(f"Navigating to {target_name}'s about page")
        self.driver.get(f"https://www.postcrossing.com/user/{target_name}")
        about_text_element = self.driver.find_element(By.CLASS_NAME, 'about-text')
        logging.info("Extracted about text")
        return about_text_element.text

    def save_to_json(self, data, filename):
        logging.info(f"Saving data to {filename}")
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Data saved to {filename}")

    def run(self, target_names):
        logging.info("Starting parser")
        self.login()
        result = {}

        # Ensure the directory exists
        output_dir = 'users'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for target_name in target_names:
            filename = os.path.join(output_dir, f'{target_name}.json')
            if os.path.exists(filename):
                logging.info(f"Data for {target_name} already exists. Skipping.")
                continue

            # Only log and parse if the file does not exist
            logging.info(f"Processing {target_name}")
            logs = self.scroll_and_collect_logs(target_name)
            thumb_urls = self.extract_thumb_urls(logs)
            about_text = self.get_about_text(target_name)
            result[target_name] = {
                "favorites": thumb_urls,
                "about_text": about_text
            }

            # Save to the specified directory
            self.save_to_json(result[target_name], filename)

        self.driver.quit()
        logging.info("Parsing completed for all users.")
        # return result

    def parse_user(self, target_name):
        logging.info(f"Starting parser for {target_name}")
        self.login()
        result = {}

        # Ensure the directory exists
        output_dir = 'users'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = os.path.join(output_dir, f'{target_name}.json')
        if os.path.exists(filename):
            logging.info(f"Data for {target_name} already exists. Skipping.")
            with open(filename, 'r') as f:
                result[target_name] = json.load(f)
            return result[target_name]

        # Only log and parse if the file does not exist
        logging.info(f"Processing {target_name}")
        logs = self.scroll_and_collect_logs(target_name)
        thumb_urls = self.extract_thumb_urls(logs)
        about_text = self.get_about_text(target_name)
        result[target_name] = {
            "favorites": thumb_urls,
            "about_text": about_text
        }

        # Save to the specified directory
        self.save_to_json(result[target_name], filename)

        self.driver.quit()
        logging.info(f"Parsing completed for {target_name}.")
        return result[target_name]