import time
from frame import Frame
from channel import UnreliableChannel
from receiver import Receiver

class Sender:
    def __init__(self, channel_to_receiver: UnreliableChannel, channel_to_sender: UnreliableChannel, receiver: Receiver, timeout: float = 0.5):
        self.channel_to_receiver = channel_to_receiver
        self.channel_to_sender = channel_to_sender
        self.receiver = receiver
        self.timeout = timeout
        self.current_seq = 0

        # Contadores estadísticos
        self.total_original_frames = 0
        self.total_retransmissions = 0
        self.total_transmitted_frames = 0

    def send_data(self, data_list: list[bytes]):
        """
        Envía una lista de paquetes de datos de la capa de red de manera secuencial y confiable.
        """
        self.total_original_frames = len(data_list)
        self.total_retransmissions = 0
        self.total_transmitted_frames = 0

        print(f"\n================ INICIO DE TRANSMISIÓN ({self.total_original_frames} paquetes) ================\n")

        for idx, payload in enumerate(data_list, start=1):
            print(f"\n>>> [CAPA DE RED -> ENLACE] Procesando paquete {idx}/{self.total_original_frames}: '{payload.decode(errors='replace')}'")
            
            ack_received = False
            attempts = 0

            while not ack_received:
                attempts += 1
                self.total_transmitted_frames += 1

                # Si es un intento posterior al primero, se cuenta como retransmisión
                if attempts > 1:
                    self.total_retransmissions += 1

                # 1. Crear y serializar la trama
                data_frame = Frame(Frame.TYPE_DATA, seq_num=self.current_seq, payload=payload)
                raw_frame_bytes = data_frame.serialize()

                tipo_envio = "Enviando trama DATA" if attempts == 1 else "[RETRANSMISIÓN] Reenviando trama DATA"
                print(f"[EMISOR] (Intento #{attempts}) -> {tipo_envio} con seq={self.current_seq}...")

                # 2. Transmitir por el canal físico hacia el receptor
                received_by_receiver = self.channel_to_receiver.transmit(raw_frame_bytes)

                start_time = time.time()

                if received_by_receiver is not None:
                    # 3. El receptor procesa la trama recibida
                    ack_bytes = self.receiver.process_incoming_frame(received_by_receiver)

                    if ack_bytes is not None:
                        # 4. El ACK viaja por el canal de regreso hacia el emisor
                        received_ack_by_sender = self.channel_to_sender.transmit(ack_bytes)

                        if received_ack_by_sender is not None:
                            # 5. Deserializar y validar integridad del ACK
                            ack_frame, ok = Frame.deserialize(received_ack_by_sender)

                            if ok and ack_frame.frame_type == Frame.TYPE_ACK:
                                if ack_frame.seq_num == self.current_seq:
                                    print(f"[EMISOR] -> ACK={ack_frame.seq_num} VÁLIDO recibido. Trama confirmada con éxito.")
                                    ack_received = True
                                    self.current_seq = 1 - self.current_seq
                                    continue
                                else:
                                    print(f"[EMISOR] -> ACK fuera de secuencia (esperaba {self.current_seq}, llegó {ack_frame.seq_num}).")
                            else:
                                print("[EMISOR] -> ACK CORRUPTO detectado por Checksum. Descartando...")

                # 6. Manejo de Timeout si no se validó el ACK (pérdida o corrupción)
                elapsed_time = time.time() - start_time
                if elapsed_time < self.timeout:
                    time.sleep(self.timeout - elapsed_time)

                print(f"[EMISOR] -> [!] TIMEOUT alcanzado. No se recibió ACK={self.current_seq}. Retransmitiendo...")

        print("\n================ TRANSMISIÓN FINALIZADA CON ÉXITO ================\n")
        self.print_statistics()

    def print_statistics(self):
        """Muestra el reporte detallado de envíos y retransmisiones."""
        porcentaje_retransmision = (
            (self.total_retransmissions / self.total_transmitted_frames) * 100 
            if self.total_transmitted_frames > 0 else 0.0
        )

        print("--------------------------------------------------")
        print("         MÉTRICAS DE RENDIMIENTO DEL ENLACE       ")
        print("--------------------------------------------------")
        print(f" Tramas de datos originales enviadas : {self.total_original_frames}")
        print(f" Retransmisiones por fallas (ruido)  : {self.total_retransmissions}")
        print(f" Total de tramas enviadas al canal   : {self.total_transmitted_frames}")
        print(f" Tasa de retransmisión               : {porcentaje_retransmision:.2f}%")
        print("--------------------------------------------------\n")


if __name__ == "__main__":
    # Canales con 25% de probabilidad de pérdida y 25% de corrupción para evidenciar retransmisiones
    canal_datos = UnreliableChannel(loss_prob=0.25, corrupt_prob=0.25, min_delay=0.01, max_delay=0.04)
    canal_ack = UnreliableChannel(loss_prob=0.25, corrupt_prob=0.25, min_delay=0.01, max_delay=0.04)

    receptor = Receiver(channel=canal_ack)
    emisor = Sender(channel_to_receiver=canal_datos, channel_to_sender=canal_ack, receiver=receptor, timeout=0.15)

    mensajes_capa_red = [
        b"Trama 1: Arquitectura de capas",
        b"Trama 2: Delimitacion de tramas",
        b"Trama 3: Algoritmo de Checksum",
        b"Trama 4: Control de errores ARQ",
        b"Trama 5: Linea libre de errores lograda",
        b"Trama 6: Verificacion de metricas",
        b"Trama 7: Medicion de desempeno"
    ]

    emisor.send_data(mensajes_capa_red)

    print("--- VERIFICACIÓN EN LA CAPA DE RED RECEPTORA ---")
    datos_recibidos = receptor.received_data
    if datos_recibidos == mensajes_capa_red:
        print("RESULTADO: TODOS LOS PAQUETES LLEGARON ÍNTEGROS, EN ORDEN Y SIN DUPLICADOS.")
    else:
        print("RESULTADO: ERROR EN LA ENTREGA FINAL.")