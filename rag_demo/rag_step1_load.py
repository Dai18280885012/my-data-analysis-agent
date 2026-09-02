from pathlib import Path
import re
from docx import Document
from pypdf import PdfReader


DOCS_DIR = Path("rag_demo/documents")


def load_txt(file_path):
    return file_path.read_text(encoding="utf-8")


def load_docx(file_path):
    document = Document(file_path)

    return "\n".join(
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )


def load_pdf(file_path):
    reader = PdfReader(file_path)

    return "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )


def load_documents():
    documents = []

    for file_path in DOCS_DIR.iterdir():
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            content = load_txt(file_path)
        elif suffix == ".docx":
            content = load_docx(file_path)
        elif suffix == ".pdf":
            content = load_pdf(file_path)
        else:
            print(f"跳过不支持的文件：{file_path.name}")
            continue

        if not content.strip():
            print(f"跳过空文档：{file_path.name}")
            continue

        documents.append(
            {
                "source": file_path.name,
                "content": content,
            }
        )

    return documents


def split_text(text, chunk_size=200, overlap=30):
    text = re.sub(r"\s+", " ", text).strip()

    # 按中文句号、问号、感叹号、分号切分，尽量保持句子完整。
    sentences = re.split(
        r"(?<=[。！？；])",
        text,
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # 当前块还能容纳这句话时，继续合并。
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence
            continue

        # 当前块已满，先保存。
        if current_chunk:
            chunks.append(current_chunk)

        # 保留上一块结尾的一小段上下文，减少上下文断裂。
        overlap_text = current_chunk[-overlap:]
        current_chunk = overlap_text + sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def split_documents(documents):
    chunk_list = []

    for document in documents:
        chunks = split_text(document["content"])

        for index, chunk in enumerate(chunks):
            chunk_list.append(
                {
                    "source": document["source"],
                    "chunk_id": index,
                    "content": chunk,
                }
            )

    return chunk_list