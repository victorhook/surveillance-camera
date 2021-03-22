import subprocess


def take_image(mailhandler, quality, output, target):
    subprocess.run(['raspistill', '-q', str(quality), '-o', output])
    try:
        subprocess.run(['scp', output, target])
    except Exception as e:
        mailhandler.send(f'Error using scp: \n{str(e)}')
