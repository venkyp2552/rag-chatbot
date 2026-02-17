import pypdf

def read_first_page():
    try:
        reader = pypdf.PdfReader("You-are-the-World.pdf")
        page = reader.pages[0]
        text = page.extract_text()
        print(text[:1000])  # Print first 1000 chars
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_first_page()
