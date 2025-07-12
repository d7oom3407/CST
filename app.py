import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import ast
import pandas as pd

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["openai_api_key"])

# --- Language Toggle Styling and Layout Direction ---
st.markdown("""
<style>
.language-toggle {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}
.language-toggle button {
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-size: 1rem;
    border: none;
    cursor: pointer;
}
.language-selected {
    background-color: #ff4b4b;
    color: white;
}
.language-unselected {
    background-color: #f0f0f0;
    color: black;
}
/* Apply direction based on language */
body[data-dir="rtl"] {
    direction: rtl;
    text-align: right;
}
body[data-dir="ltr"] {
    direction: ltr;
    text-align: left;
}
</style>
<script>
const lang = window.parent.document.body.innerText.includes("العربية") ? "rtl" : "ltr";
document.body.setAttribute("data-dir", lang);
</script>
""", unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state.lang = "English"

st.markdown("""
    <style>
    .lang-container {
        display: flex;
        justify-content: flex-start;
        gap: 10px;
        margin-bottom: 1rem;
    }
    .lang-button {
        padding: 0.5rem 1.5rem;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1rem;
        font-weight: bold;
    }
    .selected {
        background-color: #ff4b4b;
        color: white;
    }
    .unselected {
        background-color: #f0f0f0;
        color: black;
    }
    </style>
    <div class="lang-container">
        <form action="" method="post">
            <button class="lang-button {english_class}" name="lang" value="English">English</button>
            <button class="lang-button {arabic_class}" name="lang" value="العربية">العربية</button>
        </form>
    </div>
""".replace("{english_class}", "selected" if st.session_state.lang == "English" else "unselected")
   .replace("{arabic_class}", "selected" if st.session_state.lang == "العربية" else "unselected"),
   unsafe_allow_html=True)

# Capture language selection manually
if st.session_state.get("_language_posted") is None:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    import streamlit as st_internal
    ctx = get_script_run_ctx()
    if ctx is not None and ctx.query_params:
        if "lang" in ctx.query_params:
            st.session_state.lang = ctx.query_params["lang"][0]
            st.session_state._language_posted = True


lang = st.session_state.lang

# Load categories and UI text based on language
if lang == "English":
    CATEGORIES = [
        "Emerging Technologies (Augmented/Virtual Reality)",
        "Emerging Technologies (Robotics)",
        "Emerging Technologies (Artificial Intelligence)",
        "Emerging Technologies (Internet of Things)",
        "Emerging Technologies (Distributed Ledger Technology)",
        "Emerging Technologies (Big Data)",
        "Emerging Technologies (3D Printing)",

        "IT Services (Consulting Services)",
        "IT Services (IT Services Management)",
        "IT Services (IT Staffing Services)",
        "IT Services (Cybersecurity Services)",
        "IT Services (Support and Maintenance)",
        "IT Services (Systems Integration and Development)",

        "Data Centers & Cloud Computing (Data Center Services including Web Hosting and Colocation)",
        "Data Centers & Cloud Computing (Infrastructure as a Service)",
        "Data Centers & Cloud Computing (Platform as a Service)",
        "Data Centers & Cloud Computing (Software as a Service)",
        "Data Centers & Cloud Computing (Other X-as-a-Service Products)",
        "Data Centers & Cloud Computing (Content Delivery Networks)",

        "Software (End-user Applications)",
        "Software (Game Applications)",
        "Software (Middleware and Embedded Software)",
        "Software (Business Software)",
        "Software (System Software)",

        "IT Hardware (Physical Devices)",
        "IT Hardware (Mobile Devices and Wearables)",
        "IT Hardware (Accessories)",
        "IT Hardware (Data Center Equipment)",
        "IT Hardware (Monitoring and Control Devices)",
        "IT Hardware (Network Hardware)",
        "IT Hardware (Other Devices)"
    ]
    ui = {
        "title": "Company Service Categorizer",
        "subtitle": "Enter the company's website and choose the service categories you want to evaluate.",
        "url_label": "Website URL",
        "select_label": "Select Categories to Evaluate",
        "categories_placeholder": "Choose Categories",
        "button": "Analyze Website",
        "warning": "Please provide a valid URL and select at least one category.",
        "result_title": "Categorization Results",
        "error_parse": "⚠️ Failed to parse OpenAI response. Here's the raw output:",
        "error_analyze": "An error occurred while analyzing:",
        "status": "Status",
        "category": "Category",
        "explanation": "Explanation",
        "system_prompt": (
            "You will receive the content of a company website and a list of service categories. "
            "Return a Python dictionary where each key is a category, and each value is a list of two elements: "
            "[1 or 0 or None, explanation]. "
            "Respond ONLY with a valid Python dictionary. Do NOT include any explanation or notes outside the dictionary."
        )
    }
else:
    CATEGORIES = [
        "التقنيات الناشئة (الواقع المعزز/ الواقع الافتراضي)",
        "التقنيات الناشئة (الروبوتات)",
        "التقنيات الناشئة (الذكاء الاصطناعي)",
        "التقنيات الناشئة (إنترنت الأشياء)",
        "التقنيات الناشئة (تقنية السجل الموزع)",
        "التقنيات الناشئة (البيانات الضخامة)",
        "التقنيات الناشئة (الطباعة الثلاثية الأبعاد)",

        "خدمات تقنية المعلومات (الخدمات الاستشارية)",
        "خدمات تقنية المعلومات (إدارة خدمات تقنية المعلومات)",
        "خدمات تقنية المعلومات (خدمات التوظيف الخاصة بتقنية المعلومات)",
        "خدمات تقنية المعلومات (خدمات الأمن السيبراني)",
        "خدمات تقنية المعلومات (الدعم والصيانة)",
        "خدمات تقنية المعلومات (تكامل الأنظمة والتطوير)",

        "خدمات مراكز البيانات والحوسبة السحابية (خدمات مراكز البيانات ومنها خدمات استضافة المواقع الإلكترونية والموقع المشترك)",
        "خدمات مراكز البيانات والحوسبة السحابية (البنية التحتية كخدمة)",
        "خدمات مراكز البيانات والحوسبة السحابية (المنصات كخدمة)",
        "خدمات مراكز البيانات والحوسبة السحابية (البرامج كخدمة)",
        "خدمات مراكز البيانات والحوسبة السحابية (منتجات أخرى كخدمة)",
        "خدمات مراكز البيانات والحوسبة السحابية (شبكات توصيل المحتوى)",

        "البرمجيات (تطبيقات المستخدم النهائي)",
        "البرمجيات (تطبيقات الألعاب)",
        "البرمجيات (البزامج الوسيطة والبرامج المضمنة)",
        "البرمجيات (برامج الأعمال)",
        "البرمجيات (برامج الأنظمة)",

        "أجهزة تقنية المعلومات (الأجهزة المادية)",
        "أجهزة تقنية المعلومات (الأجهزة المحمولة والتقنيات القابلة للارتداء)",
        "أجهزة تقنية المعلومات (الملحقات)",
        "أجهزة تقنية المعلومات (أجهزة مراكز البيانات)",
        "أجهزة تقنية المعلومات (أجهزة المراقبة والتحكم)",
        "أجهزة تقنية المعلومات (أجهزة الشبكات الحاسوبية)",
        "أجهزة تقنية المعلومات (أجهزة أخرى)"
    ]
    ui = {
        "title": "تصنيف خدمات الشركات التقنية",
        "subtitle": "أدخل رابط موقع الشركة واختر التصنيفات التي تريد تحليلها.",
        "url_label": "رابط الموقع الإلكتروني",
        "select_label": "اختر التصنيفات التي ترغب بتحليلها",
        "categories_placeholder": "أختر التصنيفات",
        "button": "تحليل الموقع",
        "warning": "يرجى إدخال رابط صحيح واختيار تصنيف واحد على الأقل.",
        "result_title": "نتائج التصنيف",
        "error_parse": "تعذر تحويل استجابة النموذج. إليك النص كما هو:",
        "error_analyze": "حدث خطأ أثناء التحليل:",
        "status": "الحالة",
        "category": "التصنيف",
        "explanation": "التفسير",
        "system_prompt": (
            "سيتم تزويدك بمحتوى موقع إلكتروني تابع لشركة، بالإضافة إلى قائمة من التصنيفات. "
            "مهمتك هي تحديد ما إذا كانت الشركة تقدم هذه التصنيفات من خدمات أم لا. "
            "أرجو أن تعيد الرد بشكل قاموسي (dictionary) يحتوي على كل تصنيف كمفتاح، "
            "وقيمته قائمة مكونة من عنصرين: [1 أو 0 أو None، التفسير]. "
            "الرجاء إعادة الرد على شكل قاموس بايثون فقط بدون أي شرح خارجي أو تعليقات."
        )
    }

# Apply direction based on language
direction = "rtl" if lang == "العربية" else "ltr"
st.markdown(f"""
    <style>
    html, body, [class*="css"] {{
        direction: {direction};
        text-align: { 'right' if direction == 'rtl' else 'left' };
    }}
    .stDataFrame div[data-testid="stHorizontalBlock"] {{
        direction: ltr; /* Keep tables LTR for consistency */
    }}
    </style>
""", unsafe_allow_html=True)


# UI
st.set_page_config(page_title=ui["title"], layout="wide")
st.title(ui["title"])
st.write(ui["subtitle"])
url = st.text_input(ui["url_label"], placeholder="https://example.com")
selected_categories = st.multiselect(ui["select_label"], CATEGORIES, placeholder=ui["categories_placeholder"])

if st.button(ui["button"]):
    if not url or not selected_categories:
        st.warning(ui["warning"])
    else:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            category_list = "\n".join(f"{i+1}- {cat}" for i, cat in enumerate(selected_categories))
            user_prompt = f"Categories:\n{category_list}\n\nWebsite Content:\n{text}"

            result = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": ui["system_prompt"]},
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = result.choices[0].message.content.strip()
            if response_text.startswith("```") and response_text.endswith("```"):
                lines = response_text.splitlines()
                response_text = "\n".join(line for line in lines if not line.strip().startswith("```") or line.strip() == "```")

            try:
                parsed_dict = ast.literal_eval(response_text)
            except Exception:
                st.error(ui["error_parse"])
                st.code(response_text, language="python")
            else:
                st.subheader(ui["result_title"])
                data = []
                for category, value in parsed_dict.items():
                    status, reason = value
                    icon = "🟢" if status == 1 else "🔴" if status == 0 else "⚪️"
                    data.append((icon, category, reason))

                df = pd.DataFrame(data, columns=[ui['status'], ui['category'], ui['explanation']])
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"{ui['error_analyze']} {e}")
