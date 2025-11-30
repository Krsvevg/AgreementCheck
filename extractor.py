import os
import tempfile
from pdfminer.high_level import extract_text as pdf_extract_text
from pdfminer.pdfpage import PDFPage
from pypdf import PdfReader
from PIL import Image
import pytesseract
import docx
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_scanned_pdf(path):
    """Рендерит каждую страницу PDF в картинку и прогоняет OCR."""
    doc = fitz.open(path)
    result_text = []

    for page in doc:
        # Рендер страницы в изображение
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")

        # Загружаем как PIL Image
        image = Image.open(io.BytesIO(img_data))

        # OCR
        text = pytesseract.image_to_string(image, lang="rus+eng")
        result_text.append(text)

    doc.close()
    return "\n".join(result_text)



def extract_text_from_docx(path):
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


def extract_text_from_pdf_text_layer(path):
    try:
        text = pdf_extract_text(path)
        return text.strip()
    except Exception:
        return ""


def pdf_to_images(path):
    images = []
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages):
        try:
            if "/XObject" in page["/Resources"]:
                xobj = page["/Resources"]["/XObject"]
                for obj in xobj:
                    if xobj[obj]["/Subtype"] == "/Image":
                        data = xobj[obj].get_data()
                        img = Image.open(
                            tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        )
                        img.fp.write(data)
                        img.fp.seek(0)
                        images.append(img)
        except:
            pass
    return images


def extract_text_via_ocr(image):
    return pytesseract.image_to_string(image, lang="rus+eng")


def extract_text_from_image_file(path):
    image = Image.open(path)
    return extract_text_via_ocr(image)


def extract_text(path):
    ext = os.path.splitext(path)[1].lower()

    # DOCX
    if ext == ".docx":
        return extract_text_from_docx(path)

    # PDF
    if ext == ".pdf":
        # 1) Пробуем текстовый слой
        text_layer = extract_text_from_pdf_text_layer(path)
        if len(text_layer) > 20:
            return text_layer

        # 2) PDF без текстового слоя → OCR через PyMuPDF
        return extract_text_from_scanned_pdf(path)

    # JPEG/PNG
    if ext in [".jpg", ".jpeg", ".png"]:
        return extract_text_from_image_file(path)

    raise ValueError("Формат файла не поддерживается")

