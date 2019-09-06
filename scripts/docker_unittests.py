import subprocess
import os
import sys

platforms = [
    'ubuntu:trusty', 'ubuntu:xenial', 'ubuntu:bionic', 'debian:jessie',
    'debian:stretch'
]

with open('.dockerignore', 'w+')  as f:
    f.write("""
    **/*/__pycache__
    **/*.so""")


def dockerfile_base(image):
    HTTPS_PROXY = os.environ.get('https_proxy', '')
    HTTP_PROXY = os.environ.get('http_proxy', '')

    python_dependencies = ['dev', 'pip', 'setuptools', 'pil', 'wheel']
    build_dependencies = [
        'build-essential',
        'git',
    ]
    vi3o_dependencies = ['libavcodec-dev', 'libswscale-dev', 'libffi-dev']

    if 'ubuntu' in image:
        vi3o_dependencies.append('libjpeg-turbo8-dev')
    else:
        vi3o_dependencies.append('libjpeg62-turbo-dev')

    dependencies = ' '.join(
        build_dependencies + vi3o_dependencies +
        ['python-' + x for x in python_dependencies] +
        ['python3-' + x for x in python_dependencies])

    return """
FROM {image}
ENV http_proxy={http_proxy}
ENV https_proxy={https_proxy}

RUN apt-get update && apt-get install -y --no-install-recommends {dependencies}

RUN pip install "pytest<=4.6, !=4.6.0"
""".format(
        image=image,
        https_proxy=HTTPS_PROXY,
        http_proxy=HTTP_PROXY,
        dependencies=dependencies)


DOCKERFILE_TEST = """
FROM {image}
COPY setup.py /build/
COPY build_*.py /build/
COPY vi3o /build/vi3o
COPY src /build/src
COPY test /build/test
RUN pip install -e "/build"
#RUN pip3 install -e "/build"
WORKDIR /build
"""


def build_image(dockerfile, label):
    build_command = ['docker', 'build', '-f', dockerfile, '-t', label, '.']
    print(' '.join(build_command))
    assert subprocess.call(
        build_command, stderr=sys.stdout, stdout=sys.stdout) == 0


def build_base_image(img):
    filename = 'dockerfile_base.{}'.format(img)
    image = 'vi3o-base:{}'.format(img.replace(':', '-'))
    with open(filename, 'w+') as f:
        f.write(dockerfile_base(image=img))

    build_image(filename, image)
    return image


def build_test_image(img):
    filename = 'dockerfile_test.{}'.format(img)
    base_image = 'vi3o-base:{}'.format(img.replace(':', '-'))
    image = 'vi3o-test:{}'.format(img.replace(':', '-'))
    with open(filename, 'w+') as f:
        f.write(DOCKERFILE_TEST.format(image=base_image))

    build_image(filename, image)
    return image


def run_test_image(img):
    image = 'vi3o-test:{}'.format(img.replace(':', '-'))
    return subprocess.call(['docker', 'run', '--rm', image, 'pytest', '-v', '-s'],
                            stderr=sys.stdout,
                            stdout=sys.stdout)


for platform in platforms:
    build_base_image(platform)
    build_test_image(platform)

for platform in platforms:
    print("Testing", platform)
    run_test_image(platform)
