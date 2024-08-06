import csv
import os
from pathlib import Path
from src.messages import MessageHistory, RAGMessage
import streamlit as st
from streamlit_feedback import streamlit_feedback


def _submit_feedback_to_csv(feedback_input: str) -> None:
    feedback_file_path = Path(os.environ["RAG_VERSION_DIR"]) / "feedback.csv"
    file_exists = os.path.isfile(feedback_file_path)
    with open(feedback_file_path, "a", newline="") as file:
        headers = ["Feedback"]
        writer = csv.DictWriter(file, fieldnames=headers)

        if not file_exists:
            writer.writeheader()

        writer.writerow({"Feedback": feedback_input})


def feedback_form():
    st.header("Feedback Form")

    # Create a text input field for the user
    feedback_input = st.text_area("Enter your feedback here:")

    # Create a button to submit the feedback
    if st.button("Submit"):
        # Check if the file exists, if not, create a new file with headers
        _submit_feedback_to_csv(feedback_input=feedback_input)

        st.success("Feedback has been submitted.")


def feedback_box(
    message_index: int, message: RAGMessage, message_manager_state: MessageHistory
):
    if message.feedback:
        with st.container(border=True):
            c1, c2 = st.columns([1, 9])
            with c1:
                st.write(message.feedback["score"])
            with c2:
                st.write(message.feedback["text"])
    else:
        assert message_manager_state.instance
        feedback = streamlit_feedback(
            feedback_type="thumbs",
            optional_text_label="[Optional] Please provide an explanation",
            key=str(message_manager_state.instance.id) + str(message_index),
        )
        if feedback:
            message_manager_state.add_feedback(message.content, feedback)
