
import streamlit as st
import requests
from bs4 import BeautifulSoup4
import time
import smtplib
import schedule
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def fetch_jobs(keywords, locations):
    results = []
    base_url = "https://www.indeed.fr/jobs?q={query}&l={location}"

    for keyword in keywords:
        for location in locations:
            query = keyword.replace(" ", "+")
            url = base_url.format(query=query, location=location)

            response = requests.get(url)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('a', class_="tapItem")

            for job in job_cards[:5]:
                title = job.find('h2').text.strip() if job.find('h2') else "No title"
                link = "https://www.indeed.fr" + job['href']
                results.append({
                    "title": title,
                    "location": location,
                    "link": link
                })
            time.sleep(1)
    return results

def send_email(to_email, job_list):
    from_email = "your-email@gmail.com"
    from_password = "your-app-password"

    msg = MIMEMultipart("alternative")
    msg['Subject'] = "📰 Your Daily French Job Listings"
    msg['From'] = from_email
    msg['To'] = to_email

    html_content = "<h3>Today's Job Listings:</h3><ul>"
    for job in job_list:
        html_content += f"<li><strong>{job['title']}</strong> – {job['location']}<br><a href='{job['link']}'>View Listing</a></li><br>"
    html_content += "</ul>"

    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email failed:", e)
        return False

def start_scheduler(email, keywords, locations):
    def job_task():
        job_data = fetch_jobs(keywords, locations)
        if job_data:
            send_email(email, job_data)

    schedule.every().day.at("08:00").do(job_task)

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=run_schedule)
    thread.daemon = True
    thread.start()

st.set_page_config(page_title="Job Finder – Basan Groupe", layout="centered")
st.title("🔎 French-speaking Job Finder")
st.markdown("Find caregiver, hospital, and housekeeper jobs in French-speaking countries. Receive daily updates by email!")

job_categories = {
    "Aide-soignant(e)": "aide soignante",
    "Femme de ménage": "femme de ménage",
    "Garde d'enfants": "garde d'enfants",
    "Chauffeur": "chauffeur",
    "Agent de sécurité": "agent de sécurité",
    "Jardinier": "jardinier",
    "Cuisinier / Cuisinière": "cuisinier",
    "Serveur / Serveuse": "serveur",
    "Réceptionniste": "réceptionniste",
    "Ouvrier du bâtiment": "ouvrier bâtiment"
}

selected_jobs = st.multiselect(
    "📌 Select job categories to search:",
    options=list(job_categories.keys()),
    default=["Aide-soignant(e)", "Femme de ménage", "Garde d'enfants"]
)

keywords = [job_categories[job] for job in selected_jobs]

locations_input = st.text_input("Enter locations (comma-separated)", "France, Belgique, Suisse")
user_email = st.text_input("Enter your email to receive daily job alerts", "")

if st.button("Search Jobs Now"):
    locations = [l.strip() for l in locations_input.split(',')]
    jobs = fetch_jobs(keywords, locations)
    if jobs:
        st.success(f"{len(jobs)} jobs found!")
        for job in jobs:
            st.markdown(f"**{job['title']}** – {job['location']}")
            st.markdown(f"[View Listing]({job['link']})")
            st.markdown("---")
    else:
        st.warning("No jobs found. Try different keywords or locations.")

if st.button("Start Daily Email Notifications"):
    if user_email:
        locations = [l.strip() for l in locations_input.split(',')]
        start_scheduler(user_email, keywords, locations)
        st.success(f"📧 Daily email alerts scheduled for {user_email}")
    else:
        st.error("Please enter a valid email address.")
