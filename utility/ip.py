import subprocess
import random


def generate_random_port():
    return random.randint(1024, 65535)


def get_local_ip_address():
    result = subprocess.run(["ip", "addr"], capture_output=True).stdout.strip()
    for line in result.splitlines():
        line = line.decode("utf-8")
        if "inet" in line and "scope global" in line:
            return line.split()[1].split("/")[0]
