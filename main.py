from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException  # Add this line
from bs4 import BeautifulSoup
import pandas as pd
import time

def login_with_selenium():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://employer.schoolspring.com/login.cfm')

    
    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'login_user'))
        )
        password_field = driver.find_element(By.NAME, 'login_pass')
        login_button = driver.find_element(By.XPATH, "//button[@class='buttonDefault']")
        
        username_field.send_keys('zephmathnasium')
        password_field.send_keys('Zcv#9&BcG4Sr')
        login_button.click()
        
        # Wait for the dashboard to load (you might need to adjust this selector)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'dashboard'))
        )
        
        print("Login successful")
        return driver
    except Exception as e:
        print(f"Login attempt encountered an issue: {str(e)}")
        print(f"Current URL: {driver.current_url}")
        
        # Check if we're actually logged in despite the exception
        if "employer/index.cfm" in driver.current_url:
            print("It appears we've successfully logged in despite the exception.")
            return driver
        
        driver.quit()
        return None

def scrape_candidates(driver):

    candidates_data = []
    base_url = 'https://employer.schoolspring.com/employer/pool/candsearch.cfm'

    try:
        # Step 1: go to candidate page and select the job we are looking for.
        driver.get(base_url)
                # Print the entire HTML content of the page
        # print("HTML content of the page:")
        # # print(driver.page_source)

        # Wait for the job selection input to be present
        job_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//select[option[text()="Select a job posting..."]]'))
        )
        print("Job input element found successfully!")
        print(f"Job input element tag: {job_input.tag_name}")
        print(f"Job input element attributes: {job_input.get_attribute('outerHTML')}")
        
        print('before job input')
        job_select = Select(job_input)

        job_select.select_by_value('4795118')
        print('after job input')

        
        find_candidates_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Find Candidates!']")
        print(f"Button state before click: {find_candidates_button.is_enabled()}")
        find_candidates_button.click()
        print('Attempted to click the button')        

        driver.save_screenshot("after_button_click.png")
        
        driver.get(f"https://employer.schoolspring.com/employer/pool/candidatesearch.cfm?perpage=100")

        driver.save_screenshot("perpage100.png")
        
        page = 1
        while True:
            if page > 1:
                driver.get(f"https://employer.schoolspring.com/employer/pool/candidatesearch.cfm?pg={page}")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find candidate links within the table rows
            candidate_links = soup.find_all('a', href=lambda href: href and '/employer/pool/candidates/profile.cfm?c_id=' in href)
            
            if not candidate_links:
                break  # No more candidates, exit the loop
            
            for link in candidate_links:
                candidate_url = 'https://employer.schoolspring.com' + link['href']
                candidate_name = link.text.strip()
                
                candidates_data.append({
                    'Name': candidate_name,
                    'Profile Link': candidate_url
                })
            
            save_to_txt(candidates_data)

            print(f"Processed page {page}, found {len(candidate_links)} candidates")
            page += 1
            time.sleep(2)  # Respectful delay between pages

    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    
    return candidates_data


