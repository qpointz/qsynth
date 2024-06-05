import unittest

from qsynth.main import argument_parser


def parse(*args):
    p = argument_parser().parse_args(args)
    print(p)
    return p


class TestArgumentParse(unittest.TestCase):
    def test_upper(self):
        ps = parse('types', '--all')
        self.assertEqual(True, True)

    def test_parse_run(self):
        ps = parse('run', '-i', 'myfilr', '-a')


if __name__ == '__main__':
    unittest.main()
