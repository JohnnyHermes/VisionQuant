from VisionQuant.utils.Params import LOG_DIR
from VisionQuant.utils.TimeTool import get_now_time, time_to_str
from loguru import logger
from path import Path

now_time = get_now_time()
date_str_for_log = time_to_str(now_time, '%Y%m')

format_msg = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> |' \
             ' <cyan>{file.path}</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>' \
             ' - <level>{message}</level> '
logger_kwargs = {'format': format_msg, 'encoding': 'utf-8', 'enqueue': True}

logger.add(
    Path('/'.join([LOG_DIR, 'VQlog_{}.log'.format(date_str_for_log)])),
    format=format_msg,
    encoding='utf-8',
    enqueue=True
)
