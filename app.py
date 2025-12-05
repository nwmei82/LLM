import streamlit as st
import base64
import time
import json
import re
import google.generativeai as genai

# ==========================================
# 1. CONFIGURATION & CONSTANTS
# ==========================================
PAGE_TITLE = "Career Roadmap AI"
PAGE_ICON = "🚀"
# ⚠️⚠️ ใส่ API KEY ของคุณตรงนี้ ⚠️⚠️
API_KEY = API_KEY

# รายชื่อ Model ที่จะลองเรียกใช้ (ถ้าตัวแรกไม่ได้ จะลองตัวถัดไป)
AVAILABLE_MODELS = [
    "gemini-2.5-flash-preview-09-2025",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro"
]

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

# ตั้งค่า Google AI (Configuration only)
try:
    genai.configure(api_key=API_KEY.strip())
except Exception as e:
    st.error(f"⚠️ API Configuration Error: {e}")


# ==========================================
# 2. UTILITY FUNCTIONS (SERVICES)
# ==========================================

def load_image_as_base64(file_path):
    """อ่านไฟล์รูปภาพและแปลงเป็น Base64 string"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def fetch_career_roadmap_from_ai(career_name):
    """ส่งคำสั่งไปยัง Google Gemini เพื่อขอ Roadmap (พร้อมระบบ Auto-Retry โมเดลอื่น)"""
    
    # Prompt Template
    prompt = f"""
    You are an expert Career Coach. Create a detailed 3-month study roadmap for "{career_name}" in Thai language.

    IMPORTANT: You must return the result as a valid JSON Object ONLY.
    Do not add any markdown formatting like ```json or ```. Just the raw JSON string.

    The JSON structure must be exactly like this (nested structure):
    {{
        "month1": {{
            "theme": "สรุปเป้าหมายหลักของเดือนที่ 1 (สั้นๆ)",
            "weeks": [
                {{ "week": "สัปดาห์ที่ 1", "topic": "ชื่อหัวข้อที่เรียน", "desc": "คำอธิบายสั้นๆ และหัวข้อการบ้าน/โปรเจกต์", "link": "https://www.youtube.com/results?search_query=..." }},
                ... (make sure to have 4 weeks)
            ]
        }},
        "month2": {{
            "theme": "สรุปเป้าหมายหลักของเดือนที่ 2",
            "weeks": [ ...4 weeks... ]
        }},
        "month3": {{
            "theme": "สรุปเป้าหมายหลักของเดือนที่ 3",
            "weeks": [ ...4 weeks... ]
        }}
    }}

    Ensure the content is practical for beginners and includes homework/project ideas in the description.
    """

    last_error = None
    
    # 🔄 Loop ลองใช้โมเดลทีละตัวจากรายการ
    for model_name in AVAILABLE_MODELS:
        try:
            # สร้าง Model Object ภายใน loop
            model = genai.GenerativeModel(model_name)
            
            # ลองเรียก API
            response = model.generate_content(prompt)
            text = response.text

            # ถ้าสำเร็จ: Extract JSON
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                print(f"✅ Success with model: {model_name}") # Log success (optional)
                return json.loads(match.group(0)), None
            else:
                return None, f"AI Response Format Error ({model_name}): {text[:100]}..."

        except Exception as e:
            # ถ้า Error ให้เก็บ Error ล่าสุดไว้ แล้วลองตัวถัดไป
            print(f"⚠️ Failed with model {model_name}: {e}")
            last_error = e
            continue  # ลองตัวถัดไป
    
    # ถ้าลองทุกตัวแล้วยังไม่ได้
    return None, f"All models failed. Last error: {last_error}"

def create_roadmap_html(data, career_name):
    """สร้าง HTML String สำหรับดาวน์โหลดและ Print เป็น PDF"""
    month1 = data.get('month1', {})
    month2 = data.get('month2', {})
    month3 = data.get('month3', {})

    def get_weeks_html(weeks):
        html = ""
        for i, item in enumerate(weeks):
            link = item.get('link', '#')
            html += f"""
            <div class="week-item">
                <span class="week-title">🗓 {item['week']}: {item['topic']}</span>
                <span class="week-desc">{item['desc']}</span><br>
                <a class="week-link" href="{link}" target="_blank">🔗 แหล่งข้อมูล / โปรเจกต์</a>
            </div>"""
            if i < len(weeks) - 1:
                html += '<div class="dashed-line"></div>'
        return html

    html_content = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>Roadmap: {career_name}</title>
        <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Prompt', sans-serif; background-color: #f8f9fa; padding: 40px; color: #2d3436; }}
            h1 {{ text-align: center; color: #2d3436; margin-bottom: 5px; }}
            h3 {{ text-align: center; color: #636e72; font-weight: 300; margin-bottom: 40px; }}
            
            .container {{ display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; }}
            .column {{ flex: 1; min-width: 300px; max-width: 400px; }}
            
            .month-header {{ text-align: center; font-size: 20px; font-weight: 600; margin-bottom: 15px; color: #000; }}
            .circle-badge {{ display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; background: #fff; text-align: center; font-weight: bold; margin-left: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid #ddd; }}
            
            .card-box {{
                background: #fff; border-radius: 20px; padding: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.05);
                height: 100%; page-break-inside: avoid;
            }}
            .bg-month-1 {{ background: linear-gradient(135deg, #FFF6E5 0%, #FFF0D4 100%); }}
            .bg-month-2 {{ background: linear-gradient(135deg, #E3F2FD 0%, #E1F5FE 100%); }}
            .bg-month-3 {{ background: linear-gradient(135deg, #F3E5F5 0%, #EDE7F6 100%); }}
            
            .theme-title {{ font-size: 18px; font-weight: 600; text-align: center; margin-bottom: 20px; min-height: 50px; display: flex; align-items: center; justify-content: center; }}
            
            .week-item {{ margin-bottom: 15px; font-size: 14px; line-height: 1.6; }}
            .week-title {{ font-weight: 600; display: block; margin-bottom: 4px; color: #2d3436; }}
            .week-desc {{ color: #636e72; }}
            .week-link {{ display: inline-block; margin-top: 5px; color: #0984e3; text-decoration: none; font-size: 13px; background: rgba(255,255,255,0.5); padding: 2px 8px; border-radius: 8px; }}
            .dashed-line {{ border-top: 1px dashed rgba(0,0,0,0.1); margin: 15px 0; }}
            
            @media print {{
                body {{ padding: 20px; background: #fff; }}
                .container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }}
                .column {{ max-width: none; }}
                .card-box {{ box-shadow: none; border: 1px solid #ccc; }}
                /* บังคับให้พิมพ์สีพื้นหลัง */
                .bg-month-1, .bg-month-2, .bg-month-3 {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body>
        <h1>🎯 Roadmap: {career_name}</h1>
        <h3>Personalized 3-Month Study Plan</h3>
        
        <div class="container">
            <!-- Month 1 -->
            <div class="column">
                <div class="month-header">MONTH <span class="circle-badge">1</span></div>
                <div class="card-box bg-month-1">
                    <div class="theme-title">{month1.get('theme', '')}</div>
                    <div class="content">{get_weeks_html(month1.get('weeks', []))}</div>
                </div>
            </div>
            
            <!-- Month 2 -->
            <div class="column">
                <div class="month-header">MONTH <span class="circle-badge">2</span></div>
                <div class="card-box bg-month-2">
                    <div class="theme-title">{month2.get('theme', '')}</div>
                    <div class="content">{get_weeks_html(month2.get('weeks', []))}</div>
                </div>
            </div>
            
            <!-- Month 3 -->
            <div class="column">
                <div class="month-header">MONTH <span class="circle-badge">3</span></div>
                <div class="card-box bg-month-3">
                    <div class="theme-title">{month3.get('theme', '')}</div>
                    <div class="content">{get_weeks_html(month3.get('weeks', []))}</div>
                </div>
            </div>
        </div>
        
        <div style="text-align:center; margin-top: 30px; font-size: 12px; color: #aaa;">
            Generated by Career Roadmap AI
        </div>
    </body>
    </html>
    """
    return html_content


