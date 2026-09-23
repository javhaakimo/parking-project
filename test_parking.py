import io
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
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


@contextmanager
def _оролт(*мөрүүд):
    # parking.sys.stdin-г StringIO-р орлож readline-аар оролт өгнө;
    # input() дуудвал (Python 3.14-ийн кирилл алдааг дахин авчрахгүйн тулд) алдаа шидэнэ
    урсгал = io.StringIO("".join(f"{мөр}\n" for мөр in мөрүүд))
    with patch.object(parking.sys, "stdin", урсгал), patch(
        "builtins.input",
        side_effect=AssertionError("input() must not be called"),
    ):
        yield


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
        with _одоо(*одоо), _оролт(номер):
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
        with self.assertRaises(parking.ФорматАлдаа) as ctx:
            self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        мессеж = str(ctx.exception)
        self.assertIn("1-р мөр", мессеж)
        self.assertIn('"1111УБА - 10:00"', мессеж)
        self.assertIn("ДУГААР - YYYY-MM-DD HH:MM:SS", мессеж)
        self.assertIn("гараар засаад", мессеж)
        # алдаа гарвал файл өөрчлөгдөхгүй
        self.assertEqual(self._унших(), "1111УБА - 10:00\n")

    def test_секундгүй_формат_алдаа_өгнө(self):
        self._бичих(["1111УБА - 2026-09-23 10:00"])
        with self.assertRaises(parking.ФорматАлдаа) as ctx:
            self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        self.assertIn('"1111УБА - 2026-09-23 10:00"', str(ctx.exception))
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00\n")

    def test_алдаатай_мөрийн_дугаар(self):
        мөрүүд = ["2222УБА - 2026-09-23 09:00:00", "1111УБА - 10:00"]
        self._бичих(мөрүүд)
        with self.assertRaises(parking.ФорматАлдаа) as ctx:
            self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        self.assertIn("2-р мөр", str(ctx.exception))
        self.assertEqual(self._унших(), "\n".join(мөрүүд) + "\n")

    def test_тусгаарлагчгүй_мөр(self):
        self._бичих(["1111УБА 2026-09-23 10:00:00"])
        with self.assertRaises(parking.ФорматАлдаа) as ctx:
            self._гарах("1111УБА", 2026, 9, 23, 12, 0)
        self.assertIn("1-р мөр", str(ctx.exception))


class МашинОруулахТест(ФайлТест):
    def test_огноотой_бичнэ(self):
        with _одоо(2026, 9, 23, 12, 30, 45), _оролт("1111УБА"):
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

    def test_хуучин_формат_алдаа_өгнө(self):
        self._бичих(["2222УБА - 2026-09-23 09:00:00", "1111УБА - 10:00"])
        with _одоо(2026, 9, 23, 12, 0):
            with self.assertRaises(parking.ФорматАлдаа) as ctx:
                parking.Машинууд_харах()
        self.assertIn("2-р мөр", str(ctx.exception))


class MainТест(ФайлТест):
    def test_хуучин_формат_menu_унахгүй(self):
        self._бичих(["1111УБА - 10:00"])
        buf = io.StringIO()
        with _одоо(2026, 9, 23, 12, 0), \
                _оролт("2", "1111УБА", "4", "6"), \
                redirect_stdout(buf):
            parking.main()
        гаралт = buf.getvalue()
        # 2 болон 4 сонголт хоёулаа алдааны мессеж хэвлээд menu руу буцна
        self.assertEqual(гаралт.count("===== Алдаа: parking.txt-ийн 1-р мөр"), 2)
        self.assertNotIn("Traceback", гаралт)
        self.assertEqual(self._унших(), "1111УБА - 10:00\n")


class ОролтАвахТест(unittest.TestCase):
    def test_кирилл_хадгална(self):
        with patch.object(parking.sys, "stdin", io.StringIO("1111УБА\n")):
            self.assertEqual(parking._оролт_авах("Асуулт: "), "1111УБА")

    def test_кирилл_ө_үсэгтэй(self):
        with patch.object(parking.sys, "stdin", io.StringIO("2255УБӨ\n")):
            self.assertEqual(parking._оролт_авах("Асуулт: "), "2255УБӨ")

    def test_мөрийн_төгсгөл_хасна(self):
        with patch.object(parking.sys, "stdin", io.StringIO("1111УБА\r\n")):
            self.assertEqual(parking._оролт_авах("Асуулт: "), "1111УБА")

    def test_хоосон_мөр(self):
        with patch.object(parking.sys, "stdin", io.StringIO("\n")):
            self.assertEqual(parking._оролт_авах("Асуулт: "), "")

    def test_хоосон_урсгал_EOFError(self):
        with patch.object(parking.sys, "stdin", io.StringIO("")):
            with self.assertRaises(EOFError):
                parking._оролт_авах("Асуулт: ")

    def test_асуулт_хэвлэнэ(self):
        with patch.object(parking.sys, "stdin", io.StringIO("1111УБА\n")):
            buf = io.StringIO()
            with redirect_stdout(buf):
                parking._оролт_авах("Улсын дугаар: ")
        self.assertEqual(buf.getvalue(), "Улсын дугаар: ")


