import unittest
from main import clean_filename, detect_file_type, extract_all_tags, find_tag_positions

class TestEnvParser(unittest.TestCase):

    def test_clean_filename(self):
        dirty = "some:/weird\\file*name?.txt"
        cleaned = clean_filename(dirty)
        self.assertEqual(cleaned, "some_weird_file_name_.txt")

    def test_detect_file_type_by_ext(self):
        blob = b''  # content won't matter when extension is known
        ext, ftype = detect_file_type(blob, 'jpg')
        self.assertEqual((ext, ftype), ('.jpg', 'JPEG'))

    def test_detect_file_type_by_blob(self):
        blob = b'\xFF\xD8\xFFextra_data_here'
        ext, ftype = detect_file_type(blob)
        self.assertEqual((ext, ftype), ('.jpg', 'JPEG'))

    def test_detect_file_type_text_content(self):
        blob = b'This file contains some content that is readable.'
        ext, ftype = detect_file_type(blob)
        self.assertEqual((ext, ftype), ('.txt', 'TEXT'))

    def test_detect_file_type_unknown(self):
        blob = b'randombinarydatawithnorecognizableheaders'
        ext, ftype = detect_file_type(blob)
        self.assertEqual((ext, ftype), ('.bin', 'Unknown'))

    def test_extract_all_tags(self):
        data = b"GUID/some-id\nTYPE/xml\nDOCU/contents"
        tags = extract_all_tags(data)
        self.assertListEqual(tags, ['DOCU/', 'GUID/', 'TYPE/'])

    def test_find_tag_positions(self):
        data = b"GUID/abcTYPE/jpegDOCU/binary_data"
        expected = [(0, 'GUID/'), (8, 'TYPE/'), (17, 'DOCU/')]
        actual = find_tag_positions(data)
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
