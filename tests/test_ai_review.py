import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.ai_review_service import generate_fallback_reviews, generate_review_suggestions, limit_to_max_words

class AIReviewTestCase(unittest.TestCase):
    def test_limit_to_max_words(self):
        """Test that limit_to_max_words trims long strings to at most 15 words."""
        long_text = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen"
        trimmed = limit_to_max_words(long_text, max_words=15)
        self.assertLessEqual(len(trimmed.split()), 15)

    def test_fallback_reviews_word_limit(self):
        """Test that all generated fallback reviews are strictly 15 words or fewer."""
        roles = [
            ('Dr. Rahul', 'Cardiologist', 'Apex Hospital'),
            ('Aamir', 'Real Estate Advisor', 'Apex Realty'),
            ('Rahul', 'Fashion Consultant', 'Apex Styles'),
            ('Priya', 'Senior Manager', 'Apex Innovations')
        ]
        for name, desig, comp in roles:
            for star in range(1, 6):
                reviews = generate_fallback_reviews(name, desig, comp, star_rating=star)
                for r in reviews:
                    word_count = len(r['review'].split())
                    self.assertLessEqual(
                        word_count, 
                        15, 
                        f"Review exceeded 15 words ({word_count} words): {r['review']}"
                    )

    def test_fallback_doctor_reviews(self):
        """Test fallback generation for healthcare professionals."""
        reviews = generate_fallback_reviews('Dr. Rahul', 'Cardiologist', 'Apex Hospital')
        self.assertEqual(len(reviews), 3)
        self.assertTrue(any('care' in r['review'].lower() or 'doctor' in r['review'].lower() for r in reviews))

    def test_fallback_real_estate_reviews(self):
        """Test fallback generation for real estate roles."""
        reviews = generate_fallback_reviews('Aamir', 'Real Estate Advisor', 'Apex Realty')
        self.assertEqual(len(reviews), 3)
        self.assertTrue(any('property' in r['review'].lower() or 'deal' in r['review'].lower() for r in reviews))

    def test_generate_review_suggestions_structure(self):
        """Test that generate_review_suggestions returns valid structure."""
        res = generate_review_suggestions('Priya', 'Head of Talent', 'Apex Innovations', tone='friendly')
        self.assertTrue(res['success'])
        self.assertIn('reviews', res)
        self.assertEqual(len(res['reviews']), 3)
        for rev in res['reviews']:
            self.assertIn('title', rev)
            self.assertIn('review', rev)
            self.assertIn('tags', rev)
            self.assertLessEqual(len(rev['review'].split()), 15)

    def test_star_ratings_and_categories(self):
        """Test star ratings (1-5) and category custom suggestions."""
        # 5 Star with Menswear & Tailoring
        res_5 = generate_fallback_reviews('Rahul', 'Fashion Consultant', 'Apex Styles', star_rating=5, categories=['Menswear', 'Custom Tailoring'])
        self.assertEqual(len(res_5), 3)
        self.assertEqual(res_5[0]['rating'], 5)
        self.assertTrue(any('menswear' in r['title'].lower() or 'menswear' in r['review'].lower() or 'fitting' in r['review'].lower() for r in res_5))

        # 3 Star review
        res_3 = generate_fallback_reviews('Rahul', 'Fashion Consultant', 'Apex Styles', star_rating=3, categories=['Menswear'])
        self.assertEqual(len(res_3), 3)
        self.assertEqual(res_3[0]['rating'], 3)
        self.assertTrue(any('3 stars' in tag.lower() for r in res_3 for tag in r['tags']))

        # 1 Star review
        res_1 = generate_fallback_reviews('Rahul', 'Fashion Consultant', 'Apex Styles', star_rating=1, categories=['Menswear'])
        self.assertEqual(len(res_1), 3)
        self.assertEqual(res_1[0]['rating'], 1)
        self.assertTrue(any('improvement' in r['title'].lower() or 'below' in r['title'].lower() or 'disappointed' in r['title'].lower() for r in res_1))

if __name__ == '__main__':
    unittest.main()
