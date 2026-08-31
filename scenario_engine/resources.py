def parse_cpu(cpu_value: str) -> float:
    if cpu_value.endswith("m"):
        return float(cpu_value[:-1]) / 1000

    return float(cpu_value)


def parse_memory(memory_value: str) -> float:
    units = {
        "Ki": 1024,
        "Mi": 1024 ** 2,
        "Gi": 1024 ** 3,
        "Ti": 1024 ** 4,
    }

    for unit, multiplier in units.items():
        if memory_value.endswith(unit):
            value = float(
                memory_value[:-len(unit)]
            )
            return value * multiplier

    return float(memory_value)

