import subprocess
def execute_javascript(code):
    js_code = code
    result = subprocess.run(['node', '-e', js_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode().strip()
