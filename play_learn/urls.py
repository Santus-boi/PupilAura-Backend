
from django.urls import path

from . import views


app_name = "play_learn"


urlpatterns = [
    path("", views.home, name="home"),

    path(
        "alphabet-adventure/",
        views.alphabet_adventure,
        name="alphabet_adventure",
    ),

    path(
        "math-challenge/",
        views.math_challenge,
        name="math_challenge",
    ),

    path(
    "word-builder/",
    views.word_builder,
    name="word_builder",
    ),

    path(
    "pronunciation-lab/",
    views.pronunciation_lab,
    name="pronunciation_lab",
    ),

    
path("cartoon-adventure/", views.cartoon_adventure, name="cartoon_adventure"),

path("cartoon-stories/", views.cartoon_stories, name="cartoon_stories"),


path("memory-match/", views.memory_match, name="memory_match"),

path("bubble-pop/", views.bubble_pop, name="bubble_pop"),


path("whack-a-mole/", views.whack_a_mole, name="whack_a_mole"),


path("number-ninja/", views.number_ninja, name="number_ninja"),

path("color-rush/", views.color_rush, name="color_rush"),

path("simon-says/", views.simon_says, name="simon_says"),

path("treasure-hunt/", views.treasure_hunt, name="treasure_hunt"),

path("maze-runner/", views.maze_runner, name="maze_runner"),


path("chess-master/", views.chess_master, name="chess_master"),


path("sudoku-challenge/", views.sudoku_challenge, name="sudoku_challenge"),


path("detective-case-files/", views.detective_case_files, name="detective_case_files"),

path("tower-defense/", views.tower_defense, name="tower_defense"),

path("word-master/", views.word_master, name="word_master"),

path("business-tycoon/", views.business_tycoon, name="business_tycoon"),

path(
    "stock-market-simulator/",
    views.stock_market_simulator,
    name="stock_market_simulator"
),


    # Stories & Novels
    path("stories/", views.story_library, name="story_library"),
    path(
        "stories/<slug:slug>/",
        views.story_detail,
        name="story_detail",
    ),
    path(
        "stories/<slug:slug>/chapter/<int:chapter_number>/",
        views.read_story_chapter,
        name="read_story_chapter",
    ),
    path(
        "stories/<slug:slug>/bookmark/",
        views.toggle_story_bookmark,
        name="toggle_story_bookmark",
    ),

    path(
    "my-library/",
    views.my_story_library,
    name="my_story_library",
    ),

    path(
    "attempt-start/",
    views.start_game_attempt,
    name="attempt_start",
),

path(
    "attempt-finish/<int:attempt_id>/",
    views.finish_game_attempt,
    name="attempt_finish",
),
]