# ==========================================
# 3. UI & STYLING FUNCTIONS
# ==========================================

def load_custom_css():
    """โหลด CSS ทั้งหมดของแอป"""
    st.markdown("""
    <style>
        /* Import Font: Prompt */
        @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');

        /* Global Reset */
        * {
            box-sizing: border-box;
        }

        html, body, [class*="css"] {
            font-family: 'Prompt', sans-serif;
        }

        /* ซ่อน Header/Footer ของ Streamlit */
        header, [data-testid="stHeader"], footer { display: none !important; }
        
        /* ปรับ Padding คอนเทนเนอร์หลัก */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 5rem !important;
        }

         /* --- Input Box Styling (Aggressive Border Removal) --- */
        
        /* Target input container wrappers */
        div[data-testid="stForm"]{
            border: none;
        }
        div[data-baseweb="input"], 
        div[data-baseweb="base-input"] {
            background-color: #ffffff !important;
            border-radius: 50px !important;
            padding: 8px 20px !important;
            
            /* FORCE REMOVE BORDER */
            border: 0px solid transparent !important;
            border-color: transparent !important;
            
            /* Add shadow instead of border */
        }

        /* Target Focus state to remove blue outline/border */
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="base-input"]:focus-within {
            border: 0px solid transparent !important;
            border-color: transparent !important;
            outline: none !important;
        }

        /* Target the actual input element */
        input[class] { 
            color: #2d3436 !important; 
            font-size: 1.1rem !important; 
            background-color: transparent !important;
        }

        /* --- Button Styling (Aggressive Border Removal) --- */
        div[data-testid="stFormSubmitButton"] button {
            border-radius: 50px !important;
            background: linear-gradient(135deg, #7F5AF0 0%, #6246EA 100%) !important;
            color: white !important;
            
            /* FORCE REMOVE BORDER */
            border: 0px solid transparent !important;
            border-color: transparent !important;
            outline: none !important;
            
            padding: 12px 30px !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
            box-shadow: 0 5px 15px rgba(98, 70, 234, 0.3) !important;
            transition: all 0.2s ease;
        }
        
        div[data-testid="stFormSubmitButton"] button:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 20px rgba(98, 70, 234, 0.4) !important;
            border: 0px solid transparent !important;
        }
        
        div[data-testid="stFormSubmitButton"] button:active,
        div[data-testid="stFormSubmitButton"] button:focus {
            border: 0px solid transparent !important;
            outline: none !important;
        }

        /* Loading Container */
        .loading-container {
            display: flex; justify-content: center; align-items: center;
            height: 60vh; flex-direction: column;
            animation: fadeIn 0.8s ease;
        }

        /* --- Column Fix for Text Overflow --- */
        [data-testid="column"] {
            min-width: 0 !important; /* Critical for wrapping */
            flex: 1 1 0 !important;
        }

        /* --- Card & Layout Styling --- */
        .month-header {
            font-family: 'Prompt', sans-serif; font-size: 20px; font-weight: 600;
            text-align: center; margin-bottom: 15px; color: #000000;
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }
        

        /* Modern Card Box Structure */
        .card-box {
            border-radius: 24px; 
            padding: 30px 25px; /* เพิ่ม Padding เล็กน้อย */
            box-shadow: 0 10px 30px rgba(0,0,0,0.04);
            border: 1px solid rgba(255,255,255,0.8);
            color: #2d3436;
            font-family: 'Prompt', sans-serif;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            
            /* 🔥 FIX: Equal Height & Layout 🔥 */
            min-height: 320px; /* ความสูงขั้นต่ำให้เท่ากัน */
            height: 100%;
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between; /* ดันเนื้อหาบนล่างแยกกัน */
        }
        .card-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.08);
            z-index: 5;
        }

        /* Style สำหรับหัวข้อ Theme หลักของเดือน */
        .month-theme-title {
            text-align: center; 
            font-size: 18px; 
            font-weight: 600;
            color: #2d3436; 
            margin-bottom: 20px; 
            
            /* Center Content Vertically in available space */
            flex-grow: 1; /* ให้ขยายเต็มพื้นที่ว่าง */
            display: flex; 
            align-items: center; 
            justify-content: center;
            
            /* FORCE TEXT WRAP */
            width: 100%;
            white-space: normal !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
            line-height: 1.5;
        }

        /* Soft Pastel Gradients for Backgrounds */
        .bg-month-1 { background: linear-gradient(135deg, #FFF6E5 0%, #FFF0D4 100%); }
        .bg-month-2 { background: linear-gradient(135deg, #E3F2FD 0%, #E1F5FE 100%); }
        .bg-month-3 { background: linear-gradient(135deg, #F3E5F5 0%, #EDE7F6 100%); }

        /* List Items (รายละเอียดรายสัปดาห์) */
        .week-item { 
            margin-bottom: 15px; 
            font-size: 14px; 
            line-height: 1.6; 
            color: #636e72; 
            
            /* FORCE TEXT WRAP */
            width: 100%;
            display: block;
            white-space: normal !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
        }
        
        .week-title { 
            font-weight: 600; 
            display: block; 
            color: #2d3436; 
            margin-bottom: 6px; 
            font-size: 15px;
            
            /* FORCE TEXT WRAP */
            white-space: normal !important;
            overflow-wrap: anywhere !important;
        }

        .week-link a {
            color: #0984e3; 
            text-decoration: none; 
            font-size: 13px; 
            font-weight: 500;
            background-color: rgba(255,255,255,0.6); 
            padding: 4px 12px; 
            border-radius: 12px;
            display: inline-block; 
            margin-top: 6px;
            transition: all 0.2s;
            border: 1px solid rgba(0,0,0,0.05);
        }
        .week-link a:hover {
            background-color: #fff;
            box-shadow: 0 4px 10px rgba(9, 132, 227, 0.15);
            transform: translateY(-1px);
        }
        
        /* Dashed Line Styling */
        .dashed-line {
            border-top: 1px dashed rgba(0,0,0,0.15);
            margin: 15px 0;
        }

        /* --- HTML Details/Summary Styling (Replacement for Expander) --- */
        details {
            width: 100%;
            margin-top: auto; /* ดันไปล่างสุด */
            background-color: rgba(255,255,255,0.4);
            border-radius: 16px;
            padding: 10px;
        }
        
        summary {
            cursor: pointer;
            font-weight: 600;
            color: #6c5ce7;
            list-style: none; /* Hide default arrow */
            outline: none;
            text-align: center; /* จัดกึ่งกลางปุ่ม */
        }
        summary::-webkit-details-marker {
            display: none; /* Hide default arrow in Webkit */
        }
        summary:hover {
            color: #5a4ad1;
        }

        /* Title Styling */
        .main-title {
            font-family: 'Prompt', sans-serif;
            text-align: center; color: #000000; margin: 0;
            font-weight: bold;
            font-size: 3rem;
        }
        .sub-title {
            font-family: 'Prompt', sans-serif;
            text-align: center; color: #000000; font-weight: 300; font-size: 1.2rem; margin-top: 10px;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    """, unsafe_allow_html=True)

