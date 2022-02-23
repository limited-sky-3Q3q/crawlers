from sheen import ColoredHandler, Str
import logging
from logging import root, Logger
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from src.settings import LOG_FOLDER
import os


#定义导出
__all__ = [
	'root',
	'getLogger',
	'add_level',
]

CRITICAL = logging.CRITICAL
FATAL = CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

#设置控制台输出的color常量
FMT_TIME = Str.lightcyan.Underline("%(asctime)s")
FMT_THREAD_NAME = Str.cyan("[%(threadName)s]")
FMT_NAME = Str.cyan("[%(filename)s: %(lineno)s]")
FMT_LEVEL = Str.cyan("%(levelname)s: ")
FMT_MSG = Str("%(message)s")
FMT_DATE = "%Y-%m-%d %X"
FMT_PREFIX = Str(' ').join([FMT_TIME, FMT_THREAD_NAME, FMT_NAME, FMT_LEVEL])

DEFAULT_FMT = {
	'FMT_DEFAULT': FMT_PREFIX + FMT_MSG,
	'FMT_DEBUG': FMT_PREFIX + Str.lightblack(FMT_MSG),
	# 'FMT_NORMAL': FMT_PREFIX + Str.black(FMT_MSG),
	'FMT_INFO': FMT_PREFIX + Str.green(FMT_MSG),
	'FMT_WARNING': FMT_PREFIX + Str.lightyellow(FMT_MSG),
	'FMT_ERROR': FMT_PREFIX + Str.red.Bold(FMT_MSG),
	'FMT_CRITICAL': FMT_PREFIX + Str.RED(FMT_MSG),
}
USER_FMT = DEFAULT_FMT

#控制台输出格式
DEFAULT_FORMATTERS = {
	logging.DEBUG: logging.Formatter(fmt=str(DEFAULT_FMT['FMT_DEBUG']), datefmt=FMT_DATE),
	logging.INFO: logging.Formatter(fmt=str(DEFAULT_FMT['FMT_INFO']), datefmt=FMT_DATE),
	logging.WARNING: logging.Formatter(fmt=str(DEFAULT_FMT['FMT_WARNING']), datefmt=FMT_DATE),
	logging.ERROR: logging.Formatter(fmt=str(DEFAULT_FMT['FMT_ERROR']), datefmt=FMT_DATE),
	logging.CRITICAL: logging.Formatter(fmt=str(DEFAULT_FMT['FMT_CRITICAL']), datefmt=FMT_DATE),
}
USER_FORMATTERS = DEFAULT_FORMATTERS

#控制台输出可选color
CONSOLE_OUTPUT_COLOR = [
	'black',        'red',          'green',        'yellow',
	'lightblack',   'lightred',     'lightgreen',   'lightyellow',
	'blue',         'magenta',      'cyan',         'white',
	'lightblue',    'lightmagenta', 'lightcyan',    'lightwhite',
]

#控制台输出等级默认为NOTSET
DEFAULT_CONSOLE_LEVEL = logging.NOTSET
#root输出等级默认为NOTSET
DEFAULT_ROOT_LEVEL = logging.NOTSET
#filehandler的输出等级默认为INFO
DEFAULT_FILE_LEVEL = logging.INFO
#filehandler的默认格式
DEFAULT_FILEHANDLER_FORMATTER = logging.Formatter('%(asctime)s [%(threadName)s] [%(filename)s: %(lineno)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %X')

#控制台输出handler
color_handler = None

#根logger设置日志等级为最低，所有日志record都会被处理
root.setLevel(DEFAULT_ROOT_LEVEL)

#自定义日志等级 level_name(str): level(int)
USER_LEVEL = {

}

def getLogger(name=None):
	return logging.getLogger(name)

def set_console_output(formatters=None, level=DEFAULT_CONSOLE_LEVEL):
	'''
	设置控制台输出的handler
	
	:param formatters: 
	:param level: 
	:return: 
	'''
	if formatters is None:
		formatters = USER_FORMATTERS

	global color_handler
	color_handler = ColoredHandler()

	#控制台handler设置日至等级为最低，所有日志record都会被显示
	color_handler.setLevel(level)

	color_handler.setFormatters(formatters)
	root.addHandler(color_handler)

def reset_console_output(formatters=None, level=DEFAULT_CONSOLE_LEVEL):
	'''
	重置控制台输出的handler
	
	:param formatters: 
	:param level: 
	:return: 
	'''
	if formatters is None:
		formatters = USER_FORMATTERS

	global color_handler
	root.removeHandler(color_handler)
	set_console_output(formatters, level)

