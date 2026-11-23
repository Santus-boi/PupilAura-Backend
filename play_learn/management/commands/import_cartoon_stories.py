
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from play_learn.models import (
    CartoonStory,
    CartoonStoryScene,
    CartoonStoryQuestion,
    CartoonStoryAnswer,
)


LEGACY_STORIES = [
    {
        "title": "The Lion and the Little Mouse",
        "slug": "lion-and-mouse",
        "description": "Discover how a tiny mouse helps a mighty lion.",
        "category": "animals",
        "emoji": "🦁",
        "cover_emoji": "🦁🐭",
        "min_age": 3,
        "max_age": 8,
        "duration": 5,
        "lesson": "Kindness and helping others",
        "scenes": [
            ("Narrator", "📖", "Once upon a time, in a beautiful green forest, lived a mighty lion. He was strong, proud and loved sleeping under the big trees."),
            ("Little Mouse", "🐭", "One sunny afternoon, a little mouse ran across the sleeping lion's nose. The lion suddenly woke up!"),
            ("Lion", "🦁", "ROAR! Who disturbed my sleep? You tiny mouse! Why should I not eat you?"),
            ("Little Mouse", "🐭", "Please let me go, mighty lion. One day, I may be able to help you!"),
            ("Narrator", "📖", "The lion laughed, but he decided to let the little mouse go. A few days later, the lion got trapped in a hunter's net."),
            ("Lion", "🦁", "HELP! Somebody please help me! I cannot escape this net!"),
            ("Little Mouse", "🐭", "Don't worry, my friend! I will help you. I have sharp little teeth!"),
            ("Narrator", "📖", "The mouse quickly chewed through the ropes. The lion was free! He thanked the little mouse, and they became the best of friends."),
        ],
        "question": "What lesson does this story teach us?",
        "answers": [
            ("Kindness matters", True),
            ("Only strong people can help", False),
            ("Never make friends", False),
        ],
    },
    {
        "title": "The Honest Little Boy",
        "slug": "honest-boy",
        "description": "A young boy discovers why telling the truth matters.",
        "category": "honesty",
        "emoji": "👦",
        "cover_emoji": "👦💰",
        "min_age": 4,
        "max_age": 10,
        "duration": 4,
        "lesson": "Always tell the truth",
        "scenes": [
            ("Narrator", "📖", "There once lived a boy named Daniel. He loved playing football with his friends after school."),
            ("Daniel", "👦", "Oh no! I accidentally broke my mother's flower vase while playing indoors!"),
            ("Narrator", "📖", "Daniel became afraid. He wondered whether he should hide the broken vase or tell his mother the truth."),
            ("Daniel", "👦", "Mummy, I am sorry. I broke your vase by mistake. I should not have played football inside."),
            ("Mother", "👩", "Thank you for telling me the truth, Daniel. I am not happy about the broken vase, but I am proud of your honesty."),
            ("Narrator", "📖", "Daniel learned that telling the truth takes courage. From that day, he always tried to be honest."),
        ],
        "question": "What should Daniel do when he makes a mistake?",
        "answers": [
            ("Tell the truth", True),
            ("Blame somebody else", False),
            ("Hide what happened", False),
        ],
    },
    {
        "title": "Sharing Is Caring",
        "slug": "sharing-is-caring",
        "description": "Two friends discover the happiness that comes from sharing.",
        "category": "friendship",
        "emoji": "🧒",
        "cover_emoji": "🍎👧",
        "min_age": 3,
        "max_age": 8,
        "duration": 4,
        "lesson": "Sharing and generosity",
        "scenes": [
            ("Narrator", "📖", "Mia and Ben were classmates. One day, Mia brought a delicious lunch to school."),
            ("Ben", "👦", "Mia, your apple looks delicious! I forgot my lunch today."),
            ("Mia", "👧", "You can have half of my apple, Ben. Friends should look after one another!"),
            ("Ben", "👦", "Thank you, Mia! That is very kind of you. I will remember your kindness."),
            ("Narrator", "📖", "They shared their lunch, played together and enjoyed the rest of their day. They discovered that sharing can make everyone happy."),
        ],
        "question": "What did Mia teach Ben?",
        "answers": [
            ("Sharing makes people happy", True),
            ("Food should never be shared", False),
            ("Friends should not help each other", False),
        ],
    },
]


class Command(BaseCommand):
    help = "Import the three original cartoon stories into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the import without saving database changes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        created_stories = 0
        updated_stories = 0
        created_scenes = 0
        created_questions = 0
        created_answers = 0

        try:
            for data in LEGACY_STORIES:
                story, created = CartoonStory.objects.get_or_create(
                    slug=data["slug"],
                    defaults={
                        "title": data["title"],
                        "description": data["description"],
                        "category": data["category"],
                        "emoji": data["emoji"],
                        "cover_emoji": data["cover_emoji"],
                        "min_age": data["min_age"],
                        "max_age": data["max_age"],
                        "estimated_duration_minutes": data["duration"],
                        "lesson": data["lesson"],
                        "status": CartoonStory.Status.PUBLISHED,
                    },
                )

                if created:
                    created_stories += 1
                else:
                    # Do not overwrite existing story content.
                    self.stdout.write(
                        self.style.WARNING(
                            f"Story already exists; preserving it: {story.title}"
                        )
                    )
                    updated_stories += 1

                for number, (character, emoji, text) in enumerate(
                    data["scenes"], start=1
                ):
                    _, scene_created = CartoonStoryScene.objects.get_or_create(
                        story=story,
                        scene_number=number,
                        defaults={
                            "character_name": character,
                            "character_emoji": emoji,
                            "text": text,
                            "is_published": True,
                        },
                    )

                    if scene_created:
                        created_scenes += 1

                question, question_created = (
                    CartoonStoryQuestion.objects.get_or_create(
                        story=story,
                        question_number=1,
                        defaults={
                            "question_text": data["question"],
                            "is_published": True,
                        },
                    )
                )

                if question_created:
                    created_questions += 1

                for order, (answer_text, is_correct) in enumerate(
                    data["answers"], start=1
                ):
                    _, answer_created = (
                        CartoonStoryAnswer.objects.get_or_create(
                            question=question,
                            answer_text=answer_text,
                            defaults={
                                "is_correct": is_correct,
                                "order": order,
                            },
                        )
                    )

                    if answer_created:
                        created_answers += 1

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        "Dry run complete. All database changes were rolled back."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("Cartoon story import completed.")
                )

            self.stdout.write(f"New stories: {created_stories}")
            self.stdout.write(f"Existing stories preserved: {updated_stories}")
            self.stdout.write(f"New scenes: {created_scenes}")
            self.stdout.write(f"New questions: {created_questions}")
            self.stdout.write(f"New answers: {created_answers}")

        except Exception as exc:
            raise CommandError(
                f"Cartoon story import failed: {exc}"
            ) from exc
