import unittest

from src.typo import Typo


class TestRepoTypo(unittest.TestCase):
    def test_get_typo_context_1(self):
        test_readme = 'This is sumple text.Here is another sentence'
        test_typo = 'sumple'
        test_suggested = 'simple'

        repo_typo = Typo(
            repository='',
            readme=test_readme,
            word=test_typo,
            suggested=test_suggested
        )
        context_head, context_tail = repo_typo.get_context()

        self.assertEqual('This is', context_head)
        self.assertEqual('text', context_tail)

    def test_get_typo_context_2(self):
        test_readme = '''code-block::

     ■: not null
     □: null
     $: variable

  Scalar example:

  .'''
        test_typo = 'Scalar'
        test_suggested = 'Scala'

        repo_typo = Typo(
            repository='',
            readme=test_readme,
            word=test_typo,
            suggested=test_suggested
        )

        context_head, context_tail = repo_typo.get_context()

        self.assertEqual('', context_head)
        self.assertEqual('example', context_tail)

    def test_get_typo_context_3(self):
        test_readme = '''
        # CogVideo

This is the official repo for the paper: CogVideo: Large-scale Pretraining for Text-to-Video Generation via Transformers


https
        '''

        test_typo = 'Pretraining'
        test_suggested = 'Retaining'

        repo_typo = Typo(
            repository='',
            readme=test_readme,
            word=test_typo,
            suggested=test_suggested
        )

        context_head, context_tail = repo_typo.get_context()

        self.assertEqual('Large-scale', context_head)
        self.assertEqual('for Text-to-Video Generation', context_tail)


if __name__ == '__main__':
    unittest.main()