def set_background_image(image_file):
    """ตั้งค่ารูปพื้นหลัง"""
    bin_str = load_image_as_base64(image_file)
    if bin_str:
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Overlay for better readability if BG is busy */
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255, 255, 255, 0.4);
            z-index: -1;
        }}
        </style>
        """, unsafe_allow_html=True)

# ฟังก์ชันใหม่สำหรับวาดการ์ดโดยใช้ Streamlit components
# 🔥🔥🔥 UPDATED: ใช้ HTML ล้วนๆ แทนการผสม st.expander เพื่อแก้ปัญหา Layout พัง 🔥🔥🔥
def draw_month_card(st_column, month_data, bg_class, month_num):
    """วาดการ์ดเดือนลงในคอลัมน์ที่กำหนด (ใช้ HTML Structure ทั้งหมด)"""
    if not month_data: return

    with st_column:
        # เตรียม HTML ของเนื้อหาข้างใน (Weeks)
        weeks_html = ""
        weeks = month_data.get("weeks", [])
        for i, item in enumerate(weeks):
            link = item.get('link', '#')
            # สร้าง HTML สำหรับแต่ละสัปดาห์ (ลบ indentation ออกให้หมด)
            weeks_html += f"""<div class="week-item"><span class="week-title">{item['week']}: {item['topic']}</span><span style="font-size:13px; color:#636e72;">{item['desc']}</span><br><span class="week-link"><a href="{link}" target="_blank">🔗 แหล่งข้อมูล / โปรเจกต์</a></span></div>"""
            # เพิ่มเส้นคั่น ยกเว้นตัวสุดท้าย
            if i < len(weeks) - 1:
                weeks_html += '<div class="dashed-line"></div>'

        # สร้าง HTML ของการ์ดทั้งใบ (รวม Title + Details)
        # ใช้ <details> แทน st.expander เพื่อให้ทุกอย่างอยู่ใน div เดียวกันจริงๆ
        # ⚠️⚠️ สำคัญ: ต้องเขียน HTML ให้ชิดซ้าย (No Indentation) เพื่อไม่ให้ Markdown แปลงเป็น Code Block ⚠️⚠️
        full_card_html = f"""
