
from play_learn.models import PlayGame

games = [
    ("Alphabet Adventure", "alphabet-adventure", "alphabet_adventure", "learn", 3, 5, "easy", 1),
    ("Math Challenge", "math-challenge", "math_challenge", "learn", 6, 8, "medium", 2),
    ("Word Builder", "word-builder", "word_builder", "learn", 6, 8, "easy", 3),
    ("Pronunciation Lab", "pronunciation-lab", "pronunciation_lab", "speaking", 6, 12, "easy", 4),
    ("Cartoon Adventure", "cartoon-adventure", "cartoon_adventure", "cartoon", 3, 8, "easy", 5),
    ("Memory Match", "memory-match", "memory_match", "arcade", 3, 100, "easy", 6),
    ("Bubble Pop", "bubble-pop", "bubble_pop", "arcade", 3, 12, "easy", 7),
    ("Whack-a-Mole", "whack-a-mole", "whack_a_mole", "arcade", 5, 12, "medium", 8),
    ("Number Ninja", "number-ninja", "number_ninja", "learn", 6, 12, "medium", 9),
    ("Color Rush", "color-rush", "color_rush", "arcade", 3, 8, "easy", 10),
    ("Simon Says", "simon-says", "simon_says", "arcade", 4, 12, "easy", 11),
    ("Treasure Hunt", "treasure-hunt", "treasure_hunt", "arcade", 6, 12, "medium", 12),
    ("Maze Runner", "maze-runner", "maze_runner", "arcade", 6, 12, "medium", 13),
    ("Chess Master", "chess-master", "chess_master", "arcade", 8, 100, "hard", 14),
    ("Sudoku Challenge", "sudoku-challenge", "sudoku_challenge", "learn", 9, 100, "medium", 15),
    ("Detective Case Files", "detective-case-files", "detective_case_files", "learn", 9, 17, "hard", 16),
    ("Tower Defense", "tower-defense", "tower_defense", "arcade", 9, 17, "hard", 17),
    ("Word Master", "word-master", "word_master", "learn", 9, 17, "medium", 18),
    ("Business Tycoon", "business-tycoon", "business_tycoon", "learn", 13, 100, "hard", 19),
    ("Stock Market Simulator", "stock-market-simulator", "stock_market_simulator", "learn", 13, 100, "hard", 20),
]

created_count = 0
existing_count = 0

for name, slug, url_name, category, min_age, max_age, difficulty, order in games:
    game, created = PlayGame.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name,
            "url_name": url_name,
            "description": f"{name} interactive game.",
            "category": category,
            "min_age": min_age,
            "max_age": max_age,
            "difficulty": difficulty,
            "order": order,
            "is_published": True,
        },
    )

    if created:
        created_count += 1
    else:
        existing_count += 1
        game.url_name = url_name
        game.save(update_fields=["url_name"])

    print(f"{'CREATED' if created else 'EXISTING'}: {game.name}")

print("\nRegistration completed.")
print("New records:", created_count)
print("Existing records reused:", existing_count)
print("Total games in database:", PlayGame.objects.count())
