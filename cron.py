import time
from datetime import datetime

def minha_tarefa():
    print(f"Tarefa executada às {datetime.now()}")

if __name__ == "__main__":
    while True:
        minha_tarefa()
        time.sleep(3600)  # Executa a cada 1 hora (modifique conforme necessário)
