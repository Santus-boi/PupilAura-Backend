
from django.urls import path
from . import community_views
from . import story_views
from . import views
from . import ai_views


app_name = "admin_dashboard"


urlpatterns = [

    # =========================================================
    # ADMIN DASHBOARD
    # =========================================================

    path("", views.dashboard, name="dashboard"),

    # =========================================================
    # STUDENTS
    # =========================================================

    path("students/", views.students, name="students"),
    path(
        "students/<int:student_id>/",
        views.student_detail,
        name="student_detail",
    ),

    # =========================================================
    # CURRICULUM
    # =========================================================

    path("curriculum/", views.curriculum, name="curriculum"),

    # EDUCATION LEVELS
    path("curriculum/levels/", views.education_levels, name="education_levels"),
    path("curriculum/levels/create/", views.education_level_create, name="education_level_create"),
    path("curriculum/levels/<int:level_id>/", views.education_level_detail, name="education_level_detail"),
    path("curriculum/levels/<int:level_id>/edit/", views.education_level_edit, name="education_level_edit"),
    path("curriculum/levels/<int:level_id>/delete/", views.education_level_delete, name="education_level_delete"),

    # SCHOOL CLASSES
    path("curriculum/classes/", views.school_classes, name="school_classes"),
    path("curriculum/classes/create/", views.school_class_create, name="school_class_create"),
    path("curriculum/classes/<int:class_id>/", views.school_class_detail, name="school_class_detail"),
    path("curriculum/classes/<int:class_id>/edit/", views.school_class_edit, name="school_class_edit"),
    path("curriculum/classes/<int:class_id>/delete/", views.school_class_delete, name="school_class_delete"),

    # SUBJECTS
    path("curriculum/subjects/", views.subjects, name="subjects"),
    path("curriculum/subjects/create/", views.subject_create, name="subject_create"),
    path("curriculum/subjects/<int:subject_id>/", views.subject_detail, name="subject_detail"),
    path("curriculum/subjects/<int:subject_id>/edit/", views.subject_edit, name="subject_edit"),
    path("curriculum/subjects/<int:subject_id>/delete/", views.subject_delete, name="subject_delete"),

    # TERMS
    path("curriculum/terms/", views.terms, name="terms"),
    path("curriculum/terms/create/", views.term_create, name="term_create"),
    path("curriculum/terms/<int:term_id>/", views.term_detail, name="term_detail"),
    path("curriculum/terms/<int:term_id>/edit/", views.term_edit, name="term_edit"),
    path("curriculum/terms/<int:term_id>/delete/", views.term_delete, name="term_delete"),

    # WEEKS
    path("curriculum/weeks/", views.weeks, name="weeks"),
    path("curriculum/weeks/create/", views.week_create, name="week_create"),
    path("curriculum/weeks/<int:week_id>/", views.week_detail, name="week_detail"),
    path("curriculum/weeks/<int:week_id>/edit/", views.week_edit, name="week_edit"),
    path("curriculum/weeks/<int:week_id>/delete/", views.week_delete, name="week_delete"),

    # LESSONS
    path("curriculum/lessons/", views.lessons, name="lessons"),
    path("curriculum/lessons/create/", views.lesson_create, name="lesson_create"),
    path("curriculum/lessons/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("curriculum/lessons/<int:lesson_id>/edit/", views.lesson_edit, name="lesson_edit"),
    path("curriculum/lessons/<int:lesson_id>/delete/", views.lesson_delete, name="lesson_delete"),

    # LESSON CONTENT
    path("curriculum/lessons/<int:lesson_id>/content/", views.lesson_content, name="lesson_content"),

    # LESSON VIDEOS
    path("curriculum/lessons/<int:lesson_id>/videos/add/", views.lesson_video_add, name="lesson_video_add"),
    path("curriculum/videos/<int:video_id>/edit/", views.lesson_video_edit, name="lesson_video_edit"),
    path("curriculum/videos/<int:video_id>/delete/", views.lesson_video_delete, name="lesson_video_delete"),

    # LESSON IMAGES / DIAGRAMS
    path("curriculum/lessons/<int:lesson_id>/images/add/", views.lesson_image_add, name="lesson_image_add"),
    path("curriculum/images/<int:image_id>/edit/", views.lesson_image_edit, name="lesson_image_edit"),
    path("curriculum/images/<int:image_id>/delete/", views.lesson_image_delete, name="lesson_image_delete"),

    # LESSON RESOURCES
    path("curriculum/lessons/<int:lesson_id>/resources/add/", views.lesson_resource_add, name="lesson_resource_add"),
    path("curriculum/resources/<int:resource_id>/edit/", views.lesson_resource_edit, name="lesson_resource_edit"),
    path("curriculum/resources/<int:resource_id>/delete/", views.lesson_resource_delete, name="lesson_resource_delete"),

    # CURRICULUM STUDY MATERIALS
    path(
        "curriculum/materials/<str:level>/<int:object_id>/",
        views.curriculum_material_manage,
        name="curriculum_material_manage",
    ),
    path(
        "curriculum/materials/<str:level>/<int:object_id>/delete/",
        views.curriculum_material_delete,
        name="curriculum_material_delete",
    ),

    # INDEPENDENT COURSES
    path("curriculum/courses/", views.courses, name="courses"),
    path("curriculum/courses/create/", views.course_create, name="course_create"),
    path("curriculum/courses/<int:course_id>/", views.course_detail, name="course_detail"),
    path("curriculum/courses/<int:course_id>/edit/", views.course_edit, name="course_edit"),
    path("curriculum/courses/<int:course_id>/delete/", views.course_delete, name="course_delete"),

    # =========================================================
    # TECH CATEGORIES
    # =========================================================

    path("tech/categories/", views.tech_categories, name="tech_categories"),
    path("tech/categories/create/", views.tech_category_create, name="tech_category_create"),
    path("tech/categories/<int:category_id>/", views.tech_category_detail, name="tech_category_detail"),
    path("tech/categories/<int:category_id>/edit/", views.tech_category_edit, name="tech_category_edit"),
    path("tech/categories/<int:category_id>/delete/", views.tech_category_delete, name="tech_category_delete"),

    # TECH COURSES
    path("tech/courses/", views.tech_courses, name="tech_courses"),
    path("tech/courses/create/", views.tech_course_create, name="tech_course_create"),
    path("tech/courses/<int:course_id>/", views.tech_course_detail, name="tech_course_detail"),
    path("tech/courses/<int:course_id>/edit/", views.tech_course_edit, name="tech_course_edit"),
    path("tech/courses/<int:course_id>/delete/", views.tech_course_delete, name="tech_course_delete"),

    # TECH MODULES
    path("tech/modules/", views.tech_modules, name="tech_modules"),
    path("tech/modules/create/", views.tech_module_create, name="tech_module_create"),
    path("tech/modules/<int:module_id>/", views.tech_module_detail, name="tech_module_detail"),
    path("tech/modules/<int:module_id>/edit/", views.tech_module_edit, name="tech_module_edit"),
    path("tech/modules/<int:module_id>/delete/", views.tech_module_delete, name="tech_module_delete"),

    # TECH LESSONS
    path("tech/lessons/", views.tech_lessons, name="tech_lessons"),
    path("tech/lessons/create/", views.tech_lesson_create, name="tech_lesson_create"),
    path("tech/lessons/<int:lesson_id>/", views.tech_lesson_detail, name="tech_lesson_detail"),
    path("tech/lessons/<int:lesson_id>/edit/", views.tech_lesson_edit, name="tech_lesson_edit"),
    path("tech/lessons/<int:lesson_id>/delete/", views.tech_lesson_delete, name="tech_lesson_delete"),

    # TECH LESSON VIDEO
    path("tech/lessons/<int:lesson_id>/videos/create/", views.tech_lesson_video_create, name="tech_lesson_video_create"),
    path("tech/lesson-videos/<int:video_id>/edit/", views.tech_lesson_video_edit, name="tech_lesson_video_edit"),
    path("tech/lesson-videos/<int:video_id>/delete/", views.tech_lesson_video_delete, name="tech_lesson_video_delete"),

    # TECH LESSON IMAGES
    path("tech/lesson-images/<int:lesson_id>/images/create/", views.tech_lesson_image_create, name="tech_lesson_image_create"),
    path("tech/lesson-images/<int:images_id>/edit/", views.tech_lesson_image_edit, name="tech_lesson_image_edit"),
    path("tech/lesson-images/<int:images_id>/delete/", views.tech_lesson_image_delete, name="tech_lesson_image_delete"),

    # TECH LESSON RESOURCES
    path("tech/lessons/<int:lesson_id>/resources/create/", views.tech_lesson_resource_create, name="tech_lesson_resource_create"),
    path("tech/resources/<int:resource_id>/edit/", views.tech_lesson_resource_edit, name="tech_lesson_resource_edit"),
    path("tech/resources/<int:resource_id>/delete/", views.tech_lesson_resource_delete, name="tech_lesson_resource_delete"),

    # =========================================================
    # EXAM PREPARATION
    # =========================================================

    path("exams/", views.exams, name="exams"),
    path("exams/create/", views.exam_create, name="exam_create"),
    path("exams/<int:exam_id>/", views.exam_detail, name="exam_detail"),
    path("exams/<int:exam_id>/edit/", views.exam_edit, name="exam_edit"),
    path("exams/<int:exam_id>/delete/", views.exam_delete, name="exam_delete"),

    # EXAM SUBJECTS
    path("exams/<int:exam_id>/subjects/", views.exam_subjects, name="exam_subjects"),
    path("exams/<int:exam_id>/subjects/create/", views.exam_subject_create, name="exam_subject_create"),
    path("exam-subjects/<int:subject_id>/", views.exam_subject_detail, name="exam_subject_detail"),
    path("exam-subjects/<int:subject_id>/edit/", views.exam_subject_edit, name="exam_subject_edit"),
    path("exam-subjects/<int:subject_id>/delete/", views.exam_subject_delete, name="exam_subject_delete"),

    # EXAM YEARS
    path("exams/<int:exam_id>/years/", views.exam_years, name="exam_years"),
    path("exams/<int:exam_id>/years/create/", views.exam_year_create, name="exam_year_create"),
    path("exam-years/<int:year_id>/", views.exam_year_detail, name="exam_year_detail"),
    path("exam-years/<int:year_id>/edit/", views.exam_year_edit, name="exam_year_edit"),
    path("exam-years/<int:year_id>/delete/", views.exam_year_delete, name="exam_year_delete"),

    # EXAM RESOURCES
    path("exams/<int:exam_id>/resources/", views.exam_resources, name="exam_resources"),
    path("exams/<int:exam_id>/resources/create/", views.exam_resource_create, name="exam_resource_create"),
    path("exam-resources/<int:resource_id>/", views.exam_resource_detail, name="exam_resource_detail"),
    path("exam-resources/<int:resource_id>/edit/", views.exam_resource_edit, name="exam_resource_edit"),
    path("exam-resources/<int:resource_id>/delete/", views.exam_resource_delete, name="exam_resource_delete"),

    # =========================================================
    # EXAM QUESTIONS
    # =========================================================

    path("exam-resources/<int:resource_id>/questions/", views.exam_questions, name="exam_questions"),
    path("exam-resources/<int:resource_id>/questions/create/", views.exam_question_create, name="exam_question_create"),
    path(
    "exam-resources/<int:resource_id>/questions/bulk-create/",
    views.exam_question_bulk_create,
    name="exam_question_bulk_create",),
    
    path("exam-questions/<int:question_id>/", views.exam_question_detail, name="exam_question_detail"),
    path("exam-questions/<int:question_id>/edit/", views.exam_question_edit, name="exam_question_edit"),
    path("exam-questions/<int:question_id>/delete/", views.exam_question_delete, name="exam_question_delete"),

    path("exam-questions/<int:question_id>/choices/", views.exam_choices, name="exam_choices"),
    path("exam-questions/<int:question_id>/choices/create/", views.exam_choice_create, name="exam_choice_create"),
    path("exam-choices/<int:choice_id>/edit/", views.exam_choice_edit, name="exam_choice_edit"),
    path("exam-choices/<int:choice_id>/delete/", views.exam_choice_delete, name="exam_choice_delete"),

    # =========================================================
    # PLAY & LEARN — GAMES
    # =========================================================

    path("play-learn/games/", views.play_games, name="play_games"),
    path("play-learn/games/create/", views.play_game_create, name="play_game_create"),
    path("play-learn/games/<int:game_id>/", views.play_game_detail, name="play_game_detail"),
    path("play-learn/games/<int:game_id>/edit/", views.play_game_edit, name="play_game_edit"),
    path("play-learn/games/<int:game_id>/delete/", views.play_game_delete, name="play_game_delete"),

    # =========================================================
    # PLAY & LEARN — STORY LIBRARY
    # =========================================================

    path("play-learn/stories/", story_views.stories, name="stories"),
    path("play-learn/stories/create/", story_views.story_create, name="story_create"),
    path("play-learn/stories/<int:story_id>/", story_views.story_detail, name="story_detail"),
    path("play-learn/stories/<int:story_id>/edit/", story_views.story_edit, name="story_edit"),
    path("play-learn/stories/<int:story_id>/delete/", story_views.story_delete, name="story_delete"),

    # STORY LIBRARY CHAPTERS
    path("play-learn/stories/<int:story_id>/chapters/create/", story_views.story_chapter_create, name="story_chapter_create"),
    path("play-learn/chapters/<int:chapter_id>/edit/", story_views.story_chapter_edit, name="story_chapter_edit"),
    path("play-learn/chapters/<int:chapter_id>/delete/", story_views.story_chapter_delete, name="story_chapter_delete"),

    # STORY LIBRARY PUBLISHING
    path("play-learn/stories/<int:story_id>/publish/", story_views.story_publish_toggle, name="story_publish_toggle"),

    # =========================================================
    # PLAY & LEARN — INTERACTIVE CARTOON STORIES
    # =========================================================

    path("play-learn/cartoon-stories/", story_views.cartoon_stories, name="cartoon_stories"),
    path("play-learn/cartoon-stories/create/", story_views.cartoon_story_create, name="cartoon_story_create"),
    path("play-learn/cartoon-stories/<int:story_id>/", story_views.cartoon_story_detail, name="cartoon_story_detail"),
    path("play-learn/cartoon-stories/<int:story_id>/edit/", story_views.cartoon_story_edit, name="cartoon_story_edit"),
    path("play-learn/cartoon-stories/<int:story_id>/delete/", story_views.cartoon_story_delete, name="cartoon_story_delete"),

    # CARTOON STORY SCENES
    path("play-learn/cartoon-stories/<int:story_id>/scenes/create/", story_views.cartoon_scene_create, name="cartoon_scene_create"),
    path("play-learn/cartoon-scenes/<int:scene_id>/edit/", story_views.cartoon_scene_edit, name="cartoon_scene_edit"),
    path("play-learn/cartoon-scenes/<int:scene_id>/delete/", story_views.cartoon_scene_delete, name="cartoon_scene_delete"),

    # CARTOON STORY QUESTIONS AND ANSWERS
    path("play-learn/cartoon-stories/<int:story_id>/questions/create/", story_views.cartoon_question_create, name="cartoon_question_create"),
    path("play-learn/cartoon-questions/<int:question_id>/edit/", story_views.cartoon_question_edit, name="cartoon_question_edit"),
    path("play-learn/cartoon-questions/<int:question_id>/delete/", story_views.cartoon_question_delete, name="cartoon_question_delete"),

    # CARTOON STORY PUBLISHING
    path("play-learn/cartoon-stories/<int:story_id>/publish/", story_views.cartoon_story_publish_toggle, name="cartoon_story_publish_toggle"),

    # =========================================================
    # PRICING
    # =========================================================

    path("pricing/", views.pricing_overview, name="pricing_overview"),

    # =========================================================
    # ASSESSMENTS
    # =========================================================

    path("assessments/attempts/", views.assessment_attempts, name="assessment_attempts"),
    path("assessments/attempts/<int:attempt_id>/", views.attempt_detail, name="attempt_detail"),
    path("assessments/pending/", views.pending_reviews, name="pending_reviews"),
    path("assessments/review/<int:attempt_id>/", views.review_attempt, name="review_attempt"),

    # =========================================================
    # RESOURCE GENERATOR
    # =========================================================

    path("resources/generator/", views.resource_generator, name="resource_generator"),

    # =========================================================
    # AI STUDIO
    # =========================================================

    path("ai/", ai_views.ai_index, name="ai_index"),

    # AI SELECTION PAGES
    path("ai/select/lesson-week/", ai_views.ai_lesson_week_picker, name="ai_lesson_week_picker"),
    path("ai/select/exam/", ai_views.ai_exam_picker, name="ai_exam_picker"),
    path("ai/select/exam-resource/", ai_views.ai_exam_resource_picker, name="ai_exam_resource_picker"),
    path("ai/select/tech-course/", ai_views.ai_tech_course_picker, name="ai_tech_course_picker"),
    path("ai/select/tech-module/", ai_views.ai_tech_module_picker, name="ai_tech_module_picker"),

    # AI EXAM GENERATORS
    path("ai/exam-questions/<int:resource_id>/", ai_views.ai_exam_question_generator, name="ai_exam_question_generator"),
    path("ai/exam-resource/<int:exam_id>/", ai_views.ai_exam_resource_generator, name="ai_exam_resource_generator"),

    # AI TECH GENERATORS
    path("ai/tech-course/", ai_views.ai_tech_course_generator, name="ai_tech_course_generator"),
    path("ai/tech-module/<int:course_id>/", ai_views.ai_tech_module_generator, name="ai_tech_module_generator"),
    path("ai/tech-lesson/<int:module_id>/", ai_views.ai_tech_lesson_generator, name="ai_tech_lesson_generator"),

    # AI LESSON / QUIZ GENERATORS
    path("ai/lesson-generator/", ai_views.ai_lesson_generator, name="ai_lesson_generator"),
    path("ai/quiz-generator/<int:lesson_id>/", ai_views.ai_quiz_generator, name="ai_quiz_generator"),
    path("ai/quiz-generator/", ai_views.ai_quiz_picker, name="ai_quiz_generator_from_lesson"),

    # AI STORY GENERATOR
    path("ai/stories/", story_views.ai_story_generator, name="ai_story_generator"),

    # COMMUNITY MANAGEMENT
path(
    "community/",
    community_views.community,
    name="community",
),
path(
    "community/groups/<int:group_id>/",
    community_views.community_group_detail,
    name="community_group_detail",
),
path(
    "community/groups/<int:group_id>/<str:action>/",
    community_views.community_group_action,
    name="community_group_action",
),
path(
    "community/groups/<int:group_id>/members/<int:membership_id>/<str:action>/",
    community_views.community_membership_action,
    name="community_membership_action",
),
path(
    "community/groups/<int:group_id>/caretakers/<int:membership_id>/<str:action>/",
    community_views.community_caretaker_action,
    name="community_caretaker_action",
),

]
