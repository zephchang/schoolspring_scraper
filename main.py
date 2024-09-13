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
import candidate_links 
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = "https://qtmnxelrpjwtajqxqcko.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF0bW54ZWxycGp3dGFqcXhxY2tvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjYyNjQ5NjksImV4cCI6MjA0MTg0MDk2OX0.9OMSCP3oppN1-pV6z1yabOz5dHxbx9xcltUCJF2rDtY"
supabase: Client = create_client(supabase_url, supabase_key)

import traceback

# Supabase test function
def test_supabase_connection():
    try:
        # Insert a test record
        test_data = {
            'name': 'Test Candidate',
            'email': 'test@example.com',
            'profile_link': 'https://example.com/profile'
        }
        
        response = supabase.table('candidates_data').insert(test_data).execute()
        print("Insert response:", response)
        
        # Retrieve the inserted record
        result = supabase.table('candidates_data').select("*").eq('name', 'Test Candidate').execute()
        print("Retrieved data:", result)
        
        print("Supabase connection test completed successfully!")
    except Exception as e:
        print(f"Error during Supabase test: {str(e)}")
        print("Traceback:")
        traceback.print_exc()

# Run the test function
if __name__ == "__main__":
    test_supabase_connection()


def login_with_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Uncomment for headless mode
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
        
        job_select = Select(job_input)

        job_select.select_by_value('4795118')


        find_candidates_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Find Candidates!']")

        find_candidates_button.click()
        # driver.save_screenshot("after_button_click.png")
        
        driver.get(f"https://employer.schoolspring.com/employer/pool/candidatesearch.cfm?perpage=100")

        # driver.save_screenshot("perpage100.png")
        
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
    for index, candidate in enumerate(candidates_data, 1):
        try:
            profile_link = candidate['Profile Link']
            driver.get(profile_link)
            print(f"Navigated to profile: {profile_link}")
            # driver.save_screenshot("candidate_profile.png")

            time.sleep(1.5)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            tables = soup.find_all('table', width='500')

            contact_table = None
            career_table = None

            if len(tables) == 2:
                contact_table = tables[0]
                career_table = tables[1]

            elif len(tables) == 3:
                contact_table = tables[1]
                career_table = tables[2]
            # Debug: Print the contact table HTML
            if contact_table:
                print("Contact table found.")
            else:
                print("Contact table not found.")

            if career_table:
                print("Career table found.")
            else:
                print("Career table not found.")

            candidate_info = {
                'name': candidate['Name'],
                'profile_link': profile_link,
                'candidate_id': '',
                'full_name': '',
                'other_birth_names': '',
                'status': '',
                'current_address': '',
                'permanent_address': '',
                'phone': '',
                'email': '',
                'web_site': '',
                'highest_degree': '',
                'credits_beyond_degree': '',
                'date_available_to_start': '',
                'eligible_to_work_in_us_without_sponsorship': ''
            }

            if contact_table:
                print('Processing contact table')
                rows = contact_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].text.strip().lower()
                        value = cells[1].text.strip()

                        if 'candidate id' in key:
                            candidate_info['candidate_id'] = value
                        elif 'name' == key:
                            candidate_info['full_name'] = value
                        elif 'other/birth name' in key:
                            candidate_info['other_birth_names'] = value
                        elif 'current status' in key:
                            candidate_info['status'] = value
                        elif 'current address' in key:
                            candidate_info['current_address'] = value.replace('\n', ', ')
                        elif 'permanent address' in key:
                            candidate_info['permanent_address'] = value.replace('\n', ', ')
                        elif 'phone' == key:
                            candidate_info['phone'] = value
                        elif 'email' == key:
                            candidate_info['email'] = cells[1].find('a')['href'].replace('mailto:', '') if cells[1].find('a') else value
                        elif 'web site' in key:
                            candidate_info['web_site'] = value

                        print(f"Extracted: {key} -> {value}")  # Debug print

            else:
                print(f"Warning: Contact information table not found for {candidate['Name']}")

            if career_table:
                print('Processing career table')
                rows = career_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        print(f'Career table key: {key}')
                        print(f'Career table value: {value}')
                        if 'highest degree' in key:
                            candidate_info['highest_degree'] = value
                        elif 'credits beyond degree' in key:
                            candidate_info['credits_beyond_degree'] = value
                        elif 'date available to start' in key:
                            candidate_info['date_available_to_start'] = value
                        elif 'eligible to work in us without sponsorship?' in key:
                            candidate_info['eligible_to_work_in_us_without_sponsorship'] = value
                        else:
                            print(f"Unmatched key: {key}")

                        print(f"Extracted: {key} -> {value}")  # Debug print

            else:
                print(f"Warning: Career information table not found for {candidate['Name']}")

            updated_candidates.append(candidate_info)
            print(f"Processed candidate: {candidate['Name']}")
            print("Candidate info:", candidate_info)

        except Exception as e:
            print(f"Error processing candidate {candidate['Name']}: {str(e)}")
            # Add the candidate with minimal info to not lose the record
            updated_candidates.append({
                'name': candidate['Name'],
                'profile_link': candidate.get('Profile Link', ''),
                'error': str(e)
            })

        # Save to Supabase every 20 candidates or on the last candidate
        if index % 20 == 0 or index == len(candidates_data):
            try:
                # Insert data into Supabase
                response = supabase.table('candidates_data').insert(updated_candidates).execute()
                print(f"Data saved to Supabase - Response: {response}")
                
                # Clear the updated_candidates list after successful insertion
                updated_candidates = []
            except Exception as e:
                print(f"Error saving data to Supabase: {str(e)}")
                print("Traceback:")
                traceback.print_exc()
                # You might want to implement a retry mechanism or alternative storage method here
        
        print(f"Candidate {index} complete")
    
    return updated_candidates

def save_to_txt(data, filename='candidates_data.txt'):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(str(data))
    print(f"Data saved to {filename}")


just_two_candidates = [{'Name': 'Albahary, Serena', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=10261480'},{'Name': 'Adler, Rachel', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=2611152'},{'Name': 'Aditorem, Benjamin', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=10169451'}]

test_candidate_list = [{'Name': ',', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9022278'}, {'Name': 'Brown-Smalls, Camille', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=5055712'}, {'Name': 'Gerecke, Eva', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9052478'}, {'Name': 'Marshall, Kasondra', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=420051'}, {'Name': '(Mota) Hutchison, Marissa', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=8355129'}, {'Name': '000, 0000', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=7774584'}, {'Name': 'A, Emma', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=7773464'}, {'Name': 'A Hamilton, Samantha', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=6120262'}, {'Name': 'A Thibeault, Carol', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9145520'}, {'Name': 'Abadie, Melissa', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=101174'}, {'Name': 'Abalos, Teresa', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=10281425'}, {'Name': 'ABANGAN, MARY JANE', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=9284073'}, {'Name': 'Abbay, Setary', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=6620844'}, {'Name': 'Abbott, Kristen', 'Profile Link': 'https://employer.schoolspring.com/employer/pool/candidates/profile.cfm?c_id=451588'}]

# Main execution
if __name__ == "__main__":
    driver = login_with_selenium()
    if driver:
        scrape_email_phone(driver, candidate_links.pg1to42)
        # candidates_data = scrape_candidates(driver)
        # save_to_txt(candidates_data)
    else:
        print("Unable to log in. Please check the credentials and try again.")
