import time


def log_info(message):
    print(f"[INFO - {__get_current_time()}] {message}")


def log_warning(message):
    print(f"[WARNING - {__get_current_time()}] {message}")


def log_error(message):
    print(f"[ERROR - {__get_current_time()}] {message}")


def __get_current_time():
    # Get current time in format Hours:Minutes:Seconds:Millisecond
    # Example: 14:23:05:023
    millis = int(round(time.time() * 1000))
    return time.strftime("%H:%M:%S:", time.localtime()) + f"{millis % 1000:03d}"
