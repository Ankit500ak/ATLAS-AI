from typing import Dict, Optional
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes uploaded documents (PDF, images) and extracts content
    for analysis and question answering.
    """

    def __init__(self):
        self.supported_formats = [".pdf", ".txt", ".csv"]

    async def process_document(self, file_path: str, user_id: int) -> Dict:
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": "File not found"}

            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".pdf":
                content = await self._process_pdf(file_path)
            elif ext == ".txt":
                content = await self._process_text(file_path)
            elif ext == ".csv":
                content = await self._process_csv(file_path)
            else:
                return {"success": False, "error": f"Unsupported format: {ext}"}

            if not content:
                return {"success": False, "error": "Could not extract content"}

            summary = await self._generate_summary(content)
            key_insights = await self._extract_insights(content)
            chunk_count = max(1, len(content) // 2000)

            return {
                "success": True,
                "content": content[:5000],
                "summary": summary,
                "key_insights": key_insights,
                "file_path": file_path,
                "chunk_count": chunk_count,
                "processed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _process_pdf(self, file_path: str) -> Optional[str]:
        try:
            import asyncio
            loop = asyncio.get_running_loop()

            def _read_pdf():
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages[:50]:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts)

            return await loop.run_in_executor(None, _read_pdf)
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return None

    async def _process_text(self, file_path: str) -> Optional[str]:
        try:
            import asyncio
            loop = asyncio.get_running_loop()

            def _read_text():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()[:10000]

            return await loop.run_in_executor(None, _read_text)
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            return None

    async def _process_csv(self, file_path: str) -> Optional[str]:
        try:
            import asyncio
            loop = asyncio.get_running_loop()

            def _read_csv():
                import pandas as pd
                df = pd.read_csv(file_path, nrows=100)

                summary_parts = [
                    f"CSV File: {os.path.basename(file_path)}",
                    f"Rows: {len(df)}, Columns: {len(df.columns)}",
                    f"Columns: {', '.join(df.columns.tolist())}",
                    "",
                    "First 10 rows:",
                    df.head(10).to_string(index=False),
                    "",
                    "Statistics:",
                    df.describe().to_string() if len(df.select_dtypes(include='number').columns) > 0 else "No numeric columns",
                ]

                return "\n".join(summary_parts)[:10000]

            return await loop.run_in_executor(None, _read_csv)
        except Exception as e:
            logger.error(f"CSV processing failed: {e}")
            return None

    async def _generate_summary(self, content: str) -> str:
        from app.services.ai.service import ai_service
        prompt = f"Provide a concise executive summary of this document (3-5 bullet points):\n\n{content[:3000]}"
        result = await ai_service.generate(prompt=prompt, temperature=0.3)
        return result["content"] if result["success"] else "Summary unavailable"

    async def _extract_insights(self, content: str) -> list:
        from app.services.ai.service import ai_service
        prompt = f"Extract 5 key insights or findings from this document as bullet points:\n\n{content[:3000]}"
        result = await ai_service.generate(prompt=prompt, temperature=0.3)
        if result["success"]:
            lines = result["content"].split("\n")
            return [l.lstrip("•-* ").strip() for l in lines if l.strip() and l.strip()[0] in "•-*"]
        return ["Insights unavailable"]

    async def answer_question(self, content: str, question: str) -> str:
        from app.services.ai.service import ai_service
        prompt = f"""Based on the following document content, answer the user's question.

Document Content:
{content[:4000]}

Question: {question}

Provide a concise, accurate answer based only on the document content."""
        result = await ai_service.generate(prompt=prompt, temperature=0.3)
        return result["content"] if result["success"] else "I couldn't find an answer in the document."
