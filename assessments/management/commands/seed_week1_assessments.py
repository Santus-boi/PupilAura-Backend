from django.core.management.base import BaseCommand
from django.db import transaction

from assessments.models import Choice, Question, Quiz
from learning.models import Lesson


class Command(BaseCommand):
    help = "Create or update Week 1 lesson assessments for JSS 1 Computer Studies."

    LESSONS = {
        "Introduction to Computers": [
            {
                "question": "What is a computer?",
                "choices": [
                    ("A machine that processes data into useful information", True),
                    ("A machine used only for playing games", False),
                    ("A device used only for typing documents", False),
                    ("A machine used only for storing electricity", False),
                ],
            },
            {
                "question": (
                    "Which stage of computer operation changes data "
                    "into useful information?"
                ),
                "choices": [
                    ("Processing", True),
                    ("Input", False),
                    ("Storage", False),
                    ("Output", False),
                ],
            },
            {
                "question": "Which of the following is an input device?",
                "choices": [
                    ("Keyboard", True),
                    ("Monitor", False),
                    ("Speaker", False),
                    ("Printer", False),
                ],
            },
            {
                "question": (
                    "What is the result produced after a computer "
                    "processes data?"
                ),
                "choices": [
                    ("Information", True),
                    ("Raw data", False),
                    ("Electricity", False),
                    ("Keyboard input", False),
                ],
            },
            {
                "question": (
                    "In your own words, describe how a computer "
                    "processes data and produces useful information."
                ),
                "question_type": Question.QuestionType.THEORY,
                "points": 2,
            },
        ],

        "Counting and the Need for Computing Devices": [
            {
                "question": "Why did people develop methods of counting?",
                "choices": [
                    ("To keep track of quantities and amounts", True),
                    ("To make computers run faster", False),
                    ("To create electronic screens", False),
                    ("To replace written language", False),
                ],
            },
            {
                "question": (
                    "Which of the following was an early method of "
                    "helping people count?"
                ),
                "choices": [
                    ("Using fingers", True),
                    ("Using a computer mouse", False),
                    ("Using a printer", False),
                    ("Using a monitor", False),
                ],
            },
            {
                "question": (
                    "What was one limitation of using fingers for counting?"
                ),
                "choices": [
                    (
                        "They could represent only a limited range of quantities",
                        True,
                    ),
                    ("They required electricity", False),
                    ("They could not represent numbers", False),
                    ("They could only be used by computers", False),
                ],
            },
            {
                "question": (
                    "Why did people begin developing counting devices?"
                ),
                "choices": [
                    (
                        "To help handle larger quantities more accurately",
                        True,
                    ),
                    ("To produce computer games", False),
                    (
                        "To replace all forms of communication",
                        False,
                    ),
                    ("To create internet connections", False),
                ],
            },
            {
                "question": (
                    "In your own words, explain why people needed "
                    "to develop better counting devices."
                ),
                "question_type": Question.QuestionType.THEORY,
                "points": 2,
            },
        ],

        "Counting Boards and Early Computing Tools": [
            {
                "question": "What was a counting board mainly used for?",
                "choices": [
                    (
                        "Helping people perform calculations and keep track of quantities",
                        True,
                    ),
                    ("Displaying television programmes", False),
                    ("Connecting computers to the internet", False),
                    ("Printing books automatically", False),
                ],
            },
            {
                "question": (
                    "What could tally marks help people keep track of?"
                ),
                "choices": [
                    ("The number of items or events", True),
                    ("The speed of a computer processor", False),
                    ("The brightness of a monitor", False),
                    ("The temperature of a keyboard", False),
                ],
            },
            {
                "question": (
                    "Which of the following was used as an early "
                    "counting aid?"
                ),
                "choices": [
                    ("Counting rods", True),
                    ("Computer monitor", False),
                    ("Keyboard", False),
                    ("Printer cartridge", False),
                ],
            },
            {
                "question": (
                    "Why was grouping marks useful when counting?"
                ),
                "choices": [
                    (
                        "It made larger quantities easier to organize and count",
                        True,
                    ),
                    ("It made numbers disappear", False),
                    ("It allowed electricity to flow", False),
                    ("It created computer programs", False),
                ],
            },
            {
                "question": (
                    "In your own words, describe how early counting "
                    "tools helped people perform calculations."
                ),
                "question_type": Question.QuestionType.THEORY,
                "points": 2,
            },
        ],

        "The Abacus": [
            {
                "question": "What is an abacus?",
                "choices": [
                    ("A manual device used for calculation", True),
                    ("An electronic computer", False),
                    ("A type of printer", False),
                    ("A computer operating system", False),
                ],
            },
            {
                "question": (
                    "What is moved on the rods or wires of an abacus?"
                ),
                "choices": [
                    ("Beads", True),
                    ("Keys", False),
                    ("Pixels", False),
                    ("Disks", False),
                ],
            },
            {
                "question": (
                    "Which mathematical idea is important when using "
                    "an abacus?"
                ),
                "choices": [
                    ("Place value", True),
                    ("Internet browsing", False),
                    ("Screen resolution", False),
                    ("File compression", False),
                ],
            },
            {
                "question": (
                    "Does a traditional abacus require electricity "
                    "to perform calculations?"
                ),
                "choices": [
                    ("No", True),
                    ("Yes, always", False),
                    ("Only when adding", False),
                    ("Only when subtracting", False),
                ],
            },
            {
                "question": (
                    "In your own words, explain how an abacus "
                    "can be used to perform arithmetic calculations."
                ),
                "question_type": Question.QuestionType.THEORY,
                "points": 2,
            },
        ],

        "From the Abacus to the Modern Computer": [
            {
                "question": (
                    "Which sequence best represents the general "
                    "development of computing tools?"
                ),
                "choices": [
                    (
                        "Natural counting methods → counting tools → "
                        "abacus → mechanical devices → electronic computers",
                        True,
                    ),
                    (
                        "Electronic computers → abacus → fingers → "
                        "mechanical devices",
                        False,
                    ),
                    (
                        "Modern computers → counting boards → fingers → "
                        "abacus",
                        False,
                    ),
                    (
                        "Abacus → modern computers → counting boards → fingers",
                        False,
                    ),
                ],
            },
            {
                "question": (
                    "Modern computers primarily use what type of technology?"
                ),
                "choices": [
                    ("Electronic technology", True),
                    ("Only wooden beads", False),
                    ("Only stones and sticks", False),
                    ("Only handwritten marks", False),
                ],
            },
            {
                "question": (
                    "How are mechanical computing devices different "
                    "from traditional manual counting tools?"
                ),
                "choices": [
                    (
                        "They use mechanical parts to perform calculations",
                        True,
                    ),
                    ("They always require the internet", False),
                    ("They cannot represent numbers", False),
                    ("They are made only from paper", False),
                ],
            },
            {
                "question": (
                    "What is one major advantage of modern computers "
                    "over early counting tools?"
                ),
                "choices": [
                    (
                        "They can process large amounts of data very quickly",
                        True,
                    ),
                    ("They can only perform one calculation", False),
                    ("They do not process information", False),
                    ("They cannot store data", False),
                ],
            },
            {
                "question": (
                    "In your own words, describe how computing devices "
                    "developed from early counting tools into modern computers."
                ),
                "question_type": Question.QuestionType.THEORY,
                "points": 2,
            },
        ],

        "Comparing Early Counting Tools with Modern Computers": [
            {
                "question": "How were many early counting tools operated?",
                "choices": [
                    ("Manually", True),
                    ("Automatically through the internet", False),
                    ("Using artificial intelligence", False),
                    ("Using wireless networks", False),
                ],
            },
            {
                "question": (
                    "What is a major difference between an abacus "
                    "and a modern computer?"
                ),
                "choices": [
                    (
                        "An abacus is manually operated, while a modern "
                        "computer uses electronic technology",
                        True,
                    ),
                    ("Both are electronic computers", False),
                    ("A modern computer uses only beads", False),
                    ("An abacus requires an internet connection", False),
                ],
            },
            {
                "question": (
                    "Compared with early counting tools, modern "
                    "computers can generally store:"
                ),
                "choices": [
                    ("Much larger amounts of data", True),
                    ("Only one number", False),
                    ("No information", False),
                    ("Only physical objects", False),
                ],
            },
            {
                "question": (
                    "What is one important advantage of modern computers?"
                ),
                "choices": [
                    (
                        "They can perform many different types of tasks",
                        True,
                    ),
                    ("They can only perform counting", False),
                    ("They cannot process information", False),
                    ("They can only work without electricity", False),
                ],
            },
            {
                "question": (
                    "In your own words, compare an early counting tool "
                    "such as the abacus with a modern computer."
                ),
                "question_type": Question.QuestionType.THEORY,
                "points": 2,
            },
        ],
    }

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Starting Week 1 lesson assessment setup..."
            )
        )
        self.stdout.write("")

        created_quizzes = 0
        updated_quizzes = 0

        created_questions = 0
        updated_questions = 0
        deleted_questions = 0

        created_choices = 0
        updated_choices = 0
        deleted_choices = 0

        for lesson_title, questions_data in self.LESSONS.items():

            try:
                lesson = Lesson.objects.get(
                    title=lesson_title,
                    week__number=1,
                    week__term__subject__name="Computer Studies",
                    week__term__subject__school_class__name="JSS 1",
                )

            except Lesson.DoesNotExist:

                self.stdout.write(
                    self.style.ERROR(
                        f"Lesson not found: {lesson_title}"
                    )
                )

                continue

            except Lesson.MultipleObjectsReturned:

                self.stdout.write(
                    self.style.ERROR(
                        f"Multiple lessons found: {lesson_title}. "
                        "Please check the curriculum data."
                    )
                )

                continue

            quiz, quiz_created = Quiz.objects.get_or_create(
                lesson=lesson,
                defaults={
                    "title": f"{lesson.title} Assessment",
                    "description": (
                        f"Test your understanding of "
                        f"{lesson.title}."
                    ),
                    "pass_mark": 50,
                    "published": True,
                },
            )

            if quiz_created:

                created_quizzes += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created quiz: {quiz.title}"
                    )
                )

            else:

                updated_quizzes += 1

                quiz.title = f"{lesson.title} Assessment"
                quiz.description = (
                    f"Test your understanding of "
                    f"{lesson.title}."
                )
                quiz.pass_mark = 50
                quiz.published = True

                quiz.save(
                    update_fields=[
                        "title",
                        "description",
                        "pass_mark",
                        "published",
                        "updated_at",
                    ]
                )

                self.stdout.write(
                    f"Updated quiz: {quiz.title}"
                )

            # ---------------------------------------------------------
            # Synchronize the questions defined in LESSONS.
            # ---------------------------------------------------------

            valid_orders = set(
                range(
                    1,
                    len(questions_data) + 1,
                )
            )

            # Remove questions that existed previously but are no
            # longer part of the current assessment definition.
            stale_questions = (
                Question.objects
                .filter(quiz=quiz)
                .exclude(order__in=valid_orders)
            )

            stale_question_count = stale_questions.count()

            if stale_question_count:

                deleted_questions += stale_question_count

                deleted_choice_count, _ = (
                    Choice.objects
                    .filter(question__in=stale_questions)
                    .delete()
                )

                deleted_choices += deleted_choice_count

                stale_questions.delete()

                self.stdout.write(
                    self.style.WARNING(
                        f"Removed {stale_question_count} old "
                        f"question(s) from: {quiz.title}"
                    )
                )

            # ---------------------------------------------------------
            # Create or update current questions.
            # ---------------------------------------------------------

            for question_index, question_data in enumerate(
                questions_data,
                start=1,
            ):

                question_type = question_data.get(
                    "question_type",
                    Question.QuestionType.OBJECTIVE,
                )

                points = question_data.get(
                    "points",
                    1,
                )

                question, question_created = (
                    Question.objects.update_or_create(
                        quiz=quiz,
                        order=question_index,
                        defaults={
                            "text": question_data["question"],
                            "question_type": question_type,
                            "points": points,
                        },
                    )
                )

                if question_created:

                    created_questions += 1

                else:

                    updated_questions += 1

                # -----------------------------------------------------
                # Objective question choices.
                # -----------------------------------------------------

                if question_type == Question.QuestionType.OBJECTIVE:

                    choices_data = question_data.get(
                        "choices",
                        [],
                    )

                    valid_choice_orders = set(
                        range(
                            1,
                            len(choices_data) + 1,
                        )
                    )

                    # Remove choices that no longer exist in the
                    # current question definition.
                    stale_choices = (
                        Choice.objects
                        .filter(question=question)
                        .exclude(order__in=valid_choice_orders)
                    )

                    stale_choice_count = stale_choices.count()

                    if stale_choice_count:

                        deleted_choices += stale_choice_count
                        stale_choices.delete()

                    # Create or update current choices.
                    for choice_index, (
                        choice_text,
                        is_correct,
                    ) in enumerate(
                        choices_data,
                        start=1,
                    ):

                        choice, choice_created = (
                            Choice.objects.update_or_create(
                                question=question,
                                order=choice_index,
                                defaults={
                                    "text": choice_text,
                                    "is_correct": is_correct,
                                },
                            )
                        )

                        if choice_created:

                            created_choices += 1

                        else:

                            updated_choices += 1

                # -----------------------------------------------------
                # Theory and practical questions must have no choices.
                # -----------------------------------------------------

                else:

                    deleted_count, _ = (
                        Choice.objects
                        .filter(question=question)
                        .delete()
                    )

                    deleted_choices += deleted_count

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "=========================================="
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "WEEK 1 ASSESSMENT SETUP COMPLETE"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "=========================================="
            )
        )

        self.stdout.write(
            f"Quizzes created: {created_quizzes}"
        )

        self.stdout.write(
            f"Quizzes updated: {updated_quizzes}"
        )

        self.stdout.write(
            f"Questions created: {created_questions}"
        )

        self.stdout.write(
            f"Questions updated: {updated_questions}"
        )

        self.stdout.write(
            f"Questions deleted: {deleted_questions}"
        )

        self.stdout.write(
            f"Choices created: {created_choices}"
        )

        self.stdout.write(
            f"Choices updated: {updated_choices}"
        )

        self.stdout.write(
            f"Choices deleted: {deleted_choices}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "You can now test the lesson assessment flow."
            )
        )

        self.stdout.write("")