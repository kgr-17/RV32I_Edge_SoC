"""Independent history-based expectations for the T025 diagnostic boundary."""
import random


def expected_samples(samples):
    if not samples or samples[0][0] != 1:
        raise ValueError('Replay must start with an asserted reset')
    last_reset = 0
    result = []
    for index, (reset, switches, rx) in enumerate(samples):
        if reset not in (0, 1) or rx not in (0, 1) or not 0 <= switches <= 65535:
            raise ValueError('Invalid board stimulus')
        if reset:
            last_reset = index
        age = index - last_reset
        # Closed-form sample history, independent of the RTL register updates:
        # release visible on second edge; data first visible on fourth edge.
        active = age >= 4
        led = samples[index - 1][1] if active else 0
        tx = samples[index - 1][2] if active else 1
        result.append((reset, switches, rx, led, tx, int(age < 2)))
    return result


def samples(seed):
    rng = random.Random(seed)
    stimulus = [(1, 65535, 0)] + [(0, 0x1234, 0)] * 8
    stimulus += [(0, 1 << bit, bit % 2) for bit in range(16)]
    stimulus += [(0, 65535 ^ (1 << bit), 1 - bit % 2) for bit in range(16)]
    for duration in (1, 2, 5):
        stimulus += [(1, 65535, 0)] * duration
        stimulus += [(0, 0xa55a, 0)] * 8
    stimulus += [(int(i % 29 in (0, 1)), rng.randrange(65536), rng.randrange(2)) for i in range(400)]
    stimulus += [(0, 0, 1)] * 8
    return stimulus


def vectors(seed):
    return ''.join('%x %04x %x %04x %x %x\n' % row for row in expected_samples(samples(seed)))
