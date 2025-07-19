"""
Simple PDF text extraction with OCR fallback.
"""

from pathlib import Path
import PyPDF2
import pdfplumber
import fitz  
import subprocess
import tempfile
from PIL import Image
import io
from .base import TextExtractor, ExtractionResult

class PDFExtractor(TextExtractor):
    
    def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'
    
    def extract(self, file_path: Path) -> ExtractionResult:
        result = self._try_pypdf2(file_path)
        if result.text and len(result.text.strip()) > 50:
            return result
        
        result = self._try_pdfplumber(file_path)
        if result.text and len(result.text.strip()) > 50:
            return result
        
        return self._try_ocr(file_path)
    
    def _try_pypdf2(self, file_path: Path) -> ExtractionResult:
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = '\n'.join(page.extract_text() for page in reader.pages)
                
                return ExtractionResult(
                    text=text,
                    metadata={"pages": len(reader.pages), "method": "pypdf2"}
                )
        except Exception as e:
            return ExtractionResult("", error=f"PyPDF2 failed: {e}")
    
    def _try_pdfplumber(self, file_path: Path) -> ExtractionResult:
        try:
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                
                for page in pdf.pages:
                    if page.extract_text():
                        text_parts.append(page.extract_text())
                    
                    for table in page.extract_tables():
                        table_text = '\n'.join(' | '.join(row) for row in table if row)
                        text_parts.append(f"[TABLE]\n{table_text}\n[/TABLE]")
                
                return ExtractionResult(
                    text='\n'.join(text_parts),
                    metadata={"pages": len(pdf.pages), "method": "pdfplumber"}
                )
        except Exception as e:
            return ExtractionResult("", error=f"PDF extraction failed: {e}")
    
    def _try_ocr(self, file_path: Path) -> ExtractionResult:
        try:
            doc = fitz.open(file_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    img.save(tmp_file.name)
                    
                    try:
                        result = subprocess.run([
                            'tesseract', tmp_file.name, 'stdout'
                        ], capture_output=True, text=True, check=True)
                        
                        page_text = result.stdout.strip()
                        if page_text:
                            text_parts.append(page_text)
                    except subprocess.CalledProcessError:
                        continue  
                    finally:
                        import os
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass
            
            doc.close()
            
            if not text_parts:
                return ExtractionResult("", error="OCR found no text in PDF")
            
            return ExtractionResult(
                text='\n'.join(text_parts),
                metadata={"pages": len(text_parts), "method": "ocr"}
            )
            
        except Exception as e:
            return ExtractionResult("", error=f"OCR failed: {e}") 