from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import (
    Story,
    StoryChapter,
    StoryBookmark,
    CartoonStory,
)
import json

from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

from .models import PlayGame, GameAttempt


def home(request):
    """
    Main landing page for PupilAura Play & Learn.
    Loads published games dynamically from the PlayGame database.
    """

    from django.urls import reverse, NoReverseMatch
    from .models import PlayGame

    age_groups = [
        {
            "name": "Little Explorers",
            "age": "3–5 years",
            "description": "Discover letters, colours, shapes and sounds.",
            "icon": "bi-balloon-heart-fill",
            "theme": "little",
        },
        {
            "name": "Young Learners",
            "age": "6–8 years",
            "description": "Build spelling, reading and mathematics skills.",
            "icon": "bi-stars",
            "theme": "young",
        },
        {
            "name": "Junior Explorers",
            "age": "9–12 years",
            "description": "Explore science, puzzles, vocabulary and adventures.",
            "icon": "bi-rocket-takeoff-fill",
            "theme": "junior",
        },
        {
            "name": "Teen Innovators",
            "age": "13–17 years",
            "description": "Challenge your mind with logic, coding and strategy.",
            "icon": "bi-lightning-charge-fill",
            "theme": "teen",
        },
        {
            "name": "Adult Zone",
            "age": "18+ years",
            "description": "Enjoy brain training, puzzles and knowledge challenges.",
            "icon": "bi-trophy-fill",
            "theme": "adult",
        },
    ]

    play_categories = [
        {
            "name": "Arcade Games",
            "description": "Play exciting games, beat challenges and unlock achievements.",
            "icon": "bi-controller",
            "theme": "arcade",
        },
        {
            "name": "Learn & Play",
            "description": "Turn mathematics, spelling, science and other subjects into games.",
            "icon": "bi-mortarboard-fill",
            "theme": "learn",
        },
        {
            "name": "Speaking Lab",
            "description": "Listen to words and practise pronunciation and speaking.",
            "icon": "bi-mic-fill",
            "theme": "speaking",
        },
        {
            "name": "Cartoon World",
            "description": "Discover animated stories, characters and interactive adventures.",
            "icon": "bi-film",
            "theme": "cartoon",
        },
    ]

    # Game presentation settings.
    game_appearances = {
        "alphabet_adventure": {
            "icon": "🔤",
            "background": "#fff0c2",
        },
        "math_challenge": {
            "icon": "🔢",
            "background": "#e2edff",
        },
        "word_builder": {
            "icon": "🧩",
            "background": "#e4f8e9",
        },
        "pronunciation_lab": {
            "icon": "🎙️",
            "background": "#f4e6ff",
        },
        "cartoon_adventure": {
            "icon": "🐉",
            "background": "#ffe6e8",
        },
        "memory_match": {
            "icon": "🧠",
            "background": "#fff0dc",
        },
        "bubble_pop": {
            "icon": "🫧",
            "background": "#dff6ff",
        },
        "whack_a_mole": {
            "icon": "🐹",
            "background": "#fce7d8",
        },
        "number_ninja": {
            "icon": "🥷",
            "background": "#e5e7ff",
        },
        "color_rush": {
            "icon": "🎨",
            "background": "#ffe4ef",
        },
        "simon_says": {
            "icon": "🎯",
            "background": "#e0f2fe",
        },
        "treasure_hunt": {
            "icon": "💎",
            "background": "#fff1cc",
        },
        "maze_runner": {
            "icon": "🌀",
            "background": "#e0f2e9",
        },
        "chess_master": {
            "icon": "♟️",
            "background": "#e8e8e8",
        },
        "sudoku_challenge": {
            "icon": "🔲",
            "background": "#e0eaff",
        },
        "detective_case_files": {
            "icon": "🔎",
            "background": "#f1e6d8",
        },
        "tower_defense": {
            "icon": "🏰",
            "background": "#e8e4ff",
        },
        "word_master": {
            "icon": "📚",
            "background": "#e5f8e9",
        },
        "business_tycoon": {
            "icon": "💼",
            "background": "#e0edff",
        },
        "stock_market_simulator": {
            "icon": "📈",
            "background": "#dcfce7",
        },
    }

    # Retrieve published games from the database.
    games = PlayGame.objects.filter(
        is_published=True
    ).order_by("order", "name")

    # Resolve each game's existing URL.
    for game in games:
        try:
            game.play_url = (
                reverse(f"play_learn:{game.url_name}")
                if game.url_name
                else ""
            )
        except NoReverseMatch:
            game.play_url = ""

        appearance = game_appearances.get(
            game.url_name,
            {
                "icon": "🎮",
                "background": "#eee9ff",
            },
        )

        game.display_icon = appearance["icon"]
        game.art_background = appearance["background"]

    context = {
        "age_groups": age_groups,
        "play_categories": play_categories,
        "games": games,
    }

    return render(
        request,
        "play_learn/home.html",
        context,
    )

