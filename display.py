from rich import print


def print_turn(movements, zones):
    if not movements:
        return

    output = []

    for drone_id, dest in movements:
        dest_name = dest.split("-")[-1] if "-" in dest else dest
        zone = zones.get(dest_name)

        if zone and zone.color:
            output.append(f"{drone_id}-[{zone.color}]{dest}[/]")
        else:
            output.append(f"{drone_id}-{dest}")

    print(" ".join(output))
