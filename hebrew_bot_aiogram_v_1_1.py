'''В этой версии вместо запросов по API добавлена собственная база данных, 
включающая текстовые, аудиозадания и задания-картинки, плюс добавлен английский язык,
плюс включен логгинг - сохранение логов в отдельный файл'''

import aiogram
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
#from aiogram.utils.markdown import text, bold, italic, code, pre
#from aiogram.types import ParseMode
#import requests
import sqlite3
import random
import logging
from aiogram.types import InputFile
from config import TOKEN

bot = Bot(token=TOKEN)

from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log', # указываем имя файла для записи логов
    filemode='a' # режим записи логов: 'a' - добавлять новые записи в конец файла
)

multilang = {'info_ru': 'Выберите уровень. Позже вы сможете его изменить, набрав команду /level',
              'info_uk':'Оберіть рівень. Пізніше ви зможете змінити свій вибір, набравши команду /level',
              'info_en':'Choose a level. Later on you can change it by typing /level',
              'eval_poz_ru': 'Таки да! Можете попробовать ещё другой вопрос, и тоже бесплатно.',
              'eval_neg_ru': 'Не угадали. Попробуйте другую опцию выше, или закажите другой вопрос ниже.',
              'eval_poz_uk': 'Саме так! Можете спробувати наступне питання, й теж безкоштовно!',
              'eval_neg_uk': 'Не вгадали. Спробуйте іншу відповідь вище, або запросіть інше питання нижче',
              'eval_poz_en':'Right! You can try another question, if you wish',
              'eval_neg_en':'Not exactly. Try another answer above, or order one more question below',
              'final_ru':'Одно удовольствие работать с Вами. Заходите еще! \nДля начала работы нажмите /start',
              'final_uk':'Приємно було з вами працювати. Заходьте ще! \nДля початку роботи натисніть /start',
              'final_en':'It was a pleasure working with you. Come back again! \nTo start a session press /start',
              'more_ru':'Еще, пожалуйста', 'more_uk':'Ще, будь ласка', 'more_en':'One more, please',
              'enough_ru':'Пока хватит', 'enough_uk':'Поки доста', 'enough_en':'Enough for now',
              'type_ru':'Хотите вопрос в форме текста, аудио или картинки?',
              'type_uk':'Хочете запитання у формі тексту, аудіо чи зображення?',
              'type_en':'Do you want the question in text, audio or picture form?',
              'only_but_ru':'Извините, я общаюсь только через меню. Выберите опцию выше или нажмите /start',
              'only_but_uk':'Вибачте, я спілкуюсь тільки через меню. Оберіть опцію вище або наберіть /start',
              'only_but_en':'Excuse me, I can communicate only by menus. Please choose an option above or press /start',
              'assess_ru':'Соотношение правильных ответов к общему числу ответов в этой сессии: ',
              'assess_uk':'Співвідношення правильних відповідей к загальному числу відповідей в цьому сеансі: ',
              'assess_en':'Ratio of correct answers to the total number of answers in this session: '}
# language keyboard
btn1 = types.InlineKeyboardButton('Українська', callback_data='uk')
btn2 = types.InlineKeyboardButton('English', callback_data='en')
btn3 = types.InlineKeyboardButton('Русский', callback_data='ru')
lang_kb = types.InlineKeyboardMarkup().add(btn1, btn2, btn3)

# level keyboard
btn1 = types.InlineKeyboardButton('А1', callback_data='A1')
btn2 = types.InlineKeyboardButton('A2', callback_data='A2')
level_kb = types.InlineKeyboardMarkup().add(btn1, btn2)

# type of question keyboard
btn1 = types.InlineKeyboardButton('Text', callback_data='text')
btn2 = types.InlineKeyboardButton('Audio', callback_data='audio')
btn3 = types.InlineKeyboardButton('Image', callback_data='picture')
type_kb = types.InlineKeyboardMarkup().add(btn1, btn2, btn3)

# определяем функцию для сохранения предпочитаемого языка пользователя
async def save_user_language(user: types.User, language: str):
    data = await dp.storage.get_data(user=user)
    data['language'] = language
    await storage.set_data(user=user, data=data)

# определяем функцию для извлечения предпочитаемого языка пользователя из хранилища
async def get_user_language(user: types.User):
    data = await storage.get_data(user=user)
    language = data.get('language')
    return language

#  функция для сохранения уровня пользователя
async def save_user_level(user: types.User, level: str):
    data = await dp.storage.get_data(user=user)
    data['level'] = level
    await storage.set_data(user=user, data=data)

# функция для извлечения уровня пользователя из хранилища
async def get_user_level(user: types.User):
    data = await storage.get_data(user=user)
    level = data.get('level')
    return level