def alphabet_adventure(request):
    """
    Alphabet Adventure game page.
    """

    letters = [
        {"letter": "A", "word": "Apple", "emoji": "🍎"},
        {"letter": "B", "word": "Ball", "emoji": "⚽"},
        {"letter": "C", "word": "Cat", "emoji": "🐱"},
        {"letter": "D", "word": "Dog", "emoji": "🐶"},
        {"letter": "E", "word": "Elephant", "emoji": "🐘"},
        {"letter": "F", "word": "Fish", "emoji": "🐟"},
        {"letter": "G", "word": "Giraffe", "emoji": "🦒"},
        {"letter": "H", "word": "House", "emoji": "🏠"},
        {"letter": "I", "word": "Ice cream", "emoji": "🍦"},
        {"letter": "J", "word": "Juice", "emoji": "🧃"},
        {"letter": "K", "word": "Kite", "emoji": "🪁"},
        {"letter": "L", "word": "Lion", "emoji": "🦁"},
        {"letter": "M", "word": "Monkey", "emoji": "🐵"},
        {"letter": "N", "word": "Nest", "emoji": "🪺"},
        {"letter": "O", "word": "Orange", "emoji": "🍊"},
        {"letter": "P", "word": "Penguin", "emoji": "🐧"},
        {"letter": "Q", "word": "Queen", "emoji": "👑"},
        {"letter": "R", "word": "Rabbit", "emoji": "🐰"},
        {"letter": "S", "word": "Sun", "emoji": "☀️"},
        {"letter": "T", "word": "Tiger", "emoji": "🐯"},
        {"letter": "U", "word": "Umbrella", "emoji": "☂️"},
        {"letter": "V", "word": "Van", "emoji": "🚐"},
        {"letter": "W", "word": "Whale", "emoji": "🐳"},
        {"letter": "X", "word": "Xylophone", "emoji": "🎼"},
        {"letter": "Y", "word": "Yak", "emoji": "🐂"},
        {"letter": "Z", "word": "Zebra", "emoji": "🦓"},
    ]

    context = {
        "letters": letters,
    }

    return render(
        request,
        "play_learn/alphabet_adventure.html",
        context,
    )

def math_challenge(request):
    """
    Math Challenge game for children aged 6–8.
    """

    difficulty_levels = [
        {
            "value": "easy",
            "name": "Easy",
            "description": "Simple addition and subtraction.",
            "icon": "🌱",
            "time_limit": 90,
            "question_count": 10,
        },
        {
            "value": "medium",
            "name": "Medium",
            "description": "Bigger numbers and mixed operations.",
            "icon": "🚀",
            "time_limit": 75,
            "question_count": 10,
        },
        {
            "value": "hard",
            "name": "Hard",
            "description": "Multiplication, division and tougher calculations.",
            "icon": "🏆",
            "time_limit": 60,
            "question_count": 10,
        },
    ]

    operations = [
        {
            "value": "addition",
            "name": "Addition",
            "symbol": "+",
        },
        {
            "value": "subtraction",
            "name": "Subtraction",
            "symbol": "−",
        },
        {
            "value": "multiplication",
            "name": "Multiplication",
            "symbol": "×",
        },
        {
            "value": "division",
            "name": "Division",
            "symbol": "÷",
        },
    ]

    context = {
        "difficulty_levels": difficulty_levels,
        "operations": operations,
    }

    return render(
        request,
        "play_learn/math_challenge.html",
        context,
    )

