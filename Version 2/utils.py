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
        "font_style": "Font Style",
        "font_size": "Font Size",
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
    }
}

def t(key):
    return LANGUAGES["en"].get(key, key)


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
    except:
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
        return [img["original"] for img in results.get("images_results", [])[:num_images]]
    except:
        return []

st.set_page_config(page_title="BlogWiz - AI Blog Assistant", layout="wide")
st.title("🧙‍♂️ BlogWiz: Your AI Writing Companion")
st.write("Create blogs with AI — but your creativity makes it magical!")

if "selected_lang" not in st.session_state:
    st.session_state["selected_lang"] = "en"

lang_map = {"English": "en", "Hindi": "hi", "Kannada": "kn"}

with st.sidebar:
    output_lang_ui = st.selectbox("Choose Blog Output Language", ["English", "Hindi", "Kannada"])
    blog_title = st.text_input(t("blog_title"))
    keywords = st.text_area(t("keywords"))
    num_words = st.slider(t("num_words"), 250, 1000, 250, 250)
    num_images = st.number_input("Number of images", 0, 5, 0)
    custom_structure = st.text_area(t("custom_structure"))
    tone = st.selectbox(t("tone_style"), ["Neutral", "Casual", "Professional", "Persuasive", "Witty"])
    font_style = st.selectbox(t("font_style"), ["Arial", "Poppins", "Nunito", "Roboto", "Courier New"])
    font_size = st.slider(t("font_size"), 12, 48, 16)
    submit_button = st.button("✨" + t("generate_blog"))

if submit_button:
    if not blog_title or not keywords:
        st.warning(t("fill_fields"))
    elif contains_restricted_content(blog_title) or contains_restricted_content(keywords):
        st.error(t("restricted"))
    else:
        image_instruction = f"Include {num_images} image references." if num_images > 0 else "Do not include images."
        prompt = f"""
        Generate a blog on: \"{blog_title}\"
        Keywords: {keywords}
        Word count: {num_words}
        Tone: {tone}
        {"Structure: " + custom_structure if custom_structure else ""}
        {image_instruction}
        Ensure it's engaging, informative, and avoids restricted content.
        """

        with st.spinner("Generating blog..."):
            try:
                response = model.generate_content(prompt)
                blog_english = response.text.strip()

                if contains_restricted_content(blog_english):
                    st.error(t("restricted"))
                else:
                    st.success(t("blog_generated"))

                    if output_lang_ui != "English":
                        translation_prompt = f"Translate this blog to {output_lang_ui}:\n\n{blog_english}"
                        translation = model.generate_content(translation_prompt).text.strip()
                        blog_translated = translation
                    else:
                        blog_translated = blog_english

                    blog_display = re.sub(fr"^##+\s*{re.escape(blog_title)}.*\n?", "", blog_translated, flags=re.IGNORECASE | re.MULTILINE)
                    blog_display = re.sub(fr"^{re.escape(blog_title)}\s*:\s*.*\n?", "", blog_display, flags=re.IGNORECASE | re.MULTILINE)

                    for kw in map(str.strip, keywords.split(",")):
                       if len(kw) > 1:
                            try:
                              pattern = re.escape(kw)
                              blog_display = re.sub(pattern, rf"<u><b>{kw}</b></u>", blog_display, flags=re.IGNORECASE)
                            except:
                              pass
  

                    styled_blog = f"""
                    <h2 style='font-family:{font_style}; font-size:{font_size + 4}px; color:#3c3c3c'><b>{blog_title}</b></h2>
                    <div style='font-family:{font_style}; font-size:{font_size}px; line-height:1.7'>{blog_display}</div>
                    """
                    st.markdown(styled_blog, unsafe_allow_html=True)

                    st.session_state["blog_english"] = blog_english
                    st.session_state["blog_translated"] = blog_translated
                    st.session_state["blog_title"] = blog_title

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📄 Download English Blog",
                            io.BytesIO(blog_english.encode("utf-8")),
                            file_name=f"{blog_title}_English.txt"
                        )
                    with col2:
                        st.download_button(
                            f"🌐 Download in {output_lang_ui}",
                            io.BytesIO(blog_translated.encode("utf-8")),
                            file_name=f"{blog_title}_{output_lang_ui}.txt"
                        )

                    if num_images > 0:
                        st.subheader("Images")
                        for idx, img_url in enumerate(fetch_images(blog_title, num_images)):
                            st.image(img_url, caption=f"Image {idx+1}", width=600)

                    st.subheader(t("suggested_titles"))
                    for item in fetch_title_links(blog_title):
                        st.markdown(f"🔗 [{item['title']}]({item['link']})")

            except Exception as e:
                st.error(f"Error generating blog: {e}")