class ДугаарАвахТест(unittest.TestCase):
    def _авах(self, *мөрүүд):
        buf = io.StringIO()
        with _оролт(*мөрүүд), redirect_stdout(buf):
            номер = parking._дугаар_авах()
        return номер, buf.getvalue()

    def test_хоосон_мөрийн_дараа_дахин_асууна(self):
        номер, гаралт = self._авах("", "1111УБА")
        self.assertEqual(номер, "1111УБА")
        self.assertIn("Улсын дугаар хоосон байна", гаралт)
        self.assertEqual(гаралт.count("Улсын дугаар: "), 2)

    def test_зөвхөн_зайтай_мөр_хоосон(self):
        номер, гаралт = self._авах("   ", "1111УБА")
        self.assertEqual(номер, "1111УБА")
        self.assertIn("Улсын дугаар хоосон байна", гаралт)

    def test_зайг_арилгана(self):
        номер, _ = self._авах("  1111УБА  ")
        self.assertEqual(номер, "1111УБА")

    def test_хоосон_мөрийн_дараа_EOFError(self):
        with _оролт(""), redirect_stdout(io.StringIO()):
            with self.assertRaises(EOFError):
                parking._дугаар_авах()


class ДугаарФорматТест(unittest.TestCase):
    ФОРМАТ_АЛДАА = "Улсын дугаар буруу форматтай"
    ЭВДЭРСЭН = "Улсын дугаар эвдэрсэн тэмдэгт агуулж байна"

    def _авах(self, *мөрүүд):
        buf = io.StringIO()
        with _оролт(*мөрүүд), redirect_stdout(buf):
            номер = parking._дугаар_авах()
        return номер, buf.getvalue()

    # Хүлээн авах: шинэ дүрэм хэт хатуу болохыг барина
    def test_УБА_зөвшөөрнө(self):
        self.assertEqual(self._авах("1234УБА"), ("1234УБА", "Улсын дугаар: "))

    def test_УБӨ_зөвшөөрнө(self):
        self.assertEqual(self._авах("1234УБӨ"), ("1234УБӨ", "Улсын дугаар: "))

    def test_ДГА_зөвшөөрнө(self):
        self.assertEqual(self._авах("1234ДГА"), ("1234ДГА", "Улсын дугаар: "))

    # Татгалзах: буруу оролтыг таамаглахгүй, мэдэгдээд дахин асууна
    def _татгалзана(self, буруу, мессеж):
        номер, гаралт = self._авах(буруу, "1234УБА")
        self.assertEqual(номер, "1234УБА")
        self.assertIn(мессеж, гаралт)
        self.assertEqual(гаралт.count("Улсын дугаар: "), 2)
        return гаралт

    def test_2_үсэг_татгалзана(self):
        self._татгалзана("1234АБ", self.ФОРМАТ_АЛДАА)

    def test_3_цифр_татгалзана(self):
        self._татгалзана("123УБА", self.ФОРМАТ_АЛДАА)

    def test_жижиг_үсэг_татгалзана(self):
        self._татгалзана("1234уба", self.ФОРМАТ_АЛДАА)

    def test_5_цифр_татгалзана(self):
        self._татгалзана("12345УБА", self.ФОРМАТ_АЛДАА)

    def test_бүтэн_өргөнтэй_цифр_татгалзана(self):
        self._татгалзана("１２３４УБА", self.ФОРМАТ_АЛДАА)

    def test_эвдэрсэн_байт_татгалзана(self):
        гаралт = self._татгалзана("9988УБ\udcd3", self.ЭВДЭРСЭН)
        self.assertNotIn("\udcd3", гаралт)

    def test_хоосон_мөр_мессеж_хэвээр(self):
        гаралт = self._татгалзана("", "Улсын дугаар хоосон байна")
        self.assertNotIn(self.ФОРМАТ_АЛДАА, гаралт)