def word_builder(request):
    """
    Word Builder spelling game for children aged 6–8.
    """

    words = [
        {
            "word": "APPLE",
            "emoji": "🍎",
            "hint": "A red or green fruit.",
            "category": "Fruits",
        },
        {
            "word": "TIGER",
            "emoji": "🐯",
            "hint": "A large wild cat with black stripes.",
            "category": "Animals",
        },
        {
            "word": "HOUSE",
            "emoji": "🏠",
            "hint": "A place where people live.",
            "category": "Places",
        },
        {
            "word": "PLANT",
            "emoji": "🌱",
            "hint": "It grows in soil and needs water.",
            "category": "Nature",
        },
        {
            "word": "CHAIR",
            "emoji": "🪑",
            "hint": "You sit on it.",
            "category": "Objects",
        },
        {
            "word": "BREAD",
            "emoji": "🍞",
            "hint": "A food often eaten at breakfast.",
            "category": "Food",
        },
        {
            "word": "WATER",
            "emoji": "💧",
            "hint": "You drink it to stay hydrated.",
            "category": "Nature",
        },
        {
            "word": "SNAKE",
            "emoji": "🐍",
            "hint": "A long reptile without legs.",
            "category": "Animals",
        },
        {
            "word": "CLOUD",
            "emoji": "☁️",
            "hint": "You see it floating in the sky.",
            "category": "Nature",
        },
        {
            "word": "GRAPE",
            "emoji": "🍇",
            "hint": "A small fruit that grows in bunches.",
            "category": "Fruits",
        },
        {
            "word": "MOUSE",
            "emoji": "🐭",
            "hint": "A small animal with a long tail.",
            "category": "Animals",
        },
        {
            "word": "SMILE",
            "emoji": "😊",
            "hint": "You make this when you are happy.",
            "category": "Feelings",
        },
    ]

    return render(
        request,
        "play_learn/word_builder.html",
        {
            "words": words,
        },
    )

def pronunciation_lab(request):
    """
    Pronunciation Lab for listening and speaking practice.
    """

    pronunciation_words = [
        {
            "word": "Apple",
            "emoji": "🍎",
            "category": "Fruits",
            "hint": "A fruit that can be red or green.",
        },
        {
            "word": "Beautiful",
            "emoji": "🌸",
            "category": "Everyday Words",
            "hint": "Something pleasant to look at.",
        },
        {
            "word": "Elephant",
            "emoji": "🐘",
            "category": "Animals",
            "hint": "A very large animal with a trunk.",
        },
        {
            "word": "Butterfly",
            "emoji": "🦋",
            "category": "Animals",
            "hint": "An insect with colourful wings.",
        },
        {
            "word": "Computer",
            "emoji": "💻",
            "category": "Technology",
            "hint": "A device used for work and learning.",
        },
        {
            "word": "Education",
            "emoji": "📚",
            "category": "Everyday Words",
            "hint": "The process of learning.",
        },
        {
            "word": "Wonderful",
            "emoji": "🌟",
            "category": "Everyday Words",
            "hint": "Something extremely good.",
        },
        {
            "word": "Watermelon",
            "emoji": "🍉",
            "category": "Fruits",
            "hint": "A large fruit with a green outside.",
        },
        {
            "word": "Giraffe",
            "emoji": "🦒",
            "category": "Animals",
            "hint": "An animal with a very long neck.",
        },
        {
            "word": "Adventure",
            "emoji": "🧭",
            "category": "Everyday Words",
            "hint": "An exciting or unusual experience.",
        },
    ]

    context = {
        "pronunciation_words": pronunciation_words,
    }

    return render(
        request,
        "play_learn/pronunciation_lab.html",
        context,
    )

