# 🤖 Stock Alerts Discord Bot Plugin

A Discord bot that connects AWS-deployed Django stock alerts system, providing real-time notifications and easy access to your stock alerts directly from Discord.

## 🔗 Invite the Bot
[Click here to add the bot to your server](https://discord.com/oauth2/authorize?client_id=1405342632099708998&permissions=8&integration_type=0&scope=bot)


## 🌟 Features

- **🔐 Secure Authentication** - Login with your  account
- **📈 Real-time Alerts** - Get notified when your stock alerts trigger
- **💬 Rich Discord Embeds** - Beautiful formatted messages with colors and emojis
- **🔄 Auto-monitoring** - Bot checks for triggered alerts every 2 minutes
- **📊 Live Stock Prices** - View current prices from your system
- **🛡️ Session Management** - Secure token-based authentication
- **🔧 Error Handling** - Graceful handling of API failures and timeouts

## 🚀 Quick Start

### Step 1: Discord Bot Setup

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/oauth2/authorize?client_id=1405342632099708998&permissions=8&integration_type=0&scope=bot)
   - Click "New Application" and give it a name
   - Go to "Bot" section → Click "Add Bot"
   - **Copy the Bot Token** (you'll need this!)

2. **Configure Bot Permissions**
   - Under "Privileged Gateway Intents" enable:
     - ✅ Message Content Intent
   - Go to "OAuth2" → "URL Generator"
   - Select: `bot` scope
   - Select permissions: `Send Messages`, `Read Message History`
   - Copy the invite URL

3. **Invite Bot to Server**
   - Use the invite URL to add the bot to your Discord server
   - Bot will appear offline until you run the code

### Step 2: Install Dependencies

```bash
# Create project directory
mkdir stock-alerts-discord-bot
cd stock-alerts-discord-bot

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\\Scripts\\activate
# Mac/Linux:
source venv/bin/activate

# Install required packages
pip install discord.py==2.3.2 requests==2.31.0 python-dotenv==1.0.0
```

### Step 3: Configuration

Create a `.env` file in your project directory:

```env
# Discord Bot Token (from Discord Developer Portal)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

#  AWS Django API URL 
DJANGO_API_URL=https://your-aws-deployment-url.com

# Optional: Custom bot prefix (default is !)
BOT_PREFIX=!

# Optional: Enable debug logging
DEBUG=True
```

**Important:** Replace `your-aws-deployment-url.com` with your actual AWS Django deployment URL!

### Step 4: Run the Bot

1. **Save the bot code** as `main.py` in your project directory
2. **Update your .env file** with correct values
3. **Run the bot:**

```bash
python main.py
```

You should see:
```
🚀 Starting Stock Alerts Discord Bot...
🌐 API Endpoint: https://your-aws-url.com
🤖 Logged in as: YourBotName#1234
✅ Background alert monitoring started
```

## 📱 How to Use

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!login <user> <pass>` | Connect to your stock alerts account | `!login myusername mypassword` |
| `!alert <stock_id> <condition> <price> [duration minutes] ['duration]` | create new alert | `!alert 1 > 200 60 duration` |
| `!alerts` | Show all your alerts | `!alerts` |
| `!alerts active` | Show only active alerts | `!alerts active` |
| `!alerts triggered` | Show triggered alerts | `!alerts triggered` |
| `!stocks` | View current stock prices | `!stocks` |
| `!status` | Check connection status | `!status` |
| `!refresh` | Manually refresh stock prices | `!refresh` |
| `!logout` | Disconnect from account | `!logout` |
| `!help` | Show all commands | `!help` |
| `!ping` | Test bot and API connectivity | `!ping` |

### Usage Flow

1. **Login to your account:**
   ```
   !login yourusername yourpassword
   ```
   ⚠️ *Your login message will be automatically deleted for security*

2. **Check your alerts:**
   ```
   !alerts
   ```
   
3. **View stock prices:**
   ```
   !stocks
   ```

4. **Get automatic notifications:**
   - Bot monitors your alerts every 2 minutes
   - You'll get notified instantly when alerts trigger
   - Notifications appear in the channel where you logged in

## 🔧 Advanced Configuration

### Environment Variables

```env
# Required
DISCORD_BOT_TOKEN=your_token_here
DJANGO_API_URL=https://your-aws-url.com

# Optional
BOT_PREFIX=!                    # Default command prefix
DEBUG=True                      # Enable debug logging
```

### Customizing the Bot

You can modify the bot behavior by editing these variables in `main.py`:

```python
# Change monitoring frequency (default: 2 minutes)
@tasks.loop(minutes=2)  # Change to desired interval

# Change notification cooldown (default: 5 minutes)
if time_since_last.total_seconds() >= 300:  # Change 300 to desired seconds

# Change command prefix
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')  # Change default
```

## 🐛 Troubleshooting

### Common Issues

1. **Bot doesn't respond to commands**
   - Check if bot is online in Discord
   - Verify bot has "Send Messages" permission
   - Ensure "Message Content Intent" is enabled

2. **"Connection Error" when logging in**
   - Check your `DJANGO_API_URL` in .env
   - Ensure your AWS Django system is running
   - Test API manually: `curl https://your-api-url.com/api/stocks/`

3. **"Session Expired" messages**
   - Your Django JWT tokens expired (normal after 1 hour)
   - Simply login again: `!login username password`

4. **Bot stops working after some time**
   - Check console for error messages
   - Restart the bot: `Ctrl+C` then `python main.py`
   - Check your AWS Django system is still running

### Debug Steps

1. **Test API connectivity:**
   ```bash
   curl https://your-aws-url.com/api/stocks/
   ```

2. **Check bot logs:**
   - Look at console output when running the bot
   - Enable DEBUG=True in .env for more detailed logs

3. **Test Discord permissions:**
   - Try `!ping` command
   - Check bot has proper roles/permissions in your server

## 🚀 Deployment Options

### Run on Your Computer
- Simple: Just run `python main.py`
- Bot stops when you close the terminal

### Run on Cloud (24/7)

1. **Heroku (Free tier discontinued, but can use paid)**
2. **Railway.app (Free tier available)**
3. **Replit (Free tier available)**
4. **Your own VPS/server**

### Example Railway Deployment

1. Create account at [Railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy automatically

## 🔒 Security Notes

- **Never share your Discord bot token**
- **Login messages are automatically deleted**
- **Use environment variables for sensitive data**
- **Consider using Discord slash commands for better security**

## 🆘 Support

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Verify your AWS Django system is accessible**
3. **Test API endpoints manually**
4. **Check Discord bot permissions**

## 📝 API Endpoints Used

The bot connects to these Django API endpoints:

- `POST /api/auth/login/` - User authentication
- `GET /api/alerts/` - Get user alerts
- `GET /api/alerts/triggered/` - Get triggered alerts
- `GET /api/alerts/summary/` - Get alert summary
- `GET /api/stocks/` - Get stock prices
- `POST /api/stocks/actions/refresh-prices/` - Refresh prices

## 🎯 Next Steps

1. **Test the bot** with your Django system
2. **Customize commands** as needed
3. **Deploy to cloud** for 24/7 operation
4. **Add more features** (delete alerts, etc.)

---

**YAHYA | Happy Trading! 📈🤖**
