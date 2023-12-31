from meow.utils.context import get_record_handler, get_openai_handler, get_baidu_handler
import logging
from meow.utils.context import baidu_lock, openai_lock, audio_lock, msg_lock, set_msg
from meow.utils.meowinit import generate_handler
import time

from meow.utils.thread import rsgister_chat_thread

def create_chat():
    rsgister_chat_thread(chat_loop)

def chat_loop():
    try:
        generate_handler()
    except Exception as e:
        logging.error(e)
        return
    record_handler = get_record_handler() # 语音读取
    openai_handler = get_openai_handler() # OpenAi读取
    baidu_handler = get_baidu_handler()
    baidu_recognition_failed_times = 0
    baidu_tts_failed_times = 0
    openai_failed_times = 0
    while True:
        logging.debug('***START_LOOP***')
        # 秘钥或网络错误
        if(baidu_recognition_failed_times > 10 or baidu_tts_failed_times > 10 or openai_failed_times > 10):
            raise('ERROR GET MAX FAILD, CHECK NETWORK OR KEY')
            
        logging.info('爱丽丝正在聆听...')
        code = 1
        audio_lock.acquire()
        code, audio_detect_file = record_handler.detect_audio()
        audio_lock.release()
        while code == 1:
            time.sleep(1)
            with audio_lock:
                code, audio_detect_file = record_handler.detect_audio()
        
        logging.info('爱丽丝正在理解...')
        # 识别
        baidu_lock.acquire()
        code, result_text = baidu_handler.recog(audio_detect_file)
        baidu_lock.release()
        
        
        
        msg_lock.acquire()
        set_msg('你说:{}'.format(result_text))
        msg_lock.release()
        
        logging.info('你说:{}'.format(result_text))
        

        if not code == 0:
            logging.warning('recognition ERROR, TRY RESTART times{}'.format(baidu_recognition_failed_times))
            baidu_recognition_failed_times += 1
            continue
        else:
            baidu_recognition_failed_times = 0
        
        # OPENAI
        openai_lock.acquire()
        code, openai_output = openai_handler.chat(result_text)
        openai_lock.release()
        
        msg_lock.acquire()
        set_msg('爱丽丝说:{}'.format(openai_output))
        msg_lock.release()
        
        logging.info('爱丽丝说:{}'.format(openai_output))

        if not code == 0:
            logging.warning('openai ERROR, TRY RESTART times{}'.format(openai_failed_times))
            openai_failed_times += 1
            continue
        else:
            openai_failed_times = 0
        
        # 喇叭预热
        record_handler.before_play_from_str()
        
        # 百度语音合成
        baidu_lock.acquire()
        code, output_audio = baidu_handler.tts(openai_output)
        baidu_lock.release()
        
        if not code == 0:
            logging.warning('baidu ERROR, TRY RESTART times{}'.format(baidu_tts_failed_times))
            baidu_recognition_failed_times += 1
        else:
            baidu_recognition_failed_times = 0

        # 播放
        try:
            record_handler.play_from_str(output_audio)
        except Exception as e:
            logging.error('play ERROR, {}'.format(str(e)))
            raise Exception('paly ERROR STOP')

        logging.debug('***END_LOOP***')