def cartoon_adventure(request):
    story = {
        "title": "The Lost Star Crystal",
        "subtitle": "Help Kiko save the magical forest!",
        "character": "Kiko",
        "character_emoji": "🦊",
        "start_scene": "forest_gate",
        "scenes": [
            {
                "id": "forest_gate",
                "character": "Kiko",
                "emoji": "🦊",
                "location": "🌳 The Enchanted Forest",
                "text": (
                    "Hello, brave explorer! I'm Kiko. The magical Star Crystal "
                    "has disappeared, and the forest is losing its light. "
                    "Will you help me find it?"
                ),
                "choices": [
                    {
                        "label": "Let's find the crystal!",
                        "next_scene": "forest_path",
                        "points": 5,
                    },
                    {
                        "label": "Ask the wise owl for help",
                        "next_scene": "wise_owl",
                        "points": 10,
                    },
                ],
            },
            {
                "id": "forest_path",
                "character": "Kiko",
                "emoji": "🦊",
                "location": "🌿 The Forest Path",
                "text": (
                    "We have reached a fork in the road. A wooden sign says "
                    "the crystal is hidden beyond the river. Which path should we take?"
                ),
                "choices": [
                    {
                        "label": "Follow the river",
                        "next_scene": "river_bridge",
                        "points": 10,
                    },
                    {
                        "label": "Walk deeper into the forest",
                        "next_scene": "forest_trap",
                        "points": 5,
                    },
                ],
            },
            {
                "id": "wise_owl",
                "character": "Ollie the Wise Owl",
                "emoji": "🦉",
                "location": "🌲 The Old Oak Tree",
                "text": (
                    "Ollie says: Before I help you, answer this question. "
                    "How many legs does a spider have?"
                ),
                "question": "How many legs does a spider have?",
                "answers": ["Six", "Eight", "Ten"],
                "correct_answer": "Eight",
                "correct_scene": "river_bridge",
                "wrong_scene": "forest_path",
            },
            {
                "id": "forest_trap",
                "character": "Kiko",
                "emoji": "🦊",
                "location": "🍃 The Hidden Forest",
                "text": (
                    "Oh no! We walked into a patch of magical vines. "
                    "We need to think carefully and find another way."
                ),
                "choices": [
                    {
                        "label": "Go back and follow the river",
                        "next_scene": "river_bridge",
                        "points": 5,
                    },
                    {
                        "label": "Ask Ollie the owl for help",
                        "next_scene": "wise_owl",
                        "points": 10,
                    },
                ],
            },
            {
                "id": "river_bridge",
                "character": "Kiko",
                "emoji": "🦊",
                "location": "🌊 The Crystal River",
                "text": (
                    "We found the river! A little wooden bridge crosses it. "
                    "But first, solve this challenge to unlock the bridge."
                ),
                "question": "What is 5 + 3?",
                "answers": ["6", "8", "9"],
                "correct_answer": "8",
                "correct_scene": "crystal_cave",
                "wrong_scene": "river_bridge",
            },
            {
                "id": "crystal_cave",
                "character": "Kiko",
                "emoji": "🦊",
                "location": "💎 The Crystal Cave",
                "text": (
                    "Amazing! We crossed the river and found the cave. "
                    "The Star Crystal is right here, but it is protected by "
                    "one final challenge."
                ),
                "question": "Which planet is known as the Red Planet?",
                "answers": ["Earth", "Mars", "Jupiter"],
                "correct_answer": "Mars",
                "correct_scene": "victory",
                "wrong_scene": "crystal_cave",
            },
            {
                "id": "victory",
                "character": "Kiko",
                "emoji": "🦊",
                "location": "🌟 The Magical Forest",
                "ending": True,
                "text": (
                    "WE DID IT! The Star Crystal is back! The forest is shining "
                    "again. You were brave, clever and helpful. Thank you, explorer!"
                ),
            },
        ],
    }

    return render(
        request,
        "play_learn/cartoon_adventure.html",
        {"story": story},
    )


