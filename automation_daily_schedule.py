# Standard library imports for system, I/O, time, and asynchronous operations
import os
import io
import time
import asyncio
from datetime import datetime, timedelta

# Third-party library imports
from dotenv import load_dotenv
from prefect import flow, task

# Google API imports for authentication and service building
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Telegram bot imports for messaging and error handling
from telegram import Bot 
from telegram.error import TelegramError, NetworkError

# Load environment variables from a .env file into the system
load_dotenv()

# Retrieve Telegram credentials from the environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


@task(name="Get Today Schedules From Calendar", retries=3, retry_delay_seconds=5)
def get_all_schedules(date) -> str:
    """
    Task to retrieve all scheduled events and holidays within a specific date.
    The 'date' input MUST be strictly in 'YYYY-MM-DD' format.
    """
    try:
        # Authenticate with Google Calendar API using stored credentials
        creds = Credentials.from_authorized_user_file("token.json", ['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)
        
        # Format the time boundaries (Appending +07:00 for WIB/Jakarta Timezone)
        timeMin = f"{date}T00:00:00+07:00"
        timeMax = f"{date}T23:59:59+07:00"

        # Define the list of target calendars (Primary user calendar & Indonesian Holidays)
        target_calendars = ['primary', 'id.indonesian#holiday@group.v.calendar.google.com']
        all_events = []

        # Iterate through each calendar and aggregate the matching events
        for calendar_id in target_calendars:
            try: 
                result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=timeMin,
                    timeMax=timeMax,
                    maxResults=50,      # Limit to accommodate daily events
                    singleEvents=True,  # Expand recurring events into single instances
                    orderBy='startTime'
                ).execute()
                all_events.extend(result.get("items", []))
            except:
                # Silently skip if a specific calendar is inaccessible or fails
                continue

        # Handle the edge case where no events are found in the given timeframe
        if not all_events:
            return f"No events scheduled for {date}."

        # Format the aggregated events into a clean, readable string for both UI and AI context
        response = f"Schedule for {date}:\n"
        
        for e in all_events:
            title = e.get('summary', 'Untitled Event')
            
            # Extract raw date/time strings from the API payload
            start_raw = e['start'].get('dateTime', e['start'].get('date'))
            end_raw = e['end'].get('dateTime', e['end'].get('date'))

            # Extract just the YYYY-MM-DD portion for clear visual grouping
            event_date = start_raw[:10]

            # Determine if the event is time-bound or an all-day occurrence
            if "T" in start_raw:
                start_time = start_raw[11:16] # Extract HH:MM
                end_time = end_raw[11:16]
                time_str = f"{start_time} - {end_time}"
            else:
                time_str = "All-day"

            # Append the formatted event entry
            response += f"- [{event_date}] {title} ({time_str})\n"
            
        return response

    except Exception as e:
        # Secure Error Logging
        # Convert the raw exception to a lowercase string for safe keyword matching.
        # This prevents sensitive token or Google API URLs from leaking in the logs.
        error_str = str(e).lower()
        error_msg = ""
        
        # Safe Error Categorization
        if "credentials" in error_str or "token" in error_str or "json" in error_str:
            error_msg = "Authentication Error: Failed to load Google Calendar credentials securely."
        elif "quota" in error_str or "ratelimit" in error_str:
            error_msg = "API Quota Error: Google Calendar API rate limit exceeded."
        elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
            error_msg = "Network Error: Failed to connect to Google Calendar API."
        else:
            error_msg = "Unexpected Error: An unknown issue occurred while fetching schedules."
            
        # Log the safe message and raise the exception for Prefect
        print(f"Calendar Task Failed: {error_msg}")
        raise Exception(error_msg)
            
@task(name="To Telegram", retries=3, retry_delay_seconds=5)
def to_telegram(msg: str):
    """
    Task to send the generated message to a specific Telegram Chat.
    """
    
    # 1. Credential Validation
    # Ensure that the necessary Telegram API credentials exist before proceeding.
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Telegram credentials are missing.")
        raise ValueError("Missing Telegram Credentials")

    # 2. Asynchronous Sending Function
    # Define the async function to send the message using python-telegram-bot.
    async def send_via_ptb():
        bot = Bot(token=TELEGRAM_TOKEN)
        print("🚀 Sending message via Python-Telegram-Bot...")

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode="Markdown"
        )

    # 3. Execution and Error Handling
    # Run the asynchronous function and catch any potential errors.
    try:
        asyncio.run(send_via_ptb())
        print("✅ Success: Message sent to Telegram (via PTB)!")

    except Exception as e:
        # 4. Secure Error Handling
        # Convert exception to string for safe analysis.
        # This prevents sensitive data like tokens from leaking into the logs.
        error_str = str(e).lower()
        safe_msg = ""

        # 5. Error Categorization
        # Identify the type of error to provide a clear, safe log message.
        if "connection" in error_str or "dns" in error_str:
            safe_msg = "❌ Network Error: Failed to connect to Telegram API."
        elif "timeout" in error_str:
            safe_msg = "⏳ Timeout Error: Telegram API did not respond."
        elif "ssl" in error_str:
            safe_msg = "🔒 SSL Error: Certificate verification failed."
        else:
            safe_msg = "❌ Telegram Send Failed: Unknown error occurred."
            
        # Log the sanitized message to the console
        print(safe_msg)
        
        # 6. Trigger Failure
        # Raise the exception so Prefect marks the task as failed and triggers the retry mechanism.
        raise Exception(safe_msg)

