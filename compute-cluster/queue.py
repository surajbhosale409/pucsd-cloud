import os,sys,json

queue = []

def enqueue(job_data):
    if job_data:
        queue.append(job_data)

def dequeue():
    if len(queue) != 0:
        return queue.pop(0)
    else:
        return False