def _get_legacy_cartoon_story_data():
    """
    Shared data source for the built-in Cartoon Stories collection.
    Used by both the cartoon reader and the main story library.
    """

    stories = [
        {
            "id": "lion_and_mouse",
            "title": "The Lion and the Little Mouse",
            "category": "Friendship",
            "emoji": "🦁",
            "cover": "🦁🐭",
            "description": "Discover how a tiny mouse helps a mighty lion.",
            "age": "3–8",
            "duration": "5 min",
            "lesson": "Kindness and helping others",
            "scenes": [
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "Once upon a time, in a beautiful green forest, lived a mighty lion. He was strong, proud and loved sleeping under the big trees."
                },
                {
                    "character": "Little Mouse",
                    "emoji": "🐭",
                    "text": "One sunny afternoon, a little mouse ran across the sleeping lion's nose. The lion suddenly woke up!"
                },
                {
                    "character": "Lion",
                    "emoji": "🦁",
                    "text": "ROAR! Who disturbed my sleep? You tiny mouse! Why should I not eat you?"
                },
                {
                    "character": "Little Mouse",
                    "emoji": "🐭",
                    "text": "Please let me go, mighty lion. One day, I may be able to help you!"
                },
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "The lion laughed, but he decided to let the little mouse go. A few days later, the lion got trapped in a hunter's net."
                },
                {
                    "character": "Lion",
                    "emoji": "🦁",
                    "text": "HELP! Somebody please help me! I cannot escape this net!"
                },
                {
                    "character": "Little Mouse",
                    "emoji": "🐭",
                    "text": "Don't worry, my friend! I will help you. I have sharp little teeth!"
                },
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "The mouse quickly chewed through the ropes. The lion was free! He thanked the little mouse, and they became the best of friends."
                },
            ],
            "question": "What lesson does this story teach us?",
            "answers": [
                "Kindness matters",
                "Only strong people can help",
                "Never make friends"
            ],
            "correct_answer": "Kindness matters",
        },
        {
            "id": "honest_boy",
            "title": "The Honest Little Boy",
            "category": "Honesty",
            "emoji": "👦",
            "cover": "👦💰",
            "description": "A young boy discovers why telling the truth matters.",
            "age": "4–10",
            "duration": "4 min",
            "lesson": "Always tell the truth",
            "scenes": [
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "There once lived a boy named Daniel. He loved playing football with his friends after school."
                },
                {
                    "character": "Daniel",
                    "emoji": "👦",
                    "text": "Oh no! I accidentally broke my mother's flower vase while playing indoors!"
                },
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "Daniel became afraid. He wondered whether he should hide the broken vase or tell his mother the truth."
                },
                {
                    "character": "Daniel",
                    "emoji": "👦",
                    "text": "Mummy, I am sorry. I broke your vase by mistake. I should not have played football inside."
                },
                {
                    "character": "Mother",
                    "emoji": "👩",
                    "text": "Thank you for telling me the truth, Daniel. I am not happy about the broken vase, but I am proud of your honesty."
                },
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "Daniel learned that telling the truth takes courage. From that day, he always tried to be honest."
                },
            ],
            "question": "What should Daniel do when he makes a mistake?",
            "answers": [
                "Tell the truth",
                "Blame somebody else",
                "Hide what happened"
            ],
            "correct_answer": "Tell the truth",
        },
        {
            "id": "sharing_is_caring",
            "title": "Sharing Is Caring",
            "category": "Friendship",
            "emoji": "🧒",
            "cover": "🍎👧",
            "description": "Two friends discover the happiness that comes from sharing.",
            "age": "3–8",
            "duration": "4 min",
            "lesson": "Sharing and generosity",
            "scenes": [
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "Mia and Ben were classmates. One day, Mia brought a delicious lunch to school."
                },
                {
                    "character": "Ben",
                    "emoji": "👦",
                    "text": "Mia, your apple looks delicious! I forgot my lunch today."
                },
                {
                    "character": "Mia",
                    "emoji": "👧",
                    "text": "You can have half of my apple, Ben. Friends should look after one another!"
                },
                {
                    "character": "Ben",
                    "emoji": "👦",
                    "text": "Thank you, Mia! That is very kind of you. I will remember your kindness."
                },
                {
                    "character": "Narrator",
                    "emoji": "📖",
                    "text": "They shared their lunch, played together and enjoyed the rest of their day. They discovered that sharing can make everyone happy."
                },
            ],
            "question": "What did Mia teach Ben?",
            "answers": [
                "Sharing makes people happy",
                "Food should never be shared",
                "Friends should not help each other"
            ],
            "correct_answer": "Sharing makes people happy",
        },
    ]

    return stories