<div class="month-header">MONTH <span class="circle-badge">{month_num}</span></div>
<div class="card-box {bg_class}">
    <div class="month-theme-title">{month_data.get("theme", f"เป้าหมายเดือนที่ {month_num}")}</div>
    <details>
        <summary>👇 ดูรายละเอียด & การบ้าน</summary>
        <div style="margin-top: 15px; animation: fadeIn 0.3s ease; text-align: left;">
            {weeks_html}
        </div>
    </details>
</div>
"""
        
        st.markdown(full_card_html, unsafe_allow_html=True)


# ==========================================
# 4. STATE MANAGEMENT & CALLBACKS
# ==========================================

def init_session_state():
    """กำหนดค่าเริ่มต้นให้กับ Session State"""
    defaults = {
        "page": "search",
        "result_data": None,
        "career_query": "",
        "error_message": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def cb_start_search():
    """Callback เมื่อกดปุ่มค้นหา"""
    st.session_state.page = "loading"
    st.session_state.error_message = None
    st.session_state.career_query = st.session_state.user_input

def cb_reset():
    """Callback เมื่อกดปุ่มเริ่มใหม่"""
    st.session_state.page = "search"
    st.session_state.result_data = None
    st.session_state.error_message = None
    st.session_state.career_query = ""


# ==========================================
# 5. PAGE RENDERERS
# ==========================================

def render_search_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Level Up Your Skill 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='sub-title'>Create a 3-month personalized roadmap for your dream career</h3>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.error_message:
            st.error(f"❌ {st.session_state.error_message}")

        with st.form("search_form"):
            st.text_input("", placeholder="Data Scientist, UX Designer", label_visibility="collapsed", key="user_input")
            
            # ใช้ column เพื่อจัดปุ่มให้อยู่ตรงกลางสวยๆ
            b1, b2, b3 = st.columns([1, 1, 1])
            with b2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.form_submit_button("Generate Roadmap ✨", use_container_width=True, on_click=cb_start_search)

def render_loading_page():
    # แสดง Loading Animation
    gif_base64 = load_image_as_base64("loading.webp")
    if gif_base64:
        st.markdown(f"""
        <div class="loading-container">
            <img src="data:image/webp;base64,{gif_base64}" width="180">
            <h3 style="color:#000; margin-top: 30px; font-weight: 500;">AI is crafting your roadmap...</h3>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Loading...")

    # หน่วงเวลาเล็กน้อยเพื่อให้ UI แสดงผลก่อนเริ่มประมวลผล
    time.sleep(1)

    # เรียก AI
    data, error = fetch_career_roadmap_from_ai(st.session_state.career_query)

    # อัปเดตสถานะและเปลี่ยนหน้า
    if error:
        st.session_state.error_message = error
        st.session_state.page = "search"
    else:
        st.session_state.result_data = data
        st.session_state.page = "result"

    st.rerun()

