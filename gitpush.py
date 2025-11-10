

 
 
import os
from datetime import datetime

import re


def remove_lines_with_parentheses(text):
    lines = text.split('\n')
    lines = [line for line in lines if line]

    pattern = r'^\s*\(.+\)\s*$'
    lines = [line for line in lines if not re.match(pattern, line.strip())]
    return '\n'.join(lines)


class StyleText:
    STYLE_ = {
        'reset' : '\033[0m',
        'bold' : '\033[01m',
        'disable' : '\033[02m',
        'underline' : '\033[04m',
        'reverse' : '\033[07m',
        'strikethrough' : '\033[09m',
        'invisible' : '\033[08m',

        'bg': {
            'black': '\033[40m',
            'red': '\033[41m',
            'green': '\033[42m',
            'orange': '\033[43m',
            'blue': '\033[44m',
            'purple': '\033[45m',
            'cyan': '\033[46m',
            'lightgrey': '\033[47m',
        },

        'fg': {
            'black' : '\033[30m',
            'red' : '\033[31m',
            'green' : '\033[32m',
            'orange' : '\033[33m',
            'blue' : '\033[34m',
            'purple' : '\033[35m',
            'cyan' : '\033[36m',
            'lightgrey' : '\033[37m',
            'darkgrey' : '\033[90m',
            'lightred' : '\033[91m',
            'lightgreen' : '\033[92m',
            'yellow' : '\033[93m',
            'lightblue' : '\033[94m',
            'pink' : '\033[95m',
            'lightcyan' : '\033[96m',
        }
    }

    def __init__(self, text):
        self.text = text
        self.accessed_texts = []  # Initialize a list to store accessed texts

    def __getattr__(self, attr):
        if attr.startswith('bg') and attr.replace('bg_','') in self.STYLE_['bg'].keys():
            accessed_text = f"{self.STYLE_['bg'][attr.replace('bg_','')]}"
            self.accessed_texts.append(accessed_text)  # Append accessed text to the list
            return self
        elif attr.startswith('fg') and attr.replace('fg_','') in self.STYLE_['fg'].keys():
            accessed_text = f"{self.STYLE_['fg'][attr.replace('fg_','')]}"
            self.accessed_texts.append(accessed_text)  # Append accessed text to the list
            return self
        elif attr in ['bold','disable','underline','reverse','strikethrough','invisible']:
            accessed_text = f"{self.STYLE_[attr]}"
            self.accessed_texts.append(accessed_text)  # Append accessed text to the list
            return self
        else:
            raise AttributeError(f"'CustomText' object has no attribute '{attr}'")
    
    def end(self):
        # Print all accessed texts followed by "end"
        print(self.STYLE_['reset']+''.join(self.accessed_texts)+self.text+self.STYLE_['reset']) 

    def __del__(self):
        # Call end method when the object is deleted
        self.end()


# Get current date and time
current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%d %b,%Y  %I:%M%p")

LINE_WIDTH = 70

def header(header):
    print('┌' + '─'*LINE_WIDTH + '┐') 
    print('│' + header.center(LINE_WIDTH,' ') + '│') 
    print('└' + '─'*LINE_WIDTH + '┘') 
    
def footer(footer):
    print()
    print('┌' + '─'*LINE_WIDTH + '┐') 
    print('│' + footer.center(LINE_WIDTH,'=') + '│') 
    print('└' + '─'*LINE_WIDTH + '┘') 
    print()
    print()


commit = input("\033[02m\033[01m\033[96mCommit comment:\033[0m\033[02m  ")
print('\033[0m',end='\r')
# header(formatted_datetime)
# header('Checking Changes')
StyleText(('').center(LINE_WIDTH)+' ').bg_lightgrey.fg_black
StyleText(('Checking Changes').center(LINE_WIDTH)+' ').bg_lightgrey.fg_black.bold
StyleText(('').center(LINE_WIDTH)+' ').bg_lightgrey.fg_black
os.system("git status")
# header('Adding Changes')
StyleText(('Adding Changes').center(LINE_WIDTH)+' ').bg_green.fg_lightcyan.bold
os.system("git add . ")
# header('Added Status')
# StyleText(('✅').center(LINE_WIDTH-1)+' ').bg_lightgrey.fg_lightgrey.bold
os.system("git status")
# header('Uploading...')
StyleText(('Uploading...').center(LINE_WIDTH)+' ').bg_lightgrey.fg_lightgrey.bold

# os.system(f'git commit -m "{str(formatted_datetime)}" ')
os.system(f'git commit -m "{commit}"')
os.system("git push -u origin main")
print()
# footer('  '+commit +'  @ ' + formatted_datetime+'  ')

# os.popen('git config --get user.name').read()
StyleText((' 💬 '+commit).ljust(LINE_WIDTH-2)+' ').bg_cyan.fg_lightblue
StyleText((' 👤 '+os.popen('git config --get user.name').read().strip()).ljust(38) + ('🕑 '+formatted_datetime+' ').rjust(30)).bg_blue.fg_lightcyan
