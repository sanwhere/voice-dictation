"""Hata ayiklama: agent loop'u sesli giris olmadan, sabit komutla calistirir."""
import sys
import config
from anthropic import Anthropic
from computer_tool import ComputerTool
from agent import run_command

CMD = "Chrome tarayicisini ac. Acildiktan sonra adres/arama cubugina 'istanbul hava durumu' yazip Enter'a bas ve sonuclarin geldigini gor."

def main():
    print("MODEL:", config.MODEL)
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    computer = ComputerTool()
    print(f"Ekran {computer.real_w}x{computer.real_h} -> {computer.sent_w}x{computer.sent_h} scale={computer.scale:.4f}")
    print("KOMUT:", CMD)
    print("-" * 60)
    result = run_command(client, computer, CMD)
    print("-" * 60)
    print("SONUC:", result)

if __name__ == "__main__":
    main()