class ЭвдэрсэнБайтОруулахТест(ФайлТест):
    def test_оруулах_унахгүй_зөвийг_бичнэ(self):
        # Өмнө нь файлд бичихэд UnicodeEncodeError '\udcd3' гарч унадаг байсан
        with _одоо(2026, 9, 23, 12, 0), _оролт("9988УБ\udcd3", "9988УБА"), \
                redirect_stdout(io.StringIO()):
            parking.Машин_оруулах()
        self.assertEqual(self._унших(), "9988УБА - 2026-09-23 12:00:00\n")


class ХуучинДугаарТест(ФайлТест):
    # Шинэ форматаас өмнө бичигдсэн дугаар гарах/устгах үед хүрэх боломжтой байх ёстой
    МӨРҮҮД = ["2231УБӨА - 2026-09-23 10:00:00", "2222УБА - 2026-09-23 11:00:00"]

    def _ажиллуулах(self, функц, *мөрүүд):
        buf = io.StringIO()
        with _одоо(2026, 9, 23, 12, 0), _оролт(*мөрүүд), redirect_stdout(buf):
            функц()
        return buf.getvalue()

    def test_хуучин_дугаар_гарна(self):
        self._бичих(self.МӨРҮҮД)
        гаралт = self._ажиллуулах(parking.Машин_гарах, "2231УБӨА")
        self.assertIn("===== Машин олдлоо: 2231УБӨА", гаралт)
        self.assertIn("Төлбөр: 2000₮", гаралт)
        self.assertEqual(self._унших(), "2222УБА - 2026-09-23 11:00:00\n")

    def test_хуучин_дугаар_устана(self):
        self._бичих(self.МӨРҮҮД)
        self._ажиллуулах(parking.Машин_устгах, "2231УБӨА")
        self.assertEqual(self._унших(), "2222УБА - 2026-09-23 11:00:00\n")

    def test_оруулах_буруу_форматыг_татгалзсаар(self):
        гаралт = self._ажиллуулах(parking.Машин_оруулах, "2231УБӨА", "2231УБА")
        self.assertIn("Улсын дугаар буруу форматтай", гаралт)
        self.assertEqual(self._унших(), "2231УБА - 2026-09-23 12:00:00\n")

    def test_гарах_эвдэрсэн_байт_дахин_асууна(self):
        self._бичих(self.МӨРҮҮД)
        гаралт = self._ажиллуулах(parking.Машин_гарах, "9988УБ\udcd3", "2231УБӨА")
        self.assertIn("Улсын дугаар эвдэрсэн тэмдэгт агуулж байна", гаралт)
        self.assertEqual(self._унших(), "2222УБА - 2026-09-23 11:00:00\n")

    def test_устгах_эвдэрсэн_байт_дахин_асууна(self):
        self._бичих(self.МӨРҮҮД)
        гаралт = self._ажиллуулах(parking.Машин_устгах, "9988УБ\udcd3", "2231УБӨА")
        self.assertIn("Улсын дугаар эвдэрсэн тэмдэгт агуулж байна", гаралт)
        self.assertEqual(self._унших(), "2222УБА - 2026-09-23 11:00:00\n")


class ХоосонДугаарТест(ФайлТест):
    МӨРҮҮД = ["1111УБА - 2026-09-23 10:00:00", "2222УБА - 2026-09-23 11:00:00"]

    def _ажиллуулах(self, функц, *мөрүүд):
        buf = io.StringIO()
        with _одоо(2026, 9, 23, 12, 0), _оролт(*мөрүүд), redirect_stdout(buf):
            функц()
        return buf.getvalue()

    def test_устгах_хоосон_бүгдийг_устгахгүй(self):
        self._бичих(self.МӨРҮҮД)
        self._ажиллуулах(parking.Машин_устгах, "", "9999УБА")
        self.assertEqual(self._унших(), "\n".join(self.МӨРҮҮД) + "\n")

    def test_гарах_хоосон_бүгдийг_гаргахгүй(self):
        self._бичих(self.МӨРҮҮД)
        гаралт = self._ажиллуулах(parking.Машин_гарах, "", "1111УБА")
        self.assertEqual(гаралт.count("===== Машин олдлоо"), 1)
        self.assertEqual(self._унших(), "2222УБА - 2026-09-23 11:00:00\n")

    def test_оруулах_хоосон_бичихгүй(self):
        self._ажиллуулах(parking.Машин_оруулах, "", "1111УБА")
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 12:00:00\n")


