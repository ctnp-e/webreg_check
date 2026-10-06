"""
Run with:  py tests.py
"""
import unittest
from unittest.mock import patch, mock_open
from bs4 import BeautifulSoup

import web_check


# ---------- helpers ----------

def make_soup(sections, title="COMPSCI 162. FORMAL LANGUAGES AND AUTOMATA"):
    """
    Build a minimal WebSOC-style HTML table.
    sections = list of (code, max, enr)
    """
    rows = "".join(
        f"<tr><td>{code}</td><td>{mx}</td><td>{enr}</td><td>0</td></tr>"
        for code, mx, enr in sections
    )
    return BeautifulSoup(f"""
        <table>
            <tr><td colspan="9">{title}</td></tr>
            <tr><th>Code</th><th>Max</th><th>Enr</th><th>WL</th></tr>
            {rows}
        </table>
    """, "html.parser")


# ---------- classes.txt line parsing ----------

class TestParseClassLine(unittest.TestCase):

    def test_section_code_only(self):
        cls = web_check._parse_class_line("34210")
        self.assertEqual(cls["code"], "34210")
        self.assertIsNone(cls["dept"])
        self.assertIsNone(cls["course_num"])

    def test_four_parts(self):
        cls = web_check._parse_class_line("34210, COMPSCI . . . . Computer Science, 164, eppstein")
        self.assertEqual(cls["code"], "34210")
        self.assertEqual(cls["dept"], "COMPSCI . . . . Computer Science")
        self.assertEqual(cls["course_num"], "164")
        self.assertEqual(cls["instructor"], "eppstein")

    def test_three_parts_no_code(self):
        cls = web_check._parse_class_line("COMPSCI . . . . Computer Science, 164, eppstein")
        self.assertIsNone(cls["code"])
        self.assertEqual(cls["course_num"], "164")
        self.assertEqual(cls["instructor"], "eppstein")

    def test_extra_whitespace_stripped(self):
        cls = web_check._parse_class_line("  34210  ,  COMPSCI . . . . Computer Science  ,  164  ,  eppstein  ")
        self.assertEqual(cls["code"], "34210")
        self.assertEqual(cls["course_num"], "164")

    def test_bad_format_returns_none(self):
        self.assertIsNone(web_check._parse_class_line("a, b"))
        self.assertIsNone(web_check._parse_class_line("a, b, c, d, e"))


# ---------- HTML enrollment parsing ----------

class TestParseEnrollment(unittest.TestCase):

    def test_finds_correct_section(self):
        soup = make_soup([("34210", "50", "24"), ("34211", "50", "50")])
        self.assertEqual(web_check._parse_enrollment(soup, "34210"), ("50", "24"))

    def test_finds_second_section(self):
        soup = make_soup([("34210", "50", "24"), ("34211", "50", "50")])
        self.assertEqual(web_check._parse_enrollment(soup, "34211"), ("50", "50"))

    def test_missing_section_returns_none(self):
        soup = make_soup([("34210", "50", "24")])
        self.assertIsNone(web_check._parse_enrollment(soup, "99999"))

    def test_parse_all_returns_every_row(self):
        soup = make_soup([("34210", "50", "24"), ("34211", "50", "50"), ("34212", "30", "10")])
        results = web_check._parse_all_enrollments(soup)
        self.assertEqual(len(results), 3)
        self.assertIn(("34210", "50", "24"), results)
        self.assertIn(("34212", "30", "10"), results)

    def test_parse_all_empty_table(self):
        soup = BeautifulSoup("<table><tr><th>Max</th><th>Enr</th></tr></table>", "html.parser")
        self.assertEqual(web_check._parse_all_enrollments(soup), [])


# ---------- course title parsing ----------

class TestParseCourseTitle(unittest.TestCase):

    def test_finds_title_above_section(self):
        soup = make_soup([("34210", "50", "24")], title="COMPSCI 162. FORMAL LANGUAGES AND AUTOMATA")
        title = web_check._parse_course_title(soup, "34210")
        self.assertEqual(title, "COMPSCI 162. FORMAL LANGUAGES AND AUTOMATA")

    def test_returns_none_when_section_not_found(self):
        soup = make_soup([("34210", "50", "24")])
        self.assertIsNone(web_check._parse_course_title(soup, "99999"))

    def test_multiple_titles_returns_correct_one(self):
        soup = BeautifulSoup("""
            <table>
                <tr><th>Code</th><th>Max</th><th>Enr</th></tr>
                <tr><td colspan="9">COMPSCI 162. FORMAL LANGUAGES</td></tr>
                <tr><td>34210</td><td>50</td><td>24</td></tr>
                <tr><td colspan="9">COMPSCI 164. GRAPH ALGORITHMS</td></tr>
                <tr><td>34220</td><td>50</td><td>50</td></tr>
            </table>
        """, "html.parser")
        self.assertEqual(web_check._parse_course_title(soup, "34210"), "COMPSCI 162. FORMAL LANGUAGES")
        self.assertEqual(web_check._parse_course_title(soup, "34220"), "COMPSCI 164. GRAPH ALGORITHMS")


# ---------- enrollment comparison / alert logic ----------

class TestRecordAndAlert(unittest.TestCase):

    def setUp(self):
        self.cls = {"code": "34210", "dept": None, "course_num": None, "instructor": None, "title": None}

    def _run(self, max_enroll, curr_enroll):
        """Returns 'open', 'sad', or None depending on what alert fired."""
        fired = []
        with patch.object(web_check, "send_message") as mock_send, \
             patch("builtins.open", mock_open()):
            web_check.record_and_alert(self.cls, max_enroll, curr_enroll)
            if mock_send.called:
                msg = mock_send.call_args[0][0]
                fired.append("open" if "REGISTER" in msg else "sad")
        return fired[0] if fired else None

    def test_full_no_slash_is_sad(self):
        self.assertEqual(self._run("50", "50"), "sad")

    def test_open_no_slash_alerts(self):
        self.assertEqual(self._run("50", "24"), "open")

    def test_slash_full_is_sad(self):
        self.assertEqual(self._run("50", "24/24"), "sad")

    def test_slash_open_alerts(self):
        self.assertEqual(self._run("50", "20/24"), "open")

    def test_slash_with_spaces_is_sad(self):
        # "24 / 24" has whitespace around slash — must still match
        self.assertEqual(self._run("50", "24 / 24"), "sad")

    def test_slash_ignores_outer_max_column(self):
        # Max column says 50 but Enr is "24/24" — effective cap is 24, not 50
        self.assertEqual(self._run("50", "24/24"), "sad")

    def test_slash_open_ignores_outer_max_column(self):
        self.assertEqual(self._run("50", "20/24"), "open")


if __name__ == "__main__":
    unittest.main(verbosity=2)
