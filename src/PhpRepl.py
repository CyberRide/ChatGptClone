import subprocess
def execute_php(code):

    # php_code = <?php
    # echo "Hello, World!";
    

    process = subprocess.run(
        ['php'],
        input=code,
        encoding='utf-8',
        capture_output=True
    )

    output = process.stdout
    return(output)