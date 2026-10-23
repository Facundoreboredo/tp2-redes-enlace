import random
import time

class UnreliableChannel:
    def __init__(self, loss_prob: float = 0.2, corrupt_prob: float = 0.2, min_delay: float = 0.05, max_delay: float = 0.2):
        """
        loss_prob: Probabilidad de perder la trama (0.0 a 1.0)
        corrupt_prob: Probabilidad de alterar bits de la trama (0.0 a 1.0)
        min_delay / max_delay: Rango de retardo de propagación simulado en segundos
        """
        self.loss_prob = loss_prob
        self.corrupt_prob = corrupt_prob
        self.min_delay = min_delay
        self.max_delay = max_delay

    def transmit(self, raw_frame: bytes) -> bytes | None:
        """
        Simula el paso de la trama por el medio físico ruidoso.
        Retorna los bytes (posiblemente corruptos) o None si la trama se perdió.
        """
        # 1. Simular retardo de propagación en el medio
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

        # 2. Simular pérdida de trama
        if random.random() < self.loss_prob:
            print("[CANAL FÍSICO] -> Trama PERDIDA en el medio.")
            return None

        # 3. Simular corrupción de bits por ruido electromagnético
        if random.random() < self.corrupt_prob:
            print("[CANAL FÍSICO] -> Trama CORRUPTA por ruido.")
            frame_array = bytearray(raw_frame)
            
            # Selecciona un byte al azar e invierte bits con XOR
            pos = random.randint(0, len(frame_array) - 1)
            frame_array[pos] ^= random.randint(1, 255)
            return bytes(frame_array)

        # 4. Transmisión exitosa e intacta
        return raw_frame


if __name__ == "__main__":
    from frame import Frame

    print("--- PRUEBA DEL CANAL RUIDOSO ---")
    canal = UnreliableChannel(loss_prob=0.3, corrupt_prob=0.3, min_delay=0.01, max_delay=0.05)
    
    trama_ejemplo = Frame(Frame.TYPE_DATA, seq_num=1, payload=b"Dato de prueba")
    bytes_a_enviar = trama_ejemplo.serialize()

    # Probamos pasar 10 tramas por el canal para ver los distintos efectos
    for i in range(1, 11):
        print(f"\nEnvío #{i}:")
        resultado = canal.transmit(bytes_a_enviar)
        
        if resultado is None:
            print("  Resultado: La trama no llegó al receptor.")
        else:
            trama_recibida, valida = Frame.deserialize(resultado)
            if valida:
                print(f"  Resultado: Trama intacta recibida (seq={trama_recibida.seq_num}).")
            else:
                print("  Resultado: Trama recibida pero DESCARTADA por Checksum erróneo.")