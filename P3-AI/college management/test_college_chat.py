import sys
import io
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

from docx import Document
from fastapi import UploadFile


sys.path.insert(0, str(Path(__file__).parent / "college management"))
import college


class LocalChatTests(unittest.TestCase):
    def setUp(self):
        self.overview = {
            "student_count": 4,
            "department_count": 2,
            "departments": [
                {"name": "Computer Science", "code": "CS", "student_count": 3},
                {"name": "Mathematics", "code": "MATH", "student_count": 1},
            ],
        }

    def test_answers_enrollment_counts_from_overview(self):
        with patch.object(college, "get_college_overview", return_value=self.overview):
            answer = college.local_chat_answer("How many students are in CS?")

        self.assertEqual(answer, "Computer Science has 3 students.")

    def test_finds_students_in_a_department(self):
        students = {
            "students": [
                {
                    "full_name": "Test Student",
                    "email": "test@example.com",
                    "department_name": "Computer Science",
                    "enrollment_year": 2024,
                }
            ],
            "truncated": False,
        }
        with (
            patch.object(college, "get_college_overview", return_value=self.overview),
            patch.object(college, "search_students", return_value=students) as search,
        ):
            answer = college.local_chat_answer("Find students in Computer Science")

        search.assert_called_once_with(search="", department="CS")
        self.assertIn("Test Student", answer)

    def test_searches_students_by_phone(self):
        with (
            patch.object(college, "get_college_overview", return_value=self.overview),
            patch.object(college, "search_students", return_value={"students": [], "truncated": False}) as search,
        ):
            college.local_chat_answer("Find the student with phone number 555-123-4567")

        search.assert_called_once_with(search="555-123-4567", department="")

    def test_explains_how_to_use_the_directory_without_database_access(self):
        with patch.object(college, "get_college_overview") as overview:
            answer = college.local_chat_answer("How do I add a student?")

        overview.assert_not_called()
        self.assertIn("add, edit, or remove", answer)

    def test_finds_department_details(self):
        details = {
            "departments": [
                {
                    "name": "Computer Science",
                    "code": "CS",
                    "student_count": 3,
                    "building": "North Hall",
                    "head": "Department Head",
                }
            ],
            "truncated": False,
        }
        with (
            patch.object(college, "get_college_overview", return_value=self.overview),
            patch.object(college, "get_department_details", return_value=details) as search,
        ):
            answer = college.local_chat_answer("Who is the head of CS?")

        search.assert_called_once_with("CS")
        self.assertIn("North Hall", answer)
        self.assertIn("Department Head", answer)

    def test_retrieves_department_details_for_location_questions(self):
        details = {
            "departments": [
                {
                    "name": "Computer Science",
                    "code": "CS",
                    "student_count": 3,
                    "building": "North Hall",
                    "head": "Department Head",
                }
            ],
            "truncated": False,
        }
        with (
            patch.object(college, "get_college_overview", return_value=self.overview),
            patch.object(college, "get_department_details", return_value=details) as search,
        ):
            context = college.retrieve_chat_context("Where is CS located?")

        search.assert_called_once_with("CS")
        self.assertIn("North Hall", context)
        self.assertIn("Department Head", context)

    def test_generates_from_retrieved_context(self):
        with (
            patch.dict(college.os.environ, {"GEMINI_API_KEY": "test-key"}),
            patch.object(college, "retrieve_chat_context", return_value="CS is based in North Hall."),
            patch.object(college.genai, "Client") as client_factory,
        ):
            client = client_factory.return_value.__enter__.return_value
            client.models.generate_content.return_value.text = "CS is in North Hall."
            answer = college.rag_chat_answer(
                "Where is CS?",
                [college.ChatTurn(role="user", content="Tell me about CS")],
            )

        self.assertEqual(answer, "CS is in North Hall.")
        request = client.models.generate_content.call_args.kwargs
        self.assertIn("CS is based in North Hall.", request["contents"])
        self.assertIn("Tell me about CS", request["contents"])

    def test_skips_retrieval_when_gemini_is_not_configured(self):
        with (
            patch.dict(college.os.environ, {"GEMINI_API_KEY": ""}),
            patch.object(college, "retrieve_chat_context") as retrieve,
            patch.object(college, "local_chat_answer", return_value="Local answer") as local_answer,
        ):
            answer = college.rag_chat_answer("Hello", [])

        self.assertEqual(answer, "Local answer")
        retrieve.assert_not_called()
        local_answer.assert_called_once_with("Hello")

    def test_extracts_plain_text_and_splits_it_into_chunks(self):
        text = college.extract_document_text("guide.txt", b"Attendance policy applies to all students.")
        chunks = college.split_document_text(text * 80)

        self.assertIn("Attendance policy", text)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= college.DOCUMENT_CHUNK_SIZE for chunk in chunks))

    def test_rejects_unsupported_document_types(self):
        with self.assertRaises(college.HTTPException) as error:
            college.extract_document_text("guide.exe", b"not a document")

        self.assertEqual(error.exception.status_code, 415)

    def test_extracts_docx_paragraphs(self):
        document = Document()
        document.add_paragraph("Academic policy details")
        content = io.BytesIO()
        document.save(content)

        text = college.extract_document_text("handbook.docx", content.getvalue())

        self.assertIn("Academic policy details", text)

    def test_upload_stores_chunks_for_the_signed_in_user(self):
        cursor = Mock()
        cursor.fetchone.return_value = {"total": 0}
        cursor.lastrowid = 17
        connection = Mock()
        uploaded_file = UploadFile(
            filename="handbook.txt",
            file=io.BytesIO(b"Academic policy details for all students."),
        )
        with patch.object(
            college,
            "database_cursor",
            return_value=nullcontext((connection, cursor)),
        ):
            result = college.upload_chat_document(uploaded_file, {"id": 42})

        self.assertEqual(result["document"]["id"], 17)
        self.assertEqual(result["document"]["chunk_count"], 1)
        self.assertEqual(cursor.execute.call_args_list[1].args[1], (42, "handbook.txt"))
        self.assertEqual(cursor.executemany.call_args.args[1][0][0:2], (17, 0))
        connection.commit.assert_called_once()

    def test_retrieves_only_matching_uploaded_chunks_for_the_user(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {"file_name": "policy.txt", "content": "Attendance policy requires regular participation."},
            {"file_name": "calendar.txt", "content": "The semester begins in September."},
        ]
        with patch.object(college, "database_cursor", return_value=nullcontext((None, cursor))):
            results = college.retrieve_uploaded_chunks("What is the attendance policy?", user_id=42)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["file_name"], "policy.txt")
        self.assertIn("d.user_id = %s", cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_args.args[1][0], 42)

    def test_includes_uploaded_file_chunks_in_chat_context(self):
        with (
            patch.object(college, "get_college_overview", return_value=self.overview),
            patch.object(
                college,
                "retrieve_uploaded_chunks",
                return_value=[{"file_name": "policy.txt", "content": "Attendance is required."}],
            ) as retrieve,
        ):
            context = college.retrieve_chat_context("What is the attendance policy?", user_id=42)

        retrieve.assert_called_once_with("What is the attendance policy?", 42)
        self.assertIn("Uploaded file: policy.txt", context)
        self.assertIn("Attendance is required.", context)

    def test_uses_retrieved_document_when_gemini_is_unavailable(self):
        chunks = [
            {
                "file_name": "policy.txt",
                "content": "Attendance policy: Students must attend at least 80 percent of classes. "
                "Medical absences require documentation.",
            }
        ]
        with (
            patch.dict(college.os.environ, {"GEMINI_API_KEY": "test-key"}),
            patch.object(college, "get_college_overview", return_value=self.overview),
            patch.object(college, "retrieve_uploaded_chunks", return_value=chunks),
            patch.object(college.genai, "Client", side_effect=RuntimeError("model unavailable")),
        ):
            answer = college.rag_chat_answer(
                "What is the attendance policy?",
                [],
                user_id=42,
            )

        self.assertIn("From policy.txt:", answer)
        self.assertIn("80 percent", answer)
        self.assertNotIn("I work locally", answer)


if __name__ == "__main__":
    unittest.main()