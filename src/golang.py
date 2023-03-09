import subprocess
def run_go_repl(code):
    go_process = subprocess.Popen(["go", "run"],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

    stdout, stderr = go_process.communicate(code)

    return stdout.decode(), stderr.decode()