def add_level(level, level_name, console_output_color='black'):
	'''
	添加自定义等级

	:param level: 自定义等级
	:param level_name: 等级名
	:param console_output_color: 自定义等级的控制台输出颜色
								black,        red,          green,        yellow,
								lightblack,   lightred,     lightgreen,   lightyellow,
								blue,         magenta,      cyan,         white,
								lightblue,    lightmagenta, lightcyan,    lightwhite,
	:return: level or None
	'''
	if level in USER_LEVEL.values():
		root.error('the level of "{0}" is already exist'.format(level))
		return None

	if level_name in USER_LEVEL.keys():
		root.error('"{0}" is already exist'.format(level_name))
		return None

	level_name_upper = level_name.upper()
	level_name_lower = level_name.lower()

	#将自定义等级添加到全局
	globals()[level_name_upper] = level

	fmt_name = 'FMT_' + level_name_upper
	if not console_output_color in CONSOLE_OUTPUT_COLOR:
		root.warning('This color <{0}> is not currently supported'.format(console_output_color))
		console_output_color = 'black'
	USER_FMT[fmt_name] = FMT_PREFIX + getattr(Str, console_output_color)(FMT_MSG)
	USER_FORMATTERS[level] = logging.Formatter(fmt=str(USER_FMT[fmt_name]), datefmt=FMT_DATE)

	#添加新定义的日志等级的console输出配置，需重新生成color_handler
	reset_console_output(USER_FORMATTERS)

	logging.addLevelName(level, level_name_upper)
	USER_LEVEL[level_name_upper] = level

	'''
	给Logger类添加自定义日志等级输出函数
	python给类添加静态方法，类实例是会继承类的静态方法的，但是类实例在调用静态方法时，传递的第一个参数还是self
	使用setattr来动态给类\对象添加属性\方法
	'''
	new_func = lambda self, msg, *args, **kwargs: Logger._log(self, level, msg, args, **kwargs)
	setattr(Logger, level_name_lower, new_func)
	return level

def add_file_handler(self, log_path, level=DEBUG, formatter=DEFAULT_FILEHANDLER_FORMATTER):
	''' 给Logger实例添加filehandler

	:param self: Logger实例
	:param log_path: log文件地址
	:param level: filehandler的日志等级
	:param formatter: filehandler的日志格式
	:return: 返回新创建的filehandler，方便remove
	'''
	#必须得是Logger实例来调用
	if not isinstance(self, Logger):
		root.error('the caller must be an instance of Logger')
		return False

	file_handler = logging.FileHandler(log_path, encoding='utf-8')
	file_handler.setLevel(level)
	file_handler.setFormatter(formatter)
	self.addHandler(file_handler)
	return file_handler

def __init():
	#设置控制台输出
	set_console_output(DEFAULT_FORMATTERS)

	'''
	types.MethodType是给实例添加方法
	若使用该方法给类添加方法，则是给类添加类方法，不管是实例还是类对象调用，都是传入类对象为cls参数
	'''
	# Logger.add_file_handler = types.MethodType(add_file_handler, Logger)

	'''
	setattr是给对象添加属性/方法
	给类添加时，是作为类的普通函数，调用该方法的实例会当做self参数被传入
	给实例添加时，是作为实例的方法，不会传入self
	'''
	#通过给Logger添加静态函数的方法来添加add_file_handler

	setattr(Logger, 'add_file_handler', add_file_handler)

	if not os.path.exists(LOG_FOLDER):
		os.makedirs(LOG_FOLDER)

	debug_file_handle = RotatingFileHandler(filename=os.path.join(LOG_FOLDER, 'log'), maxBytes=1024*1024, backupCount=20, encoding='utf-8')
	debug_file_handle.setLevel(DEFAULT_FILE_LEVEL)
	debug_file_handle.setFormatter(DEFAULT_FILEHANDLER_FORMATTER)
	root.addHandler(debug_file_handle)

	warning_file_handle = TimedRotatingFileHandler(filename=os.path.join(LOG_FOLDER, 'warning'),
	                                               when='D', interval=1)
	warning_file_handle.setLevel(WARNING)
	warning_file_handle.setFormatter(DEFAULT_FILEHANDLER_FORMATTER)
	root.addHandler(warning_file_handle)


__init()


if __name__ == '__main__':
	def test_root_logger():
		logger = getLogger()
		logger.debug('debug')
		logger.info('info')
		logger.warning('warning')
		logger.error('error')
		logger.critical('critical')
		
	def test_sub_logger():
		sub_logger = getLogger('lance')
		sub_logger.debug('debug')
		sub_logger.info('info')
		sub_logger.warning('warning')
		sub_logger.error('error')
		sub_logger.critical('critical')

	def test_root_add_file_handler():
		root = getLogger()
		file_handler = root.add_file_handler('./test_root_log.log', INFO)
		root.debug('debug')
		root.info('info')
		root.warning('warning')
		root.error('error')
		root.critical('critical')
		root.removeHandler(file_handler)

	def test_sub_logger_add_file_handler():
		root = getLogger()
		sub_logger = getLogger('lance')
		root_file_handler = root.add_file_handler('./test_root_log.log', INFO)
		sub_logger_file_handler = sub_logger.add_file_handler('./test_sub_log.log', INFO)

		sub_logger.debug('debug')
		sub_logger.info('info')
		sub_logger.warning('warning')
		sub_logger.error('error')
		sub_logger.critical('critical')

		root.removeHandler(root_file_handler)
		sub_logger.removeHandler(sub_logger_file_handler)

	def test_add_level():
		NORMAL = add_level(11, 'normal')
		root = getLogger()
		sub_logger = getLogger('lance')

		root_file_handler = root.add_file_handler('./test_root_log.log', NORMAL)
		sub_logger_file_handler = sub_logger.add_file_handler('./test_sub_log.log', NORMAL)

		root.normal('normal')
		sub_logger.normal('normal')

		root.removeHandler(root_file_handler)
		sub_logger.removeHandler(sub_logger_file_handler)

	# test_root_logger()
	# test_sub_logger()
	# test_root_add_file_handler()
	# test_sub_logger_add_file_handler()
	# test_add_level()
