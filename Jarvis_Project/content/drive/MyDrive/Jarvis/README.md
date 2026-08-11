# Jarvis Interface — Demo & Setup

This repository includes a small local KB demo and a fallback in-memory vector store so you can run the demo without installing heavy dependencies like FAISS or SentenceTransformers.

## Quick demo (no extra packages required)

Run:

    python jarvis_interface.py --demo-build

This will create `demo_kb/` with a few `.txt` files, build a small KB using the in-memory fallback, print progress, and run a sample search.

## Optional: Install full dependencies

To get the full FAISS-backed experience and use models from `sentence-transformers`, follow the PowerShell helper:

1. Open PowerShell in the project folder
2. Run: `./setup_env.ps1`

Notes:
- FAISS on Windows is best installed via conda: `conda install -c pytorch faiss-cpu`
- The script `setup_env.ps1` installs common optional packages; heavy packages like FAISS may require platform-specific installation.

### AIMLAPI Deprecation

Support for the AIMLAPI service has been removed after the hosted API now requires account verification. The project no longer sets or reads an `AIMLAPI_KEY` environment variable and related code has been stripped out. If you were relying on AIMLAPI, please update your workflows accordingly.

## Tests

A basic `unittest` is included at `tests/test_demo_build.py` that runs the demo build and checks that it completes successfully.

## Image Attachment UI

The chat input now supports quick image attachments with inline preview:

* Paste images from the clipboard or drag-and-drop them into the input box.
* A thumbnail appears inside the text area with a close button to remove the file.
* File type and size are validated (JPG/PNG/WEBP ≤5 MB).
* Attachments are sent to the backend along with the text and shown in the chat history.

This makes the demo feel more like a modern multimodal chat interface.
