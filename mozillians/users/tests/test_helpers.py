from nose.tools import eq_

from mozillians.common.tests import TestCase
from mozillians.users import AVAILABLE_LANGUAGES, get_languages_for_locale


class GetTranslatedLanguagesTests(TestCase):
    def test_invalid_locale(self):
        """Test with invalid locale, must default to english translations."""
        languages = get_languages_for_locale('foobar')
        english_languages = get_languages_for_locale('en')
        eq_(english_languages, languages)

    def test_valid_locale(self):
        get_languages_for_locale('en')
        self.assertIn('en', list(AVAILABLE_LANGUAGES.keys()))