@flow(name="Get Today's Schedules", log_prints=True)
def main_flow():
    """
    The main Prefect flow that orchestrates the fetching of today's schedule 
    and sending it to Telegram.
    """
    
    # 1. Get the Current Date
    # Fetch today's date and format it as 'YYYY-MM-DD' to match the calendar task requirements.
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # 2. Retrieve Schedules
        # Call the task to get all events and holidays for today.
        today_schedules = get_all_schedules(current_date)
        
        # 3. Send Notification
        # If schedules are successfully retrieved (not None or empty), send them via Telegram.
        if today_schedules:
            to_telegram(today_schedules)
            
    except Exception as e:
        # 4. Secure Error Logging
        # Convert the raw exception to a lowercase string for safe keyword matching.
        error_str = str(e).lower()
        error_msg = ""
        
        # 5. Safe Error Categorization
        # Provide generic, safe messages based on the type of error detected.
        if "credentials" in error_str or "token" in error_str or "auth" in error_str:
            error_msg = "Authentication Error: Failed to verify API credentials securely."
        elif "calendar" in error_str:
            error_msg = "Calendar Error: An issue occurred while fetching Google Calendar events."
        elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
            error_msg = "Network Error: Connection issues detected during flow execution."
        else:
            error_msg = "Unexpected Error: The flow failed due to an unknown issue."
            
        # 6. Log and Raise
        # Print the safe message to the console, then raise it to trigger Prefect's failure state.
        print(f"Failed to load today's schedule: {error_msg}")
        raise Exception(error_msg)

if __name__ == "__main__":
    # ==========================================
    # 🚀 EXECUTION MODE
    # ==========================================

    # --- OPTION 1: FOR GITHUB ACTIONS (ACTIVE) ---
    # This calls the function immediately (Run Once).
    # GitHub's YAML scheduler handles the timing (CRON).
    # When finished, the script exits to save server resources.
    main_flow()

    # --- OPTION 2: FOR LOCAL SERVER / VPS (COMMENTED OUT) ---
    # Use this if you run the script on your own laptop or a 24/7 server.
    # The '.serve()' method keeps the script running indefinitely 
    # and handles the scheduling internally.
    
    # main_flow.serve(
    #     name="deployment-mentor-pagi",
    #     # cron="0 7 * * *", # Run daily at 07:00 AM (server time)
    #     interval=10,        # Or run every 10 seconds (for testing)
    #     tags=["ai", "daily"]
    # )