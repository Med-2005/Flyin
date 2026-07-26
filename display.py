from rich import print
from webcolors import name_to_hex
from webcolors import names
from exceptions import InvalidConfErr


def print_turn(movements, zones):

    if not movements:
        return
    output = []

    custom_colors = {
        "rainbow": [
            "#ff0000",  # Red
            "#ff7f00",  # Orange
            "#ffff00",  # Yellow
            "#00ff00",  # Green
            "#0000ff",  # Blue
            "#4b0082",  # Indigo
            "#8f00ff",  # Violet
        ],
    }

    for drone_id, dest in movements:
        dest_name = dest.split("-")[-1] if "-" in dest else dest
        zone = zones.get(dest_name)

        if zone and zone.color:
            line = f"Line: {line_number}: " if zones.line_number else ""
            if zone.color not in custom_colors and zone.color not in names():
                raise InvalidConfErr(
                    f"{line}Invalid color: {zone.color}")
            color_str = zone.color.lower()

            if color_str == "rainbow":
                colors = custom_colors["rainbow"]
                rainbow_text = "".join(
                    f"[{colors[i % len(colors)]}]{char}[/]"
                    for i, char in enumerate(dest)
                )
                output.append(f"{drone_id}-{rainbow_text}")
                continue

            try:
                if color_str in custom_colors:
                    hex_color = custom_colors[color_str]
                else:
                    hex_color = name_to_hex(color_str)

                output.append(f"{drone_id}-[{hex_color}]{dest}[/]")

            except ValueError:
                output.append(f"{drone_id}-[{zone.color}]{dest}[/]")
        else:
            output.append(f"{drone_id}-{dest}")

    print(" ".join(output))