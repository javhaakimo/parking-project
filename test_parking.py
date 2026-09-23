import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import parking


def _одоо(*утга):
    # parking.datetime-ийг орлох, now() нь тогтмол цаг буцаадаг класс
    class ТогтмолОгноо(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(*утга)

    return patch.object(parking, "datetime", ТогтмолОгноо)


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


class ФайлТест(unittest.TestCase):
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

    def _унших(self):
        return self.parking_file.read_text(encoding="utf-8")


class МашинГарахТест(ФайлТест):
    def _гарах(self, номер, *одоо):
        with _одоо(*одоо), patch("builtins.input", side_effect=[номер]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                parking.Машин_гарах()
        return buf.getvalue()

    def test_шөнө_дунд_гарах(self):
        # орсон 23:30, гарсан маргааш 00:15 -> 45 минут, 1000₮
        self._бичих(["1111УБА - 2026-09-22 23:30:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 0, 15)
        self.assertIn("Төлбөр: 1000₮", гаралт)
        self.assertIn("0 цаг 45 минут", гаралт)

    def test_24_цаг_зогсох(self):
        self._бичих(["1111УБА - 2026-09-22 10:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 10, 0)
        self.assertIn("Төлбөр: 24000₮", гаралт)
        self.assertIn("24 цаг 0 минут", гаралт)

    def test_26_цаг_зогсох(self):
        self._бичих(["1111УБА - 2026-09-22 10:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        self.assertIn("Төлбөр: 26000₮", гаралт)

    def test_гаралт_төлбөр_агуулна(self):
        # 10:00 -> 12:05 = 125 минут -> 3000₮
        self._бичих(["1111УБА - 2026-09-23 10:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 12, 5)
        self.assertIn("2 цаг 5 минут", гаралт)
        self.assertIn("Төлбөр: 3000₮", гаралт)

    def test_гарсан_машиныг_устгана(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00", "2222УБА - 2026-09-23 11:00:00"])
        self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        self.assertEqual(self._унших(), "2222УБА - 2026-09-23 11:00:00\n")

    def test_олдоогүй_машин(self):
        self._бичих(["2222УБА - 2026-09-23 11:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        self.assertIn("===== Машин олдсонгүй", гаралт)

    def test_сөрөг_хугацаа_машиныг_үлдээнэ(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 22, 10, 0)
        self.assertIn("Гарсан цаг орсон цагаас өмнө байна", гаралт)
        self.assertNotIn("Машин олдсонгүй", гаралт)
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00:00\n")

    def test_сөрөг_хугацаа_секунд(self):
        # 30 секунд сөрөг байхад 0 минут болж төлбөр гарах ёсгүй
        self._бичих(["1111УБА - 2026-09-23 10:00:30"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 10, 0, 0)
        self.assertIn("Гарсан цаг орсон цагаас өмнө байна", гаралт)
        self.assertNotIn("Төлбөр:", гаралт)
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00:30\n")

    def test_цагийн_хилээс_30_секунд_хэтрэх(self):
        # 10:00:00 -> 11:00:30 = 60.5 минут -> эхэлсэн 2 дахь цаг, 2000₮
        self._бичих(["1111УБА - 2026-09-23 10:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 11, 0, 30)
        self.assertIn("Төлбөр: 2000₮", гаралт)
        self.assertIn("1 цаг 1 минут", гаралт)

    def test_яг_цагийн_хил(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 11, 0, 0)
        self.assertIn("Төлбөр: 1000₮", гаралт)
        self.assertIn("1 цаг 0 минут", гаралт)

    def test_59_минут_45_секунд_илүү_төлбөргүй(self):
        # 10:00:45 -> 11:00:30 = 59:45 -> 1000₮
        self._бичих(["1111УБА - 2026-09-23 10:00:45"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 11, 0, 30)
        self.assertIn("Төлбөр: 1000₮", гаралт)

    def test_микросекунд_тооцохгүй(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00"])
        гаралт = self._гарах("1111УБА", 2026, 9, 23, 11, 0, 0, 500000)
        self.assertIn("Төлбөр: 1000₮", гаралт)

    def test_хуучин_формат_алдаа_өгнө(self):
        self._бичих(["1111УБА - 10:00"])
        with self.assertRaises(ValueError):
            self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        # алдаа гарвал файл өөрчлөгдөхгүй
        self.assertEqual(self._унших(), "1111УБА - 10:00\n")

    def test_секундгүй_формат_алдаа_өгнө(self):
        self._бичих(["1111УБА - 2026-09-23 10:00"])
        with self.assertRaises(ValueError):
            self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00\n")


class МашинОруулахТест(ФайлТест):
    def test_огноотой_бичнэ(self):
        with _одоо(2026, 9, 23, 12, 30, 45), patch("builtins.input", side_effect=["1111УБА"]):
            parking.Машин_оруулах()
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 12:30:45\n")


class МашинуудХарахТест(ФайлТест):
    def test_олон_хоног(self):
        self._бичих(["1111УБА - 2026-09-22 10:00:00"])
        with _одоо(2026, 9, 23, 12, 30):
            self.assertIn("26 цаг 30 минут", parking.Машинууд_харах())

    def test_шөнө_дамнасан(self):
        self._бичих(["1111УБА - 2026-09-22 23:30:00"])
        with _одоо(2026, 9, 23, 0, 15):
            self.assertIn("0 цаг 45 минут", parking.Машинууд_харах())


if __name__ == "__main__":
    unittest.main()