def get_cartoon_story_data():
    """
    Retrieve published cartoon stories from the database
    and convert them into JSON-friendly dictionaries
    for the cartoon stories frontend.
    """

    cartoon_stories = (
        CartoonStory.objects
        .filter(status="published")
        .prefetch_related(
            "scenes",
            "questions__answers",
        )
        .order_by("-is_featured", "order", "-created_at")
    )

    stories = []

    for story in cartoon_stories:

        # Cover image
        cover_url = ""

        if story.cover:
            try:
                cover_url = story.cover.url
            except (ValueError, AttributeError):
                cover_url = ""

        # Published scenes
        scenes = []

        for scene in story.scenes.all().order_by(
            "scene_number", "id"
        ):
            if not scene.is_published:
                continue

            illustration_url = ""
            audio_url = ""

            if scene.illustration:
                try:
                    illustration_url = scene.illustration.url
                except (ValueError, AttributeError):
                    pass

            if scene.audio_file:
                try:
                    audio_url = scene.audio_file.url
                except (ValueError, AttributeError):
                    pass

            scenes.append({
                "character": scene.character_name,
                "emoji": scene.character_emoji,
                "title": scene.title,
                "text": scene.text,
                "narration": scene.narration,
                "illustration_url": illustration_url,
                "audio_url": audio_url,
            })

        # Published questions and their answers
        questions = []

        for question in story.questions.all().order_by(
            "question_number", "id"
        ):
            if not question.is_published:
                continue

            answers = list(
                question.answers.all()
                .order_by("order", "id")
            )

            questions.append({
                "question": question.question_text,
                "answers": [
                    answer.answer_text for answer in answers
                ],
                "correct_answer": next(
                    (
                        answer.answer_text
                        for answer in answers
                        if answer.is_correct
                    ),
                    "",
                ),
                "explanation": question.explanation,
            })

        stories.append({
            "id": story.slug,
            "title": story.title,
            "category": story.category,
            "emoji": story.emoji,
            "cover": story.cover_emoji or story.emoji or "📖",
            "cover_url": cover_url,
            "description": story.description,
            "age": f"{story.min_age}-{story.max_age} years",
            "duration": story.estimated_duration_minutes,
            "lesson": story.lesson,
            "scenes": scenes,
            "questions": questions,
        })

    return stories

def cartoon_stories(request):
    """
    Display the database-driven Cartoon Stories collection.
    Supports opening a selected story using the existing ?story= parameter.
    """

    stories = get_cartoon_story_data()

    selected_story = request.GET.get("story", "").strip()

    return render(
        request,
        "play_learn/cartoon_stories.html",
        {
            "stories": stories,
            "selected_story": selected_story,
        },
    )

def memory_match(request):
    age_groups = [
        {"name": "Little Explorers", "min_age": 3, "max_age": 5},
        {"name": "Young Learners", "min_age": 6, "max_age": 8},
        {"name": "Junior Explorers", "min_age": 9, "max_age": 12},
        {"name": "Teen Innovators", "min_age": 13, "max_age": 17},
        {"name": "Adult Zone", "min_age": 18, "max_age": 100},
    ]

    return render(
        request,
        "play_learn/memory_match.html",
        {"age_groups": age_groups},
    )

def bubble_pop(request):
    return render(request, "play_learn/bubble_pop.html")

def whack_a_mole(request):
    return render(request, "play_learn/whack_a_mole.html")

def number_ninja(request):
    return render(request, "play_learn/number_ninja.html")

def color_rush(request):
    return render(request, "play_learn/color_rush.html")

def simon_says(request):
    return render(request, "play_learn/simon_says.html")

def treasure_hunt(request):
    return render(request, "play_learn/treasure_hunt.html")

def maze_runner(request):
    return render(request, "play_learn/maze_runner.html")

def chess_master(request):
    return render(request, "play_learn/chess_master.html")

def sudoku_challenge(request):
    return render(request, "play_learn/sudoku_challenge.html")

