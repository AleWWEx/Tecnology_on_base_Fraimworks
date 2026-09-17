import random
import datetime

event_name = "Дебаты: Искусственный интеллект и этика"
min_age_limit = 16
max_capacity = 25
current_participants = 24

print("Система регистрации дискуссионного клуба")
print(f"Мероприятие: {event_name}")
print(f"Минимальный возраст: {min_age_limit}+")

user_name = input("Введите ваше имя:")

age_input = input("Введите ваш возраст")
user_age = int(age_input)

print("\nОбработка заявки")

if user_age < min_age_limit:
    print(f"Отказ в регистрации: {user_name}, мероприятие доступно только с {min_age_limit} лет.")
else:
    if current_participants < max_capacity:
        
        current_participants = current_participants + 1
        free_spots = max_capacity - current_participants
        
        ticket_id = random.randint(1000, 9999)
        current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        
        print("Регистрация успешно завершена!")
        print(f"Участник: {user_name}")
        print(f"Ваш уникальный ID билета: #{ticket_id}")
        print(f"Время регистрации: {current_time}")
        print(f"Свободных мест осталось: {free_spots}")
        
    else:
        print(f"Отказ в регистрации: {user_name}, к сожалению, все места на это мероприятие уже заняты.")