def scrape_email_phone(driver, candidates_data):

    updated_candidates = []
    for candidate in candidates_data:
        profile_link = candidate['Profile Link']
        driver.get(profile_link)
        print(f"Navigated to profile: {profile_link}")
        driver.save_screenshot("candidate_profile.png")

        # Add a small delay to ensure the page loads
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find the table containing contact information
        contact_table = soup.find('table', {'width': '500', 'cellspacing': '0', 'cellpadding': '6'})
        # Find the table containing career information
        career_table = soup.find('table', {'width': '500', 'cellspacing': '0', 'cellpadding': '6', 'style': 'border:1px solid #e6e6e6;'})

        # # Debug: Print the contact table HTML
        # if contact_table:
        #     print("Contact table found:")
        #     print(contact_table.prettify())
        # else:
        #     print("Contact table not found with the specified attributes.")
        #     print("Printing all tables with width='500':")
        #     for table in soup.find_all('table', width='500'):
        #         print(table.prettify())
        #         print("---")
        if career_table:
            print("Career table found:")
            print(career_table.prettify())
        else:
            print("Career table not found with the specified attributes.")
            print("Printing all tables with width='500':")
            for table in soup.find_all('table', width='500'):
                print(table.prettify())
                print("---")
        candidate_info = {
            'Name': candidate['Name'],
            'Profile Link': profile_link,
            'Candidate ID': '',
            'Full Name': '',
            'Other/Birth Name(s)': '',
            'Status': '',
            'Current Address': '',
            'Permanent Address': '',
            'Phone': '',
            'Email': '',
            'Web Site': '',
            'Highest Degree': '',
            'Credits Beyond Degree': '',
            'Date Available To Start': '',
            'Eligible to work in US without sponsorship?': ''
        }

        if contact_table:
            rows = contact_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].text.strip().lower()
                    value = cells[1].text.strip()

                    if 'candidate id' in key:
                        candidate_info['Candidate ID'] = value
                    elif 'name' == key:
                        candidate_info['Full Name'] = value
                    elif 'other/birth name' in key:
                        candidate_info['Other/Birth Name(s)'] = value
                    elif 'current status' in key:
                        candidate_info['Status'] = value
                    elif 'current address' in key:
                        candidate_info['Current Address'] = value.replace('\n', ', ')
                    elif 'permanent address' in key:
                        candidate_info['Permanent Address'] = value.replace('\n', ', ')
                    elif 'phone' == key:
                        candidate_info['Phone'] = value
                    elif 'email' == key:
                        candidate_info['Email'] = cells[1].find('a')['href'].replace('mailto:', '') if cells[1].find('a') else value
                    elif 'web site' in key:
                        candidate_info['Web Site'] = value

                    print(f"Extracted: {key} -> {value}")  # Debug print

            if not candidate_info['Candidate ID']:
                print(f"Warning: No Candidate ID found for {candidate['Name']}")

        else:
            print(f"Warning: Contact information table not found for {candidate['Name']}")

        if career_table:
            rows = career_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].text.strip().lower()
                    value = cells[1].text.strip()

                    if 'highest degree' in key:
                        candidate_info['Highest Degree'] = value
                    elif 'credits beyond degree' in key:
                        candidate_info['Credits Beyond Degree'] = value
                    elif 'date available to start' in key:
                        candidate_info['Date Available To Start'] = value
                    elif 'eligible to work in us without sponsorship?' in key:
                        candidate_info['Eligible to work in US without sponsorship?'] = value

                    print(f"Extracted: {key} -> {value}")  # Debug print

        else:
            print(f"Warning: Career information table not found for {candidate['Name']}")

        updated_candidates.append(candidate_info)
        print(f"Processed candidate: {candidate['Name']}")
        print(f"Extracted info: {candidate_info}")  # Debug print

    df = pd.DataFrame(updated_candidates)

    # Save the DataFrame to an Excel file
    excel_filename = 'candidates_data.xlsx'
    df.to_excel(excel_filename, index=False)
    print(f"Data saved to {excel_filename}")

    return updated_candidates  # Return the updated list with all candidate information

    
def save_to_txt(data, filename='candidates_data.txt'):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(str(data))
    print(f"Data saved to {filename}")


just_two_candidates = [{'Name': 'Gerecke, Eva', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9052478'},{'Name': 'Abbay, Setary', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=6620844'}]

test_candidate_list = [{'Name': ',', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9022278'}, {'Name': 'Brown-Smalls, Camille', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=5055712'}, {'Name': 'Gerecke, Eva', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9052478'}, {'Name': 'Marshall, Kasondra', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=420051'}, {'Name': '(Mota) Hutchison, Marissa', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=8355129'}, {'Name': '000, 0000', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=7774584'}, {'Name': 'A, Emma', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=7773464'}, {'Name': 'A Hamilton, Samantha', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=6120262'}, {'Name': 'A Thibeault, Carol', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9145520'}, {'Name': 'Abadie, Melissa', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=101174'}, {'Name': 'Abalos, Teresa', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=10281425'}, {'Name': 'ABANGAN, MARY JANE', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9284073'}, {'Name': 'Abbay, Setary', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=6620844'}, {'Name': 'Abbott, Kristen', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=451588'}]

# Main execution
if __name__ == "__main__":
    driver = login_with_selenium()
    if driver:
        scrape_email_phone(driver, just_two_candidates)
        # candidates_data = scrape_candidates(driver)
        # save_to_txt(candidates_data)
    else:
        print("Unable to log in. Please check the credentials and try again.")