def render_result_page():
    data = st.session_state.result_data
    career = st.session_state.career_query

    if data:
        st.markdown(f"<h2 style='text-align:center; margin-bottom: 40px; color:#2d3436; font-weight: 700;'>🎯 Roadmap: {career}</h2>", unsafe_allow_html=True)

        # สร้าง 3 คอลัมน์
        c1, c2, c3 = st.columns(3)

        # เรียกใช้ฟังก์ชันวาดการ์ดใหม่ โดยส่งคอลัมน์เข้าไป
        draw_month_card(c1, data.get('month1'), 'bg-month-1', '1')
        draw_month_card(c2, data.get('month2'), 'bg-month-2', '2')
        draw_month_card(c3, data.get('month3'), 'bg-month-3', '3')

        # === ส่วนปุ่ม Download ===
        st.markdown("<br><br>", unsafe_allow_html=True)
        col_dl_1, col_dl_2, col_dl_3 = st.columns([1, 2, 1])
        with col_dl_2:
            html_data = create_roadmap_html(data, career)
            st.download_button(
                label="📥 ดาวน์โหลด Roadmap เพื่อบันทึกเป็น PDF",
                data=html_data,
                file_name=f"roadmap_{career}.html",
                mime="text/html",
                use_container_width=True
            )
            st.caption("ℹ️ วิธีบันทึกเป็น PDF: เปิดไฟล์ที่ดาวน์โหลด > กด Ctrl+P (หรือ Cmd+P) > เลือก 'Save as PDF' (บันทึกเป็น PDF)")

    # ปุ่ม Reset
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.button("🔍 ค้นหาอาชีพอื่น", use_container_width=True, on_click=cb_reset)


# ==========================================
# 6. MAIN APP FLOW
# ==========================================

def main():
    # 1. Initialize
    init_session_state()
    load_custom_css()
    # ตรวจสอบว่าไฟล์พื้นหลังและไฟล์ loading มีอยู่จริง
    set_background_image('bg.jpg')

    # 2. Page Router
    if st.session_state.page == "search":
        render_search_page()
    elif st.session_state.page == "loading":
        render_loading_page()
    elif st.session_state.page == "result":
        render_result_page()

if __name__ == "__main__":
    main()