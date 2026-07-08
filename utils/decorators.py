from datetime import datetime
from functools import wraps


def time_measure(inner_function):
    @wraps(inner_function)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        print(f'\nНачался тест: {inner_function.__name__}')
        inner_function(*args, **kwargs)
        end_time = datetime.now()
        print(f'\nТест {inner_function.__name__} закончился')
        print(f'\nВремя прогона теста {end_time - start_time}')
    return wrapper