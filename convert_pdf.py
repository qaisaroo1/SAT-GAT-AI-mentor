import sys
import os
from pathlib import Path

# Ensure UTF-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def extract_with_pypdf(pdf_path: Path) -> str:
    """Lightweight fallback using pypdf to extract clean text and structure."""
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    content_lines = []
    content_lines.append(f"# {pdf_path.stem.replace('_', ' ').title()}\n")

    print(f"📖 Reading {len(reader.pages)} pages with pypdf...")
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            content_lines.append(f"\n## Section / Page {i + 1}\n")
            content_lines.append(text.strip())
            content_lines.append("\n---")

    return "\n".join(content_lines)


def convert_pdf_to_markdown(pdf_path_str: str, output_md_str: str = None):
    pdf_path = Path(pdf_path_str)
    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return

    if output_md_str is None:
        output_md = pdf_path.with_suffix(".md")
    else:
        output_md = Path(output_md_str)

    converted_text = ""

    # Strategy 1: Try MarkItDown if installed
    try:
        from markitdown import MarkItDown
        print(f"📄 Converting '{pdf_path.name}' using Microsoft MarkItDown...")
        md = MarkItDown()
        result = md.convert(str(pdf_path))
        converted_text = result.text_content
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ MarkItDown conversion warning: {e}. Falling back to pypdf...")

    # Strategy 2: Lightweight pypdf fallback
    if not converted_text:
        try:
            print(f"📄 Converting '{pdf_path.name}' using fast pypdf extractor...")
            converted_text = extract_with_pypdf(pdf_path)
        except ImportError:
            print("\n❌ Please install pypdf: pip install pypdf\n")
            return
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return

    # Save to markdown file
    output_md.write_text(converted_text, encoding="utf-8")
    print(f"✅ Successfully converted and saved to: {output_md}")

    # Re-index into KnowledgeStore
    print("🔄 Indexing new Markdown file into Knowledge Store...")
    try:
        from src.ingestion import KnowledgeStore
        kb = KnowledgeStore()
        exam = "SAT" if "sat" in pdf_path.name.lower() else "GAT"
        kb.index_markdown_file(output_md, exam_type=exam)
        print(f"🎉 New book successfully indexed with {len(kb.chunks)} total chunks available!")
    except Exception as e:
        print(f"⚠️ Note: Could not auto-index ({e}). You can run the app directly.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_pdf = sys.argv[1]
    else:
        # Default check for any pdf in data folder
        data_dir = Path(__file__).resolve().parent / "data"
        pdfs = list(data_dir.glob("*.pdf"))
        if pdfs:
            input_pdf = str(pdfs[0])
            print(f"Found PDF in data directory: {input_pdf}")
        else:
            print("Usage: python convert_pdf.py <path_to_pdf>")
            print("Or drop a .pdf file into D:\\sat-gat-ai-mentor\\data\\ and run: python convert_pdf.py")
            sys.exit(0)

    convert_pdf_to_markdown(input_pdf)