def detective_case_files(request):
    return render(request, "play_learn/detective_case_files.html")

def tower_defense(request):
    return render(request, "play_learn/tower_defense.html")

def word_master(request):
    return render(request, "play_learn/word_master.html")

def business_tycoon(request):
    return render(request, "play_learn/business_tycoon.html")

def stock_market_simulator(request):
    return render(request, "play_learn/stock_market_simulator.html")

def story_library(request):
    """
    Display published adult stories and published cartoon stories.
    Adult novels and children's cartoon stories remain separate systems.
    """

    stories = Story.objects.filter(
        status=Story.Status.PUBLISHED
    ).order_by("-is_featured", "-created_at")

    cartoon_stories = get_cartoon_story_data()

    genre = request.GET.get("genre")
    audience = request.GET.get("audience")
    search_query = request.GET.get("q", "").strip()

    if genre:
        stories = stories.filter(genre=genre)

    if audience:
        stories = stories.filter(audience=audience)

    if search_query:
        stories = stories.filter(
            title__icontains=search_query
        )

        search_term = search_query.lower()

        cartoon_stories = [
            story for story in cartoon_stories
            if (
                search_term in story["title"].lower()
                or search_term in story["description"].lower()
                or search_term in story["category"].lower()
                or search_term in story.get("lesson", "").lower()
            )
        ]

    context = {
        "stories": stories,
        "cartoon_stories": cartoon_stories,
        "genres": Story.Genre.choices,
        "audiences": Story.Audience.choices,
        "selected_genre": genre or "",
        "selected_audience": audience or "",
        "search_query": search_query,
        "cartoon_stories_url": "play_learn:cartoon_stories",
    }

    return render(
        request,
        "play_learn/story_library.html",
        context,
    )

def story_detail(request, slug):
    story = get_object_or_404(
        Story,
        slug=slug,
        status=Story.Status.PUBLISHED,
    )

    chapters = story.chapters.filter(
        is_published=True
    ).order_by("chapter_number")

    bookmark = None

    if request.user.is_authenticated:
        bookmark = StoryBookmark.objects.filter(
            user=request.user,
            story=story,
        ).first()

    return render(
        request,
        "play_learn/story_detail.html",
        {
            "story": story,
            "chapters": chapters,
            "bookmark": bookmark,
        },
    )

def read_story_chapter(request, slug, chapter_number):
    story = get_object_or_404(
        Story,
        slug=slug,
        status=Story.Status.PUBLISHED,
    )

    chapter = get_object_or_404(
        StoryChapter,
        story=story,
        chapter_number=chapter_number,
        is_published=True,
    )

    chapters = list(
        story.chapters.filter(
            is_published=True
        ).order_by("chapter_number")
    )

    current_index = chapters.index(chapter)

    previous_chapter = (
        chapters[current_index - 1]
        if current_index > 0
        else None
    )

    next_chapter = (
        chapters[current_index + 1]
        if current_index < len(chapters) - 1
        else None
    )

    if request.user.is_authenticated:
        StoryBookmark.objects.update_or_create(
            user=request.user,
            story=story,
            defaults={
                "chapter": chapter,
                "last_position": 0,
            },
        )

    return render(
        request,
        "play_learn/read_story_chapter.html",
        {
            "story": story,
            "chapter": chapter,
            "previous_chapter": previous_chapter,
            "next_chapter": next_chapter,
            "chapter_count": len(chapters),
        },
    )

@login_required
@require_POST
def toggle_story_bookmark(request, slug):
    story = get_object_or_404(
        Story,
        slug=slug,
        status=Story.Status.PUBLISHED,
    )

    bookmark = StoryBookmark.objects.filter(
        user=request.user,
        story=story,
    ).first()

    if bookmark:
        bookmark.delete()
        messages.success(request, "Story removed from your library.")
    else:
        StoryBookmark.objects.create(
            user=request.user,
            story=story,
        )
        messages.success(request, "Story added to your library.")

    return redirect(
        "play_learn:story_detail",
        slug=story.slug,
    )


