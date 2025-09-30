CMD ["python", "app.py"]
    chown -R botuser:botuser /app
USER botuser

# Start the bot directly
CMD ["python", "bot.py"]

