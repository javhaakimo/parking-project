import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import parking


class ТөлбөрТооцохТест(unittest.TestCase):
    def test_0_минут(self):
        self.assertEqual(parking.Төлбөр_тооцох(0), 1000)

    def test_1_минут(self):
        self.assertEqual(parking.Төлбөр_тооцох(1), 1000)

    def test_60_минут(self):
        self.assertEqual(parking.Төлбөр_тооцох(60), 1000)

    def test_61_минут(self):
        self.assertEqual(parking.Төлбөр_тооцох(61), 2000)

    def test_125_минут(self):
        self.assertEqual(parking.Төлбөр_тооцох(125), 3000)


class МашинГарахТест(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        self._tmp.close()
        self.parking_file = Path(self._tmp.name)
        self._patcher = patch.object(parking, "PARKING_FILE", self.parking_file)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self.parking_file.unlink(missing_ok=True)

    def _бичих(self, мөрүүд):
        self.parking_file.write_text("\n".join(мөрүүд) + "\n", encoding="utf-8")

    def _гарах(self, номер, гарсан_цаг):
        with patch("builtins.input", side_effect=[номер, гарсан_цаг]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                parking.Машин_гарах()
        return buf.getvalue()

    def test_шөнө_дунд_гарах(self):
        # орсон 23:30, гарсан 00:15 -> 45 минут, 1000₮
        self._бичих(["1111УБА - 23:30"])
        гаралт = self._гарах("1111УБА", "00:15")
        self.assertIn("Төлбөр: 1000₮", гаралт)
        self.assertIn("45 минут", гаралт)

    def test_гаралт_төлбөр_агуулна(self):
        self._бичих(["1111УБА - 10:00"])
        гаралт = self._гарах("1111УБА", "12:05")
        self.assertIn("Төлбөр:", гаралт)
        self.assertIn("₮", гаралт)

    def test_гарсан_машиныг_устгана(self):
        self._бичих(["1111УБА - 10:00", "2222УБА - 11:00"])
        self._гарах("1111УБА", "12:00")
        үлдсэн = self.parking_file.read_text(encoding="utf-8")
        self.assertEqual(үлдсэн, "2222УБА - 11:00\n")

    def test_олдоогүй_машин(self):
        self._бичих(["2222УБА - 11:00"])
        гаралт = self._гарах("1111УБА", "12:00")
        self.assertIn("===== Машин олдсонгүй", гаралт)


if __name__ == "__main__":
    unittest.main()
