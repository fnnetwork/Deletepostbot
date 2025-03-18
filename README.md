# Telegram Mega Cleaner Bot

This is a powerful Telegram bot that allows users to delete all messages from a Telegram channel. The bot can work in two modes:

1. **User Mode**: Use your own API credentials for full access to delete messages from channels.
2. **Admin Mode**: Operate as a bot in channels where it has admin rights. It has limited access due to Telegram's restrictions.

## Features

- **User Mode**: The bot can delete messages using your personal API credentials.
- **Admin Mode**: The bot can delete messages in channels where it has admin rights (with limited functionality due to Telegram restrictions).
- **Rate Limiting**: The bot handles rate limits and flood waits automatically to ensure smooth operation.
- **Bot Cooldown**: A cooldown of 30 seconds is enforced between actions to prevent abuse.

## Prerequisites

Before you start, make sure you have the following:

- **Telegram Bot Token**: You can obtain this by creating a bot on [BotFather](https://core.telegram.org/bots#botfather).
- **API ID and API Hash**: These can be obtained by registering your application on [my.telegram.org](https://my.telegram.org/auth).
- **Python 3.7+**: Make sure Python 3.7 or higher is installed on your system.
- **pip**: To install the required dependencies.

## Installation Steps

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/Anujtemp/deleteposttg.git
cd deleteposttg
```

### 2. Install Dependencies

Install the required Python dependencies by running:

```bash
pip install -r requirements.txt
```

This will install all the necessary libraries, including **Telethon** for interacting with the Telegram API.

### 3. Set Up Environment Variables

Create a `.env` file in the project directory and add the following environment variables with your bot token, API ID, and API hash:

```ini
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_API_ID=your-api-id-here
TELEGRAM_API_HASH=your-api-hash-here
```

You can obtain the **API ID** and **API Hash** from [my.telegram.org](https://my.telegram.org/auth).

### 4. Running the Bot

To run the bot, simply execute the following command:

```bash
python bot.py
```

Once the bot is running, it will listen for incoming messages and commands in Telegram.

### 5. Interacting with the Bot

After the bot starts, you can interact with it directly from Telegram. The available commands are:

- **/start**: Start the bot and choose an operation mode.
- **/cancel**: Cancel any ongoing operation.
- **/user_mode**: Use your own API credentials to delete messages from a channel.
- **/admin_mode**: Use the bot as an admin in a channel to delete messages (restricted).
- **/help**: Get a help message showing available commands and usage instructions.

## Deploying the Bot

### Deploying on a Linux Server (e.g., Ubuntu)

1. **Install Python 3 and pip**

   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **Clone the Repository on the Server**

   ```bash
   git clone https://github.com/Anujtemp/deleteposttg.git
   cd deleteposttg
   ```

3. **Install Dependencies**

   ```bash
   pip3 install -r requirements.txt
   ```

4. **Set Up Environment Variables**

   Create a `.env` file on your server with the necessary credentials:

   ```ini
   TELEGRAM_BOT_TOKEN=your-bot-token-here
   TELEGRAM_API_ID=your-api-id-here
   TELEGRAM_API_HASH=your-api-hash-here
   ```

5. **Run the Bot**

   ```bash
   python3 bot.py
   ```

   The bot will now run in your terminal, and you can interact with it from your Telegram app.

### Deploying on Heroku

1. **Create a Heroku Account**: Sign up [here](https://signup.heroku.com/) if you don't have an account.
2. **Install the Heroku CLI**: Follow the instructions [here](https://devcenter.heroku.com/articles/heroku-cli).
3. **Prepare Your Project for Heroku**

   Create a `Procfile` in the project directory with the following content:

   ```ini
   web: python bot.py
   ```

   Generate a `requirements.txt` file if you haven't done so:

   ```bash
   pip freeze > requirements.txt
   ```

4. **Deploy to Heroku**

   Use the Heroku CLI to create a new app and push the code:

   ```bash
   heroku create your-app-name
   git push heroku master
   ```

5. **Set Environment Variables on Heroku**

   In your Heroku dashboard, navigate to **Settings** > **Config Vars** and add:

   ```ini
   TELEGRAM_BOT_TOKEN=your-bot-token-here
   TELEGRAM_API_ID=your-api-id-here
   TELEGRAM_API_HASH=your-api-hash-here
   ```

6. **Scale Your Heroku App**

   ```bash
   heroku ps:scale web=1
   ```

   The bot will run on Heroku, and you can interact with it via Telegram.

### Deploying on Replit

Replit provides an easy way to deploy your bot without managing your own server. Follow these steps to get your bot running on Replit:

1. **Create a New Repl**

   - Go to [Replit](https://replit.com/) and sign in or create an account.
   - Create a new Repl and choose **Python** as the template. Alternatively, you can import your GitHub repository by selecting the **Import from GitHub** option.

2. **Add Environment Secrets**

   - In the Replit sidebar, click on the **Secrets** (or **Environment Variables**) icon.
   - Add the following secrets with their respective values:
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_API_ID`
     - `TELEGRAM_API_HASH`

3. **Configure the Run Command**

   Create a file named `.replit` in your project directory with the following content to specify how the bot should run:

   ```ini
   run = "python bot.py"
   ```

4. **Run the Bot**

   - Click the **Run** button at the top of the Replit interface.
   - The console will start, and your bot will begin running. You can now interact with it via Telegram.

## Troubleshooting

- **FloodWaitError**: This error occurs when the bot exceeds Telegram's allowed rate limits. The bot will automatically wait for the required time before retrying.
- **Invalid API credentials**: Double-check your `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and bot token.
- **Bot Not Added as Admin (Admin Mode)**: Make sure the bot has admin rights with delete permissions in the channel.

## Contact

For questions, issues, or feedback, feel free to contact me on Telegram:

[Anuj Singh](https://t.me/Anuj_singg)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Special thanks to [Telethon](https://github.com/LonamiWebs/Telethon) for their excellent Python wrapper for Telegram's MTProto API.
- Inspired by various Telegram bot automation projects.

Happy Cleaning!
