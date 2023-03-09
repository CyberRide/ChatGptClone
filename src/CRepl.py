import subprocess
def execute_c(code):
    with open("temp.c", "w") as f:
        f.write(code)
    result = subprocess.run(["gcc", "temp.c", "-o", "temp"], stderr=subprocess.PIPE)
    if result.returncode == 0:
        result = subprocess.run(["./temp"], stdout=subprocess.PIPE)
        return result.stdout.decode()
    else:
        # Print the compilation error message
        return result.stderr.decode()