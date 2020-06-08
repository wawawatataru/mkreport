import sys
import os
import datetime
import requests
from redminelib import Redmine

REPORTER = os.environ['REPORTER']
DEFAULT_START_TIME = os.environ['DEFAULT_START_TIME']
DEFAULT_END_TIME = os.environ['DEFAULT_END_TIME']
REDMINE_URL = os.environ['REDMINE_URL']
REDMINE_API_KEY = os.environ['REDMINE_API_KEY']

redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
today = datetime.date.today()


def main():
    dir_path, file_name = build_file_name()
    check_exist_report(dir_path, file_name)

    worked_time = input_worked_time()
    worked_ticket, worked_ticket_comments, worked_ticket_time = input_worked_ticket()
    one_thing = input_one_thing()

    worked_ticket_text = build_worked_ticket(
        worked_ticket, worked_ticket_comments)
    one_thing_text = build_one_thing(one_thing)

    report_content = build_report_content(worked_time, worked_ticket_text, one_thing_text)
    post_time_entry(worked_ticket_time)
    make_report(dir_path, file_name, report_content)


def build_file_name():
    dir_path = "./daily_report/{year}/{month}/".format(
        year=today.year, month=today.month)
    file_name = str(today.day) + ".txt"
    return dir_path, file_name


def build_one_thing(one_thing):
    return "" if not (one_thing) else "【ひとこと】\n" + one_thing


def build_worked_ticket(worked_ticket, worked_ticket_comments):
    worked_ticket_text = "【作業内容】\n"
    for number, title in worked_ticket.items():
        worked_ticket_text += "#{number} {title}\n".format(
            number=number, title=title)
        worked_ticket_text += "  " + worked_ticket_comments[number] + "\n"
    return worked_ticket_text


def build_report_content(worked_time, worked_ticket, one_thing):
    module_dir = os.path.dirname(__file__)
    filepath = os.path.join(module_dir, 'report_content.txt')
    day_of_week_list = ["月", "火", "水", "木", "金", "土", "日"]
    start = worked_time[0]
    end = worked_time[1]
    report_content = open(filepath, 'r').read().format(
        reporter=REPORTER,
        month=today.month,
        day=today.day,
        day_of_week=day_of_week_list[today.weekday()],
        start=start,
        end=end,
        worked_ticket=worked_ticket,
        one_thing = one_thing
    )
    return report_content


def check_exist_report(dir_path, file_name):
    if os.path.isfile(dir_path + file_name):
        print_error('すでに本日の日報があります。')
        sys.exit()


def confirm_issue_title(issue_title):
    dic = {'y': True, 'yes': True, 'n': False, 'no': False}
    while True:
        try:
            inp = dic[input(
                "「{issue_title}」でよろしいですか?(y/n)\n".format(issue_title=issue_title)).lower()]
            break
        except:
            pass
        print_error('yかnを入力してください。')
    return inp


def format_time(time):
    return_time = time[:2] + ':' + time[2:]
    if return_time[0] == '0':
        return_time = return_time[1:]
    return return_time


def get_issue_title(id):
    try:
        issue_title = redmine.issue.get(id)
        return issue_title.subject
    except:
        return False



def input_one_thing():
    inp = input('日報の最後に記載する一言を入力してください\n')
    return inp


def input_ticket_comment():
    inp = input('日報に記載する作業内容を入力してください\n')
    return inp


def input_ticket_time():
    while True:
        inp = input('作業時間を入力してください\n')
        try:
            float(inp)
        except ValueError:
            print_error('数値を入力してください')
        else:
            if float(inp) > 0:
                break
            print_error('入力した値が正しくありません')
    return float(inp)


def input_worked_ticket():
    ticket_ids = {}
    ticket_comments = {}
    ticket_time = {}
    while True:
        prefix = '作業した' if len(ticket_ids) == 0 else '他にも作業したチケットがあれば'
        inp = input(prefix + 'チケットの番号を入力してください(qを入力すると終了)\n')
        if inp == 'q':
            break
        elif inp.isdigit():
            issue_title = get_issue_title(inp)
            if issue_title:
                if confirm_issue_title(issue_title):
                    ticket_ids[inp] = issue_title
                    ticket_comments[inp] = input_ticket_comment()
                    ticket_time[inp] = input_ticket_time()
            else:
                print_error('チケットが存在しません')
        else:
            print_error('チケットの番号は数字で入力してください')
    return ticket_ids, ticket_comments, ticket_time


def input_time(default_time, target_time):
    return_time = default_time
    while True:
        inp = input(
            target_time + 'を「hhmm」で入力してください(デフォルト「' + default_time + '」)\n')
        if not(inp):
            break
        elif inp.isdigit() and len(inp) == 4:
            return_time = inp
            break
        else:
            print_error('入力形式が正しくありません。')
    return return_time


def input_worked_time():
    while True:
        start_time = input_time(DEFAULT_START_TIME, '勤務開始時間')
        end_time = input_time(DEFAULT_END_TIME, '勤務終了時間')
        if start_time <= end_time:
            break
        else:
            print_error('勤務時間の入力がただしくありません。')
    return [format_time(start_time), format_time(end_time)]


def make_report(dir_path, file_name, report_content):
    file_path = dir_path + file_name
    os.makedirs(dir_path, exist_ok=True)
    f = open(file_path, 'w')
    f.write(report_content)
    print('日報を作成しました。')
    print(file_path)
    f.close()


def post_time_entry(worked_ticket_time):
    for number, hour in worked_ticket_time.items():
        try:
            redmine.time_entry.create(
                issue_id=number,
                hours=hour
            )
        except:
            print_error('作業時間の入力にエラーが発生しました')


def print_error(error_text):
    RED = '\033[31m'
    END = '\033[0m'
    print(RED + error_text + END)


if __name__ == '__main__':
    main()
