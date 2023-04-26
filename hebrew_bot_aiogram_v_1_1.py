'''В этой версии вместо запросов по API добавлена собственная база данных, 
включающая текстовые, аудиозадания и задания-картинки, плюс добавлен английский язык,
плюс включен логгинг - сохранение логов в отдельный файл'''

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
              'eval_neg_ru': 'Не угадали. Попробуйте еще раз с этим, или закажите другой вопрос получшее.',
              'eval_poz_uk': 'Саме так! Можете спробувати наступне питання, й теж майже безкоштовно!',
              'eval_neg_uk': 'Не вгадали. Спробуйте ще раз, або запросіть інше питання',
              'eval_poz_en':'Right! You can try another question, if you wish',
              'eval_neg_en':'Not exactly. Try again with this question, or order another one',
              'final_ru':'Правильно, а то от работы кони дохнут. Заходите еще!',
              'final_uk':'Приємно було з вами працювати. Заходьте ще!',
              'final_en':'It was a pleasure working with you. Come back again!',
              'more_ru':'Еще, пожалуйста', 'more_uk':'Ще, будь ласка', 'more_en':'One more, please',
              'enough_ru':'Пока хватит', 'enough_uk':'Поки доста', 'enough_en':'Enough for now',
              'type_ru':'Хотите вопрос в форме текста, аудио или картинки?',
              'type_uk':'Хочете запитання у формі тексту, аудіо чи зображення?',
              'type_en':'Do you want the question in text, audio or picture form?'}

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

# Функция для извлечения строки из базы по id
async def get_row_by_id(table_name, id):
    conn = sqlite3.connect('hebrewbot.db')
    cursor = conn.cursor()
    #query = "SELECT * FROM questions WHERE id = ?"
    cursor.execute("SELECT * FROM {} WHERE id={}".format(table_name, id))  
    row = cursor.fetchone()
    conn.close()
    return row

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    logging.info(f"Пользователь {message.from_user.username} запустил бот")
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
            num = random.randint(1, 3)
        elif level == 'A2':
            num = random.randint(1, 3)
        else:
            num = random.randint(1, 3)
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
            num = random.randint(1, 6)
        elif level == 'A2':
            num = random.randint(1, 6)
        else:
            num = random.randint(1, 6)
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
        key='final_'+lang
        txt = multilang[key]
        await bot.send_message(callback_query.from_user.id, txt)

@dp.callback_query_handler(lambda callback_query: True)
async def level_choice(callback_query: types.CallbackQuery):
    corr_answ = await get_quiz_answer(callback_query.from_user.id)
    lang = await get_user_language(callback_query.from_user.id)
    if callback_query.data == corr_answ:
        key = 'eval_poz_'+lang
        txt=multilang[key]
    else:
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
    txt1 = 'Таки шо? / So what?'
    await bot.send_message(callback_query.from_user.id, txt1, reply_markup=finish_kb)

@dp.message_handler()
async def handle_all_messages(message: types.Message):
    txt = 'Press /start'
    await bot.send_message(message.from_user.id, txt)

if __name__ == '__main__':
    executor.start_polling(dp)
