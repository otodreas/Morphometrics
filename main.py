#!/usr/bin/env python

import streamlit as st


def is_morphologika(file: list[str]) -> bool:
    # Instantiate dictionary with required headers as keys and False as values
    required_headers = {
        "[individuals]": False,
        "[landmarks]": False,
        "[dimensions]": False,
        "[names]": False,
        "[rawpoints]": False,
    }

    # Loop through lines
    for line in file:
        if line.strip() in required_headers.keys():
            # Update dictionary value to True for the corresponding header
            required_headers[line.strip()] = True

            # Break if all required headers have been found
            if all(required_headers.values()):
                return True

    # If not all required headers were found, return False
    return False


def show_upload_screen():
    st.title("Advanced Morphometric Classification")

    # File importer
    uploaded_files = st.file_uploader(
        "Import morphologika data", type="txt", accept_multiple_files=True
    )

    # Classify button
    classify = st.button("Classify morphologika files")

    # Handle classify button click
    if classify:
        # Check if any files were uploaded
        if len(uploaded_files) == 0:
            st.error("No morphologika files uploaded")

        else:
            # Loop through uploaded files
            for file in uploaded_files:
                # Read file
                content = file.read().decode("utf-8").splitlines()

                # Check if file is a valid morphologika file
                if not is_morphologika(content):
                    st.error(f"{file.name} is not a valid utf-8 morphologika file")

            # If all files are valid, proceed to classification
            # TODO: why isnt the script interrupting when just one invalid file is uploaded with a valid one?
            st.session_state.files = uploaded_files
            st.session_state.screen = "running"
            st.rerun()


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
