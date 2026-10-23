from frame import Frame
from channel import UnreliableChannel

class Receiver:
    def __init__(self, channel: UnreliableChannel):
        self.channel = channel
        self.expected_seq = 0
        self.received_data = []  # Simula la entrega de datos a la Capa de Red

    def process_incoming_frame(self, raw_frame_bytes: bytes) -> bytes | None:
        """
        Procesa una trama recibida desde el canal físico.
        Retorna los bytes del ACK a enviar de vuelta, o None si la trama se ignora/descarta.
        """
        # 1. Deserializar y validar integridad mediante Checksum
        frame, is_valid = Frame.deserialize(raw_frame_bytes)

        if not is_valid or frame is None:
            print("[RECEPTOR] -> Trama DESCARTADA por Checksum erróneo o formato corrupto.")
            return None

        # Solo procesamos tramas de tipo DATA en el receptor
        if frame.frame_type != Frame.TYPE_DATA:
            return None

        print(f"[RECEPTOR] -> Trama recibida intacta con seq={frame.seq_num}.")

        # 2. Verificar número de secuencia esperado
        if frame.seq_num == self.expected_seq:
            # Caso ideal: Trama en orden, entrega a Capa de Red
            print(f"[RECEPTOR] -> Trama ACEPTADA. Pasando payload a Capa de Red: '{frame.payload.decode(errors='replace')}'")
            self.received_data.append(frame.payload)
            
            # Generar ACK para la trama aceptada
            ack_frame = Frame(Frame.TYPE_ACK, seq_num=frame.seq_num)
            ack_bytes = ack_frame.serialize()

            # Alternar secuencia esperada (0 -> 1, 1 -> 0)
            self.expected_seq = 1 - self.expected_seq
            return ack_bytes

        else:
            # Caso duplicado: Se descarta el payload pero se reenvía el ACK
            print(f"[RECEPTOR] -> Trama DUPLICADA (esperaba seq={self.expected_seq}). Se descartan datos y se reenvía ACK={frame.seq_num}.")
            ack_frame = Frame(Frame.TYPE_ACK, seq_num=frame.seq_num)
            return ack_frame.serialize()