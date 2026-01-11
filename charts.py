 # charts.py

def bar_chart(value, max_value, length=20):
    if max_value == 0:
        return "░" * length
    filled = int((value / max_value) * length)
    return "▓" * filled + "░" * (length - filled)