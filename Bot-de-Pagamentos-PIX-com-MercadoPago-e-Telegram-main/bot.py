import datetime
import mercadopago
import telebot
import base64
from PIL import Image
from io import BytesIO
import time

# Tokens
TOKEN_MERCADOPAGO = 'APP_USR-6879684110464729-012013-4335b580e9be239df5fe65272b7365a4-1385934742'
TOKEN_BOT = '8133880602:AAG7HStSqFIREyCy9qG3c9V85wJMzE4nOg8'

# Inicializando a SDK do MercadoPago e o Bot do Telegram
sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)
bot = telebot.TeleBot(TOKEN_BOT)

# Variável para gerenciar estados dos usuários
user_states = {}

# Defina o link do grupo para enviar quando o pagamento for confirmado
GROUP_LINK = "https://t.me/+NP56Z0u9xTFmNTdh"
GROUP_ID = -1002294216444  # Substitua pelo ID do grupo criado com o bot

# Função para criar pagamento via PIX
def create_payment(value):
    expire = datetime.datetime.now() + datetime.timedelta(days=1)  # Define validade de 1 dia
    expire = expire.strftime("%Y-%m-%dT%H:%M:%S.000-03:00")  # Usando %H ao invés de %-H

    payment_data = {
        "transaction_amount": float(value),
        "payment_method_id": 'pix',
        "installments": 1,
        "description": 'Curso de Inglês Privado',
        "date_of_expiration": f"{expire}",
        "payer": {
            "email": 'andreeyjkk@gmail.com'  # E-mail fixo do cliente
        }
    }
    
    result = sdk.payment().create(payment_data)
    return result

# Função para enviar relatórios para o grupo
def send_to_group(message, custom_text=None):
    user = message.from_user
    report = (
        f"📥 *Nova mensagem recebida pelo bot:*\n\n"
        f"👤 *Usuário*: {user.first_name} {user.last_name if user.last_name else ''}\n"
        f"🆔 *ID do usuário*: {user.id}\n"
        f"📧 *Username*: @{user.username if user.username else 'Não definido'}\n"
    )

    if message.text:
        report += f"💬 *Mensagem*: {message.text}\n"
    else:
        report += "💬 *Mensagem*: [Mensagem não textual]\n"

    if custom_text:
        report += f"\n📌 *Detalhes*: {custom_text}"

    bot.send_message(GROUP_ID, report, parse_mode="Markdown")

# Função para verificar o estado do pagamento
def verify_payment_status(payment_id):
    result = sdk.payment().get(payment_id)
    payment = result["response"]
    
    if payment['status'] == 'approved':
        return "Pagamento aprovado com sucesso! 🎉"
    elif payment['status'] == 'pending':
        return "Pagamento pendente. Estamos aguardando a confirmação do seu pagamento."
    elif payment['status'] == 'cancelled':
        return "Pagamento cancelado ou expirado. 😞"
    else:
        return "Erro ao verificar o status do pagamento."

# Função para monitorar o pagamento
def monitor_payment(payment_id, user_id):
    while True:
        status_message = verify_payment_status(payment_id)
        
        if "aprovado" in status_message.lower():
            bot.send_message(user_id, "🎉 Parabéns! Seu pagamento foi aprovado com sucesso! 🎉")
            bot.send_message(user_id, "Agora você tem acesso ao nosso exclusivo curso de inglês privado!")
            bot.send_message(user_id, f"Para começar, clique no link abaixo e junte-se ao nosso grupo de alunos!")
            bot.send_message(user_id, GROUP_LINK)
            break  # Interrompe o loop ao confirmar pagamento
        elif "pendente" in status_message.lower():
            bot.send_message(user_id, "Seu pagamento está pendente. Continuamos monitorando.")
        time.sleep(15)

# Função para processar a compra
def process_purchase(message):
    try:
        payment_response = create_payment(9.99)  # Cria o pagamento com valor R$ 9,99
        payment_data = payment_response.get("response", {})
        
        if payment_data:
            payment_id = payment_data["id"]
            pix_qr_code = payment_data["point_of_interaction"]["transaction_data"]["qr_code"]
            pix_qr_image = payment_data["point_of_interaction"]["transaction_data"]["qr_code_base64"]

            user_states[message.chat.id] = "comprando"  # Altera o estado para "comprando"

            # Envia o QR Code como imagem
            image_data = BytesIO(base64.b64decode(pix_qr_image))
            bot.send_photo(message.chat.id, photo=image_data, caption="Escaneie o QR Code acima para pagar. ✅")
            
            # Envia o código PIX
            bot.send_message(message.chat.id, f"Ou copie e cole o código PIX abaixo no app do seu banco:\n\n`{pix_qr_code}`", parse_mode="Markdown")

            # Monitora o pagamento
            bot.send_message(message.chat.id, "Estamos monitorando o pagamento. Você será notificado ao ser aprovado.")
            monitor_payment(payment_id, message.chat.id)
        else:
            bot.send_message(message.chat.id, "Erro ao processar a compra. Tente novamente mais tarde.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Erro ao criar pagamento: {str(e)}")
        send_to_group(message, f"Erro ao processar pagamento: {str(e)}")

# Função para perguntar se o cliente deseja comprar
def ask_if_buy(message):
    user_states[message.chat.id] = "inicio"
    bot.send_message(
        message.chat.id,
        "Olá! Você está interessado em adquirir nosso curso de inglês por apenas R$ 9,99? 👩‍🏫"
        " Responda 'Sim' para comprar ou 'Não' se não estiver interessado."
    )
    send_to_group(message, "Perguntado ao usuário se deseja comprar o curso.")

# Função de resposta inteligente
def handle_user_response(message):
    response = message.text.lower()

    if any(keyword in response for keyword in ["sim", "quero comprar", "quero o curso", "fazer a compra", "comprar"]):
        process_purchase(message)
    elif any(keyword in response for keyword in ["não", "não quero", "não estou interessado"]):
        bot.send_message(message.chat.id, "Tudo bem! Se mudar de ideia, basta escrever 'Sim' ou usar /start.")
        user_states[message.chat.id] = "finalizado"
    elif any(keyword in response for keyword in ["quero saber mais", "me fala sobre o curso", "quais são os benefícios", "como funciona", "o que vou aprender"]):
        bot.send_message(message.chat.id, "Nosso curso oferece aulas personalizadas de inglês. Você aprende no seu ritmo, com apoio contínuo!")
    elif any(keyword in response for keyword in ["quanto custa", "qual valor", "quanto é", "qual preço"]):
        bot.send_message(message.chat.id, "O valor do curso é R$ 9,99, acessível e com ótimo conteúdo!")
    else:
        bot.send_message(message.chat.id, "Desculpe, não entendi. Você gostaria de saber mais sobre o curso ou deseja comprá-lo?")

# Captura todas as mensagens recebidas e responde com direcionamento para a venda
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    send_to_group(message, "Mensagem capturada pelo bot.")
    state = user_states.get(message.chat.id, "none")
    
    if state == "none":
        # Pergunta se deseja comprar quando a primeira mensagem for recebida
        ask_if_buy(message)
    else:
        handle_user_response(message)

if __name__ == "__main__":
    bot.infinity_polling()
