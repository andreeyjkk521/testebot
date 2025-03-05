import datetime
import mercadopago
from telethon import TelegramClient, events
import json
import asyncio

# Tokens
TOKEN_MERCADOPAGO = 'APP_USR-6879684110464729-012013-4335b580e9be239df5fe65272b7365a4-1385934742'
LOG_BOT_TOKEN = '8133880602:AAG7HStSqFIREyCy9qG3c9V85wJMzE4nOg8'  # Substitua pelo token do bot de logs

# Inicializando a SDK do MercadoPago
sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)

# Configurações do cliente
api_id = '19921533'
api_hash = '89ff4cfe2bf0439ef7d55994947fb4fb'
phone_number = '+5519994223348'

# IDs dos grupos
LOG_GROUP_ID = -1002294216444  # Substitua pelo ID do grupo de logs no Telegram
VIP_GROUP_ID = -1002249976085  # Substitua pelo ID do grupo VIP no Telegram

# Variável para gerenciar estados dos usuários
user_states = {}

# Link do grupo VIP para envio após confirmação do pagamento
GROUP_LINK = "https://t.me/+B_7Dlln4BcsyZDRh"

# Arquivo para salvar os IDs dos usuários
USER_FILE = "user_ids.json"
PENDING_REQUESTS_FILE = "pending_requests.txt"

def load_user_ids():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# Função para salvar as IDs dos usuários
def save_user_ids(user_data):
    try:
        with open(USER_FILE, "w") as file:
            json.dump(user_data, file, indent=4)
    except Exception as e:
        print(f"Erro ao salvar os dados do usuário: {e}")

# Inicializar o arquivo
user_data = load_user_ids()

# Função para salvar IDs de solicitações pendentes
def save_pending_request(user_id):
    try:
        with open(PENDING_REQUESTS_FILE, "a") as file:
            file.write(f"{user_id}\n")
        print(f"ID do usuário {user_id} salvo com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar a solicitação pendente: {e}")

# Função para carregar IDs de solicitações pendentes
def load_pending_requests():
    try:
        with open(PENDING_REQUESTS_FILE, "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        return []

# Função para enviar logs detalhados para o grupo de logs
async def send_log_to_group(client, message):
    await client.send_message(LOG_GROUP_ID, message)
    print(message)  # Log no console

# Inicializando o cliente do Telegram
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.ChatAction)
async def handle_join_request(event):
    if event.user_added or event.user_joined:
        if event.chat_id == VIP_GROUP_ID:  # Verifica se o evento está ocorrendo no grupo VIP
            user_id = event.user_id
            save_pending_request(user_id)
            
            # Envia log da solicitação de entrada para o grupo de logs
            log_message = f"Nova solicitação de entrada no grupo VIP de ID: {user_id}"
            await send_log_to_group(client, log_message)
            
            # Envia mensagem privada ao usuário oferecendo o curso
            message = (
                "Olá! 🎉\n\n"
                "Vimos que você solicitou a entrada no nosso grupo VIP de inglês. "
                "Para garantir sua vaga, oferecemos um curso exclusivo por apenas R$ 9,99. "
                "Você terá acesso a aulas semanais, materiais de estudo, suporte direto com o professor e muito mais!\n\n"
                "Clique no link abaixo para saber mais e fazer o pagamento:\n"
                f"{GROUP_LINK}\n\n"
                "Qualquer dúvida, estamos à disposição!"
            )
            await client.send_message(user_id, message)
            print(f"Mensagem enviada para o usuário {user_id}")

async def send_pending_requests_to_log():
    while True:
        pending_requests = load_pending_requests()
        if pending_requests:
            message = "IDs pendentes no grupo VIP:\n" + "\n".join(pending_requests)
            await send_log_to_group(client, message)
        await asyncio.sleep(3600)  # Espera 1 hora antes de enviar novamente

async def main():
    await client.start(phone_number)
    print("Client started")
    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
