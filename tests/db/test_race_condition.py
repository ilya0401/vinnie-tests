import threading
import time

import allure
import pytest

from utils.db import get_connection


@pytest.fixture
def race_account():
    conn = get_connection()
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS race_accounts (
                id SERIAL PRIMARY KEY,
                balance INTEGER NOT NULL
            )
        """)
        cur.execute("TRUNCATE race_accounts RESTART IDENTITY")
        cur.execute("INSERT INTO race_accounts (balance) VALUES (100) RETURNING id")
        account_id = cur.fetchone()[0]

    yield account_id

    with conn.cursor() as cur:
        cur.execute("DROP TABLE race_accounts")
    conn.close()


def _withdraw_unsafe(account_id: int, amount: int) -> None:
    conn = get_connection()
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT balance FROM race_accounts WHERE id = %s", (account_id,))
        current_balance = cur.fetchone()[0]        # 1. читаем

        time.sleep(0.05)                            # искусственно расширяем окно гонки

        new_balance = current_balance - amount      # 2. считаем в памяти потока
        cur.execute(
            "UPDATE race_accounts SET balance = %s WHERE id = %s",
            (new_balance, account_id),
        )                                            # 3. пишем поверх чужих изменений
    conn.close()


@pytest.mark.db
@allure.title("Race condition: параллельные списания без блокировки теряют часть операций")
def test_race_condition_lost_update(race_account):
    account_id = race_account
    threads_count = 5
    amount = 10

    with allure.step(f"Запустить {threads_count} параллельных списаний по {amount} с одного счёта (balance=100)"):
        threads = [
            threading.Thread(target=_withdraw_unsafe, args=(account_id, amount))
            for _ in range(threads_count)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT balance FROM race_accounts WHERE id = %s", (account_id,))
        final_balance = cur.fetchone()[0]
    conn.close()

    expected_if_sequential = 100 - threads_count * amount  # 50, если бы списания шли по очереди

    with allure.step(
        f"Итоговый balance={final_balance}, при последовательном выполнении был бы {expected_if_sequential}"
    ):
        assert final_balance != expected_if_sequential, (
            "Race condition не проявилась: все потоки почему-то отработали "
            "так, будто выполнялись строго последовательно"
        )
