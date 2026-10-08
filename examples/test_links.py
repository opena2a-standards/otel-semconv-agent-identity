import pathlib
import unittest

FOLDER = pathlib.Path(__file__).resolve().parent
OLD_REPO_URL = "github.com/opena2a-org/otel-semconv-agent-identity"
REPO_URL = "github.com/opena2a-standards/otel-semconv-agent-identity"


def lines_with(path, needle):
    return [n for n, line in enumerate(path.read_text().splitlines(), 1) if needle in line]


class RepoLinkTest(unittest.TestCase):
    def test_examples_link_the_current_repository(self):
        for path in sorted(FOLDER.glob("*.py")) + sorted(FOLDER.glob("*.md")):
            if path.name == pathlib.Path(__file__).name:
                continue
            with self.subTest(file=path.name):
                self.assertEqual(lines_with(path, OLD_REPO_URL), [])

    def test_langchain_bridge_names_the_proposal_repository(self):
        self.assertTrue(lines_with(FOLDER / "langchain.py", REPO_URL))


if __name__ == "__main__":
    unittest.main()
