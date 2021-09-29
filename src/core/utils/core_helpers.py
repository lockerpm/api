import random
import string


def secure_random_string(length: int, alpha: bool = True, upper: bool = True, lower: bool = True,
                         numeric: bool = True, special: bool = False):
    return secure_random_string_generator(
        length=length,
        characters=random_string_characters(alpha, upper, lower, numeric, special)
    )


def secure_random_string_generator(length: int, characters: str):
    if length < 0:
        raise Exception("Length cannot be less than zero")
    if not characters:
        raise Exception("Character is not valid")
    random_str = "".join([random.choice(characters) for _ in range(length)])
    return random_str


def random_string_characters(alpha: bool, upper: bool, lower: bool, numeric: bool, special: bool):
    characters = ""
    if alpha:
        if upper:
            characters += string.ascii_uppercase
        if lower:
            characters += string.ascii_lowercase
    if numeric:
        characters += string.digits
    if special:
        characters += "!@#$%^*&"
    return characters
