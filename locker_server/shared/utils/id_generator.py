import time


def timestamp_id_generator(user_id, device_user_id=1, sleep=lambda x: time.sleep(x/1000.0)):
    user_id_bits = 5
    device_user_id_bits = 5
    sequence_bits = 12

    user_id_shift = sequence_bits
    device_user_id_shift = sequence_bits + user_id_bits
    timestamp_left_shift = sequence_bits + user_id_bits + device_user_id_bits
    sequence_mask = -1 ^ (-1 << sequence_bits)

    last_timestamp = -1
    sequence = 0

    while True:
        timestamp = int(time.time() * 1000)
        if last_timestamp > timestamp:
            # log.warning("clock is moving backwards. waiting until %i" % last_timestamp)
            sleep(last_timestamp - timestamp)
            continue

        if last_timestamp == timestamp:
            sequence = (sequence + 1) & sequence_mask
            if sequence == 0:
                # log.warning("sequence overrun")
                sequence = -1 & sequence_mask
                sleep(1)
                continue
        else:
            sequence = 0

        last_timestamp = timestamp

        yield (
            (timestamp << timestamp_left_shift) |
            (device_user_id << device_user_id_shift) |
            (user_id << user_id_shift) |
            sequence
        )
