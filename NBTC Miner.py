import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import time
import os
import platform
import random
import threading

# Détecter le système d'exploitation
is_windows = platform.system() == 'Windows'

# Définir les chemins et commandes en fonction du système d'exploitation
if is_windows:
    bitcoin_cli = r"C:\Program Files\Bitcoin\daemon\bitcoin-cli.exe"
    datadir = r"C:\Program Files\Bitcoin"
else:
    bitcoin_cli = "/Users/francisc/newbitcoin/build/src/bitcoin-cli"
    datadir = "/Users/francisc/Library/Application Support/Bitcoin"

# Paramètres de connexion RPC
rpcuser = "user"
rpcpassword = "password"
rpcport = "9332"

# Adresses de test pour simulation d'activité Wallet. YOUR ADDRESSE !!!
# Si tu ne change pas ces adresses les newbitcoins evoiye seront perdu !!!
addresses_list = [
    "bc1qgam2g3thvszfhnjyswpv0hxfdp5zpqg483ulnr",
    "bc1qgam2g3thvszfhnjyswpv0hxfdp5zpqg483ulnr"
]

# Gestion du fichier address.txt
def load_addresses():
    if os.path.exists('address.txt'):
        with open('address.txt', 'r') as f:
            return [line.strip() for line in f if validate_address(line.strip())]
    return []

def save_address(address):
    addresses = load_addresses()
    if address not in addresses:
        with open('address.txt', 'a') as f:
            f.write(address + '\n')
    return addresses

# Validation d'une adresse
def validate_address(address):
    return address.startswith("bc1") and len(address) == 42

# Vérification du serveur bitcoin-qt
def verifier_serveur():
    try:
        subprocess.check_output([bitcoin_cli, "-rpcuser=" + rpcuser, "-rpcpassword=" + rpcpassword, "-rpcport=" + rpcport, "getblockchaininfo"])
        return True
    except subprocess.CalledProcessError:
        return False

# Récupération des informations du portefeuille
def get_wallet_info():
    try:
        result = subprocess.check_output([
            bitcoin_cli, "-rpcuser=" + rpcuser, "-rpcpassword=" + rpcpassword,
            "-rpcport=" + rpcport, "getwalletinfo"
        ]).decode('utf-8').strip()
        return json.loads(result)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erreur", f"Impossible de récupérer les informations du portefeuille : {e}")
        return None

# Vérifier l'adresse et récupérer les informations du portefeuille
def verify_address():
    address = address_entry.get()
    if not validate_address(address):
        messagebox.showerror("Erreur", "Adresse invalide.")
        return

    new_addresses = save_address(address)
    address_entry['values'] = new_addresses

    wallet_info = get_wallet_info()
    if wallet_info:
        balance = wallet_info.get('balance', 0.0)
        wallet_info_label.config(text=f"Solde: {balance} BTC")

# Simulation de transactions aléatoires
activity_running = False

def simulate_activity():
    global activity_running
    while activity_running:
        address = address_entry.get()
        if validate_address(address):
            random_address = random.choice(addresses_list)
            amount = random.uniform(1, 2)
            command = f"{bitcoin_cli} -rpcuser={rpcuser} -rpcpassword={rpcpassword} -rpcport={rpcport} sendtoaddress {random_address} {amount:.8f}"
            try:
                subprocess.check_output(command, shell=True)
                log_text.insert(tk.END, f"Envoyé {amount:.8f} BTC de {address} à {random_address}\n")
            except subprocess.CalledProcessError as e:
                log_text.insert(tk.END, f"Erreur lors de l'envoi: {e}\n")
            log_text.see(tk.END)
        time.sleep(200)

def toggle_activity():
    global activity_running
    if activity_running:
        activity_running = False
        activity_button.config(text="Démarrer la simulation")
    else:
        activity_running = True
        activity_button.config(text="Arrêter la simulation")
        threading.Thread(target=simulate_activity, daemon=True).start()

# Fonction de minage et affichage des informations de la blockchain
def miner_et_afficher_infos(adresse):
    """Fonction pour miner et afficher les informations sur la blockchain."""
    try:
        # Exécuter la commande de minage
        subprocess.call([
            bitcoin_cli,
            "-rpcport=" + rpcport,
            "-rpcuser=" + rpcuser,
            "-rpcpassword=" + rpcpassword,
            "generatetoaddress", "1", adresse
        ])

        # Récupérer les informations de la blockchain
        info_blockchain = subprocess.check_output([
            bitcoin_cli,
            "-rpcport=" + rpcport,
            "-rpcuser=" + rpcuser,
            "-rpcpassword=" + rpcpassword,
            "getblockchaininfo"
        ]).decode()

        data_blockchain = json.loads(info_blockchain)
        return data_blockchain['blocks']  # Retourne la hauteur du bloc trouvé
    except subprocess.CalledProcessError:
        return None
    except json.JSONDecodeError:
        return None

# Minage et informations de portefeuille
def demarrer_minage():
    """Fonction pour démarrer le minage."""
    adresse_bitcoin = address_entry.get()
    
    if not validate_address(adresse_bitcoin):
        log_text.insert(tk.END, "Adresse non valide. Veuillez en saisir une nouvelle.\n")
        return

    temps_ecoule = 0
    last_height = 0
    is_mining = True

    while is_mining:
        if not verifier_serveur():
            log_text.insert(tk.END, "Erreur : bitcoin-qt ne fonctionne pas.\n")
            break

        wallet_info = get_wallet_info()
        if wallet_info:
            wallet_name = wallet_info.get('walletname', 'inconnu')
            balance = wallet_info.get('balance', 0.0)
            immature_balance = wallet_info.get('immature_balance', 0.0)
            current_height = miner_et_afficher_infos(adresse_bitcoin)

            # Calcul du total NBTC (solde mature + solde immature)
            total_nbtc = balance + immature_balance

            log_text.insert(tk.END, f"Portefeuille chargé : {wallet_name} : OK\n")
            log_text.insert(tk.END, f"Hauteur : {current_height}\n")
            log_text.insert(tk.END, f"Solde : {balance}\n")
            log_text.insert(tk.END, f"Solde immature : {immature_balance}\n")
            log_text.insert(tk.END, f"Total NBTC : {total_nbtc}\n")  # Ligne ajoutée pour afficher le total

            if current_height and current_height > last_height:
                log_text.insert(tk.END, f"Bloc trouvé ! Hauteur : {current_height}\n")
                last_height = current_height
                temps_ecoule = 0  # Réinitialiser le compteur

            log_text.insert(tk.END, f"Temps depuis le dernier bloc miné : {temps_ecoule} secondes\n")
            temps_ecoule += 1

        log_text.yview(tk.END)  # Faire défiler vers le bas
        log_text.update()  # Mettre à jour le texte à l'écran
        time.sleep(600)


# Interface utilisateur
root = tk.Tk()
root.title("NewBitcoin Miner & Activity")

addresses = load_addresses()

address_label = tk.Label(root, text="What is your newbitcoin address?")
address_label.pack()

address_entry = ttk.Combobox(root, width=40, values=addresses)
if addresses:
    address_entry.set(addresses[0])
address_entry.pack()

verify_button = tk.Button(root, text="Vérifier l'adresse", command=verify_address)
verify_button.pack()

activity_button = tk.Button(root, text="Démarrer la simulation", command=toggle_activity)
activity_button.pack()

mine_button = tk.Button(root, text="Start mining", command=demarrer_minage)
mine_button.pack()

wallet_info_label = tk.Label(root, text="")
wallet_info_label.pack()

log_text = tk.Text(root, height=20, width=70)
log_text.pack()

root.mainloop()
