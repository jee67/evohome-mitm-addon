from dataclasses import dataclass

@dataclass
class RamsesFrame:
    verb: int
    src: str
    dst: str
    payload: bytearray
    header: list  # de niet-payload tokens, om terug te kunnen bouwen


def decode_ramses_line(line: bytes) -> RamsesFrame | None:
    """
    Verwacht iets in de trant van:
    RQ --- 01:033496 10:061315 --:------ 1F09 003 64 00
    """
    try:
        parts = line.decode(errors="ignore").strip().split()
        if len(parts) < 8:
            return None

        # indices volgens voorbeeldformat
        src = parts[2]
        dst = parts[3]
        verb = int(parts[5], 16)

        # payload bytes vanaf parts[7:]
        payload = bytearray(int(p, 16) for p in parts[7:])

        return RamsesFrame(
            verb=verb,
            src=src,
            dst=dst,
            payload=payload,
            header=parts[:7],  # tot en met length token
        )
    except Exception:
        return None


def encode_ramses_frame(frame: RamsesFrame) -> bytes:
    payload_str = " ".join(f"{b:02X}" for b in frame.payload)
    out = " ".join(frame.header) + (" " if payload_str else "") + payload_str + "\n"
    return out.encode()


def is_relevant_ch_setpoint(frame: RamsesFrame, controller_id: str, otb_id: str) -> bool:
    return frame.verb == 0x1F09 and frame.src == controller_id and frame.dst == otb_id


def get_ch_raw(frame: RamsesFrame) -> int:
    return frame.payload[0] if frame.payload else 0


def set_ch_raw(frame: RamsesFrame, value: int) -> RamsesFrame:
    if not frame.payload:
        frame.payload = bytearray([0])
    frame.payload[0] = max(0, min(255, int(value)))
    return frame
