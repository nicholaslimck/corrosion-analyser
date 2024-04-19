import os


def check_is_docker():
    path = '/proc/self/cgroup'
    return (
        os.environ.get('DOCKER') or
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )


IS_DOCKER = check_is_docker()
