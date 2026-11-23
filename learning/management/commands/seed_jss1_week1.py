from django.core.management.base import BaseCommand
from learning.models import (
    EducationLevel,
    SchoolClass,
    Subject,
    Term,
    Week,
    Lesson,
)


class Command(BaseCommand):
    help = "Create or update JSS 1 Computer Studies First Term Week 1 lessons."

    def handle(self, *args, **options):
        # ---------------------------------------------------------
        # EDUCATION LEVEL
        # ---------------------------------------------------------
        education_level, _ = EducationLevel.objects.get_or_create(
            name="Junior Secondary",
            defaults={
                "level_type": EducationLevel.LevelType.JUNIOR_SECONDARY,
                "order": 3,
            },
        )

        # ---------------------------------------------------------
        # SCHOOL CLASS
        # ---------------------------------------------------------
        school_class, _ = SchoolClass.objects.get_or_create(
            name="JSS 1",
            education_level=education_level,
            defaults={
                "order": 1,
            },
        )

        # ---------------------------------------------------------
        # SUBJECT
        # ---------------------------------------------------------
        subject, _ = Subject.objects.get_or_create(
            name="Computer Studies",
            school_class=school_class,
        )

        # ---------------------------------------------------------
        # FIRST TERM
        # ---------------------------------------------------------
        term, _ = Term.objects.get_or_create(
            term_type=Term.TermType.FIRST,
            subject=subject,
            defaults={
                "name": "First Term",
                "order": 1,
            },
        )

        # Make sure the name is correct even if the term existed.
        if term.name != "First Term":
            term.name = "First Term"
            term.order = 1
            term.save(update_fields=["name", "order"])

        # ---------------------------------------------------------
        # WEEK 1
        # ---------------------------------------------------------
        week, _ = Week.objects.get_or_create(
            term=term,
            number=1,
            defaults={
                "title": "Introduction to Computers",
                "overview": (
                    "This week introduces students to the idea of "
                    "computers and the historical need for devices "
                    "that help people count, calculate, store "
                    "information and solve problems."
                ),
                "activities": (
                    "Class discussion, identification of everyday "
                    "computing devices, historical comparison of "
                    "counting tools and a simple practical activity "
                    "using an imaginary counting board."
                ),
            },
        )

        # Keep the week information up to date.
        week.title = "Introduction to Computers"
        week.overview = (
            "This week introduces students to the idea of computers "
            "and the historical need for devices that help people "
            "count, calculate, store information and solve problems."
        )
        week.activities = (
            "Class discussion, identification of everyday computing "
            "devices, historical comparison of counting tools and a "
            "simple practical activity using an imaginary counting board."
        )
        week.save(
            update_fields=[
                "title",
                "overview",
                "activities",
            ]
        )

        # ---------------------------------------------------------
        # LESSON 1
        # ---------------------------------------------------------
        lesson_1_content = """
A computer is an electronic device that accepts data, processes
the data according to instructions, stores information and produces
useful results.

The word computer is connected with the idea of computing or
calculating. However, modern computers can do much more than
perform arithmetic. They can be used to create documents, communicate,
watch videos, listen to music, search for information, design graphics,
write programs and control machines.

A computer works by following instructions. The instructions tell
the computer what to do with the data it receives.

Data refers to raw facts and figures that have not yet been processed.
Examples of data include a student's name, age, examination scores,
numbers and dates.

Information is meaningful data that has been processed and organized
so that it can be understood and used.

For example, if a teacher enters the scores of students into a
computer, the individual scores are data. When the computer calculates
the total score and average score, the resulting figures become useful
information.

The basic activities performed by a computer can be summarized as:

1. Input
2. Processing
3. Storage
4. Output

Input is the process of entering data into a computer.

Processing is the work the computer performs on the data.

Storage is the keeping of data and information for future use.

Output is the result produced after processing.

Examples of input devices include the keyboard, mouse, scanner and
microphone.

Examples of output devices include the monitor, printer and speakers.

Examples of storage devices include hard drives, solid-state drives,
memory cards and flash drives.

Computers are used in schools, hospitals, banks, offices, shops,
factories, homes, transportation systems and many other places.
"""

        lesson_1_examples = """
Example 1:
A student types 25 into a calculator. The number 25 is input.
The calculator performs a calculation and displays the answer as output.

Example 2:
A teacher enters students' examination scores into a computer.
The computer can calculate totals, averages and other useful results.

Example 3:
A student uses a laptop to type an assignment, save it and print it.
The keyboard provides input, the computer processes the typing,
the storage device keeps the document and the printer produces output.
"""

        lesson_1_key_points = """
• A computer is an electronic device that processes data.
• Data consists of raw facts and figures.
• Information is processed data that has meaning.
• Computers operate by following instructions.
• The four basic activities are input, processing, storage and output.
• Computers are used in many areas of everyday life.
"""

        lesson_1_activity = """
1. Name five places where computers are used.
2. Mention three examples of data.
3. Mention three examples of information.
4. Identify two input devices and two output devices.
5. Explain the difference between data and information.
"""

        lesson_1_practical = """
Look around your classroom or home and identify five devices that
contain or use computer technology.

For each device, write:
• The name of the device.
• What it is used for.
• What kind of information it handles.

Students should discuss their answers with the class.
"""

        lesson_2_content = """
Before modern computers existed, people needed ways to count and
perform calculations.

Early human activities such as trading, farming, building and keeping
records required people to count objects and quantities.

At first, people could count using their fingers. Fingers were useful
for small quantities, but they were not enough for large numbers.

People also used physical objects such as stones, sticks, shells and
seeds to represent quantities.

For example, a person could place one stone beside each animal owned.
The number of stones would represent the number of animals.

As societies became larger and activities became more complex,
people needed better ways to perform calculations and keep records.

Counting systems and simple counting tools were developed to reduce
the difficulty of performing calculations manually.

The development of counting devices was important because manual
calculation could be slow and errors could occur, especially when
dealing with large quantities.

Different civilizations developed different methods and tools for
counting.

These early methods eventually contributed to the development of more
advanced calculating machines and, much later, electronic computers.

The history of computing therefore did not begin with modern laptops
and desktop computers. It developed gradually as people searched for
better ways to count, calculate, store information and solve problems.
"""

        lesson_2_examples = """
Example 1:
A farmer counting 20 bags of grain may use marks, stones or another
physical method to keep track of the quantity.

Example 2:
A trader selling many items needs a reliable way to keep track of
the number of items sold and the amount of money received.

Example 3:
A builder measuring materials for a large project needs accurate
counting and calculation to avoid mistakes.
"""

        lesson_2_key_points = """
• People needed counting methods long before electronic computers.
• Fingers were one of the earliest natural counting tools.
• Physical objects could be used to represent quantities.
• Larger quantities made manual counting more difficult.
• The need for faster and more accurate calculations encouraged the
  development of counting devices.
• Modern computers developed from a long history of counting and
  calculation tools.
"""

        lesson_2_activity = """
1. Why did early people need to count?
2. Mention four objects that could be used for simple counting.
3. Why are fingers not always suitable for counting very large
   quantities?
4. Give two occupations in which accurate counting is important.
5. Explain why people developed counting devices.
"""

        lesson_2_practical = """
Create a simple counting system using small objects such as bottle
caps, stones or pieces of paper.

Choose a quantity between 1 and 20 and represent that quantity using
your objects.

Then explain to the class how your counting system works and why
physical objects can be useful for representing numbers.
"""

        lesson_3_content = """
As people developed more organized societies, simple counting with
fingers and objects became less convenient.

One important development was the use of counting boards.

A counting board is a surface on which counters or markers can be
placed and moved to represent numbers and perform calculations.

The counters could represent different quantities depending on their
position.

Counting boards were useful because they allowed people to organize
numbers physically rather than depending entirely on memory.

Another early calculating device was the tally system. A tally is a
mark used to record a quantity. Groups of marks can be used to keep
track of objects or events.

People also used counting rods and other physical objects for
calculation.

These devices did not work like modern electronic computers. They
were mainly physical tools that helped people represent numbers and
perform calculations.

The important idea is that computing developed gradually. Each
improvement addressed some of the limitations of earlier methods.

As calculation became more complicated, people developed more
specialized tools. These developments eventually contributed to
mechanical calculators and later electronic computers.
"""

        lesson_3_examples = """
Example 1:
A person keeping track of ten items could make ten tally marks.

Example 2:
A counting board could use counters placed in different positions
to represent different quantities.

Example 3:
Counting rods could be arranged and manipulated to help with
mathematical calculations.
"""

        lesson_3_key_points = """
• A counting board is a physical surface used to help represent
  numbers and perform calculations.
• Tally marks can be used to record quantities.
• Counting rods were physical tools used for calculation.
• Early counting tools were not electronic computers.
• The development of counting tools was gradual.
• Each new tool helped solve limitations of earlier counting methods.
"""

        lesson_3_activity = """
1. What is a counting board?
2. What is a tally?
3. Mention two early counting tools.
4. Explain one advantage of using a counting board.
5. How were early counting tools different from modern computers?
"""

        lesson_3_practical = """
Draw a simple counting board in your notebook.

Divide the board into sections and use dots or small circles as
counters.

Represent the numbers 3, 7 and 12 using your counters.

Explain how changing the position or number of counters changes
the quantity being represented.
"""

        lesson_4_content = """
The abacus is one of the best-known traditional calculating devices.

An abacus consists of a frame containing rods or wires with beads
that can be moved from one position to another.

The beads are arranged according to a place-value system. Depending
on the design of the abacus, different rods can represent units,
tens, hundreds and larger values.

By moving the beads according to established rules, a user can
represent numbers and perform arithmetic operations.

The abacus is important in the history of computing because it
provided a structured way of representing numbers and carrying out
calculations.

Unlike a modern electronic calculator, the abacus does not use
electricity or electronic circuits. The user performs the calculation
by physically moving the beads.

The abacus has been used in different parts of the world for many
years and different versions have existed.

Learning about the abacus helps students understand that calculating
devices existed long before electronic computers.

The abacus also demonstrates an important computing idea: information
can be represented physically using positions and symbols.
"""

        lesson_4_examples = """
Example 1:
On an abacus, different rods can represent different place values,
such as units, tens and hundreds.

Example 2:
A user can move beads to represent a number before performing an
addition or subtraction operation.

Example 3:
Two students can use an abacus to practice representing the same
number and checking a calculation.
"""

        lesson_4_key_points = """
• An abacus is a traditional calculating device.
• It uses movable beads on rods or wires.
• It does not require electricity.
• Bead positions can represent different place values.
• The user performs calculations by manipulating the beads.
• The abacus is an important part of the history of computing.
"""

        lesson_4_activity = """
1. What is an abacus?
2. Does an abacus require electricity?
3. What are the beads used for?
4. Why is the abacus important in computing history?
5. State one difference between an abacus and an electronic calculator.
"""

        lesson_4_practical = """
If a real abacus is available, examine its frame, rods and beads.

Identify:
• The frame.
• The rods or wires.
• The movable beads.
• The different place-value positions.

If an abacus is not available, draw a simple abacus in your notebook
and label its main parts.
"""

        lesson_5_content = """
The history of computing developed through many stages.

People first used natural methods such as fingers and physical objects
for counting. Later, they developed organized counting methods and
devices such as tally systems, counting boards and the abacus.

Mechanical calculating machines were later developed to perform
calculations with less manual effort.

One important example was the development of mechanical calculators
that used gears and other moving parts.

As mathematical and scientific problems became more demanding,
inventors and scientists continued to develop machines that could
perform calculations more efficiently.

The development of electronic technology eventually changed computing
dramatically.

Electronic computers could process information much faster than
manual and mechanical devices. They could also store and process
large amounts of information.

Modern computers are the result of many developments over a long
period of time. They did not appear suddenly as the devices we use
today.

The history can therefore be viewed as a progression:

Natural counting methods
→ Counting tools
→ Mechanical calculating devices
→ Electronic computers
→ Modern digital computing devices

This development was driven by the need for greater speed, accuracy,
storage and flexibility.
"""

        lesson_5_examples = """
Example 1:
The movement from simple tally marks to organized counting tools
shows how people developed better ways to represent quantities.

Example 2:
The abacus improved organized calculation compared with simply
counting individual objects.

Example 3:
Electronic computers later made it possible to perform calculations,
store information and run many different types of programs.
"""

        lesson_5_key_points = """
• Computing developed gradually over a long period.
• Early counting methods came before mechanical calculators.
• Mechanical devices introduced machines with moving parts for
  calculation.
• Electronic computers greatly increased processing capability.
• Modern computers are the result of many earlier developments.
• The development of computing was driven by human needs and problems.
"""

        lesson_5_activity = """
1. Arrange these stages in the correct historical order:
   electronic computers, natural counting, counting tools,
   mechanical calculators.

2. Why did people develop better calculating devices?
3. Mention two limitations of simple manual counting.
4. How did electronic computers change computing?
5. Explain why modern computers did not appear suddenly.
"""

        lesson_5_practical = """
Create a simple timeline in your notebook showing the development
of computing.

Include at least these stages:

1. Natural counting
2. Counting tools
3. Abacus
4. Mechanical calculating devices
5. Electronic computers
6. Modern computers

Under each stage, write one sentence describing its importance.
"""

        lesson_6_content = """
Early counting tools and modern computers were both developed to help
people work with numbers and information, but they operate in very
different ways.

Early tools such as tally marks, counting boards and the abacus
depended heavily on the person using them.

The user had to manipulate marks, counters or beads and perform the
calculation according to established rules.

Modern computers, on the other hand, use electronic components and
software instructions to process data.

A modern computer can perform calculations at very high speed,
store large amounts of information and perform many different tasks.

Early counting tools were generally designed for specific counting
or calculation activities. Modern computers are general-purpose
machines that can perform many different tasks depending on the
software being used.

Another major difference is storage. An abacus can represent a
number while it is being used, but it does not provide digital
storage like a computer.

Modern computers can store documents, photographs, videos, programs
and other types of digital information.

Despite these differences, early counting tools are important because
they show the gradual development of ideas used in computing.

The history of computing teaches us that modern technology developed
from many earlier inventions and ideas.
"""

        lesson_6_examples = """
Example 1:
An abacus can help a person perform arithmetic by moving beads.
A computer can perform arithmetic using electronic circuits and
software instructions.

Example 2:
A counting board requires the user to manipulate counters.
A computer can process data automatically after receiving instructions.

Example 3:
A modern computer can store documents and videos digitally.
A simple counting tool cannot provide this type of digital storage.
"""

        lesson_6_key_points = """
• Early counting tools were mainly physical devices.
• Modern computers use electronic components and software.
• Early tools depended heavily on the person operating them.
• Modern computers can process information very quickly.
• Modern computers provide digital storage.
• Modern computers can perform many different tasks.
• Early counting tools are important in understanding computing history.
"""

        lesson_6_activity = """
Complete the comparison below.

1. State one similarity between an abacus and a computer.
2. State two differences between an abacus and a computer.
3. Which one uses electronic components?
4. Which one depends on physical movement of beads?
5. Why should students study early counting tools?
"""

        lesson_6_practical = """
Create a two-column comparison table in your notebook.

Column 1:
Early Counting Tools

Column 2:
Modern Computers

Compare them using:
• Method of operation
• Speed
• Storage
• Human involvement
• Type of technology
• Number of tasks they can perform

Discuss your table with a classmate.
"""

        lessons = [
            {
                "order": 1,
                "title": "Introduction to Computers",
                "description": (
                    "An introduction to computers, data, information, "
                    "input, processing, storage and output."
                ),
                "objectives": """
By the end of this lesson, students should be able to:

1. Define a computer.
2. Explain the meaning of data and information.
3. Describe the basic activities performed by a computer.
4. Identify examples of input, output and storage devices.
5. Mention areas where computers are used.
""",
                "content": lesson_1_content,
                "examples": lesson_1_examples,
                "key_points": lesson_1_key_points,
                "activity": lesson_1_activity,
                "practical": lesson_1_practical,
            },
            {
                "order": 2,
                "title": "Counting and the Need for Computing Devices",
                "description": (
                    "Students learn why people needed counting methods "
                    "and how this need contributed to the development "
                    "of computing devices."
                ),
                "objectives": """
By the end of this lesson, students should be able to:

1. Explain why early people needed to count.
2. Identify simple early methods of counting.
3. Explain some limitations of manual counting.
4. Describe why people developed counting devices.
5. Connect the need for calculation with the development of computing.
""",
                "content": lesson_2_content,
                "examples": lesson_2_examples,
                "key_points": lesson_2_key_points,
                "activity": lesson_2_activity,
                "practical": lesson_2_practical,
            },
            {
                "order": 3,
                "title": "Counting Boards and Early Computing Tools",
                "description": (
                    "An introduction to counting boards, tally marks, "
                    "counting rods and other early tools used to represent "
                    "numbers and perform calculations."
                ),
                "objectives": """
By the end of this lesson, students should be able to:

1. Explain what a counting board is.
2. Explain the use of tally marks.
3. Identify counting rods as an early calculating tool.
4. Describe how physical counters can represent quantities.
5. Explain why early counting tools were important in computing history.
""",
                "content": lesson_3_content,
                "examples": lesson_3_examples,
                "key_points": lesson_3_key_points,
                "activity": lesson_3_activity,
                "practical": lesson_3_practical,
            },
            {
                "order": 4,
                "title": "The Abacus",
                "description": (
                    "Students learn about the structure, operation and "
                    "importance of the abacus as an early calculating device."
                ),
                "objectives": """
By the end of this lesson, students should be able to:

1. Define an abacus.
2. Identify the major parts of an abacus.
3. Explain how beads are used to represent numbers.
4. Explain how an abacus can be used for calculation.
5. State why the abacus is important in computing history.
""",
                "content": lesson_4_content,
                "examples": lesson_4_examples,
                "key_points": lesson_4_key_points,
                "activity": lesson_4_activity,
                "practical": lesson_4_practical,
            },
            {
                "order": 5,
                "title": "From the Abacus to the Modern Computer",
                "description": (
                    "Students examine the gradual development from "
                    "simple counting methods and the abacus to mechanical "
                    "and electronic computing devices."
                ),
                "objectives": """
By the end of this lesson, students should be able to:

1. Describe the gradual development of computing.
2. Arrange major stages in the history of computing.
3. Explain why mechanical calculating devices were developed.
4. Explain the importance of electronic computers.
5. Describe computing as a continuous process of technological development.
""",
                "content": lesson_5_content,
                "examples": lesson_5_examples,
                "key_points": lesson_5_key_points,
                "activity": lesson_5_activity,
                "practical": lesson_5_practical,
            },
            {
                "order": 6,
                "title": "Comparing Early Counting Tools with Modern Computers",
                "description": (
                    "Students compare early counting tools with modern "
                    "computers in terms of operation, speed, storage, "
                    "human involvement and flexibility."
                ),
                "objectives": """
By the end of this lesson, students should be able to:

1. Identify similarities between early counting tools and computers.
2. Explain differences between early counting tools and modern computers.
3. Compare their methods of operation.
4. Compare their storage capabilities.
5. Explain why early counting tools remain important in computing history.
""",
                "content": lesson_6_content,
                "examples": lesson_6_examples,
                "key_points": lesson_6_key_points,
                "activity": lesson_6_activity,
                "practical": lesson_6_practical,
            },
        ]

        # ---------------------------------------------------------
        # CREATE OR UPDATE LESSONS
        # ---------------------------------------------------------
        created_count = 0
        updated_count = 0

        for lesson_data in lessons:
            lesson, created = Lesson.objects.update_or_create(
                week=week,
                order=lesson_data["order"],
                defaults={
                    "title": lesson_data["title"],
                    "description": lesson_data["description"].strip(),
                    "objectives": lesson_data["objectives"].strip(),
                    "content": lesson_data["content"].strip(),
                    "examples": lesson_data["examples"].strip(),
                    "key_points": lesson_data["key_points"].strip(),
                    "activity": lesson_data["activity"].strip(),
                    "practical": lesson_data["practical"].strip(),
                    "published": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created: {lesson.title}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Updated: {lesson.title}"
                    )
                )

        # ---------------------------------------------------------
        # FINAL MESSAGE
        # ---------------------------------------------------------
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "JSS 1 Computer Studies Week 1 content is ready."
            )
        )
        self.stdout.write(
            f"Created: {created_count} lesson(s)"
        )
        self.stdout.write(
            f"Updated: {updated_count} lesson(s)"
        )
        self.stdout.write(
            f"Week: {week}"
        )
        self.stdout.write(
            f"Subject: {subject}"
        )
        self.stdout.write(
            f"Term: {term}"
        )