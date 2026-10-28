import allure
import pytest
from utils.vinny_API import VinnyApi

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@pytest.mark.process
class TestProcess:

    @allure.title("[4.1.] Загрузка файла размером ≥10МБ в /process возвращает статус error")
    def test_upload_file_over_size_limit_returns_error(self, vinny_api: VinnyApi, api_error_handler):
        # Ровно на границе: main.py читает file.read(10*1024*1024) и сравнивает len(...) >= тому же
        # значению — проверка срабатывает до STT, поэтому содержимое файла не обязано быть валидным аудио.
        oversized_payload = b"\x00" * MAX_FILE_SIZE_BYTES
        with api_error_handler():
            with allure.step(f"Загрузить в /process файл размером {MAX_FILE_SIZE_BYTES} байт (граница лимита)"):
                result = vinny_api.process_audio(file_bytes=oversized_payload, filename="oversized.wav")
        with allure.step(f"Проверить что status == error, получено: '{result.status}'"):
            assert result.status == "error"
        with allure.step(f"Проверить текст ошибки про превышение размера, получено: '{result.voice_message}'"):
            assert "10" in result.voice_message
