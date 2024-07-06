import time
import pandas as pd
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Initialize global variables
message_template = "Hi {name},\n\nI reviewed your application for our {job_title} job and am impressed with your background. I’d like to schedule a call with you to discuss your experience. Can you share a few dates and times that would work for a 30 to 45-minute call?"
output_file = "sent_messages.csv"
delay_between_actions = (3, 5)
pause_after_messages = 100
pause_duration = 5 * 60  # 5 minutes

# Load historical data to avoid duplicate messages
try:
    sent_messages = pd.read_csv(output_file)
except FileNotFoundError:
    sent_messages = pd.DataFrame(columns=["job_id", "applicant_id", "applicant_name", "message"])

# Function to login to LinkedIn
def linkedin_login(driver):
    driver.get("https://www.linkedin.com/login")
    # Let user input the credentials and 2FA manually
    WebDriverWait(driver, 300).until(EC.url_contains("feed"))

# Function to send message to an applicant
def send_message_to_applicant(driver, applicant, job_title):
    try:
        applicant.find_element(By.CLASS_NAME, "message-anywhere-button").click()
        time.sleep(3)
        message_box = driver.find_element(By.CLASS_NAME, "msg-form__contenteditable")
        name = applicant.find_element(By.CLASS_NAME, "applicant-name").text
        message = message_template.format(name=name, job_title=job_title)
        message_box.send_keys(message)
        driver.find_element(By.CLASS_NAME, "msg-form__send-button").click()
        time.sleep(2)
        driver.find_element(By.CLASS_NAME, "msg-overlay-bubble-header__control--close").click()
        return True, message
    except Exception as e:
        print(f"Failed to send message to {name}: {e}")
        return False, None

# Function to process job applicants
def process_applicants(driver, job_id):
    driver.get(f"https://www.linkedin.com/hiring/jobs/{job_id}/detail/")
    try:
        view_applicants_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "view-applicants-button"))
        )
        view_applicants_button.click()
    except Exception as e:
        print(f"Error navigating to applicants for job ID {job_id}: {e}")
        return

    job_title = driver.find_element(By.CLASS_NAME, "job-title").text
    while True:
        try:
            applicants = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "applicant-card"))
            )
            for applicant in applicants:
                applicant_id = applicant.get_attribute("data-urn")
                if not sent_messages[(sent_messages.job_id == job_id) & (sent_messages.applicant_id == applicant_id)].empty:
                    continue
                success, message = send_message_to_applicant(driver, applicant, job_title)
                if success:
                    sent_messages.append(
                        {"job_id": job_id, "applicant_id": applicant_id, "applicant_name": name, "message": message},
                        ignore_index=True
                    )
                    sent_messages.to_csv(output_file, index=False)
                    if len(sent_messages) % pause_after_messages == 0:
                        time.sleep(pause_duration)
                time.sleep(delay_between_actions[0] + (delay_between_actions[1] - delay_between_actions[0]) * random.random())
            try:
                next_page = driver.find_element(By.CLASS_NAME, "next-button")
                next_page.click()
            except:
                break
        except Exception as e:
            print(f"Error processing applicants for job ID {job_id}: {e}")
            break

# Main function to run the script
def main():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    linkedin_login(driver)
    job_ids = ["3787656311", "another_job_id"]
    for job_id in job_ids:
        process_applicants(driver, job_id)
    driver.quit()

if __name__ == "__main__":
    main()