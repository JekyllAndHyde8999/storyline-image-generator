import requests
import streamlit as st
import zipfile
import io
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_cohere import ChatCohere
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper

load_dotenv()

# llm = ChatOpenAI(model="gpt-3.5-turbo")
llm = ChatCohere(model="command-r")
dalle = DallEAPIWrapper()

st.title("Storyline Image Generator")

theme = st.selectbox(
    "Choose a theme for the story",
    ["modern", "renaissance", "futuristic", "other"],
    index=None,
)
if theme == "other":
    theme = st.text_input("What kind of theme would you like?")
if not theme:
    st.stop()

if not (styling := st.text_input("Styling Elements")):
    st.stop()

if not (story_idea := st.text_area(label="Idea for Story")):
    st.stop()

st.write(f"{bool(st.session_state.get('story_zip'))=}")

if not st.session_state.get("download_btn"):
    prompt = PromptTemplate.from_template(
        "You are an expert storywriter. I will give you an idea. Write a 4-paragraph {theme}-era story with that idea and also provide a short and apt title.\n\nIdea: {idea}",
        partial_variables={"theme": theme},
    )

    story_chain = LLMChain(llm=llm, prompt=prompt, output_key="story")
    # story_chain = prompt | llm
    story = story_chain.invoke({"idea": story_idea})["story"]
    paras = story.split("\n\n")
    st.session_state.title = paras[0].split("Title:")[-1].strip()

    chain2_prompt = PromptTemplate.from_template(
        "You are an expert artist. I will give you a paragraph extracted from a story. Write a detailed prompt that can generate an image that aptly visualizes the paragraph. Write only the prompt and nothing else. Include the following styling elements:\n\n{elements}\n\nParagraph: {paragraph}",
        partial_variables={"elements": styling},
    )

    prompting_chain = LLMChain(llm=llm, prompt=chain2_prompt, output_key="img_prompt")

    prompts = [
        " ".join(
            [
                f"Generate a {theme}-era image.",
                prompting_chain.invoke({"paragraph": paragraph})["img_prompt"],
            ]
        )
        for paragraph in paras[1:]
    ]

    _ = [st.write(f"para-{i}: {prompt}") for i, prompt in enumerate(prompts, 1)]

    # st.write("Generatin images...")
    # img_bytes = [requests.get(dalle.run(prompt)).content for prompt in prompts]
    img_bytes = [
        requests.get(
            "https://cdn.britannica.com/13/189513-050-D73988F5/John-Smeaton-Eddystone-Lighthouse-Plymouth-Hoe-England.jpg"
        ).content
    ]
    # img_bytes = []
    # for prompt in prompts:
    #     img = requests.get(dalle.run(prompt)).content
    #     img_bytes.append(img)
    #     st.write("Generated image.")
    # st.write(f"Generated {len(img_bytes)} images.")

    col1, col2 = st.columns(2)
    col1.image(img_bytes[0], caption="para-1")
    # col2.image(img_bytes[1], caption="para-2")
    # col1.image(img_bytes[2], caption="para-3")
    # col2.image(img_bytes[3], caption="para-4")

    # st.image(img_bytes[0], caption='para-1')

    st.write("Completed script.")

    st.session_state["story_zip"] = io.BytesIO()
    with zipfile.ZipFile(
        st.session_state["story_zip"], "w", zipfile.ZIP_DEFLATED
    ) as zip_file:
        zip_file.writestr("story.txt", story)
        for i, img in enumerate(img_bytes, 1):
            zip_file.writestr(f"para-{i}.png", img)

if story_zip := st.session_state.get("story_zip"):
    st.download_button(
        "Download story",
        data=st.session_state["story_zip"],
        file_name=f"{st.session_state.title}.zip",
        key="download_btn",
    )
