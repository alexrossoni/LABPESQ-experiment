import os
import time
import random
import re
import matplotlib.pyplot as plt
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink

# Configurations
output_dir = "experiment_results"
os.makedirs(output_dir, exist_ok=True)

def simulate_network(known_demands):
    """
    Simulate network in Mininet with or without known traffic demands.
    :param known_demands: Boolean indicating if demands are known beforehand.
    :return: Tuple with average latency and packet loss percentage.
    """
    net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink)

    # Setup topology
    info("*** Adding controller\n")
    net.addController('c0')

    info("*** Adding hosts and switch\n")
    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')
    s1 = net.addSwitch('s1')

    info("*** Creating links\n")
    net.addLink(h1, s1, bw=100)
    net.addLink(h2, s1, bw=100)

    info("*** Starting network\n")
    net.start()

    # Traffic generation
    traffic_demands = [random.randint(10, 100) if not known_demands else 50 for _ in range(10)]
    latencies = []
    packet_losses = []

    for demand in traffic_demands:
        info(f"*** Simulating traffic with demand: {demand} Mbps\n")
        h1.cmd(f"iperf -s -u -p 5001 &")
        result = h2.cmd(f"iperf -c 10.0.0.1 -u -p 5001 -b {demand}M -t 2")

        print(result)

        # Inicialização das variáveis
        latency = 0
        loss = 0
        sent_packets = 0
        lost_packets = 0

        # Parse da saída do iperf para extrair as métricas
        try:
            # Buscar latência (número antes de "ms")
            latency_match = re.search(r"(\d+\.\d+)\s*ms", result)
            if latency_match:
                latency = float(latency_match.group(1))

            # Buscar perda de pacotes (número antes de "%")
            loss_match = re.search(r"\((\d+\.\d+)%\)", result)
            if loss_match:
                loss = float(loss_match.group(1))

            # Buscar número de pacotes enviados e perdidos
            packets_match = re.search(r"(\d+)/(\d+)", result)
            if packets_match:
                lost_packets = int(packets_match.group(1))
                sent_packets = int(packets_match.group(2))
                # Ajuste da taxa de perda baseada no total de pacotes enviados
                if sent_packets > 0:
                    loss = (lost_packets / sent_packets) * 100
        except Exception as e:
            print(f"Erro ao processar métricas: {e}")
            loss = 100  # Valor padrão caso ocorra erro

        # Armazenar métricas para cálculo final
        latencies.append(latency)
        packet_losses.append(loss)

        h1.cmd("pkill iperf")

    info("*** Stopping network\n")
    net.stop()

    # Cálculo das médias
    avg_latency = sum(latencies) / len(latencies)
    avg_packet_loss = sum(packet_losses) / len(packet_losses)

    return avg_latency, avg_packet_loss

def run_experiment():
    """Run experiments with and without knowledge of traffic demands."""
    info("*** Running experiment with known demands\n")
    known_latency, known_loss = simulate_network(known_demands=True)

    info("*** Running experiment with unknown demands\n")
    unknown_latency, unknown_loss = simulate_network(known_demands=False)

    # Save results
    results_file = os.path.join(output_dir, "results.txt")
    with open(results_file, "w") as f:
        f.write(f"Known Demands:\nAverage Latency: {known_latency:.2f} ms\nPacket Loss: {known_loss:.2f}%\n\n")
        f.write(f"Unknown Demands:\nAverage Latency: {unknown_latency:.2f} ms\nPacket Loss: {unknown_loss:.2f}%\n")

    info(f"Results saved to {results_file}\n")

    # Plot results
    metrics = ["Latency (ms)", "Packet Loss (%)"]
    known_metrics = [known_latency, known_loss]
    unknown_metrics = [unknown_latency, unknown_loss]

    for i, metric in enumerate(metrics):
        plt.figure()
        plt.bar(["Known", "Unknown"], [known_metrics[i], unknown_metrics[i]], color=['blue', 'orange'])
        plt.ylabel(metric)
        plt.title(f"{metric} Comparison")
        graph_path = os.path.join(output_dir, f"{metric.replace(' ', '_').lower()}_comparison.png")
        plt.savefig(graph_path)
        plt.close()

    info(f"Graphs saved to {output_dir}\n")

if __name__ == "__main__":
    setLogLevel("info")
    run_experiment()
