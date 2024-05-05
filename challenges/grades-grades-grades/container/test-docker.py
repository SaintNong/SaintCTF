import docker
import os
os.path.dirname(__file__)
client = docker.from_env()
client.images.build(tag="chall", path=os.path.dirname(__file__))
client.containers.run('chall', auto_remove=True, detach=True, ports={3001:3001})