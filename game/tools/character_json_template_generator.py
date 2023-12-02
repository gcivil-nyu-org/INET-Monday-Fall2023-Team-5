import json

CHARACTER_NAME = "Eldritch Mendoza"
QUALITIES = [
    "Decisive",
    "Intense",
    "Protective",
    "Intellectual",
    "Resourceful",
    "Clever Manipulator",
    "Familial",
    "Loyal",
    "Protective",
]

INTERESTS = [
    "Dance Clubs",
    "Concerts",
    "Community Building",
    "Business",
    "Fashion",
    "Social Justice",
    "Alien Lore",
    "Deep Conversations",
    "Good Cuisine",
]

ACTIVITIES = [
    "Watch the Skies",
    "Go Cafe Hopping",
    "Hack the Planet",
    "Work Out",
]
WORDS_PER_QUALITY = 15
QUESTIONS_PER_ACTIVITY = 3
NARRATIVE_CHOICES_PER_INTEREST = 25
WORDS_PER_NARRATIVE_CHOICE = 10


def generate_words(argument, number):
    argument = argument.lower().replace(" ", "_")
    return [f"{argument}_word_{i}" for i in range(1, number + 1)]


def generate_questions(argument, number):
    return [f"{argument}_question_{i}" for i in range(1, number + 1)]


def generate_narrative_choices(
    interest_name, num_narrative_choices, num_words_per_choice
):
    return [
        {
            "name": f"{interest_name}_narrative_choice_{i}",
            "night_number": i,
            "words": generate_words(
                f"{interest_name}_narrative_choice_{i}", num_words_per_choice
            ),
        }
        for i in range(1, num_narrative_choices + 1)
    ]


def generate_character():
    character = {
        "name": CHARACTER_NAME,
        "quality_1_choices": QUALITIES[:3],
        "quality_2_choices": QUALITIES[3:6],
        "quality_3_choices": QUALITIES[6:],
        "interest_1_choices": INTERESTS[:3],
        "interest_2_choices": INTERESTS[3:6],
        "interest_3_choices": INTERESTS[6:],
        "activity_1_choices": ACTIVITIES[:2],
        "activity_2_choices": ACTIVITIES[2:],
    }

    qualities = [
        {"name": quality, "words": generate_words(quality, WORDS_PER_QUALITY)}
        for quality in QUALITIES
    ]
    activities = [
        {
            "name": activity,
            "questions": generate_questions(activity, QUESTIONS_PER_ACTIVITY),
        }
        for activity in ACTIVITIES
    ]
    interests = [
        {
            "name": interest,
            "narrative_choices": generate_narrative_choices(
                interest, NARRATIVE_CHOICES_PER_INTEREST, WORDS_PER_NARRATIVE_CHOICE
            ),
        }
        for interest in INTERESTS
    ]

    return {
        "character": character,
        "qualities": qualities,
        "activities": activities,
        "interests": interests,
    }


def main():
    character_data = generate_character()
    with open("new_character.json", "w") as file:
        json.dump(character_data, file, indent=4)


if __name__ == "__main__":
    main()