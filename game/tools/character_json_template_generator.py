import json


def generate_words(argument, number):
    return [f"{argument}_word_{i}" for i in range(1, number + 1)]


def generate_questions(argument, number):
    return [f"{argument}_question_{i}" for i in range(1, number + 1)]


def generate_narrative_choices(
    interest_name, num_narrative_choices, num_words_per_choice
):
    narrative_choices = []
    for i in range(1, num_narrative_choices + 1):
        narrative_choice = {
            "name": f"{interest_name}_narrative_choice_{i}",
            "night_number": i,
            "words": generate_words(
                f"{interest_name}_narrative_choice_{i}", num_words_per_choice
            ),
        }
        narrative_choices.append(narrative_choice)
    return narrative_choices


def generate_vampire_character():
    character = {
        "name": "Vampire",
        "quality_1_choices": ["Mysterious", "Charming", "Ancient"],
        "quality_2_choices": ["Nocturnal", "Elegant", "Powerful"],
        "quality_3_choices": ["Immortal", "Solitary", "Mystical"],
        "interest_1_choices": ["Gothic Literature", "Classical Music", "History"],
        "interest_2_choices": ["Mystery", "Romance", "Exploration"],
        "interest_3_choices": ["Supernatural", "Occult", "Art"],
        "activity_1_choices": ["Night Stalking", "Castle Dwelling"],
        "activity_2_choices": ["Socializing", "Animal Transformation"],
    }
    qualities = [
        {"name": "Mysterious", "words": generate_words("Mysterious", 15)},
        {"name": "Charming", "words": generate_words("Charming", 15)},
        {"name": "Ancient", "words": generate_words("Ancient", 15)},
        {"name": "Nocturnal", "words": generate_words("Nocturnal", 15)},
        {"name": "Elegant", "words": generate_words("Elegant", 15)},
        {"name": "Powerful", "words": generate_words("Powerful", 15)},
        {"name": "Immortal", "words": generate_words("Immortal", 15)},
        {"name": "Solitary", "words": generate_words("Solitary", 15)},
        {"name": "Mystical", "words": generate_words("Mystical", 15)},
    ]

    activities = [
        {
            "name": "Night Stalking",
            "questions": generate_questions("Night_Stalking", 3),
        },
        {
            "name": "Castle Dwelling",
            "questions": generate_questions("Castle_Dwelling", 3),
        },
        {"name": "Socializing", "questions": generate_questions("Socializing", 3)},
        {
            "name": "Animal Transformation",
            "questions": generate_questions("Animal_Transformation", 3),
        },
    ]

    interests = [
        {
            "name": "Gothic Literature",
            "narrative_choices": generate_narrative_choices(
                "Gothic_Literature", 25, 10
            ),
        },
        {
            "name": "Classical Music",
            "narrative_choices": generate_narrative_choices("Classical_Music", 25, 10),
        },
        {
            "name": "History",
            "narrative_choices": generate_narrative_choices("History", 25, 10),
        },
        {
            "name": "Mystery",
            "narrative_choices": generate_narrative_choices("Mystery", 25, 10),
        },
        {
            "name": "Romance",
            "narrative_choices": generate_narrative_choices("Romance", 25, 10),
        },
        {
            "name": "Exploration",
            "narrative_choices": generate_narrative_choices("Exploration", 25, 10),
        },
        {
            "name": "Supernatural",
            "narrative_choices": generate_narrative_choices("Supernatural", 25, 10),
        },
        {
            "name": "Occult",
            "narrative_choices": generate_narrative_choices("Occult", 25, 10),
        },
        {
            "name": "Art",
            "narrative_choices": generate_narrative_choices("Art", 25, 10),
        },
    ]

    vampire_character = {
        "character": character,
        "qualities": qualities,
        "activities": activities,
        "interests": interests,
    }

    return vampire_character


def main():
    vampire_data = generate_vampire_character()
    with open("vampire_character.json", "w") as file:
        json.dump(vampire_data, file, indent=4)


if __name__ == "__main__":
    main()
