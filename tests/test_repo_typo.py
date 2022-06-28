import unittest

from src.repo_readme_typo import RepoReadmeTypo


class TestRepoTypo(unittest.TestCase):
    def test_get_typo_context_1(self):
        test_readme = "This is sumple text.Here is another sentence"
        test_typo = "sumple"
        test_suggested = "simple"

        repo_typo = RepoReadmeTypo(
            repository="", readme=test_readme, word=test_typo, suggested=test_suggested
        )
        context = repo_typo.get_typo_with_context()

        self.assertEqual("This is *sumple* text", context)

    def test_get_typo_context_2(self):
        test_readme = """code-block::

     ■: not null
     □: null
     $: variable

  Scalar example:

  ."""
        test_typo = "Scalar"
        test_suggested = "Scala"

        repo_typo = RepoReadmeTypo(
            repository="", readme=test_readme, word=test_typo, suggested=test_suggested
        )

        context = repo_typo.get_typo_with_context()

        self.assertEqual("*Scalar* example", context)

    def test_get_typo_context_3(self):
        test_readme = """
        # CogVideo

This is the official repo for the paper: CogVideo: Large-scale Pretraining for Text-to-Video Generation via Transformers


https
        """

        test_typo = "Pretraining"
        test_suggested = "Retaining"

        repo_typo = RepoReadmeTypo(
            repository="", readme=test_readme, word=test_typo, suggested=test_suggested
        )

        context = repo_typo.get_typo_with_context()

        self.assertEqual("Large-scale *Pretraining* for Text-to-Video Generation", context)


if __name__ == "__main__":
    unittest.main()
