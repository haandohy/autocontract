import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(layout="wide")
st.title("근로계약서 자동 작성 앱 📝")

# --- 막대 바와 숫자 입력칸을 완벽하게 묶어주는 마법의 함수 ---
def slider_with_input(label, min_v, max_v, default_v, key):
    slider_key = f"{key}_slider"
    num_key = f"{key}_num"
    
    # 1. 처음 켜졌을 때 초기값 세팅
    if slider_key not in st.session_state:
        st.session_state[slider_key] = default_v
    if num_key not in st.session_state:
        st.session_state[num_key] = default_v
        
    # 2. 막대바를 드래그하면 -> 숫자 입력칸 값을 바꿈
    def sync_from_slider():
        st.session_state[num_key] = st.session_state[slider_key]
        
    # 3. 숫자 입력칸에 타자를 치면 -> 막대바 위치를 바꿈
    def sync_from_num():
        st.session_state[slider_key] = st.session_state[num_key]

    st.markdown(f"<p style='margin-bottom:0px;'><b>{label}</b></p>", unsafe_allow_html=True)
    
    # 나란히 배치
    col1, col2 = st.columns([3, 1])
    with col1:
        st.slider(label, min_v, max_v, key=slider_key, on_change=sync_from_slider, label_visibility="collapsed")
    with col2:
        st.number_input(label, min_v, max_v, key=num_key, on_change=sync_from_num, label_visibility="collapsed")
        
    return st.session_state[slider_key]

# --- 좌측 사이드바: 묶음 컨트롤러 ---
with st.sidebar:
    st.header("🎯 위치 실시간 조정")
    st.info("왼쪽 막대를 드래그하거나, 오른쪽 빈칸에 타자를 치면 서로 똑같이 움직입니다!")

    st.subheader("1. 상단 빈칸")
    name_top_x = slider_with_input("이름 가로 (X)", 0, 1000, 290, "name_x")
    name_top_y = slider_with_input("이름 세로 (Y)", 0, 1200, 205, "name_y")

    st.subheader("2. 하단 정보 그룹 (기준: 주소)")
    bottom_x = slider_with_input("전체 그룹 가로 (X)", 0, 1000, 166, "bot_x")
    bottom_y = slider_with_input("전체 그룹 세로 (Y)", 0, 1200, 808, "bot_y")

    st.subheader("3. 미세 간격 세팅")
    line_spacing = slider_with_input("줄 간격", 10, 100, 29, "line_s")
    sig_offset_x = slider_with_input("서명 우측 간격", 0, 500, 84, "sig_x")
    sig_offset_y = slider_with_input("서명 상하 간격", -100, 100, 42, "sig_y")

# --- 본문 화면 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. 정보 입력")
    name = st.text_input("성명", "한도현")
    address = st.text_input("주소", "서울시 송파구 위례순환로 477 2310동 402호")
    phone = st.text_input("연락처", "010-4562-1724")
    signature_file = st.file_uploader("2. 서명 이미지 업로드 (JPG/PNG)", type=["png", "jpg", "jpeg"])

template_path = "근로계약서.png" 

with col2:
    st.header("3. 실시간 미리보기")
    if signature_file is not None:
        # 서명 투명화 처리
        file_bytes = np.asarray(bytearray(signature_file.read()), dtype=np.uint8)
        sig_img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
        _, mask = cv2.threshold(sig_img, 200, 255, cv2.THRESH_BINARY_INV)
        sig_rgba = cv2.cvtColor(sig_img, cv2.COLOR_GRAY2BGRA)
        sig_rgba[:, :, 3] = mask
        signature = Image.fromarray(cv2.cvtColor(sig_rgba, cv2.COLOR_BGRA2RGBA))
        signature = signature.resize((70, 35))

        template = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(template)
        
        try:
            font = ImageFont.truetype("malgun.ttf", 13)
        except IOError:
            font = ImageFont.load_default()

        # [1] 상단 이름
        draw.text((name_top_x, name_top_y), name, font=font, fill=(0, 0, 0))
        
        # [2] 하단 정보 (기준점 bottom_y에 line_spacing을 더해 자동으로 줄맞춤)
        draw.text((bottom_x, bottom_y), address, font=font, fill=(0, 0, 0)) 
        draw.text((bottom_x, bottom_y + line_spacing), phone, font=font, fill=(0, 0, 0))   
        
        name_final_y = bottom_y + (line_spacing * 2)
        draw.text((bottom_x, name_final_y), name, font=font, fill=(0, 0, 0))    
        
        # [3] 서명 (성명 위치를 기준으로 함께 따라다님)
        sig_final_x = bottom_x + sig_offset_x
        sig_final_y = name_final_y + sig_offset_y
        template.paste(signature, (sig_final_x, sig_final_y), signature)

        # 결과물 화면 출력
        final_image = template.convert("RGB")
        st.image(final_image, caption="막대와 숫자가 완벽하게 연동됩니다. 직접 움직여보세요!", use_container_width=True)

        buf = io.BytesIO()
        final_image.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(label="완성본 다운로드", data=byte_im, file_name="완성된_근로계약서.png", mime="image/png")
    else:
        st.info("좌측에 서명 이미지를 업로드하면 미리보기가 나타납니다.")
