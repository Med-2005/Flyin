from rich import print
from webcolors import name_to_hex


def print_turn(movements, zones):
    if not movements:
        return

    output = []

    custom_colors = {
        "rainbow": "#ff00ff",
        "darkred": "#8b0000"
    }

    for drone_id, dest in movements:
        dest_name = dest.split("-")[-1] if "-" in dest else dest
        zone = zones.get(dest_name)

        if zone and zone.color:
            color_str = zone.color.lower()

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
