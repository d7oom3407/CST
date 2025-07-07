import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd
import ast

# ---- Set your API Key here using Streamlit secrets ----
client = OpenAI(api_key=st.secrets["openai_api_key"])

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
            text = soup.get_text(separator=' ', strip=True)

            # Prepare categories as string
            category_list = "\n".join(f"{i+1}- {cat}" for i, cat in enumerate(selected_categories))

            # OpenAI Prompt
            system_prompt = (
                "You will receive the content of a company website and a list of service categories. "
                "Return a Python dictionary where each key is a category, and each value is a list of two elements: "
                "[1 or 0 or None, explanation]. "
                "Respond ONLY with a valid Python dictionary. Do NOT include any explanation or notes outside the dictionary."
            )

            user_prompt = f"Categories:\n{category_list}\n\nWebsite Content:\n{text}"

            # Call OpenAI API (v1.0+)
            result = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract and clean OpenAI response
            response_text = result.choices[0].message.content.strip()

            # Remove markdown code block formatting if present
            if response_text.startswith("```") and response_text.endswith("```"):
                lines = response_text.splitlines()
                response_text = "\n".join(line for line in lines if not line.strip().startswith("```"))

            # Try to parse the dictionary
            try:
                parsed_dict = ast.literal_eval(response_text)
            except Exception as e:
                st.error("⚠️ Failed to parse OpenAI response. Here's the raw output:")
                st.code(response_text, language="python")
            else:
                st.subheader("Categorization Table")

                # Build display data
                data = []
                for category, value in parsed_dict.items():
                    status, reasoning = value
                    if status == 1:
                        icon = "🟢"
                    elif status == 0:
                        icon = "🔴"
                    else:
                        icon = "⚪️"
                    data.append((icon, category, reasoning))

                # Show as table
                df = pd.DataFrame(data, columns=["Status", "Category", "Reasoning"])
                # Build HTML table with only Reasoning wrapped
                html = """
                <style>
                .custom-table {
                    font-size: 18px;
                    border-collapse: collapse;
                    width: 100%;
                    table-layout: auto;
                }
                .custom-table th {
                    background-color: #f2f2f2;
                    text-align: left;
                    white-space: nowrap;
                    padding: 8px;
                    font-weight: bold;
                    border: 1px solid #ddd;
                }
                .custom-table td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    vertical-align: top;
                }
                .custom-table td.reasoning {
                    white-space: normal;
                    word-break: break-word;
                }
                .custom-table td.status,
                .custom-table td.category {
                    white-space: nowrap;
                }
            </style>
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Category</th>
                        <th>Reasoning</th>
                    </tr>
                </thead>
                <tbody>
                """
                
                for row in data:
                    status, category, reasoning = row
                    html += f"<tr><td>{status}</td><td>{category}</td><td>{reasoning}</td></tr>"
                
                html += "</tbody></table>"
                
                st.markdown(html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")
