from game.models import (
    Quality,
    Word,
    Activity,
    Interest,
    NarrativeChoice,
    Character,
    Question,
)


def ingest_json_data(json_data):
    # Iterate through the qualities, activities, interests, and character data
    for quality_data in json_data["qualities"]:
        quality, created = Quality.objects.get_or_create(name=quality_data["name"])
        for word in quality_data["words"]:
            word_obj, created = Word.objects.get_or_create(word=word)
            quality.words.add(word_obj)

    for activity_data in json_data["activities"]:
        activity, created = Activity.objects.get_or_create(name=activity_data["name"])
        for question in activity_data["questions"]:
            question_obj, created = Question.objects.get_or_create(text=question)
            activity.questions.add(question_obj)

    for interest_data in json_data["interests"]:
        interest, created = Interest.objects.get_or_create(name=interest_data["name"])
        for narrative_choice_data in interest_data["narrative_choices"]:
            narrative_choice, created = NarrativeChoice.objects.get_or_create(
                name=narrative_choice_data["name"],
                interest=interest,
                night_number=narrative_choice_data["night_number"],
            )
            for word in narrative_choice_data["words"]:
                word_obj, created = Word.objects.get_or_create(word=word)
                narrative_choice.words.add(word_obj)

    character_data = json_data["character"]
    character, created = Character.objects.get_or_create(name=character_data["name"])
    # Attach qualities, interests, and activities to the character
    # For example:
    for quality_name in character_data["quality_1_choices"]:
        quality = Quality.objects.get(name=quality_name)
        character.quality_1_choices.add(quality)
    for quality_name in character_data["quality_2_choices"]:
        quality = Quality.objects.get(name=quality_name)
        character.quality_2_choices.add(quality)
    for quality_name in character_data["quality_3_choices"]:
        quality = Quality.objects.get(name=quality_name)
        character.quality_3_choices.add(quality)
    for interest_name in character_data["interest_1_choices"]:
        interest = Interest.objects.get(name=interest_name)
        character.interest_1_choices.add(interest)
    for interest_name in character_data["interest_2_choices"]:
        interest = Interest.objects.get(name=interest_name)
        character.interest_2_choices.add(interest)
    for interest_name in character_data["interest_3_choices"]:
        interest = Interest.objects.get(name=interest_name)
        character.interest_3_choices.add(interest)
    for activity_name in character_data["activity_1_choices"]:
        activity = Activity.objects.get(name=activity_name)
        character.activity_1_choices.add(activity)
    for activity_name in character_data["activity_2_choices"]:
        activity = Activity.objects.get(name=activity_name)
        character.activity_2_choices.add(activity)
