import streamlit as st
import google.generativeai as genai
import requests
from apikey import google_gemini_api_key, serpapi_key
from serpapi import GoogleSearch
import io
import re
import json
import datetime
import os

genai.configure(api_key=google_gemini_api_key)

RESTRICTED_TOPICS = [
    "sexual content", "sex", "rape", "harassment", "porn", "pornography",
    "sexual assault", "sexual violence", "nudity", "explicit content",
    "sexual abuse", "child abuse", "molestation", "incest"
]

def contains_restricted_content(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(topic in text_lower for topic in RESTRICTED_TOPICS)

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

LANGUAGES = {
    "en": {
        "dashboard": "Dashboard",
        "generate_blog": "Generate Blog",
        "blog_title": "Blog Title",
        "keywords": "Keywords (comma separated)",
        "custom_structure": "Custom Blog Structure (optional)",
        "tone_style": "Blog Tone & Style",
        "num_words": "Number of words",
        "blog_generated": "Blog generated!",
        "download_blog": "Download Blog as Text",
        "blog_history": "Blog History",
        "saved_blogs": "Saved Blogs",
        "view_blog": "View Blog",
        "no_blogs": "No blog history available.",
        "restricted": "Content generation restricted for this topic.",
        "fill_fields": "Please provide both blog title and keywords.",
        "your_blog": "Your Blog Post",
        "suggested_titles": "Suggested Blog Titles (with Links)",
    },
    "hi": {
        "dashboard": "डैशबोर्ड",
        "generate_blog": "ब्लॉग बनाएं",
        "blog_title": "ब्लॉग शीर्षक",
        "keywords": "कीवर्ड्स (कॉमा से पृथक)",
        "custom_structure": "कस्टम ब्लॉग संरचना (वैकल्पिक)",
        "tone_style": "ब्लॉग टोन और शैली",
        "num_words": "शब्दों की संख्या",
        "blog_generated": "ब्लॉग बन गया!",
        "download_blog": "ब्लॉग को टेक्स्ट में डाउनलोड करें",
        "blog_history": "ब्लॉग इतिहास",
        "saved_blogs": "सहेजे गए ब्लॉग",
        "view_blog": "ब्लॉग देखें",
        "no_blogs": "कोई ब्लॉग इतिहास नहीं है।",
        "restricted": "इस विषय के लिए सामग्री उत्पन्न करना सीमित है।",
        "fill_fields": "कृपया ब्लॉग शीर्षक और कीवर्ड्स दोनों प्रदान करें।",
        "your_blog": "आपका ब्लॉग पोस्ट",
        "suggested_titles": "शीर्षक सुझाव (लिंक सहित)",
    },
    "kn": {
        "dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "generate_blog": "ಬ್ಲಾಗ್ ರಚಿಸಿ",
        "blog_title": "ಬ್ಲಾಗ್ ಶೀರ್ಷಿಕೆ",
        "keywords": "ಕೀವರ್ಡ್‌ಗಳು (ಕಾಮಾ ಪ್ರತ್ಯೇಕಿಸಿ)",
        "custom_structure": "ಕಸ್ಟಮ್ ಬ್ಲಾಗ್ ರಚನೆ (ಐಚ್ಛಿಕ)",
        "tone_style": "ಬ್ಲಾಗ್ ಶೈಲಿ ಮತ್ತು ಧ್ವನಿ",
        "num_words": "ಪದಗಳ ಸಂಖ್ಯೆ",
        "blog_generated": "ಬ್ಲಾಗ್ ರಚನೆಗೂ ಮುಗಿಯಿತು!",
        "download_blog": "ಬ್ಲಾಗ್ ಟೆಕ್ಸ್ಟ್‌ವನ್ನಾಗಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
        "blog_history": "ಬ್ಲಾಗ್ ಇತಿಹಾಸ",
        "saved_blogs": "ಉಳಿಸಲಾಗಿದೆ ಬ್ಲಾಗ್‌ಗಳು",
        "view_blog": "ಬ್ಲಾಗ್ ನೋಡದ್ದು",
        "no_blogs": "ಯಾವುದೇ ಬ್ಲಾಗ್ ಇರೋದಿಲ್ಲ.",
        "restricted": "ಈ ವಿಷಯಕ್ಕೆ ವಿಷಯ ಸೃಷ್ಟಿ ನಿರ್ಬಂಧಿಸಲಾಗಿದೆ.",
        "fill_fields": "ದಯವಿಟ್ಟು ಬ್ಲಾಗ್ ಶೀರ್ಷಿಕೆ ಮತ್ತು ಕೀವರ್ಡ್‌ಗಳನ್ನು ನೀಡಿ.",
        "your_blog": "ನಿಮ್ಮ ಬ್ಲಾಗ್ ಪೋಸ್ಟ್",
        "suggested_titles": "ಶಿಫಾರಸು ಮಾಡಿದ ಶೀರ್ಷಿಕೆಗಳು (ಲಿಂಕ್‌ಗಳೊಡನೆ)",
    }
}

def t(key):
    return LANGUAGES.get(st.session_state.get("selected_lang", "en"), LANGUAGES["en"]).get(key, key)


def fetch_title_links(query, num_results=5):
    params = {
        "engine": "google",
        "q": query,
        "api_key": serpapi_key,
        "num": num_results,
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return [
            {"title": item["title"], "link": item["link"]}
            for item in results.get("organic_results", [])[:num_results]
            if "title" in item and "link" in item
        ]
    except Exception:
        return []

def fetch_images(query, num_images=2):
    if num_images == 0 or contains_restricted_content(query):
        return []
    params = {
        "engine": "google",
        "q": query,
        "tbm": "isch",
        "num": num_images,
        "api_key": serpapi_key
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "images_results" in results:
            return [img["original"] for img in results["images_results"][:num_images]]
        else:
            return []
    except:
        return []


st.set_page_config(page_title="BlogWiz - AI Blog Assistant", layout="wide")
st.title("🧙‍♂️ BlogWiz: Your AI Writing Companion")
st.write("Create blogs with AI — but your creativity makes it magical!")

if "selected_lang" not in st.session_state:
    st.session_state["selected_lang"] = "en"

lang_map = {"English": "en", "Hindi": "hi", "Kannada": "kn"}


with st.sidebar:
    blog_language = st.selectbox("Choose Blog Output Language", ["English", "Hindi", "Kannada"])
    blog_title = st.text_input(t("blog_title"))
    keywords = st.text_area(t("keywords"))
    num_words = st.slider(t("num_words"), 250, 1000, 250, 250)
    num_images = st.number_input("Number of images", 0, 5, 0)
    custom_structure = st.text_area(t("custom_structure"))
    tone = st.selectbox(t("tone_style"), ["Neutral", "Casual", "Professional", "Persuasive", "Witty"])
    submit_button = st.button("🪄 " + t("generate_blog"))


if submit_button:
    if not blog_title or not keywords:
        st.warning("Please provide both a blog title and keywords.")
    elif contains_restricted_content(blog_title) or contains_restricted_content(keywords):
        st.error("Content generation restricted for this topic.")
    else:
        image_instruction = f"Include {num_images} image references." if num_images > 0 else "Do not include images."
        prompt = f"""
        Generate a blog on: "{blog_title}"
        Keywords: {keywords}
        Word count: {num_words}
        Tone: {tone}
        {"Structure: " + custom_structure if custom_structure else ""}
        {image_instruction}
        Ensure it's engaging, informative, and avoids restricted content.
        """

        with st.spinner("Generating blog...✨"):
            try:
                response = model.generate_content(prompt)
                blog_english = response.text.strip()

                if contains_restricted_content(blog_english):
                    st.error("Content contains restricted material.")
                else:
                    st.success("Blog generated!")
                    st.subheader("Your Blog Post")

                    if blog_language != "English":
                        translate_prompt = f"Translate the following blog to {blog_language}:\n\n{blog_english}"
                        translated_response = model.generate_content(translate_prompt)
                        blog_display = translated_response.text.strip()
                        for kw in map(str.strip, keywords.split(",")):
                           if len(kw) > 1:
                            blog_display = re.sub(fr"(?i)\b({re.escape(kw)})\b", r"<u>\1</u>", blog_display)
                    else:
                        blog_display = blog_english
                        for kw in map(str.strip, keywords.split(",")):
                            if len(kw) > 1:
                             blog_display = re.sub(fr"(?i)\b({re.escape(kw)})\b", r"<u>\1</u>", blog_display)

                    st.markdown(blog_display, unsafe_allow_html=True)
                    st.session_state["blog_english"] = blog_english
                    st.session_state["blog_translated"] = blog_display
                    st.session_state["blog_title"] = blog_title

                    col1, col2 = st.columns(2)

                    with col1:
                        st.download_button(
                          "📄 Download English Blog",
                          io.BytesIO(st.session_state["blog_english"].encode("utf-8")),
                          file_name=f"{st.session_state['blog_title']}_English.txt"
                        )

                    with col2:
                        if blog_language != "English":
                          st.download_button(
                             f"🌐 Download in {blog_language}",
                             io.BytesIO(st.session_state["blog_translated"].encode("utf-8")),
                             file_name=f"{st.session_state['blog_title']}_{blog_language}.txt"
                          )




                    if num_images > 0:
                        st.subheader("Images")
                        for idx, img in enumerate(fetch_images(blog_title, num_images)):
                            st.image(img, caption=f"Image {idx+1}", width=400)


                    st.subheader("Suggested Reads (with Links)")
                    for item in fetch_title_links(blog_title):
                        st.markdown(f"🔗 [{item['title']}]({item['link']})")

            except Exception as e:
                st.error(f"Error: {e}")
