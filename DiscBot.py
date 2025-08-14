"""
Stock Alerts Discord Bot Plugin
Connects AWS-deployed Django stock alerts system

This bot provides:
1. User authentication with your Django API
2. Real-time alert monitoring
3. Stock price checking
4. Rich Discord embeds for better user experience
"""

import discord
from discord.ext import commands, tasks
import requests
import json
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging to help with debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAlertsBot:
    """
    Main bot class that handles all Discord interactions and API connections
    """
    
    def __init__(self):
        # Bot configuration from environment variables
        self.bot_token = os.getenv('DISCORD_BOT_TOKEN')
        self.django_api_url = os.getenv('DJANGO_API_URL', '').rstrip('/')
        self.bot_prefix = os.getenv('BOT_PREFIX', '!')
        
        # Validate configuration
        if not self.bot_token:
            raise ValueError("❌ DISCORD_BOT_TOKEN not found! Please check your .env file")
        if not self.django_api_url:
            raise ValueError("❌ DJANGO_API_URL not found! Please check your .env file")
        
        print(f"🌐 Django API URL: {self.django_api_url}")
        print(f"🤖 Bot prefix: {self.bot_prefix}")
        
        # Storage for user sessions (in production, use Redis or database)
        # Format: {discord_user_id: {'access_token': 'token', 'username': 'user', ...}}
        self.user_sessions = {}
        
        # Storage for alert channels (where to send notifications)
        # Format: {discord_user_id: channel_id}
        self.alert_channels = {}
        
        # Set up Discord bot with required intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read message content
        
        # Create bot instance
        self.bot = commands.Bot(
            command_prefix=self.bot_prefix,
            intents=intents,
            help_command=None  # We'll create our own help command
        )
        
        # Initialize bot events and commands
        self.setup_events()
        self.setup_commands()
    
    def setup_events(self):
        """
        Set up Discord bot events (triggered automatically by Discord)
        """
        
        @self.bot.event
        async def on_ready():
            """
            Called when bot successfully connects to Discord
            """
            print(f"🚀 Bot is ready!")
            print(f"🤖 Logged in as: {self.bot.user}")
            print(f"📊 Connected to {len(self.bot.guilds)} Discord servers")
            print(f"🔗 API Endpoint: {self.django_api_url}")
            
            # Set bot's "activity status" (what users see under the bot's name)
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"stock alerts 📈 | {self.bot_prefix}help"
            )
            await self.bot.change_presence(activity=activity)
            
            # Start background monitoring task
            if not self.monitor_triggered_alerts.is_running():
                self.monitor_triggered_alerts.start()
                print("✅ Background alert monitoring started")
        
        @self.bot.event
        async def on_command_error(ctx, error):
            """
            Handle command errors gracefully
            """
            if isinstance(error, commands.CommandNotFound):
                await ctx.send(f"❌ Command not found. Use `{self.bot_prefix}help` to see available commands.")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Missing required arguments. Use `{self.bot_prefix}help` for command usage.")
            else:
                logger.error(f"Command error: {error}")
                await ctx.send("❌ An error occurred while processing your command.")
    
    def setup_commands(self):
        """
        Set up all Discord commands that users can use
        """
        
        
        #register
        @self.bot.command(name='register', aliases=['signup'])
        async def register_command(ctx, username: str = None, password: str = None, email: str = None):
            """
            Register a new account for stock alerts
            """

            if not username or not password or not email:
                embed = discord.Embed(
                    title="🔐 Register for Stock Alerts",
                    description=f"**Usage:** `{self.bot_prefix}register <username> <password> <email>`\n\n"
                                "This creates a new account in the AWS stock alerts system.\n"
                                "⚠️ Your registration message will be deleted for security.",
                    color=0x3498db
                )
                await ctx.send(embed=embed)
                return

            # Delete the command message for security (contains password)
            try:
                await ctx.message.delete()
                print(f"🗑️ Deleted registration message from {ctx.author}")
            except discord.errors.NotFound:
                pass  # Message already deleted
            except discord.errors.Forbidden:
                await ctx.send("⚠️ Cannot delete your message. Please delete it manually for security.")

            # Show loading message
            loading_msg = await ctx.send("🔄 Registering your account...")
            try:
                # Make API call to your Django registration endpoint
                register_url = f"{self.django_api_url}/api/auth/register/"
                print(f"🌐 Attempting registration at: {register_url}")

                response = requests.post(
                    register_url,
                    json={"username": username, "password": password, "email": email},
                    headers={"Content-Type": "application/json"},
                    timeout=15  # 15 second timeout
                )

                print(f"📡 Registration response status: {response.status_code}")

                if response.status_code == 201:
                    # Successful registration
                    await ctx.send("✅ Registration successful! You can now log in.")
                else:
                    await ctx.send("❌ Registration failed. Please try again.")

            except Exception as e:
                print(f"⚠️ Error during registration: {e}")
                await ctx.send("❌ An error occurred while registering your account.")

        @self.bot.command(name='login', aliases=['connect'])
        async def login_command(ctx, username: str = None, password: str = None):
            """
            Login to your stock alerts account
            Usage: !login <username> <password>
            """
            
            # Validate command arguments
            if not username or not password:
                embed = discord.Embed(
                    title="🔐 Login to Stock Alerts",
                    description=f"**Usage:** `{self.bot_prefix}login <username> <password>`\n\n"
                               "This connects your Discord account to your AWS stock alerts system.\n"
                               "⚠️ Your login message will be deleted for security.",
                    color=0x3498db
                )
                await ctx.send(embed=embed)
                return
            
            # Delete the command message for security (contains password)
            try:
                await ctx.message.delete()
                print(f"🗑️ Deleted login message from {ctx.author}")
            except discord.errors.NotFound:
                print("❌ Message already deleted or doesn't exist.")
            except discord.errors.Forbidden:
                print("🚫 Bot lacks permission to delete this message.")
                await ctx.send("⚠️ Cannot delete your message. Please delete it manually for security.")
            except Exception as e:
                print(f"⚠️ Unexpected error deleting message: {e}")
                await ctx.send("⚠️ An unexpected error occurred. Please try again later.")
            # Show loading message
            loading_msg = await ctx.send("🔄 Connecting to your stock alerts system...")
            
            try:
                # Make API call to your Django login endpoint
                login_url = f"{self.django_api_url}/api/auth/login/"
                print(f"🌐 Attempting login to: {login_url}")
                
                response = requests.post(
                    login_url,
                    json={"username": username, "password": password},
                    headers={"Content-Type": "application/json"},
                    timeout=15  # 15 second timeout
                )
                
                print(f"📡 Login response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Successful login
                    data = response.json()
                    access_token = data.get('access')
                    
                    if access_token:
                        # Store user session
                        user_id = ctx.author.id
                        self.user_sessions[user_id] = {
                            'access_token': access_token,
                            'username': username,
                            'connected_at': datetime.now(),
                            'refresh_token': data.get('refresh'),
                            'last_alert_check': datetime.now()
                        }
                        
                        # Set current channel as alert notification channel
                        self.alert_channels[user_id] = ctx.channel.id
                        
                        print(f"✅ User {ctx.author} logged in successfully as {username}")
                        
                        # Try to get user's alert summary
                        alert_summary = ""
                        try:
                            summary_response = requests.get(
                                f"{self.django_api_url}/api/alerts/summary/",
                                headers={'Authorization': f"Bearer {access_token}"},
                                timeout=10
                            )
                            if summary_response.status_code == 200:
                                summary = summary_response.json()
                                alert_summary = (
                                    f"\n📊 **Your Alert Summary:**\n"
                                    f"• Active alerts: {summary.get('active_count', 0)}\n"
                                    f"• Triggered alerts: {summary.get('triggered_count', 0)}"
                                )
                        except Exception as e:
                            print(f"⚠️ Could not fetch alert summary: {e}")
                        
                        # Create success embed
                    embed = discord.Embed(
                        title="✅ Successfully Connected!",
                        description=f"Welcome **{username}**! Your Discord account is now connected to your stock alerts system.",
                        color=0x00ff00
                    )
                    
                    # Safely display channel info
                    if hasattr(ctx.channel, "mention"):
                        channel_display = ctx.channel.mention
                    else:
                        channel_display = "Direct Messages"
                    
                    embed.add_field(
                        name="🔔 Alert Notifications",
                        value=f"Will be sent to {channel_display}",
                        inline=False
                    )
                    embed.add_field(
                        name="🚀 Next Steps",
                        value=f"• Use `{self.bot_prefix}alerts` to view your alerts\n"
                              f"• Use `{self.bot_prefix}stocks` to see current prices\n"
                              f"• Use `{self.bot_prefix}help` for all commands",
                        inline=False
                    )
                    if alert_summary:
                        embed.add_field(
                            name="📈 Current Status",
                            value=alert_summary,
                            inline=False
                        )
                    
                        
                        # Update loading message with success
                        await loading_msg.edit(content="", embed=embed)
                        
                    else:
                        raise Exception("No access token received from API")
                
                else:
                    # Login failed
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', f'Login failed (HTTP {response.status_code})')
                    except:
                        error_msg = f'Login failed (HTTP {response.status_code})'
                    
                    print(f"❌ Login failed: {error_msg}")
                    
                    embed = discord.Embed(
                        title="❌ Login Failed",
                        description=f"**Error:** {error_msg}\n\n"
                                   "Please check:\n"
                                   "• Username and password are correct\n"
                                   "• Your AWS Django system is running\n"
                                   f"• API endpoint is accessible: `{self.django_api_url}`",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)
            
            except requests.exceptions.Timeout:
                print("⏰ Request timeout")
                embed = discord.Embed(
                    title="⏰ Connection Timeout",
                    description="The connection to your stock alerts API timed out.\n\n"
                               "This might mean:\n"
                               "• Your AWS server is slow to respond\n"
                               "• Network connectivity issues\n"
                               "• Your Django app is not running",
                    color=0xff9500
                )
                await loading_msg.edit(content="", embed=embed)
            
            except requests.exceptions.ConnectionError:
                print(f"🌐 Connection error to {self.django_api_url}")
                embed = discord.Embed(
                    title="🌐 Connection Error", 
                    description=f"Cannot connect to your stock alerts API.\n\n"
                               f"**API URL:** `{self.django_api_url}`\n\n"
                               "Please check:\n"
                               "• Your AWS Django system is running\n"
                               "• The API URL in .env is correct\n"
                               "• Your server allows external connections",
                    color=0xff0000
                )
                await loading_msg.edit(content="", embed=embed)
            
            except Exception as e:
                print(f"❌ Unexpected error during login: {e}")
                embed = discord.Embed(
                    title="❌ Unexpected Error",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=0xff0000
                )
                await loading_msg.edit(content="", embed=embed)
        
        @self.bot.command(name='alerts')
        async def alerts_command(ctx, filter_type: str = "all"):
            """
            Show your stock alerts
            Usage: !alerts [all|active|triggered]
            """
            
            # Check if user is logged in
            user_id = ctx.author.id
            if user_id not in self.user_sessions:
                embed = discord.Embed(
                    title="🔒 Not Connected",
                    description=f"Please login first: `{self.bot_prefix}login <username> <password>`",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            session = self.user_sessions[user_id]
            loading_msg = await ctx.send("🔄 Fetching your alerts...")
            
            try:
                # Determine API endpoint based on filter
                if filter_type.lower() == "triggered":
                    endpoint = "/api/alerts/triggered/"
                    title = "🚨 Your Triggered Alerts"
                    empty_message = "No triggered alerts found"
                    color = 0xff0000
                elif filter_type.lower() == "active":
                    endpoint = "/api/alerts/"
                    title = "🟢 Your Active Alerts"
                    empty_message = "No active alerts found"
                    color = 0x00ff00
                else:
                    endpoint = "/api/alerts/"
                    title = "📈 All Your Stock Alerts"
                    empty_message = "No alerts found"
                    color = 0x3498db
                
                # Make API request
                response = requests.get(
                    f"{self.django_api_url}{endpoint}",
                    headers={'Authorization': f"Bearer {session['access_token']}"},
                    timeout=15
                )
                
                print(f"📡 Alerts response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle both paginated and non-paginated responses
                    alerts = data.get('results', data) if isinstance(data, dict) else data
                    
                    if not alerts or len(alerts) == 0:
                        embed = discord.Embed(
                            title=title,
                            description=empty_message,
                            color=0xffff00
                        )
                        embed.add_field(
                            name="💡 Tip",
                            value=f"Use `{self.bot_prefix}stocks` to see current stock prices",
                            inline=False
                        )
                        await loading_msg.edit(content="", embed=embed)
                        return
                    
                    # Filter active alerts if needed
                    if filter_type.lower() == "active":
                        alerts = [alert for alert in alerts if alert.get('is_active', True)]
                    
                    # Create rich embed with alerts
                    embed = discord.Embed(
                        title=title,
                        description=f"Found **{len(alerts)}** alerts for **{session['username']}**",
                        color=color,
                        timestamp=datetime.now()
                    )
                    
                    # Add up to 10 alerts (Discord embed field limit)
                    alerts_shown = 0
                    for alert in alerts[:10]:
                        # Get alert details
                        stock_symbol = alert.get('stock_symbol', alert.get('stock', 'Unknown'))
                        is_active = alert.get('is_active', True)
                        status_emoji = "🟢" if is_active else "🔴"
                        
                        # Create field name and value
                        field_name = f"{status_emoji} {stock_symbol}"
                        
                        field_lines = []
                        field_lines.append(f"**Type:** {alert.get('alert_type', 'N/A')}")
                        field_lines.append(f"**Condition:** {alert.get('condition', 'N/A')} ${alert.get('threshold_price', 'N/A')}")
                        
                        if alert.get('duration_minutes'):
                            field_lines.append(f"**Duration:** {alert['duration_minutes']} minutes")
                        
                        # Add dates
                        if alert.get('created_at'):
                            try:
                                created = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00'))
                                field_lines.append(f"**Created:** {created.strftime('%m/%d/%Y')}")
                            except:
                                pass
                        
                        if alert.get('triggered_at'):
                            try:
                                triggered = datetime.fromisoformat(alert['triggered_at'].replace('Z', '+00:00'))
                                field_lines.append(f"**Triggered:** {triggered.strftime('%m/%d %H:%M')}")
                            except:
                                pass
                        
                        # Add field to embed
                        embed.add_field(
                            name=field_name,
                            value="\n".join(field_lines),
                            inline=True  # Display in columns
                        )
                        alerts_shown += 1
                    
                    # Add footer if there are more alerts
                    if len(alerts) > 10:
                        embed.set_footer(text=f"Showing first 10 of {len(alerts)} alerts")
                    else:
                        embed.set_footer(text=f"Total: {len(alerts)} alerts")
                    
                    await loading_msg.edit(content="", embed=embed)
                
                elif response.status_code == 401:
                    # Token expired - remove session
                    print(f"🔑 Token expired for user {ctx.author}")
                    del self.user_sessions[user_id]
                    if user_id in self.alert_channels:
                        del self.alert_channels[user_id]
                    
                    embed = discord.Embed(
                        title="🔒 Session Expired",
                        description="Your login session has expired.\n\n"
                                   f"Please login again: `{self.bot_prefix}login <username> <password>`",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)
                
                else:
                    # Other API error
                    embed = discord.Embed(
                        title="❌ API Error",
                        description=f"Failed to fetch alerts (HTTP {response.status_code})",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)
            
            except Exception as e:
                print(f"❌ Error fetching alerts: {e}")
                embed = discord.Embed(
                    title="❌ Connection Error",
                    description="Could not connect to the stock alerts API",
                    color=0xff0000
                )
                await loading_msg.edit(content="", embed=embed)
                
        @self.bot.command(name='alert', aliases=['createalert', 'setalert'])
        async def create_alert_command(ctx, stock_id: int, condition: str, price: float, duration: int = None, alert_type: str = "THRESHOLD"):
                """
                Create a stock price alert
                Usage: !alert <stock_id> <condition> <price> [duration_minutes]

                Examples:
                !alert 1 > 150.50
                !alert 2 < 50.00 60
                !alert 3 >= 100.25 1440

                Conditions: >, <, >=, <=, ==
                Duration: minutes (optional, defaults to very long time)
                """

                # Validate condition
                valid_conditions = ['>', '<', '>=', '<=', '==']
                if condition not in valid_conditions:
                    embed = discord.Embed(
                        title="❌ Invalid Condition",
                        description=f"Condition must be one of: {', '.join(valid_conditions)}",
                        color=0xff0000
                    )
                    await ctx.send(embed=embed)
                    return

                
                # Validate duration
                # if duration not none
                if duration is not None:
                    if duration <= 0:
                        embed = discord.Embed(
                            title="❌ Invalid Duration",
                            description="Duration must be a positive number of minutes",
                            color=0xff0000
                        )
                    await ctx.send(embed=embed)
                    return


                loading_msg = await ctx.send("🔔 Creating stock alert...")
                user_id = ctx.author.id
                if user_id not in self.user_sessions:
                     embed = discord.Embed(
                         title="🔒 Not Connected",
                         description=f"Please login first: `{self.bot_prefix}login <username> <password>`",
                         color=0xff0000
                     )
                     await ctx.send(embed=embed)
                     return

                session = self.user_sessions[user_id]

                try:
                    # Prepare alert data
                    alert_data = {
                        "stock": stock_id,
                        "alert_type": alert_type,
                        "condition": condition,
                        "threshold_price": str(price),  # Convert to string as in your example
                        "is_active": True
                    }

                    if duration is not None:
                        alert_data["duration_minutes"] = duration

                    # Send POST request to create alert
                    response = requests.post(
                        f"{self.django_api_url}/api/alerts/",
                        json=alert_data,
                        headers={'Content-Type': 'application/json',
                                 'Authorization': f"Bearer {session['access_token']}"},
                        timeout=15
                    )

                    print(f"🔔 Alert creation response status: {response.status_code}")
                    print(f"🔔 Alert data sent: {alert_data}")

                    if response.status_code in [200, 201]:
                        # Alert created successfully
                        response_data = response.json()

                        embed = discord.Embed(
                            title="✅ Alert Created Successfully",
                            color=0x00ff00
                        )

                        embed.add_field(
                            name="📊 Stock ID",
                            value=str(stock_id),
                            inline=True
                        )

                        embed.add_field(
                            name="📈 Condition",
                            value=f"Price {condition} ${price:.2f}",
                            inline=True
                        )

                        embed.add_field(
                            name="⏰ Duration",
                            value=f"{duration:,} minutes" if duration is not None and duration < 9223372036854776000 else "Indefinite",
                            inline=True
                        )

                        # Add alert ID if returned
                        if 'id' in response_data:
                            embed.add_field(
                                name="🆔 Alert ID",
                                value=str(response_data['id']),
                                inline=True
                            )

                        embed.add_field(
                            name="🟢 Status",
                            value="Active",
                            inline=True
                        )

                        embed.set_footer(text="Alert will notify when condition is met")
                        await loading_msg.edit(content="", embed=embed)

                    elif response.status_code == 400:
                        # Bad request - validation error
                        try:
                            error_data = response.json()
                            error_msg = "Invalid data provided"
                            if isinstance(error_data, dict):
                                # Try to extract meaningful error messages
                                errors = []
                                for field, messages in error_data.items():
                                    if isinstance(messages, list):
                                        errors.extend([f"{field}: {msg}" for msg in messages])
                                    else:
                                        errors.append(f"{field}: {messages}")
                                if errors:
                                    error_msg = "\n".join(errors[:3])  # Limit to first 3 errors
                        except:
                            error_msg = "Invalid data format"

                        embed = discord.Embed(
                            title="❌ Validation Error",
                            description=f"```{error_msg}```",
                            color=0xff0000
                        )
                        await loading_msg.edit(content="", embed=embed)

                    elif response.status_code == 404:
                        embed = discord.Embed(
                            title="❌ Stock Not Found",
                            description=f"Stock with ID {stock_id} does not exist",
                            color=0xff0000
                        )
                        await loading_msg.edit(content="", embed=embed)

                    else:
                        embed = discord.Embed(
                            title="❌ Server Error",
                            description=f"Failed to create alert (HTTP {response.status_code})",
                            color=0xff0000
                        )
                        await loading_msg.edit(content="", embed=embed)

                except requests.exceptions.Timeout:
                    print("❌ Request timeout while creating alert")
                    embed = discord.Embed(
                        title="❌ Timeout Error",
                        description="Request timed out while creating alert",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)

                except requests.exceptions.RequestException as e:
                    print(f"❌ Request error while creating alert: {e}")
                    embed = discord.Embed(
                        title="❌ Connection Error",
                        description="Could not connect to the alert API",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)

                except ValueError as e:
                    print(f"❌ Value error: {e}")
                    embed = discord.Embed(
                        title="❌ Input Error",
                        description="Invalid input values provided",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)

                except Exception as e:
                    print(f"❌ Unexpected error while creating alert: {e}")
                    embed = discord.Embed(
                        title="❌ Unexpected Error",
                        description="An unexpected error occurred while creating the alert",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)


        @self.bot.command(name='alerthelp', aliases=['alertinfo'])
        async def alert_help_command(ctx):
                """
                Show help information for the alert command
                """
                embed = discord.Embed(
                    title="🔔 Stock Alert Help",
                    description="Learn how to create stock price alerts",
                    color=0x0099ff
                )

                embed.add_field(
                    name="📝 Basic Usage",
                    value="`!alert <stock_id> <condition> <price> [duration]`",
                    inline=False
                )

                embed.add_field(
                    name="🔢 Parameters",
                    value="""
                    **stock_id**: ID of the stock to monitor
                    **condition**: >, <, >=, <=, ==
                    **price**: Target price (decimal)
                    **duration**: Minutes (optional)
                    """,
                    inline=False
                )

                embed.add_field(
                    name="💡 Examples",
                    value="""
                    `!alert 1 > 150.50` - Alert when stock 1 goes above $150.50
                    `!alert 2 < 50.00 60` - Alert when stock 2 goes below $50 (1 hour)
                    `!alert 3 >= 100.25 1440` - Alert when stock 3 reaches $100.25+ (24 hours)
                    """,
                    inline=False
                )

                embed.add_field(
                    name="⏰ Duration",
                    value="If not specified, alert will remain active indefinitely",
                    inline=False
                )

                await ctx.send(embed=embed)        
                
         
         
                
        @self.bot.command(name='stocks', aliases=['prices'])
        async def stocks_command(ctx):
            """
            Show current stock prices from your system
            Usage: !stocks
            """

            loading_msg = await ctx.send("📊 Fetching current stock prices...")

            try:
                response = requests.get(
                    f"{self.django_api_url}/api/stocks/",
                    timeout=15
                )

                print(f"📡 Stocks response status: {response.status_code}")

                if response.status_code == 200:
                    stocks_data = response.json()

                    # If API returns a dict with a key holding the list
                    if isinstance(stocks_data, dict):
                        if "results" in stocks_data and isinstance(stocks_data["results"], list):
                            stocks = stocks_data["results"]
                        elif "stocks" in stocks_data:
                            stocks = stocks_data["stocks"]
                        elif "data" in stocks_data:
                            stocks = stocks_data["data"]
                        else:
                            # Convert dict values to list, but filter for dict items only
                            stocks = [v for v in stocks_data.values() if isinstance(v, dict)]
                            if not stocks:
                                stocks = []
                    else:
                        stocks = stocks_data if isinstance(stocks_data, list) else []

                    if not stocks:
                        embed = discord.Embed(
                            title="📊 Stock Prices",
                            description="No stock data available",
                            color=0xffff00
                        )
                        await loading_msg.edit(content="", embed=embed)
                        return

                    # Create embed BEFORE the loop
                    embed = discord.Embed(
                        title="📊 Current Stock Prices",
                        color=0x00ff00
                    )

                    # Slice safely and add fields
                    display_stocks = stocks[:15]  # Limit to first 15 stocks

                    for stock in display_stocks:
                        # Ensure stock is a dict
                        if not isinstance(stock, dict):
                            continue

                        symbol = stock.get('symbol', 'Unknown')
                        current_price = stock.get('current_price', 'N/A')

                        # Format price
                        if current_price != 'N/A' and current_price is not None:
                            try:
                                price_float = float(current_price)
                                price_display = f"${price_float:.2f}"
                            except (ValueError, TypeError):
                                price_display = f"${current_price}"
                        else:
                            price_display = "N/A"

                        # Get last updated time
                        last_updated = stock.get('last_updated', 'N/A')
                        if last_updated != 'N/A' and last_updated is not None:
                            try:
                                # Handle different datetime formats
                                if isinstance(last_updated, str):
                                    # Remove timezone info if present and parse
                                    clean_time = last_updated.replace('Z', '+00:00')
                                    updated_time = datetime.fromisoformat(clean_time)
                                    time_display = updated_time.strftime('%H:%M')
                                else:
                                    time_display = "Unknown"
                            except (ValueError, AttributeError):
                                time_display = "Unknown"
                        else:
                            time_display = "Unknown"

                        # Add field to embed
                        embed.add_field(
                            name=f"📈 {symbol}",
                            value=f"**{price_display}**\n*Updated: {time_display}*",
                            inline=True
                        )

                    # Add footer
                    if len(stocks) > 15:
                        embed.set_footer(text=f"Showing first 15 of {len(stocks)} stocks")
                    else:
                        embed.set_footer(text=f"Showing {len(stocks)} stocks • Data from API")

                    await loading_msg.edit(content="", embed=embed)

                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description=f"Failed to fetch stock data (HTTP {response.status_code})",
                        color=0xff0000
                    )
                    await loading_msg.edit(content="", embed=embed)

            except requests.exceptions.Timeout:
                print("❌ Request timeout")
                embed = discord.Embed(
                    title="❌ Timeout Error",
                    description="Request timed out while fetching stock data",
                    color=0xff0000
                )
                await loading_msg.edit(content="", embed=embed)

            except requests.exceptions.RequestException as e:
                print(f"❌ Request error: {e}")
                embed = discord.Embed(
                    title="❌ Connection Error",
                    description="Could not connect to the stock data API",
                    color=0xff0000
                )
                await loading_msg.edit(content="", embed=embed)

            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                embed = discord.Embed(
                    title="❌ Unexpected Error",
                    description="An unexpected error occurred while processing stock data",
                    color=0xff0000
                )
                await loading_msg.edit(content="", embed=embed)
        
        
        @self.bot.command(name='status')
        async def status_command(ctx):
            """
            Show connection status and system info
            Usage: !status
            """
            
            user_id = ctx.author.id
            embed = discord.Embed(
                title="🔍 System Status",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            # Connection status
            if user_id in self.user_sessions:
                session = self.user_sessions[user_id]
                connected_time = session['connected_at'].strftime('%Y-%m-%d %H:%M UTC')
                
                embed.add_field(
                    name="🟢 Connection Status",
                    value=f"**Connected as:** {session['username']}\n"
                          f"**Since:** {connected_time}",
                    inline=False
                )
                
                # Test API connection
                try:
                    test_response = requests.get(
                        f"{self.django_api_url}/api/alerts/summary/",
                        headers={'Authorization': f"Bearer {session['access_token']}"},
                        timeout=10
                    )
                    
                    if test_response.status_code == 200:
                        summary = test_response.json()
                        embed.add_field(
                            name="📊 Alert Summary",
                            value=f"**Active:** {summary.get('active_count', 0)}\n"
                                  f"**Triggered:** {summary.get('triggered_count', 0)}",
                            inline=True
                        )
                        api_status = "✅ Connected"
                        api_color = 0x00ff00
                    else:
                        api_status = f"⚠️ HTTP {test_response.status_code}"
                        api_color = 0xff9500
                
                except Exception as e:
                    api_status = "❌ Connection Failed"
                    api_color = 0xff0000
                
                embed.add_field(
                    name="🌐 API Status",
                    value=api_status,
                    inline=True
                )
                
            else:
                embed.add_field(
                    name="🔒 Connection Status",
                    value=f"**Not connected**\n"
                          f"Use `{self.bot_prefix}login <username> <password>` to connect",
                    inline=False
                )
                api_color = 0xff0000
            
            # System information
            embed.add_field(
                name="🏠 API Endpoint",
                value=f"`{self.django_api_url}`",
                inline=False
            )
            
            # Alert channel
            alert_channel_id = self.alert_channels.get(user_id, ctx.channel.id)
            embed.add_field(
                name="🔔 Alert Channel",
                value=f"<#{alert_channel_id}>",
                inline=True
            )
            
            # Bot information
            embed.add_field(
                name="🤖 Bot Info",
                value=f"**Servers:** {len(self.bot.guilds)}\n"
                      f"**Prefix:** {self.bot_prefix}",
                inline=True
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='logout', aliases=['disconnect'])
        async def logout_command(ctx):
            """
            Disconnect from your stock alerts account
            Usage: !logout
            """
            
            user_id = ctx.author.id
            
            if user_id in self.user_sessions:
                username = self.user_sessions[user_id]['username']
                
                # Remove session and alert channel
                del self.user_sessions[user_id]
                if user_id in self.alert_channels:
                    del self.alert_channels[user_id]
                
                print(f"👋 User {ctx.author} logged out ({username})")
                
                embed = discord.Embed(
                    title="👋 Disconnected",
                    description=f"**{username}** has been disconnected successfully.\n\n"
                               "You will no longer receive alert notifications.",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="ℹ️ Not Connected",
                    description="You are not currently connected to any account.",
                    color=0xffff00
                )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='start')
        async def start_command(ctx):
            """
            Show all available commands
            Usage: !start
            """
            
            embed = discord.Embed(
                title="🤖 Stock Alerts Bot - Help",
                description="Connect to your AWS-deployed Django stock alerts system\n"
                           f"**Command Prefix:** `{self.bot_prefix}`",
                color=0x3498db
            )
            
            # Authentication commands
            embed.add_field(
                name="🔐 Authentication",
                value=f"`{self.bot_prefix}register <user> <pass>` - Register a new account\n"
                      f"`{self.bot_prefix}login <user> <pass>` - Connect to your account\n"
                      f"`{self.bot_prefix}logout` - Disconnect from account\n"
                      f"`{self.bot_prefix}status` - Check connection status",
                inline=False
            )
            
            # Alert commands
            embed.add_field(
                name="📈 Stock Alerts",
                value=f"`{self.bot_prefix}alert <stock_id> <condition> <price> [duration]` - Create a stock alert\n"
                      f"`{self.bot_prefix}alerthelp` - See how to use the create alert command\n"
                      f"`{self.bot_prefix}alerts` - Show all your alerts\n"
                      f"`{self.bot_prefix}alerts active` - Show only active alerts\n"
                      f"`{self.bot_prefix}alerts triggered` - Show triggered alerts",
                inline=False
            )
            
            # Stock data commands
            embed.add_field(
                name="📊 Stock Data",
                value=f"`{self.bot_prefix}stocks` - Show current stock prices\n"
                      f"`{self.bot_prefix}refresh` - Manually refresh stock prices",
                inline=False
            )
            
            # Bot information
            embed.add_field(
                name="ℹ️ Information",
                value=f"`{self.bot_prefix}start` - Show this help message\n"
                      f"`{self.bot_prefix}ping` - Check bot response time",
                inline=False
            )
            
            # Add setup instructions
            embed.add_field(
                name="🚀 Getting Started",
                value=f"1. Use `{self.bot_prefix}login <username> <password>`\n"
                      f"2. Check your alerts with `{self.bot_prefix}alerts`\n"
                      f"3. Monitor stock prices with `{self.bot_prefix}stocks`\n"
                      f"4. The bot will notify you of triggered alerts automatically!",
                inline=False
            )
            
            embed.set_footer(
                text=f"API: {self.django_api_url}",
                icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
            )
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='refresh')
        async def refresh_command(ctx):
            """
            Manually refresh stock prices (if user is logged in)
            Usage: !refresh
            """
            
            user_id = ctx.author.id
            if user_id not in self.user_sessions:
                embed = discord.Embed(
                    title="🔒 Not Connected",
                    description=f"Please login first: `{self.bot_prefix}login <username> <password>`",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            session = self.user_sessions[user_id]
            loading_msg = await ctx.send("🔄 Refreshing stock prices...")
            
            try:
                # Call the refresh endpoint from your Django API
                response = requests.post(
                    f"{self.django_api_url}/api/stocks/actions/refresh-prices/",
                    headers={'Authorization': f"Bearer {session['access_token']}"},
                    timeout=30  # Longer timeout for refresh operation
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embed = discord.Embed(
                        title="✅ Refresh Complete",
                        description="Stock prices have been refreshed successfully!",
                        color=0x00ff00
                    )
                    
                    # Add refresh details if available
                    if isinstance(data, dict):
                        if 'refreshed_count' in data:
                            embed.add_field(
                                name="📊 Updated",
                                value=f"{data['refreshed_count']} stocks refreshed",
                                inline=True
                            )
                        if 'message' in data:
                            embed.add_field(
                                name="ℹ️ Details",
                                value=data['message'],
                                inline=False
                            )
                    
                    embed.set_footer(text=f"Use {self.bot_prefix}stocks to see updated prices")
                    
                elif response.status_code == 401:
                    # Token expired
                    del self.user_sessions[user_id]
                    embed = discord.Embed(
                        title="🔒 Session Expired",
                        description="Please login again",
                        color=0xff0000
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Refresh Failed",
                        description=f"HTTP {response.status_code}: Could not refresh prices",
                        color=0xff0000
                    )
                
                await loading_msg.edit(content="", embed=embed)
                
            except Exception as e:
                print(f"❌ Error refreshing prices: {e}")
                embed = discord.Embed(
                    title="❌ Refresh Error",
                    description="Could not refresh stock prices",
                    color=0xff0000
                )
                await loading_msg.edit(content="", embed=embed)
        
        @self.bot.command(name='ping')
        async def ping_command(ctx):
            """
            Check bot response time and API connectivity
            Usage: !ping
            """
            
            start_time = datetime.now()
            
            # Send initial message
            message = await ctx.send("🏓 Pinging...")
            
            # Calculate Discord API latency
            end_time = datetime.now()
            discord_latency = (end_time - start_time).total_seconds() * 1000
            
            # Test Django API connectivity
            api_latency = "N/A"
            api_status = "❌ Failed"
            
            try:
                api_start = datetime.now()
                response = requests.get(f"{self.django_api_url}/api/stocks/", timeout=10)
                api_end = datetime.now()
                
                if response.status_code == 200:
                    api_latency = f"{(api_end - api_start).total_seconds() * 1000:.0f}ms"
                    api_status = "✅ Connected"
                else:
                    api_status = f"⚠️ HTTP {response.status_code}"
                    
            except Exception as e:
                api_status = "❌ Connection Failed"
            
            embed = discord.Embed(
                title="🏓 Pong!",
                color=0x00ff00 if api_status.startswith("✅") else 0xff9500
            )
            
            embed.add_field(
                name="🤖 Discord Bot",
                value=f"**Latency:** {discord_latency:.0f}ms\n**Status:** ✅ Online",
                inline=True
            )
            
            embed.add_field(
                name="🌐 Django API",
                value=f"**Latency:** {api_latency}\n**Status:** {api_status}",
                inline=True
            )
            
            embed.set_footer(text=f"Bot uptime: {str(datetime.now() - start_time).split('.')[0]}")
            
            await message.edit(content="", embed=embed)
    
    @tasks.loop(minutes=2)  # Check every 2 minutes
    async def monitor_triggered_alerts(self):
        """
        Background task that monitors for triggered alerts and sends notifications
        This runs automatically every 2 minutes
        """
        
        # Skip if no users are logged in
        if not self.user_sessions:
            return
        
        print(f"🔍 Monitoring triggered alerts for {len(self.user_sessions)} users...")
        
        # Check each logged-in user
        for user_id, session in list(self.user_sessions.items()):
            try:
                # Get triggered alerts for this user
                response = requests.get(
                    f"{self.django_api_url}/api/alerts/triggered/",
                    headers={'Authorization': f"Bearer {session['access_token']}"},
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    alerts = data.get('results', data) if isinstance(data, dict) else data
                    
                    # If there are triggered alerts, send notification
                    if alerts and len(alerts) > 0:
                        user = self.bot.get_user(user_id)
                        channel_id = self.alert_channels.get(user_id)
                        
                        if user and channel_id:
                            channel = self.bot.get_channel(channel_id)
                            if channel:
                                # Check if we should send notification (avoid spam)
                                last_check = session.get('last_alert_check', datetime.now() - timedelta(hours=1))
                                time_since_last = datetime.now() - last_check
                                
                                # Only send notification if it's been at least 5 minutes since last one
                                if time_since_last.total_seconds() >= 300:  # 5 minutes
                                    await self.send_triggered_alert_notification(
                                        channel, user, alerts, session['username']
                                    )
                                    # Update last check time
                                    session['last_alert_check'] = datetime.now()
                
                elif response.status_code == 401:
                    # Token expired - remove session
                    print(f"🔑 Token expired for user ID {user_id}")
                    del self.user_sessions[user_id]
                    if user_id in self.alert_channels:
                        del self.alert_channels[user_id]
                    
                    # Optionally notify user their session expired
                    try:
                        user = self.bot.get_user(user_id)
                        if user:
                            embed = discord.Embed(
                                title="🔒 Session Expired",
                                description="Your login session has expired. Please login again to continue receiving alerts.",
                                color=0xff9500
                            )
                            await user.send(embed=embed)
                    except:
                        pass  # User might have DMs disabled
                
            except Exception as e:
                print(f"❌ Error monitoring alerts for user {user_id}: {e}")
    
    async def send_triggered_alert_notification(self, channel, user, alerts, username):
        """
        Send a notification message when alerts are triggered
        """
        
        try:
            # Create notification embed
            embed = discord.Embed(
                title="🚨 STOCK ALERT TRIGGERED!",
                description=f"**{len(alerts)}** alert(s) triggered for **{username}**",
                color=0xff0000,
                timestamp=datetime.now()
            )
            
            # Add individual alert details (limit to 5 to avoid embed size limits)
            alerts_to_show = alerts[:5]
            
            for alert in alerts_to_show:
                stock_symbol = alert.get('stock_symbol', alert.get('stock', 'Unknown'))
                condition = alert.get('condition', 'N/A')
                threshold_price = alert.get('threshold_price', 'N/A')
                alert_type = alert.get('alert_type', 'N/A')
                
                field_value_lines = [f"**{condition} ${threshold_price}**"]
                
                if alert_type != 'N/A':
                    field_value_lines.append(f"Type: {alert_type}")
                
                if alert.get('duration_minutes'):
                    field_value_lines.append(f"Duration: {alert['duration_minutes']} min")
                
                if alert.get('triggered_at'):
                    try:
                        triggered_time = datetime.fromisoformat(alert['triggered_at'].replace('Z', '+00:00'))
                        field_value_lines.append(f"Triggered: {triggered_time.strftime('%H:%M')}")
                    except:
                        pass
                
                embed.add_field(
                    name=f"🔴 {stock_symbol}",
                    value="\n".join(field_value_lines),
                    inline=True
                )
            
            # Add footer with instructions
            if len(alerts) > 5:
                embed.set_footer(
                    text=f"Showing 5 of {len(alerts)} alerts. Use {self.bot_prefix}alerts triggered to see all."
                )
            else:
                embed.set_footer(
                    text=f"Use {self.bot_prefix}alerts triggered to manage your alerts."
                )
            
            # Send notification with user mention
            await channel.send(f"{user.mention} 📢", embed=embed)
            
            print(f"✅ Sent alert notification to {user} in {channel}")
            
        except discord.Forbidden:
            print(f"❌ Cannot send message to channel {channel.id} - no permissions")
        except discord.HTTPException as e:
            print(f"❌ Discord API error sending notification: {e}")
        except Exception as e:
            print(f"❌ Unexpected error sending notification: {e}")
    
    def run(self):
        """
        Start the Discord bot
        """
        
        # Validate configuration before starting
        if not self.bot_token:
            raise ValueError(
                "❌ DISCORD_BOT_TOKEN not found!\n"
                "Please add your Discord bot token to the .env file:\n"
                "DISCORD_BOT_TOKEN=your_token_here"
            )
        
        if not self.django_api_url:
            raise ValueError(
                "❌ DJANGO_API_URL not found!\n"
                "Please add your AWS Django API URL to the .env file:\n"
                "DJANGO_API_URL=https://your-aws-domain.com"
            )
        
        print("🚀 Starting Stock Alerts Discord Bot...")
        print(f"🌐 API Endpoint: {self.django_api_url}")
        print(f"🎯 Command Prefix: {self.bot_prefix}")
        print("📝 Make sure your .env file is configured correctly!")
        print("🔗 Invite the bot to your Discord server and start using it!")
        print("-" * 60)
        
        try:
            # Run the bot (this blocks until the bot shuts down)
            self.bot.run(self.bot_token)
        except discord.LoginFailure:
            print("❌ Failed to login to Discord! Check your bot token.")
        except Exception as e:
            print(f"❌ Bot error: {e}")

# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 STOCK ALERTS DISCORD BOT")
    print("=" * 60)
    
    try:
        # Create and run the bot
        bot = StockAlertsBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start bot: {e}")
        print("\n🔧 Please check:")
        print("1. Your .env file exists and contains:")
        print("   - DISCORD_BOT_TOKEN=your_bot_token")
        print("   - DJANGO_API_URL=your_aws_url")
        print("2. Your Discord bot token is correct")
        print("3. Your AWS Django system is running and accessible")
        print("4. All required packages are installed (discord.py, requests, python-dotenv)")
        input("\nPress Enter to exit...")