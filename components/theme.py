import base64

import streamlit as st
import streamlit.components.v1 as components

# Logo image generation
@st.cache_resource
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = (
        """
    <style>
    .appview-container section.main::after{
        background-image: url("data:image/png;base64,%s");
    }
    </style>
    """
        % bin_str
    )
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return


def static_prompts():

    # Added static prompt
    components.html(
        """
                <style>
                        .draft-class {
                            background-color: #F0F4F9;
                            width: 18%;
                            margin: 5px;
                            padding: 20px;
                            font-size: 14px;
                            font-family: arial;
                            border-radius: 10px;
                            min-height: 100px;
                            transition: all 0.5s ease;
                        }
                        .draft-class p {
                            font-size: 15px;
                            font-family: arial;
                            margin-top: 5px;
                            margin-left: 5px;
                        }
                        .draft-class p b {
                            padding-bottom: 10px;
                            display: block;
                        }
                        .draft-section-class {
                            display: flex;
                            position: relative;
                            justify-content: center;
                        }
                </style>
                <div class="draft-section-class">
                    <div class="draft-class">
                        <p>
                            <b>Payment Terms</b>
                            What are our standard payment terms?
                        </p>
                    </div>
                    <div class="draft-class">
                        <p>
                            <b>Audit Rights</b>
                            What minimum audit rights do we require in a contract?
                        </p>
                    </div>
                    <div class="draft-class">
                        <p>
                            <b>Affiliate</b>
                            What is an affiliate?
                        </p>
                    </div>
                    <div class="draft-class">
                        <p>
                            <b>Sub-Contracting</b>
                            When can a supplier sub-contract?
                        </p>
                    </div>
                </div>
                """,
        height=150,
    )


def static_admin_head():
    st.markdown(
        """<a class="logo-class" href="" target="_self">
    <img src="data:image/png;base64,{}" width="320" height="39">
    </a>""".format(
            base64.b64encode(open("style/assets/logo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

    components.html(
        f"""
                <style> @import url("https://use.typekit.net/qsd6fjc.css"); </style>
                <div style="padding-bottom: 10px;text-align: center; font-size: 32px;font-family: 'lexia', serif; font-weight: 800; color: #830051;">Admin</div>
                """,
        height=100,
    )


def static_chat_history_head():
    st.markdown(
        """<a class="logo-class" href="" target="_self">
    <img src="data:image/png;base64,{}" width="320" height="39">
    </a>""".format(
            base64.b64encode(open("style/assets/logo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

    components.html(
        f"""
                <style> @import url("https://use.typekit.net/qsd6fjc.css"); </style>
                <div style="padding-bottom: 10px;text-align: center; font-size: 32px;font-family: 'lexia', serif; font-weight: 800; color: #830051;">Chat History</div>
                """,
        height=100,
    )


def static_version_eval_head():
    st.markdown(
        """<a class="logo-class" href="" target="_self">
    <img src="data:image/png;base64,{}" width="320" height="39">
    </a>""".format(
            base64.b64encode(open("style/assets/logo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

    components.html(
        f"""
                <style> @import url("https://use.typekit.net/qsd6fjc.css"); </style>
                <div style="padding-bottom: 10px;text-align: center; font-size: 32px;font-family: 'lexia', serif; font-weight: 800; color: #830051;">Version Evaluator</div>
                """,
        height=100,
    )


def static_version_runner_head():
    st.markdown(
        """<a class="logo-class" href="" target="_self">
    <img src="data:image/png;base64,{}" width="320" height="39">
    </a>""".format(
            base64.b64encode(open("style/assets/logo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

    components.html(
        f"""
                <style> @import url("https://use.typekit.net/qsd6fjc.css"); </style>
                <div style="padding-bottom: 10px;text-align: center; font-size: 32px;font-family: 'lexia', serif; font-weight: 800; color: #830051;">Version Runner</div>
                """,
        height=100,
    )


def static_summariser_head():
    st.markdown(
        """<a class="logo-class" href="" target="_self">
    <img src="data:image/png;base64,{}" width="320" height="39">
    </a>""".format(
            base64.b64encode(open("style/assets/logo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

    components.html(
        f"""
                <style> @import url("https://use.typekit.net/qsd6fjc.css"); </style>
                <div style="padding-bottom: 10px;text-align: center; font-size: 32px;font-family: 'lexia', serif; font-weight: 800; color: #830051;">Contract Summariser</div>
                """,
        height=100,
    )


def static_welcome_head():
    st.markdown(
        """<a class="logo-class" href="" target="_self">
    <img src="data:image/png;base64,{}" width="320" height="39">
    </a>""".format(
            base64.b64encode(open("style/assets/logo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

    components.html(
        f"""
                <style> @import url("https://use.typekit.net/qsd6fjc.css"); </style>
                <div style="padding-bottom: 10px;text-align: center; font-size: 32px;font-family: 'lexia', serif; font-weight: 800; color: #830051;">Welcome {st.session_state.user_info['name'].split(',')[-1] if "user_info" in st.session_state else "Colleague"} to the Contract Automation Tool</div>
                """,
        height=100,
    )


def static_prompt_head():
    st.markdown(
        """<a class="logo-class" href="" target="_self">
    <img src="data:image/png;base64,{}" width="320" height="39">
    </a>""".format(
            base64.b64encode(open("style/assets/logo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

    components.html(
        """
                <style> @import url("https://use.typekit.net/qsd6fjc.css"); </style>
                <div style="padding-bottom: 10px;text-align: center; font-size: 32px;font-family: 'lexia', serif; font-weight: 800; color: #830051;">Contracting Assistant</div>
                <div style="font-size: 16px;font-family: arial;line-height: 22px;text-align: center;width: 54%;margin: auto;">Contracting Assistant can help accelerate contract negotiation and review process by giving you easy to use interface to query contracting playbooks.</div>
                """,
        height=100,
    )
    # st.warning(
    #     "_This is an experimental prototype, so results may be incorrect or misleading.  This application is only to be used for testing, not as a source of truth._",
    #     icon="🚨",
    # )


def backgroundImage():
    st.markdown(
        """
            <div class="polygonal-lines">
            <img src="data:image/svg+xml;base64,{}">
            </div>
        """.format(
            base64.b64encode(open("style/assets/polygonal.svg", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )


def custom_css():
    # Added custom css
    with open("style/css/contracting.css") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
