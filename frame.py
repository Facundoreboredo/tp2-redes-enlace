import struct

class Frame:
    # Constantes de tipos de trama
    TYPE_DATA = 0
    TYPE_ACK = 1

    # Formato de la cabecera fija:
    # ! -> Big-Endian (orden de red estándar)
    # B -> unsigned char (1 byte): Tipo de trama
    # B -> unsigned char (1 byte): Número de secuencia (0 o 1)
    # H -> unsigned short (2 bytes): Longitud de la carga útil
    # H -> unsigned short (2 bytes): Checksum de verificación
    HEADER_FORMAT = "!BBHH"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # Total: 6 bytes

    def __init__(self, frame_type: int, seq_num: int, payload: bytes = b"", checksum: int = 0):
        self.frame_type = frame_type
        self.seq_num = seq_num
        self.payload = payload
        self.checksum = checksum

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        Calcula el Checksum de Internet (suma en complemento a 1 de palabras de 16 bits).
        """
        # Si la longitud es impar, se agrega un byte de padding temporal
        if len(data) % 2 != 0:
            data += b"\x00"

        total_sum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            total_sum += word
            # Suma de acarreo circular (end-around carry de 16 bits)
            total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)

        # Complemento a 1
        return ~total_sum & 0xFFFF

    def serialize(self) -> bytes:
        """
        Empaqueta la cabecera y el payload en un flujo de bytes, 
        calculando e insertando el checksum correspondiente.
        """
        # 1. Empaquetar cabecera con checksum en 0 para calcular la verificación
        temp_header = struct.pack(self.HEADER_FORMAT, self.frame_type, self.seq_num, len(self.payload), 0)
        calculated_checksum = self.calculate_checksum(temp_header + self.payload)

        # 2. Empaquetar la cabecera real con el checksum calculado
        final_header = struct.pack(self.HEADER_FORMAT, self.frame_type, self.seq_num, len(self.payload), calculated_checksum)
        return final_header + self.payload

    @classmethod
    def deserialize(cls, raw_bytes: bytes):
        """
        Desempaqueta bytes crudos, extrae la cabecera y verifica la integridad por checksum.
        Retorna (instancia_Frame, es_valido: bool).
        """
        if len(raw_bytes) < cls.HEADER_SIZE:
            return None, False  # Trama incompleta o corrupta en longitud

        header_bytes = raw_bytes[:cls.HEADER_SIZE]
        payload = raw_bytes[cls.HEADER_SIZE:]

        frame_type, seq_num, declared_length, received_checksum = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Validar si el payload coincide con la longitud declarada
        if len(payload) != declared_length:
            return None, False

        # Recalcular el checksum con campo de checksum en 0
        verify_header = struct.pack(cls.HEADER_FORMAT, frame_type, seq_num, declared_length, 0)
        expected_checksum = cls.calculate_checksum(verify_header + payload)

        is_valid = (expected_checksum == received_checksum)
        frame = cls(frame_type, seq_num, payload, received_checksum)
        return frame, is_valid


if __name__ == "__main__":
    print("--- PRUEBAS UNITARIAS DE FRAME.PY ---")
    
    # 1. Prueba de serialización y deserialización correcta
    mensaje = b"Hola Mundo desde Capa de Red"
    trama = Frame(Frame.TYPE_DATA, seq_num=0, payload=mensaje)
    paquete_bytes = trama.serialize()
    
    trama_recibida, ok = Frame.deserialize(paquete_bytes)
    print(f"Recepcion correcta sin errores: {ok}")
    print(f"Tipo: {trama_recibida.frame_type} | Secuencia: {trama_recibida.seq_num} | Datos: {trama_recibida.payload.decode()}")

    # 2. Prueba de corrupción de datos (ruido de canal)
    paquete_alterado = bytearray(paquete_bytes)
    paquete_alterado[-1] ^= 0xFF  # Invierte los bits del último byte
    _, ok_corrupto = Frame.deserialize(bytes(paquete_alterado))
    print(f"Deteccion de error ante datos corruptos: {'DESCARTADA CORRECTAMENTE' if not ok_corrupto else 'ERROR: NO DETECTADO'}")
