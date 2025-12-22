import os
import re
import docx
import fitz  # PyMuPDF
from src.database import get_db

DATABASE_NPA_COLLECTION = "npa_collection"
DATABASE_INSTRUCTIONS_COLLECTION = "instructions_collection"

def clean_text(text):
    return text.strip().replace('\xa0', ' ')

class DocxParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.doc = docx.Document(filepath)
    
    def parse(self):
        chunks = []
        
        # Context trackers
        current_section = ""
        current_chapter = ""
        current_paragraph_header = "" # as in hierarchy paragraph
        current_article = ""
        
        # Regex patterns
        re_section = re.compile(r'^РАЗДЕЛ\s+\d+\.', re.IGNORECASE) 
        re_chapter = re.compile(r'^Глава\s+\d+\.', re.IGNORECASE)
        re_paragraph_header = re.compile(r'^Параграф\s+\d+\.', re.IGNORECASE) # Hierarchy paragraph
        re_article = re.compile(r'^Статья\s+[\d\-]+\.', re.IGNORECASE)
        
        # Buffer for merging small paragraphs
        current_chunk_text = []
        current_chunk_size = 0
        CHUNK_SIZE_LIMIT = 1000  # Target characters per chunk
        
        def commit_chunk(text_list, metadata):
             if not text_list:
                 return
             full_text = "\n".join(text_list)
             chunks.append({
                "text": full_text,
                "metadata": metadata.copy()
             })
        
        # Base metadata for the current buffer
        # We need to capture the context at the START of the chunk or dominant context.
        # Simplification: Use current context at commit time? 
        # Better: Update context immediately when header found, commit previous buffer, start new buffer with new context.
        
        from docx.oxml.text.paragraph import CT_P
        from docx.oxml.table import CT_Tbl
        from docx.text.paragraph import Paragraph
        from docx.table import Table

        # Iterate over all block items in order (interleaved paragraphs and tables)
        for child in self.doc.element.body.iterchildren():
            if isinstance(child, CT_P):
                para = Paragraph(child, self.doc)
                text = clean_text(para.text)
                if not text:
                    continue

                # Identify hierarchy
                is_header = False
                match_section = re_section.match(text)
                match_chapter = re_chapter.match(text)
                match_paragraph_header = re_paragraph_header.match(text)
                match_article = re_article.match(text)
                
                if match_section:
                    is_header = True
                elif match_chapter:
                    is_header = True
                elif match_paragraph_header:
                    is_header = True
                elif match_article:
                    is_header = True
                
                if is_header:
                    # 1. Commit previous buffer with OLD context
                    if current_chunk_text:
                        commit_chunk(current_chunk_text, {
                            "source": os.path.basename(self.filepath),
                            "section": current_section,
                            "chapter": current_chapter,
                            "paragraph_header": current_paragraph_header,
                            "article": current_article,
                            "full_context": f"{current_section} > {current_chapter} > {current_paragraph_header} > {current_article}".strip(" >")
                        })
                        current_chunk_text = []
                        current_chunk_size = 0
                    
                    # 2. Update Context
                    if match_section:
                        current_section = text
                        current_chapter = ""
                        current_paragraph_header = ""
                        current_article = ""
                    elif match_chapter:
                        current_chapter = text
                        current_paragraph_header = ""
                        current_article = ""
                    elif match_paragraph_header:
                        current_paragraph_header = text
                        current_article = ""
                    elif match_article:
                        current_article = text
                    
                    # 3. Add Header to NEW buffer
                    current_chunk_text.append(text)
                    current_chunk_size += len(text)
                    
                else:
                    # Normal paragraph
                    if current_chunk_size + len(text) > CHUNK_SIZE_LIMIT and current_chunk_text:
                        commit_chunk(current_chunk_text, {
                            "source": os.path.basename(self.filepath),
                            "section": current_section,
                            "chapter": current_chapter,
                            "paragraph_header": current_paragraph_header,
                            "article": current_article,
                            "full_context": f"{current_section} > {current_chapter} > {current_paragraph_header} > {current_article}".strip(" >")
                        })
                        current_chunk_text = []
                        current_chunk_size = 0
                    
                    current_chunk_text.append(text)
                    current_chunk_size += len(text)

            elif isinstance(child, CT_Tbl):
                table = Table(child, self.doc)
                table_text = []
                for row in table.rows:
                    row_data = [clean_text(cell.text) for cell in row.cells if clean_text(cell.text)]
                    if row_data:
                        table_text.append(" | ".join(row_data))
                
                if table_text:
                    # Commit any pending text before the table
                    if current_chunk_text:
                         commit_chunk(current_chunk_text, {
                            "source": os.path.basename(self.filepath),
                            "section": current_section,
                            "chapter": current_chapter,
                            "paragraph_header": current_paragraph_header,
                            "article": current_article,
                            "full_context": f"{current_section} > {current_chapter} > {current_paragraph_header} > {current_article}".strip(" >")
                        })
                         current_chunk_text = []
                         current_chunk_size = 0

                    # Commit table as its own chunk, inheriting CURRENT context
                    commit_chunk(table_text, {
                        "source": os.path.basename(self.filepath),
                        "section": current_section,
                        "chapter": current_chapter,
                        "paragraph_header": current_paragraph_header,
                        "article": current_article,
                        "full_context": f"{current_section} > {current_chapter} > {current_paragraph_header} > {current_article} > Table Content".strip(" >"),
                        "type": "table"
                    })
        
        # Final commit for text
        if current_chunk_text:
             commit_chunk(current_chunk_text, {
                "source": os.path.basename(self.filepath),
                "section": current_section,
                "chapter": current_chapter,
                "paragraph_header": current_paragraph_header,
                "article": current_article,
                "full_context": f"{current_section} > {current_chapter} > {current_paragraph_header} > {current_article}".strip(" >")
            })

        return chunks

