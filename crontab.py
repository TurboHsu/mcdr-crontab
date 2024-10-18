import os
import time
from threading import Thread, Event
from mcdreforged.api.all import *

PLUGIN_METADATA = {
    'id': 'crontab_executor',
    'version': '1.0.0',
    'name': 'Crontab Executor',
    'author': 'TurboHsu',
    'description': 'What do you expect from a crontab executor?',
}

executor = None
permission_level = 3 # Operator

class CronTab(Thread):
    def __init__(self, server: ServerInterface):
        super().__init__()
        self.setDaemon(True)
        self.server = server
        self.setName(self.__class__.__name__)
        self.crontab_tasks = []
        self.stop_event = Event()
        self.crontab_file_path = os.path.join('config', 'crontab.txt')
        
        self.reload_crontab()
    
    def reload_crontab(self):
        self.crontab_tasks.clear()
        try:
            with open(self.crontab_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            minute, hour, day, month, weekday, command = self.parse_crontab_line(line)
                            self.crontab_tasks.append((minute, hour, day, month, weekday, command))
                        except ValueError as e:
                            self.server.logger.error(f'Error parsing crontab line: {line} ({e})')
        except FileNotFoundError:
            self.server.logger.info('crontab.txt not found, creating template')
            self.create_template_crontab()
        except Exception as e:
            self.server.logger.error(f'Error reloading crontab: {e}')
        
        self.server.logger.info('Crontab reloaded with {} tasks'.format(len(self.crontab_tasks)))
    
    def get_crontab_tasks(self) -> str:
        msg = 'Crontab tasks:'
        for minute, hour, day, month, weekday, command in self.crontab_tasks:
            msg += f'\nMinute: {minute}, Hour: {hour}, Day: {day}, Month: {month}, Weekday: {weekday}, Command: {command}'
        return msg
    
    def create_template_crontab(self):
        template = """# * * * * * <command>
# - - - - -
# | | | | |
# | | | | +----- day of week (0 - 6) (Sunday=0)
# | | | +------- month (1 - 12)
# | | +--------- day of month (1 - 31)
# | +----------- hour (0 - 23)
# +------------- minute (0 - 59)
# 
# Example:
# * * * * * say Hello
# 0 0 * * * say Good night"""
        with open(self.crontab_file_path, 'w') as f:
            f.write(template)
    
    def parse_crontab_line(self, line: str):
        parts = line.split(maxsplit=5)
        if len(parts) != 6:
            raise ValueError("Missing fields")
        minute = parts[0]
        hour = parts[1]
        day = parts[2]
        month = parts[3]
        weekday = parts[4]
        command = parts[5]
        return minute, hour, day, month, weekday, command
    
    def match_time(self, cron_field, current_value):
        if cron_field == '*':
            return True
        if ',' in cron_field:
            return any(self.match_time(part, current_value) for part in cron_field.split(','))
        if '-' in cron_field:
            start, end = map(int, cron_field.split('-'))
            return start <= current_value <= end
        if '/' in cron_field:
            base, step = cron_field.split('/')
            if base == '*':
                return current_value % int(step) == 0
            return self.match_time(base, current_value) and current_value % int(step) == 0
        return int(cron_field) == current_value
    
    def run(self):
        while not self.stop_event.is_set():
            current_time = time.localtime()
            current_minute = current_time.tm_min
            current_hour = current_time.tm_hour
            current_day = current_time.tm_mday
            current_month = current_time.tm_mon
            current_weekday = current_time.tm_wday  # 0 means Monday

            for minute, hour, day, month, weekday, command in self.crontab_tasks:
                if (self.match_time(minute, current_minute) and
                    self.match_time(hour, current_hour) and
                    self.match_time(day, current_day) and
                    self.match_time(month, current_month) and
                    self.match_time(weekday, current_weekday)):
                    self.execute_command(command)

            time.sleep(60)

    def execute_command(self, command: str):
        self.server.logger.info(f"Run command: {command}")
        self.server.execute(command)

    def stop(self):
        self.stop_event.set()

def on_load(server: PluginServerInterface, old_module):
    global executor
    executor = CronTab(server)
    server.register_command(
        Literal('!!crontab').requires(lambda src: src.has_permission(permission_level)).then(
            Literal('reload').runs(lambda src: (
                executor.reload_crontab(),
                src.reply('Reloaded crontab with {} tasks'.format(len(executor.crontab_tasks)))
            ))
        ).then(
            Literal('list').runs(lambda src: src.reply(executor.get_crontab_tasks()))
        ).runs(lambda src: src.reply('Usage: !!crontab <reload|list>'))
    )
    executor.start()
    server.logger.info("Crontab Executor loaded")

def on_unload(server: PluginServerInterface):
    executor.stop()
    server.logger.info("Crontab Executor unloaded")