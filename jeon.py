import json
import time
import random
from decimal import Decimal
from web3 import Web3, HTTPProvider
from eth_account import Account
from rich.console import Console
from rich.panel import Panel

# Setup console
console = Console()

# Constants
CHAIN_ID = 11155111
PRIVATE_KEYS_FILE = "pkevm.txt"
PROXY_LIST_FILE = "proxy.txt"
TOKEN_ABI_FILE = "token_abi.json"
ROUTER_ABI_FILE = "router_swap_abi.json"
TOKEN_R2 = Web3.to_checksum_address("0xb816bB88f836EA75Ca4071B46FF285f690C43bb7")
TOKEN_USDC = Web3.to_checksum_address("0x8BEbFCBe5468F146533C182dF3DFbF5ff9BE00E2")
ROUTER = Web3.to_checksum_address("0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3")
DECIMALS_R2 = 18
DECIMALS_USDC = 6
POINTS_PER_SWAP = 40000
MAX_POINTS = 400000

# Load ABIs
with open(TOKEN_ABI_FILE) as f:
    token_abi = json.load(f)
with open(ROUTER_ABI_FILE) as f:
    router_abi = json.load(f)

def load_proxies(file_path=PROXY_LIST_FILE):
    try:
        with open(file_path) as f:
            proxies = [line.strip() for line in f if line.strip()]
        console.print(f"[green]✅ Loaded {len(proxies)} proxies.[/green]")
        return proxies
    except FileNotFoundError:
        console.print("[yellow]⚠️ proxy.txt not found. Will connect directly.[/yellow]")
        return []

def get_random_proxy(proxy_list):
    if not proxy_list:
        return None
    return random.choice(proxy_list)

def create_web3_with_proxy(proxy_url=None, rpc_url="https://ethereum-sepolia-rpc.publicnode.com"):
    if proxy_url is None:
        console.print(f"[blue]🌐 Connecting direct: {rpc_url}[/blue]")
        provider = HTTPProvider(rpc_url, request_kwargs={"timeout": 20})
    else:
        console.print(f"[blue]🌐 Connecting via proxy: {proxy_url}[/blue]")
        provider = HTTPProvider(
            rpc_url,
            request_kwargs={
                "proxies": {"http": proxy_url, "https": proxy_url},
                "timeout": 20,
            },
        )
    w3 = Web3(provider)
    if not w3.is_connected():
        console.print(f"[red]❌ Connection failed.[/red]")
        return None
    console.print(f"[green]✅ Connected successfully.[/green]")
    return w3

def get_nonce(w3, address):
    return w3.eth.get_transaction_count(address, 'pending')

def get_gas_price(w3):
    return int(w3.eth.gas_price * 1.2)

def approve_token(w3, wallet_address, private_key, token_address, spender, amount):
    contract = w3.eth.contract(address=token_address, abi=token_abi)
    allowance = contract.functions.allowance(wallet_address, spender).call()
    if allowance >= amount:
        return True
    tx = contract.functions.approve(spender, amount).build_transaction({
        'from': wallet_address,
        'nonce': get_nonce(w3, wallet_address),
        'gasPrice': get_gas_price(w3),
        'gas': 60000,
        'chainId': CHAIN_ID
    })
    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return True

def swap(w3, wallet_address, private_key, amount, path):
    contract = w3.eth.contract(address=ROUTER, abi=router_abi)
    tx = contract.functions.swapExactTokensForTokens(
        amount,
        0,
        path,
        wallet_address,
        int(time.time()) + 600
    ).build_transaction({
        'from': wallet_address,
        'nonce': get_nonce(w3, wallet_address),
        'gas': 300000,
        'gasPrice': get_gas_price(w3),
        'chainId': CHAIN_ID
    })
    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.status == 1, tx_hash.hex()

def get_balance(w3, token_address, wallet_address):
    contract = w3.eth.contract(address=token_address, abi=token_abi)
    return contract.functions.balanceOf(wallet_address).call()