class PdfParser:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def parse(self):
        chunks = []
        doc = fitz.open(self.filepath)
        for page_num, page in enumerate(doc):
            text = page.get_text()
            # Simple chunking by paragraph for now for PDFs
            # PDFs are notoriously hard to retain hierarchy without visual analysis
            # We will split by double newlines or similar
            paragraphs = text.split('\n\n')
            for p in paragraphs:
                p = clean_text(p)
                if len(p) > 20: # Filter tiny chunks
                    chunks.append({
                        "text": p,
                        "metadata": {
                            "source": os.path.basename(self.filepath),
                            "page": page_num + 1
                        }
                    })
        return chunks

def ingest_data():
    db = get_db()
    npa_collection = db.get_or_create_collection(DATABASE_NPA_COLLECTION)
    instructions_collection = db.get_or_create_collection(DATABASE_INSTRUCTIONS_COLLECTION)

    base_path = os.getcwd()
    npa_path = os.path.join(base_path, "data_npa")
    instructions_path = os.path.join(base_path, "data_instructions")

    # Ingest NPA
    print("Ingesting NPA...")
    process_directory(npa_path, npa_collection, is_npa=True)

    # Ingest Instructions
    print("Ingesting Instructions...")
    process_directory(instructions_path, instructions_collection, is_npa=False)
    
    print("Ingestion Complete.")

def process_directory(directory, collection, is_npa=True):
    for root, dirs, files in os.walk(directory):
        category = os.path.basename(root)
        if root == directory: # Skip root folder itself if it contains files (usually files are in subfolders)
            category = "General"
            
        for file in files:
            file_path = os.path.join(root, file)
            filepath_abs = os.path.abspath(file_path)
            
            # Determine parser
            chunks = []
            if file.endswith(".docx"):
                parser = DocxParser(filepath_abs)
                chunks = parser.parse()
            elif file.endswith(".pdf"):
                parser = PdfParser(filepath_abs)
                chunks = parser.parse()
            else:
                continue
                
            if not chunks:
                continue
            
            # Add to DB
            ids = [f"{category}_{file}_{i}" for i in range(len(chunks))]
            documents = [c["text"] for c in chunks]
            metadatas = []
            for c in chunks:
                meta = c["metadata"]
                meta["category"] = category
                meta["type"] = "NPA" if is_npa else "Instruction"
                metadatas.append(meta)
            
            # Batch add with larger batches for better performance
            # OpenAI API can handle larger batches efficiently
            batch_size = 500
            total_chunks = len(documents)
            print(f"Processing {file} ({total_chunks} chunks)...", end=" ", flush=True)
            
            for i in range(0, len(documents), batch_size):
                end = min(i + batch_size, len(documents))
                collection.add(
                    ids=ids[i:end],
                    documents=documents[i:end],
                    metadatas=metadatas[i:end]
                )
                # Show progress
                progress = min(end, total_chunks)
                print(f"{progress}/{total_chunks}", end=" ", flush=True)
            
            print("✓ Done")

if __name__ == "__main__":
    ingest_data()
