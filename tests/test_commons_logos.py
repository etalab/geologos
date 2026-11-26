import unittest

from commons_logos.matching import match_insee_code, normalize_key
from commons_logos.planning import plan_files

INDEX = {normalize_key(name): code for name, code in [
    ('Agen', '47001'), ('Cergy', '95127'), ('Rougé', '44146'),
    ('Grand', '88212'), ('Tours', '37261'), ('Saintes', '17415'),
    ('Port', '00001'), ('La Riche', '37195'), ('Arradon', '56003'),
]}


class MatchingTest(unittest.TestCase):

    def test_whole_names_are_matched(self):
        cases = {
            "File:Logo ville d'Agen.jpg": '47001',
            'File:Logo de la ville d\'Agen.jpg': '47001',
            'File:LogoVilledeSaintes.png': '17415',
            'File:Logo-Cergy-Rouge-web.png': '95127',
            'File:Logo La-Riche.jpg': '37195',
            'File:Logo arradon-1024x574.png': '56003',
        }
        for title, code in cases.items():
            with self.subTest(title=title):
                self.assertEqual(match_insee_code(title, INDEX), code)

    def test_partial_names_are_rejected(self):
        for title in ('File:Logo Grand Quevilly.png',
                      'File:Tours Métropole Val de Loire.jpg',
                      'File:LOGO LE PORT 2016.jpg'):
            with self.subTest(title=title):
                self.assertIsNone(match_insee_code(title, INDEX))


class PlanningTest(unittest.TestCase):

    def test_names_and_extensions(self):
        def info(title, mime):
            return {'title': title, 'mime': mime, 'url': '', 'size': 0,
                    'sha1': ''}

        infos = {t: info(t, m) for t, m in [
            ('File:Logo Agen.jpg', 'image/png'),
            ('File:Z.svg', 'image/svg+xml'),
        ]}
        plan = plan_files(infos, {}, {'File:Z.svg': '47001',
                                      'File:Logo Agen.jpg': '47001'}, INDEX)
        # The extension follows the real format.
        self.assertEqual([row['path'] for row in plan],
                         ['FR-47001.png', 'FR-47001.svg'])


if __name__ == '__main__':
    unittest.main()
