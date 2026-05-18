import os


def _file_contains(path, text):
    with open(path) as f:
        return any(text in line for line in f)


def check_is_docker():
    path = '/proc/self/cgroup'
    return (
        os.environ.get('DOCKER') or
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and _file_contains(path, 'docker')
    )


IS_DOCKER = check_is_docker()