class ЯгТэнцүүХайлтТест(ФайлТест):
    def _ажиллуулах(self, функц, номер):
        buf = io.StringIO()
        with _одоо(2026, 9, 23, 12, 0), _оролт(номер), redirect_stdout(buf):
            функц()
        return buf.getvalue()

    def test_гарах_хэсэгчилсэн_дугаар_олдохгүй(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00"])
        гаралт = self._ажиллуулах(parking.Машин_гарах, "11УБА")
        self.assertIn("===== Машин олдсонгүй", гаралт)
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00:00\n")

    def test_гарах_зөвхөн_яг_таарсныг_гаргана(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00", "11УБА - 2026-09-23 11:00:00"])
        гаралт = self._ажиллуулах(parking.Машин_гарах, "11УБА")
        self.assertEqual(гаралт.count("===== Машин олдлоо"), 1)
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00:00\n")

    def test_устгах_зөвхөн_яг_таарсныг_устгана(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00", "11УБА - 2026-09-23 11:00:00"])
        self._ажиллуулах(parking.Машин_устгах, "11УБА")
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00:00\n")

    def test_устгах_хэсэгчилсэн_дугаар_устгахгүй(self):
        self._бичих(["1111УБА - 2026-09-23 10:00:00"])
        self._ажиллуулах(parking.Машин_устгах, "11УБА")
        self.assertEqual(self._унших(), "1111УБА - 2026-09-23 10:00:00\n")

    def test_устгах_тусгаарлагчгүй_мөр_алдаа_өгнө(self):
        мөрүүд = ["2222УБА - 2026-09-23 09:00:00", "1111УБА 2026-09-23 10:00:00"]
        self._бичих(мөрүүд)
        with self.assertRaises(parking.ФорматАлдаа) as ctx:
            self._ажиллуулах(parking.Машин_устгах, "1111УБА")
        self.assertIn("2-р мөр", str(ctx.exception))
        self.assertEqual(self._унших(), "\n".join(мөрүүд) + "\n")

    def test_гарах_таарсны_дараах_тусгаарлагчгүй_мөр_юу_ч_хэвлэхгүй(self):
        # Алдаа гарвал машин "гарсан" гэж хэвлэгдээд файлд үлдэх ёсгүй
        мөрүүд = ["1111УБА - 2026-09-23 10:00:00", "2222УБА 2026-09-23 11:00:00"]
        self._бичих(мөрүүд)
        buf = io.StringIO()
        with _одоо(2026, 9, 23, 12, 0), _оролт("1111УБА"), redirect_stdout(buf):
            with self.assertRaises(parking.ФорматАлдаа) as ctx:
                parking.Машин_гарах()
        self.assertIn("2-р мөр", str(ctx.exception))
        self.assertEqual(buf.getvalue(), "Улсын дугаар: ")
        self.assertEqual(self._унших(), "\n".join(мөрүүд) + "\n")

    def test_гарах_хоёр_дахь_таарсан_мөр_алдаатай_бол_юу_ч_хэвлэхгүй(self):
        мөрүүд = ["1111УБА - 2026-09-23 10:00:00", "1111УБА - 10:00"]
        self._бичих(мөрүүд)
        buf = io.StringIO()
        with _одоо(2026, 9, 23, 12, 0), _оролт("1111УБА"), redirect_stdout(buf):
            with self.assertRaises(parking.ФорматАлдаа):
                parking.Машин_гарах()
        self.assertEqual(buf.getvalue(), "Улсын дугаар: ")
        self.assertEqual(self._унших(), "\n".join(мөрүүд) + "\n")

    def test_гарах_өөр_дугаарын_тусгаарлагчгүй_мөр_алдаа_өгнө(self):
        # Тусгаарлагчгүй мөрийн дугаарыг таамаглахгүй тул хайж буй дугаараас үл хамааран алдаа өгнө
        мөрүүд = ["2222УБА 2026-09-23 09:00:00", "1111УБА - 2026-09-23 10:00:00"]
        self._бичих(мөрүүд)
        with self.assertRaises(parking.ФорматАлдаа) as ctx:
            self._ажиллуулах(parking.Машин_гарах, "1111УБА")
        self.assertIn("1-р мөр", str(ctx.exception))
        self.assertEqual(self._унших(), "\n".join(мөрүүд) + "\n")


class MainИнтеграцТест(ФайлТест):
    def test_кирилл_дугаар_бүртгэнэ(self):
        with _одоо(2026, 9, 23, 12, 30, 45), _оролт("1", "2255УБӨ", "6"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                parking.main()
        self.assertEqual(self._унших(), "2255УБӨ - 2026-09-23 12:30:45\n")


if __name__ == "__main__":
    unittest.main()