# определяем функцию для сохранения правильного ответа квиза
async def save_quiz_answer(user: types.User, answer: str):
    data = await dp.storage.get_data(user=user)
    data['answer'] = answer
    await storage.set_data(user=user, data=data)

# определяем функцию для извлечения правильного ответа из хранилища
async def get_quiz_answer(user: types.User):
    data = await storage.get_data(user=user)
    answer = data.get('answer')
    return answer

# функция для сохранения количества right  / wrong ответов
async def save_num_answers(user: types.User, number: int, mode=str):
    data = await dp.storage.get_data(user=user)
    data[mode] = number
    await storage.set_data(user=user, data=data)

# функция для получения количества right  / wrong ответов
async def get_num_answers(user: types.User, mode=str):
    data = await storage.get_data(user=user)
    number = data.get(mode)
    return number   

# Функция для извлечения строки из базы по id
async def get_row_by_id(table_name, id):
    conn = sqlite3.connect('hebrewbot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM {} WHERE id={}".format(table_name, id))  
    row = cursor.fetchone()
    conn.close()
    return row

@dp.message_handler(commands=['help'])
async def process_start_command(message: types.Message):
    txt='I can offer you the Hebrew quiz questions for levels A1 and A2 in the form of text, pictures or audio, and assess your answers.'
    await bot.send_message(message.from_user.id, txt)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    logging.info(f"User {message.from_user.username} started using the bot")
    await bot.send_message(message.from_user.id, "Оберіть мову / Choose your language /Выберите язык", reply_markup=lang_kb)

@dp.message_handler(commands=['level'])
async def process_start_command(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if lang == None:
        lang = 'en'
    key = 'info_'+lang
    txt=multilang[key]
    await bot.send_message(message.from_user.id, txt, reply_markup=level_kb)

@dp.callback_query_handler(lambda callback_query: callback_query.data in ['uk', 'ru', 'en'])
async def lang_choice(callback_query: types.CallbackQuery):
    await save_user_language(callback_query.from_user.id, callback_query.data)
    key = 'info_'+callback_query.data
    txt=multilang[key]
    await bot.send_message(callback_query.from_user.id, txt, reply_markup=level_kb)

# Тут впишем функцию, к-ая сохранит уровень и перебросит на клаву с выбором текст / аудио
@dp.callback_query_handler(lambda callback_query: callback_query.data in ['A1', 'A2'])
async def level_choice(callback_query: types.CallbackQuery):
    await save_user_level(callback_query.from_user.id, callback_query.data)
    lang = await get_user_language(callback_query.from_user.id)
    await save_user_level(callback_query.from_user.id, callback_query.data)
    key = 'type_'+lang
    txt=multilang[key]
    await bot.send_message(callback_query.from_user.id, txt, reply_markup=type_kb)

@dp.callback_query_handler(lambda callback_query: callback_query.data in ['text', 'audio', 'picture'])
async def type_choice(callback_query: types.CallbackQuery):
    if callback_query.data == 'text':
        level = await get_user_level(callback_query.from_user.id)
        if level == 'A1':
            num = random.randint(1, 30)
        elif level == 'A2':
            num = random.randint(31, 60)
        else:
            num = random.randint(1, 60)
        table_name='questions'
        row=await get_row_by_id(table_name, num)
        quest = row[1]
        choices=row[2].split('|')
        corr=row[3]
        var1=choices[0]
        var2=choices[1]
        var3=choices[2]
        var4=choices[3]

        await save_quiz_answer(callback_query.from_user.id, corr)

        quiz_markup = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton(var1, callback_data=var1)
        item2 = types.InlineKeyboardButton(var2, callback_data=var2)
        item3 = types.InlineKeyboardButton(var3, callback_data=var3)
        item4 = types.InlineKeyboardButton(var4, callback_data=var4)

        quiz_markup.add(item1, item2, item3, item4)
        await bot.send_message(callback_query.from_user.id, quest, reply_markup=quiz_markup)

    elif callback_query.data == 'audio':
        level = await get_user_level(callback_query.from_user.id)
        if level == 'A1':
            num = random.randint(1, 12)
        elif level == 'A2':
            num = random.randint(1, 12)
        else:
            num = random.randint(1, 12)
        table_name='audio_sent'
        row=await get_row_by_id(table_name, num)
        audio_file = InputFile(row[5])
        quest = row[1]
        choices=row[2].split('|')
        corr=row[3]
        await save_quiz_answer(callback_query.from_user.id, corr)
        # choices keyboard
        btn1 = types.InlineKeyboardButton(choices[0], callback_data=choices[0])
        btn2 = types.InlineKeyboardButton(choices[1], callback_data=choices[1])
        btn3 = types.InlineKeyboardButton(choices[2], callback_data=choices[2])
        btn4 = types.InlineKeyboardButton(choices[3], callback_data=choices[3])
        quiz_markup = types.InlineKeyboardMarkup().add(btn1, btn2, btn3, btn4)
        
        await bot.send_audio(callback_query.from_user.id, audio_file)
        await bot.send_message(callback_query.from_user.id, quest, reply_markup=quiz_markup)

    elif callback_query.data == 'picture':
        level = await get_user_level(callback_query.from_user.id)
        if level == 'A1':
            num = random.randint(1, 10)
        elif level == 'A2':
            num = random.randint(11, 20)
        else:
            num = random.randint(1, 20)
        table_name='pictures'
        row=await get_row_by_id(table_name, num)
        image_file = InputFile(row[5])
        quest = row[1]
        choices=row[2].split('|')
        corr=row[3]
        await save_quiz_answer(callback_query.from_user.id, corr)
        # choices keyboard
        btn1 = types.InlineKeyboardButton(choices[0], callback_data=choices[0])
        btn2 = types.InlineKeyboardButton(choices[1], callback_data=choices[1])
        btn3 = types.InlineKeyboardButton(choices[2], callback_data=choices[2])
        btn4 = types.InlineKeyboardButton(choices[3], callback_data=choices[3])
        quiz_markup = types.InlineKeyboardMarkup().add(btn1, btn2, btn3, btn4)
        
        await bot.send_photo(callback_query.from_user.id, image_file)
        await bot.send_message(callback_query.from_user.id, quest, reply_markup=quiz_markup)

# Обработчик, отвечающий на вопрос, давать ли еще вопрос (из функции, расположенной ниже)
@dp.callback_query_handler(lambda callback_query: callback_query.data in ['yes', 'no'])
async def loop(callback_query: types.CallbackQuery):
    lang = await get_user_language(callback_query.from_user.id)
    if callback_query.data == 'yes':
        key = 'type_'+lang
        txt=multilang[key]
        await bot.send_message(callback_query.from_user.id, txt, reply_markup=type_kb) # type_kb
    elif callback_query.data == 'no':
        # Выставление финальной оценки, текст-прощание и обнуление счетчиков правильных и непр. ответов
        num_right = await get_num_answers(callback_query.from_user.id, 'right')
        if num_right == None:
            num_right = 0
        num_wrong = await get_num_answers(callback_query.from_user.id, 'wrong')
        if num_wrong == None:
            num_wrong = 0
        
        key='final_'+lang
        key2='assess_'+lang
        txt1 = multilang[key] # текст-прощание
        txt2 = multilang[key2]
        txt3='{}/{}'.format(num_right, num_right+num_wrong)
        txt=f'{txt2}{txt3}\n{txt1}'
        await bot.send_message(callback_query.from_user.id, txt)
        await save_num_answers(callback_query.from_user.id, 0, 'right')
        await save_num_answers(callback_query.from_user.id, 0, 'wrong')

@dp.callback_query_handler(lambda callback_query: True)
async def level_choice(callback_query: types.CallbackQuery):
    corr_answ = await get_quiz_answer(callback_query.from_user.id)
    lang = await get_user_language(callback_query.from_user.id)
    if callback_query.data == corr_answ:
        # Увеличиваем на 1 количество правильных ответов
        mode = 'right'
        num = await get_num_answers(callback_query.from_user.id, mode)
        if num == None:
            num=0
        num_new=num+1
        await save_num_answers(callback_query.from_user.id, num_new, mode)

        key = 'eval_poz_'+lang
        txt=multilang[key]
    else:
        # Увеличиваем на 1 количество неправильных ответов
        mode = 'wrong'
        num = await get_num_answers(callback_query.from_user.id, mode)
        if num == None:
            num=0
        num_new=num+1
        await save_num_answers(callback_query.from_user.id, num_new, mode)

        key = 'eval_neg_'+lang
        txt=multilang[key]
    await bot.send_message(callback_query.from_user.id, txt)
    
    # finish choice keyboard. Она тут, а не отдельно, т.к. текст кнопок - разный в зависимости от языка
    key1='more_'+lang
    key2='enough_'+lang
    button1=multilang[key1]
    button2=multilang[key2]
    btn1 = types.InlineKeyboardButton(button1, callback_data='yes')
    btn2 = types.InlineKeyboardButton(button2, callback_data='no')
    finish_kb = types.InlineKeyboardMarkup().add(btn1, btn2)
    txt1 = 'So?'
    await bot.send_message(callback_query.from_user.id, txt1, reply_markup=finish_kb)

@dp.message_handler()
async def handle_all_messages(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if lang == None:
        txt = 'Press /start'
    else:
        key = 'only_but_'+lang
        txt=multilang[key]
    await bot.send_message(message.from_user.id, txt)

if __name__ == '__main__':
    executor.start_polling(dp, timeout=2)
