#!/usr/bin/env python

import streamlit as st

def show_upload_screen():
    st.title("Advanced Morphometric Classification")

    # File importer
    staged_files = st.file_uploader(
        "Import morphologika data", type="txt", accept_multiple_files=True
    )

    # Upload button
    upload = st.button("Upload morphologika files")

    # Handle upload button click
    if upload:
        # Check if any files were uploaded
        if len(staged_files) == 0:
            st.error("No morphologika files uploaded")

        else:
            contents = []
            st.session_state.files = staged_files
            for file in st.session_state.files:
                contents.append(file.read())
                
            st.session_state.contents = contents
            print(st.session_state.contents)
            

def show_running_screen():
    st.title("Classifying morphologika data...")
    cancel = st.button("Cancel")
    if cancel:
        st.session_state.screen = "upload"
        st.rerun()

def main():
    if "screen" not in st.session_state:
        st.session_state.screen = "upload"
    if st.session_state.screen == "upload":
        show_upload_screen()
    elif st.session_state.screen == "running":
        show_running_screen()

if __name__ == "__main__":
    main()

# def show_upload_screen():
#     st.session_state.screen = "upload"

#     st.title("Advanced Morphometric Classification")
#     st.markdown("*State-of-the-art techniques inspired by Kaggle-winning approach*")

#     staged_files = st.file_uploader("Import morphologika data", accept_multiple_files=True)

#     upload = st.button("Upload morphologika files")

#     if upload:
#         if len(staged_files) > 0:
#             st.success("Morphologika files uploaded")
#             run = st.button("Classify morphologika data")
#             if run:
#                 st.session_state.screen = "running"
#                 st.rerun()
#         else:
#             st.error("No morphologika files uploaded")

#     st.markdown("*Classification algorithm: Sara Behnamian, Web app: Oliver Todreas*")

# def show_running_screen():
#     st.header("Classifying morphologika data...")
#     cancel = st.button("Cancel")
#     if cancel:
#         st.session_state.screen = "upload"
#         st.rerun()

# def show_dashboard_screen():
#     pass


# def main():
#     if "screen" not in st.session_state:
#         st.session_state.screen = "upload"

#     if st.session_state.screen == "upload":
#         show_dashboard_screen()
#     elif st.session_state.screen == "running":
#         show_running_screen()
#     elif st.session_state.screen == "dashboard":
#         show_dashboard_screen()


# if __name__ == "__main__":
#     main()