@login_required
def my_story_library(request):
    """
    Display stories bookmarked by the currently logged-in reader.
    """

    bookmarks = (
        StoryBookmark.objects
        .filter(
            user=request.user,
            story__status=Story.Status.PUBLISHED,
        )
        .select_related("story", "chapter")
        .order_by("-updated_at")
    )

    return render(
        request,
        "play_learn/my_story_library.html",
        {
            "bookmarks": bookmarks,
        },
    )

@require_POST
@csrf_protect
def start_game_attempt(request):
    """
    Create a new Memory Match attempt for an authenticated
    player or guest.
    """

    game = get_object_or_404(
        PlayGame,
        slug="memory-match",
        is_published=True,
    )

    attempt = GameAttempt.objects.create(
        user=request.user if request.user.is_authenticated else None,
        game=game,
        status=GameAttempt.Status.STARTED,
    )

    return JsonResponse({
        "success": True,
        "attempt_id": attempt.id,
    })


@require_POST
@csrf_protect
def finish_game_attempt(request, attempt_id):
    """
    Save a completed or abandoned Memory Match attempt.
    Scores are calculated and validated server-side.
    """

    try:
        data = json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"success": False, "error": "Invalid request data."},
            status=400,
        )

    attempt = get_object_or_404(
        GameAttempt,
        id=attempt_id,
        game__slug="memory-match",
    )

    # Prevent one authenticated user from modifying another
    # authenticated user's attempt.
    if attempt.user_id:
        if not request.user.is_authenticated or attempt.user_id != request.user.id:
            return JsonResponse(
                {"success": False, "error": "Permission denied."},
                status=403,
            )

    if attempt.status != GameAttempt.Status.STARTED:
        return JsonResponse(
            {"success": False, "error": "This attempt has already ended."},
            status=400,
        )

    level = data.get("level")
    matches = data.get("matches")
    attempts = data.get("attempts")
    requested_status = data.get("status", "completed")

    if level not in {"easy", "medium", "hard"}:
        return JsonResponse(
            {"success": False, "error": "Invalid difficulty level."},
            status=400,
        )

    try:
        matches = int(matches)
        attempts = int(attempts)
    except (TypeError, ValueError):
        return JsonResponse(
            {"success": False, "error": "Invalid game statistics."},
            status=400,
        )

    pair_limits = {
        "easy": 6,
        "medium": 8,
        "hard": 10,
    }

    total_pairs = pair_limits[level]

    if matches < 0 or matches > total_pairs:
        return JsonResponse(
            {"success": False, "error": "Invalid match count."},
            status=400,
        )

    if attempts < matches:
        return JsonResponse(
            {"success": False, "error": "Invalid attempt count."},
            status=400,
        )

    if requested_status not in {"completed", "abandoned"}:
        return JsonResponse(
            {"success": False, "error": "Invalid completion status."},
            status=400,
        )

    if requested_status == "completed" and matches != total_pairs:
        return JsonResponse(
            {"success": False, "error": "The game is not yet completed."},
            status=400,
        )

    now = timezone.now()

    duration = max(
        0,
        int((now - attempt.started_at).total_seconds()),
    )

    # Memory Match awards 20 points per matched pair and
    # up to 60 bonus points based on completion time.
    max_score = (total_pairs * 20) + 60

    if requested_status == "completed":
        time_bonus = max(0, 60 - duration)
        final_score = (matches * 20) + time_bonus
        status = GameAttempt.Status.COMPLETED
        completed_at = now
    else:
        final_score = matches * 20
        status = GameAttempt.Status.ABANDONED
        completed_at = None

    attempt.score = final_score
    attempt.max_score = max_score
    attempt.duration_seconds = duration
    attempt.status = status
    attempt.completed_at = completed_at
    attempt.extra_data = {
        "level": level,
        "matches": matches,
        "attempts": attempts,
        "total_pairs": total_pairs,
        "time_bonus": max(
            0,
            60 - duration,
        ) if requested_status == "completed" else 0,
    }

    attempt.save()

    return JsonResponse({
        "success": True,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "percentage": attempt.percentage,
        "duration_seconds": attempt.duration_seconds,
        "status": attempt.status,
    })
