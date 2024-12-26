from django.test import TestCase
from apps.question_handling.models import Questions
from django.core.exceptions import ValidationError

class QuestionsModelTest(TestCase):
    def test_valid_multiple_choice_question(self):
        """
        Teste une question MULTIPLE_CHOICE valide.
        """
        question = Questions(
            text="Quels sont vos langages préférés ?",
            type="MULTIPLE_CHOICE",
            configuration={"options": ["Python", "JavaScript", "C++", "Java"]},
        )
        try:
            question.clean()  # Validation explicite
            question.save()   # Sauvegarde si tout est valide
            self.assertTrue(True)
        except ValidationError:
            self.fail("ValidationError levée pour une question MULTIPLE_CHOICE valide.")

    def test_invalid_multiple_choice_question_with_too_many_options(self):
        """
        Teste une question MULTIPLE_CHOICE avec trop d'options.
        """
        question = Questions(
            text="Quels sont vos langages préférés ?",
            type="MULTIPLE_CHOICE",
            configuration={"options": ["Python", "JavaScript", "C++", "Java", "Ruby"]},  # 5 options
        )
        with self.assertRaises(ValidationError) as context:
            question.clean()
        self.assertIn("Maximum 4 options allowed for MULTIPLE_CHOICE questions", str(context.exception))

    def test_valid_table_question(self):
        """
        Teste une question TABLE valide.
        """
        question = Questions(
            text="Listez vos expériences professionnelles",
            type="TABLE",
            configuration={"columns": ["Entreprise", "Poste", "Durée"]},  # 3 colonnes
        )
        try:
            question.clean()
            question.save()
            self.assertTrue(True)
        except ValidationError:
            self.fail("ValidationError levée pour une question TABLE valide.")

    def test_invalid_table_question_with_too_many_columns(self):
        """
        Teste une question TABLE avec trop de colonnes.
        """
        question = Questions(
            text="Listez vos expériences professionnelles",
            type="TABLE",
            configuration={"columns": ["Entreprise", "Poste", "Durée", "Localisation"]},  # 4 colonnes
        )
        with self.assertRaises(ValidationError) as context:
            question.clean()
        self.assertIn("Maximum 3 columns allowed for TABLE questions", str(context.exception))

    def test_invalid_table_question_with_wrong_type(self):
        """
        Teste une question TABLE avec une configuration invalide (columns n'est pas une liste).
        """
        question = Questions(
            text="Listez vos expériences professionnelles",
            type="TABLE",
            configuration={"columns": "Entreprise, Poste, Durée"},  # Mauvais type : chaîne
        )
        with self.assertRaises(ValidationError) as context:
            question.clean()
        self.assertIn("Columns must be a list", str(context.exception))

    def test_invalid_configuration_not_a_dict(self):
        """
        Teste une question avec une configuration qui n'est pas un dictionnaire.
        """
        question = Questions(
            text="Configuration invalide",
            type="TABLE",
            configuration="Invalid configuration",  # Mauvais type : chaîne
        )
        with self.assertRaises(ValidationError) as context:
            question.clean()
        self.assertIn("Configuration must be a valid JSON object (dictionary)", str(context.exception))
