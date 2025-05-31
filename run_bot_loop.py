# run_bot_loop.py
import subprocess
import time

while True:
    print("Starting bot...")
    process = subprocess.Popen(["python", "BotCEM.py"])
    process.wait()
    print("Bot stopped. Restarting in 5 seconds...")
    time.sleep(5)
