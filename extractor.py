import fitz
import os
import re
import tempfile

def extract_mcqs_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    mcqs_by_topic = {}
    current_topic = "General"
    image_folder = tempfile.mkdtemp()

    topic_pattern = re.compile(
        r"^(?:[A-Z][A-Z\s&\-]+|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$",  # detects both CAPS and Title Case
        re.MULTILINE
    )

    mcq_pattern = re.compile(
        r"Q\d+\.\s*(.*?)\nA\.\s*(.*?)\nB\.\s*(.*?)\nC\.\s*(.*?)\nD\.\s*(.*?)\n(?:Answer|Correct Answer)[:\- ]?\s*([A-D])(?:[\s\S]*?(?:Explanation[:\- ]?(.*?))?(?=\nQ\d+|$))?",
        re.DOTALL
    )

    # Extract text from each page
    page_texts = [page.get_text("text") for page in doc]

    # Extract images
    page_images = []
    for pno, page in enumerate(doc):
        imgs = []
        for i, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base = doc.extract_image(xref)
            image_path = os.path.join(image_folder, f"page{pno}_img{i}.png")
            with open(image_path, "wb") as f:
                f.write(base["image"])
            imgs.append(image_path)
        page_images.append(imgs)

    # Combine text and detect topics + MCQs
    for pno, text in enumerate(page_texts):
        lines = text.splitlines()

        for i, line in enumerate(lines):
            # Detect topic titles (CAPS or Title Case)
            if topic_pattern.match(line.strip()):
                current_topic = line.strip().title()
                if current_topic not in mcqs_by_topic:
                    mcqs_by_topic[current_topic] = []
                continue

        # Extract MCQs under current topic
        for match in mcq_pattern.finditer(text):
            q, a, b, c, d, ans, exp = match.groups()
            correct = ord(ans.strip().upper()) - ord("A")
            mcq = {
                "question": q.strip(),
                "options": [a.strip(), b.strip(), c.strip(), d.strip()],
                "correct_index": correct,
                "explanation": (exp or "").strip(),
                "images": page_images[pno],
            }
            mcqs_by_topic.setdefault(current_topic, []).append(mcq)

    doc.close()
    return mcqs_by_topic