def format_amount(value, decimals):
    return Decimal(value) / Decimal(10 ** decimals)

def main():
    logo = """
     ██╗ ███████╗ ██████╗ ███╗   ██╗
     ██║ ██╔════╝██╔═══██╗████╗  ██║
     ██║ █████╗  ██║   ██║██╔██╗ ██║
██   ██║ ██╔══╝  ██║   ██║██║╚██╗██║
╚█████╔╝ ███████╗╚██████╔╝██║ ╚████║
 ╚════╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
          J E O N   B O T
    """

    console.print(f"[bold magenta]{logo}[/bold magenta]")
    console.print(Panel.fit("[bold cyan]✨ Jeon Auto Trade R2 ✨[/bold cyan]", border_style="bright_magenta"))

    with open(PRIVATE_KEYS_FILE) as f:
        private_keys = [x.strip() for x in f if x.strip()]
    proxy_list = load_proxies()

    for i, pk in enumerate(private_keys, 1):
        acc = Account.from_key(pk)
        addr = acc.address

        console.print(Panel.fit(f"[bold cyan]Wallet #{i} → {addr}[/bold cyan]"))

        # Try up to 3 proxies before skipping
        attempts = 3
        w3 = None
        for attempt in range(attempts):
            proxy_url = get_random_proxy(proxy_list)
            w3 = create_web3_with_proxy(proxy_url)
            if w3:
                break

        if not w3:
            console.print(f"[red]🚫 All proxies failed. Skipping wallet {addr}.[/red]")
            continue

        total_points = 0
        swap_count = 0

        while total_points < MAX_POINTS:
            r2_balance = get_balance(w3, TOKEN_R2, addr)
            usdc_balance = get_balance(w3, TOKEN_USDC, addr)
            console.print(f"[blue]💰 R2: {format_amount(r2_balance, DECIMALS_R2):.4f} | USDC: {format_amount(usdc_balance, DECIMALS_USDC):.4f}[/blue]")

            amount_r2 = int(Decimal("14.6") * 10 ** DECIMALS_R2)
            amount_usdc = int(Decimal("5.0") * 10 ** DECIMALS_USDC)
            did_swap = False

            if r2_balance >= amount_r2:
                approve_token(w3, addr, pk, TOKEN_R2, ROUTER, amount_r2)
                status1, tx1 = swap(w3, addr, pk, amount_r2, [TOKEN_R2, TOKEN_USDC])
                if status1:
                    console.print(f"[green]✅ Swap R2 → USDC ({format_amount(amount_r2, DECIMALS_R2):.4f} R2) | TX: {tx1}[/green]")
                    swap_count += 1
                    total_points += POINTS_PER_SWAP
                    did_swap = True
                    time.sleep(random.randint(10, 20))

            if usdc_balance >= amount_usdc:
                approve_token(w3, addr, pk, TOKEN_USDC, ROUTER, amount_usdc)
                status2, tx2 = swap(w3, addr, pk, amount_usdc, [TOKEN_USDC, TOKEN_R2])
                if status2:
                    console.print(f"[green]✅ Swap USDC → R2 ({format_amount(amount_usdc, DECIMALS_USDC):.4f} USDC) | TX: {tx2}[/green]")
                    swap_count += 1
                    total_points += POINTS_PER_SWAP
                    did_swap = True

            if did_swap:
                percent = (total_points / MAX_POINTS) * 100
                console.print(f"[cyan]🔄 Total swap: {swap_count}, Estimasi poin: {total_points} ({percent:.2f}%)[/cyan]")
            else:
                console.print("[yellow]⚠️ Saldo tidak cukup untuk swap berikutnya.[/yellow]")
                break

            if total_points >= MAX_POINTS:
                console.print("[bold green]🎉 Target poin harian tercapai![/bold green]")
                break

            delay = random.randint(10, 20)
            console.print(f"[blue]⏳ Menunggu {delay} detik sebelum loop berikutnya...[/blue]")
            time.sleep(delay)

if __name__ == "__main__":
    main()
