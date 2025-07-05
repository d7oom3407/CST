import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup

# ---- Set your API Key here ----
openai.api_key = st.secrets["openai_api_key"]
# ---- Fixed list of known categories ----
CATEGORIES = [
    "IT Services (IT Services Management)",
    "IT Services (Cybersecurity Services)",
    "IT Services (Consulting Services)",
    "IT Services (Support and maintainance)",
    "IT Infrastructure (Cloud Solutions)",
    "IT Infrastructure (Network Design)",
    "Data Services (Data Analytics)",
    "Software Development (Custom Applications)",
    "AI Solutions (ML Consulting)",
    "Digital Transformation (Strategy & Execution)"
]

# ---- Streamlit UI ----
st.title("Company Service Categorizer")
st.write("Provide a company website and select the service categories to evaluate.")

# Input fields
url = st.text_input("Website URL", placeholder="https://example.com")
selected_categories = st.multiselect("Select Categories to Check", CATEGORIES)

if st.button("Analyze Website"):
    if not url or not selected_categories:
        st.warning("Please provide a valid URL and select at least one category.")
    else:
        try:
            # Fetch and clean website content
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()

            # Prepare categories as string
            category_list = "\n".join(f"{i+1}- {cat}" for i, cat in enumerate(selected_categories))

            # OpenAI Prompt
            system_prompt = (
                "i want to give you the content of a website of a company and a group of categories and i want you to tell me "
                "if the company satisfies these categories. for example i'll give a link, and the categories can be something like; "
                "IT Consultation, Cybersecurity Solutions, IT Infra. u then tell me which ones you can be certain that they provide "
                "after accessing their website. Your response should be in a form of a dictionary, where the keys are the categories, "
                "and the value is a list where the first index is a binary representation of your response (0 for no, 1 for yes, or None if you're not sure), "
                "and the second index your reasoning behind that choice. Do not add anything else to your response, no summary no nothing all i need to see is the dictionary"
            )

            user_prompt = f"Categories:\n{category_list}\nWebsite Content:\n{text}"

            # Call OpenAI API
            result = openai.ChatCompletion.create(
                model="gpt-4o",  # use gpt-4o or other preferred model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            st.subheader("Categorization Result")
            st.code(result.choices[0].message.content, language='python')

        except Exception as e:
            st.error(f"An error occurred: {e}")
