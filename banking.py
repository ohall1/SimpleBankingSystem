# Write your code here
import random
import sqlite3


class BankAccount:
    def __init__(self, *args, **kwargs):
        if args:
            self.account_number = args[0][1]
            self.pin = args[0][2]
            self.balance = args[0][3]
        elif kwargs:
            print(kwargs)
        else:
            temp_account = "400000" + "{:09d}".format(random.randint(0, 999999999))
            all_n = 0.0
            for i in range(len(temp_account)):
                if (i + 1) % 2 == 1:
                    temp = int(temp_account[i])*2
                else:
                    temp = int(temp_account[i])
                if temp > 9:
                    temp -= 9
                all_n += temp
            check_sum = 10 - (all_n % 10)
            if check_sum == 10:
                check_sum -= 10

            self.account_number = temp_account + "{:01d}".format(int(check_sum))
            self.pin = "{:04d}".format(random.randint(0, 9999))
            self.balance = 0

    def get_account_number(self):
        return self.account_number

    def get_pin(self):
        return self.pin

    def get_balance(self):
        return self.balance

    def add_income(self, income):
        self.balance += income

    def transfer_out(self, amount):
        if amount > self.balance:
            return False
        else:
            self.balance -= amount
            return True


def luhn_algorithm(card_number):
    all_n = 0
    for i in range(len(card_number)):
        if (i + 1) % 2 == 1:
            temp = int(card_number[i]) * 2
        else:
            temp = int(card_number[i])
        if temp > 9:
            temp -= 9
        all_n += temp
    if all_n % 10 == 0:
        return True
    else:
        return False


random.seed()
accounts = dict()

conn = sqlite3.connect('card.s3db')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS card(
    id INTEGER,
    number TEXT,
    pin TEXT,
    balance INTEGER DEFAULT 0)''')
conn.commit()


running = True
while running:
    print("1. Create an account")
    print("2. Log into account")
    print("0. Exit")
    user_input = int(input())
    if user_input == 1:
        unique_account = False
        while not unique_account:
            account = BankAccount()
            cur.execute('''
            SELECT EXISTS(
                SELECT * FROM card
                WHERE
                number = {account_n}
                )'''.format(account_n=account.get_account_number()))
            status = cur.fetchone()[0]
            if not status:
                accounts[account.get_account_number()] = account
                print("Your card has been created")
                print("Your card number:")
                print(account.get_account_number())
                print("Your card PIN:")
                print(account.get_pin())
                unique_account = True
                cur.execute('''
                SELECT MAX(id) FROM card''')
                entries = cur.fetchone()[0]
                if not entries:
                    print(entries)
                    entries = 0
                cur.execute('''
                INSERT INTO card
                (id, number, pin, balance)
                VALUES
                ({0},{1},{2},{3});
                '''.format(entries+1, account.get_account_number(), account.get_pin(), 0))
                conn.commit()
    elif user_input == 2:
        print("Enter your card number:")
        user_account_n = input()
        print("Enter your PIN:")
        user_pin = input()
        #  Search thorough the database for the account
        cur.execute('''
        SELECT id, number, pin, balance
        FROM card
        WHERE
        number='{account_in}' AND
        pin='{pin_in}' '''.format(account_in=user_account_n, pin_in=user_pin))
        account_out = cur.fetchone()
        if not account_out:
            print("Wrong card number or pin")
        else:
            account = BankAccount(account_out)
            print("You have logged in successfully")
            logged_in = True
            while logged_in:
                print("1. Balance")
                print("2. Add income")
                print("3. Do transfer")
                print("4. Close account")
                print("5. Log out")
                print("0. Exit")
                user_input = int(input())
                if user_input == 1:
                    print(account.get_balance())
                elif user_input == 2:
                    print("Enter income:")
                    user_input = int(input())
                    account.add_income(user_input)
                    cur.execute('''UPDATE card
                    SET
                    balance={new_balance}
                    WHERE
                    number='{account_in}'
                    AND pin='{pin_in}'
                    '''.format(account_in=account.get_account_number(), new_balance=int(account.get_balance()),
                               pin_in=account.get_pin()))
                    conn.commit()
                    print("Income added")
                elif user_input == 3:
                    print("Transfer")
                    print("Enter card number")
                    account_in = input()
                    if luhn_algorithm(account_in):
                        if account_in == account.get_account_number():
                            print("You can't transfer money to the same account!")
                        else:
                            cur.execute('''
                            SELECT EXISTS(
                            SELECT * FROM
                            card
                            WHERE
                            number = {transfer_account}
                            )'''.format(transfer_account=account_in))
                            status = cur.fetchone()[0]
                            if status:
                                print("Enter how much money you want to transfer:")
                                transfer_amount = int(input())
                                if account.transfer_out(transfer_amount):
                                    cur.execute('''
                                    SELECT balance FROM card
                                    WHERE
                                    number = {transfer_account}'''.format(transfer_account=account_in))
                                    temp_balance = cur.fetchone()[0]
                                    temp_balance += transfer_amount
                                    cur.execute('''
                                    UPDATE card
                                    SET balance = {new_balance}
                                    WHERE
                                    number = {transfer_account}'''.format(new_balance=temp_balance,
                                                                          transfer_account=account_in))
                                    conn.commit()
                                    cur.execute('''UPDATE card
                                    SET
                                    balance={new_balance}
                                    WHERE
                                    number='{account_in}'
                                    AND pin='{pin_in}'
                                    '''.format(account_in=account.get_account_number(),
                                               new_balance=int(account.get_balance()),
                                               pin_in=account.get_pin()))
                                    conn.commit()
                                    print("Success!")
                                else:
                                    print("Not enough money!")
                            else:
                                print("Such a card does not exist")
                    else:
                        print("Probably you made a mistake in the card number. Please try again!")
                elif user_input == 4:
                    cur.execute('''
                    DELETE FROM card
                    WHERE
                    number = {delete_account}'''.format(delete_account=account.get_account_number()))
                    print("The account has been closed.")
                    conn.commit()
                    logged_in = False
                elif user_input == 5:
                    logged_in = False
                elif user_input == 0:
                    logged_in = False
                    running = False
    elif user_input == 0:
        running = False
print("Bye!")
conn.close()
